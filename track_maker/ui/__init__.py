"""Módulo de interfaz gráfica de Track Maker."""

from . import panel_main
from . import panel_race_nodes
from . import panel_road


def register():
    panel_main.register()
    panel_race_nodes.register()
    panel_road.register()


def unregister():
    panel_road.unregister()
    panel_race_nodes.unregister()
    panel_main.unregister()

