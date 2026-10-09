"""Track Maker: Addon de Blender para creación de circuitos y tramos reales para Assetto Corsa."""

bl_info = {
    "name": "Track Maker (Assetto Corsa Edition)",
    "author": "Track Maker Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Track Maker Tab",
    "description": "Herramienta para creación y exportación de circuitos y tramos reales para Assetto Corsa.",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}

# Soporte para recarga en caliente de submódulos durante desarrollo
if "bpy" in locals():
    import importlib
    if "core" in locals():
        importlib.reload(core)
    if "race_nodes" in locals():
        importlib.reload(race_nodes)
    if "road" in locals():
        importlib.reload(road)
    if "gis" in locals():
        importlib.reload(gis)
    if "exporters" in locals():
        importlib.reload(exporters)
    if "ui" in locals():
        importlib.reload(ui)

import bpy
from . import core
from . import race_nodes
from . import road
from . import gis
from . import exporters
from . import ui

modules = (
    core,
    race_nodes,
    road,
    gis,
    exporters,
    ui,
)


def register():
    for mod in modules:
        mod.register()


def unregister():
    for mod in reversed(modules):
        mod.unregister()


if __name__ == "__main__":
    register()
