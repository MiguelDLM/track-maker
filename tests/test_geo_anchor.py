"""Tests unitarios para el cálculo de coordenadas georreferenciadas y anclaje local (anti-jitter)."""

import sys
import unittest
from unittest.mock import MagicMock

import tests  # Inicializa los mocks de Blender

from track_maker.gis.geo_anchor import wgs84_to_utm, utm_to_local, local_to_utm



class TestGeoAnchorMath(unittest.TestCase):
    def test_wgs84_to_utm_madrid(self):
        # Madrid: Lat 40.4168, Lon -3.7038 (Huso 30 Norte)
        lat = 40.4168
        lon = -3.7038
        easting, northing, zone, hemisphere = wgs84_to_utm(lat, lon)

        self.assertEqual(zone, 30)
        self.assertEqual(hemisphere, "N")
        # El centro de Madrid ronda los 440.000m Easting y 4.474.000m Northing
        self.assertAlmostEqual(easting, 440316.0, delta=100.0)
        self.assertAlmostEqual(northing, 4474246.0, delta=100.0)

    def test_wgs84_to_utm_mexico_city(self):
        # CDMX: Lat 19.4326, Lon -99.1332 (Huso 14 Norte)
        lat = 19.4326
        lon = -99.1332
        easting, northing, zone, hemisphere = wgs84_to_utm(lat, lon)

        self.assertEqual(zone, 14)
        self.assertEqual(hemisphere, "N")
        # El Zócalo de CDMX ronda los 486.000m Easting y 2.148.700m Northing
        self.assertAlmostEqual(easting, 486026.0, delta=100.0)
        self.assertAlmostEqual(northing, 2148767.0, delta=100.0)

    def test_utm_local_roundtrip_precision(self):
        # Simular una carretera con coordenadas reales gigantescas
        real_utm_x = 450325.875
        real_utm_y = 4210452.125
        real_elev_z = 1845.500

        # Ancla en el inicio del circuito
        anchor_x = 450300.0
        anchor_y = 4210400.0
        anchor_z = 1840.0

        local_vec = utm_to_local(real_utm_x, real_utm_y, real_elev_z, anchor_x, anchor_y, anchor_z)

        # En coordenadas locales, los números son pequeños (del orden de decenas de metros)
        # Esto previene por completo la pérdida de precisión de 32 bits (jitter)
        self.assertAlmostEqual(local_vec.x, 25.875, places=3)
        self.assertAlmostEqual(local_vec.y, 52.125, places=3)
        self.assertAlmostEqual(local_vec.z, 5.500, places=3)

        # Inversión exacta
        back_x, back_y, back_z = local_to_utm(local_vec.x, local_vec.y, local_vec.z, anchor_x, anchor_y, anchor_z)
        self.assertAlmostEqual(back_x, real_utm_x, places=3)
        self.assertAlmostEqual(back_y, real_utm_y, places=3)
        self.assertAlmostEqual(back_z, real_elev_z, places=3)


if __name__ == "__main__":
    unittest.main()
