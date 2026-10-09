"""Generador de archivos de configuración obligatorios para Assetto Corsa (surfaces.ini, models.ini, ui_track.json)."""

import os
import json
from ..core.constants import SURFACE_DEFAULTS


def generate_surfaces_ini_content(custom_surfaces: dict = None) -> str:
    """Genera el contenido de texto para el archivo surfaces.ini según el estándar de Assetto Corsa."""
    surfaces = custom_surfaces or SURFACE_DEFAULTS
    lines = [
        "; surfaces.ini generado automáticamente por Track Maker",
        "; Define las propiedades físicas de fricción, baches y Force Feedback (FFB)",
        "",
    ]

    for idx, (surface_key, params) in enumerate(surfaces.items()):
        lines.append(f"[SURFACE_{idx}]")
        lines.append(f"KEY={params.get('KEY', surface_key)}")
        lines.append(f"FRICTION={params.get('FRICTION', 0.98):.2f}")
        lines.append(f"DAMPING={params.get('DAMPING', 0.0):.2f}")
        lines.append(f"WAV_PITCH={params.get('WAV_PITCH', 0.0):.2f}")
        lines.append(f"FF_EFFECT={params.get('FF_EFFECT', 'NULL')}")
        lines.append(f"DIRT_ADD={params.get('DIRT_ADD', 0.0):.2f}")
        lines.append(f"IS_VALID_TRACK={int(params.get('IS_VALID_TRACK', 1))}")
        lines.append(f"BLACK_FLAG_TIME={int(params.get('BLACK_FLAG_TIME', 0))}")
        lines.append(f"SIN_HEIGHT={params.get('SIN_HEIGHT', 0.0):.3f}")
        lines.append(f"SIN_LENGTH={params.get('SIN_LENGTH', 0.0):.2f}")
        lines.append(f"IS_PITLANE={int(params.get('IS_PITLANE', 0))}")
        lines.append(f"VIBRATION_GAIN={params.get('VIBRATION_GAIN', 0.0):.2f}")
        lines.append(f"VIBRATION_LENGTH={params.get('VIBRATION_LENGTH', 0.0):.2f}")
        lines.append("")

    return "\n".join(lines)


def generate_models_ini_content(track_name: str) -> str:
    """Genera el archivo models.ini que referencia el archivo .kn5 compilado del circuito."""
    clean_name = track_name.strip()
    return f"""[MODEL_0]
FILE={clean_name}.kn5
POSITION=0,0,0
ROTATION=0,0,0
"""


def generate_ui_track_json_data(
    name: str,
    author: str = "Track Maker",
    country: str = "México",
    city: str = "CDMX",
    length_m: float = 3500.0,
    width_m: float = 9.0,
    pitboxes: int = 24,
    circuit_type: str = "CIRCUIT",
) -> dict:
    """Genera la estructura de diccionario para ui/ui_track.json leída por Content Manager y AC."""
    length_str = f"{length_m:.0f} m" if length_m < 10000 else f"{length_m / 1000.0:.2f} km"
    type_tag = "circuit" if circuit_type == "CIRCUIT" else "hillclimb"

    data = {
        "name": name,
        "description": f"Trazado recreado con alta fidelidad métrica y física para Assetto Corsa.",
        "tags": [type_tag, "scratch", "lidar", "real", country.lower()],
        "geotags": [country, city],
        "country": country,
        "city": city,
        "length": length_str,
        "width": f"{width_m:.1f} m",
        "pitboxes": str(pitboxes),
        "run": "clockwise",
        "author": author,
        "version": "1.0",
        "url": "",
    }
    return data


def create_track_mod_package(
    base_export_dir: str,
    track_name: str,
    author: str,
    country: str,
    city: str,
    length_m: float = 3000.0,
    width_m: float = 9.0,
    pitboxes: int = 24,
    circuit_type: str = "CIRCUIT",
) -> str:
    """Crea la estructura física de carpetas y los archivos INI y JSON en el disco."""
    track_dir = os.path.join(base_export_dir, track_name)
    data_dir = os.path.join(track_dir, "data")
    ui_dir = os.path.join(track_dir, "ui")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(ui_dir, exist_ok=True)

    # 1. surfaces.ini (se guarda tanto en raíz como en data/ para máxima compatibilidad)
    surfaces_content = generate_surfaces_ini_content()
    with open(os.path.join(track_dir, "surfaces.ini"), "w", encoding="utf-8") as f:
        f.write(surfaces_content)
    with open(os.path.join(data_dir, "surfaces.ini"), "w", encoding="utf-8") as f:
        f.write(surfaces_content)

    # 2. models.ini
    models_content = generate_models_ini_content(track_name)
    with open(os.path.join(track_dir, "models.ini"), "w", encoding="utf-8") as f:
        f.write(models_content)

    # 3. ui/ui_track.json
    ui_data = generate_ui_track_json_data(
        name=track_name,
        author=author,
        country=country,
        city=city,
        length_m=length_m,
        width_m=width_m,
        pitboxes=pitboxes,
        circuit_type=circuit_type,
    )
    with open(os.path.join(ui_dir, "ui_track.json"), "w", encoding="utf-8") as f:
        json.dump(ui_data, f, indent=4, ensure_ascii=False)

    return track_dir
