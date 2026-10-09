# ARKAIOS Spatial Music Studio (5 Planos 3D) 🎵🌌

> **Motor y especificación de composición musical espacial orientada a objetos en 5 planos de profundidad, apertura geométrica triangular y acústica binaural.**  
> Diseñado para ejecución humana y colaboración autónoma entre agentes de Inteligencia Artificial (**Gemini, Claude, ChatGPT / Codex y agentes autónomos**).

---

## 🏛️ Filosofía del Proyecto

Este repositorio implementa un modelo de composición sonora donde la música no se concibe como un plano bidimensional estático, sino como un **espacio acústico tridimensional con cinco planos de profundidad**:

* **Plano 1 (Fondo):** Distancia aparente máxima, mayor absorción de altas frecuencias (filtro de aire ~3.2 kHz) y predominio de reflexiones/ecos difusos.
* **Plano 2 al 4:** Planos intermedios de transición y desplazamiento continuo.
* **Plano 5 (Frente):** Máxima cercanía al oyente, presencia directa y brillo espectral completo (~16.0 kHz).

Cada evento musical separa de forma independiente:
1. **Tiempo y Duración**: Línea de tiempo y longitud del sonido.
2. **Nodos Temporales (Amarillos)**: Instantes de inflexión en posición y anchura.
3. **Tono**: Frecuencia inicial y final (soporta notas fijas, microtonos y *pitch glides* continuos).
4. **Volumen Intrínseco**: Nivel intrínseco desacoplado de la distancia.
5. **Apertura Triangular**:
   - `single_source_width`: Una fuente cuya presencia se expande y contrae en el campo estéreo.
   - `dual_source_split`: Dos voces que divergen hacia los laterales y vuelven a converger en el centro.
6. **Ecos Virtuales**: Simulación de reflexiones inspirada en el sonar / ecolocalización (tiempo de retardo de ida y vuelta, retroalimentación y filtrado).

---

## 🤖 Guía de Colaboración para Agentes de IA (Multi-Agent Protocol)

Este repositorio está preparado para que **agentes de diferentes arquitecturas** puedan leer, ejecutar, componer y colaborar de forma asíncrona:

```
                  ┌───────────────────────┐
                  │    Human Composer     │
                  └───────────┬───────────┘
                              │
     ┌────────────────────────┼────────────────────────┐
     ▼                        ▼                        ▼
┌─────────┐              ┌─────────┐              ┌─────────┐
│ Gemini  │              │ Claude  │              │ ChatGPT │
│ (Agent) │              │ (Agent) │              │ / Codex │
└────┬────┘              └────┬────┘              └────┬────┘
     │                        │                        │
     └────────────────►───────┼───────◄────────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │  projects/*.json        │
                 │  (Esquema Validado)     │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ engine/spatial_renderer │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ output/*.wav (320kbps)  │
                 └─────────────────────────┘
```

### 1. Rol de Cada Agente
* **ChatGPT / OpenAI Codex**: Ideación matemática, matrices de acordes microtonales, diseño de geometrías de apertura y scripting de automatización.
* **Gemini (Antigravity)**: Orquestación del sistema en el entorno local/workspace, ejecución de pruebas de ingeniería, verificación acústica y mantenimiento del árbol de código.
* **Claude (Anthropic)**: Auditoría de código, revisión de análisis espectral, balance de niveles RMS y documentación de arquitectura.
* **Agentes Autónomos CI/CD**: Ejecución de la batería de pruebas en GitHub Actions ante cada Pull Request para validar que no haya saturación ni valores `NaN`.

---

## 📐 Especificación del Formato de Proyecto JSON

Cualquier agente o programa que desee generar una composición debe emitir un archivo `.json` en el directorio `projects/` cumpliendo con el siguiente esquema:

```json
{
  "$schema": "https://arkaios.org/schemas/spatial-music-project.v1.json",
  "name": "Título de la Obra",
  "version": "1.0",
  "bpm": 80.0,
  "seed": 42,
  "depth_planes": 5,
  "sample_rate": 44100,
  "events": [
    {
      "id": "ev_01",
      "name": "Pad Espacial Líquido",
      "time_start": 0.0,
      "duration": 2.5,
      "pitch_start": 60.0,
      "pitch_end": 64.0,
      "volume": 0.8,
      "waveform": "warm_saw",
      "trajectory_type": "depth_sweep",
      "width_mode": "single_source_width",
      "nodes": [
        {"t_offset": 0.0, "depth": 1.0, "pan": -0.5, "width": 0.0},
        {"t_offset": 1.25, "depth": 3.0, "pan": 0.0, "width": 0.8},
        {"t_offset": 2.5, "depth": 5.0, "pan": 0.5, "width": 0.0}
      ],
      "echoes": {
        "enabled": true,
        "delay_ms": 110.0,
        "feedback": 0.22,
        "damping_hz": 3200.0
      }
    }
  ]
}
```

---

## 🚀 Uso y Operación

### Requisitos
- Windows 11 o Linux / macOS
- Python 3.10+ con librerías: `numpy`, `scipy`, `mido`

### Iniciar la Interfaz Gráfica (Windows 11)
Haz doble clic en:
```
iniciar_studio.bat
```
O desde la terminal:
```bash
python gui_studio.py
```

### Ejecutar Batería de Pruebas de Ingeniería (Headless)
```bash
python tests_run.py
```

Salida esperada:
* `test1_nota_fija.wav`: Referencia estática (Plano 3).
* `test2_fondo_al_frente.wav`: Trayectoria continua Plano 1 $\rightarrow$ Plano 5.
* `test3_apertura_triangular.wav`: Modo `dual_source_split` con apertura a 2 voces y convergencia a 1 punto.

---

## 🔒 Seguridad y Política de Tokens para Agentes (PATs & Bots)

### ⚠️ Regla de Seguridad de la API de GitHub sobre PATs:
Por diseño de seguridad estricto, **GitHub NO permite generar un nuevo Personal Access Token (PAT) utilizando otro PAT a través de su API**. Esto evita que si un token se ve comprometido, un atacante o script pueda generar tokens infinitos o escalar privilegios.

### Cómo habilitar acceso seguro para Agentes Colaboradores:
1. **Opción A (Recomendada - GitHub Actions `GITHUB_TOKEN`):**
   - Configurar un flujo de trabajo en `.github/workflows/agent-pipeline.yml`.
   - GitHub proporciona automáticamente un token efímero con permisos estrictos para ejecutar pruebas, generar releases de audio y responder a Pull Requests sin almacenar tokens permanentes.
2. **Opción B (Fine-Grained Personal Access Token):**
   - El administrador humano puede generar un token secundario limitado en [github.com/settings/tokens](https://github.com/settings/tokens?type=beta).
   - **Permisos restringidos sugeridos:**
     - `Repository access`: Solo `arkaios-music-studio`.
     - `Contents`: Read & Write.
     - `Pull requests`: Read & Write.
     - `Metadata`: Read-only.
   - Con este token, cualquier agente secundario puede clonar, crear ramas (`feature/nuevo-algoritmo`) y abrir PRs sin tener acceso al resto de tu cuenta de GitHub.

---

## 📄 Licencia y Reconocimientos
Desarrollado dentro del ecosistema **ARKAIOS**.  
Inspirado conceptualmente en la percepción auditiva y háptica por vías alternativas y en las analogías de propagación/retorno acústico del sonar biológico.
