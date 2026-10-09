# Roadmap del Proyecto: Track Maker

Este documento define el estado actual, las fases de desarrollo planificadas y el registro de avances del proyecto. Cualquier agente de IA debe actualizar este archivo al completar hitos o redefinir prioridades.

---

## 🧭 Estado Actual del Proyecto
* **Estado General:** **¡Núcleo Completo (Fases 1, 2, 3 y 4 Implementadas y Verificadas)!**
* **Capacidades Operativas:**
  1. Generación de todos los Race Nodes de Assetto Corsa (`AC_START_`, `AC_PIT_`, `AC_HOTLAP_`, `AC_TIME_`).
  2. Generador de Carreteras Procedurales con Geometry Nodes y división estricta Malla Visual vs Malla Física (`1ROAD_`).
  3. Georreferenciación y origen local anti-jitter (Geo-Anchor), con proyección vertical Raycast y extracción de peralte real LiDAR.
  4. Validador Pre-flight y Exportador de Mod (FBX para ksEditor, `surfaces.ini`, `models.ini` y `ui/ui_track.json`).
  5. 14 Tests unitarios automatizados que cubren toda la lógica matemática y de exportación.

---

## 🗺️ Fases de Desarrollo

```mermaid
flowchart LR
    Fase1["Fase 1: Base & Race Nodes\n🟢 Completada"]
    Fase2["Fase 2: Carreteras & Físicas\n🟢 Completada"]
    Fase3["Fase 3: LiDAR & Topografía Real\n🟢 Completada"]
    Fase4["Fase 4: Exportación & Archivos AC\n🟢 Completada"]

    Fase1 --> Fase2
    Fase2 --> Fase3
    Fase3 --> Fase4
```


---

### Fase 1: Esqueleto Modular y Nodos de Carrera de Assetto Corsa 🟢 *(Completada)*
- [x] Documentación exhaustiva técnica y guía de handover para futuros agentes.
- [x] Definición de constantes oficiales de Assetto Corsa (`core/constants.py`).
- [x] Creación de propiedades de escena y objeto (`core/properties.py`).
- [x] Utilidades de escena: colecciones automáticas, visualizadores de orientación y flechas (`core/utils.py`).
- [x] Operador de Parrilla de Salida (`race_nodes/spawn_manager.py`):
  - Creación de `AC_START_0..N`.
  - Opciones de espaciado longitudinal/lateral, escalonado (staggered), paralelo o en fila india.
  - Orientación automática y flecha visual en 3D Viewport.
- [x] Operador de Puestos de Boxes (`AC_PIT_0..N`):
  - Creación de boxes con distancia configurable.
- [x] Operador de Salida Lanzada / Hotlap (`AC_HOTLAP_START_0`).
- [x] Operador de Puertas de Cronometraje (`race_nodes/timing_gates.py`):
  - Línea de Meta: `AC_TIME_0_L` y `AC_TIME_0_R`.
  - Splits / Sectores: `AC_TIME_1_L/R`, `AC_TIME_2_L/R`.
  - Modo Tramo A-B (Hillclimb/Rally): `AC_AB_START_L/R` y `AC_AB_FINISH_L/R`.
- [x] Panel UI en el Sidebar (`3D View > N-Panel > Track Maker`):
  - `panel_main.py`: Diagnóstico de circuito y estado en tiempo real de nodos en escena.
  - `panel_race_nodes.py`: Controles interactivos y generación con 1 clic.

---

### Fase 2: Carreteras Procedurales y Separación Física/Visual 🟢 *(Completada)*
- [x] Generador de curvas guía de circuito (Spline 3D en `curve_tools.py`) para circuitos cerrados y tramos A-B.
- [x] Herramientas de peralte: Fijar peralte exacto (`set_curve_tilt`) y cálculo de auto-peralte por radio de curvatura (`auto_bank_curve`).
- [x] Generador de perfiles transversales paramétricos (`profile_generator.py`):
  - Calzada con anchura ajustable y bombeo parabólico de drenaje (*camber*).
  - Bordillos / pianos laterales con chaflán (`KERB`).
  - Banquetas peatonales urbanas (`SIDEWALK`).
  - Muros y barreras rígidas (`WALL`).
