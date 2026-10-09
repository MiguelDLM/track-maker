"""Generador unificado de tramos reales A-B (Pipeline Ruta-Primero: OSRM + DEM + Puertas AC).

Implementa el flujo de trabajo natural:
1. Obtiene la ruta de conducción real entre Salida (Punto A) y Meta (Punto B).
2. Calcula el corredor delimitador (Bounding Box) exacto de las curvas del trazado.
3. Descarga la topografía DEM (AWS Terrarium) adaptada a ese corredor con la escala vertical elegida.
4. Genera la curva 3D Bézier proyectando con raycast sobre la superficie del relieve.
5. Coloca automáticamente las puertas de cronometraje de Assetto Corsa (AC_AB_START y AC_AB_FINISH).
6. Ajusta el límite de visión lejano (clip_end) del visor 3D y centra la cámara sobre el tramo.
"""

from __future__ import annotations
import math
from typing import List, Tuple
import bpy
from mathutils import Vector, Euler

from .osrm_routing import fetch_osrm_route, create_ab_route_curve
from .dem_downloader import EARTH_RADIUS_KM, download_elevation_grid, create_blender_terrain_mesh
from .viewport_tools import adjust_viewport_clipping, frame_active_object
from ..core.constants import (
    NAME_AB_START_L,
    NAME_AB_START_R,
    NAME_AB_FINISH_L,
    NAME_AB_FINISH_R,
    ELEMENT_TIMING_GATE,
)
from ..core.utils import create_ac_empty


def bbox_from_route_coords(
    coords: List[Tuple[float, float]],
    margin_km: float = 1.0,
) -> Tuple[float, float, float, float]:
    """Calcula el bounding box exacto alrededor de todos los puntos de la ruta con un margen en km."""
    if not coords:
        raise ValueError("La lista de coordenadas está vacía.")

    lats = [c[0] for c in coords]
    lons = [c[1] for c in coords]

    min_lat_raw = min(lats)
    max_lat_raw = max(lats)
    min_lon_raw = min(lons)
    max_lon_raw = max(lons)

    center_lat = (min_lat_raw + max_lat_raw) / 2.0
    delta_lat_deg = math.degrees(margin_km / EARTH_RADIUS_KM)
    lat_rad = math.radians(center_lat)
    cos_lat = max(0.01, math.cos(lat_rad))
    delta_lon_deg = math.degrees(margin_km / (EARTH_RADIUS_KM * cos_lat))

    min_lat = max(-85.0, min_lat_raw - delta_lat_deg)
    max_lat = min(85.0, max_lat_raw + delta_lat_deg)
    min_lon = max(-180.0, min_lon_raw - delta_lon_deg)
    max_lon = min(180.0, max_lon_raw + delta_lon_deg)

    return min_lat, min_lon, max_lat, max_lon


