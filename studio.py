import os
import sys

# Asegurar UTF-8 en terminal de Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from engine.composer import generate_lines_progression
from engine.synth import render_score_to_audio
from engine.spatializer_8d import process_8d, save_wav_file, load_audio_file, convert_to_8d
import subprocess

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="ARKAIOS Autonomous Music & 8D Studio")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Comando 1: compose (Componer, sintetizar y opcionalmente espacializar en 8D)
    compose_parser = subparsers.add_parser("compose", help="Componer nueva pieza musical con glides continuos y sintetizador")
    compose_parser.add_argument("--style", choices=["ethereal_dream", "cyber_ambient", "deep_space", "neo_tokyo", "hypnotic_drift"], default="ethereal_dream", help="Estilo armónico")
    compose_parser.add_argument("--duration", type=float, default=45.0, help="Duración en segundos")
    compose_parser.add_argument("--bpm", type=float, default=80.0, help="Tempo en BPM")
    compose_parser.add_argument("--name", type=str, default="arkaios_agentic_flow", help="Nombre del archivo resultante")
    compose_parser.add_argument("--spatialize-8d", action="store_true", default=True, help="Aplicar motor espacial 8D binaural")
    compose_parser.add_argument("--orbit-period", type=float, default=9.0, help="Segundos por rotación 360°")
    
    # Comando 2: spatialize (Procesar cualquier archivo existente a 8D)
    spat_parser = subparsers.add_parser("spatialize", help="Convertir un archivo existente (canción de KLMR, etc.) a Audio 8D")
    spat_parser.add_argument("--input", "-i", type=str, required=True, help="Ruta al archivo MP3/WAV original")
    spat_parser.add_argument("--output", "-o", type=str, default="", help="Ruta al archivo resultante (opcional)")
    spat_parser.add_argument("--period", type=float, default=9.0, help="Periodo orbital en segundos (default: 9.0s)")
    spat_parser.add_argument("--radius", type=float, default=0.9, help="Intensidad de separación (0.1 a 1.0)")
    
    args = parser.parse_args()
    
    if args.command == "compose":
        print(f"\n==================================================")
        print(f"  ARKAIOS AUTONOMOUS MUSIC STUDIO - COMPOSER")
        print(f"==================================================")
        print(f"[*] Estilo: {args.style} | BPM: {args.bpm} | Duración: {args.duration}s")
        
        # 1. Composición algorítmica
        score = generate_lines_progression(style=args.style, duration_sec=args.duration, bpm=args.bpm)
        midi_path = os.path.join(OUTPUT_DIR, f"{args.name}.mid")
        score.export_midi(midi_path)
        print(f"[+] Partitura MIDI con curvas de Pitch Bend exportada: {midi_path}")
        
        # 2. Síntesis de audio
        synth_audio = render_score_to_audio(score)
        stereo_wav_path = os.path.join(OUTPUT_DIR, f"{args.name}_stereo.wav")
        save_wav_file(stereo_wav_path, synth_audio)
        print(f"[+] Audio Estéreo Directo (WAV): {stereo_wav_path}")
        
        # 3. Procesamiento Espacial 8D
        if args.spatialize_8d:
            print(f"[*] Aplicando Spatializer 8D Binaural (Rotación: {args.orbit_period}s)...")
            audio_8d = process_8d(synth_audio, orbit_period_sec=args.orbit_period, radius=0.92)
            wav_8d_path = os.path.join(OUTPUT_DIR, f"{args.name}_8D.wav")
            save_wav_file(wav_8d_path, audio_8d)
            
            mp3_8d_path = os.path.join(OUTPUT_DIR, f"{args.name}_8D.mp3")
            print(f"[*] Codificando a MP3 320kbps: {mp3_8d_path}...")
            cmd = ["ffmpeg", "-y", "-i", wav_8d_path, "-b:a", "320k", mp3_8d_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"\n[OK] OBRA MUSICAL 8D FINALIZADA: {mp3_8d_path}")
            print(f"[OK] MIDI original para DAWs: {midi_path}")
            
    elif args.command == "spatialize":
        inp = os.path.abspath(args.input)
        if not os.path.exists(inp):
            print(f"[-] Error: Archivo no encontrado: {inp}")
            sys.exit(1)
            
        out = args.output
        if not out:
            base, ext = os.path.splitext(inp)
            out = f"{base}_8D.mp3"
            
        convert_to_8d(inp, out, period=args.period, radius=args.radius)
        print(f"\n[OK] Conversión a 8D finalizada: {out}")

if __name__ == "__main__":
    main()
