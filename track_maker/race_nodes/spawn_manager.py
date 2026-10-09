"""Operadores para la generación de posiciones de salida (AC_START) y boxes (AC_PIT)."""

import math
import bpy
from mathutils import Vector, Euler, Matrix
from ..core.constants import (
    PREFIX_START,
    PREFIX_PIT,
    NAME_HOTLAP_START,
    ELEMENT_SPAWN_START,
    ELEMENT_SPAWN_PIT,
    ELEMENT_SPAWN_HOTLAP,
)
from ..core.utils import create_ac_empty, remove_objects_by_prefix


class TRACKMAKER_OT_CreateGridStarts(bpy.types.Operator):
    """Genera la parrilla de salida completa (AC_START_0..N) con orientación y espaciado."""

    bl_idname = "track_maker.create_grid_starts"
    bl_label = "Generar Parrilla de Salida"
    bl_options = {"REGISTER", "UNDO"}

    clear_existing: bpy.props.BoolProperty(
        name="Limpiar Previos",
        description="Eliminar posiciones de salida existentes antes de generar las nuevas",
        default=True,
    )

    def execute(self, context):
        spawns_cfg = context.scene.track_maker_spawns

        if self.clear_existing:
            remove_objects_by_prefix(PREFIX_START)

        # Referencia de origen y orientación: el objeto activo o el cursor 3D
        active_obj = context.active_object
        if active_obj and active_obj.select_get():
            base_loc = active_obj.location.copy()
            base_rot = active_obj.rotation_euler.copy()
        else:
            base_loc = context.scene.cursor.location.copy()
            base_rot = context.scene.cursor.rotation_euler.copy()

        # Matriz de rotación base
        rot_matrix = base_rot.to_matrix().to_4x4()
        forward_dir = (rot_matrix @ Vector((0.0, 1.0, 0.0))).normalized()
        right_dir = (rot_matrix @ Vector((1.0, 0.0, 0.0))).normalized()
        up_dir = (rot_matrix @ Vector((0.0, 0.0, 1.0))).normalized()

        count = spawns_cfg.grid_count
        row_spacing = spawns_cfg.grid_row_spacing
        lat_spacing = spawns_cfg.grid_lateral_spacing
        stagger_offset = spawns_cfg.grid_stagger_offset
        layout = spawns_cfg.grid_layout

        created_objects = []

        for i in range(count):
            name = f"{PREFIX_START}{i}"

            if layout == "STAGGERED":
                row_index = i // 2
                is_right_side = (i % 2 == 0)

                # Desplazamiento lateral (-X / +X)
                side_sign = 1.0 if is_right_side else -1.0
                lateral_offset = (lat_spacing / 2.0) * side_sign

                # Desplazamiento hacia atrás (-Y respecto al frente)
                longitudinal_offset = -(row_index * row_spacing)
                if not is_right_side:
                    longitudinal_offset -= stagger_offset

            elif layout == "PARALLEL":
                row_index = i // 2
                is_right_side = (i % 2 == 0)
                side_sign = 1.0 if is_right_side else -1.0
                lateral_offset = (lat_spacing / 2.0) * side_sign
                longitudinal_offset = -(row_index * row_spacing)

            else:  # IN_LINE
                lateral_offset = 0.0
                longitudinal_offset = -(i * row_spacing)

            # Posición final calculada en el espacio mundo
            pos = (
                base_loc
                + (forward_dir * longitudinal_offset)
                + (right_dir * lateral_offset)
                + (up_dir * 0.15)  # Ligera elevación sobre el asfalto (15cm)
            )

            empty = create_ac_empty(
                name=name,
                location=pos,
                rotation_euler=base_rot,
                display_type="SINGLE_ARROW",
                display_size=2.0,
                element_type=ELEMENT_SPAWN_START,
            )
            created_objects.append(empty)

        self.report(
            {"INFO"},
            f"Parrilla generada con éxito: {len(created_objects)} posiciones ({PREFIX_START}0..{count-1})",
        )
        return {"FINISHED"}


