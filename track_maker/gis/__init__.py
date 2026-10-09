"""Módulo de georreferenciación, topografía DEM, vías OSM y snapping LiDAR."""

from . import geo_anchor
from . import terrain_snap
from . import geocoding
from . import dem_downloader
from . import osm_roads


def register():
    geo_anchor.register()
    terrain_snap.register()
    geocoding.register()
    dem_downloader.register()
    osm_roads.register()


def unregister():
    osm_roads.unregister()
    dem_downloader.unregister()
    geocoding.unregister()
    terrain_snap.unregister()
    geo_anchor.unregister()
