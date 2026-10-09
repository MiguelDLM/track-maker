"""Propiedades personalizadas y PropertyGroups para Blender."""

import bpy
from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty,
)


class TrackMakerCircuitSettings(bpy.types.PropertyGroup):
    """Configuración general del circuito para Assetto Corsa."""

    circuit_name: StringProperty(
        name="Nombre del Circuito",
        description="Nombre identificativo de la pista",
        default="Mi_Circuito_Custom",
    )

    circuit_type: EnumProperty(
        name="Tipo de Trazado",
        description="Formato del trazado de carreras",
        items=[
            ("CIRCUIT", "Circuito Cerrado", "Pista tradicional en bucle cerrado"),
            ("HILLCLIMB_AB", "Tramo Punto a Punto (A-B)", "Subida de montaña, rally o tramo abierto"),
        ],
        default="CIRCUIT",
    )

    author: StringProperty(
        name="Autor",
        description="Nombre del creador o equipo",
        default="Track Maker",
    )

    country: StringProperty(
        name="País",
        description="País donde se ubica el circuito real",
        default="México",
    )

    city: StringProperty(
        name="Ciudad / Región",
        description="Localidad o zona geográfica",
        default="CDMX",
    )


class TrackMakerSpawnSettings(bpy.types.PropertyGroup):
    """Parámetros para la generación de posiciones de salida y boxes."""

    grid_count: IntProperty(
        name="Coches en Parrilla",
        description="Número de posiciones AC_START a generar",
        default=24,
        min=1,
        max=64,
    )

    grid_layout: EnumProperty(
        name="Distribución de Parrilla",
        description="Formato de colocación de los coches",
        items=[
            ("STAGGERED", "Escalonada (F1 / GT)", "Dos columnas alternadas longitudinalmente"),
            ("IN_LINE", "Fila India (1 Columna)", "Una sola fila de salida"),
            ("PARALLEL", "En Paralelo", "Pares de coches a la misma altura"),
        ],
        default="STAGGERED",
    )

    grid_row_spacing: FloatProperty(
        name="Distancia Longitudinal",
        description="Separación en metros entre filas (eje Y)",
        default=8.0,
        min=4.0,
        max=25.0,
        unit="LENGTH",
    )

    grid_lateral_spacing: FloatProperty(
        name="Separación Lateral",
        description="Separación en metros entre columnas izquierda y derecha (eje X)",
        default=3.5,
        min=1.5,
        max=10.0,
        unit="LENGTH",
    )

    grid_stagger_offset: FloatProperty(
        name="Desfase Escalonado",
        description="Adelanto en metros del coche preferente en parrilla escalonada",
        default=4.0,
        min=0.0,
        max=10.0,
        unit="LENGTH",
    )

    pit_count: IntProperty(
        name="Puestos de Boxes",
        description="Número de puestos AC_PIT a generar",
        default=24,
        min=1,
        max=64,
    )

    pit_spacing: FloatProperty(
        name="Separación de Boxes",
        description="Distancia en metros entre cada box en el pitlane",
        default=12.0,
        min=5.0,
        max=30.0,
        unit="LENGTH",
    )


class TrackMakerTimingSettings(bpy.types.PropertyGroup):
    """Parámetros para las puertas de cronometraje de sectores y meta."""

    gate_width: FloatProperty(
        name="Anchura de Puerta",
        description="Distancia en metros entre los postes izquierdo y derecho (L y R)",
        default=16.0,
        min=4.0,
        max=50.0,
        unit="LENGTH",
    )

    gate_type: EnumProperty(
        name="Tipo de Puerta",
        description="Sector o función de cronometraje",
        items=[
            ("FINISH", "Línea de Meta (AC_TIME_0)", "Inicio / Fin de vuelta para circuitos cerrados"),
            ("SPLIT_1", "Sector 1 (AC_TIME_1)", "Primer punto intermedio de cronometraje"),
            ("SPLIT_2", "Sector 2 (AC_TIME_2)", "Segundo punto intermedio de cronometraje"),
            ("AB_START", "Salida Tramo (AC_AB_START)", "Punto de salida para tramos punto a punto A-B"),
            ("AB_FINISH", "Meta Tramo (AC_AB_FINISH)", "Punto de meta para tramos punto a punto A-B"),
        ],
        default="FINISH",
    )


