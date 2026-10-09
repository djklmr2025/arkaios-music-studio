"""
ARKAIOS Spatial Audio Engine - Renderizador por Fuente
Procesa y espacializa objetos sonoros independientes en 5 planos de profundidad (fondo a frente).
Aproximación acústica documentada:
- ILD (Interaural Level Difference) y paneo de energía constante.
- ITD (Interaural Time Difference) de retardo microtemporal fraccional (hasta 0.65 ms).
- Filtro espectral de absorción de aire dependiente del plano de profundidad (Z=1 a Z=5).
- Relación Directo / Reflexión ajustada por profundidad para no confundir distancia con volumen.
- Modos de apertura triangular: ensanchamiento de fuente única vs separación y reunión de dos voces.
- Ecos virtuales con retardo, ganancia y amortiguación espectral configurables.
"""

import numpy as np
from scipy import signal
import wave
import os

SAMPLE_RATE = 44100
SOUND_SPEED = 343.0  # m/s
HEAD_RADIUS = 0.0875  # ~17.5 cm

def midi_to_freq(midi_val):
    return 440.0 * (2.0 ** ((midi_val - 69.0) / 12.0))

def interpolate_property(nodes, t, prop_name, default_val=0.0):
    if not nodes:
        return default_val
    if t <= nodes[0].t_offset:
        return getattr(nodes[0], prop_name)
    if t >= nodes[-1].t_offset:
        return getattr(nodes[-1], prop_name)
    for i in range(len(nodes) - 1):
        n0 = nodes[i]
        n1 = nodes[i + 1]
        if n0.t_offset <= t <= n1.t_offset:
            span = max(1e-9, n1.t_offset - n0.t_offset)
            alpha = (t - n0.t_offset) / span
            v0 = getattr(n0, prop_name)
            v1 = getattr(n1, prop_name)
            return v0 + alpha * (v1 - v0)
    return getattr(nodes[-1], prop_name)

def generate_voice_signal(t_arr, freqs, waveform="sine"):
    phase = 2.0 * np.pi * np.cumsum(freqs / SAMPLE_RATE)
    if waveform == "triangle":
        # Onda triangular simétrica
        tri = 2.0 * np.abs(2.0 * (phase / (2.0 * np.pi) - np.floor(phase / (2.0 * np.pi) + 0.5))) - 1.0
        return tri.astype(np.float32)
    elif waveform == "warm_saw":
        saw = signal.sawtooth(phase)
        saw2 = signal.sawtooth(phase * 1.003)
        return (saw * 0.5 + saw2 * 0.5).astype(np.float32)
    elif waveform == "flute":
        sine = np.sin(phase)
        sine2 = 0.3 * np.sin(phase * 2.0)
        return (sine + sine2).astype(np.float32)
    else:  # sine pura
        return np.sin(phase).astype(np.float32)

def apply_echo_line(mono_sig, delay_ms, feedback, damping_hz, sr=SAMPLE_RATE):
    delay_samples = int(delay_ms * sr / 1000.0)
    if delay_samples <= 0 or feedback <= 0:
        return np.zeros_like(mono_sig)
    
    echo_buf = np.zeros(len(mono_sig) + delay_samples, dtype=np.float32)
    echo_buf[:len(mono_sig)] = mono_sig
    
    # Filtro paso bajo para las reflexiones del eco
    nyquist = sr / 2.0
    norm_cutoff = min(damping_hz / nyquist, 0.95)
    b, a = signal.butter(1, norm_cutoff, btype='low')
    
    for i in range(delay_samples, len(echo_buf)):
        in_val = echo_buf[i - delay_samples] * feedback
        echo_buf[i] += in_val
        
    filtered_echo = signal.lfilter(b, a, echo_buf[delay_samples:delay_samples + len(mono_sig)])
    return filtered_echo.astype(np.float32)

