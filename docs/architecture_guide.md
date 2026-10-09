# Guía de Arquitectura del Addon: Track Maker

Este documento define la arquitectura interna, convenciones de programación y patrones de diseño utilizados en el addon de Blender para que cualquier desarrollador o agente pueda extenderlo de forma consistente.

---

## 1. Principios de Diseño

1. **Compatibilidad con Blender 4.2+ LTS:**
   * Utilizar la API moderna de Blender (`bpy.types`, nuevos identificadores de colecciones y nodos).
   * Uso del nuevo sistema de extensiones de Blender si procede, manteniendo compatibilidad como paquete ZIP o carpeta de addon clásica.
2. **Modularidad Desacoplada:**
   * Los operadores no contienen lógica matemática pesada directamente; llaman a funciones puras alojadas en módulos específicos (`core`, `road`, `race_nodes`, `gis`).
3. **Persistencia mediante Custom Properties:**
   * Las propiedades del circuito y de cada elemento se guardan en el ID de Blender (`obj["track_element_type"] = "ROAD"` o mediante `PointerProperty` / `PropertyGroup` en `bpy.types.Scene`), permitiendo que el proyecto no dependa exclusivamente del nombre visible en el Outliner.
4. **Manejo Seguro de Registro (`register` / `unregister`):**
   * Cada submódulo exporta tuplas o listas `classes` con sus operadores y paneles.
   * El archivo raíz `__init__.py` itera y registra en orden de dependencia, con soporte para recarga en caliente (`importlib.reload`).

---

## 2. Mapa de Módulos y Responsabilidades

```text
track_maker/
├── __init__.py               # Entrada principal, metadatos bl_info y ciclo de vida
├── core/
│   ├── constants.py          # Enums y cadenas fijas (nombres AC, friction presets, etc.)
│   ├── properties.py         # PropertyGroups vinculados a Scene y Object
│   └── utils.py              # Creación de colecciones, generación de empties visuales, álgebra
├── race_nodes/
│   ├── spawn_manager.py      # Operadores para parrilla (AC_START_), boxes (AC_PIT_), hotlap
│   └── timing_gates.py       # Operadores para puertas de meta, sectores y tramos A-B
├── road/
│   ├── curve_tools.py        # Helpers para curvas y splines
│   └── geometry_nodes.py     # Creación y enlace de modificadores Geometry Nodes
├── gis/
│   └── geo_anchor.py         # Cálculos de traslación de origen y offsets UTM
├── exporters/
│   ├── assetto_corsa.py      # Pre-flight checklist y exportador FBX
│   └── config_generator.py   # Serialización de surfaces.ini, models.ini, ui_track.json
└── ui/
    ├── panel_main.py         # Cabecera, estado del circuito y selector de módulos
    ├── panel_race_nodes.py   # Botones y controles para spawns y cronometraje
    ├── panel_road.py         # Controles del generador procedural de pista
    └── panel_export.py       # Botón de validación y exportación de archivos
```

---

## 3. Convenciones de Código

### 3.1. Nomenclatura de Clases de Blender
* **Operadores (`bpy.types.Operator`):**
  * `bl_idname`: `track_maker.<accion_en_snake_case>` (ej: `track_maker.create_grid_starts`).
  * Nombre de clase: `TRACKMAKER_OT_<accion_en_camel_case>` (ej: `TRACKMAKER_OT_CreateGridStarts`).
* **Paneles (`bpy.types.Panel`):**
  * `bl_space_type`: `'VIEW_3D'`.
  * `bl_region_type`: `'UI'`.
  * `bl_category`: `'Track Maker'`.
  * Nombre de clase: `TRACKMAKER_PT_<nombre>` (ej: `TRACKMAKER_PT_RaceNodesPanel`).
* **Grupos de Propiedades (`bpy.types.PropertyGroup`):**
  * Nombre de clase: `TRACKMAKER_<nombre>Settings` (ej: `TRACKMAKER_CircuitSettings`).

### 3.2. Colecciones en el Outliner
Para mantener el archivo `.blend` ordenado, el addon crea y gestiona automáticamente una jerarquía limpia de colecciones:

```text
📁 TrackMaker_Project
├── 📁 TM_RaceNodes (AC_START_*, AC_PIT_*, AC_TIME_*)
├── 📁 TM_Road_Visual (Mallas estéticas)
├── 📁 TM_Road_Physics (Mallas 1ROAD_, 1KERB_, 1WALL_)
└── 📁 TM_Terrain (Mallas de terreno o LiDAR de referencia)
```

### 3.3. Manejo de Errores
Todos los operadores deben capturar excepciones y mostrar mensajes claros en la interfaz mediante `self.report({'ERROR'}, "Mensaje explicativo")` en lugar de fallar silenciosamente en la consola.
