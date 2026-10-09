"""Pipeline de exportación a Assetto Corsa y validación para ksEditor."""

import os
import subprocess
import bpy
from .validator import validate_scene_for_assetto_corsa
from .config_generator import create_track_mod_package
from ..core.constants import PREFIX_PHYS_ROAD


def estimate_track_length(scene: bpy.types.Scene) -> float:
    """Calcula la longitud del trazado a partir de la curva activa o las aristas de la malla física 1ROAD_."""
    # 1. Intentar calcular desde la curva de carretera
    for obj in scene.objects:
        if obj.type == "CURVE" and obj.name.startswith(("Spline", "TM_Road")):
            total_len = 0.0
            spline = obj.data.splines[0]
            pts = spline.bezier_points
            for i in range(len(pts) - 1):
                total_len += (pts[i + 1].co - pts[i].co).length
            if spline.use_cyclic_u and len(pts) > 2:
                total_len += (pts[0].co - pts[-1].co).length
            if total_len > 10.0:
                return total_len

    # 2. Intentar calcular desde la caja delimitadora de la malla física
    for obj in scene.objects:
        if obj.type == "MESH" and obj.name.startswith(PREFIX_PHYS_ROAD):
            bb = obj.dimensions
            diag = (bb.x ** 2 + bb.y ** 2) ** 0.5
            return max(500.0, diag * 3.14)

    return 3000.0


class TRACKMAKER_OT_ValidatePreflight(bpy.types.Operator):
    """Ejecuta la comprobación previa (Pre-flight) de requisitos obligatorios de Assetto Corsa."""

    bl_idname = "track_maker.validate_preflight"
    bl_label = "Comprobar Requisitos Pre-flight"
    bl_options = {"REGISTER"}

    def execute(self, context):
        report = validate_scene_for_assetto_corsa(context.scene)

        if report.errors:
            msg = f"Se detectaron {len(report.errors)} errores bloqueantes:\n" + "\n".join(
                [f"• {e.message}" for e in report.errors]
            )
            self.report({"ERROR"}, f"Validación FALLIDA ({len(report.errors)} errores). Ver consola.")
            print("\n[TRACK MAKER - PRE-FLIGHT ERROR REPORT]")
            print(msg)
            return {"CANCELLED"}

        if report.warnings:
            self.report(
                {"WARNING"},
                f"Validación superada con {len(report.warnings)} avisos recomendados.",
            )
        else:
            self.report({"INFO"}, "¡Escena 100% lista para Assetto Corsa! Todos los requisitos superados.")

        return {"FINISHED"}


class TRACKMAKER_OT_ExportAssettoCorsa(bpy.types.Operator):
    """Exporta el modelo FBX y genera la carpeta completa del mod de Assetto Corsa."""

    bl_idname = "track_maker.export_assetto_corsa"
    bl_label = "Exportar Mod para Assetto Corsa"
    bl_options = {"REGISTER"}

    force_export: bpy.props.BoolProperty(
        name="Ignorar Errores",
        description="Fuerza la exportación incluso si faltan requisitos obligatorios",
        default=False,
    )

    def execute(self, context):
        scene = context.scene
        circuit_cfg = scene.track_maker_circuit
        export_cfg = scene.track_maker_export

        # 1. Comprobación Pre-flight
        report = validate_scene_for_assetto_corsa(scene)
        if not report.is_valid and not self.force_export:
            error_summary = "; ".join([e.message for e in report.errors[:2]])
            self.report(
                {"ERROR"},
                f"Exportación cancelada por errores: {error_summary}. Corrige los fallos o activa 'Ignorar Errores'.",
            )
            return {"CANCELLED"}

        # 2. Resolver directorio de exportación
        raw_path = export_cfg.export_directory.strip()
        if raw_path.startswith("//"):
            blend_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else os.getcwd()
            resolved_base_dir = os.path.abspath(os.path.join(blend_dir, raw_path[2:]))
        else:
            resolved_base_dir = os.path.abspath(raw_path) if raw_path else os.path.join(os.getcwd(), "export")

        track_name = circuit_cfg.circuit_name.strip() or "Track_Custom"
        track_len = estimate_track_length(scene)
        pit_count = report.stats.get("pit_count", 24)

        # 3. Crear carpetas y archivos de configuración (surfaces.ini, models.ini, ui_track.json)
        if export_cfg.generate_configs:
            mod_dir = create_track_mod_package(
                base_export_dir=resolved_base_dir,
                track_name=track_name,
                author=circuit_cfg.author,
                country=circuit_cfg.country,
                city=circuit_cfg.city,
                length_m=track_len,
                width_m=scene.track_maker_road.road_width,
                pitboxes=pit_count,
                circuit_type=circuit_cfg.circuit_type,
            )
        else:
            mod_dir = os.path.join(resolved_base_dir, track_name)
            os.makedirs(mod_dir, exist_ok=True)

        # 4. Exportar el modelo 3D en formato FBX optimizado para ksEditor
        if export_cfg.export_fbx:
            fbx_path = os.path.join(mod_dir, f"{track_name}.fbx")

            # Seleccionar solo objetos exportables (nodos AC y mallas de pista)
            export_prefixes = ("AC_", "1ROAD_", "2ROAD_", "1WALL_", "1KERB_", "1GRASS_", "1SAND_", "ROAD_")
            export_objs = []

            for obj in scene.objects:
                if obj.name.startswith(export_prefixes) or (obj.type == "MESH" and obj.name.startswith("TM_")):
                    export_objs.append(obj)

            if not export_objs:
                self.report({"ERROR"}, "No se encontraron mallas ni nodos de carrera para exportar.")
                return {"CANCELLED"}

            # Deseleccionar todo y marcar solo los objetos de circuito
            bpy.ops.object.select_all(action="DESELECT")
            for obj in export_objs:
                obj.select_set(True)

            # Exportar FBX con ejes estándar de Kunos: -Z Forward, Y Up
            try:
                bpy.ops.export_scene.fbx(
                    filepath=fbx_path,
                    use_selection=True,
                    global_scale=1.0,
                    apply_unit_scale=True,
                    apply_scale_options="FBX_SCALE_ALL",
                    axis_forward="-Z",
                    axis_up="Y",
                    use_mesh_modifiers=export_cfg.apply_modifiers_on_export,
                    bake_anim=False,
                )
                self.report({"INFO"}, f"FBX exportado con éxito en: {fbx_path}")
            except Exception as e:
                self.report({"ERROR"}, f"Fallo al exportar FBX: {str(e)}")
                return {"CANCELLED"}

        # 5. Abrir carpeta al finalizar si está marcado
        if export_cfg.open_folder_after:
            try:
                bpy.ops.wm.path_open(filepath=mod_dir)
            except Exception:
                pass

        self.report(
            {"INFO"},
            f"¡Mod de Assetto Corsa empaquetado con éxito en '{mod_dir}'!",
        )
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_ValidatePreflight,
    TRACKMAKER_OT_ExportAssettoCorsa,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
