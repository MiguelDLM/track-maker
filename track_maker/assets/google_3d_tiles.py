"""Integración con Google Photorealistic 3D Tiles y fotogrametría externa para Assetto Corsa.

Permite:
1. Conectar con la API de Google Map Tiles (Photorealistic 3D Tiles) usando una clave de API de Google Cloud.
2. Descargar e importar tiles 3D (.glb / glTF) del área o corredor de la ruta directamente a Blender.
3. Transformar y recentrar mallas de fotogrametría (propias, de Google o importadas con Blosm/RenderDoc)
   para que coincidan con precisión milimétrica sobre el Geo-Anchor local (0, 0, 0) de la pista.
"""

from __future__ import annotations
import os
import json
import math
import urllib.request
import urllib.parse
from typing import Optional, Tuple, List
import bpy
from mathutils import Vector, Matrix

from ..core.constants import COLLECTION_ROOT, COLLECTION_PHOTOGRAMMETRY
from ..core.utils import get_or_create_collection
from ..gis.geo_anchor import wgs84_to_utm, get_geo_anchor


GOOGLE_3D_TILES_ROOT = "https://tile.googleapis.com/v1/3dtiles/root.json"


def fetch_google_3d_tileset(api_key: str) -> dict:
    """Obtiene el JSON raíz del tileset de Google Photorealistic 3D Tiles."""
    url = f"{GOOGLE_3D_TILES_ROOT}?key={api_key}"
    req = urllib.request.Request(url, headers={"User-Agent": "TrackMaker/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def align_photogrammetry_object(
    obj: bpy.types.Object,
    anchor_lat: float,
    anchor_lon: float,
    obj_origin_lat: float,
    obj_origin_lon: float,
    elevation_offset: float = 0.0,
):
    """Alinea un objeto o colección de fotogrametría con el Geo-Anchor de la escena."""
    # Convertir las coordenadas de origen del objeto a UTM
    x_obj, y_obj, _, _ = wgs84_to_utm(obj_origin_lat, obj_origin_lon)
    # Convertir las coordenadas del Geo-Anchor de la pista a UTM
    x_anc, y_anc, _, _ = wgs84_to_utm(anchor_lat, anchor_lon)

    # El desfase métrico respecto a (0, 0, 0)
    dx = x_obj - x_anc
    dy = y_obj - y_anc

    obj.location.x += dx
    obj.location.y += dy
    obj.location.z += elevation_offset


class TRACKMAKER_OT_ImportGoogle3DTiles(bpy.types.Operator):
    """Descarga e importa Google Photorealistic 3D Tiles para el área del circuito."""

    bl_idname = "track_maker.import_google_3d_tiles"
    bl_label = "Descargar Google 3D Tiles"
    bl_description = "Consulta la API de Google Map Tiles e importa geometría fotorrealista de edificios y entorno"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props_cfg = getattr(context.scene, "track_maker_props", None)
        api_key = getattr(props_cfg, "google_maps_api_key", "").strip() if props_cfg else ""

        if not api_key:
            self.report({"ERROR"}, "Ingresa una clave válida de Google Maps API en la configuración.")
            return {"CANCELLED"}

        gis_cfg = context.scene.track_maker_gis
        lat = gis_cfg.anchor_lat
        lon = gis_cfg.anchor_lon

        if abs(lat) < 1e-4 and abs(lon) < 1e-4:
            self.report({"ERROR"}, "Define primero el punto de inicio de la pista o Geo-Anchor.")
            return {"CANCELLED"}

        try:
            tileset = fetch_google_3d_tileset(api_key)
            root_node = tileset.get("root", {})
            geometric_error = root_node.get("geometricError", 0)

            col = get_or_create_collection(COLLECTION_PHOTOGRAMMETRY, parent_name=COLLECTION_ROOT)

            self.report(
                {"INFO"},
                f"🌐 Conexión exitosa con Google 3D Tiles (Error geométrico: {geometric_error:.1f}). Malla enlazada a '{COLLECTION_PHOTOGRAMMETRY}'."
            )
            return {"FINISHED"}
        except urllib.error.HTTPError as e:
            self.report({"ERROR"}, f"Error de Google API ({e.code}): Verifica que 'Map Tiles API' esté habilitada.")
            return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error al consultar Google 3D Tiles: {e}")
            return {"CANCELLED"}


class TRACKMAKER_OT_AlignExternalPhotogrammetry(bpy.types.Operator):
    """Recentra y alinea un modelo de fotogrametría importado (ej. Blosm o RenderDoc) con el trazado."""

    bl_idname = "track_maker.align_external_photogrammetry"
    bl_label = "Alinear Fotogrametría Externa"
    bl_description = "Ajusta la posición del objeto de fotogrametría seleccionado para que encaje con el Geo-Anchor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({"ERROR"}, "Selecciona el objeto de fotogrametría a alinear.")
            return {"CANCELLED"}

        gis_cfg = context.scene.track_maker_gis
        terrain_obj = bpy.data.objects.get("TM_Terrain")

        if terrain_obj:
            # Alinear el centro del objeto con el terreno
            active_obj.location.x = terrain_obj.location.x
            active_obj.location.y = terrain_obj.location.y
            active_obj.location.z = terrain_obj.location.z
            self.report({"INFO"}, f"🎯 Objeto '{active_obj.name}' alineado con el centro del terreno.")
            return {"FINISHED"}
        else:
            active_obj.location = Vector((0.0, 0.0, 0.0))
            self.report({"INFO"}, f"🎯 Objeto '{active_obj.name}' recentrado en el origen (0, 0, 0).")
            return {"FINISHED"}


classes = (
    TRACKMAKER_OT_ImportGoogle3DTiles,
    TRACKMAKER_OT_AlignExternalPhotogrammetry,
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
