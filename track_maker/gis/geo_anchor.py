"""Gestión de coordenadas georreferenciadas, origen local y prevención de floating-point jitter."""

import math
import bpy
from mathutils import Vector


def wgs84_to_utm(lat: float, lon: float) -> tuple[float, float, int, str]:
    """Convierte Latitud y Longitud (WGS84) a coordenadas UTM (Easting, Northing, Huso, Hemisferio).
    Implementación matemática pura en Python según la proyección Transversal de Mercator.
    """
    # Constantes WGS84
    a = 6378137.0  # Semieje mayor
    f = 1.0 / 298.257223563  # Achatamiento
    e2 = 2 * f - f * f  # Primera excentricidad al cuadrado
    e_prime2 = e2 / (1.0 - e2)

    # Determinar Huso UTM (Zone)
    zone_number = int((lon + 180.0) / 6.0) + 1
    lon_origin = (zone_number - 1) * 6 - 180 + 3
    lon_origin_rad = math.radians(lon_origin)

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)

    k0 = 0.9996  # Factor de escala en meridiano central

    # Cálculos elipsoidales
    N = a / math.sqrt(1.0 - e2 * (math.sin(lat_rad) ** 2))
    T = math.tan(lat_rad) ** 2
    C = e_prime2 * (math.cos(lat_rad) ** 2)
    A = math.cos(lat_rad) * (lon_rad - lon_origin_rad)

    # Longitud de arco de meridiano M
    M = a * (
        (1.0 - e2 / 4.0 - 3.0 * e2 * e2 / 64.0 - 5.0 * (e2 ** 3) / 256.0) * lat_rad
        - (3.0 * e2 / 8.0 + 3.0 * e2 * e2 / 32.0 + 45.0 * (e2 ** 3) / 1024.0) * math.sin(2.0 * lat_rad)
        + (15.0 * e2 * e2 / 256.0 + 45.0 * (e2 ** 3) / 1024.0) * math.sin(4.0 * lat_rad)
        - (35.0 * (e2 ** 3) / 3072.0) * math.sin(6.0 * lat_rad)
    )

    # Coordenada Este (Easting)
    easting = k0 * N * (
        A
        + (1.0 - T + C) * (A ** 3) / 6.0
        + (5.0 - 18.0 * T + (T ** 2) + 72.0 * C - 58.0 * e_prime2) * (A ** 5) / 120.0
    ) + 500000.0

    # Coordenada Norte (Northing)
    northing = k0 * (
        M
        + N * math.tan(lat_rad) * (
            (A ** 2) / 2.0
            + (5.0 - T + 9.0 * C + 4.0 * (C ** 2)) * (A ** 4) / 24.0
            + (61.0 - 58.0 * T + (T ** 2) + 600.0 * C - 330.0 * e_prime2) * (A ** 6) / 720.0
        )
    )

    hemisphere = "N" if lat >= 0 else "S"
    if lat < 0:
        northing += 10000000.0  # False Northing para hemisferio sur

    return easting, northing, zone_number, hemisphere


def utm_to_local(utm_x: float, utm_y: float, utm_z: float, anchor_x: float, anchor_y: float, anchor_z: float) -> Vector:
    """Convierte coordenadas UTM a posición métrica local de Blender centrada en el ancla."""
    return Vector((utm_x - anchor_x, utm_y - anchor_y, utm_z - anchor_z))


def local_to_utm(local_x: float, local_y: float, local_z: float, anchor_x: float, anchor_y: float, anchor_z: float) -> tuple[float, float, float]:
    """Convierte posición local de Blender a coordenadas UTM globales del mundo real."""
    return (local_x + anchor_x, local_y + anchor_y, local_z + anchor_z)


def get_geo_anchor(context: bpy.types.Context) -> tuple[float, float, float, float, float, float]:
    """Retorna (lat, lon, elev, utm_x, utm_y, utm_z) del ancla activa."""
    gis = context.scene.track_maker_gis
    return (
        getattr(gis, "anchor_lat", 0.0),
        getattr(gis, "anchor_lon", 0.0),
        getattr(gis, "anchor_elevation", 0.0),
        getattr(gis, "anchor_utm_x", 0.0),
        getattr(gis, "anchor_utm_y", 0.0),
        getattr(gis, "anchor_utm_z", 0.0),
    )


