"""Módulo de interfaz gráfica de Track Maker."""

from . import panel_main
from . import panel_race_nodes


def register():
    panel_main.register()
    panel_race_nodes.register()


def unregister():
    panel_race_nodes.unregister()
    panel_main.unregister()
