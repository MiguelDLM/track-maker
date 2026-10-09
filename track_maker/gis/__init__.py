"""Módulo de georreferenciación, anclaje local y snapping LiDAR."""

from . import geo_anchor
from . import terrain_snap


def register():
    geo_anchor.register()
    terrain_snap.register()


def unregister():
    terrain_snap.unregister()
    geo_anchor.unregister()
