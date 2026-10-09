"""Panel de generación y edición de carreteras y peraltes en el Sidebar de Blender."""

import bpy
from ..core.constants import BL_CATEGORY


class TRACKMAKER_PT_RoadPanel(bpy.types.Panel):
    """Subpanel para diseño de trazados, peraltes y generación de mallas visuales y físicas."""

    bl_label = "Carreteras y Físicas (Assetto Corsa)"
    bl_idname = "TRACKMAKER_PT_road_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = BL_CATEGORY
    bl_parent_id = "TRACKMAKER_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        road_cfg = scene.track_maker_road

        # ---------------------------------------------------------
        # 1. HERRAMIENTAS DE SPLINE (TRAZADO 3D)
        # ---------------------------------------------------------
        box_spline = layout.box()
        box_spline.label(text="Eje Central de Pista (Spline 3D)", icon="CURVE_PATH")

        row_sp_create = box_spline.row(align=True)
        row_sp_create.operator("track_maker.create_road_spline", text="Crear Spline Base", icon="ADD")
        row_sp_create.operator("track_maker.start_surface_draw", text="✏️ Dibujar sobre Terreno", icon="BRUSH_DATA")

        row_sp_tools = box_spline.row(align=True)
        row_sp_tools.operator("track_maker.toggle_spline_cyclic", text="Abierto / Cerrado", icon="LOOP_FORWARDS")
        row_sp_tools.operator("track_maker.smooth_spline", text="Suavizar", icon="SMOOTHCURVE")
        row_sp_tools.operator("track_maker.project_curve_to_terrain", text="Proyectar Z", icon="SNAP_ON")

        row_gates = box_spline.row(align=True)
        row_gates.operator("track_maker.auto_place_ab_gates", text="🏁 Puertas Salida/Meta AC", icon="EMPTY_DATA")

        # Control de Peralte (Tilt / Banking)
        box_tilt = box_spline.box()
        box_tilt.label(text="Peraltes y Curvatura", icon="DRIVER_ROTATIONAL_DIFFERENCE")
        row_tilt = box_tilt.row(align=True)
        row_tilt.operator("track_maker.set_curve_tilt", text="Fijar Peralte (°)", icon="SNAP_INCREMENT")
        row_tilt.operator("track_maker.auto_bank_curve", text="Auto-Peralte", icon="AUTO")

        # ---------------------------------------------------------
        # 2. CONFIGURACIÓN DEL PERFIL TRANSVERSAL
        # ---------------------------------------------------------
        box_prof = layout.box()
        box_prof.label(text="Perfil de Carretera", icon="MOD_EDGESPLIT")
        box_prof.prop(road_cfg, "road_name")
        box_prof.prop(road_cfg, "road_width")
        box_prof.prop(road_cfg, "road_subdivisions_x")

        # Bombeo / Camber
        box_prof.prop(road_cfg, "has_crown")
        if road_cfg.has_crown:
            box_prof.prop(road_cfg, "crown_height")

        # Bordillos / Pianos
        box_prof.prop(road_cfg, "has_kerbs")
        if road_cfg.has_kerbs:
            col_k = box_prof.column(align=True)
            col_k.prop(road_cfg, "kerb_width")
            col_k.prop(road_cfg, "kerb_height")

        # Banquetas peatonales (Escenarios urbanos)
        box_prof.prop(road_cfg, "has_sidewalks")
        if road_cfg.has_sidewalks:
            box_prof.prop(road_cfg, "sidewalk_width")

        # Muros / Barreras
        box_prof.prop(road_cfg, "has_walls")
        if road_cfg.has_walls:
            box_prof.prop(road_cfg, "wall_height")

        # Texturas
        box_prof.prop(road_cfg, "uv_tiling_v")

        # ---------------------------------------------------------
        # 3. GENERACIÓN DE MALLAS Y FÍSICAS DE AC
        # ---------------------------------------------------------
        box_gen = layout.box()
        box_gen.label(text="Generación y Físicas AC", icon="PHYSICS")
        box_gen.prop(road_cfg, "physics_subdivision_y")
        box_gen.prop(road_cfg, "visual_resolution_y")

        # Botón Geometry Nodes (Previsualización interactiva)
        row_gn = box_gen.row(align=True)
        row_gn.operator("track_maker.attach_road_geo_nodes", text="Previsualizar con Geometry Nodes", icon="NODETREE")

        # Botón Maestro de Bake / Creación de Mallas
        row_master = box_gen.row(align=True)
        row_master.scale_y = 1.4
        op_gen = row_master.operator(
            "track_maker.generate_road_meshes",
            text="Generar Malla Visual + Física (1ROAD_)",
            icon="MOD_BEVEL",
        )
        op_gen.create_visual = True
        op_gen.create_physics = True


classes = (TRACKMAKER_PT_RoadPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

