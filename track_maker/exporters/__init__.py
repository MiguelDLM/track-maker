"""Módulo de validación pre-flight y exportación para Assetto Corsa."""

from . import validator
from . import config_generator
from . import assetto_corsa


def register():
    assetto_corsa.register()


def unregister():
    assetto_corsa.unregister()