def place_ab_timing_gates_on_curve(
    context,
    curve_obj: bpy.types.Object,
    gate_width: float = 16.0,
) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    """Coloca automáticamente las puertas AC_AB_START y AC_AB_FINISH en los extremos de la curva."""
    if not curve_obj or curve_obj.type != "CURVE" or not curve_obj.data.splines:
        raise ValueError("Se requiere un objeto de curva válido con al menos un spline.")

    spline = curve_obj.data.splines[0]
    mat_world = curve_obj.matrix_world

    # Obtener puntos iniciales y finales
    if spline.type == "BEZIER":
        pts = spline.bezier_points
        if len(pts) < 2:
            raise ValueError("El spline Bézier requiere al menos 2 puntos.")
        p0 = mat_world @ pts[0].co
        p1 = mat_world @ pts[1].co
        pn = mat_world @ pts[-1].co
        p_prev = mat_world @ pts[-2].co
    else:  # POLY o NURBS
        pts = spline.points
        if len(pts) < 2:
            raise ValueError("El spline requiere al menos 2 puntos.")
        p0 = mat_world @ pts[0].co.to_3d()
        p1 = mat_world @ pts[1].co.to_3d()
        pn = mat_world @ pts[-1].co.to_3d()
        p_prev = mat_world @ pts[-2].co.to_3d()

    half_w = gate_width / 2.0

    # 1. Puerta de Salida (AC_AB_START)
    tan_start = (p1 - p0).to_2d()
    if tan_start.length == 0:
        tan_start = Vector((0.0, 1.0))
    else:
        tan_start = tan_start.normalized()

    right_start = Vector((-tan_start.y, tan_start.x, 0.0))
    yaw_start = math.atan2(tan_start.y, tan_start.x) - math.pi / 2.0
    rot_start = Euler((0.0, 0.0, yaw_start), "XYZ")

    pos_start_l = p0 - (right_start * half_w) + Vector((0.0, 0.0, 0.5))
    pos_start_r = p0 + (right_start * half_w) + Vector((0.0, 0.0, 0.5))

    empty_start_l = create_ac_empty(
        name=NAME_AB_START_L,
        location=pos_start_l,
        rotation_euler=rot_start,
        display_type="SPHERE",
        display_size=1.0,
        element_type=ELEMENT_TIMING_GATE,
    )
    empty_start_r = create_ac_empty(
        name=NAME_AB_START_R,
        location=pos_start_r,
        rotation_euler=rot_start,
        display_type="SPHERE",
        display_size=1.0,
        element_type=ELEMENT_TIMING_GATE,
    )

    # 2. Puerta de Meta (AC_AB_FINISH)
    tan_end = (pn - p_prev).to_2d()
    if tan_end.length == 0:
        tan_end = Vector((0.0, 1.0))
    else:
        tan_end = tan_end.normalized()

    right_end = Vector((-tan_end.y, tan_end.x, 0.0))
    yaw_end = math.atan2(tan_end.y, tan_end.x) - math.pi / 2.0
    rot_end = Euler((0.0, 0.0, yaw_end), "XYZ")

    pos_end_l = pn - (right_end * half_w) + Vector((0.0, 0.0, 0.5))
    pos_end_r = pn + (right_end * half_w) + Vector((0.0, 0.0, 0.5))

    empty_finish_l = create_ac_empty(
        name=NAME_AB_FINISH_L,
        location=pos_end_l,
        rotation_euler=rot_end,
        display_type="SPHERE",
        display_size=1.0,
        element_type=ELEMENT_TIMING_GATE,
    )
    empty_finish_r = create_ac_empty(
        name=NAME_AB_FINISH_R,
        location=pos_end_r,
        rotation_euler=rot_end,
        display_type="SPHERE",
        display_size=1.0,
        element_type=ELEMENT_TIMING_GATE,
    )

    return empty_start_l, empty_start_r, empty_finish_l, empty_finish_r


