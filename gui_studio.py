"""
ARKAIOS Spatial Music Studio - Secuenciador Vectorial de 5 Planos 3D (Estilo LINES)
Inspirado en la composición continua por glissandos, ribbons polifónicos y 
espacialización 8D acústica en Windows 11.
"""

import os
import sys
import time
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import winsound
import numpy as np

# Configurar ruta del motor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine.spatial_model import SpatialProject, SpatialEvent, SpatialNode
from engine.spatial_renderer import render_project, export_wav

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mapeo de notas MIDI
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
def midi_to_note_name(midi_val):
    val = int(round(midi_val))
    octave = (val // 12) - 1
    name = NOTE_NAMES[val % 12]
    return f"{name}{octave}"

def is_black_key(midi_val):
    return (int(round(midi_val)) % 12) in [1, 3, 6, 8, 10]

class SpatialStudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ARKAIOS · LINES SPATIAL MUSIC STUDIO (5 PLANOS 8D)")
        self.root.geometry("1240x820")
        self.root.minsize(980, 650)
        self.root.configure(bg="#0b0a16")
        
        # Estado del proyecto
        self.current_project = None
        self.current_wav_path = None
        self.selected_event_idx = 0
        self.selected_node_idx = None
        
        # Rango de afinación visible (MIDI)
        self.min_midi = 36.0  # C2
        self.max_midi = 84.0  # C6
        
        # Modo de herramienta: 'select' o 'draw'
        self.tool_mode = "select"
        self._updating_inspector = False
        self.drawing_in_progress = False
        
        # Estado de transporte
        self.is_playing = False
        self.is_looping = False
        self.play_start_time = 0.0
        self.playhead_pos_sec = 0.0
        self.total_duration_sec = 10.0
        self._anim_job = None
        
        # Paleta de colores para voces/líneas vectoriales (estilo LINES)
        self.voice_colors = [
            ("#38e8ff", "#133845"), # Cyan brillante
            ("#2ee6a8", "#123b31"), # Menta esmeralda
            ("#ffc94d", "#423517"), # Dorado ámbar
            ("#ff3df0", "#451642"), # Magenta neón
            ("#a855f7", "#311847"), # Púrpura cósmico
            ("#60a5fa", "#192942"), # Azul eléctrico
            ("#f97316", "#3d1e0d"), # Coral cálido
            ("#ec4899", "#3b1327"), # Rosa brillante
        ]
        
        self._setup_styles()
        self._build_ui()
        self._bind_shortcuts()
        
        # Cargar preset por defecto: Masterpiece 8D si existe, o Prueba 2
        masterpiece_file = os.path.join(PROJECTS_DIR, "lines_8d_masterpiece.json")
        if os.path.exists(masterpiece_file):
            self.load_preset("lines_8d_masterpiece")
        else:
            self.load_preset("test2_fondo_al_frente")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0b0a16", foreground="#d8d6f5", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 13, "bold"), foreground="#38e8ff")
        style.configure("Metrics.TLabel", font=("Consolas", 9), foreground="#ffc94d")

    def _build_ui(self):
        # 1. BARRA SUPERIOR (TOOLBAR - Estilo LINES)
        top_bar = tk.Frame(self.root, bg="#121024", height=54, bd=1, relief=tk.SOLID)
        top_bar.pack(fill=tk.X, side=tk.TOP, padx=8, pady=(6, 4))
        
        # Logo / Título
        title_box = tk.Frame(top_bar, bg="#121024")
        title_box.pack(side=tk.LEFT, padx=10, pady=4)
        tk.Label(title_box, text="ARKAIOS · LINES", bg="#121024", fg="#38e8ff", font=("Segoe UI", 13, "bold")).pack(anchor=tk.W)
        tk.Label(title_box, text="Secuenciador Polifónico 8D (5 Planos)", bg="#121024", fg="#8e8ba8", font=("Segoe UI", 8)).pack(anchor=tk.W)
        
        # Separador visual
        tk.Frame(top_bar, bg="#2a274c", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=6)
        
        # Herramientas de Edición [Draw / Select]
        self.btn_select_tool = tk.Button(top_bar, text="🖐 Seleccionar (S)", bg="#2b2854", fg="#38e8ff", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=8, command=lambda: self.set_tool_mode("select"))
        self.btn_select_tool.pack(side=tk.LEFT, padx=3, pady=8)
        
        self.btn_draw_tool = tk.Button(top_bar, text="✏️ Dibujar (D)", bg="#181530", fg="#d8d6f5", font=("Segoe UI", 9), relief=tk.FLAT, padx=8, command=lambda: self.set_tool_mode("draw"))
        self.btn_draw_tool.pack(side=tk.LEFT, padx=3, pady=8)
        
        tk.Button(top_bar, text="➕ Nueva Voz", bg="#1f1b3d", fg="#2ee6a8", font=("Segoe UI", 9), relief=tk.FLAT, padx=8, command=self.add_new_voice).pack(side=tk.LEFT, padx=3, pady=8)
        tk.Button(top_bar, text="🗑️ Borrar Voz", bg="#1f1b3d", fg="#ff6b6b", font=("Segoe UI", 9), relief=tk.FLAT, padx=6, command=self.delete_selected_event).pack(side=tk.LEFT, padx=3, pady=8)
        
        # Separador visual
        tk.Frame(top_bar, bg="#2a274c", width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=6)
        
        # Selector de Presets
        tk.Label(top_bar, text="Preset:", bg="#121024", fg="#ffc94d", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(4, 2))
        self.preset_combo = ttk.Combobox(top_bar, values=[
            "lines_8d_masterpiece",
            "test1_nota_fija",
            "test2_fondo_al_frente",
            "test3_apertura_triangular"
        ], state="readonly", width=18)
        self.preset_combo.pack(side=tk.LEFT, padx=4)
        self.preset_combo.set("lines_8d_masterpiece" if os.path.exists(os.path.join(PROJECTS_DIR, "lines_8d_masterpiece.json")) else "test2_fondo_al_frente")
        self.preset_combo.bind("<<ComboboxSelected>>", lambda e: self.load_preset(self.preset_combo.get()))

        # Botones de Proyecto
        tk.Button(top_bar, text="📂 Abrir...", bg="#221e45", fg="#d8d6f5", relief=tk.FLAT, command=self.open_json_dialog).pack(side=tk.RIGHT, padx=4, pady=8)
        tk.Button(top_bar, text="💾 Guardar JSON", bg="#221e45", fg="#d8d6f5", relief=tk.FLAT, command=self.save_current_json).pack(side=tk.RIGHT, padx=4, pady=8)
        tk.Button(top_bar, text="🎵 Exportar WAV 8D", bg="#38e8ff", fg="#07060f", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, command=self.render_and_export_wav).pack(side=tk.RIGHT, padx=6, pady=8)

        # 2. CONTENEDOR CENTRAL (PANEL PRINCIPAL: PIANO + TIMELINE CANVAS + INSPECTOR)
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#0b0a16", sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        # Contenedor del Secuenciador (Piano a la izquierda + Canvas de Líneas a la derecha)
        sequencer_frame = tk.Frame(main_paned, bg="#0e0d1e", bd=1, relief=tk.SOLID)
        main_paned.add(sequencer_frame, minsize=720)
        
        # Piano vertical a la izquierda
        self.piano_canvas = tk.Canvas(sequencer_frame, width=54, bg="#110f21", highlightthickness=0)
        self.piano_canvas.pack(side=tk.LEFT, fill=tk.Y, padx=(2, 0), pady=2)
        
        # Canvas de las líneas vectoriales (Timeline con compases y ribbons)
        self.timeline_canvas = tk.Canvas(sequencer_frame, bg="#0b0a19", highlightthickness=0)
        self.timeline_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        self.timeline_canvas.bind("<Configure>", lambda e: self.draw_scene())
        self.timeline_canvas.bind("<Button-1>", self.on_canvas_click)
        self.timeline_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.timeline_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.timeline_canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        
        # Inspector Derecho (Parámetros Espaciales de la Voz Seleccionada)
        inspector_frame = tk.Frame(main_paned, bg="#121024", width=340, padx=12, pady=8)
        main_paned.add(inspector_frame, minsize=280)
        
        tk.Label(inspector_frame, text="PARÁMETROS DE LA VOZ:", bg="#121024", fg="#38e8ff", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(4, 6))
        
        self.lbl_voice_info = tk.Label(inspector_frame, text="Voz Seleccionada: 1", bg="#121024", fg="#ffc94d", font=("Segoe UI", 9, "bold"))
        self.lbl_voice_info.pack(anchor=tk.W)
        
        # Tono MIDI
        self.lbl_pitch = tk.Label(inspector_frame, text="Tono MIDI: 60 (C4)", bg="#121024", fg="#ffffff", font=("Segoe UI", 9))
        self.lbl_pitch.pack(anchor=tk.W, pady=(6, 0))
        self.scale_pitch = tk.Scale(inspector_frame, from_=36, to_=84, orient=tk.HORIZONTAL, bg="#121024", fg="#d8d6f5", highlightthickness=0, command=self.on_pitch_change)
        self.scale_pitch.set(60)
        self.scale_pitch.pack(fill=tk.X)
        
        # Volumen Intrínseco
        self.lbl_volume = tk.Label(inspector_frame, text="Volumen: 0.80", bg="#121024", fg="#ffffff", font=("Segoe UI", 9))
        self.lbl_volume.pack(anchor=tk.W, pady=(6, 0))
        self.scale_volume = tk.Scale(inspector_frame, from_=0.05, to_=1.0, resolution=0.05, orient=tk.HORIZONTAL, bg="#121024", fg="#d8d6f5", highlightthickness=0, command=self.on_volume_change)
        self.scale_volume.set(0.80)
        self.scale_volume.pack(fill=tk.X)
        
        # Profundidad Espacial Z (Plano 1 al 5)
        tk.Label(inspector_frame, text="Plano Espacial (1 Fondo ↔ 5 Frente):", bg="#121024", fg="#ffffff", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(8, 0))
        self.lbl_depth = tk.Label(inspector_frame, text="Plano Z: 3.0", bg="#121024", fg="#38e8ff", font=("Segoe UI", 9, "bold"))
        self.lbl_depth.pack(anchor=tk.W)
        self.scale_depth = tk.Scale(inspector_frame, from_=1.0, to_=5.0, resolution=0.1, orient=tk.HORIZONTAL, bg="#121024", fg="#38e8ff", highlightthickness=0, command=self.on_depth_change)
        self.scale_depth.set(3.0)
        self.scale_depth.pack(fill=tk.X)
        
        # Modo de Apertura Triangular
        tk.Label(inspector_frame, text="Modo de Apertura Estéreo:", bg="#121024", fg="#d8d6f5", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(8, 2))
        self.width_mode_var = tk.StringVar(value="single_source_width")
        self.cmb_width = ttk.Combobox(inspector_frame, textvariable=self.width_mode_var, values=["single_source_width", "dual_source_split"], state="readonly")
        self.cmb_width.pack(fill=tk.X)
        self.cmb_width.bind("<<ComboboxSelected>>", self.on_mode_change)
        
        # Timbre / Waveform
        tk.Label(inspector_frame, text="Forma de Onda (Timbre):", bg="#121024", fg="#d8d6f5", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(8, 2))
        self.waveform_var = tk.StringVar(value="warm_saw")
        self.cmb_waveform = ttk.Combobox(inspector_frame, textvariable=self.waveform_var, values=["warm_saw", "flute", "triangle", "sine"], state="readonly")
        self.cmb_waveform.pack(fill=tk.X)
        self.cmb_waveform.bind("<<ComboboxSelected>>", self.on_waveform_change)
        
        # Eco virtual (Sonar)
        self.echo_var = tk.BooleanVar(value=True)
        self.chk_echo = tk.Checkbutton(inspector_frame, text="Ecos Virtuales Activados (Sonar)", variable=self.echo_var, bg="#121024", fg="#38e8ff", selectcolor="#221e45", activebackground="#121024", command=self.on_echo_toggle)
        self.chk_echo.pack(anchor=tk.W, pady=(10, 4))
        
        # Telemetría Acústica
        tk.Label(inspector_frame, text="TELEMETRÍA ACÚSTICA:", bg="#121024", fg="#ffc94d", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(12, 2))
        self.lbl_metrics = tk.Label(inspector_frame, text="Peak: - dBFS | RMS: - dBFS\nDuración: - s | Voces: -", bg="#0e0d1e", fg="#38e8ff", font=("Consolas", 8), justify=tk.LEFT, padx=8, pady=6, bd=1, relief=tk.RIDGE)
        self.lbl_metrics.pack(fill=tk.X, pady=4)

        # 3. BARRA INFERIOR DE TRANSPORTE
        transport_frame = tk.Frame(self.root, bg="#121024", height=56, bd=1, relief=tk.SOLID)
        transport_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(4, 6))
        
        self.btn_play = tk.Button(transport_frame, text="▶ REPRODUCIR", bg="#2ee6a8", fg="#07060f", font=("Segoe UI", 10, "bold"), padx=14, relief=tk.FLAT, command=self.play_audio)
        self.btn_play.pack(side=tk.LEFT, padx=6, pady=8)
        
        self.btn_stop = tk.Button(transport_frame, text="⏹ DETENER", bg="#3a3760", fg="#ffffff", font=("Segoe UI", 10), padx=10, relief=tk.FLAT, command=self.stop_audio)
        self.btn_stop.pack(side=tk.LEFT, padx=4, pady=8)
        
        self.btn_loop = tk.Button(transport_frame, text="🔁 LOOP", bg="#221e45", fg="#d8d6f5", font=("Segoe UI", 9), relief=tk.FLAT, command=self.toggle_loop)
        self.btn_loop.pack(side=tk.LEFT, padx=8, pady=8)
        
        # BPM
        tk.Label(transport_frame, text="BPM:", bg="#121024", fg="#ffc94d", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(12, 2))
        self.lbl_bpm_val = tk.Label(transport_frame, text="85", bg="#121024", fg="#ffffff", font=("Segoe UI", 9))
        self.lbl_bpm_val.pack(side=tk.LEFT, padx=2)
        
        self.scale_bpm = tk.Scale(transport_frame, from_=60, to_=160, orient=tk.HORIZONTAL, bg="#121024", fg="#d8d6f5", length=110, highlightthickness=0, showvalue=0, command=self.on_bpm_change)
        self.scale_bpm.set(85)
        self.scale_bpm.pack(side=tk.LEFT, padx=4)
        
        # Estado
        self.status_lbl = tk.Label(transport_frame, text="Listo.", bg="#121024", fg="#9a98c0", font=("Segoe UI", 9))
        self.status_lbl.pack(side=tk.RIGHT, padx=12)

    def set_tool_mode(self, mode):
        self.tool_mode = mode
        if mode == "select":
            self.btn_select_tool.config(bg="#2b2854", fg="#38e8ff")
            self.btn_draw_tool.config(bg="#181530", fg="#d8d6f5")
            self.status_lbl.config(text="Modo: Seleccionar y mover nodos")
        else:
            self.btn_select_tool.config(bg="#181530", fg="#d8d6f5")
            self.btn_draw_tool.config(bg="#2b2854", fg="#ff3df0")
            self.status_lbl.config(text="Modo: Dibujar nuevas líneas (Haz clic y arrastra en el lienzo)")

    def _bind_shortcuts(self):
        # Atajos estándar de LINES (Juan Pestana Guide 1.2)
        self.root.bind("<d>", lambda e: self.set_tool_mode("draw" if self.tool_mode == "select" else "select"))
        self.root.bind("<D>", lambda e: self.set_tool_mode("draw" if self.tool_mode == "select" else "select"))
        self.root.bind("<s>", lambda e: self.set_tool_mode("select"))
        self.root.bind("<S>", lambda e: self.set_tool_mode("select"))
        self.root.bind("<Up>", lambda e: self.transpose_selection(1))
        self.root.bind("<Down>", lambda e: self.transpose_selection(-1))
        self.root.bind("<Shift-Up>", lambda e: self.transpose_selection(12))
        self.root.bind("<Shift-Down>", lambda e: self.transpose_selection(-12))
        self.root.bind("<space>", lambda e: self.toggle_play())

    def toggle_play(self):
        if self.is_playing:
            self.stop_audio()
        else:
            self.play_audio()

    def toggle_loop(self):
        self.is_looping = not self.is_looping
        color = "#2ee6a8" if self.is_looping else "#d8d6f5"
        self.btn_loop.config(fg=color)
        self.status_lbl.config(text=f"Loop: {'Activado' if self.is_looping else 'Desactivado'}")

    def on_bpm_change(self, val):
        if self.current_project:
            self.current_project.bpm = float(val)
            self.lbl_bpm_val.config(text=f"{int(float(val))}")

    # -------------------------------------------------------------
    # DIBUJADO DE LA ESCENA (PIANO VERTICAL + LÍNEAS VECTORIALES)
    # -------------------------------------------------------------
    def draw_scene(self):
        self._draw_piano()
        self._draw_timeline()

    def _draw_piano(self):
        self.piano_canvas.delete("all")
        w = self.piano_canvas.winfo_width()
        h = self.piano_canvas.winfo_height()
        if w < 10 or h < 10:
            return

        total_semitones = self.max_midi - self.min_midi
        semitone_h = h / max(1.0, total_semitones)
        
        # Identificar qué notas están activas en el playhead
        active_pitches = self._get_active_pitches_at(self.playhead_pos_sec) if self.is_playing else []

        for m in range(int(self.min_midi), int(self.max_midi)):
            y_top = h - (m + 1 - self.min_midi) * semitone_h
            y_bot = h - (m - self.min_midi) * semitone_h
            is_black = is_black_key(m)
            
            # Color base
            fill = "#1b1933" if is_black else "#2e2b52"
            
            # Si la nota está activa en el playhead: iluminar como en el video!
            for ap in active_pitches:
                if abs(ap - m) < 0.6:
                    fill = "#ff3df0" if is_black else "#38e8ff"
                    break
            
            self.piano_canvas.create_rectangle(0, y_top, w, y_bot, fill=fill, outline="#0e0d1e", width=1)
            
            # Etiqueta en notas C
            if (m % 12) == 0:
                note_lbl = midi_to_note_name(m)
                self.piano_canvas.create_text(w - 18, (y_top + y_bot) / 2, text=note_lbl, fill="#ffffff", font=("Segoe UI", 7, "bold"))

    def _draw_timeline(self):
        self.timeline_canvas.delete("all")
        w = self.timeline_canvas.winfo_width()
        h = self.timeline_canvas.winfo_height()
        if w < 50 or h < 50:
            return

        total_semitones = self.max_midi - self.min_midi
        semitone_h = h / max(1.0, total_semitones)
        
        # Duración total visible (mínimo 10 segundos)
        proj_dur = self.current_project.total_duration() if self.current_project else 10.0
        self.total_duration_sec = max(10.0, proj_dur)
        sec_to_x = lambda t: (t / self.total_duration_sec) * w
        pitch_to_y = lambda p: h - ((p - self.min_midi) / total_semitones) * h

        # 1. Rejilla horizontal de semitonos y octavas
        for m in range(int(self.min_midi), int(self.max_midi) + 1):
            y = pitch_to_y(m)
            is_c = (m % 12) == 0
            line_col = "#252147" if is_c else "#131126"
            width = 1.5 if is_c else 1.0
            self.timeline_canvas.create_line(0, y, w, y, fill=line_col, width=width)

        # 2. Rejilla vertical de compases (Bars)
        bpm = self.current_project.bpm if self.current_project else 85.0
        sec_per_beat = 60.0 / bpm
        sec_per_bar = sec_per_beat * 4.0
        num_bars = int(np.ceil(self.total_duration_sec / sec_per_bar)) + 1
        
        for bar in range(num_bars):
            t_bar = bar * sec_per_bar
            bx = sec_to_x(t_bar)
            self.timeline_canvas.create_line(bx, 0, bx, h, fill="#1c1838", width=1.2)
            # Etiqueta de compás
            self.timeline_canvas.create_text(bx + 14, 12, text=f"{bar + 1}", fill="#5f5b82", font=("Consolas", 8, "bold"))

        # 3. Dibujar todos los eventos/voces (Polifonía simultánea con ribbons translúcidos)
        if not self.current_project:
            return

        self.screen_nodes = [] # Lista de (x, y, event_idx, node_idx) para interacción

        for ev_idx, ev in enumerate(self.current_project.events):
            is_selected_ev = (ev_idx == self.selected_event_idx)
            color_pair = self.voice_colors[ev_idx % len(self.voice_colors)]
            line_color = "#ffffff" if is_selected_ev else color_pair[0]
            ribbon_outline = color_pair[0]

            t_start = ev.time_start
            t_end = ev.time_start + ev.duration
            x_start = sec_to_x(t_start)
            x_end = sec_to_x(t_end)

            # Si el evento tiene nodos, calcular puntos de control
            if ev.nodes:
                pts = []
                for n_idx, nd in enumerate(ev.nodes):
                    nx = sec_to_x(t_start + nd.t_offset)
                    # Tono en este nodo
                    frac = nd.t_offset / max(0.001, ev.duration)
                    p_val = getattr(nd, 'pitch', None)
                    if p_val is None:
                        p_val = ev.pitch_start + (ev.pitch_end - ev.pitch_start) * frac
                    ny = pitch_to_y(p_val)
                    pts.append((nx, ny, nd, n_idx))
                    self.screen_nodes.append((nx, ny, ev_idx, n_idx))
            else:
                p_s = ev.pitch_start
                p_e = ev.pitch_end
                pts = [
                    (x_start, pitch_to_y(p_s), None, 0),
                    (x_end, pitch_to_y(p_e), None, 1)
                ]

            # DIBUJAR RIBBON (Cinta envolvente translúcida estilo LINES)
            if len(pts) >= 2:
                # Ancho visual del ribbon proporcional al volumen y width espacial
                ribbon_half = max(3.0, ev.volume * 12.0)
                upper_pts = []
                lower_pts = []
                for px, py, nd, _ in pts:
                    w_mult = (1.0 + nd.width * 0.8) if (nd and hasattr(nd, 'width')) else 1.0
                    rh = ribbon_half * w_mult
                    upper_pts.extend([px, py - rh])
                    lower_pts.extend([px, py + rh])
                
                polygon_pts = upper_pts + lower_pts[::-1]
                # Dibujar sombreado del ribbon
                self.timeline_canvas.create_polygon(polygon_pts, fill="#000000", outline=ribbon_outline, width=1, stipple="gray25" if not is_selected_ev else "")

                # DIBUJAR LÍNEA VECTORIAL CENTRAL
                for i in range(len(pts) - 1):
                    p0 = pts[i]
                    p1 = pts[i + 1]
                    lw = 3.5 if is_selected_ev else 2.0
                    self.timeline_canvas.create_line(p0[0], p0[1], p1[0], p1[1], fill=line_color, width=lw)

                # DIBUJAR NODOS AMARILLOS INTERACTIVOS
                for px, py, nd, n_idx in pts:
                    r = 5.5
                    is_sel_node = (is_selected_ev and n_idx == self.selected_node_idx)
                    n_fill = "#ffffff" if is_sel_node else "#ffc94d"
                    n_out = "#38e8ff" if is_sel_node else "#121024"
                    self.timeline_canvas.create_oval(px - r, py - r, px + r, py + r, fill=n_fill, outline=n_out, width=1.5)

        # 4. DIBUJAR EL PLAYHEAD DORADO (Línea vertical en tiempo real)
        px_head = sec_to_x(self.playhead_pos_sec)
        self.timeline_canvas.create_line(px_head, 0, px_head, h, fill="#ffe066", width=2.0)
        # Marcador triangular superior del playhead
        self.timeline_canvas.create_polygon([px_head - 6, 0, px_head + 6, 0, px_head, 10], fill="#ffe066", outline="")

    def _get_active_pitches_at(self, t_sec):
        """Retorna las notas que están sonando activamente en el instante t (con soporte multipunto)."""
        if not self.current_project:
            return []
        active = []
        for ev in self.current_project.events:
            if ev.time_start <= t_sec <= (ev.time_start + ev.duration):
                if ev.nodes and any(getattr(n, 'pitch', None) is not None for n in ev.nodes):
                    node_times = [n.t_offset for n in ev.nodes]
                    node_pitches = [n.pitch if (hasattr(n, 'pitch') and n.pitch is not None) else (ev.pitch_start + (ev.pitch_end - ev.pitch_start) * (n.t_offset / max(1e-6, ev.duration))) for n in ev.nodes]
                    t_in_ev = t_sec - ev.time_start
                    pitch = float(np.interp(t_in_ev, node_times, node_pitches))
                else:
                    rel_t = (t_sec - ev.time_start) / max(0.001, ev.duration)
                    pitch = ev.pitch_start + (ev.pitch_end - ev.pitch_start) * rel_t
                active.append(pitch)
        return active

    # -------------------------------------------------------------
    # INTERACCIÓN CON EL CANVAS (SELECCIÓN, BEND POINTS Y DIBUJO CONTINUO)
    # -------------------------------------------------------------
    def on_canvas_double_click(self, event):
        """Añade un punto de control (Bend point) en la posición del doble clic (estilo LINES)."""
        if not self.current_project or not self.current_project.events:
            return
        w = self.timeline_canvas.winfo_width()
        h = self.timeline_canvas.winfo_height()
        if w < 10 or h < 10:
            return

        total_semitones = self.max_midi - self.min_midi
        clicked_midi = self.min_midi + (1.0 - (np.clip(event.y, 0, h) / h)) * total_semitones
        clicked_t = (np.clip(event.x, 0, w) / w) * self.total_duration_sec

        # Buscar el evento más cercano o el seleccionado
        ev = self.current_project.events[self.selected_event_idx]
        if not (ev.time_start <= clicked_t <= ev.time_start + ev.duration):
            for i, other in enumerate(self.current_project.events):
                if other.time_start <= clicked_t <= other.time_start + other.duration:
                    self.selected_event_idx = i
                    ev = other
                    break

        rel_t = max(0.01, min(ev.duration - 0.01, clicked_t - ev.time_start))
        # Determinar profundidad interpolada
        z_approx = ev.nodes[0].depth if ev.nodes else 3.0
        new_node = SpatialNode(t_offset=round(rel_t, 3), depth=z_approx, pan=0.0, width=0.4, pitch=round(clicked_midi, 2))
        ev.nodes.append(new_node)
        ev.nodes.sort(key=lambda n: n.t_offset)
        self.selected_node_idx = ev.nodes.index(new_node)
        self._sync_inspector_to_event()
        self.draw_scene()
        self.status_lbl.config(text=f"Añadido punto de curvatura (Bend) en t={rel_t:.2f}s, {midi_to_note_name(clicked_midi)}")

    def on_canvas_click(self, event):
        w = self.timeline_canvas.winfo_width()
        h = self.timeline_canvas.winfo_height()
        if w < 10 or h < 10:
            return

        # 1. Buscar si se hizo clic en un nodo amarillo existente
        for nx, ny, ev_idx, n_idx in self.screen_nodes:
            if np.hypot(event.x - nx, event.y - ny) <= 10.0:
                self.selected_event_idx = ev_idx
                self.selected_node_idx = n_idx
                self._sync_inspector_to_event()
                self.draw_scene()
                return

        # 2. Si es modo Draw (Lápiz libre / continuo)
        if self.tool_mode == "draw":
            total_semitones = self.max_midi - self.min_midi
            clicked_midi = self.min_midi + (1.0 - (event.y / h)) * total_semitones
            clicked_t = (event.x / w) * self.total_duration_sec
            
            # Crear nueva voz y registrar inicio del trazo
            idx = len(self.current_project.events) + 1
            new_ev = SpatialEvent(
                id=f"voice_{idx}",
                name=f"Voz {idx}",
                time_start=round(max(0.0, clicked_t), 2),
                duration=1.5,
                pitch_start=round(clicked_midi, 1),
                pitch_end=round(clicked_midi, 1),
                volume=0.60,
                waveform="warm_saw",
                nodes=[
                    SpatialNode(0.0, depth=3.0, pan=0.0, width=0.4, pitch=round(clicked_midi, 2))
                ]
            )
            self.current_project.add_event(new_ev)
            self.selected_event_idx = len(self.current_project.events) - 1
            self.selected_node_idx = 0
            self.drawing_in_progress = True
            self._sync_inspector_to_event()
            self.draw_scene()
            self.status_lbl.config(text=f"Dibujando trazo libre desde {midi_to_note_name(clicked_midi)}...")
        else:
            # En modo select, buscar si hizo clic en una línea para seleccionarla
            total_semitones = self.max_midi - self.min_midi
            clicked_midi = self.min_midi + (1.0 - (event.y / h)) * total_semitones
            clicked_t = (event.x / w) * self.total_duration_sec
            found = False
            for i, ev in enumerate(self.current_project.events):
                if ev.time_start <= clicked_t <= ev.time_start + ev.duration:
                    if abs(ev.pitch_start - clicked_midi) <= 3.0 or abs(ev.pitch_end - clicked_midi) <= 3.0:
                        self.selected_event_idx = i
                        self.selected_node_idx = None
                        self._sync_inspector_to_event()
                        self.draw_scene()
                        found = True
                        break
            if not found:
                # Mover el playhead al punto cliqueado
                self.playhead_pos_sec = max(0.0, min(self.total_duration_sec, clicked_t))
                self.selected_node_idx = None
                self.draw_scene()

    def on_canvas_drag(self, event):
        if not self.current_project or self.selected_event_idx >= len(self.current_project.events):
            return

        w = self.timeline_canvas.winfo_width()
        h = self.timeline_canvas.winfo_height()
        total_semitones = self.max_midi - self.min_midi
        y_clamped = np.clip(event.y, 0, h)
        new_pitch = self.min_midi + (1.0 - (y_clamped / h)) * total_semitones
        x_clamped = np.clip(event.x, 0, w)
        abs_t = (x_clamped / w) * self.total_duration_sec
        ev = self.current_project.events[self.selected_event_idx]

        # Si estamos en modo de dibujo continuo con el lápiz:
        if self.drawing_in_progress:
            rel_t = max(0.02, abs_t - ev.time_start)
            # Agregar nodo si avanzó en el tiempo
            last_t = ev.nodes[-1].t_offset if ev.nodes else 0.0
            if rel_t > last_t + 0.05:
                ev.nodes.append(SpatialNode(t_offset=round(rel_t, 3), depth=3.0, pan=0.0, width=0.4, pitch=round(new_pitch, 2)))
                ev.duration = max(ev.duration, round(rel_t + 0.05, 3))
                ev.pitch_end = round(new_pitch, 1)
            self.draw_scene()
            return

        # Si estamos arrastrando un nodo existente:
        if self.selected_node_idx is not None and ev.nodes and self.selected_node_idx < len(ev.nodes):
            nd = ev.nodes[self.selected_node_idx]
            rel_t = np.clip(abs_t - ev.time_start, 0.0, ev.duration)
            nd.t_offset = round(float(rel_t), 3)
            nd.pitch = round(float(new_pitch), 2)
            
            if self.selected_node_idx == 0:
                ev.pitch_start = round(float(new_pitch), 1)
            elif self.selected_node_idx == len(ev.nodes) - 1:
                ev.pitch_end = round(float(new_pitch), 1)
                
            self._updating_inspector = True
            try:
                self.scale_pitch.set(int(round(new_pitch)))
                self.lbl_pitch.config(text=f"Tono MIDI: {int(round(new_pitch))} ({midi_to_note_name(new_pitch)})")
            finally:
                self._updating_inspector = False

        self.draw_scene()

    def on_canvas_release(self, event):
        if self.drawing_in_progress:
            self.drawing_in_progress = False
            ev = self.current_project.events[self.selected_event_idx]
            if len(ev.nodes) == 1:
                # Si fue solo un clic sin arrastre, añadir nodo final
                ev.nodes.append(SpatialNode(t_offset=ev.duration, depth=3.0, pan=0.0, width=0.4, pitch=ev.pitch_start))
            ev.nodes.sort(key=lambda n: n.t_offset)
            self.selected_node_idx = len(ev.nodes) - 1
            self._sync_inspector_to_event()
            self.draw_scene()
            self.status_lbl.config(text=f"Trazo completado ({len(ev.nodes)} nodos).")

    # -------------------------------------------------------------
    # GESTIÓN DE VOCES Y PARÁMETROS (INSPECTOR SEGURO)
    # -------------------------------------------------------------
    def add_new_voice(self):
        if not self.current_project:
            return
        idx = len(self.current_project.events) + 1
        ev = SpatialEvent(
            id=f"voice_{idx}",
            name=f"Voz {idx}",
            time_start=0.0,
            duration=3.0,
            pitch_start=60.0,
            pitch_end=64.0,
            volume=0.50,
            waveform="warm_saw",
            nodes=[
                SpatialNode(0.0, depth=3.0, pan=0.0, width=0.5, pitch=60.0),
                SpatialNode(3.0, depth=4.0, pan=0.0, width=0.5, pitch=64.0)
            ]
        )
        self.current_project.add_event(ev)
        self.selected_event_idx = len(self.current_project.events) - 1
        self.selected_node_idx = 0
        self._sync_inspector_to_event()
        self.draw_scene()
        self.status_lbl.config(text=f"Voz {idx} agregada.")

    def delete_selected_event(self):
        if not self.current_project or not self.current_project.events:
            return
        if len(self.current_project.events) <= 1:
            messagebox.showinfo("Información", "El proyecto debe contener al menos 1 voz.")
            return
        del self.current_project.events[self.selected_event_idx]
        self.selected_event_idx = max(0, self.selected_event_idx - 1)
        self.selected_node_idx = 0
        self._sync_inspector_to_event()
        self.draw_scene()
        self.status_lbl.config(text="Voz eliminada.")

    def _sync_inspector_to_event(self):
        """Sincroniza los controles sin disparar callbacks que aplanen curvas."""
        if not self.current_project or not self.current_project.events:
            return
        if self.selected_event_idx >= len(self.current_project.events):
            self.selected_event_idx = 0

        self._updating_inspector = True
        try:
            ev = self.current_project.events[self.selected_event_idx]
            self.lbl_voice_info.config(text=f"Voz: {ev.name} ({self.selected_event_idx + 1}/{len(self.current_project.events)})")
            
            # Tono del nodo seleccionado o tono de inicio
            if self.selected_node_idx is not None and ev.nodes and self.selected_node_idx < len(ev.nodes):
                curr_p = getattr(ev.nodes[self.selected_node_idx], 'pitch', None)
                if curr_p is None:
                    curr_p = ev.pitch_start
            else:
                curr_p = ev.pitch_start

            self.scale_pitch.set(int(round(curr_p)))
            self.lbl_pitch.config(text=f"Tono MIDI: {int(round(curr_p))} ({midi_to_note_name(curr_p)})")
            self.scale_volume.set(ev.volume)
            self.lbl_volume.config(text=f"Volumen: {ev.volume:.2f}")
            
            # Profundidad Z
            if self.selected_node_idx is not None and ev.nodes and self.selected_node_idx < len(ev.nodes):
                z_val = ev.nodes[self.selected_node_idx].depth
            else:
                z_val = ev.nodes[0].depth if ev.nodes else 3.0
            self.scale_depth.set(z_val)
            self.lbl_depth.config(text=f"Plano Z: {z_val:.1f}")
            
            self.width_mode_var.set(ev.width_mode)
            self.waveform_var.set(ev.waveform)
            self.echo_var.set(ev.echo_enabled)
        finally:
            self._updating_inspector = False

    def transpose_selection(self, semitones):
        """Transpone de manera no destructiva conservando curvas de glissando."""
        if not self.current_project or not self.current_project.events:
            return
        if self.selected_event_idx < len(self.current_project.events):
            ev = self.current_project.events[self.selected_event_idx]
            if self.selected_node_idx is not None and ev.nodes and self.selected_node_idx < len(ev.nodes):
                nd = ev.nodes[self.selected_node_idx]
                curr = nd.pitch if getattr(nd, 'pitch', None) is not None else ev.pitch_start
                nd.pitch = float(np.clip(curr + semitones, self.min_midi, self.max_midi))
                if self.selected_node_idx == 0:
                    ev.pitch_start = nd.pitch
                elif self.selected_node_idx == len(ev.nodes) - 1:
                    ev.pitch_end = nd.pitch
            else:
                ev.pitch_start = float(np.clip(ev.pitch_start + semitones, self.min_midi, self.max_midi))
                ev.pitch_end = float(np.clip(ev.pitch_end + semitones, self.min_midi, self.max_midi))
                for nd in ev.nodes:
                    if getattr(nd, 'pitch', None) is not None:
                        nd.pitch = float(np.clip(nd.pitch + semitones, self.min_midi, self.max_midi))
            self._sync_inspector_to_event()
            self.draw_scene()
            self.status_lbl.config(text=f"Transposición: {'+' if semitones > 0 else ''}{semitones} st")

    def on_pitch_change(self, val):
        if self._updating_inspector:
            return
        if self.current_project and self.current_project.events:
            if self.selected_event_idx < len(self.current_project.events):
                p = float(val)
                ev = self.current_project.events[self.selected_event_idx]
                if self.selected_node_idx is not None and ev.nodes and self.selected_node_idx < len(ev.nodes):
                    # Actualizar solo este nodo sin aplanar el resto
                    ev.nodes[self.selected_node_idx].pitch = p
                    if self.selected_node_idx == 0:
                        ev.pitch_start = p
                    elif self.selected_node_idx == len(ev.nodes) - 1:
                        ev.pitch_end = p
                else:
                    # Transponer toda la voz uniformemente
                    delta = p - ev.pitch_start
                    ev.pitch_start = p
                    ev.pitch_end += delta
                    for nd in ev.nodes:
                        if getattr(nd, 'pitch', None) is not None:
                            nd.pitch += delta
                self.lbl_pitch.config(text=f"Tono MIDI: {int(p)} ({midi_to_note_name(p)})")
                self.draw_scene()

    def on_volume_change(self, val):
        if self._updating_inspector:
            return
        if self.current_project and self.current_project.events:
            if self.selected_event_idx < len(self.current_project.events):
                v = float(val)
                self.current_project.events[self.selected_event_idx].volume = v
                self.lbl_volume.config(text=f"Volumen: {v:.2f}")
                self.draw_scene()

    def on_depth_change(self, val):
        if self._updating_inspector:
            return
        if self.current_project and self.current_project.events:
            if self.selected_event_idx < len(self.current_project.events):
                z = float(val)
                ev = self.current_project.events[self.selected_event_idx]
                if self.selected_node_idx is not None and ev.nodes and self.selected_node_idx < len(ev.nodes):
                    ev.nodes[self.selected_node_idx].depth = z
                else:
                    old_z = ev.nodes[0].depth if ev.nodes else 3.0
                    delta = z - old_z
                    for nd in ev.nodes:
                        nd.depth = float(np.clip(nd.depth + delta, 1.0, 5.0))
                self.lbl_depth.config(text=f"Plano Z: {z:.1f}")
                self.draw_scene()

    def on_mode_change(self, event):
        if self.current_project and self.current_project.events:
            if self.selected_event_idx < len(self.current_project.events):
                self.current_project.events[self.selected_event_idx].width_mode = self.width_mode_var.get()
                self.draw_scene()

    def on_waveform_change(self, event):
        if self.current_project and self.current_project.events:
            if self.selected_event_idx < len(self.current_project.events):
                self.current_project.events[self.selected_event_idx].waveform = self.waveform_var.get()

    def on_echo_toggle(self):
        if self.current_project and self.current_project.events:
            if self.selected_event_idx < len(self.current_project.events):
                self.current_project.events[self.selected_event_idx].echo_enabled = self.echo_var.get()

    # -------------------------------------------------------------
    # TRANSPORTE Y REPRODUCCIÓN EN VIVO CON PLAYHEAD
    # -------------------------------------------------------------
    def play_audio(self):
        if not self.current_project:
            return
            
        self.status_lbl.config(text="Renderizando preescucha...")
        self.root.update_idletasks()
        
        temp_wav = os.path.join(OUTPUT_DIR, "live_preview.wav")
        audio_data, metrics = render_project(self.current_project)
        export_wav(temp_wav, audio_data, metrics["sample_rate"])
        self.current_wav_path = temp_wav
        self._update_metrics_display(metrics)
        
        # Reproducir asíncronamente vía winsound
        winsound.PlaySound(temp_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.is_playing = True
        self.play_start_time = time.time()
        self.btn_play.config(bg="#ff3df0", text="▶ REPRODUCIENDO...")
        self.status_lbl.config(text="▶ Reproduciendo en vivo...")
        
        # Iniciar loop de animación del Playhead a 30 FPS
        self._animate_playhead()

    def _animate_playhead(self):
        if not self.is_playing:
            return
            
        elapsed = time.time() - self.play_start_time
        total_dur = self.current_project.total_duration(include_tail=True) if self.current_project else 10.0
        
        if elapsed >= total_dur:
            if self.is_looping:
                self.play_start_time = time.time()
                self.playhead_pos_sec = 0.0
                winsound.PlaySound(self.current_wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                self.stop_audio()
                self.playhead_pos_sec = 0.0
                self.draw_scene()
                return
        else:
            self.playhead_pos_sec = elapsed
            
        self.draw_scene()
        self._anim_job = self.root.after(33, self._animate_playhead) # ~30 fps

    def stop_audio(self):
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None
        winsound.PlaySound(None, winsound.SND_PURGE)
        self.is_playing = False
        self.btn_play.config(bg="#2ee6a8", text="▶ REPRODUCIR")
        self.status_lbl.config(text="⏹ Detenido.")
        self.draw_scene()

    # -------------------------------------------------------------
    # PRESETS Y PERSISTENCIA (JSON / WAV)
    # -------------------------------------------------------------
    def load_preset(self, preset_name):
        json_file = os.path.join(PROJECTS_DIR, f"{preset_name}.json")
        if not os.path.exists(json_file):
            if preset_name == "lines_8d_masterpiece":
                from generate_lines_8d_masterpiece import build_lines_8d_masterpiece
                proj = build_lines_8d_masterpiece()
                proj.save_json(json_file)
            else:
                from tests_run import run_tests
                run_tests()
                
        if os.path.exists(json_file):
            self.current_project = SpatialProject.load_json(json_file)
            self.total_duration_sec = max(1.0, self.current_project.total_duration(include_tail=True))
            self.selected_event_idx = 0
            self.selected_node_idx = 0
            self.preset_combo.set(preset_name)
            self._sync_inspector_to_event()
            self.draw_scene()
            self._update_metrics_display()
            self.status_lbl.config(text=f"Cargado: {self.current_project.name}")

    def _update_metrics_display(self, metrics=None):
        if not self.current_project:
            return
        if metrics is None:
            dur = self.current_project.total_duration(include_tail=True)
            text = (f"Peak: - dBFS | RMS: - dBFS\n"
                    f"Duración: {dur:.1f} s | Voces: {len(self.current_project.events)}")
        else:
            text = (f"Peak: {metrics['peak_dbfs']} dBFS | RMS: {metrics['rms_dbfs']} dBFS\n"
                    f"Duración: {metrics['duration_sec']} s | Voces: {metrics['total_events']}")
        self.lbl_metrics.config(text=text)

    def save_current_json(self):
        if not self.current_project:
            return
        out_path = filedialog.asksaveasfilename(
            initialdir=PROJECTS_DIR,
            title="Guardar Proyecto JSON",
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")]
        )
        if out_path:
            self.current_project.save_json(out_path)
            messagebox.showinfo("Guardado", f"Proyecto JSON guardado con éxito:\n\n{out_path}")

    def open_json_dialog(self):
        path = filedialog.askopenfilename(
            initialdir=PROJECTS_DIR,
            title="Abrir Proyecto JSON",
            filetypes=[("Archivos JSON", "*.json")]
        )
        if path and os.path.exists(path):
            self.current_project = SpatialProject.load_json(path)
            self.total_duration_sec = max(1.0, self.current_project.total_duration(include_tail=True))
            self.selected_event_idx = 0
            self.selected_node_idx = 0
            self._sync_inspector_to_event()
            self.draw_scene()
            self._update_metrics_display()
            self.status_lbl.config(text=f"Abierto: {os.path.basename(path)}")

    def render_and_export_wav(self):
        if not self.current_project:
            return
        out_path = filedialog.asksaveasfilename(
            initialdir=OUTPUT_DIR,
            title="Exportar Audio WAV Espacial 8D",
            defaultextension=".wav",
            filetypes=[("Archivos WAV", "*.wav")]
        )
        if out_path:
            self.status_lbl.config(text="Renderizando master WAV...")
            self.root.update_idletasks()
            audio_data, metrics = render_project(self.current_project)
            export_wav(out_path, audio_data, metrics["sample_rate"])
            self._update_metrics_display(metrics)
            self.status_lbl.config(text=f"Exportado: {os.path.basename(out_path)}")
            messagebox.showinfo("Exportación Completada", f"Archivo WAV exportado exitosamente:\n\n{out_path}\n\nPeak: {metrics['peak_dbfs']} dBFS\nRMS: {metrics['rms_dbfs']} dBFS\nDuración: {metrics['duration_sec']} s")

def main():
    root = tk.Tk()
    app = SpatialStudioApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
