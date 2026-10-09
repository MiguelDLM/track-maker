"""Configuración global de mocks de Blender para ejecución de tests fuera de Blender."""

import sys
from unittest.mock import MagicMock


class MockVector:
    """Implementación ligera de Vector para pruebas fuera del runtime de Blender."""

    def __init__(self, coords=(0.0, 0.0, 0.0)):
        self.x = float(coords[0])
        self.y = float(coords[1])
        self.z = float(coords[2]) if len(coords) > 2 else 0.0

    def __getitem__(self, idx):
        return (self.x, self.y, self.z)[idx]

    def __repr__(self):
        return f"MockVector(({self.x}, {self.y}, {self.z}))"


# Mockear módulos de Blender si no estamos dentro de Blender
if "bpy" not in sys.modules:
    sys.modules["bpy"] = MagicMock()
    sys.modules["bpy.props"] = MagicMock()

if "bmesh" not in sys.modules:
    sys.modules["bmesh"] = MagicMock()

if "mathutils" not in sys.modules:
    mock_mathutils = MagicMock()
    mock_mathutils.Vector = MockVector
    mock_bvhtree = MagicMock()
    sys.modules["mathutils"] = mock_mathutils
    sys.modules["mathutils.bvhtree"] = mock_bvhtree
