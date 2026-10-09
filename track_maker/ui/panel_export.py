"""Panel de validación y exportación de mods para Assetto Corsa en el Sidebar de Blender."""

import bpy
from ..core.constants import BL_CATEGORY
from ..exporters.validator import validate_scene_for_assetto_corsa


class TRACKMAKER_PT_ExportPanel(bpy.types.Panel):
    """Subpanel para comprobaciones pre-flight y exportación automática a Assetto Corsa."""

    bl_label = "Exportación y Empaquetado (Assetto Corsa)"
    bl_idname = "TRACKMAKER_PT_export_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = BL_CATEGORY
    bl_parent_id = "TRACKMAKER_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        export_cfg = scene.track_maker_export

        # ---------------------------------------------------------
        # 1. CONFIGURACIÓN DE DESTINO
        # ---------------------------------------------------------
        box_dest = layout.box()
        box_dest.label(text="Carpeta de Salida del Mod", icon="FILE_FOLDER")
        box_dest.prop(export_cfg, "export_directory", text="")

        col_opts = box_dest.column(align=True)
        col_opts.prop(export_cfg, "export_fbx")
        col_opts.prop(export_cfg, "generate_configs")
        col_opts.prop(export_cfg, "apply_modifiers_on_export")
        col_opts.prop(export_cfg, "open_folder_after")

        # ---------------------------------------------------------
        # 2. VALIDACIÓN PRE-FLIGHT
        # ---------------------------------------------------------
        box_val = layout.box()
        box_val.label(text="Comprobación Pre-flight", icon="CHECKBOX_HLT")

        report = validate_scene_for_assetto_corsa(scene)

        if report.is_valid:
            box_val.label(text="Estado: Apto para exportar", icon="CHECKMARK")
            if report.warnings:
                box_val.label(text=f"{len(report.warnings)} avisos no bloqueantes", icon="INFO")
        else:
            box_val.label(text=f"Errores Bloqueantes: {len(report.errors)}", icon="CANCEL")
            for err in report.errors[:3]:
                box_val.label(text=f"• {err.message}", icon="ERROR")

        row_check = box_val.row(align=True)
        row_check.operator("track_maker.validate_preflight", text="Inspeccionar Escena", icon="VIEWZOOM")

        # ---------------------------------------------------------
        # 3. ACCIÓN DE EXPORTACIÓN
        # ---------------------------------------------------------
        row_exp = layout.row(align=True)
        row_exp.scale_y = 1.6
        row_exp.operator(
            "track_maker.export_assetto_corsa",
            text="Exportar Mod para Assetto Corsa",
            icon="EXPORT",
        )


classes = (TRACKMAKER_PT_ExportPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

