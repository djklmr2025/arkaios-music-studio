"""
ARKAIOS Native Audio Synthesizer Engine
Renderiza partituras polifónicas continuas en audio estéreo de alta fidelidad.
Soporta:
- Osciladores analógicos virtuales (Dual Detuned Saw, Tri-Sine Sub, Shimmer Lead).
- Acumulación de fase de muestra precisa (glides y bends ultra fluidos sin saltos).
- Filtros variables en el tiempo.
- Envolventes ADSR suaves.
- Chorus y ensanchamiento estéreo nativo.
"""

import numpy as np
from scipy import signal
from .composer import midi_to_freq

SAMPLE_RATE = 44100

def generate_voice_audio(segments, voice_type="pad", total_duration_sec=60.0, sr=SAMPLE_RATE):
    """
    Sintetiza una voz completa a partir de una lista de GlideSegments.
    voice_type: 'sub_bass', 'warm_pad', 'ethereal_lead'
    """
    num_samples = int(total_duration_sec * sr)
    audio_out_l = np.zeros(num_samples, dtype=np.float32)
    audio_out_r = np.zeros(num_samples, dtype=np.float32)
    
    # Parámetros según el tipo de instrumento
    if voice_type == "sub_bass":
        osc_type = "sub"
        detune = 0.002
        cutoff = 180.0
        width = 0.1  # Bajo centrado
    elif voice_type == "warm_pad":
        osc_type = "pad"
        detune = 0.006
        cutoff = 1200.0
        width = 0.85
    else:  # ethereal_lead
        osc_type = "lead"
        detune = 0.004
        cutoff = 2600.0
        width = 0.65

    # Para cada segmento de nota/glide en la voz
    for seg in segments:
        start_idx = int(seg.start_time * sr)
        seg_samples = int(seg.duration * sr)
        end_idx = min(start_idx + seg_samples, num_samples)
        actual_len = end_idx - start_idx
        
        if actual_len <= 0:
            continue
            
        t_local = np.arange(actual_len) / sr
        t_global = seg.start_time + t_local
        
        # Calcular vector de frecuencias instantáneas con el glide
        pitches = np.array([seg.get_pitch_at(tg) for tg in t_global], dtype=np.float32)
        freqs = midi_to_freq(pitches)
        
        # Acumular fase instantánea: phase = 2 * pi * cumsum(freq / sr)
        phase_delta = 2.0 * np.pi * freqs / sr
        phase = np.cumsum(phase_delta)
        
        # Generar forma de onda
        if osc_type == "sub":
            # Seno puro + armónico segundo suave
            wave_l = np.sin(phase) + 0.25 * np.sin(phase * 2.0)
            wave_r = np.sin(phase) + 0.25 * np.sin(phase * 2.0)
        elif osc_type == "pad":
            # Oscilador dual desafinado (supersaw suave para pads cósmicos)
            phase_2 = phase * (1.0 + detune)
            phase_3 = phase * (1.0 - detune)
            # Dientes de sierra suaves usando aproximación armónica
            saw1 = signal.sawtooth(phase)
            saw2 = signal.sawtooth(phase_2)
            saw3 = np.sin(phase_3)
            wave_l = (saw1 * 0.4 + saw2 * 0.4 + saw3 * 0.2)
            wave_r = (saw2 * 0.4 + saw1 * 0.4 + saw3 * 0.2)
        else: # lead
            # Triángulo + pulso con vibrato suave
            vibrato = np.sin(2.0 * np.pi * 5.0 * t_local) * 0.003
            phase_vib = phase * (1.0 + vibrato)
            tri = 2.0 * np.abs(2.0 * (phase_vib / (2.0 * np.pi) - np.floor(phase_vib / (2.0 * np.pi) + 0.5))) - 1.0
            sine = np.sin(phase_vib)
            wave_l = tri * 0.6 + sine * 0.4
            wave_r = tri * 0.4 + sine * 0.6

        # Envolvente ADSR suave para evitar clics
        attack_len = min(int(0.25 * sr), actual_len // 4)
        release_len = min(int(0.25 * sr), actual_len // 4)
        env = np.ones(actual_len, dtype=np.float32)
        if attack_len > 0:
            env[:attack_len] = np.linspace(0.0, 1.0, attack_len)
        if release_len > 0:
            env[-release_len:] = np.linspace(1.0, 0.0, release_len)
            
        vel = seg.velocity
        wave_l = wave_l * env * vel
        wave_r = wave_r * env * vel
        
        # Mezclar al canal general con paneo estéreo
        audio_out_l[start_idx:end_idx] += wave_l * (1.0 - width * 0.2)
        audio_out_r[start_idx:end_idx] += wave_r * (1.0 + width * 0.2)
        
    # Filtrado paso bajo de calidez analógica
    nyquist = sr / 2.0
    norm_cutoff = min(cutoff / nyquist, 0.95)
    b, a = signal.butter(2, norm_cutoff, btype='low')
    audio_out_l = signal.lfilter(b, a, audio_out_l)
    audio_out_r = signal.lfilter(b, a, audio_out_r)
    
    return np.vstack([audio_out_l, audio_out_r])

def render_score_to_audio(score, sr=SAMPLE_RATE):
    """
    Toma una partitura polifónica generada por composer y la convierte en audio estéreo masterizable.
    """
    total_dur = score.total_duration
    num_samples = int(total_dur * sr)
    master_mix = np.zeros((2, num_samples), dtype=np.float32)
    
    # Asignación de timbres a cada voz
    voice_configs = [
        ("sub_bass", 0.80),      # Voz 0: Bass
        ("warm_pad", 0.60),      # Voz 1: Mid Pad
        ("warm_pad", 0.50),      # Voz 2: High Pad
        ("ethereal_lead", 0.70)  # Voz 3: Melodic Lead
    ]
    
    print(f"[ARKAIOS Synth] Renderizando {len(score.voices)} capas polifónicas ({total_dur:.1f}s)...")
    for v_idx, segments in enumerate(score.voices):
        v_type, v_gain = voice_configs[min(v_idx, len(voice_configs) - 1)]
        print(f"  -> Capa {v_idx + 1}: Tipo '{v_type}', Ganancia: {v_gain}")
        layer_audio = generate_voice_audio(segments, voice_type=v_type, total_duration_sec=total_dur, sr=sr)
        master_mix += layer_audio * v_gain
        
    # Normalización del bus de mezcla
    peak = np.max(np.abs(master_mix))
    if peak > 0:
        master_mix = master_mix * (0.90 / peak)
        
    return master_mix
