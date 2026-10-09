"""Módulo de generación de carreteras procedurales y colisionadores de Assetto Corsa."""

from . import curve_tools
from . import profile_generator
from . import road_generator
from . import geometry_nodes


def register():
    curve_tools.register()
    road_generator.register()
    geometry_nodes.register()


def unregister():
    geometry_nodes.unregister()
    road_generator.unregister()
    curve_tools.unregister()
