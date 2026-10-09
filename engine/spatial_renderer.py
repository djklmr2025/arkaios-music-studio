"""Stereo spatial approximation: dynamic depth, fractional ITD and virtual echoes.
No measured HRTF or guaranteed front/back localization is claimed.
"""
import os
import wave
import numpy as np
from scipy import signal
SAMPLE_RATE = 44100

def midi_to_freq(value):
    return 440.0 * 2.0 ** ((value - 69.0) / 12.0)

def interpolate_property(nodes, t, prop_name, default_val=0.0):
    if not nodes:
        return np.full_like(t, default_val, dtype=float) if np.ndim(t) else default_val
    return np.interp(t, [n.t_offset for n in nodes], [getattr(n, prop_name) for n in nodes])

def validate_event(event, sr):
    if not isinstance(sr, int) or not 8000 <= sr <= 192000:
        raise ValueError('sample_rate must be an integer between 8000 and 192000')
    limits = {'time_start': (0, 3600), 'duration': (1/sr, 3600),
              'pitch_start': (0,127), 'pitch_end': (0,127), 'volume': (0,1),
              'echo_delay_ms': (0,2000), 'echo_feedback': (0,0.95),
              'echo_damping_hz': (1,sr/2-1)}
    for key, (lo,hi) in limits.items():
        value = getattr(event,key)
        if not np.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f'{key} must be finite and within [{lo}, {hi}]')
    if event.waveform not in ('sine','triangle','warm_saw','flute'):
        raise ValueError('Unsupported waveform')
    if event.width_mode not in ('single_source_width','dual_source_split'):
        raise ValueError('Unsupported width_mode')
    last = -1
    for n in event.nodes:
        for key,lo,hi in [('t_offset',0,event.duration),('depth',1,5),('pan',-1,1),('width',0,1)]:
            value=getattr(n,key)
            if not np.isfinite(value) or not lo <= value <= hi:
                raise ValueError(f'Invalid node {key}')
        if n.t_offset <= last:
            raise ValueError('Node times must be strictly increasing')
        last=n.t_offset

def generate_voice_signal(t_arr, freqs, waveform='sine', sr=SAMPLE_RATE):
    phase=2*np.pi*np.cumsum(freqs/sr)
    if waveform=='triangle': return signal.sawtooth(phase, width=0.5)
    if waveform=='warm_saw': return .5*(signal.sawtooth(phase)+signal.sawtooth(phase*1.003))
    if waveform=='flute': return np.sin(phase)+.3*np.sin(2*phase)
    return np.sin(phase)

