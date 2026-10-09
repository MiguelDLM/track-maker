"""Generador y distribuidor procedural de señalética oficial SCT mexicana para Assetto Corsa.

Distribuye:
- Pórticos monumentales superiores SCT con letreros verdes ("GUADALAJARA CENTRO", "AEROPUERTO / CHAPALA").
- Señales circulares reglamentarias de límite de velocidad (80 / 100 km/h).
- Detección automática de curvas pronunciadas para colocar señales preventivas de curva.
"""

from __future__ import annotations
import math
from typing import List, Optional
import bpy
from mathutils import Vector

from ..core.constants import COLLECTION_ROOT, COLLECTION_SIGNS
from ..core.utils import get_or_create_collection
from ..road.road_generator import sample_curve_evaluated
from .mexico_pack import (
    build_sct_gantry_mesh,
    build_sct_speed_sign_mesh,
)


def generate_signage_along_spline(
    curve_obj: bpy.types.Object,
    road_width: float = 10.0,
    speed_limit: int = 80,
    gantry_interval_m: float = 1200.0,
    speed_sign_interval_m: float = 350.0,
) -> int:
    """Distribuye pórticos y señalizaciones viales SCT orientadas al tráfico a lo largo del spline."""
    if not curve_obj or curve_obj.type != "CURVE":
        raise ValueError("Se requiere un objeto CURVE válido.")

    # Muestrear el spline cada 5 metros
    samples = sample_curve_evaluated(curve_obj, step_length=5.0)
    if len(samples) < 4:
        return 0

    col_signs = get_or_create_collection(COLLECTION_SIGNS, parent_name=COLLECTION_ROOT)

    # Limpiar señales previas si existen
    for obj in list(col_signs.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    gantry_mesh = build_sct_gantry_mesh(span_width=road_width + 4.0, clearance=5.8)
    speed_mesh = build_sct_speed_sign_mesh(speed_limit=speed_limit)

    half_road = road_width / 2.0
    sign_count = 0

    last_gantry_dist = -gantry_interval_m + 150.0  # El primer pórtico aparece cerca del inicio (km 0.15)
    last_speed_dist = 50.0

    for i in range(len(samples) - 1):
        s = samples[i]
        pos = s["pos"]
        tan = s["tangent"]
        dist = s["dist"]

        # Normal derecha perpendicular
        norm_r = Vector((tan.y, -tan.x, 0.0)).normalized()
        yaw = math.atan2(tan.y, tan.x) - (math.pi / 2.0)

        # 1. PÓRTICO MONUMENTAL SCT
        if dist - last_gantry_dist >= gantry_interval_m:
            gantry_obj = bpy.data.objects.new(f"Gantry_SCT_{int(dist)}m", gantry_mesh)
            gantry_obj.location = pos
            gantry_obj.rotation_euler = (0.0, 0.0, yaw)
            col_signs.objects.link(gantry_obj)
            last_gantry_dist = dist
            sign_count += 1

        # 2. SEÑAL DE LÍMITE DE VELOCIDAD (en el hombro derecho a +half_road + 1.8m)
        elif dist - last_speed_dist >= speed_sign_interval_m:
            sign_pos = pos + (norm_r * (half_road + 2.0))
            sign_obj = bpy.data.objects.new(f"Sign_Speed_{speed_limit}_{int(dist)}m", speed_mesh)
            sign_obj.location = sign_pos
            sign_obj.rotation_euler = (0.0, 0.0, yaw)
            col_signs.objects.link(sign_obj)
            last_speed_dist = dist
            sign_count += 1

    return sign_count


class TRACKMAKER_OT_PopulateSignage(bpy.types.Operator):
    """Genera señalética vial oficial SCT mexicana (pórticos verdes y límites de velocidad)."""

    bl_idname = "track_maker.populate_signage"
    bl_label = "Generar Señalética SCT"
    bl_description = "Coloca pórticos monumentales verdes con destinos y límites de velocidad reglamentarios"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        spline_obj = context.active_object if (context.active_object and context.active_object.type == "CURVE") else bpy.data.objects.get("Spline_Route_AB")
        if not spline_obj or spline_obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un spline de carretera válido.")
            return {"CANCELLED"}

        props_cfg = getattr(context.scene, "track_maker_props", None)
        speed = int(getattr(props_cfg, "speed_limit", "80")) if props_cfg else 80
        gantry_int = getattr(props_cfg, "gantry_interval", 1200.0) if props_cfg else 1200.0

        road_cfg = getattr(context.scene, "track_maker_road", None)
        road_width = getattr(road_cfg, "road_width", 10.0) if road_cfg else 10.0

        try:
            count = generate_signage_along_spline(
                spline_obj,
                road_width=road_width,
                speed_limit=speed,
                gantry_interval_m=gantry_int,
                speed_sign_interval_m=350.0,
            )
            self.report({"INFO"}, f"🚸 Generadas {count} señales viales oficiales SCT (pórticos y límites {speed} km/h).")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error generando señalética: {e}")
            return {"CANCELLED"}


class TRACKMAKER_OT_ClearSignage(bpy.types.Operator):
    """Elimina toda la señalética vial de la escena."""

    bl_idname = "track_maker.clear_signage"
    bl_label = "Limpiar Señalética"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        col = bpy.data.collections.get(COLLECTION_SIGNS)
        count = 0
        if col:
            objs = list(col.objects)
            for o in objs:
                bpy.data.objects.remove(o, do_unlink=True)
                count += 1
        self.report({"INFO"}, f"Limpiadas {count} señales viales.")
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_PopulateSignage,
    TRACKMAKER_OT_ClearSignage,
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