class TrackMakerRoadSettings(bpy.types.PropertyGroup):
    """Parámetros para la generación procedural de carreteras y gemelos físicos de AC."""

    road_name: StringProperty(
        name="Nombre de la Carretera",
        description="Identificador base para las mallas generadas (ROAD_ y 1ROAD_)",
        default="Pista_Principal",
    )

    road_width: FloatProperty(
        name="Anchura de Calzada",
        description="Anchura total del asfalto en metros",
        default=9.0,
        min=2.0,
        max=50.0,
        unit="LENGTH",
    )

    road_subdivisions_x: IntProperty(
        name="Subdivisiones Perfil",
        description="Número de segmentos transversales para formar el ancho de la calzada",
        default=6,
        min=2,
        max=32,
    )

    physics_subdivision_y: FloatProperty(
        name="Paso Longitudinal FFB",
        description="Distancia longitudinal entre vértices en la malla física 1ROAD_ (ideal 0.2m - 0.4m para FFB en AC)",
        default=0.30,
        min=0.10,
        max=2.00,
        unit="LENGTH",
    )

    visual_resolution_y: IntProperty(
        name="Resolución Spline Visual",
        description="Número de cortes evaluados por segmento de curva para la malla visual",
        default=24,
        min=4,
        max=128,
    )

    has_crown: bpy.props.BoolProperty(
        name="Bombeo Central (Camber)",
        description="Añade curvatura transversal convexa para simular desagüe y peralte natural de carreteras",
        default=True,
    )

    crown_height: FloatProperty(
        name="Altura Bombeo",
        description="Elevación del centro de la calzada respecto a los bordes en metros",
        default=0.06,
        min=0.0,
        max=0.3,
        unit="LENGTH",
    )

    # Bordillos / Pianos / Banquetas
    has_kerbs: bpy.props.BoolProperty(
        name="Bordillos / Banquetas",
        description="Generar bordillos laterales a lo largo de la calzada",
        default=True,
    )

    kerb_width: FloatProperty(
        name="Anchura Bordillo",
        description="Anchura del bordillo en metros",
        default=0.40,
        min=0.1,
        max=2.5,
        unit="LENGTH",
    )

    kerb_height: FloatProperty(
        name="Altura Bordillo",
        description="Altura del bordillo o banqueta respecto al asfalto en metros",
        default=0.12,
        min=0.02,
        max=0.4,
        unit="LENGTH",
    )

    # Banquetas peatonales (Escenarios Urbanos)
    has_sidewalks: bpy.props.BoolProperty(
        name="Banquetas Urbanas",
        description="Extruir aceras peatonales tras el bordillo",
        default=False,
    )

    sidewalk_width: FloatProperty(
        name="Anchura Banqueta",
        description="Anchura de la acera peatonal en metros",
        default=1.80,
        min=0.5,
        max=8.0,
        unit="LENGTH",
    )

    # Barreras / Guardarraíles
    has_walls: bpy.props.BoolProperty(
        name="Muros / Barreras (1WALL_)",
        description="Generar barreras rígidas o guardarraíles con colisión 1WALL_",
        default=False,
    )

    wall_height: FloatProperty(
        name="Altura Muro",
        description="Altura de la barrera en metros",
        default=0.90,
        min=0.3,
        max=3.0,
        unit="LENGTH",
    )

    # Texturizado y UVs
    uv_tiling_v: FloatProperty(
        name="Repetición UV (Longitudinal)",
        description="Repetición de la textura de asfalto por metro",
        default=0.20,
        min=0.01,
        max=2.0,
    )


