"""Panel de georreferenciación, topografía DEM, trazados OSM y snapping LiDAR en el Sidebar de Blender."""

import bpy
from ..core.constants import BL_CATEGORY


class TRACKMAKER_PT_GISPanel(bpy.types.Panel):
    """Subpanel para gestión de datos GIS mundiales, relieve DEM, carreteras OSM y anclaje anti-jitter."""

    bl_label = "Topografía Real y GIS Mundial"
    bl_idname = "TRACKMAKER_PT_gis_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = BL_CATEGORY
    bl_parent_id = "TRACKMAKER_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        gis_cfg = scene.track_maker_gis

        # ---------------------------------------------------------
        # 1. BÚSQUEDA GPS MUNDIAL (NOMINATIM)
        # ---------------------------------------------------------
        box_search = layout.box()
        box_search.label(text="1. Localización GPS (Nominatim)", icon="VIEWZOOM")

        row_search = box_search.row(align=True)
        row_search.prop(gis_cfg, "search_query", text="", icon="URL")
        row_search.operator("track_maker.search_location", text="Buscar", icon="SYSTEM")

        if gis_cfg.search_result_name:
            col_res = box_search.column(align=True)
            col_res.label(text=f"Lugar: {gis_cfg.search_result_name[:42]}...", icon="CHECKBOX_HLT")

        col_coords = box_search.column(align=True)
        row_ll = col_coords.row(align=True)
        row_ll.prop(gis_cfg, "latitude")
        row_ll.prop(gis_cfg, "longitude")

        row_set_anchor = box_search.row(align=True)
        row_set_anchor.operator("track_maker.set_anchor_from_gps", text="Fijar Ancla desde GPS", icon="PINNED")

        # ---------------------------------------------------------
        # 2. DESCARGA TOPOGRAFÍA DEM (AWS TERRARIUM)
        # ---------------------------------------------------------
        box_dem = layout.box()
        box_dem.label(text="2. Relieve Terreno 3D (AWS DEM)", icon="WORLD")

        col_dem_opts = box_dem.column(align=True)
        col_dem_opts.prop(gis_cfg, "terrain_radius_km")
        row_dem_detail = col_dem_opts.row(align=True)
        row_dem_detail.prop(gis_cfg, "dem_zoom")
        row_dem_detail.prop(gis_cfg, "terrain_resolution")

        row_dem_btn = box_dem.row(align=True)
        row_dem_btn.scale_y = 1.3
        row_dem_btn.operator(
            "track_maker.download_terrain_dem",
            text="Descargar Terreno 3D (DEM)",
            icon="IMPORT",
        )

        # ---------------------------------------------------------
        # 3. IMPORTAR CARRETERAS / CIRCUITOS OSM (OVERPASS API)
        # ---------------------------------------------------------
        box_osm = layout.box()
        box_osm.label(text="3. Carreteras y Circuitos (OSM)", icon="CURVE_PATH")

        col_osm_opts = box_osm.column(align=True)
        col_osm_opts.prop(gis_cfg, "osm_road_type")
        if gis_cfg.osm_road_type == "CUSTOM":
            col_osm_opts.prop(gis_cfg, "osm_custom_filter")

        row_osm_geom = col_osm_opts.row(align=True)
        row_osm_geom.prop(gis_cfg, "osm_radius_m")
        row_osm_geom.prop(gis_cfg, "osm_curve_type")

        col_osm_opts.prop(gis_cfg, "osm_snap_to_terrain")

        row_osm_btn = box_osm.row(align=True)
        row_osm_btn.scale_y = 1.3
        row_osm_btn.operator(
            "track_maker.import_osm_roads",
            text="Importar Trazado OSM",
            icon="CURVE_DATA",
        )

        # ---------------------------------------------------------
        # 4. ANCLA GEORREFERENCIADA (ANTI-JITTER)
        # ---------------------------------------------------------
        box_anchor = layout.box()
        box_anchor.label(text="4. Ancla Georreferenciada (Anti-Jitter)", icon="ORIENTATION_GIMBAL")

        row_status = box_anchor.row()
        if gis_cfg.has_anchor:
            row_status.label(text="Estado: Ancla Activa (0, 0, 0)", icon="CHECKMARK")
            col_info = box_anchor.column(align=True)
            col_info.label(text=f"UTM X: {gis_cfg.anchor_utm_x:.2f} m | UTM Y: {gis_cfg.anchor_utm_y:.2f} m")
            col_info.label(text=f"Cota Z: {gis_cfg.anchor_elevation_z:.2f} m (EPSG {gis_cfg.epsg_code})")
        else:
            row_status.label(text="Estado: Sin Fijar", icon="INFO")
            box_anchor.label(text="Fija un ancla para evitar distorsiones en 32-bit.", icon="ERROR")

        row_anchor_ops = box_anchor.row(align=True)
        row_anchor_ops.operator("track_maker.set_geo_anchor", text="Opciones Ancla", icon="PINNED")
        row_anchor_ops.operator("track_maker.clear_geo_anchor", text="Reset", icon="PANEL_CLOSE")

        row_recenter = box_anchor.row(align=True)
        row_recenter.scale_y = 1.2
        row_recenter.operator(
            "track_maker.recenter_gis_objects",
            text="Recentrar Selección a (0, 0, 0)",
            icon="SNAP_VOLUME",
        )

        # ---------------------------------------------------------
        # 5. PROYECCIÓN Y SUAVIZADO LIDAR / TERRENO
        # ---------------------------------------------------------
        box_snap = layout.box()
        box_snap.label(text="5. Adaptación y Suavizado Terreno", icon="MESH_ICOSPHERE")

        box_snap.prop_search(
            gis_cfg,
            "target_terrain_name",
            bpy.data,
            "objects",
            text="Malla Terreno",
        )

        col_snap_opts = box_snap.column(align=True)
        col_snap_opts.prop(gis_cfg, "snap_elevation_offset")
        col_snap_opts.prop(gis_cfg, "match_terrain_banking")

        row_snap_btn = box_snap.row(align=True)
        row_snap_btn.scale_y = 1.2
        row_snap_btn.operator(
            "track_maker.snap_curve_to_terrain",
            text="Proyectar Spline a Terreno",
            icon="SNAP_FACE",
        )

        row_smooth = box_snap.row(align=True)
        row_smooth.prop(gis_cfg, "smoothing_passes")
        row_smooth.operator(
            "track_maker.smooth_curve_elevation",
            text="Suavizar",
            icon="SMOOTHCURVE",
        )


classes = (TRACKMAKER_PT_GISPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
