"""Pruebas unitarias para el generador unificado de tramos A-B y las herramientas de dibujo de curvas."""

import math
import unittest
from unittest.mock import MagicMock
from mathutils import Vector

from track_maker.gis.stage_builder import (
    bbox_from_route_coords,
    place_ab_timing_gates_on_curve,
    TRACKMAKER_OT_BuildFullABStage,
)
from track_maker.road.curve_tools import (
    TRACKMAKER_OT_StartSurfaceDraw,
    TRACKMAKER_OT_FinishSurfaceDraw,
    TRACKMAKER_OT_ProjectCurveToTerrain,
    TRACKMAKER_OT_SmoothSpline,
    TRACKMAKER_OT_AutoPlaceABGates,
)


class TestStageBuilderAndDrawing(unittest.TestCase):

    def test_bbox_from_route_coords(self):
        """Verifica que el cálculo de bounding box envuelva todos los puntos con el margen especificado."""
        coords = [
            (20.5308, -103.2932),
            (20.6000, -103.3100),
            (20.6788, -103.3475),
        ]
        margin_km = 1.0
        min_lat, min_lon, max_lat, max_lon = bbox_from_route_coords(coords, margin_km=margin_km)

        # El bbox debe ser estrictamente mayor que los extremos de las coordenadas
        self.assertLess(min_lat, min(c[0] for c in coords))
        self.assertGreater(max_lat, max(c[0] for c in coords))
        self.assertLess(min_lon, min(c[1] for c in coords))
        self.assertGreater(max_lon, max(c[1] for c in coords))

        # Verificar caso de lista vacía
        with self.assertRaises(ValueError):
            bbox_from_route_coords([], margin_km=1.0)

    def test_operator_identifiers(self):
        """Verifica que los nuevos operadores registren los identificadores requeridos para la UI."""
        self.assertEqual(TRACKMAKER_OT_BuildFullABStage.bl_idname, "track_maker.build_full_ab_stage")
        self.assertEqual(TRACKMAKER_OT_StartSurfaceDraw.bl_idname, "track_maker.start_surface_draw")
        self.assertEqual(TRACKMAKER_OT_FinishSurfaceDraw.bl_idname, "track_maker.finish_surface_draw")
        self.assertEqual(TRACKMAKER_OT_ProjectCurveToTerrain.bl_idname, "track_maker.project_curve_to_terrain")
        self.assertEqual(TRACKMAKER_OT_SmoothSpline.bl_idname, "track_maker.smooth_spline")
        self.assertEqual(TRACKMAKER_OT_AutoPlaceABGates.bl_idname, "track_maker.auto_place_ab_gates")

    def test_place_ab_timing_gates_validation(self):
        """Verifica que la función de colocación de puertas valide adecuadamente objetos inválidos."""
        with self.assertRaises(ValueError):
            place_ab_timing_gates_on_curve(None, None)

        mock_obj = MagicMock()
        mock_obj.type = "MESH"  # No es una curva
        with self.assertRaises(ValueError):
            place_ab_timing_gates_on_curve(None, mock_obj)


if __name__ == "__main__":
    unittest.main()
