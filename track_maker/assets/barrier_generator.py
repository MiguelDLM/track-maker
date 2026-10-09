"""Generador y distribuidor procedural de barreras y contenciones viales para Assetto Corsa.

Soporta:
- Muro central New Jersey de concreto con vialetas reflectivas.
- Barrera metálica galvanizada SCT (Armco W-Beam).
- Malla ciclónica perimetral.
Genera la geometría visual en 'TM_Barriers' y genera simultáneamente la malla de colisión
física simplificada '1WALL_Barriers' en 'TM_Road_Physics' para el motor de físicas de Assetto Corsa.
"""

from __future__ import annotations
import math
from typing import List, Dict, Optional
import bpy
import bmesh
from mathutils import Vector, Matrix

from ..core.constants import (
    COLLECTION_ROOT,
    COLLECTION_BARRIERS,
    COLLECTION_ROAD_PHYSICS,
    PREFIX_PHYS_WALL,
)
from ..core.utils import get_or_create_collection
from ..road.road_generator import sample_curve_evaluated
from .mexico_pack import (
    build_new_jersey_barrier_mesh,
    build_armco_barrier_mesh,
    setup_mexico_materials,
)


def generate_barriers_along_spline(
    curve_obj: bpy.types.Object,
    barrier_type: str = "NEW_JERSEY",
    side: str = "CENTER",
    road_width: float = 10.0,
    lateral_offset: float = 0.0,
    segment_length: float = 3.0,
    create_physics: bool = True,
) -> tuple[int, Optional[bpy.types.Object]]:
    """Distribuye barreras viales modulares a lo largo del trazado y genera la física 1WALL_."""
    if not curve_obj or curve_obj.type != "CURVE":
        raise ValueError("Se requiere un objeto CURVE válido.")

    samples = sample_curve_evaluated(curve_obj, step_length=segment_length)
    if len(samples) < 2:
        return 0, None

    col_barriers = get_or_create_collection(COLLECTION_BARRIERS, parent_name=COLLECTION_ROOT)
    col_physics = get_or_create_collection(COLLECTION_ROAD_PHYSICS, parent_name=COLLECTION_ROOT)

    # Limpiar barreras previas si existen
    objs_to_del = [obj for obj in col_barriers.objects if obj.name.startswith("Barrier_")]
    for obj in objs_to_del:
        bpy.data.objects.remove(obj, do_unlink=True)

    phys_name = f"{PREFIX_PHYS_WALL}Barriers_{barrier_type}"
    if phys_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[phys_name], do_unlink=True)

    # Determinar qué malla visual modular usar
    if barrier_type == "NEW_JERSEY":
        unit_mesh = build_new_jersey_barrier_mesh(length=segment_length, height=0.85)
        bar_height = 0.85
        bar_half_w = 0.25
    elif barrier_type == "ARMCO":
        unit_mesh = build_armco_barrier_mesh(length=segment_length, height=0.75)
        bar_height = 0.75
        bar_half_w = 0.15
    else:
        unit_mesh = build_new_jersey_barrier_mesh(length=segment_length, height=0.85)
        bar_height = 0.85
        bar_half_w = 0.25

    # Determinar los desfases laterales según el lado
    half_road = road_width / 2.0
    offsets: list[float] = []
    if side == "CENTER":
        offsets.append(0.0 + lateral_offset)
    elif side == "LEFT":
        offsets.append(-half_road - lateral_offset)
    elif side == "RIGHT":
        offsets.append(half_road + lateral_offset)
    elif side == "BOTH":
        offsets.append(-half_road - lateral_offset)
        offsets.append(half_road + lateral_offset)

    instances_count = 0
    bm_phys = bmesh.new() if create_physics else None

    # Colocar elementos modulares
    for off in offsets:
        prev_pt_phys_l = None
        prev_pt_phys_r = None

        for i in range(len(samples) - 1):
            s0 = samples[i]
            s1 = samples[i + 1]

            pos0 = s0["pos"]
            tan0 = s0["tangent"]

            # Vector perpendicular horizontal (normal derecha)
            norm = Vector((tan0.y, -tan0.x, 0.0)).normalized()
            center_pos = pos0 + (norm * off)

            # Orientación angular respecto a la tangente
            yaw = math.atan2(tan0.y, tan0.x) - (math.pi / 2.0)

            obj_name = f"Barrier_{barrier_type}_{off:+.1f}_{i:04d}"
            bar_obj = bpy.data.objects.new(obj_name, unit_mesh)
            bar_obj.location = center_pos
            bar_obj.rotation_euler = (0.0, 0.0, yaw)
            col_barriers.objects.link(bar_obj)
            instances_count += 1

            # Construir tira física continua simplificada (1WALL_)
            if bm_phys is not None:
                pt_l = center_pos - (norm * bar_half_w)
                pt_r = center_pos + (norm * bar_half_w)

                if prev_pt_phys_l is not None and prev_pt_phys_r is not None:
                    # Crear prisma rectangular de colisión para el tramo
                    v0 = bm_phys.verts.new(prev_pt_phys_l)
                    v1 = bm_phys.verts.new(prev_pt_phys_r)
                    v2 = bm_phys.verts.new(pt_r)
                    v3 = bm_phys.verts.new(pt_l)

                    v4 = bm_phys.verts.new(prev_pt_phys_l + Vector((0, 0, bar_height)))
                    v5 = bm_phys.verts.new(prev_pt_phys_r + Vector((0, 0, bar_height)))
                    v6 = bm_phys.verts.new(pt_r + Vector((0, 0, bar_height)))
                    v7 = bm_phys.verts.new(pt_l + Vector((0, 0, bar_height)))

                    # Caras laterales y superior
                    bm_phys.faces.new([v0, v1, v5, v4])
                    bm_phys.faces.new([v1, v2, v6, v5])
                    bm_phys.faces.new([v2, v3, v7, v6])
                    bm_phys.faces.new([v3, v0, v4, v7])
                    bm_phys.faces.new([v4, v5, v6, v7])

                prev_pt_phys_l = pt_l
                prev_pt_phys_r = pt_r

    phys_obj = None
    if bm_phys is not None and len(bm_phys.verts) > 0:
        phys_mesh = bpy.data.meshes.new(phys_name)
        bm_phys.to_mesh(phys_mesh)
        bm_phys.free()

        phys_obj = bpy.data.objects.new(phys_name, phys_mesh)
        phys_obj.display_type = "WIRE"
        phys_obj["track_element_type"] = "WALL"
        col_physics.objects.link(phys_obj)

    return instances_count, phys_obj


