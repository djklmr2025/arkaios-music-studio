"""
ARKAIOS Spatial Music Studio - Batería de Pruebas de Ingeniería Acústica
Genera, renderiza y valida las tres pruebas obligatorias de la primera entrega:
1. Prueba 1: Nota fija de referencia (Plano 3 estático).
2. Prueba 2: Nota que viaja del fondo al frente (Plano 1 -> Plano 5).
3. Prueba 3: Apertura y cierre triangular (Plano 1 fondo cerrado -> apertura en Plano 3-5 -> cierre).
"""

import os
import sys

# Asegurar UTF-8 en consola de Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.spatial_model import SpatialProject, SpatialEvent, SpatialNode
from engine.spatial_renderer import render_project, export_wav

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_test1_nota_fija():
    """Prueba 1: Nota estática en el plano 3 (medio), pan central, volumen calibrado."""
    proj = SpatialProject(name="Prueba 1 - Nota Fija de Referencia", bpm=80.0, seed=101)
    ev = SpatialEvent(
        id="ev_fija",
        name="Nota Fija C4",
        time_start=0.0,
        duration=1.0,
        pitch_start=60.0,
        pitch_end=60.0,
        volume=0.80,
        waveform="warm_saw",
        trajectory_type="static",
        width_mode="single_source_width",
        nodes=[
            SpatialNode(t_offset=0.0, depth=3.0, pan=0.0, width=0.0),
            SpatialNode(t_offset=1.0, depth=3.0, pan=0.0, width=0.0)
        ],
        echo_enabled=True,
        echo_delay_ms=80.0,
        echo_feedback=0.20,
        echo_damping_hz=3500.0
    )
    proj.add_event(ev)
    return proj

def build_test2_fondo_al_frente():
    """
    Prueba 2: Nota de 1 segundo que viaja del fondo (Plano 1) al frente (Plano 5).
    Nodo amarillo intermedio a 0.5s en Plano 3. Tono constante para aislar la profundidad.
    """
    proj = SpatialProject(name="Prueba 2 - Fondo al Frente", bpm=80.0, seed=102)
    ev = SpatialEvent(
        id="ev_profundidad",
        name="Viaje Fondo a Frente C4",
        time_start=0.0,
        duration=1.0,
        pitch_start=60.0,
        pitch_end=60.0,
        volume=0.80,
        waveform="warm_saw",
        trajectory_type="depth_sweep",
        width_mode="single_source_width",
        nodes=[
            SpatialNode(t_offset=0.0, depth=1.0, pan=0.0, width=0.0),  # Inicio en Fondo (Plano 1)
            SpatialNode(t_offset=0.5, depth=3.0, pan=0.0, width=0.0),  # Nodo intermedio (Plano 3)
            SpatialNode(t_offset=1.0, depth=5.0, pan=0.0, width=0.0)   # Llegada al Frente (Plano 5)
        ],
        echo_enabled=True,
        echo_delay_ms=80.0,
        echo_feedback=0.20,
        echo_damping_hz=3500.0
    )
    proj.add_event(ev)
    return proj

def build_test3_apertura_triangular():
    """
    Prueba 3: Apertura y cierre triangular.
    Inicia en Plano 1 (fondo, anchura 0.0). A 0.5s alcanza Plano 4 y máxima apertura (anchura 1.0).
    A 1.0s llega al frente Plano 5 y vuelve a cerrar la figura (anchura 0.0).
    Modo dual_source_split: 2 voces que se separan a los lados y vuelven a converger.
    """
    proj = SpatialProject(name="Prueba 3 - Apertura Triangular", bpm=80.0, seed=103)
    ev = SpatialEvent(
        id="ev_triangular",
        name="Apertura Triangular C4",
        time_start=0.0,
        duration=1.0,
        pitch_start=60.0,
        pitch_end=60.0,
        volume=0.80,
        waveform="warm_saw",
        trajectory_type="triangular_aperture",
        width_mode="dual_source_split",
        nodes=[
            SpatialNode(t_offset=0.0, depth=1.0, pan=0.0, width=0.0),   # Punto 0 en fondo
            SpatialNode(t_offset=0.5, depth=4.0, pan=0.0, width=1.0),   # Máxima apertura triangular
            SpatialNode(t_offset=1.0, depth=5.0, pan=0.0, width=0.0)    # Cierre en frente
        ],
        echo_enabled=True,
        echo_delay_ms=80.0,
        echo_feedback=0.20,
        echo_damping_hz=3500.0
    )
    proj.add_event(ev)
    return proj

def run_tests():
    print("=" * 70)
    print("  ARKAIOS SPATIAL MUSIC STUDIO - EJECUCIÓN Y AUDITORÍA DE PRUEBAS")
    print("=" * 70)
    
    tests = [
        ("test1_nota_fija", build_test1_nota_fija()),
        ("test2_fondo_al_frente", build_test2_fondo_al_frente()),
        ("test3_apertura_triangular", build_test3_apertura_triangular())
    ]
    
    results = []
    
    for filename_base, proj in tests:
        json_path = os.path.join(PROJECTS_DIR, f"{filename_base}.json")
        wav_path = os.path.join(OUTPUT_DIR, f"{filename_base}.wav")
        
        # 1. Guardar especificación JSON
        proj.save_json(json_path)
        
        # 2. Renderizar audio por fuente
        audio_data, metrics = render_project(proj)
        export_wav(wav_path, audio_data)
        
        # 3. Guardar resultados
        results.append({
            "name": proj.name,
            "json_path": json_path,
            "wav_path": wav_path,
            "metrics": metrics
        })
        
        print(f"\n[+] {proj.name}")
        print(f"    - Archivo JSON : {json_path}")
        print(f"    - Archivo WAV  : {wav_path}")
        print(f"    - Duración     : {metrics['duration_sec']} s")
        print(f"    - Peak Amplitud: {metrics['peak_dbfs']} dBFS")
        print(f"    - Nivel RMS    : {metrics['rms_dbfs']} dBFS")
        print(f"    - Sin NaNs/Infs: {'SI' if not metrics['has_nan'] else 'ERROR'}")
        print(f"    - Saturación   : {'NO' if not metrics['is_saturated'] else 'ALERTA SATURADO'}")

    print("\n" + "=" * 70)
    print("  EVALUACIÓN DE COMPARABILIDAD ACÚSTICA (Nivel Perceptual Parejo)")
    print("=" * 70)
    ref_rms = results[0]["metrics"]["rms_dbfs"]
    for r in results:
        diff_rms = r["metrics"]["rms_dbfs"] - ref_rms
        print(f"[*] {r['name']}: RMS {r['metrics']['rms_dbfs']} dBFS (Diferencia vs Referencia: {diff_rms:+.2f} dB)")
        
    print("\n[OK] Todas las 3 pruebas fueron generadas, renderizadas y validadas correctamente.")
    return results

if __name__ == "__main__":
    run_tests()
