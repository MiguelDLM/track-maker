# Track Maker: Blender Addon para Circuitos de Assetto Corsa

> **Herramienta modular para Blender (v4.2+ / 2026) diseñada para reconstruir carreteras y circuitos del mundo real con fidelidad métrica y física para Assetto Corsa.**

---

## 🎯 Visión del Proyecto

El objetivo de **Track Maker** es cerrar la brecha entre los datos geoespaciales reales (LiDAR, DTM, ortofotografía, OpenStreetMap) y la simulación automovilística en **Assetto Corsa**, automatizando las tareas manuales y complejas del modding:

1. **Fidelidad Topográfica Real:** Recreación milimétrica de peraltes, pendientes e irregularidades del terreno a partir de nubes de puntos LiDAR o mallas DTM sin sufrir los problemas de precisión de coma flotante (*floating-point jitter*).
2. **La Regla de Oro de Assetto Corsa:** Separación automática entre **Malla Visual** (alta fidelidad estética, shaders complejos, UVs continuos) y **Malla Física** (`1ROAD_`, colisionador optimizado con subdivisión longitudinal uniforme de 20-50 cm para un Force Feedback perfecto).
3. **Automatización de Nodos y Estructura:** Generación de parrillas de salida (`AC_START_`), boxes (`AC_PIT_`), puertas de tiempo (`AC_TIME_`) y empaquetado de archivos esenciales (`surfaces.ini`, `models.ini`, `ui/ui_track.json`).
4. **Enfoque Procedural Moderno:** Uso de **Geometry Nodes** de Blender 4.2+ en lugar de modificadores anticuados (`Curve + Array`), garantizando texturizado sin estiramientos y deformaciones.

---

## 📁 Estructura del Repositorio

```text
track-maker/
├── README.md                          # Este archivo (Visión general y guía de inicio)
├── ROADMAP.md                         # Estado del proyecto, fases y backlog técnico
├── especificaciones_agente_gemini.md  # Especificaciones base y prompt del agente
├── docs/                              # Documentación técnica exhaustiva para desarrolladores y agentes
│   ├── assetto_corsa_standards.md    # Estándares de AC: físicas, prefijos, shaders, INIs y nodos
│   ├── lidar_gis_pipeline.md         # Pipeline de datos reales: LiDAR, DTM, CloudCompare y anti-jitter
│   └── architecture_guide.md         # Arquitectura del Addon, convenciones y API de Blender
└── track_maker/                      # Código fuente del Addon de Blender
    ├── __init__.py                   # Registro bl_info y carga modular
    ├── core/                         # Constantes de AC, propiedades y utilidades
    ├── race_nodes/                   # Generadores de Start, Pits y Timing Gates
    ├── road/                         # Generadores procedurales de carretera y colisionadores
    ├── gis/                          # Georreferenciación y snap a terreno
    ├── exporters/                    # Validaciones pre-flight y exportación AC
    └── ui/                           # Interfaz de usuario en el N-Panel (Sidebar) de Blender
```

---

## 🤖 Guía Rápida para Agentes (Context Handover)

Si eres un agente de IA que retoma este proyecto:
1. **Lee primero [`ROADMAP.md`](file:///home/miguel/Documents/software/track-maker/ROADMAP.md)** para saber qué fase se está ejecutando y cuál es la siguiente tarea.
2. **Consulta [`docs/assetto_corsa_standards.md`](file:///home/miguel/Documents/software/track-maker/docs/assetto_corsa_standards.md)** antes de tocar cualquier lógica de colisión, prefijos o exportación.
3. **Consulta [`docs/lidar_gis_pipeline.md`](file:///home/miguel/Documents/software/track-maker/docs/lidar_gis_pipeline.md)** para comprender el tratamiento de coordenadas y topografía real.
4. **Respeta las convenciones descritas en [`docs/architecture_guide.md`](file:///home/miguel/Documents/software/track-maker/docs/architecture_guide.md)**: Blender 4.2+ Python API, tipado limpio y comentarios explicativos en español.

---

## 🚀 Instalación y Uso en Blender (Modo Desarrollo)

1. En Blender (v4.2 LTS o superior):
   * Ve a `Edit > Preferences > Add-ons`.
   * Para desarrollo en vivo, crea un enlace simbólico de la carpeta `track_maker` a la carpeta de addons de tu Blender:
     ```bash
     ln -s /home/miguel/Documents/software/track-maker/track_maker ~/.config/blender/4.2/scripts/addons/track_maker
     ```
2. Activa el addon **"Custom Track & Urban Builder (AC Edition)"**.
3. Abre la vista 3D (`3D Viewport`) y pulsa la tecla `N` para abrir el Sidebar lateral.
4. Selecciona la pestaña **"Track Maker"**.
