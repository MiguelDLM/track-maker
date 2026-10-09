"""Generador y distribuidor procedural de iluminación vial para autopistas de Assetto Corsa.

Distribuye luminarias modernas de acero con brazo(s) curvos y cabezales LED emissive
para el camellón central o laterales de la calzada, compatible con Assetto Corsa CSP (Shaders Patch)
para carreras nocturnas.
"""

from __future__ import annotations
import math
from typing import Optional
import bpy
from mathutils import Vector

from ..core.constants import COLLECTION_ROOT, COLLECTION_LIGHTING
from ..core.utils import get_or_create_collection
from ..road.road_generator import sample_curve_evaluated
from .mexico_pack import build_highway_lighting_mesh


def generate_lighting_along_spline(
    curve_obj: bpy.types.Object,
    spacing_m: float = 40.0,
    placement: str = "CENTER",
    road_width: float = 10.0,
    lateral_offset: float = 0.0,
) -> int:
    """Distribuye postes de alumbrado de autopista a lo largo del trazado."""
    if not curve_obj or curve_obj.type != "CURVE":
        raise ValueError("Se requiere un objeto CURVE válido.")

    samples = sample_curve_evaluated(curve_obj, step_length=spacing_m)
    if len(samples) < 2:
        return 0

    col_lighting = get_or_create_collection(COLLECTION_LIGHTING, parent_name=COLLECTION_ROOT)

    # Limpiar luminarias previas
    for obj in list(col_lighting.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    is_double = (placement == "CENTER")
    light_mesh = build_highway_lighting_mesh(height=10.0, is_double=is_double)

    half_road = road_width / 2.0
    count = 0

    for i, s in enumerate(samples):
        pos = s["pos"]
        tan = s["tangent"]
        dist = s["dist"]

        norm_r = Vector((tan.y, -tan.x, 0.0)).normalized()
        yaw = math.atan2(tan.y, tan.x) - (math.pi / 2.0)

        if placement == "CENTER":
            pole_pos = pos + (norm_r * lateral_offset)
        elif placement == "LEFT":
            pole_pos = pos - (norm_r * (half_road + lateral_offset + 1.5))
        elif placement == "RIGHT":
            pole_pos = pos + (norm_r * (half_road + lateral_offset + 1.5))
        else:
            pole_pos = pos

        pole_obj = bpy.data.objects.new(f"Highway_Light_{i:04d}", light_mesh)
        pole_obj.location = pole_pos
        pole_obj.rotation_euler = (0.0, 0.0, yaw)
        col_lighting.objects.link(pole_obj)
        count += 1

    return count


class TRACKMAKER_OT_PopulateLighting(bpy.types.Operator):
    """Genera luminarias de autopista con brazos LED dobles a lo largo del trazado."""

    bl_idname = "track_maker.populate_lighting"
    bl_label = "Generar Alumbrado de Autopista"
    bl_description = "Coloca luminarias LED de acero cada 35-40 metros para ambientación diurna y nocturna"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        spline_obj = context.active_object if (context.active_object and context.active_object.type == "CURVE") else bpy.data.objects.get("Spline_Route_AB")
        if not spline_obj or spline_obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un spline de carretera válido.")
            return {"CANCELLED"}

        props_cfg = getattr(context.scene, "track_maker_props", None)
        spacing = getattr(props_cfg, "light_spacing", 40.0) if props_cfg else 40.0
        placement = getattr(props_cfg, "light_placement", "CENTER") if props_cfg else "CENTER"

        road_cfg = getattr(context.scene, "track_maker_road", None)
        road_width = getattr(road_cfg, "road_width", 10.0) if road_cfg else 10.0

        try:
            count = generate_lighting_along_spline(
                spline_obj,
                spacing_m=spacing,
                placement=placement,
                road_width=road_width,
            )
            self.report({"INFO"}, f"💡 Generadas {count} luminarias de autopista a lo largo de la ruta.")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error generando alumbrado: {e}")
            return {"CANCELLED"}


class TRACKMAKER_OT_ClearLighting(bpy.types.Operator):
    """Elimina las luminarias de la escena."""

    bl_idname = "track_maker.clear_lighting"
    bl_label = "Limpiar Alumbrado"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        col = bpy.data.collections.get(COLLECTION_LIGHTING)
        count = 0
        if col:
            objs = list(col.objects)
            for o in objs:
                bpy.data.objects.remove(o, do_unlink=True)
                count += 1
        self.report({"INFO"}, f"Limpiadas {count} luminarias.")
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_PopulateLighting,
    TRACKMAKER_OT_ClearLighting,
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
