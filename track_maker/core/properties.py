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


classes = (
    TrackMakerCircuitSettings,
    TrackMakerSpawnSettings,
    TrackMakerTimingSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.track_maker_circuit = PointerProperty(type=TrackMakerCircuitSettings)
    bpy.types.Scene.track_maker_spawns = PointerProperty(type=TrackMakerSpawnSettings)
    bpy.types.Scene.track_maker_timing = PointerProperty(type=TrackMakerTimingSettings)


def unregister():
    del bpy.types.Scene.track_maker_circuit
    del bpy.types.Scene.track_maker_spawns
    del bpy.types.Scene.track_maker_timing

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