class TrackMakerGISSettings(bpy.types.PropertyGroup):
    """Parámetros para georreferenciación, origen local anti-jitter y snapping LiDAR."""

    anchor_utm_x: FloatProperty(
        name="Ancla UTM X (Easting)",
        description="Coordenada este en metros del punto de referencia central",
        default=0.0,
        precision=3,
    )

    anchor_utm_y: FloatProperty(
        name="Ancla UTM Y (Northing)",
        description="Coordenada norte en metros del punto de referencia central",
        default=0.0,
        precision=3,
    )

    anchor_elevation_z: FloatProperty(
        name="Ancla Elevación Z",
        description="Cota de altura sobre el nivel del mar en metros del origen local",
        default=0.0,
        precision=3,
        unit="LENGTH",
    )

    epsg_code: IntProperty(
        name="Código EPSG / CRS",
        description="Sistema de referencia de coordenadas (ej. 25830 para UTM30N España, 32614 para UTM14N México)",
        default=25830,
        min=1000,
        max=99999,
    )

    has_anchor: bpy.props.BoolProperty(
        name="Ancla Activa",
        description="Indica si el proyecto tiene un ancla georreferenciada fijada",
        default=False,
    )

    # Búsqueda GPS Mundial (Nominatim)
    search_query: StringProperty(
        name="Buscar Lugar GPS",
        description="Nombre del circuito, tramo o lugar del mundo real (ej. 'Circuito del Jarama', 'Monza', 'Passo dello Stelvio')",
        default="",
    )

    search_result_name: StringProperty(
        name="Nombre Encontrado",
        description="Resultado descriptivo del lugar encontrado",
        default="",
    )

    latitude: FloatProperty(
        name="Latitud (°)",
        description="Latitud GPS en grados decimales (WGS84)",
        default=40.615823,
        precision=6,
    )

    longitude: FloatProperty(
        name="Longitud (°)",
        description="Longitud GPS en grados decimales (WGS84)",
        default=-3.584889,
        precision=6,
    )

    # Modo de Cobertura Geográfica
    coverage_mode: EnumProperty(
        name="Modo de Cobertura",
        description="Selecciona entre área radial (circuito cerrado) o tramo lineal entre dos puntos A y B",
        items=[
            ("RADIUS", "Centro y Radio (Circuito)", "Para autódromos y circuitos cerrados"),
            ("POINTS_AB", "Tramo Punto A ➔ B (Carretera)", "Para tramos punto a punto (Hillclimb / Rally / Carretera)"),
        ],
        default="RADIUS",
    )

    # Coordenadas Punto A (Salida) y Punto B (Meta)
    point_a_lat: FloatProperty(
        name="Latitud Salida A",
        description="Latitud GPS del punto de inicio / salida A",
        default=20.530890,
        precision=6,
    )

    point_a_lon: FloatProperty(
        name="Longitud Salida A",
        description="Longitud GPS del punto de inicio / salida A",
        default=-103.293237,
        precision=6,
    )

    point_b_lat: FloatProperty(
        name="Latitud Meta B",
        description="Latitud GPS del punto de llegada / meta B",
        default=20.678863,
        precision=6,
    )

    point_b_lon: FloatProperty(
        name="Longitud Meta B",
        description="Longitud GPS del punto de llegada / meta B",
        default=-103.347552,
        precision=6,
    )

    corridor_margin_km: FloatProperty(
        name="Margen Corredor (km)",
        description="Margen lateral extra en kilómetros alrededor del tramo A-B",
        default=1.0,
        min=0.1,
        max=10.0,
        unit="LENGTH",
    )

    # Ajuste de Visor y Escala Real
    auto_adjust_clipping: bpy.props.BoolProperty(
        name="Ajustar Visor Automáticamente",
        description="Ajusta el límite lejano (clip_end) de los visores 3D para evitar que mallas kilométricas se corten o desaparezcan",
        default=True,
    )

    auto_frame_view: bpy.props.BoolProperty(
        name="Enfocar Vista Automáticamente",
        description="Centra y encuadra la vista 3D sobre la geometría generada",
        default=True,
    )

    # Exageración / Escala Vertical
    vertical_scale: FloatProperty(
        name="Escala Vertical (Relieve)",
        description="Multiplicador de relieve vertical (1.0 = escala 1:1 real en metros; 1.5x a 2.0x resalta puertos y pendientes)",
        default=1.0,
        min=0.5,
        max=5.0,
        precision=2,
    )

    # Estadísticas Altimétricas de Ruta en Vivo
    route_info_distance: FloatProperty(
        name="Longitud Ruta (km)",
        description="Distancia recorrida del tramo en kilómetros",
        default=0.0,
        precision=2,
    )

    route_info_climb: FloatProperty(
        name="Desnivel Acumulado (m)",
        description="Desnivel bruto entre cota máxima y mínima del tramo",
        default=0.0,
        precision=1,
    )

    route_info_min_elev: FloatProperty(
        name="Cota Mínima (m)",
        description="Altitud mínima sobre el nivel del mar en metros",
        default=0.0,
        precision=1,
    )

    route_info_max_elev: FloatProperty(
        name="Cota Máxima (m)",
        description="Altitud máxima sobre el nivel del mar en metros",
        default=0.0,
        precision=1,
    )

    route_info_max_grade: FloatProperty(
        name="Pendiente Máxima (%)",
        description="Mayor pendiente porcentual registrada en el tramo",
        default=0.0,
        precision=1,
    )

    # Descarga DEM (AWS Terrarium)
    terrain_radius_km: FloatProperty(
        name="Radio Terreno (km)",
        description="Radio de cobertura del terreno DEM en kilómetros (Modo Radio)",
        default=2.0,
        min=0.5,
        max=25.0,
        unit="LENGTH",
    )

    terrain_resolution: IntProperty(
        name="Resolución Malla",
        description="Número de subdivisiones de la cuadrícula de relieve DEM",
        default=256,
        min=32,
        max=1024,
    )

    dem_zoom: IntProperty(
        name="Zoom Mosaicos DEM",
        description="Nivel de detalle de elevación Terrarium (11-15, recomendado 13-14)",
        default=13,
        min=10,
        max=15,
    )

    # Carreteras OpenStreetMap (Overpass API)
    osm_road_type: EnumProperty(
        name="Tipo de Vía OSM",
        description="Tipo de carretera a importar de OpenStreetMap",
        items=[
            ("RACEWAY", "Circuitos (Raceway)", "Circuitos cerrados y pistas de competición"),
            ("MAIN_ROADS", "Carreteras Principales", "Autopistas, carreteras nacionales y secundarias (Rally / Tramos)"),
            ("ALL_ROADS", "Todas las Vías Transitables", "Toda la red de carreteras públicas"),
            ("CUSTOM", "Filtro Personalizado", "Expresión regular personalizada para etiqueta highway"),
        ],
        default="RACEWAY",
    )

    osm_custom_filter: StringProperty(
        name="Filtro Highway OSM",
        description="Expresión regular para la clave highway de OpenStreetMap (ej. raceway|primary)",
        default="raceway",
    )

    osm_radius_m: FloatProperty(
        name="Radio Búsqueda Vías (m)",
        description="Radio en metros para extraer carreteras desde el centro GPS",
        default=2000.0,
        min=100.0,
        max=25000.0,
        unit="LENGTH",
    )

    osm_snap_to_terrain: bpy.props.BoolProperty(
        name="Proyectar a Terreno",
        description="Proyectar automáticamente la cota Z de los vértices sobre el terreno DEM",
        default=True,
    )

    osm_curve_type: EnumProperty(
        name="Tipo de Spline",
        description="Tipo de spline para la curva generada en Blender",
        items=[
            ("BEZIER", "Bézier Suave", "Curva Bézier con tangentes automáticas"),
            ("POLY", "Polilínea Fiel", "Curva poligonal recta punto a punto exacta"),
        ],
        default="BEZIER",
    )

    # Snapping a terreno
    target_terrain_name: StringProperty(
        name="Malla Terreno",
        description="Nombre del objeto de terreno DTM o LiDAR escaneado sobre el que proyectar",
        default="",
    )

    snap_elevation_offset: FloatProperty(
        name="Offset Vertical",
        description="Elevación sobre la superficie del terreno para evitar Z-fighting con la hierba (ej. +2 a 5 cm)",
        default=0.03,
        min=-0.5,
        max=2.0,
        unit="LENGTH",
    )

    match_terrain_banking: bpy.props.BoolProperty(
        name="Copiar Peralte Real",
        description="Calcula e iguala la inclinación transversal (tilt) analizando las normales del terreno LiDAR",
        default=True,
    )

    smoothing_passes: IntProperty(
        name="Pasadas de Suavizado",
        description="Pasadas de suavizado de cota vertical para filtrar ruido del escaneo LiDAR",
        default=2,
        min=0,
        max=10,
    )