def build_complete_ab_stage(context) -> dict:
    """Ejecuta el pipeline completo Ruta-Primero entre los puntos A y B de la escena."""
    gis_cfg = context.scene.track_maker_gis
    lat_a = gis_cfg.point_a_lat
    lon_a = gis_cfg.point_a_lon
    lat_b = gis_cfg.point_b_lat
    lon_b = gis_cfg.point_b_lon
    margin_km = gis_cfg.corridor_margin_km
    zoom = gis_cfg.dem_zoom
    res = gis_cfg.terrain_resolution

    # Paso 1: Obtener ruta por carretera real desde OSRM
    coords, dist_km, dur_min = fetch_osrm_route(lat_a, lon_a, lat_b, lon_b)
    if not coords:
        raise RuntimeError("OSRM no devolvió puntos para la ruta solicitada.")

    # Paso 2: Calcular Bounding Box exacto del trazado con margen
    bbox = bbox_from_route_coords(coords, margin_km=margin_km)
    min_lat, min_lon, max_lat, max_lon = bbox
    center_lat = (min_lat + max_lat) / 2.0
    center_lon = (min_lon + max_lon) / 2.0

    # Paso 3: Descargar mosaicos de elevación AWS Terrarium para el corredor
    elev_grid, bbox_out, width_m, height_m = download_elevation_grid(
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=margin_km,
        bbox=bbox,
        zoom=zoom,
        target_resolution=res,
    )

    # Paso 4: Generar malla de terreno 3D en Blender (fija ancla UTM y elevación Z)
    terrain_obj = create_blender_terrain_mesh(
        context=context,
        elevation=elev_grid,
        center_lat=center_lat,
        center_lon=center_lon,
        width_m=width_m,
        height_m=height_m,
        bbox=bbox_out,
        obj_name="TM_Terrain",
    )

    # Paso 5: Generar Spline 3D proyectado por raycast sobre la topografía
    spline_obj, real_altitudes, local_points = create_ab_route_curve(
        context=context,
        coords=coords,
        obj_name="Spline_Route_AB",
        snap_to_terrain=True,
        terrain_obj_name=terrain_obj.name,
        offset_z=gis_cfg.snap_elevation_offset,
    )

    # Paso 6: Colocar puertas de cronometraje de Assetto Corsa
    timing_cfg = getattr(context.scene, "track_maker_timing", None)
    gate_width = getattr(timing_cfg, "gate_width", 16.0) if timing_cfg else 16.0
    gates = place_ab_timing_gates_on_curve(context, spline_obj, gate_width=gate_width)

    # Paso 7: Configurar tipo de circuito como HILLCLIMB_AB
    if hasattr(context.scene, "track_maker_circuit"):
        context.scene.track_maker_circuit.circuit_type = "HILLCLIMB_AB"

    # Paso 8: Actualizar estadísticas altimétricas
    gis_cfg.route_info_distance = dist_km
    if real_altitudes:
        min_a = min(real_altitudes)
        max_a = max(real_altitudes)
        gis_cfg.route_info_min_elev = min_a
        gis_cfg.route_info_max_elev = max_a
        gis_cfg.route_info_climb = max_a - min_a
        grades = []
        for i in range(1, len(local_points)):
            dd = (local_points[i] - local_points[i - 1]).length
            dz = abs(local_points[i].z - local_points[i - 1].z)
            if dd > 1.0:
                grades.append((dz / dd) * 100.0)
        gis_cfg.route_info_max_grade = max(grades) if grades else 0.0

    # Paso 9: Ajustar visor y encuadrar
    if gis_cfg.auto_adjust_clipping:
        max_span = max(width_m, height_m, dist_km * 1000.0)
        adjust_viewport_clipping(context, max_span)
    if gis_cfg.auto_frame_view:
        for o in context.selected_objects:
            o.select_set(False)
        spline_obj.select_set(True)
        context.view_layer.objects.active = spline_obj
        frame_active_object(context)

    return {
        "terrain_obj": terrain_obj,
        "spline_obj": spline_obj,
        "gates": gates,
        "distance_km": dist_km,
        "min_elevation": min(real_altitudes) if real_altitudes else 0.0,
        "max_elevation": max(real_altitudes) if real_altitudes else 0.0,
        "climb_m": (max(real_altitudes) - min(real_altitudes)) if real_altitudes else 0.0,
    }


class TRACKMAKER_OT_BuildFullABStage(bpy.types.Operator):
    """Flujo 1-Clic: Descarga la ruta real OSRM, genera el terreno DEM del corredor exacto, proyecta la cota 3D y coloca las puertas AC."""

    bl_idname = "track_maker.build_full_ab_stage"
    bl_label = "⚡ Crear Tramo Completo A ➔ B (Ruta + Relieve 3D)"
    bl_description = (
        "Calcula la ruta de carretera real entre A y B, descarga la topografía DEM correspondiente a ese corredor, "
        "genera el spline 3D ajustado al relieve y añade las puertas de salida y meta de Assetto Corsa"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        self.report(
            {"INFO"},
            f"Construyendo tramo completo A ({gis_cfg.point_a_lat:.4f}) ➔ B ({gis_cfg.point_b_lat:.4f})...",
        )

        try:
            res = build_complete_ab_stage(context)
            dist_km = res["distance_km"]
            climb = res["climb_m"]
            min_e = res["min_elevation"]
            max_e = res["max_elevation"]

            self.report(
                {"INFO"},
                f"✅ Tramo A-B completado: {dist_km:.2f} km | Cota {min_e:.0f}m - {max_e:.0f}m (Desnivel: {climb:.0f}m) | Puertas AC creadas",
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error creando tramo completo A-B: {e}")
            return {"CANCELLED"}


classes = (
    TRACKMAKER_OT_BuildFullABStage,
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
