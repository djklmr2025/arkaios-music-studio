# ARKAIOS Spatial Music Studio (5 Planos 3D) 🎵🌌

> **Motor y especificación de composición musical espacial orientada a objetos en 5 planos de profundidad, apertura geométrica triangular y aproximación espacial estéreo.**  
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
                 │  (Validación del motor)     │
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
   - Configurar un flujo de trabajo en `.github/workflows/agent-ci.yml`.
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



## Actualización de Codex - 08/10/2026

### Correcciones implementadas
- Profundidad interpolada por muestra: el filtro y la relación directo/eco cambian durante el recorrido; se elimina el promedio que hacía casi iguales la nota fija y la móvil.
- Retardos interaurales fraccionales causales por fuente, de hasta 0,65 ms. No se utiliza un conjunto HRTF medido.
- `single_source_width`: componente lateral basada en una copia retardada, para crear diferencias entre canales.
- `dual_source_split`: segunda voz con desafinación de 0,07 semitonos, posicionada separadamente. Ambos timbres permanecen al reunirse.
- Ecos filtrados: primer retorno después del retardo solicitado y cola de hasta 0,5 s. Las repeticiones se limitan a 128 y a la longitud disponible; no es reverberación física completa.
- Corrección de frecuencia cuando se renderiza a 48 kHz, validación de parámetros finitos/rangos/orden de nodos y métricas RMS calculadas después de controlar el pico.
- Comando de renderizado de proyectos JSON y dependencias declaradas en `requirements.txt`.
- Lanzador con entorno `.venv` dentro del repositorio; detiene el arranque si falla instalación o pruebas. Requiere Python 3 y el lanzador `py` en Windows.
- CI usa las mismas dependencias y permisos de lectura. Las pruebas ahora fallan ante regresiones en lugar de imprimir éxito incondicionalmente.

### Uso para agentes
```bash
python -m pip install -r requirements.txt
python tests_run.py
python studio.py render --project projects/test2_fondo_al_frente.json --output output/mi_recorrido.wav
```
El comando respeta `sample_rate` del proyecto. El motor no necesita un PAT para generar audio; `.env.example` documenta una variable para herramientas externas de colaboración, no una conexión automática entre agentes.

### Verificación y límites
Se ejecutaron las tres pruebas y comprobaciones de profundidad, anchura, separación de voces, eco causal, cola audible en muestras, tono de 440 Hz a 48 kHz y rechazo de parámetros inválidos. Los WAV son finitos y sin saturación en los ejemplos. La igualdad RMS no acredita igualdad perceptual: la apertura triangular puede cambiar el nivel y requiere comparación de escucha.

La interfaz Tkinter/winsound y el lanzador deben verificarse en Windows 11; no se han ejecutado en este entorno Linux. Hay reproducción y parada, pero todavía no pausa. La GUI edita principalmente el primer evento y no es aún un secuenciador multipista completo. `trajectory_type` es una etiqueta: el movimiento lo definen los nodos y su interpolación lineal; no hay generador de curvas circulares o Bézier. No hay elevación acústica, HRTF medida, salida háptica ni garantía de localización frontal/posterior. `seed` se conserva como metadato en proyectos espaciales, sin generación aleatoria asociada. El sintetizador antiguo y su MIDI requieren una auditoría adicional; estas correcciones corresponden al motor por objetos.

GitHub Actions puede fallar por condiciones de la cuenta o infraestructura antes de ejecutar pasos. Un workflow publicado no demuestra que una ejecución haya pasado. `.gitignore` no elimina secretos ya versionados y no prueba el estado del `.env` de una computadora.

---

## Actualización de Validación en Windows 11 (Gemini) - 08/10/2026

### Qué cambió
1. **`iniciar_studio.bat`**: Detección inteligente y tolerante a fallos de Python 3.10+ en Windows 11. Se evalúa `py -3`, luego `python` en `%PATH%` (filtrando stubs del Microsoft Store), y finalmente rutas directas estándar (`C:\Python314\python.exe`, `C:\Python313\python.exe`, `%LOCALAPPDATA%\Programs\Python\...`, `%ProgramFiles%\Python...`).
2. **`gui_studio.py`**: En `render_and_export_wav`, se pasa explícitamente `metrics["sample_rate"]` a `export_wav` para garantizar consistencia con proyectos a 48 kHz u otras frecuencias de muestreo.

### Por qué
1. En Windows 11, el comando `py` falló con `"py" no se reconoce como un comando interno o externo...` debido a que el lanzador opcional `py.exe` no siempre está en el `%PATH%` cuando Python se instala en directorios como `C:\Python314`. La búsqueda directa asegura que cualquier usuario en Windows 11 pueda arrancar el estudio con un doble clic sin configuraciones manuales.
2. La exportación manual desde la GUI mantenía el `sample_rate` estático de 44.1 kHz, ignorando si el proyecto requería 48 kHz.