class TRACKMAKER_OT_CreatePitBoxes(bpy.types.Operator):
    """Genera puestos de boxes (AC_PIT_0..N) a lo largo del pitlane."""

    bl_idname = "track_maker.create_pit_boxes"
    bl_label = "Generar Puestos de Boxes"
    bl_options = {"REGISTER", "UNDO"}

    clear_existing: bpy.props.BoolProperty(
        name="Limpiar Previos",
        description="Eliminar puestos de boxes existentes antes de generar los nuevos",
        default=True,
    )

    def execute(self, context):
        spawns_cfg = context.scene.track_maker_spawns

        if self.clear_existing:
            remove_objects_by_prefix(PREFIX_PIT)

        active_obj = context.active_object
        if active_obj and active_obj.select_get():
            base_loc = active_obj.location.copy()
            base_rot = active_obj.rotation_euler.copy()
        else:
            base_loc = context.scene.cursor.location.copy()
            base_rot = context.scene.cursor.rotation_euler.copy()

        rot_matrix = base_rot.to_matrix().to_4x4()
        forward_dir = (rot_matrix @ Vector((0.0, 1.0, 0.0))).normalized()
        up_dir = (rot_matrix @ Vector((0.0, 0.0, 1.0))).normalized()

        count = spawns_cfg.pit_count
        spacing = spawns_cfg.pit_spacing

        created_objects = []

        for i in range(count):
            name = f"{PREFIX_PIT}{i}"
            # Los boxes se generan hacia atrás a lo largo de la línea de pitlane
            pos = (
                base_loc
                + (forward_dir * (i * spacing))
                + (up_dir * 0.15)
            )

            empty = create_ac_empty(
                name=name,
                location=pos,
                rotation_euler=base_rot,
                display_type="SINGLE_ARROW",
                display_size=2.0,
                element_type=ELEMENT_SPAWN_PIT,
            )
            created_objects.append(empty)

        self.report(
            {"INFO"},
            f"Boxes generados con éxito: {len(created_objects)} puestos ({PREFIX_PIT}0..{count-1})",
        )
        return {"FINISHED"}


class TRACKMAKER_OT_CreateHotlapSpawn(bpy.types.Operator):
    """Crea el punto de salida contrarreloj lanzada (AC_HOTLAP_START_0)."""

    bl_idname = "track_maker.create_hotlap_spawn"
    bl_label = "Crear Spawn de Hotlap"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_obj = context.active_object
        if active_obj and active_obj.select_get():
            base_loc = active_obj.location.copy()
            base_rot = active_obj.rotation_euler.copy()
        else:
            base_loc = context.scene.cursor.location.copy()
            base_rot = context.scene.cursor.rotation_euler.copy()

        # Elevar ligeramente sobre el asfalto
        rot_matrix = base_rot.to_matrix().to_4x4()
        up_dir = (rot_matrix @ Vector((0.0, 0.0, 1.0))).normalized()
        pos = base_loc + (up_dir * 0.15)

        create_ac_empty(
            name=NAME_HOTLAP_START,
            location=pos,
            rotation_euler=base_rot,
            display_type="SINGLE_ARROW",
            display_size=3.0,
            element_type=ELEMENT_SPAWN_HOTLAP,
        )

        self.report({"INFO"}, f"Nodo '{NAME_HOTLAP_START}' creado correctamente.")
        return {"FINISHED"}


