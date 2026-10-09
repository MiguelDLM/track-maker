"""Panel de georreferenciación y proyección LiDAR en el Sidebar de Blender."""

import bpy
from ..core.constants import BL_CATEGORY


class TRACKMAKER_PT_GISPanel(bpy.types.Panel):
    """Subpanel para gestión de anclaje georreferenciado (anti-jitter) y proyección sobre nubes LiDAR / DTM."""

    bl_label = "Topografía Real y LiDAR (GIS)"
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
        # 1. ANCLA GEORREFERENCIADA (ANTI-JITTER)
        # ---------------------------------------------------------
        box_anchor = layout.box()
        box_anchor.label(text="Ancla Georreferenciada (Anti-Jitter)", icon="ORIENTATION_GIMBAL")

        # Estado del ancla
        row_status = box_anchor.row()
        if gis_cfg.has_anchor:
            row_status.label(text="Estado: Ancla Activa (0, 0, 0)", icon="CHECKMARK")
            col_info = box_anchor.column(align=True)
            col_info.label(text=f"UTM X: {gis_cfg.anchor_utm_x:.2f} m")
            col_info.label(text=f"UTM Y: {gis_cfg.anchor_utm_y:.2f} m")
            col_info.label(text=f"Cota Z: {gis_cfg.anchor_elevation_z:.2f} m (EPSG {gis_cfg.epsg_code})")
        else:
            row_status.label(text="Estado: Sin Fijar", icon="INFO")
            box_anchor.label(text="Fija un ancla para evitar deformaciones en 32-bit.", icon="ERROR")

        row_anchor_ops = box_anchor.row(align=True)
        row_anchor_ops.operator("track_maker.set_geo_anchor", text="Fijar Ancla", icon="PINNED")
        row_anchor_ops.operator("track_maker.clear_geo_anchor", text="Reset", icon="PANEL_CLOSE")

        row_recenter = box_anchor.row(align=True)
        row_recenter.scale_y = 1.2
        row_recenter.operator(
            "track_maker.recenter_gis_objects",
            text="Recentrar Selección a (0, 0, 0)",
            icon="SNAP_VOLUME",
        )

        # ---------------------------------------------------------
        # 2. PROYECCIÓN TOPOGRÁFICA (SNAP LIDAR / DTM)
        # ---------------------------------------------------------
        box_snap = layout.box()
        box_snap.label(text="Adaptación a Malla LiDAR / Terreno", icon="MESH_ICOSPHERE")

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
        row_snap_btn.scale_y = 1.3
        row_snap_btn.operator(
            "track_maker.snap_curve_to_terrain",
            text="Proyectar Spline a Terreno LiDAR",
            icon="IMPORT",
        )

        # ---------------------------------------------------------
        # 3. FILTRADO Y SUAVIZADO DE RUIDO
        # ---------------------------------------------------------
        box_smooth = layout.box()
        box_smooth.label(text="Filtrado de Ruido LiDAR", icon="MOD_SMOOTH")
        box_smooth.prop(gis_cfg, "smoothing_passes")

        row_smooth_btn = box_smooth.row(align=True)
        row_smooth_btn.operator(
            "track_maker.smooth_curve_elevation",
            text="Suavizar Pendientes",
            icon="SMOOTHCURVE",
        )


classes = (TRACKMAKER_PT_GISPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