class TrackMakerExportSettings(bpy.types.PropertyGroup):
    """Parámetros de validación y exportación a Assetto Corsa."""

    export_directory: StringProperty(
        name="Carpeta de Destino",
        description="Directorio donde se creará la carpeta del mod con el FBX y configuraciones",
        default="//export",
        subtype="DIR_PATH",
    )

    export_fbx: bpy.props.BoolProperty(
        name="Exportar FBX para ksEditor",
        description="Genera el modelo 3D en formato FBX optimizado para ksEditor",
        default=True,
    )

    generate_configs: bpy.props.BoolProperty(
        name="Generar INIs y ui_track.json",
        description="Crea automáticamente surfaces.ini, models.ini y ui/ui_track.json",
        default=True,
    )

    apply_modifiers_on_export: bpy.props.BoolProperty(
        name="Aplicar Modificadores",
        description="Aplica Geometry Nodes y otros modificadores antes de exportar el FBX",
        default=True,
    )

    open_folder_after: bpy.props.BoolProperty(
        name="Abrir Carpeta al Finalizar",
        description="Abre el explorador de archivos en la carpeta del mod exportado",
        default=False,
    )


classes = (
    TrackMakerCircuitSettings,
    TrackMakerSpawnSettings,
    TrackMakerTimingSettings,
    TrackMakerRoadSettings,
    TrackMakerGISSettings,
    TrackMakerExportSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.track_maker_circuit = PointerProperty(type=TrackMakerCircuitSettings)
    bpy.types.Scene.track_maker_spawns = PointerProperty(type=TrackMakerSpawnSettings)
    bpy.types.Scene.track_maker_timing = PointerProperty(type=TrackMakerTimingSettings)
    bpy.types.Scene.track_maker_road = PointerProperty(type=TrackMakerRoadSettings)
    bpy.types.Scene.track_maker_gis = PointerProperty(type=TrackMakerGISSettings)
    bpy.types.Scene.track_maker_export = PointerProperty(type=TrackMakerExportSettings)


def unregister():
    for attr in ("track_maker_circuit", "track_maker_spawns", "track_maker_timing", "track_maker_road", "track_maker_gis", "track_maker_export"):
        if hasattr(bpy.types.Scene, attr):
            delattr(bpy.types.Scene, attr)

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass




