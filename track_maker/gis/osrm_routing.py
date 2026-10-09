"""Enrutador y generador de trazados reales punto a punto (OSRM - Open Source Routing Machine).

Obtiene la ruta real conducida entre un Punto A (Salida) y un Punto B (Meta)
directamente desde OpenStreetMap OSRM, genera un spline 3D continuo en Blender
con cota Z sobre el terreno DEM y crea automáticamente las puertas de tramo
de Assetto Corsa (AC_AB_START y AC_AB_FINISH).
"""

from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import List, Tuple
import bpy
from mathutils import Vector, bvhtree

from .geo_anchor import wgs84_to_utm
from .viewport_tools import adjust_viewport_clipping, frame_active_object

OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving/{lon_a},{lat_a};{lon_b},{lat_b}?overview=full&geometries=geojson"
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) TrackMaker/1.0 (Blender Addon; migueldlm1307@gmail.com)"


def fetch_osrm_route(
    lat_a: float,
    lon_a: float,
    lat_b: float,
    lon_b: float,
    user_agent: str = DEFAULT_USER_AGENT,
) -> Tuple[List[Tuple[float, float]], float, float]:
    """Obtiene la lista de coordenadas GPS [(lat, lon), ...] de la carretera real entre A y B."""
    url = OSRM_ROUTE_URL.format(lat_a=lat_a, lon_a=lon_a, lat_b=lat_b, lon_b=lon_b)
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Error HTTP consultando OSRM ({e.code}): {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Error de red consultando OSRM: {e.reason}")

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"OSRM no pudo encontrar una carretera transitable entre los puntos: {data.get('code')}")

    route = data["routes"][0]
    distance_km = float(route["distance"]) / 1000.0
    duration_min = float(route["duration"]) / 60.0

    # OSRM devuelve [lon, lat] en formato GeoJSON
    raw_coords = route["geometry"]["coordinates"]
    coords_lat_lon = [(float(c[1]), float(c[0])) for c in raw_coords]

    return coords_lat_lon, distance_km, duration_min


def create_ab_route_curve(
    context,
    coords: List[Tuple[float, float]],
    obj_name: str = "Spline_Route_AB",
    snap_to_terrain: bool = True,
    terrain_obj_name: str = "TM_Terrain",
    offset_z: float = 0.05,
) -> bpy.types.Object:
    """Crea una curva 3D en Blender a partir de las coordenadas del tramo A-B."""
    gis_cfg = context.scene.track_maker_gis

    # Asegurar Ancla Georreferenciada en el centroide del tramo
    if not gis_cfg.has_anchor:
        center_lat = (coords[0][0] + coords[-1][0]) / 2.0
        center_lon = (coords[0][1] + coords[-1][1]) / 2.0
        easting, northing, zone, hem = wgs84_to_utm(center_lat, center_lon)
        gis_cfg.anchor_utm_x = easting
        gis_cfg.anchor_utm_y = northing
        gis_cfg.has_anchor = True
        gis_cfg.epsg_code = (32600 if hem == "N" else 32700) + zone

    # Preparar raycaster si hay terreno disponible
    bvh = None
    terrain_obj = bpy.data.objects.get(terrain_obj_name)
    mat_world = terrain_obj.matrix_world if terrain_obj else None
    inv_mat = mat_world.inverted() if mat_world else None

    if snap_to_terrain and terrain_obj and terrain_obj.type == "MESH":
        depsgraph = context.evaluated_depsgraph_get()
        bvh = bvhtree.BVHTree.FromObject(terrain_obj, depsgraph)

    local_points: List[Vector] = []
    real_altitudes: List[float] = []
    last_valid_z = None

    for lat, lon in coords:
        easting, northing, _, _ = wgs84_to_utm(lat, lon)
        lx = easting - gis_cfg.anchor_utm_x
        ly = northing - gis_cfg.anchor_utm_y
        lz = 0.0

        if bvh and inv_mat and mat_world:
            ray_origin_world = Vector((lx, ly, 10000.0))
            ray_dir_world = Vector((0.0, 0.0, -1.0))
            ray_origin_local = inv_mat @ ray_origin_world
            ray_dir_local = (inv_mat.to_3x3() @ ray_dir_world).normalized()

            hit_loc, _, _, _ = bvh.ray_cast(ray_origin_local, ray_dir_local)
            if hit_loc:
                hit_world = mat_world @ hit_loc
                lz = hit_world.z + offset_z
                last_valid_z = lz
            elif last_valid_z is not None:
                lz = last_valid_z

        local_points.append(Vector((lx, ly, lz)))
        v_scale = getattr(gis_cfg, "vertical_scale", 1.0) or 1.0
        real_alt = (lz / v_scale) + getattr(gis_cfg, "anchor_elevation_z", 0.0)
        real_altitudes.append(real_alt)

    # Crear colección de rutas si no existe
    col_name = "TM_OSM_Roads"
    col = bpy.data.collections.get(col_name)
    if not col:
        col = bpy.data.collections.new(col_name)
        context.scene.collection.children.link(col)

    # Crear Curva Bézier 3D
    curve_data = bpy.data.curves.new(name=f"{obj_name}_Data", type="CURVE")
    curve_data.dimensions = "3D"
    spline = curve_data.splines.new("BEZIER")
    spline.bezier_points.add(len(local_points) - 1)

    for i, pt in enumerate(local_points):
        bp = spline.bezier_points[i]
        bp.co = pt
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"

    spline.use_cyclic_u = False  # Tramo punto a punto abierto

    obj = bpy.data.objects.new(obj_name, curve_data)
    col.objects.link(obj)

    # Seleccionar y activar objeto
    for o in context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj

    return obj, real_altitudes, local_points


