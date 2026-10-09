"""Operadores para la creación y alineación de puertas de cronometraje (AC_TIME y AC_AB)."""

import bpy
from mathutils import Vector
from ..core.constants import (
    NAME_TIME_0_L,
    NAME_TIME_0_R,
    NAME_TIME_1_L,
    NAME_TIME_1_R,
    NAME_TIME_2_L,
    NAME_TIME_2_R,
    NAME_AB_START_L,
    NAME_AB_START_R,
    NAME_AB_FINISH_L,
    NAME_AB_FINISH_R,
    ELEMENT_TIMING_GATE,
)
from ..core.utils import create_ac_empty


class TRACKMAKER_OT_CreateTimingGate(bpy.types.Operator):
    """Crea un par de postes de cronometraje (L y R) perpendiculares a la dirección de la pista."""

    bl_idname = "track_maker.create_timing_gate"
    bl_label = "Crear Puerta de Cronometraje"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        timing_cfg = context.scene.track_maker_timing
        gate_type = timing_cfg.gate_type
        width = timing_cfg.gate_width

        # Nombres de los nodos según el tipo
        names_map = {
            "FINISH": (NAME_TIME_0_L, NAME_TIME_0_R, "Línea de Meta (AC_TIME_0)"),
            "SPLIT_1": (NAME_TIME_1_L, NAME_TIME_1_R, "Sector 1 (AC_TIME_1)"),
            "SPLIT_2": (NAME_TIME_2_L, NAME_TIME_2_R, "Sector 2 (AC_TIME_2)"),
            "AB_START": (NAME_AB_START_L, NAME_AB_START_R, "Salida Tramo (AC_AB_START)"),
            "AB_FINISH": (NAME_AB_FINISH_L, NAME_AB_FINISH_R, "Meta Tramo (AC_AB_FINISH)"),
        }

        name_l, name_r, label_desc = names_map.get(gate_type)

        # Ubicación y orientación de referencia
        active_obj = context.active_object
        if active_obj and active_obj.select_get():
            center_loc = active_obj.location.copy()
            rot = active_obj.rotation_euler.copy()
        else:
            center_loc = context.scene.cursor.location.copy()
            rot = context.scene.cursor.rotation_euler.copy()

        rot_matrix = rot.to_matrix().to_4x4()
        right_dir = (rot_matrix @ Vector((1.0, 0.0, 0.0))).normalized()
        up_dir = (rot_matrix @ Vector((0.0, 0.0, 1.0))).normalized()

        half_width = width / 2.0

        # Posiciones izquierda y derecha
        pos_l = center_loc - (right_dir * half_width) + (up_dir * 0.5)
        pos_r = center_loc + (right_dir * half_width) + (up_dir * 0.5)

        # Crear Empties L y R
        empty_l = create_ac_empty(
            name=name_l,
            location=pos_l,
            rotation_euler=rot,
            display_type="SPHERE",
            display_size=1.0,
            element_type=ELEMENT_TIMING_GATE,
        )

        empty_r = create_ac_empty(
            name=name_r,
            location=pos_r,
            rotation_euler=rot,
            display_type="SPHERE",
            display_size=1.0,
            element_type=ELEMENT_TIMING_GATE,
        )

        self.report({"INFO"}, f"Puerta '{label_desc}' creada con éxito ({name_l} / {name_r}).")
        return {"FINISHED"}


class TRACKMAKER_OT_DeleteTimingGate(bpy.types.Operator):
    """Elimina la puerta de cronometraje seleccionada."""

    bl_idname = "track_maker.delete_timing_gate"
    bl_label = "Eliminar Puerta"
    bl_options = {"REGISTER", "UNDO"}

    gate_type: bpy.props.EnumProperty(
        name="Tipo de Puerta",
        items=[
            ("FINISH", "Meta (AC_TIME_0)", ""),
            ("SPLIT_1", "Sector 1 (AC_TIME_1)", ""),
            ("SPLIT_2", "Sector 2 (AC_TIME_2)", ""),
            ("AB_START", "Salida Tramo (AC_AB_START)", ""),
            ("AB_FINISH", "Meta Tramo (AC_AB_FINISH)", ""),
        ],
        default="FINISH",
    )

    def execute(self, context):
        pairs_map = {
            "FINISH": (NAME_TIME_0_L, NAME_TIME_0_R),
            "SPLIT_1": (NAME_TIME_1_L, NAME_TIME_1_R),
            "SPLIT_2": (NAME_TIME_2_L, NAME_TIME_2_R),
            "AB_START": (NAME_AB_START_L, NAME_AB_START_R),
            "AB_FINISH": (NAME_AB_FINISH_L, NAME_AB_FINISH_R),
        }

        names = pairs_map.get(self.gate_type, ())
        removed = 0
        for name in names:
            if name in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
                removed += 1

        self.report({"INFO"}, f"Se eliminaron {removed} nodos de la puerta {self.gate_type}.")
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_CreateTimingGate,
    TRACKMAKER_OT_DeleteTimingGate,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
