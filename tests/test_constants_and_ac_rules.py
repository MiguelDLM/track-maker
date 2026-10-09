"""Tests para verificar que los estándares de Assetto Corsa se cumplen en las constantes."""

import sys
import unittest
from unittest.mock import MagicMock

if "bpy" not in sys.modules:
    sys.modules["bpy"] = MagicMock()
    sys.modules["bpy.props"] = MagicMock()
if "mathutils" not in sys.modules:
    sys.modules["mathutils"] = MagicMock()
if "bmesh" not in sys.modules:
    sys.modules["bmesh"] = MagicMock()

from track_maker.core.constants import (
    PREFIX_PHYS_ROAD,
    PREFIX_PHYS_WALL,
    PREFIX_PHYS_KERB,
    PREFIX_START,
    PREFIX_PIT,
    NAME_HOTLAP_START,
    NAME_TIME_0_L,
    NAME_TIME_0_R,
    SURFACE_DEFAULTS,
)


class TestAssettoCorsaStandards(unittest.TestCase):
    def test_prefixes_match_ac_engine(self):
        # Assetto Corsa requiere obligatoriamente prefijos numéricos para físicas
        self.assertTrue(PREFIX_PHYS_ROAD.startswith("1ROAD_"))
        self.assertTrue(PREFIX_PHYS_WALL.startswith("1WALL_"))
        self.assertTrue(PREFIX_PHYS_KERB.startswith("1KERB_"))

        # Prefijos de objetos de carrera
        self.assertEqual(PREFIX_START, "AC_START_")
        self.assertEqual(PREFIX_PIT, "AC_PIT_")
        self.assertEqual(NAME_HOTLAP_START, "AC_HOTLAP_START_0")
        self.assertEqual(NAME_TIME_0_L, "AC_TIME_0_L")
        self.assertEqual(NAME_TIME_0_R, "AC_TIME_0_R")

    def test_surfaces_defaults(self):
        # La superficie ROAD debe ser válida para pista y tener fricción estándar
        self.assertIn("ROAD", SURFACE_DEFAULTS)
        road_cfg = SURFACE_DEFAULTS["ROAD"]
        self.assertEqual(road_cfg["IS_VALID_TRACK"], 1)
        self.assertGreaterEqual(road_cfg["FRICTION"], 0.95)

        # La hierba no debe ser válida para pista
        grass_cfg = SURFACE_DEFAULTS["GRASS"]
        self.assertEqual(grass_cfg["IS_VALID_TRACK"], 0)
        self.assertLess(grass_cfg["FRICTION"], 0.80)


if __name__ == "__main__":
    unittest.main()
