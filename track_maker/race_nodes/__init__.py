"""Módulo para la gestión y colocación de nodos de carrera de Assetto Corsa."""

from . import spawn_manager
from . import timing_gates


def register():
    spawn_manager.register()
    timing_gates.register()


def unregister():
    timing_gates.unregister()
    spawn_manager.unregister()
