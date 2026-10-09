# Especificaciones Técnicas y Prompt Base para Agente de Gemini
## Extensión de Blender para Creación de Escenarios Urbanos y Circuitos Custom (Enfoque: Assetto Corsa & Real-World LiDAR)

Este documento contiene la estructura fundamental, las especificaciones técnicas y el plan de trabajo para el desarrollo de un addon de Blender (v4.2+ / 2026) orientado a la recreación ultrarrealista de circuitos y tramos del mundo real para **Assetto Corsa** (manteniendo una arquitectura modular extensible a otros simuladores en el futuro).

---

## 1. Comando Base Inicial (System Prompt para el Agente)

```text
Actúa como un Ingeniero de Software Senior experto en el desarrollo de Addons para Blender (Python API / `bpy`), especialista en Modding de Assetto Corsa y procesamiento de datos geoespaciales (LiDAR / GIS). Tu objetivo es ayudar al usuario a diseñar, programar y estructurar una extensión de Blender modular para la creación fiel y automatizada de pistas y entornos reales (carreteras de montaña, circuitos y trazados urbanos).

Principios de desarrollo de la extensión:
1. Máxima Fidelidad Real: Flujo de trabajo basado en elevación real (nubes LiDAR / DTM) y corrección de origen de coordenadas para evitar jitter de coma flotante en Blender y motores de juego.
2. Separación Visual vs Física (Estándar de Oro de Assetto Corsa): Generar mallas visuales detalladas y mallas físicas colisionadoras (prefijo 1ROAD_) con subdivisión longitudinal uniforme (0.2m - 0.5m) para un Force Feedback (FFB) fiel sin sobrecargar la GPU.
3. Modularidad y Proceduralidad: Código dividido en módulos limpios (core, road, race_nodes, gis, exporters, ui), utilizando Geometry Nodes y splines modernos de Blender 4.x.
4. Gestión Integral de Assetto Corsa: Automatización de Nodos de Carrera (AC_START_, AC_PIT_, AC_TIME_), validaciones pre-flight y generación de archivos auxiliares (surfaces.ini, ui_track.json, models.ini).

Cuando escribas código, utiliza la API moderna de Blender (Blender 4.2+), incluye manejo de errores robusto, registra correctamente las clases y documenta el código en español con claridad.
```

---

## 2. Arquitectura del Addon y Pipeline Técnico

### 2.1. Estructura Modular del Proyecto (`track_maker`)
```text
track_maker/
├── __init__.py               # Registro de Blender y metadatos bl_info
├── core/
│   ├── constants.py          # Prefijos de AC (1ROAD_, 1WALL_, AC_START_, etc.)
│   ├── properties.py         # Custom Properties del circuito y elementos
│   └── utils.py              # Operaciones auxiliares de geometría y matrices
├── road/
│   ├── curve_tools.py        # Creación y ajuste de splines y peraltes
│   ├── profile_generator.py  # Generador de secciones transversales (asfalto, banquetas, arcenes)
│   └── geometry_nodes.py     # Grafos de Geometry Nodes para carreteras procedurales
├── race_nodes/
│   ├── spawn_manager.py      # Creación y ajuste visual de Starts, Pits, Hotlap
│   └── timing_gates.py       # Puertas de tiempo (Split, Finish)
├── gis/
│   ├── geo_anchor.py         # Manejo de coordenadas métricas y orígenes
│   └── terrain_snap.py       # Algoritmos de snap al terreno / nubes LiDAR
├── exporters/
│   ├── assetto_corsa.py      # Pipeline FBX, validaciones pre-flight y jerarquías
│   └── config_generator.py   # Creación de surfaces.ini, ui_track.json, models.ini
└── ui/
    ├── panel_main.py         # Panel principal en el Sidebar (N-Panel)
    ├── panel_road.py         # Herramientas de carretera y bordillos
    ├── panel_race_nodes.py   # Herramientas de colocación de spawns y gates
    └── panel_export.py       # Interfaz de validación y exportación
```

### 2.2. Requisitos Técnicos de Assetto Corsa:
* **Separación de Mallas:**
  * `Visual Mesh`: Shaders complejos, UVs continuos para texturas de asfalto y marcas viales, optimizado para render.
  * `Physical Collision Mesh`: Prefijos `1ROAD_`, `1KERB_`, `1WALL_`, `1GRASS_`, `1SAND_`. Sin materiales complejos, geometría optimizada pero densamente subdividida a lo largo de la calzada (cada 20-50 cm) para calcular las físicas de suspensión y FFB con precisión milimétrica.
