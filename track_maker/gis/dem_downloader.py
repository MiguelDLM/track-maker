"""Descargador y generador de mallas de relieve topográfico 3D (DEM) desde AWS Open Data (Terrarium).

Descarga mosaicos de elevación de 256x256 píxeles sin necesidad de API keys o registros:
    https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png
Fórmula de elevación Terrarium:
    elev_m = (R * 256.0 + G + B / 256.0) - 32768.0

Construye mallas nativas en Blender mediante buffers vectorizados C-speed (foreach_set).
"""

from __future__ import annotations
import math
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple, List, Optional
import numpy as np
import bpy
from mathutils import Vector

from .png_decoder import decode_png_rgb
from .geo_anchor import wgs84_to_utm
from .viewport_tools import adjust_viewport_clipping, frame_active_object

TERRARIUM_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) TrackMaker/1.0 (Blender Addon; migueldlm1307@gmail.com)"
EARTH_RADIUS_KM = 6378.137
MAX_WORKERS = 8


def lat_lon_to_tile(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    """Convierte Latitud y Longitud WGS84 en coordenadas de mosaico Slippy Map (x, y)."""
    lat_deg = max(-85.05112878, min(85.05112878, lat_deg))
    lon_deg = max(-180.0, min(180.0, lon_deg))
    n = 2.0 ** zoom
    x = int(math.floor((lon_deg + 180.0) / 360.0 * n))
    lat_rad = math.radians(lat_deg)
    y = int(math.floor((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n))
    max_t = int(n) - 1
    return max(0, min(x, max_t)), max(0, min(y, max_t))


def bbox_from_center(center_lat: float, center_lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    """Calcula bounding box (min_lat, min_lon, max_lat, max_lon) a partir de centro y radio en km."""
    delta_lat_deg = math.degrees(radius_km / EARTH_RADIUS_KM)
    lat_rad = math.radians(center_lat)
    cos_lat = max(0.01, math.cos(lat_rad))
    delta_lon_deg = math.degrees(radius_km / (EARTH_RADIUS_KM * cos_lat))

    min_lat = max(-85.0, center_lat - delta_lat_deg)
    max_lat = min(85.0, center_lat + delta_lat_deg)
    min_lon = max(-180.0, center_lon - delta_lon_deg)
    max_lon = min(180.0, center_lon + delta_lon_deg)
    return min_lat, min_lon, max_lat, max_lon


def bbox_from_points_ab(
    lat_a: float,
    lon_a: float,
    lat_b: float,
    lon_b: float,
    margin_km: float = 1.0,
) -> Tuple[float, float, float, float]:
    """Calcula bounding box con margen alrededor del corredor que une el Punto A y el Punto B."""
    center_lat = (lat_a + lat_b) / 2.0
    delta_lat_deg = math.degrees(margin_km / EARTH_RADIUS_KM)
    lat_rad = math.radians(center_lat)
    cos_lat = max(0.01, math.cos(lat_rad))
    delta_lon_deg = math.degrees(margin_km / (EARTH_RADIUS_KM * cos_lat))

    min_lat = max(-85.0, min(lat_a, lat_b) - delta_lat_deg)
    max_lat = min(85.0, max(lat_a, lat_b) + delta_lat_deg)
    min_lon = max(-180.0, min(lon_a, lon_b) - delta_lon_deg)
    max_lon = min(180.0, max(lon_a, lon_b) + delta_lon_deg)
    return min_lat, min_lon, max_lat, max_lon


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia geodésica entre dos puntos en metros."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * 1000.0 * c


def decode_terrarium_elevation(rgb_array: np.ndarray) -> np.ndarray:
    """Decodifica un mosaico Terrarium RGB (H, W, 3) a elevación float32 en metros."""
    r = rgb_array[:, :, 0].astype(np.float32)
    g = rgb_array[:, :, 1].astype(np.float32)
    b = rgb_array[:, :, 2].astype(np.float32)
    return (r * 256.0 + g + b / 256.0) - 32768.0


def resample_grid_bilinear(grid: np.ndarray, out_shape: Tuple[int, int]) -> np.ndarray:
    """Remuestrea un array 2D de elevación con interpolación bilineal."""
    out_h, out_w = out_shape
    in_h, in_w = grid.shape
    if in_h == out_h and in_w == out_w:
        return grid.copy()

    y_indices = np.linspace(0, in_h - 1, out_h)
    x_indices = np.linspace(0, in_w - 1, out_w)

    y0 = np.floor(y_indices).astype(int)
    y1 = np.clip(y0 + 1, 0, in_h - 1)
    x0 = np.floor(x_indices).astype(int)
    x1 = np.clip(x0 + 1, 0, in_w - 1)

    wy1 = (y_indices - y0)[:, np.newaxis]
    wy0 = 1.0 - wy1
    wx1 = (x_indices - x0)[np.newaxis, :]
    wx0 = 1.0 - wx1

    top = wy0 * grid[y0, :][:, x0] * wx0 + wy0 * grid[y0, :][:, x1] * wx1
    bot = wy1 * grid[y1, :][:, x0] * wx0 + wy1 * grid[y1, :][:, x1] * wx1
    return (top + bot).astype(np.float32)


def fetch_tile_bytes(z: int, x: int, y: int, user_agent: str = DEFAULT_USER_AGENT) -> bytes:
    """Descarga los bytes PNG de un mosaico Terrarium individual."""
    url = TERRARIUM_URL.format(z=z, x=x, y=y)
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=12) as response:
        return response.read()


def download_elevation_grid(
    center_lat: float,
    center_lon: float,
    radius_km: float = 2.0,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    zoom: int = 13,
    target_resolution: int = 256,
) -> Tuple[np.ndarray, Tuple[float, float, float, float], float, float]:
    """Descarga mosaicos AWS Terrarium y devuelve la cuadrícula de elevación en metros y dimensiones."""
    if bbox is not None:
        min_lat, min_lon, max_lat, max_lon = bbox
    else:
        min_lat, min_lon, max_lat, max_lon = bbox_from_center(center_lat, center_lon, radius_km)

    x1, y1 = lat_lon_to_tile(max_lat, min_lon, zoom)  # NW
    x2, y2 = lat_lon_to_tile(min_lat, max_lon, zoom)  # SE
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)

    tiles_w = (max_x - min_x) + 1
    tiles_h = (max_y - min_y) + 1
    tile_px = 256

    canvas_h = tiles_h * tile_px
    canvas_w = tiles_w * tile_px
    stitched = np.zeros((canvas_h, canvas_w), dtype=np.float32)

    tiles = []
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            tiles.append((zoom, x, y))

    def _get_tile(tile):
        z, x, y = tile
        return tile, fetch_tile_bytes(z, x, y)

    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(tiles))) as pool:
        results = list(pool.map(_get_tile, tiles))

    for (z, x, y), raw_bytes in results:
        rgb = decode_png_rgb(raw_bytes)
        elev = decode_terrarium_elevation(rgb)
        c_off = (x - min_x) * tile_px
        r_off = (y - min_y) * tile_px
        stitched[r_off : r_off + tile_px, c_off : c_off + tile_px] = elev

    # Recorte exacto al bounding box
    n = 2.0 ** zoom

    def _lat_lon_to_pixel(lat: float, lon: float) -> Tuple[float, float]:
        x_tile_f = (lon + 180.0) / 360.0 * n
        lat_rad = math.radians(max(-85.05, min(85.05, lat)))
        y_tile_f = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
        px = (x_tile_f - min_x) * tile_px
        py = (y_tile_f - min_y) * tile_px
        return px, py

    px_left, py_top = _lat_lon_to_pixel(max_lat, min_lon)
    px_right, py_bottom = _lat_lon_to_pixel(min_lat, max_lon)

    c_left = int(max(0, min(math.floor(px_left), canvas_w - 1)))
    c_right = int(max(c_left + 1, min(math.ceil(px_right), canvas_w)))
    c_top = int(max(0, min(math.floor(py_top), canvas_h - 1)))
    c_bottom = int(max(c_top + 1, min(math.ceil(py_bottom), canvas_h)))

    cropped = stitched[c_top:c_bottom, c_left:c_right]

    width_m = haversine_distance_m(center_lat, min_lon, center_lat, max_lon)
    height_m = haversine_distance_m(min_lat, center_lon, max_lat, center_lon)

    # Remuestreo
    if target_resolution and target_resolution > 16:
        # Mantener proporción aproximada
        if width_m >= height_m:
            cols = target_resolution
            rows = max(2, int(round(target_resolution * height_m / max(1e-6, width_m))))
        else:
            rows = target_resolution
            cols = max(2, int(round(target_resolution * width_m / max(1e-6, height_m))))
        elevation_final = resample_grid_bilinear(cropped, (rows, cols))
    else:
        elevation_final = cropped

    return elevation_final, (min_lat, min_lon, max_lat, max_lon), width_m, height_m


