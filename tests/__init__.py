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


class MockMesh:
    def __init__(self, name="Mesh"):
        self.name = name
        self.vertices = []
        self.polygons = []
        self.materials = []


def mock_new_mesh(name):
    return MockMesh(name)


def mock_new_material(name):
    mat = MagicMock()
    mat.name = name
    return mat


# Mockear módulos de Blender si no estamos dentro de Blender
if "bpy" not in sys.modules:
    mock_bpy = MagicMock()
    mock_bpy.types.Operator = type("Operator", (), {})
    mock_bpy.types.Panel = type("Panel", (), {})
    mock_bpy.types.PropertyGroup = type("PropertyGroup", (), {})
    mock_bpy.data.meshes.new.side_effect = mock_new_mesh
    mock_bpy.data.materials.new.side_effect = mock_new_material
    mock_bpy.data.materials.get.return_value = None
    mock_bpy.data.meshes.get.return_value = None
    sys.modules["bpy"] = mock_bpy
    sys.modules["bpy.props"] = MagicMock()

class MockBMVerts(list):
    def new(self, co):
        v = MagicMock()
        v.co = co
        self.append(v)
        return v


class MockBMFaces(list):
    def new(self, verts):
        f = MagicMock()
        f.verts = verts
        self.append(f)
        return f


class MockBMEdges(list):
    def new(self, verts):
        e = MagicMock()
        e.verts = verts
        self.append(e)
        return e


class MockBMesh:
    def __init__(self):
        self.verts = MockBMVerts()
        self.faces = MockBMFaces()
        self.edges = MockBMEdges()

    def to_mesh(self, mesh):
        mesh.vertices = list(self.verts)
        mesh.polygons = list(self.faces)

    def free(self):
        pass


if "bmesh" not in sys.modules:
    mock_bmesh = MagicMock()
    mock_bmesh.new.side_effect = MockBMesh
    sys.modules["bmesh"] = mock_bmesh

if "mathutils" not in sys.modules:
    mock_mathutils = MagicMock()
    mock_mathutils.Vector = MockVector
    mock_bvhtree = MagicMock()
    sys.modules["mathutils"] = mock_mathutils
    sys.modules["mathutils.bvhtree"] = mock_bvhtree