* **Nodos de Carrera Esenciales:**
  * `AC_START_0..N`: Parrilla de salida con orientación frontal.
  * `AC_PIT_0..N`: Puestos de boxes.
  * `AC_HOTLAP_START_0`: Salida lanzada contrarreloj.
  * `AC_TIME_0_L/R`: Puerta de meta y salida.
  * `AC_TIME_1_L/R`, `AC_TIME_2_L/R`: Sectores intermedios.
  * *(Hillclimbs / Rally A a B)*: `AC_AB_START_L/R` y `AC_AB_FINISH_L/R`.
* **Archivos de Configuración del Circuito:**
  * `surfaces.ini`: Define fricción, baches (damping), sonidos y si cuenta como pista válida (`IS_VALID_TRACK=1`).
  * `ui/ui_track.json`: Metadatos para Content Manager y el juego.

---

## 3. Metodología de Recreación del Mundo Real (LiDAR / GIS)

1. **Gestión de Origen Local (Anti-Jitter):**
   * Las coordenadas geográficas UTM (millones de metros) rompen la precisión de coma flotante de 32 bits de los motores de juego y causan temblores en los vértices.
   * La herramienta implementa un punto de anclaje georreferenciado y centra el proyecto en `(0, 0, 0)` en Blender (1 unidad = 1 metro).
2. **Uso de Datos LiDAR / DTM:**
   * Utilizar nubes de puntos LiDAR o mallas de elevación digital (DTM) filtradas a nivel de suelo para reproducir con total fidelidad las pendientes reales, peraltes naturales y desniveles.
3. **Geometry Nodes vs Modificadores Antiguos:**
   * Sustituir el flujo antiguo de `Curve + Array` por grafos de **Geometry Nodes** (Blender 4.x), lo que permite:
     * Generar carretera, bordillos, banquetas y arcenes sin distorsiones de textura en curvas pronunciadas.
     * Proyectar (Raycast/Snap) la superficie directamente a la cota del terreno real.
     * Generar la malla física colisionadora (`1ROAD_`) y la visual en paralelo con un solo clic.

---

## 4. Proyectos Afines y Referencias Clave de la Comunidad

* **Técnicas de LilSki (OverTake / RaceDepartment):** El estándar de oro en modding de Assetto Corsa ("Proper technique in track making"). Define el uso de nubes LiDAR, triangulación de mallas físicas y optimización de materiales.
* **ac-track-tools (nendotools):** Addon de referencia para gestión de nodos de carrera (`AC_START_`, `AC_TIME_`), configuración de superficies y pre-flight checks.
* **blender_ac_exporter (nothke):** Automatización de exportación FBX con jerarquías limpias listas para ksEditor.
* **Blosm / BlenderGIS:** Referentes de importación de mallas de relieve y ortofotos satelitales.

---

## 5. Plan de Fases de Desarrollo

* **Fase 1 (Inmediata): Esqueleto del Addon y Nodos de Carrera AC**
  * Crear la estructura de carpetas modular del addon e instalarlo en Blender.
  * Implementar el panel UI en el Sidebar (`Track Maker`).
  * Implementar el generador interactivo de spawns (`AC_START_`, `AC_PIT_`, `AC_HOTLAP_`) y puertas de tiempo (`AC_TIME_`) con indicadores visuales en el viewport.
* **Fase 2: Generador de Carreteras Procedural y Separación Física/Visual**
  * Generador de carreteras paramétrico sobre splines/curvas (anchura, peralte, banquetas, bordillos).
  * Extrusión simultánea de la malla física `1ROAD_` (subdivisión longitudinal para FFB).
  * Asignación automática de tags y propiedades de superficie.
* **Fase 3: Integración LiDAR y Snapping Topográfico Real**
  * Herramientas de anclaje georreferenciado (origen local 0,0,0).
  * Proyección de curvas y perfiles sobre mallas DTM/LiDAR reales mediante Geometry Nodes / Raycast.
* **Fase 4: Exportación Completa y Validación de Assetto Corsa**
  * Sistema de comprobación "Pre-flight" (verifica que existan los objetos obligatorios de AC).
  * Exportador FBX optimizado para ksEditor (orientación de ejes y escala 1.0).
  * Generador automático de archivos de configuración (`surfaces.ini`, `models.ini`, `ui/ui_track.json`).