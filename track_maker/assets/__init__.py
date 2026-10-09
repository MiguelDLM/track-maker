"""Módulo de assets, señalética, iluminación, edificios y fotogrametría 'Mexico-Pack'."""

from . import mexico_pack
from . import barrier_generator
from . import signage_generator
from . import lighting_generator
from . import building_populator
from . import google_3d_tiles

modules = (
    barrier_generator,
    signage_generator,
    lighting_generator,
    building_populator,
    google_3d_tiles,
)


def register():
    for m in modules:
        m.register()


def unregister():
    for m in reversed(modules):
        try:
            m.unregister()
        except Exception:
            pass