class TRACKMAKER_OT_FetchOSRMRoute(bpy.types.Operator):
    """Obtiene la ruta navegable real entre el Punto A y Punto B y genera la curva 3D."""

    bl_idname = "track_maker.fetch_osrm_route"
    bl_label = "Trazar Ruta Real A ➔ B (OSRM)"
    bl_description = "Calcula la carretera transitable exacta entre las dos coordenadas GPS y crea la curva 3D"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        lat_a = gis_cfg.point_a_lat
        lon_a = gis_cfg.point_a_lon
        lat_b = gis_cfg.point_b_lat
        lon_b = gis_cfg.point_b_lon

        self.report({"INFO"}, f"Calculando ruta por carretera de A ({lat_a:.4f}, {lon_a:.4f}) a B ({lat_b:.4f}, {lon_b:.4f})...")

        try:
            coords, dist_km, dur_min = fetch_osrm_route(lat_a, lon_a, lat_b, lon_b)
            if not coords:
                self.report({"WARNING"}, "No se encontraron coordenadas en la ruta calculada.")
                return {"CANCELLED"}

            spline_obj, real_altitudes, local_points = create_ab_route_curve(
                context=context,
                coords=coords,
                obj_name="Spline_Route_AB",
                snap_to_terrain=gis_cfg.osm_snap_to_terrain,
                terrain_obj_name=gis_cfg.target_terrain_name or "TM_Terrain",
                offset_z=gis_cfg.snap_elevation_offset,
            )

            # Establecer tipo de circuito como HILLCLIMB_AB para Assetto Corsa
            if hasattr(context.scene, "track_maker_circuit"):
                context.scene.track_maker_circuit.circuit_type = "HILLCLIMB_AB"

            # Actualizar estadísticas altimétricas
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

            # Ajustar visor y encuadrar
            if gis_cfg.auto_adjust_clipping:
                max_span = max(spline_obj.dimensions.x, spline_obj.dimensions.y, dist_km * 1000.0)
                adjust_viewport_clipping(context, max_span)
            if gis_cfg.auto_frame_view:
                frame_active_object(context)

            self.report(
                {"INFO"},
                f"Ruta trazada: {dist_km:.2f} km | Cota: {min(real_altitudes):.0f}m a {max(real_altitudes):.0f}m (Desnivel: {max(real_altitudes)-min(real_altitudes):.0f}m)",
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error calculando ruta OSRM: {e}")
            return {"CANCELLED"}


class TRACKMAKER_OT_SwapPointsAB(bpy.types.Operator):
    """Intercambia el Punto A y el Punto B (para invertir la dirección de subida/bajada)."""

    bl_idname = "track_maker.swap_points_ab"
    bl_label = "Invertir Sentido (A ⇄ B)"
    bl_description = "Intercambia la salida y la meta para invertir el trazado"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        tmp_lat = gis_cfg.point_a_lat
        tmp_lon = gis_cfg.point_a_lon

        gis_cfg.point_a_lat = gis_cfg.point_b_lat
        gis_cfg.point_a_lon = gis_cfg.point_b_lon

        gis_cfg.point_b_lat = tmp_lat
        gis_cfg.point_b_lon = tmp_lon

        self.report({"INFO"}, "Puntos de Salida A y Meta B intercambiados.")
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_FetchOSRMRoute,
    TRACKMAKER_OT_SwapPointsAB,
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
