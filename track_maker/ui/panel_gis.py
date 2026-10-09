"""Panel de georreferenciación, topografía DEM, trazados OSM/OSRM y adaptación de visor 3D."""

import math
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
        # 0. MODO DE COBERTURA GEOGRÁFICA
        # ---------------------------------------------------------
        box_mode = layout.box()
        box_mode.label(text="Tipo de Cobertura Geográfica", icon="URL")
        box_mode.prop(gis_cfg, "coverage_mode", expand=True)

        # ---------------------------------------------------------
        # 1. COORDENADAS: MODO RADIO vs MODO TRAMO A -> B
        # ---------------------------------------------------------
        if gis_cfg.coverage_mode == "POINTS_AB":
            box_ab = layout.box()
            box_ab.label(text="1. Coordenadas del Tramo A ➔ B", icon="IPO_BEZIER")

            col_pt_a = box_ab.column(align=True)
            col_pt_a.label(text="Punto A (Salida):", icon="PLAY")
            row_a = col_pt_a.row(align=True)
            row_a.prop(gis_cfg, "point_a_lat", text="Lat")
            row_a.prop(gis_cfg, "point_a_lon", text="Lon")

            col_pt_b = box_ab.column(align=True)
            col_pt_b.label(text="Punto B (Meta):", icon="CHECKMARK")
            row_b = col_pt_b.row(align=True)
            row_b.prop(gis_cfg, "point_b_lat", text="Lat")
            row_b.prop(gis_cfg, "point_b_lon", text="Lon")

            row_ab_tools = box_ab.row(align=True)
            row_ab_tools.operator("track_maker.swap_points_ab", text="Invertir Sentido (A ⇄ B)", icon="FILE_REFRESH")

            # Cálculo en vivo de distancia estimada en línea recta
            d_lat = abs(gis_cfg.point_b_lat - gis_cfg.point_a_lat) * 111.32
            d_lon = abs(gis_cfg.point_b_lon - gis_cfg.point_a_lon) * 111.32 * math.cos(math.radians((gis_cfg.point_a_lat + gis_cfg.point_b_lat) / 2.0))
            dist_est_km = math.hypot(d_lat, d_lon)
            box_ab.label(text=f"Distancia recta: ~{dist_est_km:.1f} km", icon="INFO")
            box_ab.prop(gis_cfg, "corridor_margin_km")

        else:  # Modo RADIO (Circuito cerrado)
            box_search = layout.box()
            box_search.label(text="1. Localización GPS (Nominatim)", icon="VIEWZOOM")

            row_search = box_search.row(align=True)
            row_search.prop(gis_cfg, "search_query", text="", icon="URL")
            row_search.operator("track_maker.search_location", text="Buscar", icon="SYSTEM")

            if gis_cfg.search_result_name:
                col_res = box_search.column(align=True)
                col_res.label(text=f"Lugar: {gis_cfg.search_result_name[:40]}...", icon="CHECKBOX_HLT")

            col_coords = box_search.column(align=True)
            row_ll = col_coords.row(align=True)
            row_ll.prop(gis_cfg, "latitude")
            row_ll.prop(gis_cfg, "longitude")

            box_search.prop(gis_cfg, "terrain_radius_km")

            row_set_anchor = box_search.row(align=True)
            row_set_anchor.operator("track_maker.set_anchor_from_gps", text="Fijar Ancla desde GPS", icon="PINNED")

        # ---------------------------------------------------------
        # 2. DESCARGA TOPOGRAFÍA DEM (AWS TERRARIUM)
        # ---------------------------------------------------------
        box_dem = layout.box()
        box_dem.label(text="2. Relieve Terreno 3D (AWS DEM)", icon="WORLD")

        row_dem_detail = box_dem.row(align=True)
        row_dem_detail.prop(gis_cfg, "dem_zoom")
        row_dem_detail.prop(gis_cfg, "terrain_resolution")

        row_dem_btn = box_dem.row(align=True)
        row_dem_btn.scale_y = 1.3
        btn_dem_text = "Descargar Terreno Corredor A-B" if gis_cfg.coverage_mode == "POINTS_AB" else "Descargar Terreno 3D (DEM)"
        row_dem_btn.operator(
            "track_maker.download_terrain_dem",
            text=btn_dem_text,
            icon="IMPORT",
        )

        # ---------------------------------------------------------
        # 3. CARRETERAS Y CIRCUITOS (OSM / OSRM)
        # ---------------------------------------------------------
        box_osm = layout.box()
        box_osm.label(text="3. Carreteras y Trazados Reales", icon="CURVE_PATH")

        if gis_cfg.coverage_mode == "POINTS_AB":
            # Botón destacado OSRM para ruta exacta de conducción
            row_osrm_btn = box_osm.row(align=True)
            row_osrm_btn.scale_y = 1.35
            row_osrm_btn.operator(
                "track_maker.fetch_osrm_route",
                text="Trazar Ruta Real A ➔ B (OSRM)",
                icon="AUTO",
            )
            box_osm.label(text="Calcula la carretera transitable exacta entre A y B.", icon="INFO")

            # Opción secundaria Overpass de corredor
            col_extra = box_osm.column(align=True)
            col_extra.prop(gis_cfg, "osm_snap_to_terrain")
            row_osm_btn = box_osm.row(align=True)
            row_osm_btn.operator(
                "track_maker.import_osm_roads",
                text="Importar Red de Vías del Corredor (Overpass)",
                icon="CURVE_DATA",
            )

        else:  # Modo RADIUS
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
        # 4. CONTROL DE VISOR 3D Y ESCALA REAL (ANTI-RECORTE)
        # ---------------------------------------------------------
        box_view = layout.box()
        box_view.label(text="4. Control de Visor 3D (Escala Real)", icon="VIEW_CAMERA")

        row_frame = box_view.row(align=True)
        row_frame.scale_y = 1.2
        row_frame.operator(
            "track_maker.frame_gis_view",
            text="Enfocar Terreno / Pista en Visor",
            icon="VIEWZOOM",
        )

        col_view_opts = box_view.column(align=True)
        col_view_opts.prop(gis_cfg, "auto_adjust_clipping")
        col_view_opts.prop(gis_cfg, "auto_frame_view")
        box_view.label(text="Ajusta la distancia de visión para evitar cortes al hacer zoom.", icon="INFO")

        # ---------------------------------------------------------
        # 5. ANCLA GEORREFERENCIADA (ANTI-JITTER)
        # ---------------------------------------------------------
        box_anchor = layout.box()
        box_anchor.label(text="5. Ancla Georreferenciada (Anti-Jitter)", icon="ORIENTATION_GIMBAL")

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
        # 6. PROYECCIÓN Y SUAVIZADO TERRENO
        # ---------------------------------------------------------
        box_snap = layout.box()
        box_snap.label(text="6. Adaptación y Suavizado Terreno", icon="MESH_ICOSPHERE")

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