class TRACKMAKER_OT_PopulateBarriers(bpy.types.Operator):
    """Genera barreras y muros viales a lo largo del spline activo (New Jersey o Armco SCT)."""

    bl_idname = "track_maker.populate_barriers"
    bl_label = "Generar Barreras y Contenciones"
    bl_description = "Distribuye barreras New Jersey o Armco y crea el colisionador físico 1WALL_ para Assetto Corsa"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        spline_obj = context.active_object if (context.active_object and context.active_object.type == "CURVE") else bpy.data.objects.get("Spline_Route_AB")
        if not spline_obj or spline_obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un spline de carretera válido.")
            return {"CANCELLED"}

        props_cfg = getattr(context.scene, "track_maker_props", None)
        barrier_type = getattr(props_cfg, "barrier_type", "NEW_JERSEY") if props_cfg else "NEW_JERSEY"
        side = getattr(props_cfg, "barrier_side", "CENTER") if props_cfg else "CENTER"
        offset = getattr(props_cfg, "barrier_offset", 0.0) if props_cfg else 0.0

        road_cfg = getattr(context.scene, "track_maker_road", None)
        road_width = getattr(road_cfg, "road_width", 10.0) if road_cfg else 10.0

        seg_len = 3.0 if barrier_type == "NEW_JERSEY" else 4.0

        try:
            count, phys = generate_barriers_along_spline(
                spline_obj,
                barrier_type=barrier_type,
                side=side,
                road_width=road_width,
                lateral_offset=offset,
                segment_length=seg_len,
                create_physics=True,
            )
            self.report({"INFO"}, f"🚧 Generadas {count} secciones de barrera ({barrier_type}) y colisionador 1WALL_.")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error generando barreras: {e}")
            return {"CANCELLED"}


class TRACKMAKER_OT_ClearBarriers(bpy.types.Operator):
    """Elimina todas las barreras y colisionadores de contención de la escena."""

    bl_idname = "track_maker.clear_barriers"
    bl_label = "Limpiar Barreras"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        col = bpy.data.collections.get(COLLECTION_BARRIERS)
        count = 0
        if col:
            objs = list(col.objects)
            for o in objs:
                bpy.data.objects.remove(o, do_unlink=True)
                count += 1

        # Limpiar físicas 1WALL_Barriers
        for o in list(bpy.data.objects):
            if o.name.startswith(f"{PREFIX_PHYS_WALL}Barriers_"):
                bpy.data.objects.remove(o, do_unlink=True)

        self.report({"INFO"}, f"Limpiadas {count} barreras de la escena.")
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_PopulateBarriers,
    TRACKMAKER_OT_ClearBarriers,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
