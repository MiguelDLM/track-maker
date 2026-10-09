"""Módulo de geocodificación mediante OpenStreetMap Nominatim.

Permite buscar nombres de circuitos, carreteras de montaña o ubicaciones del mundo real
(ej. 'Circuito del Jarama', 'Nürburgring Nordschleife', 'Passo dello Stelvio', 'Mount Akina')
y obtener coordenadas geográficas decimales (Latitud, Longitud) y bounding boxes.
"""

from __future__ import annotations
import json
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import List, Optional
import bpy

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) TrackMaker/1.0 (Blender Addon; migueldlm1307@gmail.com)"


@dataclass
class GeocodingResult:
    """Resultado de una búsqueda por nombre de lugar."""
    display_name: str
    latitude: float
    longitude: float
    boundingbox: tuple[float, float, float, float]  # (south, north, west, east)
    place_type: str


def search_location(query: str, limit: int = 5, user_agent: str = DEFAULT_USER_AGENT) -> List[GeocodingResult]:
    """Busca ubicaciones por nombre en OpenStreetMap Nominatim."""
    query = query.strip()
    if not query:
        return []

    params = {
        "q": query,
        "format": "json",
        "limit": str(limit),
        "addressdetails": "1",
    }
    url = f"{NOMINATIM_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Error HTTP en búsqueda Nominatim ({e.code}): {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Error de conexión en búsqueda Nominatim: {e.reason}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Respuesta inválida de Nominatim: {e}")

    results: List[GeocodingResult] = []
    for item in data:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
            raw_bb = item.get("boundingbox", [lat - 0.02, lat + 0.02, lon - 0.02, lon + 0.02])
            south = float(raw_bb[0])
            north = float(raw_bb[1])
            west = float(raw_bb[2])
            east = float(raw_bb[3])

            results.append(
                GeocodingResult(
                    display_name=item.get("display_name", ""),
                    latitude=lat,
                    longitude=lon,
                    boundingbox=(south, north, west, east),
                    place_type=item.get("type", "feature"),
                )
            )
        except (KeyError, ValueError):
            continue

    return results


class TRACKMAKER_OT_SearchLocation(bpy.types.Operator):
    """Busca un circuito o lugar en el mundo mediante OpenStreetMap Nominatim."""

    bl_idname = "track_maker.search_location"
    bl_label = "Buscar Lugar GPS"
    bl_description = "Consulta OpenStreetMap Nominatim para localizar el circuito o tramo por nombre"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        query = gis_cfg.search_query.strip()

        if not query:
            self.report({"WARNING"}, "Introduce un término de búsqueda (ej. 'Circuito del Jarama', 'Monza').")
            return {"CANCELLED"}

        try:
            results = search_location(query, limit=1)
            if not results:
                self.report({"WARNING"}, f"No se encontraron resultados para '{query}'.")
                return {"CANCELLED"}

            res = results[0]
            gis_cfg.latitude = res.latitude
            gis_cfg.longitude = res.longitude
            gis_cfg.search_result_name = res.display_name

            self.report(
                {"INFO"},
                f"Encontrado: {res.display_name[:50]}... -> Lat={res.latitude:.6f}, Lon={res.longitude:.6f}",
            )
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error en la búsqueda GPS: {e}")
            return {"CANCELLED"}


class TRACKMAKER_OT_SearchAndSetAnchor(bpy.types.Operator):
    """Fija el Ancla Georreferenciada (0, 0, 0) directamente desde las coordenadas GPS actuales."""

    bl_idname = "track_maker.set_anchor_from_gps"
    bl_label = "Fijar Ancla desde GPS"
    bl_description = "Calcula UTM y establece el origen local (0, 0, 0) a partir de la Latitud/Longitud actuales"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        from .geo_anchor import wgs84_to_utm

        easting, northing, zone, hem = wgs84_to_utm(gis_cfg.latitude, gis_cfg.longitude)
        gis_cfg.anchor_utm_x = easting
        gis_cfg.anchor_utm_y = northing
        gis_cfg.has_anchor = True

        epsg = (32600 if hem == "N" else 32700) + zone
        gis_cfg.epsg_code = epsg

        self.report(
            {"INFO"},
            f"Ancla fijada en Lat={gis_cfg.latitude:.5f}, Lon={gis_cfg.longitude:.5f} -> Huso {zone}{hem} (EPSG {epsg})",
        )
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_SearchLocation,
    TRACKMAKER_OT_SearchAndSetAnchor,
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