class TRACKMAKER_OT_SetGeoAnchor(bpy.types.Operator):
    """Establece las coordenadas del Ancla Georreferenciada para el origen (0, 0, 0) de la escena."""

    bl_idname = "track_maker.set_geo_anchor"
    bl_label = "Fijar Ancla Georreferenciada"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        name="Método",
        items=[
            ("FROM_SELECTION", "Centro de Selección", "Calcula el centroide de la malla/terreno seleccionado"),
            ("FROM_LAT_LON", "Latitud / Longitud", "Introduce coordenadas GPS en grados decimales"),
            ("FROM_UTM", "Coordenadas UTM Manuales", "Introduce coordenadas métricas UTM directamente"),
        ],
        default="FROM_SELECTION",
    )

    latitude: bpy.props.FloatProperty(
        name="Latitud (°)",
        description="Grados decimales (ej. 19.4326 o 40.4168)",
        default=19.4326,
        precision=6,
    )

    longitude: bpy.props.FloatProperty(
        name="Longitud (°)",
        description="Grados decimales (ej. -99.1332 o -3.7038)",
        default=-99.1332,
        precision=6,
    )

    elevation: bpy.props.FloatProperty(
        name="Altitud / Cota (m)",
        description="Elevación sobre el nivel del mar en metros",
        default=2240.0,
        unit="LENGTH",
    )

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis

        if self.mode == "FROM_SELECTION":
            selected = context.selected_objects
            if not selected:
                self.report({"ERROR"}, "Selecciona al menos un objeto (malla o curva) para fijar el ancla.")
                return {"CANCELLED"}

            # Calcular centroide mundo
            total_center = Vector((0.0, 0.0, 0.0))
            for obj in selected:
                total_center += obj.matrix_world.translation
            center = total_center / len(selected)

            gis_cfg.anchor_utm_x = center.x
            gis_cfg.anchor_utm_y = center.y
            gis_cfg.anchor_elevation_z = center.z
            gis_cfg.has_anchor = True

            self.report(
                {"INFO"},
                f"Ancla fijada desde selección: X={center.x:.2f}, Y={center.y:.2f}, Z={center.z:.2f} m",
            )

        elif self.mode == "FROM_LAT_LON":
            easting, northing, zone, hem = wgs84_to_utm(self.latitude, self.longitude)
            gis_cfg.anchor_utm_x = easting
            gis_cfg.anchor_utm_y = northing
            gis_cfg.anchor_elevation_z = self.elevation
            gis_cfg.has_anchor = True

            # Estimación código EPSG para UTM WGS84 (32600 + zona para N, 32700 + zona para S)
            epsg = (32600 if hem == "N" else 32700) + zone
            gis_cfg.epsg_code = epsg

            self.report(
                {"INFO"},
                f"Ancla fijada (GPS): Huso {zone}{hem} (EPSG {epsg}) -> X={easting:.2f}, Y={northing:.2f}, Z={self.elevation:.2f} m",
            )

        else:  # FROM_UTM
            gis_cfg.has_anchor = True
            self.report(
                {"INFO"},
                f"Ancla UTM fijada: X={gis_cfg.anchor_utm_x:.2f}, Y={gis_cfg.anchor_utm_y:.2f}, Z={gis_cfg.anchor_elevation_z:.2f} m",
            )

        return {"FINISHED"}


class TRACKMAKER_OT_RecenterGISObjects(bpy.types.Operator):
    """Mueve los objetos seleccionados restando el ancla georreferenciada para eliminar el temblor de vértices."""

    bl_idname = "track_maker.recenter_gis_objects"
    bl_label = "Recentrar al Origen (Anti-Jitter)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        if not gis_cfg.has_anchor:
            self.report({"ERROR"}, "Fija primero un Ancla Georreferenciada antes de recentrar objetos.")
            return {"CANCELLED"}

        selected = context.selected_objects
        if not selected:
            self.report({"ERROR"}, "Selecciona los objetos que deseas recentrar.")
            return {"CANCELLED"}

        shift = Vector((gis_cfg.anchor_utm_x, gis_cfg.anchor_utm_y, gis_cfg.anchor_elevation_z))

        for obj in selected:
            # Desplazar la ubicación del objeto hacia el origen
            obj.location -= shift
            # Guardar propiedad de respaldo para permitir des-recentrado si es necesario
            obj["gis_shifted"] = True
            obj["gis_offset_x"] = gis_cfg.anchor_utm_x
            obj["gis_offset_y"] = gis_cfg.anchor_utm_y
            obj["gis_offset_z"] = gis_cfg.anchor_elevation_z

        self.report({"INFO"}, f"Se recentraron {len(selected)} objetos al origen (0, 0, 0). Jitter neutralizado.")
        return {"FINISHED"}


class TRACKMAKER_OT_ClearGeoAnchor(bpy.types.Operator):
    """Restablece el ancla georreferenciada del proyecto."""

    bl_idname = "track_maker.clear_geo_anchor"
    bl_label = "Limpiar Ancla"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        gis_cfg.anchor_utm_x = 0.0
        gis_cfg.anchor_utm_y = 0.0
        gis_cfg.anchor_elevation_z = 0.0
        gis_cfg.has_anchor = False
        self.report({"INFO"}, "Ancla georreferenciada restablecida.")
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_SetGeoAnchor,
    TRACKMAKER_OT_RecenterGISObjects,
    TRACKMAKER_OT_ClearGeoAnchor,
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