def create_blender_terrain_mesh(
    context,
    elevation: np.ndarray,
    center_lat: float,
    center_lon: float,
    width_m: float,
    height_m: float,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    obj_name: str = "TM_Terrain",
) -> bpy.types.Object:
    """Construye un objeto de malla Blender a partir de la cuadrícula DEM centrada en el Geo-Anchor."""
    gis_cfg = context.scene.track_maker_gis

    # Sincronizar Ancla Georreferenciada siempre al centro exacto del relieve generado
    easting, northing, zone, hem = wgs84_to_utm(center_lat, center_lon)
    gis_cfg.anchor_utm_x = easting
    gis_cfg.anchor_utm_y = northing
    gis_cfg.anchor_elevation_z = float(np.min(elevation))
    gis_cfg.has_anchor = True
    gis_cfg.epsg_code = (32600 if hem == "N" else 32700) + zone

    rows, cols = elevation.shape
    v_scale = getattr(gis_cfg, "vertical_scale", 1.0)

    # Coordenadas locales en metros relativas al centro
    # X va de Oeste a Este (-width/2 a +width/2)
    # Y va de Sur a Norte (-height/2 a +height/2)
    x_coords = np.linspace(-width_m / 2.0, width_m / 2.0, cols, dtype=np.float32)
    y_coords = np.linspace(height_m / 2.0, -height_m / 2.0, rows, dtype=np.float32)

    xx, yy = np.meshgrid(x_coords, y_coords)
    # Z relativo a la cota base del ancla multiplicado por escala vertical
    zz = ((elevation - gis_cfg.anchor_elevation_z) * v_scale).astype(np.float32)

    vertices = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()]).astype(np.float32)

    # UVs
    u_coords = np.linspace(0.0, 1.0, cols, dtype=np.float32)
    v_coords = np.linspace(1.0, 0.0, rows, dtype=np.float32)
    uu, vv = np.meshgrid(u_coords, v_coords)
    uvs = np.column_stack([uu.ravel(), vv.ravel()]).astype(np.float32)

    # Caras quads
    r_idx = np.arange(rows - 1)[:, np.newaxis]
    c_idx = np.arange(cols - 1)[np.newaxis, :]
    v0 = (r_idx * cols + c_idx).ravel()
    v1 = ((r_idx + 1) * cols + c_idx).ravel()
    v2 = ((r_idx + 1) * cols + (c_idx + 1)).ravel()
    v3 = (r_idx * cols + (c_idx + 1)).ravel()
    faces = np.column_stack([v0, v1, v2, v3]).astype(np.int32)
    n_faces = len(faces)

    # Crear malla
    mesh = bpy.data.meshes.new(f"{obj_name}_Mesh")
    mesh.vertices.add(len(vertices))
    mesh.vertices.foreach_set("co", vertices.ravel())
    mesh.loops.add(n_faces * 4)
    mesh.loops.foreach_set("vertex_index", faces.ravel())
    mesh.polygons.add(n_faces)
    mesh.polygons.foreach_set("loop_start", np.arange(0, n_faces * 4, 4, dtype=np.int32))
    mesh.update(calc_edges=True)
    mesh.shade_smooth()

    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", uvs[faces.ravel()].ravel())

    # Crear o reemplazar objeto en escena
    existing_obj = bpy.data.objects.get(obj_name)
    if existing_obj:
        existing_obj.data = mesh
        obj = existing_obj
    else:
        obj = bpy.data.objects.new(obj_name, mesh)
        context.collection.objects.link(obj)

    # Asignar propiedades personalizadas
    obj["gis_is_terrain"] = True
    obj["gis_lat"] = center_lat
    obj["gis_lon"] = center_lon
    obj["gis_width_m"] = width_m
    obj["gis_height_m"] = height_m
    obj["gis_elevation_min"] = float(np.min(elevation))
    obj["gis_elevation_max"] = float(np.max(elevation))
    obj["gis_vertical_scale"] = float(v_scale)
    if bbox:
        obj["gis_bbox"] = list(bbox)

    # Establecer como terreno objetivo en configuración GIS
    gis_cfg.target_terrain_name = obj.name

    # Ajustar límite lejano de cámara (clip_end) y encuadrar vista
    if getattr(gis_cfg, "auto_adjust_clipping", True):
        max_span = max(width_m, height_m)
        adjust_viewport_clipping(context, max_span)

    if getattr(gis_cfg, "auto_frame_view", True):
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        frame_active_object(context)

    return obj