### Pruebas ejecutadas
1. **Lanzador**: Ejecución de `iniciar_studio.bat` con validación de detección de intérprete y paso de dependencias.
2. **Entorno y Dependencias**: Instalación correcta de `requirements.txt` (`numpy 2.5.3`, `scipy 1.18.1`, `mido 1.3.3`) en `.venv`.
3. **Batería de Pruebas Acústicas**: `.venv\Scripts\python.exe tests_run.py` ejecutado al 100% de éxito:
   - Prueba 1 (Nota Fija): Peak -8.65 dBFS, RMS -18.49 dBFS, 0 NaNs, Sin Saturación.
   - Prueba 2 (Fondo a Frente): Peak -8.62 dBFS, RMS -18.75 dBFS, 0 NaNs, Sin Saturación.
   - Prueba 3 (Apertura Triangular): Peak -8.95 dBFS, RMS -20.48 dBFS, 0 NaNs, Sin Saturación.
   - Regresiones verificadas: variación dinámica de profundidad, separación de voces duales, descorrelación estéreo, causalidad de eco (retardo > 0), persistencia de cola audible, preservación de frecuencia a 48 kHz y rechazo de eventos inválidos.
4. **Comando de Renderizado CLI**:
   `.venv\Scripts\python.exe studio.py render --project projects/test2_fondo_al_frente.json --output output/prueba_windows.wav`
   Completado con éxito (duración 1.5s, 264.644 bytes generados).
5. **Auditoría de GUI**:
   Pruebas de ciclo de vida completas: carga de los 3 presets, movimiento de nodos amarillos (profundidad/paneo), alteración de tono y volumen, reproducción asíncrona y parada vía `winsound`, guardado de JSON, reapertura con conservación de cambios y exportación a WAV.
6. **Auditoría de GitHub Actions para commit `5d85b02`**:
   Se consultó la API de GitHub Actions (Run `37880839401`). El fallo se identificó como **problema de infraestructura/cuenta**, no de código: `"The job was not started because your account is locked due to a billing issue."`.

### Qué sigue pendiente
1. **Evaluación Perceptual Humana**: Se requiere escucha crítica binaural con auriculares por parte del usuario para validar si el gradiente de filtrado y retardo se percibe de forma convincente como profundidad tridimensional.
2. **Función de Pausa en Transporte**: Actualmente la GUI implementa Reproducir (`winsound.PlaySound`) y Detener (`winsound.SND_PURGE`); `winsound` nativo no soporta pausa/reanudación sin librerías externas de audio (p.ej. `sounddevice` o `pygame`).
3. **Editor Multipista**: Resuelto en la actualización a continuación.

---

## Actualización de Secuenciador Vectorial LINES 8D - 08/10/2026

### Transformación de la Interfaz a Secuenciador Polifónico Vectorial
Basado en la referencia técnica de `Musica creada en 8D.mp4` (LINES):
1. **Teclado Piano Vertical Activo**:
   - Piano en el lateral izquierdo con teclas sensibles a la afinación (C2 a C6).
   - Retroalimentación luminosa dinámica: las teclas se encienden en tiempo real con resplandor neón magenta/cian conforme el playhead recorre las notas activas.
2. **Línea de Tiempo Polifónica Multivoz**:
   - Rejilla continua de compases (Bars) calculada dinámicamente según el tempo (BPM).
   - **Playhead Dorado en Tiempo Real**: línea vertical móvil sincronizada a 30 FPS con el motor de audio `winsound`.
   - **Ribbons Vectoriales Translúcidos**: cada voz dibuja su cinta de grosor proporcional al volumen y apertura estéreo, permitiendo visualizar acordes masivos que se deslizan libremente (*microtonal glissando*).
3. **Herramientas de Composición Interactiva**:
   - Modo `Seleccionar (S)`: arrastre intuitivo de nodos en tiempo y afinación.
   - Modo `Dibujar (D)`: creación rápida de nuevas líneas vectoriales con un clic sobre el lienzo.
   - `Nueva Voz` / `Borrar Voz`: control de polifonía arbitraria (más de 50 voces simultáneas).
