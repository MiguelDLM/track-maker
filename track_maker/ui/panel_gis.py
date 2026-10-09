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
        # 1. MODO TRAMO PUNTO A ➔ PUNTO B (HILLCLIMB / SPRINT / RALLY)
        # ---------------------------------------------------------
        if gis_cfg.coverage_mode == "POINTS_AB":
            # 1.0 BOTÓN MAESTRO 1-CLIC (PIPELINE RUTA-PRIMERO)
            box_quick = layout.box()
            box_quick.label(text="⚡ Flujo 1-Clic: Tramo Completo", icon="AUTO")
            row_quick_btn = box_quick.row(align=True)
            row_quick_btn.scale_y = 1.4
            row_quick_btn.operator(
                "track_maker.build_full_ab_stage",
                text="⚡ Crear Tramo Completo A ➔ B",
                icon="PLAY",
            )
            box_quick.label(
                text="Descarga ruta OSRM, genera relieve del corredor exacto y crea puertas AC.",
                icon="INFO",
            )

            # 1.1 Coordenadas de Salida y Meta
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

            # Distancia aproximada en línea recta
            d_lat = abs(gis_cfg.point_b_lat - gis_cfg.point_a_lat) * 111.32
            d_lon = abs(gis_cfg.point_b_lon - gis_cfg.point_a_lon) * 111.32 * math.cos(math.radians((gis_cfg.point_a_lat + gis_cfg.point_b_lat) / 2.0))
            dist_est_km = math.hypot(d_lat, d_lon)
            box_ab.label(text=f"Distancia recta: ~{dist_est_km:.1f} km", icon="INFO")
            box_ab.prop(gis_cfg, "corridor_margin_km")

            # 1.2 Relieve DEM Corredor
            box_dem = layout.box()
            box_dem.label(text="2. Relieve Terreno 3D (AWS DEM)", icon="WORLD")
            row_dem_detail = box_dem.row(align=True)
            row_dem_detail.prop(gis_cfg, "dem_zoom")
            row_dem_detail.prop(gis_cfg, "terrain_resolution")
            box_dem.prop(gis_cfg, "vertical_scale")
            row_dem_btn = box_dem.row(align=True)
            row_dem_btn.scale_y = 1.2
            row_dem_btn.operator(
                "track_maker.download_terrain_dem",
                text="Descargar Terreno Corredor A-B",
                icon="IMPORT",
            )

            # 1.3 Trazado Manual OSRM
            box_osm = layout.box()
            box_osm.label(text="3. Carretera Real (Trazado Spline)", icon="CURVE_PATH")
            row_osrm_btn = box_osm.row(align=True)
            row_osrm_btn.scale_y = 1.3
            row_osrm_btn.operator(
                "track_maker.fetch_osrm_route",
                text="Trazar Ruta Real A ➔ B (OSRM)",
                icon="AUTO",
            )
            col_extra = box_osm.column(align=True)
            col_extra.prop(gis_cfg, "osm_snap_to_terrain")
            row_osm_btn = box_osm.row(align=True)
            row_osm_btn.operator(
                "track_maker.import_osm_roads",
                text="Importar Red de Vías del Corredor (Overpass)",
                icon="CURVE_DATA",
            )

        # ---------------------------------------------------------
        # 1. MODO RADIO (CIRCUITO CERRADO O ÁREA GEOGRÁFICA)
        # ---------------------------------------------------------
        else:
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

            # Relieve DEM
            box_dem = layout.box()
            box_dem.label(text="2. Relieve Terreno 3D (AWS DEM)", icon="WORLD")
            row_dem_detail = box_dem.row(align=True)
            row_dem_detail.prop(gis_cfg, "dem_zoom")
            row_dem_detail.prop(gis_cfg, "terrain_resolution")
            box_dem.prop(gis_cfg, "vertical_scale")
            row_dem_btn = box_dem.row(align=True)
            row_dem_btn.scale_y = 1.3
            row_dem_btn.operator(
                "track_maker.download_terrain_dem",
                text="Descargar Terreno 3D (DEM)",
                icon="IMPORT",
            )

            # Carreteras OSM
            box_osm = layout.box()
            box_osm.label(text="3. Carreteras y Circuitos OSM", icon="CURVE_PATH")
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
        # HERRAMIENTAS DE DIBUJO LIBRE SOBRE RELIEVE REAL
        # ---------------------------------------------------------
        box_draw = layout.box()
        box_draw.label(text="Diseño Libre sobre Terreno Real", icon="GREASEPENCIL")
        row_draw = box_draw.row(align=True)
        row_draw.scale_y = 1.3
        row_draw.operator(
            "track_maker.start_surface_draw",
            text="✏️ Dibujar Pista sobre Terreno",
            icon="BRUSH_DATA",
        )

        row_draw_tools = box_draw.row(align=True)
        row_draw_tools.operator("track_maker.finish_surface_draw", text="Finalizar", icon="CHECKMARK")
        row_draw_tools.operator("track_maker.smooth_spline", text="Suavizar", icon="SMOOTHCURVE")
        row_draw_tools.operator("track_maker.project_curve_to_terrain", text="Proyectar Z", icon="SNAP_ON")

        row_draw_gates = box_draw.row(align=True)
        row_draw_gates.operator("track_maker.auto_place_ab_gates", text="🏁 Puertas Salida/Meta AC", icon="EMPTY_DATA")

        # ---------------------------------------------------------
        # PERFIL ALTIMÉTRICO EN VIVO
        # ---------------------------------------------------------
        if gis_cfg.route_info_distance > 0:
            box_alti = layout.box()
            box_alti.label(text="Perfil Altimétrico Real", icon="GRAPH")
            col_al = box_alti.column(align=True)
            col_al.label(text=f"Longitud: {gis_cfg.route_info_distance:.2f} km | Desnivel: {gis_cfg.route_info_climb:.1f} m", icon="TRACKING_FORWARDS")
            col_al.label(text=f"Cota: {gis_cfg.route_info_min_elev:.0f} m a {gis_cfg.route_info_max_elev:.0f} m", icon="DRIVER_DISTANCE")
            col_al.label(text=f"Pendiente Máxima: {gis_cfg.route_info_max_grade:.1f}%", icon="IPO_BEZIER")

        # ---------------------------------------------------------
        # 4. CONTROL DE VISOR 3D Y ESCALA REAL (ANTI-RECORTE)
        # ---------------------------------------------------------
        box_view = layout.box()
        box_view.label(text="Control de Visor 3D (Escala Real)", icon="VIEW_CAMERA")

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
        box_anchor.label(text="Ancla Georreferenciada (Anti-Jitter)", icon="ORIENTATION_GIMBAL")

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
        box_snap.label(text="Adaptación y Suavizado Terreno", icon="MESH_ICOSPHERE")

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

        row_terra = box_snap.row(align=True)
        row_terra.scale_y = 1.2
        row_terra.operator(
            "track_maker.terraform_terrain",
            text="Conformar Terreno bajo Calzada",
            icon="MESH_GRID",
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
