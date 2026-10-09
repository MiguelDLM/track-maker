"""Panel principal de Track Maker en el Sidebar (N-Panel) de la vista 3D."""

import bpy
from ..core.constants import BL_CATEGORY
from ..core.utils import count_race_nodes


class TRACKMAKER_PT_MainPanel(bpy.types.Panel):
    """Panel principal que muestra la configuración del circuito y el estado de los nodos."""

    bl_label = "Track Maker (Assetto Corsa)"
    bl_idname = "TRACKMAKER_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = BL_CATEGORY

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        circuit_cfg = scene.track_maker_circuit

        # Sección de Configuración General
        box_meta = layout.box()
        box_meta.label(text="Configuración del Circuito", icon="WORLD")
        box_meta.prop(circuit_cfg, "circuit_name")
        box_meta.prop(circuit_cfg, "circuit_type")

        col_loc = box_meta.column(align=True)
        col_loc.prop(circuit_cfg, "author")
        col_loc.prop(circuit_cfg, "country")
        col_loc.prop(circuit_cfg, "city")

        # Sección de Diagnóstico Rápido de Nodos
        box_diag = layout.box()
        box_diag.label(text="Estado de Nodos en Escena", icon="CHECKLIST")

        nodes = count_race_nodes()

        # Parrilla
        row_start = box_diag.row()
        if nodes["start_count"] > 0:
            row_start.label(text=f"Parrilla: {nodes['start_count']} coches", icon="CHECKMARK")
        else:
            row_start.label(text="Parrilla: Sin definir", icon="ERROR")

        # Boxes
        row_pit = box_diag.row()
        if nodes["pit_count"] > 0:
            row_pit.label(text=f"Boxes: {nodes['pit_count']} puestos", icon="CHECKMARK")
        else:
            row_pit.label(text="Boxes: Sin definir", icon="ERROR")

        # Hotlap
        row_hl = box_diag.row()
        if nodes["has_hotlap"]:
            row_hl.label(text="Hotlap: Configurado", icon="CHECKMARK")
        else:
            row_hl.label(text="Hotlap: Sin definir", icon="INFO")

        # Cronometraje según el tipo de pista
        if circuit_cfg.circuit_type == "CIRCUIT":
            row_t0 = box_diag.row()
            if nodes["has_time_0"]:
                row_t0.label(text="Línea de Meta: OK", icon="CHECKMARK")
            else:
                row_t0.label(text="Línea de Meta: Falta AC_TIME_0", icon="ERROR")

            row_splits = box_diag.row()
            s1 = "S1: OK" if nodes["has_time_1"] else "S1: -"
            s2 = "S2: OK" if nodes["has_time_2"] else "S2: -"
            row_splits.label(text=f"Sectores: {s1} | {s2}", icon="SORTTIME")
        else:
            row_ab = box_diag.row()
            ab_s = "Salida: OK" if nodes["has_ab_start"] else "Salida: -"
            ab_f = "Meta: OK" if nodes["has_ab_finish"] else "Meta: -"
            row_ab.label(text=f"Tramo A-B: {ab_s} | {ab_f}", icon="TRACKING")


classes = (TRACKMAKER_PT_MainPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
