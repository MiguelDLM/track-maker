"""Módulo de interfaz gráfica de Track Maker."""

from . import panel_main
from . import panel_race_nodes
from . import panel_road
from . import panel_gis
from . import panel_export


def register():
    panel_main.register()
    panel_gis.register()
    panel_road.register()
    panel_race_nodes.register()
    panel_export.register()


def unregister():
    panel_export.unregister()
    panel_race_nodes.unregister()
    panel_road.unregister()
    panel_gis.unregister()
    panel_main.unregister()



