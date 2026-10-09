"""
ARKAIOS 8D Spatial Audio Engine
Transforma cualquier audio estéreo o mono en una experiencia binaural inmersiva 360° (8D).
Incluye:
- Paneo orbital continuo 360° (LFO configurable).
- Diferencia Interaural de Nivel (ILD).
- Diferencia Interaural de Tiempo (ITD - retardo microtemporal de fase).
- Atenuación espectral posterior (HRTF aproximado: el sonido suena más oscuro al estar atrás).
- Difusión espacial y reverberación 3D para sensación de campo abierto.
"""

import numpy as np
from scipy import signal
import wave
import subprocess
import os

SAMPLE_RATE = 44100
SOUND_SPEED = 343.0  # m/s
HEAD_RADIUS = 0.0875  # ~17.5 cm diámetro de cabeza humana

def load_audio_file(filepath, target_sr=SAMPLE_RATE):
    """Carga audio usando FFmpeg a float32 estéreo."""
    cmd = [
        "ffmpeg", "-y", "-i", filepath,
        "-ar", str(target_sr),
        "-ac", "2",
        "-f", "f32le",
        "-"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw_data, _ = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Error cargando audio con ffmpeg: {filepath}")
    
    audio = np.frombuffer(raw_data, dtype=np.float32)
    audio = audio.reshape(-1, 2).T  # forma (2, N): [canal_izq, canal_der]
    return audio

def save_wav_file(filepath, audio_data, sample_rate=SAMPLE_RATE):
    """Guarda array float32 (2, N) como WAV PCM de 16 o 24 bits."""
    # Normalizar para evitar clipping
    max_val = np.max(np.abs(audio_data))
    if max_val > 0.98:
        audio_data = audio_data * (0.95 / max_val)
    
    int_data = (audio_data.T * 32767.0).clip(-32768, 32767).astype(np.int16)
    with wave.open(filepath, "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(int_data.tobytes())

def apply_reverb_space(audio, sr=SAMPLE_RATE, room_size=0.35, damping=0.5):
    """Agrega una reverberación espacial difusa para situar el audio en un entorno 3D."""
    delay_ms = [29.7, 37.1, 41.5, 43.7, 53.2, 61.9]
    gains = [0.4, 0.35, 0.3, 0.25, 0.2, 0.15]
    wet = np.zeros_like(audio)
    
    for d_ms, g in zip(delay_ms, gains):
        delay_samples = int(d_ms * sr / 1000.0)
        delayed = np.pad(audio, ((0, 0), (delay_samples, 0)))[:, :-delay_samples]
        
        # Filtro de amortiguación de agudos en las reflexiones
        b, a = signal.butter(1, 4500.0 / (sr / 2.0), btype='low')
        delayed = signal.lfilter(b, a, delayed)
        wet += g * delayed
    
    # Mezcla Dry / Wet equilibrada
    return audio * (1.0 - room_size * 0.4) + wet * (room_size * 0.4)

def process_8d(audio_in, sr=SAMPLE_RATE, orbit_period_sec=8.5, radius=0.85, trajectory="circle"):
    """
    Procesa audio en 8D envolvente.
    - orbit_period_sec: Tiempo en segundos que tarda en dar una vuelta completa a la cabeza.
    - radius: Intensidad de la distancia/profundidad (0.1 a 1.0).
    - trajectory: 'circle' o 'figure8'.
    """
    num_samples = audio_in.shape[1]
    t = np.arange(num_samples) / sr
    
    # 1. Trayectoria angular theta(t)
    omega = 2.0 * np.pi / orbit_period_sec
    theta = omega * t  # Ángulo de 0 a 2pi continuamente
    
    if trajectory == "figure8":
        # Movimiento en infinito/figura 8
        pan_x = np.sin(theta)
        pan_y = np.sin(2.0 * theta) * 0.7
    else:
        # Órbita circular suave (x = izquierda/derecha, y = frente/detrás)
        pan_x = np.sin(theta)
        pan_y = np.cos(theta)
    
    # 2. Interaural Level Difference (ILD)
    # Paneo sinusoidal con compensación de energía constante
    angle = np.clip((pan_x * radius + 1.0) * 0.5, 0.0, 1.0)
    gain_l = np.cos(angle * np.pi * 0.5)
    gain_r = np.sin(angle * np.pi * 0.5)
    
    # Entrada monomix combinada o estéreo base ensanchado
    mid = 0.5 * (audio_in[0] + audio_in[1])
    side = 0.5 * (audio_in[0] - audio_in[1]) * 0.4
    base_signal = mid + side
    
    out_l = base_signal * gain_l
    out_r = base_signal * gain_r
    
    # 3. Interaural Time Difference (ITD)
    # Retardo temporal fraccional (hasta ~0.65ms para la oreja más alejada)
    max_delay_samples = int((HEAD_RADIUS / SOUND_SPEED) * sr)  # ~11-12 muestras a 44.1kHz
    delay_delta = (pan_x * max_delay_samples).astype(np.int32)
    
    # Aplicar retardo dinámico por bloques para rendimiento y pureza acústica
    block_size = 2048
    processed_l = np.zeros_like(out_l)
    processed_r = np.zeros_like(out_r)
    
    for i in range(0, num_samples, block_size):
        end = min(i + block_size, num_samples)
        d = delay_delta[i]
        
        # Canal Izquierdo: si d > 0, fuente a la derecha -> oreja izquierda se retrasa
        if d > 0 and i >= d:
            processed_l[i:end] = np.roll(out_l[i:end], d)
            processed_r[i:end] = out_r[i:end]
        elif d < 0 and i >= abs(d):
            processed_l[i:end] = out_l[i:end]
            processed_r[i:end] = np.roll(out_r[i:end], abs(d))
        else:
            processed_l[i:end] = out_l[i:end]
            processed_r[i:end] = out_r[i:end]
    
    # 4. Atenuación Espectral Posterior (Head Shadow / HRTF dinámico)
    # Cuando pan_y < 0 (la fuente está detrás de la cabeza), filtramos agudos
    rear_factor = np.clip(-pan_y, 0.0, 1.0)  # 0 en el frente, 1 completamente atrás
    
    # Filtro paso bajo suave que se mezcla cuando está detrás
    b_rear, a_rear = signal.butter(2, 3800.0 / (sr / 2.0), btype='low')
    muffled_l = signal.lfilter(b_rear, a_rear, processed_l)
    muffled_r = signal.lfilter(b_rear, a_rear, processed_r)
    
    final_l = processed_l * (1.0 - 0.45 * rear_factor) + muffled_l * (0.45 * rear_factor)
    final_r = processed_r * (1.0 - 0.45 * rear_factor) + muffled_r * (0.45 * rear_factor)
    
    out_8d = np.vstack([final_l, final_r])
    
    # 5. Espacio acústico tridimensional
    out_8d = apply_reverb_space(out_8d, sr=sr, room_size=0.30)
    
    # Normalización final con margen seguro (-0.5 dB)
    peak = np.max(np.abs(out_8d))
    if peak > 0:
        out_8d = out_8d * (0.94 / peak)
        
    return out_8d

def convert_to_8d(input_file, output_file, period=9.0, radius=0.9, trajectory="circle"):
    """Función de alto nivel para procesar cualquier archivo y guardarlo en formato WAV o MP3."""
    print(f"[ARKAIOS 8D Engine] Cargando audio: {input_file}...")
    audio = load_audio_file(input_file, SAMPLE_RATE)
    
    print(f"[ARKAIOS 8D Engine] Aplicando espacialización binaural 360° (Periodo: {period}s, Radio: {radius})...")
    audio_8d = process_8d(audio, sr=SAMPLE_RATE, orbit_period_sec=period, radius=radius, trajectory=trajectory)
    
    temp_wav = output_file if output_file.lower().endswith(".wav") else output_file + ".temp.wav"
    save_wav_file(temp_wav, audio_8d, SAMPLE_RATE)
    
    if output_file.lower().endswith(".mp3"):
        print(f"[ARKAIOS 8D Engine] Codificando a MP3 320kbps: {output_file}...")
        cmd = ["ffmpeg", "-y", "-i", temp_wav, "-b:a", "320k", output_file]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if os.path.exists(temp_wav) and temp_wav != output_file:
            os.remove(temp_wav)
            
    print(f"[ARKAIOS 8D Engine] Completado con éxito -> {output_file}")
    return output_file
