"""Generador de minimapas 2D para Assetto Corsa y Content Manager (map.png y data/map.ini).

Genera un gráfico vectorial/raster transparente de 1024x1024 con la silueta de la pista y calcula
las variables de transformación espacial (WIDTH, HEIGHT, MARGIN, SCALE_FACTOR, X_OFFSET, Z_OFFSET)
para la aplicación de radar en tiempo real y la vista previa en Content Manager.
"""

from __future__ import annotations
import os
import math
import struct
import zlib
from typing import Tuple, List, Optional
import numpy as np
import bpy
from mathutils import Vector


def encode_png_rgba(image_rgba: np.ndarray) -> bytes:
    """Codifica un array NumPy RGBA (H, W, 4) uint8 en un archivo PNG válido en Python puro sin dependencias."""
    h, w, c = image_rgba.shape
    if c != 4:
        raise ValueError("La imagen debe tener 4 canales (RGBA).")

    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)  # 6 = Color Type RGBA
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    ihdr = struct.pack(">I4s", len(ihdr_data), b"IHDR") + ihdr_data + ihdr_crc

    raw_lines = bytearray()
    for y in range(h):
        raw_lines.append(0)  # Tipo de filtro 0 (None)
        raw_lines.extend(image_rgba[y].tobytes())

    compressed = zlib.compress(bytes(raw_lines), level=6)
    idat_crc = struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    idat = struct.pack(">I4s", len(compressed), b"IDAT") + compressed + idat_crc

    iend_crc = struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    iend = struct.pack(">I4s", 0, b"IEND") + iend_crc

    return header + ihdr + idat + iend


def generate_track_minimap(
    curve_obj: bpy.types.Object,
    output_dir: str,
    img_size: int = 1024,
    margin: int = 50,
    line_thickness: int = 6,
) -> Tuple[str, str, float]:
    """Genera map.png y data/map.ini en la carpeta del mod a partir de los puntos del spline de la pista."""
    if not curve_obj or curve_obj.type != "CURVE" or not curve_obj.data.splines:
        raise ValueError("Se requiere un objeto de curva válido con al menos un spline.")

    spline = curve_obj.data.splines[0]
    mat = curve_obj.matrix_world

    # Obtener puntos 2D en espacio de coordenadas de Assetto Corsa
    # En AC: X = Horizontal (Blender X), Z = Profundidad (Blender Y)
    if spline.type == "BEZIER":
        pts = [mat @ bp.co for bp in spline.bezier_points]
    else:
        pts = [mat @ p.co.to_3d() for p in spline.points]

    if len(pts) < 2:
        raise ValueError("El spline debe contener al menos 2 puntos.")

    xs = [p.x for p in pts]
    zs = [p.y for p in pts]

    min_x, max_x = min(xs), max(xs)
    min_z, max_z = min(zs), max(zs)
    span_x = max(1.0, max_x - min_x)
    span_z = max(1.0, max_z - min_z)

    drawable = img_size - (2 * margin)
    scale = drawable / max(span_x, span_z)

    # Crear lienzo transparente RGBA (1024x1024)
    canvas = np.zeros((img_size, img_size, 4), dtype=np.uint8)
    radius = max(2, line_thickness // 2)

    # Trazar segmentos de línea continuos
    for i in range(len(pts) - 1):
        x0 = (pts[i].x - min_x) * scale + margin
        z0 = (pts[i].y - min_z) * scale + margin
        x1 = (pts[i + 1].x - min_x) * scale + margin
        z1 = (pts[i + 1].y - min_z) * scale + margin

        dist = math.hypot(x1 - x0, z1 - z0)
        steps = max(1, int(dist * 2.0))

        for s in range(steps + 1):
            t = s / max(1, steps)
            px = int(round(x0 + t * (x1 - x0)))
            # Blender Y crece hacia arriba; en la imagen las filas crecen hacia abajo
            py = int(round((img_size - 1) - (z0 + t * (z1 - z0))))

            r_min = max(0, py - radius)
            r_max = min(img_size, py + radius + 1)
            c_min = max(0, px - radius)
            c_max = min(img_size, px + radius + 1)

            for r in range(r_min, r_max):
                for c in range(c_min, c_max):
                    if (r - py) ** 2 + (c - px) ** 2 <= radius ** 2:
                        canvas[r, c] = [255, 255, 255, 255]

    # Guardar map.png en la raíz del mod
    map_png_path = os.path.join(output_dir, "map.png")
    png_bytes = encode_png_rgba(canvas)
    with open(map_png_path, "wb") as f:
        f.write(png_bytes)

    # Guardar data/map.ini
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    map_ini_path = os.path.join(data_dir, "map.ini")

    ini_content = f"""[PARAMETERS]
WIDTH={img_size}
HEIGHT={img_size}
MARGIN={margin}
SCALE_FACTOR={scale:.6f}
X_OFFSET={min_x:.2f}
Z_OFFSET={min_z:.2f}
DRAWING_SIZE=10
"""
    with open(map_ini_path, "w", encoding="utf-8") as f:
        f.write(ini_content)

    return map_png_path, map_ini_path, scale


class TRACKMAKER_OT_GenerateTrackMap(bpy.types.Operator):
    """Genera map.png y data/map.ini para Content Manager y el radar en juego de Assetto Corsa."""

    bl_idname = "track_maker.generate_track_map"
    bl_label = "Generar Minimapa de Pista (map.png)"
    bl_description = "Dibuja la silueta 2D de la pista y calcula los factores de escala para Content Manager"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        export_cfg = context.scene.track_maker_export
        track_name = getattr(context.scene.track_maker_circuit, "track_name", "Mi_Circuito") or "Mi_Circuito"
        base_dir = os.path.expanduser(export_cfg.export_directory or "~/Desktop")
        track_dir = os.path.join(base_dir, track_name)
        os.makedirs(track_dir, exist_ok=True)

        spline_obj = context.active_object if (context.active_object and context.active_object.type == "CURVE") else bpy.data.objects.get("Spline_Route_AB")

        if not spline_obj or spline_obj.type != "CURVE":
            for obj in bpy.data.objects:
                if obj.type == "CURVE" and obj.data.splines:
                    spline_obj = obj
                    break

        if not spline_obj:
            self.report({"ERROR"}, "No se encontró ningún spline de carretera para generar el mapa.")
            return {"CANCELLED"}

        try:
            png_p, ini_p, sc = generate_track_minimap(spline_obj, track_dir)
            self.report({"INFO"}, f"🗺️ Minimapa generado con éxito: map.png y data/map.ini (Escala: {sc:.4f}).")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error generando minimapa: {e}")
            return {"CANCELLED"}


classes = (TRACKMAKER_OT_GenerateTrackMap,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
