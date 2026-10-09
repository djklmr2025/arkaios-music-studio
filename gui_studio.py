"""
ARKAIOS Spatial Music Studio - Interfaz Gráfica Nativa de 5 Planos para Windows 11
Visualizador y editor interactivo con perspectiva tridimensional (fondo a frente),
nodos amarillos editables, transporte (Play/Stop/Pause), selector de pruebas y exportación WAV.
"""

import os
import sys
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

class SpatialStudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ARKAIOS Spatial Music Studio - 5 Planos 3D (Windows 11)")
        self.root.geometry("1100x750")
        self.root.configure(bg="#0b0a16")
        
        self.current_project = None
        self.current_wav_path = None
        self.selected_node_idx = None
        self.is_playing = False
        
        self._setup_styles()
        self._build_ui()
        
        # Cargar prueba 2 por defecto (Fondo a Frente)
        self.load_preset("test2_fondo_al_frente")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0b0a16", foreground="#d8d6f5", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#38e8ff")
        style.configure("Metrics.TLabel", font=("Consolas", 10), foreground="#ffc94d")

    def _build_ui(self):
        # 1. Cabecera
        header_frame = tk.Frame(self.root, bg="#121024", height=50)
        header_frame.pack(fill=tk.X, side=tk.TOP, padx=10, pady=6)
        
        title_lbl = tk.Label(header_frame, text="ARKAIOS · SPATIAL MUSIC COMPOSER (5 PLANOS)", bg="#121024", fg="#38e8ff", font=("Segoe UI", 14, "bold"))
        title_lbl.pack(side=tk.LEFT, padx=12, pady=8)
        
        sub_lbl = tk.Label(header_frame, text="Perspectiva Z: Fondo (1) → Frente (5) · Nodos Editables", bg="#121024", fg="#9a98c0", font=("Segoe UI", 10))
        sub_lbl.pack(side=tk.LEFT, padx=10)
        
        # 2. Contenedor Principal (Panel Izquierdo: Canvas 3D, Panel Derecho: Inspector)
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#0b0a16", sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
        
        # Left Panel: Canvas de los 5 Planos
        canvas_container = tk.Frame(main_paned, bg="#14122a", bd=1, relief=tk.SOLID)
        main_paned.add(canvas_container, minsize=650)
        
        self.canvas = tk.Canvas(canvas_container, bg="#0e0d1e", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.canvas.bind("<Configure>", lambda e: self.draw_scene())
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Right Panel: Inspector de Controles y Parámetros
        inspector_frame = tk.Frame(main_paned, bg="#14122a", width=380, padx=12, pady=10)
        main_paned.add(inspector_frame, minsize=320)
        
        # Presets selector
        tk.Label(inspector_frame, text="CARGAR PRESET DE PRUEBA:", bg="#14122a", fg="#ffc94d", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(4, 2))
        preset_btn_box = tk.Frame(inspector_frame, bg="#14122a")
        preset_btn_box.pack(fill=tk.X, pady=2)
        
        tk.Button(preset_btn_box, text="Prueba 1 (Fija)", bg="#221e45", fg="#ffffff", command=lambda: self.load_preset("test1_nota_fija")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(preset_btn_box, text="Prueba 2 (Viaje)", bg="#221e45", fg="#ffffff", command=lambda: self.load_preset("test2_fondo_al_frente")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(preset_btn_box, text="Prueba 3 (Triangular)", bg="#221e45", fg="#ffffff", command=lambda: self.load_preset("test3_apertura_triangular")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Propiedades del evento seleccionado
        tk.Label(inspector_frame, text="PARÁMETROS DEL EVENTO:", bg="#14122a", fg="#38e8ff", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(14, 4))
        
        self.lbl_pitch = tk.Label(inspector_frame, text="Tono MIDI: 60 (C4)", bg="#14122a", fg="#ffffff", font=("Segoe UI", 9))
        self.lbl_pitch.pack(anchor=tk.W)
        self.scale_pitch = tk.Scale(inspector_frame, from_=36, to_=84, orient=tk.HORIZONTAL, bg="#14122a", fg="#d8d6f5", highlightthickness=0, command=self.on_pitch_change)
        self.scale_pitch.set(60)
        self.scale_pitch.pack(fill=tk.X)
        
        self.lbl_volume = tk.Label(inspector_frame, text="Volumen Intrínseco: 0.80", bg="#14122a", fg="#ffffff", font=("Segoe UI", 9))
        self.lbl_volume.pack(anchor=tk.W)
        self.scale_volume = tk.Scale(inspector_frame, from_=0.1, to_=1.0, resolution=0.05, orient=tk.HORIZONTAL, bg="#14122a", fg="#d8d6f5", highlightthickness=0, command=self.on_volume_change)
        self.scale_volume.set(0.80)
        self.scale_volume.pack(fill=tk.X)
        
        # Modo de apertura triangular
        tk.Label(inspector_frame, text="Modo de Apertura Espacial:", bg="#14122a", fg="#d8d6f5", font=("Segoe UI", 9)).pack(anchor=tk.W, pady=(8, 2))
        self.width_mode_var = tk.StringVar(value="single_source_width")
        self.cmb_width = ttk.Combobox(inspector_frame, textvariable=self.width_mode_var, values=["single_source_width", "dual_source_split"], state="readonly")
        self.cmb_width.pack(fill=tk.X)
        self.cmb_width.bind("<<ComboboxSelected>>", self.on_mode_change)
        
        # Eco virtual (Sonar)
        self.echo_var = tk.BooleanVar(value=True)
        self.chk_echo = tk.Checkbutton(inspector_frame, text="Ecos Virtuales Activados (Emisión/Retorno)", variable=self.echo_var, bg="#14122a", fg="#38e8ff", selectcolor="#221e45", activebackground="#14122a", command=self.on_echo_toggle)
        self.chk_echo.pack(anchor=tk.W, pady=(10, 4))
        
        # Telemetría de ingeniería
        tk.Label(inspector_frame, text="MÉTRICAS ACÚSTICAS VERIFICADAS:", bg="#14122a", fg="#ffc94d", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(14, 2))
        self.lbl_metrics = tk.Label(inspector_frame, text="Peak: - dBFS | RMS: - dBFS\nDuración: - s | Saturación: No", bg="#0e0d1e", fg="#38e8ff", font=("Consolas", 9), justify=tk.LEFT, padx=8, pady=8, bd=1, relief=tk.RIDGE)
        self.lbl_metrics.pack(fill=tk.X, pady=4)
        
        # Botones de Acción (Guardar JSON / Exportar WAV)
        tk.Button(inspector_frame, text="💾 Guardar Proyecto JSON", bg="#2c2854", fg="#ffffff", font=("Segoe UI", 10, "bold"), command=self.save_current_json).pack(fill=tk.X, pady=(12, 4))
        tk.Button(inspector_frame, text="🎵 Renderizar & Exportar WAV", bg="#38e8ff", fg="#07060f", font=("Segoe UI", 10, "bold"), command=self.render_and_export_wav).pack(fill=tk.X, pady=4)
        
        # 3. Barra de Transporte Inferior (Play / Stop / Cargar)
        transport_frame = tk.Frame(self.root, bg="#121024", height=60)
        transport_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=6)
        
        self.btn_play = tk.Button(transport_frame, text="▶ REPRODUCIR", bg="#ff3df0", fg="#07060f", font=("Segoe UI", 11, "bold"), padx=16, command=self.play_audio)
        self.btn_play.pack(side=tk.LEFT, padx=8, pady=8)
        
        self.btn_stop = tk.Button(transport_frame, text="⏹ DETENER", bg="#3a3760", fg="#ffffff", font=("Segoe UI", 11), padx=12, command=self.stop_audio)
        self.btn_stop.pack(side=tk.LEFT, padx=4, pady=8)
        
        tk.Button(transport_frame, text="📂 Abrir JSON...", bg="#221e45", fg="#d8d6f5", command=self.open_json_dialog).pack(side=tk.LEFT, padx=12, pady=8)
        
        self.status_lbl = tk.Label(transport_frame, text="Listo.", bg="#121024", fg="#9a98c0", font=("Segoe UI", 10))
        self.status_lbl.pack(side=tk.RIGHT, padx=12)

    def draw_scene(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            return
            
        # Coordenadas de la perspectiva 3D (Túnel hacia el fondo)
        # Plano 1 (Fondo): y_min = h * 0.18, ancho estrecho
        # Plano 5 (Frente): y_max = h * 0.85, ancho completo
        top_y = h * 0.16
        bot_y = h * 0.84
        top_w_half = w * 0.22
        bot_w_half = w * 0.42
        center_x = w * 0.50
        
        # Líneas de fuga izquierda y derecha (marco del túnel 3D)
        self.canvas.create_line(center_x - top_w_half, top_y, center_x - bot_w_half, bot_y, fill="#2b2854", dash=(4, 4), width=1)
        self.canvas.create_line(center_x + top_w_half, top_y, center_x + bot_w_half, bot_y, fill="#2b2854", dash=(4, 4), width=1)
        
        # Etiquetas de Orientación
        self.canvas.create_text(center_x, top_y - 20, text="FONDO (Plano 1 - Más alejado)", fill="#7a78a6", font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(center_x, bot_y + 26, text="FRENTE (Plano 5 - Más cercano al oyente)", fill="#38e8ff", font=("Segoe UI", 10, "bold"))
        
        # Dibujar los 5 planos horizontales
        self.plane_coords = {}
        for p in range(1, 6):
            frac = (p - 1) / 4.0  # 0.0 en plano 1 (fondo), 1.0 en plano 5 (frente)
            py = top_y + frac * (bot_y - top_y)
            px_half = top_w_half + frac * (bot_w_half - top_w_half)
            x1 = center_x - px_half
            x2 = center_x + px_half
            self.plane_coords[p] = (py, x1, x2)
            
            # Línea del plano
            line_color = "#38e8ff" if p == 5 else ("#2b2854" if p == 1 else "#1f1d3d")
            line_w = 2 if p in (1, 5) else 1
            self.canvas.create_line(x1, py, x2, py, fill=line_color, width=line_w)
            
            # Etiqueta lateral del plano
            self.canvas.create_text(x2 + 28, py, text=f"Plano {p}", fill="#9a98c0", font=("Consolas", 9))
            
        # Dibujar eventos y nodos de la composición actual
        if not self.current_project or not self.current_project.events:
            return
            
        ev = self.current_project.events[0]
        nodes = ev.nodes
        if not nodes:
            return
            
        # Calcular coordenadas en pantalla para cada nodo
        self.node_screen_points = []
        for nd in nodes:
            # nd.depth: 1.0 a 5.0
            depth_frac = np.clip((nd.depth - 1.0) / 4.0, 0.0, 1.0)
            ny = top_y + depth_frac * (bot_y - top_y)
            nx_half = top_w_half + depth_frac * (bot_w_half - top_w_half)
            nx = center_x + nd.pan * nx_half
            self.node_screen_points.append((nx, ny, nd))
            
        # Si es modo de apertura triangular: dibujar la envolvente triangular
        if ev.trajectory_type == "triangular_aperture" and len(self.node_screen_points) >= 3:
            pts = self.node_screen_points
            mid_p = pts[1]
            depth_frac = np.clip((mid_p[2].depth - 1.0) / 4.0, 0.0, 1.0)
            nx_half = top_w_half + depth_frac * (bot_w_half - top_w_half)
            spread = mid_p[2].width * nx_half * 0.75
            
            # Polígono triangular de apertura
            triangle_pts = [
                pts[0][0], pts[0][1],
                mid_p[0] - spread, mid_p[1],
                pts[2][0], pts[2][1],
                mid_p[0] + spread, mid_p[1]
            ]
            self.canvas.create_polygon(triangle_pts, fill="#ff3df018", outline="#ff3df0", width=2, dash=(3, 3))
            
        # Dibujar líneas conectoras entre nodos (línea de duración del sonido)
        for i in range(len(self.node_screen_points) - 1):
            p0 = self.node_screen_points[i]
            p1 = self.node_screen_points[i + 1]
            self.canvas.create_line(p0[0], p0[1], p1[0], p1[1], fill="#38e8ff", width=3)
            
        # Dibujar los nodos amarillos (nodos temporales interactivos)
        for idx, (nx, ny, nd) in enumerate(self.node_screen_points):
            r = 7
            is_sel = (idx == self.selected_node_idx)
            fill_color = "#ffffff" if is_sel else "#ffc94d"
            outline_color = "#38e8ff" if is_sel else "#07060f"
            
            self.canvas.create_oval(nx - r, ny - r, nx + r, ny + r, fill=fill_color, outline=outline_color, width=2)
            # Etiqueta con el tiempo del nodo
            self.canvas.create_text(nx, ny - 14, text=f"{nd.t_offset:.2f}s", fill="#ffc94d", font=("Consolas", 8, "bold"))

    def on_canvas_click(self, event):
        # Detectar si se hizo clic en un nodo amarillo
        self.selected_node_idx = None
        for idx, (nx, ny, nd) in enumerate(self.node_screen_points):
            dist = np.hypot(event.x - nx, event.y - ny)
            if dist <= 12:
                self.selected_node_idx = idx
                self.draw_scene()
                return

    def on_canvas_drag(self, event):
        if self.selected_node_idx is None:
            return
            
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        top_y = h * 0.16
        bot_y = h * 0.84
        top_w_half = w * 0.22
        bot_w_half = w * 0.42
        center_x = w * 0.50
        
        # Mapear Y a depth (1.0 a 5.0)
        y_clamped = np.clip(event.y, top_y, bot_y)
        depth_frac = (y_clamped - top_y) / max(1.0, bot_y - top_y)
        new_depth = 1.0 + depth_frac * 4.0
        
        # Mapear X a pan (-1.0 a +1.0)
        nx_half = top_w_half + depth_frac * (bot_w_half - top_w_half)
        new_pan = np.clip((event.x - center_x) / max(1.0, nx_half), -1.0, 1.0)
        
        # Actualizar nodo
        nd = self.current_project.events[0].nodes[self.selected_node_idx]
        nd.depth = round(float(new_depth), 2)
        nd.pan = round(float(new_pan), 2)
        
        self.draw_scene()
        self.status_lbl.config(text=f"Nodo {self.selected_node_idx + 1}: Plano {nd.depth:.2f}, Pan {nd.pan:+.2f}")

    def on_canvas_release(self, event):
        pass

    def load_preset(self, preset_name):
        json_file = os.path.join(PROJECTS_DIR, f"{preset_name}.json")
        if not os.path.exists(json_file):
            from tests_run import run_tests
            run_tests()
            
        if os.path.exists(json_file):
            self.current_project = SpatialProject.load_json(json_file)
            wav_file = os.path.join(OUTPUT_DIR, f"{preset_name}.wav")
            self.current_wav_path = wav_file if os.path.exists(wav_file) else None
            
            # Sincronizar UI
            ev = self.current_project.events[0]
            self.scale_pitch.set(int(ev.pitch_start))
            self.scale_volume.set(ev.volume)
            self.width_mode_var.set(ev.width_mode)
            self.echo_var.set(ev.echo_enabled)
            
            self.draw_scene()
            self._update_metrics_display()
            self.status_lbl.config(text=f"Cargado: {self.current_project.name}")

    def _update_metrics_display(self):
        if not self.current_project:
            return
        _, metrics = render_project(self.current_project)
        text = (f"Peak: {metrics['peak_dbfs']} dBFS | RMS: {metrics['rms_dbfs']} dBFS\n"
                f"Duración: {metrics['duration_sec']} s | Saturación: {'SI' if metrics['is_saturated'] else 'No'}")
        self.lbl_metrics.config(text=text)

    def on_pitch_change(self, val):
        if self.current_project and self.current_project.events:
            p = float(val)
            self.current_project.events[0].pitch_start = p
            self.current_project.events[0].pitch_end = p
            self.lbl_pitch.config(text=f"Tono MIDI: {int(p)}")

    def on_volume_change(self, val):
        if self.current_project and self.current_project.events:
            v = float(val)
            self.current_project.events[0].volume = v
            self.lbl_volume.config(text=f"Volumen Intrínseco: {v:.2f}")

    def on_mode_change(self, event):
        if self.current_project and self.current_project.events:
            self.current_project.events[0].width_mode = self.width_mode_var.get()
            self.draw_scene()

    def on_echo_toggle(self):
        if self.current_project and self.current_project.events:
            self.current_project.events[0].echo_enabled = self.echo_var.get()

    def play_audio(self):
        if not self.current_project:
            return
        # Renderizar en memoria temporal o usar wav actual
        self.status_lbl.config(text="Renderizando y reproduciendo...")
        self.root.update_idletasks()
        
        temp_wav = os.path.join(OUTPUT_DIR, "live_preview.wav")
        audio_data, metrics = render_project(self.current_project)
        export_wav(temp_wav, audio_data, metrics["sample_rate"])
        self.current_wav_path = temp_wav
        self._update_metrics_display()
        
        # Reproducir de forma asíncrona mediante winsound
        winsound.PlaySound(temp_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
        self.is_playing = True
        self.status_lbl.config(text="▶ Reproduciendo audio espacial...")

    def stop_audio(self):
        winsound.PlaySound(None, winsound.SND_PURGE)
        self.is_playing = False
        self.status_lbl.config(text="⏹ Detenido.")

    def render_and_export_wav(self):
        if not self.current_project:
            return
        out_path = filedialog.asksaveasfilename(
            initialdir=OUTPUT_DIR,
            title="Exportar Audio WAV Espacial",
            defaultextension=".wav",
            filetypes=[("Archivos WAV", "*.wav")]
        )
        if out_path:
            audio_data, metrics = render_project(self.current_project)
            export_wav(out_path, audio_data)
            self._update_metrics_display()
            messagebox.showinfo("Exportación Completada", f"Archivo WAV exportado exitosamente:\n\n{out_path}\n\nPeak: {metrics['peak_dbfs']} dBFS\nRMS: {metrics['rms_dbfs']} dBFS")

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
            self.draw_scene()
            self._update_metrics_display()
            self.status_lbl.config(text=f"Abierto: {os.path.basename(path)}")

def main():
    root = tk.Tk()
    app = SpatialStudioApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

