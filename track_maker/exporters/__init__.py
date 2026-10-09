"""Módulo de validación pre-flight y exportación para Assetto Corsa."""

from . import validator
from . import config_generator
from . import assetto_corsa
from . import map_generator


def register():
    assetto_corsa.register()
    map_generator.register()


def unregister():
    map_generator.unregister()
    assetto_corsa.unregister()
