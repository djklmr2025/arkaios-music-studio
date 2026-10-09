import os
import sys
import numpy as np

# Configurar ruta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.spatial_model import SpatialProject, SpatialEvent, SpatialNode
from engine.spatial_renderer import render_project, export_wav

def build_lines_8d_masterpiece():
    """
    Recreación fiel de la estructura musical y espacial de LINES ('Musica creada en 8D.mp4'):
    1. Sección 1 (0.0s - 13.0s): Pad polifónico de 8 voces con glissandos sutiles y expansión espacial.
    2. Sección 2 (13.0s - 15.5s): Convergencia de todas las voces hacia un nodo central (Singularidad).
    3. Sección 3 (15.5s - 26.0s): Cascada de arpegios ascendentes y descendentes con ecos espaciales 8D.
    """
    proj = SpatialProject(name="LINES 8D - Masterpiece (Arkaios Spatial Studio)", bpm=85.0, seed=777)
    
    # -------------------------------------------------------------
    # SECCIÓN 1 + 2: PADS POLIFÓNICOS (8 Voces que convergen a C4)
    # -------------------------------------------------------------
    pad_voices = [
        # (id, name, start_pitch, mid_pitch, end_pitch, depth, pan, width_mode, waveform, vol)
        ("bass", "Voz 1 - Sub Bass", 36.0, 38.0, 48.0, 1.5, 0.0, "single_source_width", "warm_saw", 0.35),
        ("low", "Voz 2 - Low Harmony", 43.0, 45.0, 48.0, 2.0, -0.2, "single_source_width", "warm_saw", 0.32),
        ("tenor", "Voz 3 - Tenor Pad", 48.0, 52.0, 60.0, 2.5, -0.4, "single_source_width", "flute", 0.28),
        ("mid", "Voz 4 - Mid Pad", 55.0, 57.0, 60.0, 3.0, +0.4, "single_source_width", "flute", 0.28),
        ("alto", "Voz 5 - Alto Voice", 59.0, 62.0, 60.0, 3.5, -0.6, "dual_source_split", "warm_saw", 0.25),
        ("lead", "Voz 6 - Lush Lead", 64.0, 65.0, 60.0, 4.0, +0.6, "dual_source_split", "warm_saw", 0.25),
        ("shimmer", "Voz 7 - Shimmer Air", 67.0, 71.0, 72.0, 4.5, -0.7, "dual_source_split", "triangle", 0.22),
        ("top", "Voz 8 - Celestial Top", 72.0, 74.0, 72.0, 5.0, +0.7, "dual_source_split", "sine", 0.20),
    ]
    
    for vid, vname, p_start, p_mid, p_end, z_base, pan_base, wmode, wform, vol in pad_voices:
        # Fase 1: Pad sostenido con micro-glide (0.0 a 11.5s)
        ev_pad = SpatialEvent(
            id=f"pad_{vid}_a",
            name=f"{vname} (Sostenido)",
            time_start=0.0,
            duration=11.5,
            pitch_start=p_start,
            pitch_end=p_mid,
            volume=vol,
            waveform=wform,
            trajectory_type="depth_sweep",
            width_mode=wmode,
            nodes=[
                SpatialNode(0.0, depth=z_base, pan=pan_base, width=0.4),
                SpatialNode(6.0, depth=min(5.0, z_base + 0.5), pan=pan_base * 1.2, width=0.8),
                SpatialNode(11.5, depth=z_base, pan=pan_base, width=0.5)
            ],
            echo_enabled=True,
            echo_delay_ms=140.0,
            echo_feedback=0.22,
            echo_damping_hz=3200.0
        )
        proj.add_event(ev_pad)
        
        # Fase 2: Gran Glissando de Convergencia hacia el punto central (11.5 a 15.0s)
        ev_conv = SpatialEvent(
            id=f"pad_{vid}_conv",
            name=f"{vname} (Convergencia)",
            time_start=11.5,
            duration=3.5,
            pitch_start=p_mid,
            pitch_end=p_end,
            volume=vol * 0.9,
            waveform=wform,
            trajectory_type="depth_sweep",
            width_mode="single_source_width",
            nodes=[
                SpatialNode(0.0, depth=z_base, pan=pan_base, width=0.5),
                SpatialNode(2.5, depth=4.5, pan=pan_base * 0.3, width=0.2),
                SpatialNode(3.5, depth=5.0, pan=0.0, width=0.0) # Todo converge al centro frontal
            ],
            echo_enabled=True,
            echo_delay_ms=100.0,
            echo_feedback=0.25,
            echo_damping_hz=4000.0
        )
        proj.add_event(ev_conv)

    # -------------------------------------------------------------
    # SECCIÓN 3: CASCADA DE ARPEGIOS ESPACIALES 8D (15.5s a 26.0s)
    # -------------------------------------------------------------
    # Escala ascendente y descendente pentatónica cósmica (C, D, E, G, A)
    arp_scale = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84, 81, 79, 76, 74, 72, 69, 67, 64, 62]
    arp_t = 15.5
    step_duration = 0.22
    
    # 2 ciclos de arpegios en cascada
    for cycle in range(2):
        for idx, pitch in enumerate(arp_scale):
            t_curr = arp_t + (cycle * len(arp_scale) + idx) * step_duration
            if t_curr >= 25.5:
                break
            
            # Movimiento orbital 8D: pan y profundidad oscilando
            phase = (idx / len(arp_scale)) * 2 * np.pi
            pan_orb = np.sin(phase) * 0.85
            depth_orb = 2.0 + (np.cos(phase) + 1.0) * 1.5 # Entre Z=2.0 y Z=5.0
            
            # Cada nota del arpegio se desliza ligeramente (+1 semitono o fija)
            glide = 0.5 if idx % 3 == 0 else 0.0
            
            ev_arp = SpatialEvent(
                id=f"arp_{cycle}_{idx}",
                name=f"Arpegio {pitch}",
                time_start=t_curr,
                duration=0.45, # Duración con solapamiento suave
                pitch_start=float(pitch),
                pitch_end=float(pitch + glide),
                volume=0.55,
                waveform="warm_saw" if idx % 2 == 0 else "triangle",
                trajectory_type="single_source_width",
                width_mode="single_source_width",
                nodes=[
                    SpatialNode(0.0, depth=depth_orb, pan=pan_orb, width=0.3),
                    SpatialNode(0.45, depth=max(1.0, depth_orb - 0.5), pan=pan_orb * 0.8, width=0.0)
                ],
                echo_enabled=True,
                echo_delay_ms=90.0 + (idx % 4) * 20.0,
                echo_feedback=0.35,
                echo_damping_hz=4500.0
            )
            proj.add_event(ev_arp)
            
    # Nota pedal final envolvente (25.5s a 28.5s)
    ev_final = SpatialEvent(
        id="final_chord",
        name="Acorde Final Resonante",
        time_start=25.0,
        duration=3.5,
        pitch_start=60.0,
        pitch_end=60.0,
        volume=0.70,
        waveform="warm_saw",
        trajectory_type="depth_sweep",
        width_mode="dual_source_split",
        nodes=[
            SpatialNode(0.0, depth=5.0, pan=0.0, width=0.0),
            SpatialNode(1.5, depth=3.0, pan=0.0, width=1.0),
            SpatialNode(3.5, depth=1.0, pan=0.0, width=0.0) # Se desvanece al fondo
        ],
        echo_enabled=True,
        echo_delay_ms=180.0,
        echo_feedback=0.40,
        echo_damping_hz=2800.0
    )
    proj.add_event(ev_final)
    
    return proj

if __name__ == "__main__":
    proj = build_lines_8d_masterpiece()
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects", "lines_8d_masterpiece.json")
    proj.save_json(json_path)
    print(f"[OK] Proyecto LINES 8D Masterpiece guardado: {json_path}")
    print(f"     Total de eventos/voces: {len(proj.events)}")
    print(f"     Duración total calculada: {proj.total_duration():.2f} s")
    
    print("[...] Renderizando audio espacial 8D para verificar...")
    audio_data, metrics = render_project(proj)
    wav_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "lines_8d_masterpiece.wav")
    export_wav(wav_path, audio_data, metrics["sample_rate"])
    print(f"[OK] Audio WAV 8D exportado exitosamente: {wav_path}")
    print(f"     Duración: {metrics['duration_sec']} s")
    print(f"     Peak: {metrics['peak_dbfs']} dBFS")
    print(f"     RMS: {metrics['rms_dbfs']} dBFS")
    print(f"     Saturación: {'SI' if metrics['is_saturated'] else 'NO'}")
    print(f"     NaNs: {'ERROR' if metrics['has_nan'] else 'NO'}")