4. **Obra Maestra LINES 8D**:
   - Se incluyó el generador y proyecto [`projects/lines_8d_masterpiece.json`](file:///c:/ARKAIOS/arkaios-music-studio/projects/lines_8d_masterpiece.json) (57 eventos, 28.5 s), que replica fielmente la progresión demostrada:
     - *Fase 1*: Pad cósmico de 8 voces con micro-glissando y apertura triangular.
     - *Fase 2*: Gran convergencia gravitacional de todas las voces hacia un punto central.
     - *Fase 3*: Cascada de arpegios ascendentes y descendentes con ecos sonar 8D.
     - *Fase 4*: Acorde resonante final que se desvanece en el fondo (Plano 1).

### Pruebas Realizadas
- [x] Ejecución de `tests_run.py` (100% de regresiones y pruebas de ingeniería superadas).
- [x] Generación y renderizado de `lines_8d_masterpiece.wav` (29.0s, Peak -2.24 dBFS, RMS -16.62 dBFS, 0 NaNs).
- [x] Validación de la GUI: adición de voces, eliminación, dibujo, selección, reproducción con playhead y exportación WAV.

---

## Actualización de Curvas Multinodo, Atenuación 1/d y Edición No Destructiva - 09/10/2026

### Qué se implementó y publicó
1. **Afinación Independiente por Nodo (Glissando Multipunto Arbitrario)**:
   - `SpatialNode` ahora soporta el atributo opcional `pitch` (0-127).
   - `render_spatial_event` interpola continuamente las frecuencias en el tiempo (`np.interp(t, node_times, node_pitches)`), permitiendo trayectorias tonales microtonales y curvas complejas dentro de un mismo evento continuo.
2. **Sincronización Total del Transporte y Colas de Eco**:
   - `SpatialProject.total_duration(include_tail=True)` incluye la cola acústica de reverberación/eco (+0.5 s).
   - El bucle de animación a 30 FPS del cursor (`_animate_playhead`) y la línea de tiempo de la GUI usan esta duración exacta, evitando que la animación termine antes de que expire la cola sonora.
3. **Atenuación Física por Ley Inversa de Distancia $1/d$**:
   - Se formalizó la atenuación geométrica en `engine/spatial_renderer.py` calculando $d = 1.5 - 0.5 \cdot z$ ($d_{ref}=1.0$ al frente en Plano 5, $d_{far}=1.5$ al fondo en Plano 1), con factor de amplitud proporcional a $1/d$, combinado con la absorción en altas frecuencias por distancia.
4. **Protección de Inspector y Edición No Destructiva**:
   - Se incorporó la bandera `_updating_inspector` para evitar que la selección de una voz dispare eventos de deslizadores que aplanen las notas.
   - El cambio de tono en el inspector aplica un desplazamiento diferencial (`delta`) que preserva la pendiente de los glissandos en lugar de sobrescribir el inicio y el final con el mismo valor.
5. **Atajos de Teclado y Flujo de LINES**:
   - **Tecla `D`**: Alternar entre herramienta de selección (`Select`) y lápiz continuo (`Draw`).
   - **Tecla `S`**: Seleccionar herramienta de cursor.
   - **Doble Clic**: Insertar un punto de control de curvatura (*bend point*) en la posición exacta del evento.
   - **Flechas `<Up>` / `<Down>`**: Transponer el nodo o evento seleccionado por semitonos individuales; `<Shift-Up>` / `<Shift-Down>` transpone por octavas completas (12 semitonos).
   - **Dibujo Continuo (*Freehand Pencil*)**: En modo `Draw`, arrastrar el ratón genera múltiples nodos a lo largo de la trayectoria.
6. **Pruebas de Regresión Ampliadas**:
   - Verificación automatizada de renderizado con curvas multinodo y validación estricta de tonos en `tests_run.py` (10 suites, 100% éxito).

---

## Actualización de Invariantes de Edición en GUI y Robustez en Windows - 09/10/2026

### Mejoras Realizadas en Respuesta a la Auditoría de ChatGPT
1. **Selección Precisa de Voces Intermedias**:
   - `SpatialProject.add_event` inserta los eventos ordenados cronológicamente por `time_start`. Anteriormente, la GUI asumía que el nuevo evento quedaba en `len(events) - 1`.
   - Se corrigió tanto en `on_canvas_click` (dibujo) como en `add_new_voice` para usar `self.current_project.events.index(new_ev)`, asegurando que al dibujar o agregar una voz entre eventos existentes, la voz seleccionada e inspeccionada sea **exactamente la voz recién creada**, sin alterar eventos vecinos.
2. **Confinamiento Temporal de Nodos Arrastrados (Prevención de Cruce Temporal)**:
   - Al arrastrar un nodo intermedio, su tiempo se confina estrictamente entre sus vecinos adyacentes: `nodes[i-1].t_offset + 0.02` y `nodes[i+1].t_offset - 0.02`.
   - El nodo inicial queda delimitado antes del segundo nodo, y el nodo final controla dinámicamente la duración total del evento sin invertir la trayectoria.
   - En `on_canvas_release`, se realiza una pasada de desduplicación y garantía de monotonicidad temporal estricta para cumplir con los requisitos del motor de síntesis.
3. **Batería de Pruebas Automatizadas de Invariantes**:
   - Se añadió `verify_gui_editing_invariants()` a `tests_run.py`, validando:
     - Inserción ordenada y resolución de índice de voces intermedias.
     - Confinamiento temporal de nodos ante arrastres extremos sin inversión de trayectoria.
     - Precisión exacta (+0.5 s) de duración con cola de reverberación/eco.


