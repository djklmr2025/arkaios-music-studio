"""
ARKAIOS Algorithmic Composer & Pitch-Glide Generator (Style: LINES Plugin)
Genera secuencias armónicas con curvas continuas de pitch bend, glides polifónicos,
microtonalidad y progresiones emocionales cinemáticas/ambientales.
"""

import numpy as np
import mido
from mido import Message, MidiFile, MidiTrack

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def midi_to_freq(midi_pitch):
    """Convierte número MIDI (incluso fraccionario / microtonal) a frecuencia en Hz."""
    return 440.0 * (2.0 ** ((midi_pitch - 69.0) / 12.0))

def note_name_to_midi(name_with_octave):
    """Convierte ej. 'C4', 'A#3', 'F5' a número MIDI."""
    name = name_with_octave[:-1].upper()
    octave = int(name_with_octave[-1])
    idx = NOTE_NAMES.index(name)
    return 12 * (octave + 1) + idx

# Escalas y acordes etéreos
SCALES = {
    "cyber_ambient": [0, 2, 4, 7, 9, 11],          # Pentatónica extendida + sensible
    "deep_space": [0, 2, 3, 7, 8, 10],             # Eólico / menor natural cósmico
    "neo_tokyo": [0, 1, 5, 7, 8, 12],              # Escala Insen / Hirajoshi moderna
    "hypnotic_drift": [0, 3, 5, 6, 7, 10],         # Blues menor / Dórico místico
    "ethereal_dream": [0, 4, 7, 9, 11, 14]         # Lidio luminoso suspendido
}

class GlideSegment:
    """Representa una curva de nota deslizante (como las líneas del plugin LINES)."""
    def __init__(self, start_pitch, end_pitch, start_time, duration, curve_type="ease_in_out", velocity=0.8):
        self.start_pitch = float(start_pitch)
        self.end_pitch = float(end_pitch)
        self.start_time = float(start_time)
        self.duration = float(duration)
        self.curve_type = curve_type
        self.velocity = float(velocity)

    def get_pitch_at(self, t):
        eps = 1e-6
        if t < self.start_time - eps or t > self.start_time + self.duration + eps:
            return None
        progress = (t - self.start_time) / max(1e-9, self.duration)
        progress = float(np.clip(progress, 0.0, 1.0))
        
        if self.curve_type == "linear":
            factor = progress
        elif self.curve_type == "ease_in":
            factor = progress ** 2
        elif self.curve_type == "ease_out":
            factor = 1.0 - (1.0 - progress) ** 2
        elif self.curve_type == "ease_in_out":
            factor = 0.5 * (1.0 - np.cos(progress * np.pi))
        else:
            factor = progress
            
        return self.start_pitch + factor * (self.end_pitch - self.start_pitch)

class CompositionScore:
    """Contenedor de voces polifónicas con glides continuos."""
    def __init__(self, tempo_bpm=95.0, total_duration_sec=60.0):
        self.bpm = tempo_bpm
        self.total_duration = total_duration_sec
        self.voices = []  # Lista de listas de GlideSegments (cada voz es una pista)
        
    def add_voice(self, segments):
        self.voices.append(segments)
        
    def export_midi(self, output_filepath):
        """Exporta la partitura a archivo MIDI multicanal con pitch bends interpolados."""
        mid = MidiFile()
        ticks_per_beat = 480
        seconds_per_beat = 60.0 / self.bpm
        
        for voice_idx, segments in enumerate(self.voices):
            track = MidiTrack()
            mid.tracks.append(track)
            track.name = f"Voice_{voice_idx + 1}_Glide"
            channel = voice_idx % 16
            
            # Ordenar segmentos por tiempo de inicio
            sorted_segs = sorted(segments, key=lambda s: s.start_time)
            last_event_time_sec = 0.0
            
            for seg in sorted_segs:
                # Delta time hasta el inicio del segmento
                delta_sec = seg.start_time - last_event_time_sec
                delta_ticks = int(max(0, delta_sec / seconds_per_beat * ticks_per_beat))
                
                base_note = int(round(seg.start_pitch))
                vel = int(seg.velocity * 127)
                
                # Note On
                track.append(Message('note_on', note=base_note, velocity=vel, time=delta_ticks, channel=channel))
                last_event_time_sec = seg.start_time
                
                # Subdividir el glide en micro-eventos de pitch bend (32 pasos por glide)
                num_bends = 24
                bend_step_sec = seg.duration / num_bends
                
                for b in range(1, num_bends + 1):
                    t_curr = seg.start_time + b * bend_step_sec
                    pitch_curr = seg.get_pitch_at(t_curr)
                    if pitch_curr is None:
                        pitch_curr = seg.end_pitch
                    semitone_diff = pitch_curr - base_note
                    # Pitch bend estándar (-2 a +2 semitonos mapeados a -8192..8191)
                    pitch_bend_val = int(np.clip((semitone_diff / 2.0) * 8191, -8192, 8191))
                    
                    bend_ticks = int(bend_step_sec / seconds_per_beat * ticks_per_beat)
                    track.append(Message('pitchwheel', pitch=pitch_bend_val, time=bend_ticks, channel=channel))
                    last_event_time_sec = t_curr
                    
                # Note Off
                track.append(Message('note_off', note=base_note, velocity=0, time=0, channel=channel))
                # Reset pitch bend
                track.append(Message('pitchwheel', pitch=0, time=0, channel=channel))
                
        mid.save(output_filepath)
        return output_filepath

