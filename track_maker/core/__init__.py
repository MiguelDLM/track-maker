"""Módulo core del addon Track Maker."""

from . import constants
from . import properties
from . import utils


def register():
    properties.register()


def unregister():
    properties.unregister()
