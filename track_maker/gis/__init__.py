"""Módulo de georreferenciación, topografía DEM, vías OSM, enrutamiento A-B y snapping LiDAR."""

from . import geo_anchor
from . import terrain_snap
from . import geocoding
from . import dem_downloader
from . import osm_roads
from . import viewport_tools
from . import osrm_routing
from . import stage_builder


def register():
    geo_anchor.register()
    terrain_snap.register()
    geocoding.register()
    dem_downloader.register()
    osm_roads.register()
    viewport_tools.register()
    osrm_routing.register()
    stage_builder.register()


def unregister():
    stage_builder.unregister()
    osrm_routing.unregister()
    viewport_tools.unregister()
    osm_roads.unregister()
    dem_downloader.unregister()
    geocoding.unregister()
    terrain_snap.unregister()
    geo_anchor.unregister()