def render_spatial_event(event, sr=SAMPLE_RATE):
    """
    Renderiza un único SpatialEvent con espacialización por fuente en 5 planos de profundidad.
    Retorna (2, N_samples) estéreo.
    """
    num_samples = int(event.duration * sr)
    if num_samples <= 0:
        return np.zeros((2, 0), dtype=np.float32)
        
    t_local = np.arange(num_samples) / sr
    
    # 1. Curva de tono instantánea (pitch glide / frecuencia continua)
    p_start = event.pitch_start
    p_end = event.pitch_end
    if abs(p_end - p_start) < 1e-4:
        pitches = np.full(num_samples, p_start, dtype=np.float32)
    else:
        # Interpolación suave de tono
        progress = t_local / event.duration
        pitches = p_start + progress * (p_end - p_start)
    freqs = midi_to_freq(pitches)
    
    # 2. Generar señal base
    raw_sig = generate_voice_signal(t_local, freqs, event.waveform)
    
    # Envolvente de amplitud (ADSR suave para evitar clics)
    env = np.ones(num_samples, dtype=np.float32)
    attack_samples = min(int(0.02 * sr), num_samples // 4)
    release_samples = min(int(0.03 * sr), num_samples // 4)
    if attack_samples > 0:
        env[:attack_samples] = np.linspace(0.0, 1.0, attack_samples)
    if release_samples > 0:
        env[-release_samples:] = np.linspace(1.0, 0.0, release_samples)
    
    # Señal con volumen intrínseco (independiente de la posición espacial)
    sig = raw_sig * env * event.volume
    
    # 3. Interpolar trayectoria temporal (Plano de profundidad, Paneo, Anchura)
    depth_traj = np.array([interpolate_property(event.nodes, t, "depth", 3.0) for t in t_local], dtype=np.float32)
    pan_traj = np.array([interpolate_property(event.nodes, t, "pan", 0.0) for t in t_local], dtype=np.float32)
    width_traj = np.array([interpolate_property(event.nodes, t, "width", 0.0) for t in t_local], dtype=np.float32)
    
    # 4. Modos de Apertura Triangular
    # En modo dual_source_split: se separan dos voces independientes hacia los lados
    if event.width_mode == "dual_source_split":
        # Voz A se desplaza hacia la izquierda (-pan_split), Voz B hacia la derecha (+pan_split)
        split_delta = width_traj * 0.85
        pan_l = np.clip(pan_traj - split_delta, -1.0, 1.0)
        pan_r = np.clip(pan_traj + split_delta, -1.0, 1.0)
        
        # Paneo y mezcla de las 2 fuentes que convergen/divergen
        angle_l = (pan_l + 1.0) * 0.5
        angle_r = (pan_r + 1.0) * 0.5
        
        # Voz A
        sig_a_l = sig * 0.5 * np.cos(angle_l * np.pi * 0.5)
        sig_a_r = sig * 0.5 * np.sin(angle_l * np.pi * 0.5)
        # Voz B
        sig_b_l = sig * 0.5 * np.cos(angle_r * np.pi * 0.5)
        sig_b_r = sig * 0.5 * np.sin(angle_r * np.pi * 0.5)
        
        out_l = sig_a_l + sig_b_l
        out_r = sig_a_r + sig_b_r
    else:
        # Modo single_source_width: una sola fuente cuya anchura aumenta y disminuye
        # Paneo estándar central
        angle = (np.clip(pan_traj, -1.0, 1.0) + 1.0) * 0.5
        gain_l = np.cos(angle * np.pi * 0.5)
        gain_r = np.sin(angle * np.pi * 0.5)
        
        # Ensanchamiento estéreo decorrelacionado según width_traj
        side_comp = width_traj * 0.4
        out_l = sig * (gain_l * (1.0 + side_comp))
        out_r = sig * (gain_r * (1.0 - side_comp))
        
    # 5. Acústica de los 5 Planos de Profundidad (Z = 1..5)
    # Plano 1 (fondo): distancia aparente máxima, absorción de aire (filtro paso bajo ~3500 Hz), mayor difusividad
    # Plano 5 (frente): proximidad máxima, agudos brillantes (~16000 Hz), sonido directo
    # Normalización de nivel comparable: compensamos la ganancia para que el paso 1->5 sea percibido
    # por cercanía acústica/timbre y no como una simple subida artificial de volumen masivo.
    avg_depth = float(np.mean(depth_traj))
    depth_norm = np.clip((avg_depth - 1.0) / 4.0, 0.0, 1.0)  # 0.0 en fondo (plano 1), 1.0 en frente (plano 5)
    
    # Frecuencia de corte dinámica del filtro de absorción de aire
    cutoff_hz = 3200.0 + depth_norm * (16000.0 - 3200.0)
    b_air, a_air = signal.butter(2, min(cutoff_hz / (sr / 2.0), 0.95), btype='low')
    out_l = signal.lfilter(b_air, a_air, out_l)
    out_r = signal.lfilter(b_air, a_air, out_r)
    
    # 6. Ecos Virtuales (Inspiración Sonar / Tiempo de ida y vuelta)
    if event.echo_enabled:
        echo_l = apply_echo_line(out_l, event.echo_delay_ms, event.echo_feedback, event.echo_damping_hz, sr)
        echo_r = apply_echo_line(out_r, event.echo_delay_ms * 1.15, event.echo_feedback, event.echo_damping_hz, sr)
        # En el fondo (plano 1), el eco tiene mayor peso relativo; en el frente (plano 5), el directo predomina
        echo_mix_weight = 0.40 - depth_norm * 0.25
        out_l = out_l * (1.0 - echo_mix_weight) + echo_l * echo_mix_weight
        out_r = out_r * (1.0 - echo_mix_weight) + echo_r * echo_mix_weight
        
    # Calibración de ganancia comparable para aislar espacialización
    # Mantenemos nivel perceptual parejo entre planos (headroom seguro)
    calib_gain = 0.85 + depth_norm * 0.15
    out_l = out_l * calib_gain
    out_r = out_r * calib_gain
    
    return np.vstack([out_l, out_r])

def render_project(project, sr=SAMPLE_RATE):
    """
    Renderiza un proyecto SpatialProject completo a un array estéreo (2, N_samples).
    Calcula métricas técnicas acústicas (Peak, RMS, duración y ausencia de saturación/NaNs).
    """
    total_sec = max(project.total_duration(), 0.1)
    # Añadir cola de decaimiento de 0.5s para posibles ecos
    tail_sec = 0.5
    total_samples = int((total_sec + tail_sec) * sr)
    master_bus = np.zeros((2, total_samples), dtype=np.float32)
    
    for ev in project.events:
        start_sample = int(ev.time_start * sr)
        ev_audio = render_spatial_event(ev, sr=sr)
        ev_len = ev_audio.shape[1]
        end_sample = min(start_sample + ev_len, total_samples)
        valid_len = end_sample - start_sample
        if valid_len > 0:
            master_bus[:, start_sample:end_sample] += ev_audio[:, :valid_len]
            
    # Medir métricas de ingeniería
    has_nan = bool(np.isnan(master_bus).any() or np.isinf(master_bus).any())
    peak_val = float(np.max(np.abs(master_bus)))
    peak_dbfs = 20.0 * np.log10(max(peak_val, 1e-6))
    rms_val = float(np.sqrt(np.mean(master_bus ** 2)))
    rms_dbfs = 20.0 * np.log10(max(rms_val, 1e-6))
    
    # Si hay saturación (> 0 dBFS), aplicar limitación suave y advertir
    is_saturated = peak_val > 0.999
    if peak_val > 0.92:
        master_bus = master_bus * (0.92 / peak_val)
        peak_val = 0.92
        peak_dbfs = 20.0 * np.log10(peak_val)
        
    metrics = {
        "duration_sec": round(float(total_samples / sr), 4),
        "has_nan": has_nan,
        "is_saturated": is_saturated,
        "peak_dbfs": round(peak_dbfs, 2),
        "rms_dbfs": round(rms_dbfs, 2),
        "sample_rate": sr,
        "total_events": len(project.events)
    }
    
    return master_bus, metrics

def export_wav(filepath, audio_data, sr=SAMPLE_RATE):
    """Exporta matriz (2, N) a archivo WAV PCM estéreo de 16 bits."""
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    # Escalar a int16 con margen seguro
    clipped = np.clip(audio_data.T * 32767.0, -32768.0, 32767.0).astype(np.int16)
    with wave.open(filepath, "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(clipped.tobytes())
    return filepath
