"""
ARKAIOS Spatial Music Studio - Modelo de Datos y Proyectos
Especificación formal de eventos musicales con 5 planos de profundidad (1=Fondo, 5=Frente),
nodos temporales, trayectorias continuas, apertura triangular y ecos virtuales.
"""

import json
import os

class SpatialNode:
    """Nodo temporal que marca un instante de cambio en la trayectoria espacial."""
    def __init__(self, t_offset=0.0, depth=3.0, pan=0.0, width=0.0):
        self.t_offset = float(t_offset)      # Tiempo relativo dentro del evento (s)
        self.depth = float(depth)            # Plano 1 (fondo) a 5 (frente)
        self.pan = float(pan)                # -1.0 (izq) a +1.0 (der)
        self.width = float(width)            # 0.0 (puntual) a 1.0 (máxima apertura)

    def to_dict(self):
        return {
            "t_offset": round(self.t_offset, 4),
            "depth": round(self.depth, 2),
            "pan": round(self.pan, 2),
            "width": round(self.width, 2)
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            t_offset=data.get("t_offset", 0.0),
            depth=data.get("depth", 3.0),
            pan=data.get("pan", 0.0),
            width=data.get("width", 0.0)
        )

class SpatialEvent:
    """Evento sonoro con duración, tono, volumen, trayectoria y acústica espacial."""
    def __init__(self,
                 id="event_1",
                 name="Nota Espacial",
                 time_start=0.0,
                 duration=1.0,
                 pitch_start=60.0,
                 pitch_end=60.0,
                 volume=0.8,
                 waveform="sine",
                 trajectory_type="depth_sweep",
                 width_mode="single_source_width",
                 nodes=None,
                 echo_enabled=False,
                 echo_delay_ms=80.0,
                 echo_feedback=0.25,
                 echo_damping_hz=3500.0):
        self.id = str(id)
        self.name = str(name)
        self.time_start = float(time_start)
        self.duration = float(duration)
        self.pitch_start = float(pitch_start)
        self.pitch_end = float(pitch_end)
        self.volume = float(volume)
        self.waveform = str(waveform)  # sine, triangle, warm_saw, flute
        self.trajectory_type = str(trajectory_type)  # static, depth_sweep, triangular_aperture, curve
        self.width_mode = str(width_mode)  # single_source_width, dual_source_split
        self.nodes = nodes if nodes is not None else []
        self.echo_enabled = bool(echo_enabled)
        self.echo_delay_ms = float(echo_delay_ms)
        self.echo_feedback = float(echo_feedback)
        self.echo_damping_hz = float(echo_damping_hz)

    def add_node(self, node):
        self.nodes.append(node)
        self.nodes.sort(key=lambda n: n.t_offset)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "time_start": round(self.time_start, 4),
            "duration": round(self.duration, 4),
            "pitch_start": round(self.pitch_start, 2),
            "pitch_end": round(self.pitch_end, 2),
            "volume": round(self.volume, 3),
            "waveform": self.waveform,
            "trajectory_type": self.trajectory_type,
            "width_mode": self.width_mode,
            "nodes": [n.to_dict() for n in self.nodes],
            "echoes": {
                "enabled": self.echo_enabled,
                "delay_ms": round(self.echo_delay_ms, 2),
                "feedback": round(self.echo_feedback, 3),
                "damping_hz": round(self.echo_damping_hz, 1)
            }
        }

    @classmethod
    def from_dict(cls, data):
        raw_nodes = data.get("nodes", [])
        nodes = [SpatialNode.from_dict(nd) for nd in raw_nodes]
        echoes = data.get("echoes", {})
        return cls(
            id=data.get("id", "event_1"),
            name=data.get("name", "Nota Espacial"),
            time_start=data.get("time_start", 0.0),
            duration=data.get("duration", 1.0),
            pitch_start=data.get("pitch_start", 60.0),
            pitch_end=data.get("pitch_end", 60.0),
            volume=data.get("volume", 0.8),
            waveform=data.get("waveform", "sine"),
            trajectory_type=data.get("trajectory_type", "depth_sweep"),
            width_mode=data.get("width_mode", "single_source_width"),
            nodes=nodes,
            echo_enabled=echoes.get("enabled", False),
            echo_delay_ms=echoes.get("delay_ms", 80.0),
            echo_feedback=echoes.get("feedback", 0.25),
            echo_damping_hz=echoes.get("damping_hz", 3500.0)
        )

class SpatialProject:
    """Proyecto completo editable que preserva objetos, trayectorias y parámetros acústicos."""
    def __init__(self, name="ARKAIOS Spatial Composition", bpm=80.0, seed=42):
        self.name = str(name)
        self.version = "1.0"
        self.bpm = float(bpm)
        self.seed = int(seed)
        self.depth_planes = 5
        self.sample_rate = 44100
        self.events = []

    def add_event(self, event):
        self.events.append(event)
        self.events.sort(key=lambda e: e.time_start)

    def total_duration(self):
        if not self.events:
            return 0.0
        return max(e.time_start + e.duration for e in self.events)

    def to_dict(self):
        return {
            "$schema": "https://arkaios.org/schemas/spatial-music-project.v1.json",
            "name": self.name,
            "version": self.version,
            "bpm": self.bpm,
            "seed": self.seed,
            "depth_planes": self.depth_planes,
            "sample_rate": self.sample_rate,
            "events": [e.to_dict() for e in self.events]
        }

    def save_json(self, filepath):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return filepath

    @classmethod
    def load_json(cls, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        proj = cls(
            name=data.get("name", "ARKAIOS Spatial Composition"),
            bpm=data.get("bpm", 80.0),
            seed=data.get("seed", 42)
        )
        proj.version = data.get("version", "1.0")
        proj.depth_planes = data.get("depth_planes", 5)
        proj.sample_rate = data.get("sample_rate", 44100)
        for ev_data in data.get("events", []):
            proj.add_event(SpatialEvent.from_dict(ev_data))
        return proj