class TRACKMAKER_OT_ClearRaceSpawns(bpy.types.Operator):
    """Elimina todos los nodos de salida o boxes creados."""

    bl_idname = "track_maker.clear_race_spawns"
    bl_label = "Limpiar Spawns de Carrera"
    bl_options = {"REGISTER", "UNDO"}

    target_type: bpy.props.EnumProperty(
        name="Tipo a Eliminar",
        items=[
            ("STARTS", "Solo Parrilla (AC_START_*)", "Eliminar todas las posiciones de salida"),
            ("PITS", "Solo Boxes (AC_PIT_*)", "Eliminar todos los puestos de boxes"),
            ("ALL", "Todos los Spawns", "Eliminar starts, pits y hotlap"),
        ],
        default="ALL",
    )

    def execute(self, context):
        removed = 0
        if self.target_type in {"STARTS", "ALL"}:
            removed += remove_objects_by_prefix(PREFIX_START)
        if self.target_type in {"PITS", "ALL"}:
            removed += remove_objects_by_prefix(PREFIX_PIT)
        if self.target_type == "ALL":
            if NAME_HOTLAP_START in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[NAME_HOTLAP_START], do_unlink=True)
                removed += 1

        self.report({"INFO"}, f"Se eliminaron {removed} objetos de carrera.")
        return {"FINISHED"}