- [x] Árbol interactivo de **Geometry Nodes** para previsualización en tiempo real (`geometry_nodes.py`).
- [x] Generador de mallas acopladas/desacopladas (`road_generator.py`):
  - **Malla Visual (`ROAD_`)**: UV continuo longitudinal sin estiramiento (`UVMap`), materiales asignados (`MAT_TM_Asphalt`, `MAT_TM_Kerb`, `MAT_TM_Sidewalk`, `MAT_TM_Wall`) en `TM_Road_Visual`.
  - **Malla Física (`1ROAD_`)**: Subdivisión longitudinal uniforme (0.2m - 0.4m para FFB), triangulación obligatoria para el motor de físicas de AC en `TM_Road_Physics`.
- [x] Panel UI de carreteras (`ui/panel_road.py`) integrado en el N-Panel de Blender.
- [x] Tests unitarios matemáticos y de perfiles (`tests/test_road_profile.py`).

---

### Fase 3: Integración de Datos Topográficos Reales (LiDAR / GIS) 🟢 *(Completada)*
- [x] Sistema de Anclaje Georreferenciado (*Geo-Anchor* en `geo_anchor.py`):
  - Conversión de WGS84 (Lat/Lon) a UTM con cálculo de husos y hemisferio.
  - Compensación y desplazamiento del origen local `(0, 0, 0)` para neutralizar el *floating-point jitter* (pérdida de precisión de 32 bits).
  - Operador para recentrar mallas y nubes de puntos importadas (`recenter_gis_objects`).
- [x] Módulo de proyección al terreno (*Terrain Snapping* en `terrain_snap.py`):
  - Algoritmo de *Raycast Vertical* acelerado mediante árboles espaciales `BVHTree` para adaptar la curva Bézier a la topografía de la malla LiDAR (`snap_curve_to_terrain`).
  - Extracción y ajuste de peralte real (*Match Terrain Banking*) a partir de las normales de la superficie del terreno.
  - Filtro laplaciano de suavizado de pendientes (`smooth_curve_elevation`) para eliminar artefactos y ruido del escáner.
- [x] Panel UI de Topografía y LiDAR (`ui/panel_gis.py`) integrado en el N-Panel de Blender.
- [x] Tests unitarios de conversión de coordenadas y precisión milimétrica (`tests/test_geo_anchor.py`).

---

### Fase 4: Validación Pre-flight, Exportación y Empaquetado 🟢 *(Completada)*
- [x] Validador Pre-flight (`exporters/validator.py`):
  - Verificación de nodos obligatorios (`AC_START_0`, al menos una puerta de meta `AC_TIME_0` o tramo `AC_AB`).
  - Verificación de existencia de mallas físicas (`1ROAD_`).
  - Detección de escalas no unitarias (escala != 1.0) para prevenir deformaciones en ksEditor.
  - Generación de informe con errores bloqueantes y advertencias no bloqueantes.
- [x] Generador de Archivos de Configuración (`exporters/config_generator.py`):
  - `surfaces.ini` generado automáticamente en raíz y en `data/` con presets de fricción, baches y FFB.
  - `models.ini` configurando la carga del archivo `<track_name>.kn5`.
  - `ui/ui_track.json` con metadatos calculados (longitud estimada de trazado, autor, país, etiquetas).
  - Empaquetado en la jerarquía física de carpetas del mod de Assetto Corsa.
- [x] Exportador FBX para ksEditor (`exporters/assetto_corsa.py`):
  - Filtrado automático de objetos de circuito y exclusión de cámaras/luces de Blender.
  - Configuración automatizada de ejes de ksEditor (-Z Forward, Y Up, escala 1.0).
  - Apertura automática opcional del directorio del mod al finalizar.
- [x] Panel UI de Exportación (`ui/panel_export.py`) con checklist pre-flight interactivo en el N-Panel.
- [x] Tests unitarios de validación y generación de paquetes (`tests/test_exporters_and_validation.py`).
