# Estándares Técnicos para Modding de Assetto Corsa

Este documento recopila las especificaciones técnicas obligatorias y las mejores prácticas de la comunidad de Assetto Corsa (Kunos Simulazioni SDK, guías de LilSki, Custom Shaders Patch). Cualquier módulo del addon debe cumplir estas reglas.

---

## 1. Nomenclatura y Prioridad de Mallas Físicas

En Assetto Corsa, el motor físico detecta las colisiones y las características del suelo analizando el **nombre del objeto 3D**. Los prefijos numéricos determinan el canal físico:

| Prefijo de Malla | Tipo de Superficie | Función en Simulación | Referencia en `surfaces.ini` |
| :--- | :--- | :--- | :--- |
| `1ROAD_xxx` | Asfalto principal | Conducción principal, agarre 0.98 - 1.0, zona válida de pista | `KEY=ROAD` |
| `2ROAD_xxx` | Asfalto secundario | Pistas auxiliares, accesos o asfalto desgastado | `KEY=ROAD` |
| `1KERB_xxx` | Pianos / Bordillos | Bordillos y pianos, respuesta háptica con vibración FFB | `KEY=KERB` |
| `1GRASS_xxx` | Hierba / Césped | Escapatorias, baja adherencia, baches continuos | `KEY=GRASS` |
| `1SAND_xxx` | Arena / Puzolana | Zonas de deceleración rápida, alta resistencia de rodadura | `KEY=SAND` |
| `1WALL_xxx` | Muros / Barreras | Guardarraíles, muros de hormigón, vallas (colisión rígida) | Colisión estricta |
| `1PIT_xxx` | Carril de boxes | Asfalto de la zona de pitlane | `KEY=PIT` |

> [!IMPORTANT]
> **La Regla de Oro (Separación Visual vs Física)**:
> Nunca se debe asignar el prefijo `1ROAD_` a la malla visual de alta resolución gráfica.
> * **Malla Visual (`ROAD_...`)**: Contiene shaders avanzados, texturas multicapa, mapas de normales y parches estéticos. No tiene prefijo numérico de colisión.
> * **Malla Física (`1ROAD_...`)**: Es invisible (o con material transparente/básico) y se coloca ligeramente oculta o coincidente. Debe tener una **subdivisión longitudinal uniforme (entre 0.2m y 0.5m)** en el sentido de la marcha para alimentar el modelo de neumáticos y Force Feedback sin saltos.

---

## 2. Nodos de Carrera Obligatorios (Race Nodes)

Assetto Corsa requiere objetos vacíos (`Empties`) con nombres y orientaciones precisas. **Si faltan estos objetos, el circuito crasheará o no cargará.**

### 2.1. Puntos de Salida y Posicionamiento
* **`AC_START_0`, `AC_START_1`, ... `AC_START_N`**:
  * Posiciones de la parrilla de salida.
  * Deben colocarse aproximadamente a 0.1m - 0.2m sobre el asfalto.
  * La orientación local en Blender debe apuntar hacia el frente de la pista (dirección de carrera).
  * Convención: `AC_START_0` es la Pole Position.
* **`AC_PIT_0`, `AC_PIT_1`, ... `AC_PIT_N`**:
  * Puestos de parada en boxes para cada coche.
  * Deben alinearse en el pitlane con espacio suficiente para que el coche maniobre.
* **`AC_HOTLAP_START_0`**:
  * Punto de reaparición para el modo contrarreloj (Hotlap).
  * Debe situarse unos 100-200 metros antes de la línea de meta, en plena recta y en sentido de carrera, para que el coche inicie lanzado a velocidad adecuada.

### 2.2. Puertas de Cronometraje (Timing Gates)
Las puertas de cronometraje son pares de objetos vacíos (Izquierda y Derecha) que trazan una línea invisible perpendicular a la pista:
* **Circuito Cerrado**:
  * `AC_TIME_0_L` y `AC_TIME_0_R`: Línea de Meta y Salida.
  * `AC_TIME_1_L` y `AC_TIME_1_R`: Sector 1.
  * `AC_TIME_2_L` y `AC_TIME_2_R`: Sector 2.
* **Tramo Punto a Punto (Hillclimbs / Rally A a B)**:
  * `AC_AB_START_L` y `AC_AB_START_R`: Línea de salida del tramo.
  * `AC_AB_FINISH_L` y `AC_AB_FINISH_R`: Línea de meta del tramo.

---

## 3. Archivos de Configuración del Circuito

Un mod de pista completo para Assetto Corsa requiere la siguiente jerarquía de archivos:

```text
content/tracks/<nombre_pista>/
├── <nombre_pista>.kn5            # Malla 3D compilada por ksEditor
├── models.ini                    # Definición de modelos .kn5 cargados
├── surfaces.ini                  # Propiedades físicas de las superficies
├── map.ini                       # Configuración matemática del minimapa
├── map.png                       # Imagen 2D del minimapa
├── ui/
│   ├── ui_track.json             # Metadatos del circuito (nombre, país, etc.)
│   ├── preview.png               # Imagen de vista previa (1920x1080)
│   └── outline.png               # Trazado vectorial blanco con fondo transparente
├── data/
│   └── surfaces.ini              # (Ubicación alternativa leída por AC)
└── extension/
    └── ext_config.ini            # Configuración de Custom Shaders Patch (CSP)
```

### 3.1. Estructura de `surfaces.ini`
Define la física de cada superficie según su clave (`KEY`):

```ini
[SURFACE_0]
KEY=ROAD
FRICTION=0.98
DAMPING=0
WAV_PITCH=0
FF_EFFECT=NULL
DIRT_ADD=0
IS_VALID_TRACK=1
BLACK_FLAG_TIME=0
SIN_HEIGHT=0
SIN_LENGTH=0
IS_PITLANE=0
VIBRATION_GAIN=0
VIBRATION_LENGTH=0

[SURFACE_1]
KEY=KERB
FRICTION=0.92
DAMPING=0
WAV_PITCH=0
FF_EFFECT=NULL
DIRT_ADD=0
IS_VALID_TRACK=1
BLACK_FLAG_TIME=0
SIN_HEIGHT=0.005
SIN_LENGTH=0.15
IS_PITLANE=0
VIBRATION_GAIN=0.2
VIBRATION_LENGTH=0.2

[SURFACE_2]
KEY=GRASS
FRICTION=0.55
DAMPING=0.1
WAV_PITCH=0
FF_EFFECT=NULL
DIRT_ADD=0.05
IS_VALID_TRACK=0
BLACK_FLAG_TIME=5
SIN_HEIGHT=0.03
SIN_LENGTH=0.5
IS_PITLANE=0
```

---

## 4. Estándares de Shaders y Texturas

* **Formato de Texturas:** Todas las texturas deben exportarse en formato **DDS** (DirectDraw Surface) con MipMaps generados obligatoriamente:
  * `BC1 / DXT1`: Para texturas sin transparencia (asfalto, terrenos, muros).
  * `BC3 / DXT5`: Para texturas con transparencia suave o alfa (marcas viales, árboles, vallas).
  * `BC7`: Para texturas de alta calidad moderna con Custom Shaders Patch.
* **Shaders de Kunos:**
  * `ksPerPixelMultiMap_emissive`: El shader rey para asfalto. Permite mapa difuso, mapa de normales y mapa multicanal (R: detalle, G: suciedad/huella, B: reflexión especular).
  * `ksTree`: Shader para vegetación con iluminación esférica suave.
