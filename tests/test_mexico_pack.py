"""Tests unitarios para la biblioteca de assets y generadores 'Mexico-Pack'."""

import unittest
from unittest.mock import MagicMock

import tests  # Inicializa los mocks de Blender

from track_maker.assets.mexico_pack import (
    build_new_jersey_barrier_mesh,
    build_armco_barrier_mesh,
    build_sct_gantry_mesh,
    build_sct_speed_sign_mesh,
    build_highway_lighting_mesh,
    build_oxxo_store_mesh,
    build_gas_station_mesh,
    build_industrial_warehouse_mesh,
    build_mexican_house_with_tinaco_mesh,
)
from track_maker.core.constants import (
    COLLECTION_BARRIERS,
    COLLECTION_SIGNS,
    COLLECTION_LIGHTING,
    COLLECTION_BUILDINGS,
    PREFIX_PHYS_WALL,
)


class TestMexicoPackAssets(unittest.TestCase):
    def test_new_jersey_barrier_mesh_creation(self):
        mesh = build_new_jersey_barrier_mesh(length=3.0, height=0.85)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 10)
        self.assertGreater(len(mesh.polygons), 6)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Concrete_Jersey", mat_names)
        self.assertIn("MAT_TM_Reflector_Yellow", mat_names)

    def test_armco_barrier_mesh_creation(self):
        mesh = build_armco_barrier_mesh(length=4.0, height=0.75)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 8)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Metal_Galvanized", mat_names)

    def test_sct_gantry_mesh_creation(self):
        mesh = build_sct_gantry_mesh(span_width=14.0, clearance=5.8)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 16)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Sign_Green_SCT", mat_names)
        self.assertIn("MAT_TM_Metal_Galvanized", mat_names)

    def test_sct_speed_sign_mesh_creation(self):
        mesh = build_sct_speed_sign_mesh(speed_limit=80)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 16)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Sign_Red", mat_names)
        self.assertIn("MAT_TM_Sign_White", mat_names)

    def test_highway_lighting_mesh_creation(self):
        mesh = build_highway_lighting_mesh(height=10.0, is_double=True)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 16)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Metal_Galvanized", mat_names)
        self.assertIn("MAT_TM_Reflector_White", mat_names)

    def test_oxxo_store_mesh_creation(self):
        mesh = build_oxxo_store_mesh(width=12.0, depth=9.0, height=4.2)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 12)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Oxxo_Red", mat_names)
        self.assertIn("MAT_TM_Oxxo_Yellow", mat_names)

    def test_gas_station_mesh_creation(self):
        mesh = build_gas_station_mesh(width=20.0, depth=14.0, clearance=5.2)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 16)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Pemex_Green", mat_names)

    def test_industrial_warehouse_mesh_creation(self):
        mesh = build_industrial_warehouse_mesh(width=24.0, depth=35.0, height=7.5)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 10)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Industrial_Sheet", mat_names)

    def test_mexican_house_with_tinaco_mesh_creation(self):
        mesh = build_mexican_house_with_tinaco_mesh(width=8.0, depth=10.0, height=5.5)
        self.assertIsNotNone(mesh)
        self.assertGreater(len(mesh.vertices), 20)
        mat_names = [m.name for m in mesh.materials]
        self.assertIn("MAT_TM_Brick_Mexican", mat_names)
        self.assertIn("MAT_TM_Rotoplas_Black", mat_names)


if __name__ == "__main__":
    unittest.main()
