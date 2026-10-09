"""Funciones auxiliares para manipulación de colecciones, objetos y matemáticas de Blender."""

import math
import bpy
from mathutils import Vector, Euler
from .constants import (
    COLLECTION_ROOT,
    COLLECTION_RACE_NODES,
    PREFIX_START,
    PREFIX_PIT,
    NAME_HOTLAP_START,
    NAME_TIME_0_L,
    NAME_TIME_1_L,
    NAME_TIME_2_L,
    NAME_AB_START_L,
    NAME_AB_FINISH_L,
)


def get_or_create_collection(name: str, parent_name: str = None) -> bpy.types.Collection:
    """Obtiene una colección existente o la crea en la jerarquía adecuada."""
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)

    # Determinar padre
    if parent_name:
        parent_col = get_or_create_collection(parent_name)
        if col.name not in parent_col.children:
            # Si estaba en la escena raíz, desenlazar
            if col.name in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.unlink(col)
            parent_col.children.link(col)
    else:
        if col.name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(col)

    return col


def create_ac_empty(
    name: str,
    location: Vector = Vector((0.0, 0.0, 0.0)),
    rotation_euler: Euler = Euler((0.0, 0.0, 0.0), "XYZ"),
    display_type: str = "ARROWS",
    display_size: float = 1.5,
    element_type: str = None,
    collection_name: str = COLLECTION_RACE_NODES,
) -> bpy.types.Object:
    """Crea o actualiza un Empty de Assetto Corsa con orientación y etiquetas."""
    # Si el objeto ya existe con ese nombre, eliminarlo para recrearlo limpio
    if name in bpy.data.objects:
        old_obj = bpy.data.objects[name]
        bpy.data.objects.remove(old_obj, do_unlink=True)

    empty_obj = bpy.data.objects.new(name, None)
    empty_obj.empty_display_type = display_type
    empty_obj.empty_display_size = display_size
    empty_obj.location = location
    empty_obj.rotation_euler = rotation_euler

    if element_type:
        empty_obj["track_element_type"] = element_type

    # Asociar a la colección correspondiente
    target_col = get_or_create_collection(collection_name, parent_name=COLLECTION_ROOT)
    target_col.objects.link(empty_obj)

    return empty_obj


def count_race_nodes() -> dict:
    """Escanea la escena y contabiliza los nodos de carrera existentes de Assetto Corsa."""
    starts = [obj.name for obj in bpy.data.objects if obj.name.startswith(PREFIX_START)]
    pits = [obj.name for obj in bpy.data.objects if obj.name.startswith(PREFIX_PIT)]
    has_hotlap = NAME_HOTLAP_START in bpy.data.objects

    # Detección de puertas
    has_time_0 = NAME_TIME_0_L in bpy.data.objects
    has_time_1 = NAME_TIME_1_L in bpy.data.objects
    has_time_2 = NAME_TIME_2_L in bpy.data.objects
    has_ab_start = NAME_AB_START_L in bpy.data.objects
    has_ab_finish = NAME_AB_FINISH_L in bpy.data.objects

    return {
        "start_count": len(starts),
        "pit_count": len(pits),
        "has_hotlap": has_hotlap,
        "has_time_0": has_time_0,
        "has_time_1": has_time_1,
        "has_time_2": has_time_2,
        "has_ab_start": has_ab_start,
        "has_ab_finish": has_ab_finish,
    }


def remove_objects_by_prefix(prefix: str) -> int:
    """Elimina todos los objetos cuyos nombres comienzan por el prefijo dado."""
    to_remove = [obj for obj in bpy.data.objects if obj.name.startswith(prefix)]
    count = len(to_remove)
    for obj in to_remove:
        bpy.data.objects.remove(obj, do_unlink=True)
    return count
