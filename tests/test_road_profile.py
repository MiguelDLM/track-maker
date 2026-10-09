"""Tests unitarios para las funciones matemáticas y de perfiles de Track Maker."""

import sys
import unittest
from unittest.mock import MagicMock

import tests  # Inicializa los mocks de Blender

from track_maker.road.profile_generator import generate_cross_section_profile



class TestRoadProfileGenerator(unittest.TestCase):
    def test_standard_road_profile(self):
        # 1. Calzada estándar de 10m sin bordillos
        profile = generate_cross_section_profile(
            road_width=10.0,
            subdivisions_x=4,
            has_crown=True,
            crown_height=0.10,
            has_kerbs=False,
            has_sidewalks=False,
            has_walls=False,
            for_physics_only=False,
        )

        # 4 subdivisiones = 5 puntos
        self.assertEqual(len(profile), 5)
        # Extremo izquierdo en -5m, derecho en +5m
        self.assertAlmostEqual(profile[0].offset_x, -5.0)
        self.assertAlmostEqual(profile[-1].offset_x, 5.0)
        # Centro en 0m con altura de bombeo 0.10m
        self.assertAlmostEqual(profile[2].offset_x, 0.0)
        self.assertAlmostEqual(profile[2].offset_z, 0.10)
        # Bordes con altura 0.0m
        self.assertAlmostEqual(profile[0].offset_z, 0.0)
        self.assertAlmostEqual(profile[-1].offset_z, 0.0)

    def test_road_with_kerbs_and_walls(self):
        # 2. Calzada con bordillos y muros laterales
        profile = generate_cross_section_profile(
            road_width=8.0,
            subdivisions_x=4,
            has_crown=False,
            has_kerbs=True,
            kerb_width=0.50,
            kerb_height=0.15,
            has_sidewalks=False,
            has_walls=True,
            wall_height=1.0,
            for_physics_only=False,
        )

        # Verificar presencia de muros y bordillos
        types = [p.surface_type for p in profile]
        self.assertIn("WALL", types)
        self.assertIn("KERB", types)
        self.assertIn("ROAD", types)

        # Muro izquierdo debe estar más a la izquierda que el bordillo
        wall_pts_l = [p for p in profile if p.surface_type == "WALL" and p.offset_x < 0]
        self.assertTrue(len(wall_pts_l) >= 2)
        # El muro debe llegar a la altura de kerb_height + wall_height
        self.assertAlmostEqual(wall_pts_l[0].offset_z, 1.15)

    def test_physics_only_profile(self):
        # 3. Perfil físico para 1ROAD_ (solo asfalto de contacto)
        profile_phys = generate_cross_section_profile(
            road_width=9.0,
            subdivisions_x=6,
            for_physics_only=True,
        )

        # Solo debe contener puntos de tipo ROAD
        types = set(p.surface_type for p in profile_phys)
        self.assertEqual(types, {"ROAD"})
        self.assertEqual(len(profile_phys), 7)


if __name__ == "__main__":
    unittest.main()