def auto_align_all_spawns_to_spline(context, curve_obj: bpy.types.Object = None) -> dict:
    """Alinea automáticamente todos los puntos de salida, boxes y hotlap al inicio de la carretera."""
    if curve_obj is None:
        active = context.active_object
        if active and active.type == "CURVE":
            curve_obj = active
        else:
            curve_obj = bpy.data.objects.get("Spline_Route_AB")
        if not curve_obj:
            for obj in bpy.data.objects:
                if obj.type == "CURVE" and obj.data.splines:
                    curve_obj = obj
                    break

    if not curve_obj or not curve_obj.data.splines:
        raise ValueError("No se encontró ningún spline de carretera para alinear los spawns.")

    spline = curve_obj.data.splines[0]
    mat_world = curve_obj.matrix_world

    if spline.type == "BEZIER":
        pts = spline.bezier_points
        if len(pts) < 2:
            raise ValueError("El spline requiere al menos 2 puntos.")
        p0 = mat_world @ pts[0].co
        p1 = mat_world @ pts[1].co
    else:
        pts = spline.points
        if len(pts) < 2:
            raise ValueError("El spline requiere al menos 2 puntos.")
        p0 = mat_world @ pts[0].co.to_3d()
        p1 = mat_world @ pts[1].co.to_3d()

    tan = (p1 - p0).to_2d()
    if tan.length == 0:
        tan = Vector((0.0, 1.0))
    else:
        tan = tan.normalized()

    forward = Vector((tan.x, tan.y, 0.0))
    right = Vector((-tan.y, tan.x, 0.0))
    up = Vector((0.0, 0.0, 1.0))

    yaw = math.atan2(tan.y, tan.x) - math.pi / 2.0
    rot = Euler((0.0, 0.0, yaw), "XYZ")

    spawns_cfg = getattr(context.scene, "track_maker_spawns", None)
    start_count = getattr(spawns_cfg, "grid_count", 24) if spawns_cfg else 24
    row_spacing = getattr(spawns_cfg, "grid_row_spacing", 8.0) if spawns_cfg else 8.0
    lat_spacing = getattr(spawns_cfg, "grid_lateral_spacing", 3.5) if spawns_cfg else 3.5
    stagger_offset = getattr(spawns_cfg, "grid_stagger_offset", 4.0) if spawns_cfg else 4.0
    layout = getattr(spawns_cfg, "grid_layout", "STAGGERED") if spawns_cfg else "STAGGERED"

    # 1. Eliminar spawns previos
    remove_objects_by_prefix(PREFIX_START)
    remove_objects_by_prefix(PREFIX_PIT)
    if NAME_HOTLAP_START in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[NAME_HOTLAP_START], do_unlink=True)

    # 2. Generar AC_START_0..N escalonados o en fila detrás de la salida
    created_starts = []
    base_start_offset = -12.0  # 12 metros detrás de la línea de salida

    for i in range(start_count):
        name = f"{PREFIX_START}{i}"
        if layout == "STAGGERED":
            row_idx = i // 2
            is_right = (i % 2 == 0)
            side_sign = 1.0 if is_right else -1.0
            lat_off = (lat_spacing / 2.0) * side_sign
            long_off = base_start_offset - (row_idx * row_spacing)
            if not is_right:
                long_off -= stagger_offset
        elif layout == "PARALLEL":
            row_idx = i // 2
            is_right = (i % 2 == 0)
            side_sign = 1.0 if is_right else -1.0
            lat_off = (lat_spacing / 2.0) * side_sign
            long_off = base_start_offset - (row_idx * row_spacing)
        else:  # IN_LINE
            lat_off = 0.0
            long_off = base_start_offset - (i * row_spacing)

        pos = p0 + (forward * long_off) + (right * lat_off) + (up * 0.18)
        empty = create_ac_empty(
            name=name,
            location=pos,
            rotation_euler=rot,
            display_type="SINGLE_ARROW",
            display_size=2.0,
            element_type=ELEMENT_SPAWN_START,
        )
        created_starts.append(empty)

    # 3. Generar AC_HOTLAP_START_0 (25m detrás de la salida en el carril central)
    hl_pos = p0 + (forward * -25.0) + (up * 0.18)
    hl_empty = create_ac_empty(
        name=NAME_HOTLAP_START,
        location=hl_pos,
        rotation_euler=rot,
        display_type="SINGLE_ARROW",
        display_size=2.5,
        element_type=ELEMENT_SPAWN_HOTLAP,
    )

    # 4. Generar AC_PIT_0..N (en el arcén antes de la parrilla)
    pit_count = getattr(spawns_cfg, "pit_count", 24) if spawns_cfg else 24
    pit_spacing = getattr(spawns_cfg, "pit_spacing", 10.0) if spawns_cfg else 10.0
    road_cfg = getattr(context.scene, "track_maker_road", None)
    road_w = getattr(road_cfg, "road_width", 9.0) if road_cfg else 9.0
    pit_lat_offset = (road_w / 2.0) + 2.5

    created_pits = []
    base_pit_offset = base_start_offset - (start_count * (row_spacing / 2.0)) - 10.0

    for i in range(pit_count):
        name = f"{PREFIX_PIT}{i}"
        pos = p0 + (forward * (base_pit_offset - (i * pit_spacing))) + (right * pit_lat_offset) + (up * 0.18)
        empty = create_ac_empty(
            name=name,
            location=pos,
            rotation_euler=rot,
            display_type="SINGLE_ARROW",
            display_size=1.8,
            element_type=ELEMENT_SPAWN_PIT,
        )
        created_pits.append(empty)

    return {
        "starts": created_starts,
        "pits": created_pits,
        "hotlap": hl_empty,
    }


class TRACKMAKER_OT_AlignSpawnsToSpline(bpy.types.Operator):
    """Alinea automáticamente todos los puntos de salida, boxes y hotlap al inicio del trazado activo."""

    bl_idname = "track_maker.align_spawns_to_spline"
    bl_label = "Alinear Spawns al Inicio del Trazado"
    bl_description = "Coloca automáticamente AC_START_0..N, AC_PIT_0..N y AC_HOTLAP sobre el asfalto al inicio de la carretera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            res = auto_align_all_spawns_to_spline(context)
            starts_len = len(res["starts"])
            pits_len = len(res["pits"])
            self.report(
                {"INFO"},
                f"🏁 Spawns alineados con éxito: {starts_len} salidas, {pits_len} boxes y Hotlap en cabecera.",
            )
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error alineando spawns: {e}")
            return {"CANCELLED"}


classes = (
    TRACKMAKER_OT_CreateGridStarts,
    TRACKMAKER_OT_CreatePitBoxes,
    TRACKMAKER_OT_CreateHotlapSpawn,
    TRACKMAKER_OT_ClearRaceSpawns,
    TRACKMAKER_OT_AlignSpawnsToSpline,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

