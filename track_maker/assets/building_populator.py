"""Poblador procedural de edificios y arquitectura mexicana a lo largo del corredor vial.

Distribuye parcelas y clusters con arquitectura auténtica mexicana:
- Tiendas OXXO con marquesinas y estacionamientos.
- Estaciones de servicio y gasolineras con marquesinas Pemex.
- Naves industriales y bodegas de almacenamiento logístico.
- Casas mexicanas autoconstruidas con tinacos Rotoplas negros y castillos con varillas.

Ajusta automáticamente el retranqueo (setback), la orientación hacia la calzada
y apoya los cimientos sobre el terreno DEM mediante BVHTree raycast.
"""

from __future__ import annotations
import math
import random
from typing import Optional, List
import bpy
from mathutils import Vector, bvhtree

from ..core.constants import COLLECTION_ROOT, COLLECTION_BUILDINGS
from ..core.utils import get_or_create_collection
from ..road.road_generator import sample_curve_evaluated
from .mexico_pack import (
    build_oxxo_store_mesh,
    build_gas_station_mesh,
    build_industrial_warehouse_mesh,
    build_mexican_house_with_tinaco_mesh,
)


def populate_buildings_along_corridor(
    curve_obj: bpy.types.Object,
    terrain_obj: Optional[bpy.types.Object] = None,
    spacing_m: float = 120.0,
    setback_m: float = 24.0,
    road_width: float = 10.0,
    density: float = 0.65,
    seed: int = 42,
) -> int:
    """Distribuye edificios temáticos mexicanos a lo largo de los márgenes de la carretera."""
    if not curve_obj or curve_obj.type != "CURVE":
        raise ValueError("Se requiere un objeto CURVE válido.")

    samples = sample_curve_evaluated(curve_obj, step_length=spacing_m)
    if len(samples) < 2:
        return 0

    col_buildings = get_or_create_collection(COLLECTION_BUILDINGS, parent_name=COLLECTION_ROOT)

    # Limpiar edificios previos
    for obj in list(col_buildings.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    # Preparar raycaster contra el terreno DEM si está disponible
    bvh = None
    if terrain_obj and terrain_obj.type == "MESH":
        bvh = bvhtree.BVHTree.FromObject(terrain_obj, bpy.context.evaluated_depsgraph_get())

    # Inicializar mallas de edificios
    mesh_oxxo = build_oxxo_store_mesh()
    mesh_gas = build_gas_station_mesh()
    mesh_warehouse = build_industrial_warehouse_mesh()
    mesh_house = build_mexican_house_with_tinaco_mesh()

    building_types = [
        ("OXXO", mesh_oxxo, 12.0),
        ("GAS_STATION", mesh_gas, 20.0),
        ("WAREHOUSE", mesh_warehouse, 24.0),
        ("MEXICAN_HOUSE", mesh_house, 8.0),
    ]

    rng = random.Random(seed)
    half_road = road_width / 2.0
    count = 0

    for i in range(1, len(samples) - 1):
        # Probabilidad de generar edificio en este tramo
        if rng.random() > density:
            continue

        s = samples[i]
        pos = s["pos"]
        tan = s["tangent"]
        dist = s["dist"]

        # Vector normal perpendicular a la carretera
        norm_r = Vector((tan.y, -tan.x, 0.0)).normalized()
        yaw_road = math.atan2(tan.y, tan.x)

        # Seleccionar lado: Izquierda (-1) o Derecha (+1)
        side = -1.0 if rng.random() < 0.5 else 1.0

        # Seleccionar tipo de edificio (pesos ponderados: casas y bodegas más frecuentes)
        choice = rng.choices(
            building_types,
            weights=[0.15, 0.10, 0.35, 0.40],
            k=1
        )[0]
        b_name_tag, b_mesh, b_front_w = choice

        # Calcular posición con retranqueo respecto al borde de la carretera
        actual_setback = setback_m + rng.uniform(0.0, 10.0)
        target_pos = pos + (norm_r * (side * (half_road + actual_setback)))

        # Ajustar cota Z contra el terreno DEM mediante raycast vertical
        final_z = pos.z
        if bvh is not None and terrain_obj is not None:
            ray_origin = Vector((target_pos.x, target_pos.y, pos.z + 100.0))
            hit_loc, hit_norm, _, _ = bvh.ray_cast(ray_origin, Vector((0, 0, -1.0)))
            if hit_loc is not None:
                final_z = hit_loc.z
            else:
                final_z = pos.z

        building_loc = Vector((target_pos.x, target_pos.y, final_z))

        # Rotación para que la fachada apunte hacia la carretera
        # Si está en el lado derecho, rotar hacia la izquierda (yaw - 90), si está a la izquierda rotar hacia la derecha (yaw + 90)
        if side > 0:
            rot_z = yaw_road - (math.pi / 2.0)
        else:
            rot_z = yaw_road + (math.pi / 2.0)

        obj_name = f"Building_{b_name_tag}_{int(dist)}m_{'R' if side > 0 else 'L'}"
        b_obj = bpy.data.objects.new(obj_name, b_mesh)
        b_obj.location = building_loc
        b_obj.rotation_euler = (0.0, 0.0, rot_z)
        col_buildings.objects.link(b_obj)
        count += 1

    return count


class TRACKMAKER_OT_PopulateBuildings(bpy.types.Operator):
    """Genera edificios temáticos mexicanos (OXXO, gasolineras, bodegas y casas) a lo largo de la ruta."""

    bl_idname = "track_maker.populate_buildings"
    bl_label = "Poblar Edificios (Mexico Pack)"
    bl_description = "Distribuye tiendas OXXO, gasolineras, naves logísticas y casas con tinacos a los lados de la calzada"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        spline_obj = context.active_object if (context.active_object and context.active_object.type == "CURVE") else bpy.data.objects.get("Spline_Route_AB")
        if not spline_obj or spline_obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un spline de carretera válido.")
            return {"CANCELLED"}

        terrain_obj = bpy.data.objects.get("TM_Terrain")

        props_cfg = getattr(context.scene, "track_maker_props", None)
        spacing = getattr(props_cfg, "building_spacing", 120.0) if props_cfg else 120.0
        setback = getattr(props_cfg, "building_setback", 24.0) if props_cfg else 24.0
        density = getattr(props_cfg, "building_density", 0.65) if props_cfg else 0.65

        road_cfg = getattr(context.scene, "track_maker_road", None)
        road_width = getattr(road_cfg, "road_width", 10.0) if road_cfg else 10.0

        try:
            count = populate_buildings_along_corridor(
                spline_obj,
                terrain_obj=terrain_obj,
                spacing_m=spacing,
                setback_m=setback,
                road_width=road_width,
                density=density,
            )
            self.report({"INFO"}, f"🏪 Generados {count} edificios temáticos del Mexico-Pack (OXXO, Pemex, bodegas y casas).")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error poblando edificios: {e}")
            return {"CANCELLED"}


class TRACKMAKER_OT_ClearBuildings(bpy.types.Operator):
    """Elimina todos los edificios de la escena."""

    bl_idname = "track_maker.clear_buildings"
    bl_label = "Limpiar Edificios"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        col = bpy.data.collections.get(COLLECTION_BUILDINGS)
        count = 0
        if col:
            objs = list(col.objects)
            for o in objs:
                bpy.data.objects.remove(o, do_unlink=True)
                count += 1
        self.report({"INFO"}, f"Limpiados {count} edificios de la escena.")
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_PopulateBuildings,
    TRACKMAKER_OT_ClearBuildings,
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