def apply_echo_line(mono_sig, delay_ms, feedback, damping_hz, sr=SAMPLE_RATE, tail_samples=0):
    """Causal, filtered repeats. The first return starts after the requested delay."""
    delay=int(round(delay_ms*sr/1000))
    out=np.zeros(len(mono_sig)+tail_samples)
    if delay<=0 or feedback<=0: return out
    b,a=signal.butter(1,min(damping_hz/(sr/2),.95))
    reflection=np.pad(mono_sig,(0,tail_samples)).astype(float)
    # Bound repeat count and stop when gain is negligible.
    for repeat in range(1, min(128,(len(out)-1)//delay)+1):
        reflection=signal.lfilter(b,a,reflection)*feedback
        shift=repeat*delay
        out[shift:]+=reflection[:len(out)-shift]
        if feedback**repeat < 1e-5: break
    return out

def _delay(x, samples):
    return np.interp(np.arange(len(x))-samples,np.arange(len(x)),x,left=0,right=0)

def _dynamic_lowpass(x, cutoff, sr):
    # Stable one-pole lowpass with a per-sample coefficient and continuous state.
    alpha=1-np.exp(-2*np.pi*np.minimum(cutoff,sr*.45)/sr)
    out=np.empty_like(x); state=0.0
    for i in range(len(x)):
        state+=alpha[i]*(x[i]-state);out[i]=state
    return out

def _position(sig, pan, sr):
    angle=(pan+1)*np.pi/4
    itd=pan*.00065*sr
    return np.vstack((_delay(sig,np.maximum(itd,0))*np.cos(angle),
                      _delay(sig,np.maximum(-itd,0))*np.sin(angle)))

def render_spatial_event(event, sr=SAMPLE_RATE):
    validate_event(event,sr)
    n=int(event.duration*sr);t=np.arange(n)/sr
    pitch=event.pitch_start+(event.pitch_end-event.pitch_start)*t/event.duration
    raw=generate_voice_signal(t,midi_to_freq(pitch),event.waveform,sr)
    env=np.ones(n);attack=min(int(.02*sr),n//4);release=min(int(.03*sr),n//4)
    if attack:env[:attack]=np.linspace(0,1,attack)
    if release:env[-release:]=np.linspace(1,0,release)
    sig=raw*env*event.volume
    depth=interpolate_property(event.nodes,t,'depth',3)
    pan=interpolate_property(event.nodes,t,'pan',0)
    width=interpolate_property(event.nodes,t,'width',0)
    if event.width_mode=='dual_source_split':
        # Independent detuned voice; convergence retains both timbres.
        voice_b=generate_voice_signal(t,midi_to_freq(pitch+.07),event.waveform,sr)*env*event.volume
        stereo=(_position(sig,np.clip(pan-width*.85,-1,1),sr)+
                _position(voice_b,np.clip(pan+width*.85,-1,1),sr))*.5
    else:
        stereo=_position(sig,pan,sr)
        # Difference with a delayed copy creates an antisymmetric side component.
        side=(sig-_delay(sig,np.full(n,.0013*sr)))*width*.22
        stereo+=np.vstack((side,-side))
    z=(depth-1)/4
    for ch in range(2):stereo[ch]=_dynamic_lowpass(stereo[ch],3200+z*12800,sr)
    stereo*=.85+.15*z
    if event.echo_enabled and event.echo_delay_ms>0 and event.echo_feedback>0:
        tail=int(.5*sr)
        weight=.40-.25*z
        wet=np.vstack([apply_echo_line(stereo[ch]*weight,event.echo_delay_ms*(1 if ch==0 else 1.15),
                          event.echo_feedback,event.echo_damping_hz,sr,tail) for ch in range(2)])
        stereo=np.pad(stereo*(1-weight),((0,0),(0,tail)))+wet
    return stereo.astype(np.float32)

def render_project(project, sr=None):
    sr=project.sample_rate if sr is None else sr
    if not isinstance(sr,int) or not 8000<=sr<=192000:raise ValueError('Invalid sample_rate')
    for ev in project.events:validate_event(ev,sr)
    n=int((max(project.total_duration(),.1)+.5)*sr)
    bus=np.zeros((2,n),dtype=np.float32)
    for ev in project.events:
        start=int(ev.time_start*sr);audio=render_spatial_event(ev,sr)
        length=min(audio.shape[1],n-start)
        bus[:,start:start+length]+=audio[:,:length]
    if not np.isfinite(bus).all():raise ValueError('Nonfinite render')
    peak=float(np.max(abs(bus)));saturated=peak>.999
    if peak>.92:bus*=.92/peak
    metrics={'duration_sec':round(n/sr,4),'has_nan':False,'is_saturated':saturated,
             'peak_dbfs':round(20*np.log10(max(float(np.max(abs(bus))),1e-6)),2),
             'rms_dbfs':round(20*np.log10(max(float(np.sqrt(np.mean(bus**2))),1e-6)),2),
             'sample_rate':sr,'total_events':len(project.events)}
    return bus,metrics

def export_wav(filepath,audio_data,sr=SAMPLE_RATE):
    if not np.isfinite(audio_data).all():raise ValueError('Nonfinite audio')
    os.makedirs(os.path.dirname(os.path.abspath(filepath)),exist_ok=True)
    with wave.open(filepath,'wb') as wav:
        wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(sr)
        wav.writeframes(np.clip(audio_data.T*32767,-32768,32767).astype(np.int16).tobytes())
    return filepath
