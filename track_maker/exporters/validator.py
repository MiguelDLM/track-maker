"""Validador Pre-flight para escenas de Assetto Corsa."""

import re
import bpy
from ..core.constants import (
    PREFIX_START,
    PREFIX_PIT,
    PREFIX_PHYS_ROAD,
    PREFIX_PHYS_WALL,
    PREFIX_PHYS_KERB,
    NAME_TIME_0_L,
    NAME_TIME_0_R,
    NAME_AB_START_L,
    NAME_AB_START_R,
    NAME_AB_FINISH_L,
    NAME_AB_FINISH_R,
    NAME_HOTLAP_START,
)


class ValidationIssue:
    """Representa una incidencia o comprobación en la escena."""

    def __init__(self, severity: str, category: str, message: str, obj_name: str = None):
        self.severity = severity  # 'ERROR' o 'WARNING'
        self.category = category  # 'RACE_NODES', 'PHYSICS', 'TRANSFORMS', 'CONFIG'
        self.message = message
        self.obj_name = obj_name

    def __repr__(self):
        return f"[{self.severity}] ({self.category}) {self.message}"


class ValidationReport:
    """Informe consolidado de la validación pre-flight."""

    def __init__(self):
        self.issues: list[ValidationIssue] = []
        self.stats: dict = {}

    @property
    def is_valid(self) -> bool:
        """True si no hay errores bloqueantes (los warnings son permitidos)."""
        return not any(i.severity == "ERROR" for i in self.issues)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "WARNING"]


def validate_scene_for_assetto_corsa(scene: bpy.types.Scene) -> ValidationReport:
    """Ejecuta una inspección completa de la escena para asegurar compatibilidad con Assetto Corsa."""
    report = ValidationReport()
    objects = scene.objects

    circuit_cfg = scene.track_maker_circuit
    circuit_name = circuit_cfg.circuit_name.strip()
    circuit_type = circuit_cfg.circuit_type

    # 1. VALIDACIÓN DE NOMBRE Y CONFIGURACIÓN
    if not circuit_name:
        report.issues.append(
            ValidationIssue("ERROR", "CONFIG", "El nombre del circuito no puede estar vacío.")
        )
    elif re.search(r'[\\/:*?"<>| ]', circuit_name):
        report.issues.append(
            ValidationIssue(
                "WARNING",
                "CONFIG",
                f"El nombre '{circuit_name}' contiene espacios o caracteres especiales. Se recomienda usar guiones bajos.",
            )
        )

    # 2. VALIDACIÓN DE NODOS DE SALIDA (AC_START)
    start_nodes = [obj for obj in objects if obj.name.startswith(PREFIX_START)]
    report.stats["start_count"] = len(start_nodes)

    has_pole = any(obj.name == f"{PREFIX_START}0" for obj in start_nodes)
    if not has_pole:
        report.issues.append(
            ValidationIssue(
                "ERROR",
                "RACE_NODES",
                f"Falta el nodo de salida principal '{PREFIX_START}0'. Assetto Corsa crasheará sin él.",
            )
        )
    elif len(start_nodes) < 2:
        report.issues.append(
            ValidationIssue(
                "WARNING",
                "RACE_NODES",
                f"Solo hay {len(start_nodes)} posición de salida. Se recomiendan al menos 12-24 coches.",
            )
        )

    # 3. VALIDACIÓN DE BOXES (AC_PIT)
    pit_nodes = [obj for obj in objects if obj.name.startswith(PREFIX_PIT)]
    report.stats["pit_count"] = len(pit_nodes)

    has_pit_0 = any(obj.name == f"{PREFIX_PIT}0" for obj in pit_nodes)
    if not has_pit_0:
        report.issues.append(
            ValidationIssue(
                "WARNING",
                "RACE_NODES",
                f"Falta el puesto de boxes '{PREFIX_PIT}0'. Modo fin de semana o carreras no funcionarán correctamente.",
            )
        )

    obj_names = {obj.name for obj in objects}

    # 4. VALIDACIÓN DE HOTLAP (AC_HOTLAP_START_0)
    has_hotlap = NAME_HOTLAP_START in obj_names
    report.stats["has_hotlap"] = has_hotlap
    if not has_hotlap:
        report.issues.append(
            ValidationIssue(
                "WARNING",
                "RACE_NODES",
                f"No se ha definido '{NAME_HOTLAP_START}'. El modo contrarreloj no podrá generar el coche en marcha.",
            )
        )

    # 5. VALIDACIÓN DE CRONOMETRAJE SEGÚN TIPO DE CIRCUITO
    if circuit_type == "CIRCUIT":
        has_t0_l = NAME_TIME_0_L in obj_names
        has_t0_r = NAME_TIME_0_R in obj_names
        if not (has_t0_l and has_t0_r):
            report.issues.append(
                ValidationIssue(
                    "ERROR",
                    "RACE_NODES",
                    f"Falta la puerta de meta obligatoria ({NAME_TIME_0_L} / {NAME_TIME_0_R}).",
                )
            )
    else:  # HILLCLIMB_AB
        has_ab_s = (NAME_AB_START_L in obj_names) and (NAME_AB_START_R in obj_names)
        has_ab_f = (NAME_AB_FINISH_L in obj_names) and (NAME_AB_FINISH_R in obj_names)
        if not has_ab_s:
            report.issues.append(
                ValidationIssue(
                    "ERROR",
                    "RACE_NODES",
                    f"Falta la puerta de salida de tramo ({NAME_AB_START_L} / {NAME_AB_START_R}).",
                )
            )
        if not has_ab_f:
            report.issues.append(
                ValidationIssue(
                    "ERROR",
                    "RACE_NODES",

                    f"Falta la puerta de meta de tramo ({NAME_AB_FINISH_L} / {NAME_AB_FINISH_R}).",
                )
            )

    # 6. VALIDACIÓN DE MALLAS FÍSICAS (1ROAD_)
    phys_roads = [
        obj for obj in objects
        if obj.type == "MESH" and (obj.name.startswith(PREFIX_PHYS_ROAD) or obj.name.startswith("2ROAD_"))
    ]
    report.stats["phys_road_count"] = len(phys_roads)

    if not phys_roads:
        report.issues.append(
            ValidationIssue(
                "ERROR",
                "PHYSICS",
                f"No se encontró ninguna malla física con prefijo '{PREFIX_PHYS_ROAD}'. Los coches caerán al vacío.",
            )
        )

    # 7. VALIDACIÓN DE ESCALAS UNITARIAS (1.0, 1.0, 1.0)
    unapplied_scale_objs = []
    for obj in objects:
        if obj.name.startswith(("AC_", "1ROAD_", "2ROAD_", "1WALL_", "1KERB_", "ROAD_")):
            s = obj.scale
            if abs(s.x - 1.0) > 0.001 or abs(s.y - 1.0) > 0.001 or abs(s.z - 1.0) > 0.001:
                unapplied_scale_objs.append(obj.name)

    if unapplied_scale_objs:
        sample_names = ", ".join(unapplied_scale_objs[:3])
        if len(unapplied_scale_objs) > 3:
            sample_names += f" (+{len(unapplied_scale_objs)-3} más)"
        report.issues.append(
            ValidationIssue(
                "WARNING",
                "TRANSFORMS",
                f"Hay objetos con escala sin aplicar ({sample_names}). Se recomienda aplicar escala (Ctrl+A > Scale) antes de exportar.",
            )
        )

    return report
