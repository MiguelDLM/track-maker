"""Tests unitarios para la validación pre-flight y generación de configuraciones de Assetto Corsa."""

import os
import json
import tempfile
import unittest
from unittest.mock import MagicMock

import tests  # Inicializa los mocks compartidos de Blender

from track_maker.exporters.config_generator import (
    generate_surfaces_ini_content,
    generate_models_ini_content,
    generate_ui_track_json_data,
    create_track_mod_package,
)
from track_maker.exporters.validator import (
    validate_scene_for_assetto_corsa,
    ValidationIssue,
    ValidationReport,
)


class TestConfigGenerator(unittest.TestCase):
    def test_surfaces_ini_generation(self):
        content = generate_surfaces_ini_content()
        self.assertIn("[SURFACE_0]", content)
        self.assertIn("KEY=ROAD", content)
        self.assertIn("FRICTION=0.98", content)
        self.assertIn("IS_VALID_TRACK=1", content)
        self.assertIn("KEY=KERB", content)
        self.assertIn("VIBRATION_GAIN=", content)

    def test_models_ini_generation(self):
        content = generate_models_ini_content("Autodromo_Hermanos_Rodriguez")
        self.assertIn("[MODEL_0]", content)
        self.assertIn("FILE=Autodromo_Hermanos_Rodriguez.kn5", content)
        self.assertIn("POSITION=0,0,0", content)

    def test_ui_track_json_structure(self):
        data = generate_ui_track_json_data(
            name="Circuito_Pruebas",
            author="Gemini Dev",
            country="México",
            city="Monterrey",
            length_m=4250.0,
            width_m=10.0,
            pitboxes=32,
            circuit_type="CIRCUIT",
        )

        self.assertEqual(data["name"], "Circuito_Pruebas")
        self.assertEqual(data["length"], "4250 m")
        self.assertEqual(data["pitboxes"], "32")
        self.assertEqual(data["country"], "México")
        self.assertIn("circuit", data["tags"])

    def test_package_filesystem_creation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            track_dir = create_track_mod_package(
                base_export_dir=temp_dir,
                track_name="TestTrack",
                author="Tester",
                country="Spain",
                city="Madrid",
                length_m=2500.0,
            )

            # Verificar que se crearon los archivos esenciales
            self.assertTrue(os.path.exists(os.path.join(track_dir, "surfaces.ini")))
            self.assertTrue(os.path.exists(os.path.join(track_dir, "models.ini")))
            self.assertTrue(os.path.exists(os.path.join(track_dir, "data", "surfaces.ini")))
            self.assertTrue(os.path.exists(os.path.join(track_dir, "ui", "ui_track.json")))

            # Verificar validez del JSON generado
            with open(os.path.join(track_dir, "ui", "ui_track.json"), "r", encoding="utf-8") as f:
                json_data = json.load(f)
                self.assertEqual(json_data["name"], "TestTrack")


class TestPreflightValidator(unittest.TestCase):
    def test_empty_scene_fails_validation(self):
        mock_scene = MagicMock()
        mock_scene.objects = []
        mock_scene.track_maker_circuit.circuit_name = "Pista_Vacia"
        mock_scene.track_maker_circuit.circuit_type = "CIRCUIT"

        report = validate_scene_for_assetto_corsa(mock_scene)
        self.assertFalse(report.is_valid)

        error_messages = [e.message for e in report.errors]
        # Debe fallar por falta de AC_START_0, AC_TIME_0 y 1ROAD_
        self.assertTrue(any("AC_START_0" in m for m in error_messages))
        self.assertTrue(any("AC_TIME_0" in m for m in error_messages))
        self.assertTrue(any("1ROAD_" in m for m in error_messages))

    def test_complete_scene_passes_validation(self):
        mock_scene = MagicMock()

        def make_obj(name, obj_type="EMPTY"):
            o = MagicMock()
            o.name = name
            o.type = obj_type
            o.scale = MagicMock(x=1.0, y=1.0, z=1.0)
            return o

        mock_scene.objects = [
            make_obj("AC_START_0"),
            make_obj("AC_START_1"),
            make_obj("AC_PIT_0"),
            make_obj("AC_TIME_0_L"),
            make_obj("AC_TIME_0_R"),
            make_obj("1ROAD_Principal", "MESH"),
            make_obj("ROAD_Visual", "MESH"),
        ]
        mock_scene.track_maker_circuit.circuit_name = "Pista_Completa"
        mock_scene.track_maker_circuit.circuit_type = "CIRCUIT"

        report = validate_scene_for_assetto_corsa(mock_scene)
        self.assertTrue(report.is_valid)
        self.assertEqual(len(report.errors), 0)


if __name__ == "__main__":
    unittest.main()
