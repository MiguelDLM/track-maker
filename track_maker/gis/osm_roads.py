"""Importador de carreteras, tramos de montaña y circuitos reales desde OpenStreetMap (Overpass API).

Permite consultar la API Overpass de OpenStreetMap para extraer vías ('highway=raceway',
'motorway', 'primary', etc.) alrededor de unas coordenadas GPS, transformarlas a
coordenadas locales métricas respecto al Geo-Anchor (0, 0, 0) y generar curvas 3D nativas
en Blender con proyección opcional sobre el terreno DEM.
"""

from __future__ import annotations
import json
import math
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Tuple, Optional
import bpy
from mathutils import Vector, bvhtree

from .geo_anchor import wgs84_to_utm
from .viewport_tools import adjust_viewport_clipping, frame_active_object
from .dem_downloader import bbox_from_points_ab

OVERPASS_ENDPOINTS = [
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]

DEFAULT_USER_AGENT = "TrackMaker/1.0 (Blender Addon; https://github.com/user/track-maker)"


def query_overpass_api(
    lat: float,
    lon: float,
    radius_m: float = 2000.0,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    highway_filter: str = "raceway",
    timeout: int = 25,
) -> dict:
    """Envía una consulta a los servidores Overpass API con failover automático entre réplicas."""
    if bbox is not None:
        south, west, north, east = bbox
        target_selector = f"{south:.6f},{west:.6f},{north:.6f},{east:.6f}"
    else:
        target_selector = f"around:{int(radius_m)},{lat:.6f},{lon:.6f}"

    query = f"""[out:json][timeout:{timeout}];
(
  way["highway"~"{highway_filter}"]({target_selector});
);
out body;
>;
out skel qt;"""

    post_data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    last_error = None

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            req = urllib.request.Request(
                endpoint,
                data=post_data,
                headers={"User-Agent": DEFAULT_USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Todas las réplicas de Overpass API fallaron. Último error: {last_error}")


def chain_way_segments(ways: List[dict], nodes_map: Dict[int, Tuple[float, float]]) -> List[List[Tuple[float, float]]]:
    """Encadena tramos de vías contiguos que comparten nodos finales para formar trazados continuos o circuitos cerrados."""
    # Convertir cada vía a una lista de coordenadas [(lat, lon), ...]
    polylines: List[List[Tuple[float, float]]] = []
    for w in ways:
        w_nodes = w.get("nodes", [])
        pts = [nodes_map[nid] for nid in w_nodes if nid in nodes_map]
        if len(pts) >= 2:
            polylines.append(pts)

    if not polylines:
        return []

    # Unir progresivamente polilíneas contiguas
    merged = True
    while merged:
        merged = False
        for i in range(len(polylines)):
            if not polylines[i]:
                continue
            head_a = polylines[i][0]
            tail_a = polylines[i][-1]

            for j in range(i + 1, len(polylines)):
                if not polylines[j]:
                    continue
                head_b = polylines[j][0]
                tail_b = polylines[j][-1]

                # Distancia umbral en grados (~2 metros)
                eps = 0.00003

                # Caso 1: tail_a coincide con head_b
                if abs(tail_a[0] - head_b[0]) < eps and abs(tail_a[1] - head_b[1]) < eps:
                    polylines[i] = polylines[i] + polylines[j][1:]
                    polylines[j] = []
                    merged = True
                    break
                # Caso 2: tail_a coincide con tail_b (invertir b)
                elif abs(tail_a[0] - tail_b[0]) < eps and abs(tail_a[1] - tail_b[1]) < eps:
                    polylines[i] = polylines[i] + polylines[j][-2::-1]
                    polylines[j] = []
                    merged = True
                    break
                # Caso 3: head_a coincide con tail_b
                elif abs(head_a[0] - tail_b[0]) < eps and abs(head_a[1] - tail_b[1]) < eps:
                    polylines[i] = polylines[j] + polylines[i][1:]
                    polylines[j] = []
                    merged = True
                    break
                # Caso 4: head_a coincide con head_b (invertir b)
                elif abs(head_a[0] - head_b[0]) < eps and abs(head_a[1] - head_b[1]) < eps:
                    polylines[i] = polylines[j][::-1] + polylines[i][1:]
                    polylines[j] = []
                    merged = True
                    break

            if merged:
                break

    return [p for p in polylines if len(p) >= 2]


def create_osm_curve_objects(
    context,
    polylines: List[List[Tuple[float, float]]],
    base_name: str = "Spline_OSM",
    curve_type: str = "BEZIER",
    snap_to_terrain: bool = True,
    terrain_obj_name: str = "TM_Terrain",
    offset_z: float = 0.05,
) -> List[bpy.types.Object]:
    """Genera objetos de Curva 3D en Blender a partir de las coordenadas de las vías OSM."""
    gis_cfg = context.scene.track_maker_gis

    # Preparar raycaster BVHTree si se solicita proyección sobre terreno
    bvh = None
    terrain_obj = bpy.data.objects.get(terrain_obj_name)
    if snap_to_terrain and terrain_obj and terrain_obj.type == "MESH":
        depsgraph = context.evaluated_depsgraph_get()
        bvh = bvhtree.BVHTree.FromObject(terrain_obj, depsgraph)

    # Colección de destino
    col_name = "TM_OSM_Roads"
    col = bpy.data.collections.get(col_name)
    if not col:
        col = bpy.data.collections.new(col_name)
        context.scene.collection.children.link(col)

    created_objects = []

    for idx, poly in enumerate(polylines):
        # Nombre de la vía
        obj_name = f"{base_name}_{idx + 1}" if len(polylines) > 1 else base_name

        # Convertir coordenadas WGS84 -> UTM -> Local Blender
        local_coords: List[Vector] = []
        for lat, lon in poly:
            easting, northing, _, _ = wgs84_to_utm(lat, lon)
            local_x = easting - gis_cfg.anchor_utm_x
            local_y = northing - gis_cfg.anchor_utm_y
            local_z = 0.0

            # Proyectar sobre terreno si está disponible
            if bvh:
                ray_origin = Vector((local_x, local_y, 5000.0))
                ray_dir = Vector((0.0, 0.0, -1.0))
                hit_loc, _, _, _ = bvh.ray_cast(ray_origin, ray_dir)
                if hit_loc:
                    local_z = hit_loc.z + offset_z

            local_coords.append(Vector((local_x, local_y, local_z)))

        # Comprobar si es un circuito cerrado (loop)
        is_closed = False
        if len(local_coords) >= 3:
            dist_ends = (local_coords[0] - local_coords[-1]).length
            if dist_ends < 5.0:  # Menos de 5 metros entre inicio y fin
                is_closed = True
                local_coords.pop()  # Eliminar el punto duplicado final para cerrar el spline limpiamente

        # Crear curva
        curve_data = bpy.data.curves.new(name=f"{obj_name}_Data", type="CURVE")
        curve_data.dimensions = "3D"

        if curve_type == "BEZIER":
            spline = curve_data.splines.new("BEZIER")
            spline.bezier_points.add(len(local_coords) - 1)
            for i, co in enumerate(local_coords):
                bp = spline.bezier_points[i]
                bp.co = co
                bp.handle_left_type = "AUTO"
                bp.handle_right_type = "AUTO"
            spline.use_cyclic_u = is_closed
        else:  # POLY
            spline = curve_data.splines.new("POLY")
            spline.points.add(len(local_coords) - 1)
            for i, co in enumerate(local_coords):
                spline.points[i].co = Vector((co.x, co.y, co.z, 1.0))
            spline.use_cyclic_u = is_closed

        obj = bpy.data.objects.new(obj_name, curve_data)
        col.objects.link(obj)
        created_objects.append(obj)

    return created_objects


class TRACKMAKER_OT_ImportOSMRoads(bpy.types.Operator):
    """Importa carreteras y trazados de circuitos reales desde OpenStreetMap (Overpass API)."""

    bl_idname = "track_maker.import_osm_roads"
    bl_label = "Importar Trazado OSM"
    bl_description = "Descarga vías públicas o circuitos (raceway) de OpenStreetMap y genera splines 3D"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        lat = gis_cfg.latitude
        lon = gis_cfg.longitude
        radius = gis_cfg.osm_radius_m
        road_type = gis_cfg.osm_road_type

        # Determinar filtro regex según tipo de vía
        if road_type == "RACEWAY":
            filter_pattern = "^(raceway)$"
        elif road_type == "MAIN_ROADS":
            filter_pattern = "^(motorway|trunk|primary|secondary|tertiary)$"
        elif road_type == "ALL_ROADS":
            filter_pattern = "^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|raceway)$"
        else:  # CUSTOM
            filter_pattern = gis_cfg.osm_custom_filter or "raceway"

        if gis_cfg.coverage_mode == "POINTS_AB":
            lat_a, lon_a = gis_cfg.point_a_lat, gis_cfg.point_a_lon
            lat_b, lon_b = gis_cfg.point_b_lat, gis_cfg.point_b_lon
            center_lat = (lat_a + lat_b) / 2.0
            center_lon = (lon_a + lon_b) / 2.0
            bbox = bbox_from_points_ab(lat_a, lon_a, lat_b, lon_b, gis_cfg.corridor_margin_km)
            self.report({"INFO"}, f"Consultando Overpass API tramo A-B ({filter_pattern}) con margen {gis_cfg.corridor_margin_km:.1f}km...")
        else:
            center_lat = gis_cfg.latitude
            center_lon = gis_cfg.longitude
            bbox = None
            self.report({"INFO"}, f"Consultando Overpass API ({filter_pattern}) en Lat={center_lat:.5f}, Lon={center_lon:.5f}...")

        # Asegurar ancla fijada
        if not gis_cfg.has_anchor:
            easting, northing, zone, hem = wgs84_to_utm(center_lat, center_lon)
            gis_cfg.anchor_utm_x = easting
            gis_cfg.anchor_utm_y = northing
            gis_cfg.has_anchor = True
            gis_cfg.epsg_code = (32600 if hem == "N" else 32700) + zone

        try:
            osm_data = query_overpass_api(
                lat=center_lat,
                lon=center_lon,
                radius_m=radius,
                bbox=bbox,
                highway_filter=filter_pattern,
            )

            elements = osm_data.get("elements", [])
            nodes_map: Dict[int, Tuple[float, float]] = {}
            ways: List[dict] = []

            for elem in elements:
                if elem["type"] == "node":
                    nodes_map[elem["id"]] = (elem["lat"], elem["lon"])
                elif elem["type"] == "way":
                    ways.append(elem)

            if not ways:
                self.report({"WARNING"}, f"No se encontraron vías con filtro '{filter_pattern}' en el área seleccionada.")
                return {"CANCELLED"}

            # Encadenar tramos
            polylines = chain_way_segments(ways, nodes_map)
            if not polylines:
                self.report({"WARNING"}, "No se pudieron ensamblar tramos continuos de vías.")
                return {"CANCELLED"}

            # Crear objetos Curva en Blender
            created_objs = create_osm_curve_objects(
                context=context,
                polylines=polylines,
                base_name="Spline_OSM",
                curve_type=gis_cfg.osm_curve_type,
                snap_to_terrain=gis_cfg.osm_snap_to_terrain,
                terrain_obj_name=gis_cfg.target_terrain_name or "TM_Terrain",
                offset_z=gis_cfg.snap_elevation_offset,
            )

            # Seleccionar la primera curva creada
            for o in context.selected_objects:
                o.select_set(False)
            if created_objs:
                created_objs[0].select_set(True)
                context.view_layer.objects.active = created_objs[0]

                if getattr(gis_cfg, "auto_adjust_clipping", True):
                    max_span = max(created_objs[0].dimensions.x, created_objs[0].dimensions.y, 5000.0)
                    adjust_viewport_clipping(context, max_span)
                if getattr(gis_cfg, "auto_frame_view", True):
                    frame_active_object(context)

            self.report(
                {"INFO"},
                f"Importación completada con éxito: {len(created_objs)} trazados de carretera creados en 'TM_OSM_Roads'.",
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error importando carreteras OSM: {e}")
            return {"CANCELLED"}


classes = (
    TRACKMAKER_OT_ImportOSMRoads,
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
