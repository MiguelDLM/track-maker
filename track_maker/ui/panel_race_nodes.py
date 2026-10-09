"""Panel de colocación y gestión de Nodos de Carrera (AC_START, AC_PIT, AC_TIME)."""

import bpy
from ..core.constants import BL_CATEGORY


class TRACKMAKER_PT_RaceNodesPanel(bpy.types.Panel):
    """Subpanel para la creación interactiva de posiciones de salida, boxes y cronometraje."""

    bl_label = "Nodos de Carrera (Assetto Corsa)"
    bl_idname = "TRACKMAKER_PT_race_nodes_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = BL_CATEGORY
    bl_parent_id = "TRACKMAKER_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        spawns_cfg = scene.track_maker_spawns
        timing_cfg = scene.track_maker_timing

        # ---------------------------------------------------------
        # 1. PARRILLA DE SALIDA (AC_START)
        # ---------------------------------------------------------
        box_grid = layout.box()
        box_grid.label(text="Parrilla de Salida (AC_START)", icon="AUTO")
        box_grid.prop(spawns_cfg, "grid_count")
        box_grid.prop(spawns_cfg, "grid_layout")

        col_grid_dist = box_grid.column(align=True)
        col_grid_dist.prop(spawns_cfg, "grid_row_spacing")
        if spawns_cfg.grid_layout in {"STAGGERED", "PARALLEL"}:
            col_grid_dist.prop(spawns_cfg, "grid_lateral_spacing")
        if spawns_cfg.grid_layout == "STAGGERED":
            col_grid_dist.prop(spawns_cfg, "grid_stagger_offset")

        row_grid_btn = box_grid.row(align=True)
        row_grid_btn.scale_y = 1.3
        row_grid_btn.operator(
            "track_maker.create_grid_starts",
            text="Generar Parrilla",
            icon="DUPLICATE",
        )

        # ---------------------------------------------------------
        # 2. PUESTOS DE BOXES (AC_PIT)
        # ---------------------------------------------------------
        box_pit = layout.box()
        box_pit.label(text="Puestos de Boxes (AC_PIT)", icon="TOOL_SETTINGS")
        box_pit.prop(spawns_cfg, "pit_count")
        box_pit.prop(spawns_cfg, "pit_spacing")

        row_pit_btn = box_pit.row(align=True)
        row_pit_btn.scale_y = 1.3
        row_pit_btn.operator(
            "track_maker.create_pit_boxes",
            text="Generar Boxes",
            icon="PRESET",
        )

        # ---------------------------------------------------------
        # 3. CONTRARRELOJ / HOTLAP (AC_HOTLAP_START_0)
        # ---------------------------------------------------------
        box_hl = layout.box()
        box_hl.label(text="Modo Contrarreloj (Hotlap)", icon="TIME")
        row_hl_btn = box_hl.row(align=True)
        row_hl_btn.scale_y = 1.2
        row_hl_btn.operator(
            "track_maker.create_hotlap_spawn",
            text="Crear Spawn Hotlap (Cursor 3D)",
            icon="PLAY",
        )

        # ---------------------------------------------------------
        # 4. PUERTAS DE CRONOMETRAJE (AC_TIME_*)
        # ---------------------------------------------------------
        box_timing = layout.box()
        box_timing.label(text="Puertas de Cronometraje", icon="SORTTIME")
        box_timing.prop(timing_cfg, "gate_type")
        box_timing.prop(timing_cfg, "gate_width")

        row_timing_btn = box_timing.row(align=True)
        row_timing_btn.scale_y = 1.3
        row_timing_btn.operator(
            "track_maker.create_timing_gate",
            text="Crear Puerta Seleccionada",
            icon="ADD",
        )

        # ---------------------------------------------------------
        # 5. LIMPIEZA
        # ---------------------------------------------------------
        box_clean = layout.box()
        box_clean.label(text="Mantenimiento", icon="TRASH")
        op_clean = box_clean.operator(
            "track_maker.clear_race_spawns",
            text="Limpiar Todos los Spawns",
            icon="X",
        )
        op_clean.target_type = "ALL"


classes = (TRACKMAKER_PT_RaceNodesPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