class TRACKMAKER_OT_DownloadTerrainDEM(bpy.types.Operator):
    """Descarga topografía DEM real (AWS Terrarium) y genera la malla 3D de terreno en Blender."""

    bl_idname = "track_maker.download_terrain_dem"
    bl_label = "Descargar Terreno 3D (DEM)"
    bl_description = "Descarga elevación real desde AWS Open Data (Terrarium) sin necesidad de API key"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        zoom = gis_cfg.dem_zoom
        res = gis_cfg.terrain_resolution

        if gis_cfg.coverage_mode == "POINTS_AB":
            lat_a, lon_a = gis_cfg.point_a_lat, gis_cfg.point_a_lon
            lat_b, lon_b = gis_cfg.point_b_lat, gis_cfg.point_b_lon
            center_lat = (lat_a + lat_b) / 2.0
            center_lon = (lon_a + lon_b) / 2.0
            bbox = bbox_from_points_ab(lat_a, lon_a, lat_b, lon_b, gis_cfg.corridor_margin_km)
            self.report(
                {"INFO"},
                f"Descargando topografía DEM tramo A-B ({lat_a:.4f} -> {lat_b:.4f}) | Margen: {gis_cfg.corridor_margin_km:.1f}km (Zoom={zoom})...",
            )
            radius = gis_cfg.corridor_margin_km
        else:
            center_lat = gis_cfg.latitude
            center_lon = gis_cfg.longitude
            bbox = None
            radius = gis_cfg.terrain_radius_km
            self.report(
                {"INFO"},
                f"Descargando topografía DEM en Lat={center_lat:.5f}, Lon={center_lon:.5f} (Radio={radius:.1f}km, Zoom={zoom})...",
            )

        try:
            elev_grid, bbox_out, width_m, height_m = download_elevation_grid(
                center_lat=center_lat,
                center_lon=center_lon,
                radius_km=radius,
                bbox=bbox,
                zoom=zoom,
                target_resolution=res,
            )

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

            min_z = float(np.min(elev_grid))
            max_z = float(np.max(elev_grid))

            self.report(
                {"INFO"},
                f"Terreno generado '{terrain_obj.name}': {width_m/1000.0:.2f} x {height_m/1000.0:.2f} km | Cota: {min_z:.1f}m a {max_z:.1f}m",
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error descargando terreno DEM: {e}")
            return {"CANCELLED"}


classes = (
    TRACKMAKER_OT_DownloadTerrainDEM,
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