def generate_lines_progression(style="ethereal_dream", duration_sec=45.0, bpm=80.0):
    """
    Genera una composición algorítmica con 4 capas armónicas polifónicas
    que se deslizan suavemente (Sub-Bass, Pad Armónico 1, Pad Armónico 2, Lead Flotante).
    """
    score = CompositionScore(tempo_bpm=bpm, total_duration_sec=duration_sec)
    
    # Progresión de acordes raíces según el estilo
    root_midi = 48  # C3
    if style == "deep_space":
        chords = [[0, 7, 12, 15], [-2, 5, 10, 14], [-4, 3, 8, 12], [-5, 2, 7, 10]]
    elif style == "cyber_ambient":
        chords = [[0, 7, 14, 16], [5, 12, 16, 19], [-3, 4, 9, 14], [2, 9, 14, 18]]
    else:  # ethereal_dream
        chords = [[0, 7, 11, 14], [-3, 4, 9, 12], [2, 9, 13, 16], [-5, 2, 7, 11]]
        
    num_chords = len(chords)
    chord_len = 8.0  # 8 segundos por acorde
    total_cycles = int(np.ceil(duration_sec / (num_chords * chord_len)))
    
    # 4 Voces: 0 = Sub, 1 = Low Mid, 2 = High Mid, 3 = Top Lead
    voice_0 = [] # Bass
    voice_1 = [] # Chords A
    voice_2 = [] # Chords B
    voice_3 = [] # Lead melody
    
    curr_time = 0.0
    
    for cycle in range(total_cycles):
        for c_idx in range(num_chords):
            if curr_time >= duration_sec:
                break
                
            next_c_idx = (c_idx + 1) % num_chords
            c_now = chords[c_idx]
            c_next = chords[next_c_idx]
            
            dur = min(chord_len, duration_sec - curr_time)
            glide_dur = dur * 0.45  # El 45% final del acorde es un glide suave hacia el siguiente
            hold_dur = dur - glide_dur
            
            # Voz 0: Bass
            p0_start = root_midi - 12 + c_now[0]
            p0_end = root_midi - 12 + c_next[0]
            # Paso estático
            voice_0.append(GlideSegment(p0_start, p0_start, curr_time, hold_dur, "linear", 0.9))
            # Paso deslizante (Glide)
            voice_0.append(GlideSegment(p0_start, p0_end, curr_time + hold_dur, glide_dur, "ease_in_out", 0.9))
            
            # Voz 1: Armonía Media
            p1_start = root_midi + c_now[1]
            p1_end = root_midi + c_next[1]
            voice_1.append(GlideSegment(p1_start, p1_start, curr_time, hold_dur, "linear", 0.75))
            voice_1.append(GlideSegment(p1_start, p1_end, curr_time + hold_dur, glide_dur, "ease_in_out", 0.75))
            
            # Voz 2: Armonía Alta
            p2_start = root_midi + c_now[2]
            p2_end = root_midi + c_next[2]
            voice_2.append(GlideSegment(p2_start, p2_start, curr_time, hold_dur, "linear", 0.70))
            voice_2.append(GlideSegment(p2_start, p2_end, curr_time + hold_dur, glide_dur, "ease_in_out", 0.70))
            
            # Voz 3: Melodía / Lead (cambia y se desliza más frecuentemente)
            half_dur = dur / 2.0
            p3_a = root_midi + 12 + c_now[3]
            p3_b = root_midi + 12 + c_now[2] + 2
            p3_next = root_midi + 12 + c_next[3]
            
            voice_3.append(GlideSegment(p3_a, p3_b, curr_time, half_dur, "ease_in_out", 0.85))
            voice_3.append(GlideSegment(p3_b, p3_next, curr_time + half_dur, half_dur, "ease_in_out", 0.85))
            
            curr_time += dur
            
    score.add_voice(voice_0)
    score.add_voice(voice_1)
    score.add_voice(voice_2)
    score.add_voice(voice_3)
    
    return score
