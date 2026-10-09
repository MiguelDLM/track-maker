"""Pruebas unitarias para los módulos GIS (PNG decoder, DEM downloader, geocoding y OSM roads)."""

import math
import struct
import zlib
import unittest
import numpy as np

from track_maker.gis.png_decoder import decode_png_rgb
from track_maker.gis.dem_downloader import (
    lat_lon_to_tile,
    bbox_from_center,
    haversine_distance_m,
    decode_terrarium_elevation,
    resample_grid_bilinear,
)
from track_maker.gis.geocoding import GeocodingResult
from track_maker.gis.osm_roads import chain_way_segments


def create_synthetic_png_rgb(width: int, height: int, rgb_data: np.ndarray) -> bytes:
    """Genera bytes PNG válidos sin compresión compleja para verificar el decodificador PNG."""
    # Cabecera PNG
    header = b"\x89PNG\r\n\x1a\n"
    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    ihdr = struct.pack(">I4s", len(ihdr_data), b"IHDR") + ihdr_data + ihdr_crc

    # IDAT
    # Cada fila lleva un byte de filtro (0 = None) seguido de los píxeles RGB
    raw_lines = bytearray()
    for y in range(height):
        raw_lines.append(0)  # Filtro 0
        raw_lines.extend(rgb_data[y].tobytes())

    compressed = zlib.compress(bytes(raw_lines))
    idat_crc = struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    idat = struct.pack(">I4s", len(compressed), b"IDAT") + compressed + idat_crc

    # IEND
    iend_crc = struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    iend = struct.pack(">I4s", 0, b"IEND") + iend_crc

    return header + ihdr + idat + iend


class TestGISTools(unittest.TestCase):

    def test_png_decoder(self):
        """Verifica que el decodificador PNG puro extraiga los valores RGB idénticos."""
        w, h = 4, 4
        # Crear matriz sintética RGB con valores conocidos
        expected_rgb = np.zeros((h, w, 3), dtype=np.uint8)
        expected_rgb[0, 0] = [128, 64, 32]
        expected_rgb[1, 2] = [255, 128, 0]
        expected_rgb[3, 3] = [10, 20, 30]

        png_bytes = create_synthetic_png_rgb(w, h, expected_rgb)
        decoded = decode_png_rgb(png_bytes)

        self.assertEqual(decoded.shape, (4, 4, 3))
        np.testing.assert_array_equal(decoded, expected_rgb)

    def test_dem_terrarium_elevation_decoding(self):
        """Verifica la fórmula matemática de elevación de AWS Terrarium: (R*256 + G + B/256) - 32768."""
        rgb = np.zeros((2, 2, 3), dtype=np.uint8)
        # Nivel del mar (0 metros) corresponde en Terrarium a: 32768 = 128 * 256 + 0 + 0
        rgb[0, 0] = [128, 0, 0]  # (128*256 + 0) - 32768 = 0.0 m
        # 1000 metros: 33768 = 131 * 256 + 232 + 0 -> 131*256 = 33536, 33768 - 33536 = 232
        rgb[0, 1] = [131, 232, 0]

        elev = decode_terrarium_elevation(rgb)
        self.assertAlmostEqual(elev[0, 0], 0.0, places=1)
        self.assertAlmostEqual(elev[0, 1], 1000.0, places=1)

    def test_lat_lon_to_tile(self):
        """Verifica la conversión de Lat/Lon a coordenadas Slippy Map (x, y)."""
        # Madrid / Jarama aprox 40.615, -3.584 a zoom 13
        x, y = lat_lon_to_tile(40.615, -3.584, zoom=13)
        self.assertTrue(0 <= x < 8192)
        self.assertTrue(0 <= y < 8192)
        # Verificar límites polares
        x_pole, y_pole = lat_lon_to_tile(85.0, 0.0, zoom=10)
        self.assertTrue(0 <= x_pole < 1024)

    def test_bbox_from_center_and_haversine(self):
        """Verifica el cálculo de bounding box y distancia métrica geodésica."""
        lat, lon = 40.615, -3.584
        min_lat, min_lon, max_lat, max_lon = bbox_from_center(lat, lon, radius_km=2.0)
        self.assertTrue(min_lat < lat < max_lat)
        self.assertTrue(min_lon < lon < max_lon)

        # Distancia haversine entre centro y extremos norte/sur debe ser aprox 2.0 km (2000m)
        dist_ns = haversine_distance_m(lat, lon, max_lat, lon)
        self.assertAlmostEqual(dist_ns, 2000.0, delta=50.0)

    def test_resample_grid_bilinear(self):
        """Verifica el remuestreo bilineal de elevación."""
        grid = np.array([
            [0.0, 10.0],
            [20.0, 30.0],
        ], dtype=np.float32)

        resampled = resample_grid_bilinear(grid, (3, 3))
        self.assertEqual(resampled.shape, (3, 3))
        # El centro debe ser el promedio exacto: 15.0
        self.assertAlmostEqual(float(resampled[1, 1]), 15.0, places=2)

    def test_osm_way_chaining(self):
        """Verifica que el encadenador de segmentos una tramos adyacentes en una polilínea continua."""
        nodes_map = {
            1: (40.0, -3.0),
            2: (40.1, -3.0),
            3: (40.2, -3.0),
            4: (40.3, -3.0),
        }
        # Dos tramos de vía que comparten el nodo 2
        ways = [
            {"id": 101, "nodes": [1, 2]},
            {"id": 102, "nodes": [2, 3, 4]},
        ]

        polylines = chain_way_segments(ways, nodes_map)
        self.assertEqual(len(polylines), 1)
        # El resultado debe ser una única polilínea de 4 puntos
        self.assertEqual(len(polylines[0]), 4)
        self.assertEqual(polylines[0][0], (40.0, -3.0))
        self.assertEqual(polylines[0][-1], (40.3, -3.0))

    def test_bbox_from_points_ab(self):
        """Verifica que el bounding box del tramo A-B englobe ambos puntos con su margen."""
        from track_maker.gis.dem_downloader import bbox_from_points_ab
        lat_a, lon_a = 20.53089, -103.29324
        lat_b, lon_b = 20.67886, -103.34755
        min_lat, min_lon, max_lat, max_lon = bbox_from_points_ab(lat_a, lon_a, lat_b, lon_b, margin_km=1.0)

        # Ambos puntos deben quedar estrictamente dentro del bounding box
        self.assertTrue(min_lat < lat_a < max_lat)
        self.assertTrue(min_lat < lat_b < max_lat)
        self.assertTrue(min_lon < lon_a < max_lon)
        self.assertTrue(min_lon < lon_b < max_lon)


if __name__ == "__main__":
    unittest.main()
