"""Constantes globales y nomenclaturas técnicas para Assetto Corsa."""

# Versión del addon
ADDON_NAME = "Track Maker (Assetto Corsa Edition)"
BL_CATEGORY = "Track Maker"

# Nombres de Colecciones en el Outliner
COLLECTION_ROOT = "TrackMaker_Project"
COLLECTION_RACE_NODES = "TM_RaceNodes"
COLLECTION_ROAD_VISUAL = "TM_Road_Visual"
COLLECTION_ROAD_PHYSICS = "TM_Road_Physics"
COLLECTION_TERRAIN = "TM_Terrain"
COLLECTION_BARRIERS = "TM_Barriers"
COLLECTION_SIGNS = "TM_Signage"
COLLECTION_LIGHTING = "TM_Lighting"
COLLECTION_BUILDINGS = "TM_Buildings"
COLLECTION_PHOTOGRAMMETRY = "TM_Photogrammetry"

# Prefijos de Mallas Físicas de Assetto Corsa
PREFIX_PHYS_ROAD = "1ROAD_"
PREFIX_PHYS_ROAD_SECONDARY = "2ROAD_"
PREFIX_PHYS_KERB = "1KERB_"
PREFIX_PHYS_GRASS = "1GRASS_"
PREFIX_PHYS_SAND = "1SAND_"
PREFIX_PHYS_WALL = "1WALL_"
PREFIX_PHYS_PIT = "1PIT_"

# Nomenclaturas de Nodos de Carrera (Race Nodes)
PREFIX_START = "AC_START_"
PREFIX_PIT = "AC_PIT_"
NAME_HOTLAP_START = "AC_HOTLAP_START_0"

# Puertas de Cronometraje en Circuitos Cerrados
NAME_TIME_0_L = "AC_TIME_0_L"
NAME_TIME_0_R = "AC_TIME_0_R"
NAME_TIME_1_L = "AC_TIME_1_L"
NAME_TIME_1_R = "AC_TIME_1_R"
NAME_TIME_2_L = "AC_TIME_2_L"
NAME_TIME_2_R = "AC_TIME_2_R"

# Puertas de Cronometraje en Tramos A a B (Hillclimbs / Rally)
NAME_AB_START_L = "AC_AB_START_L"
NAME_AB_START_R = "AC_AB_START_R"
NAME_AB_FINISH_L = "AC_AB_FINISH_L"
NAME_AB_FINISH_R = "AC_AB_FINISH_R"

# Tipos de Elementos Internos (Agnósticos)
ELEMENT_ROAD_VISUAL = "ROAD_VISUAL"
ELEMENT_ROAD_PHYSICS = "ROAD_PHYSICS"
ELEMENT_KERB_VISUAL = "KERB_VISUAL"
ELEMENT_KERB_PHYSICS = "KERB_PHYSICS"
ELEMENT_WALL = "WALL"
ELEMENT_GRASS = "GRASS"
ELEMENT_SAND = "SAND"
ELEMENT_SPAWN_START = "SPAWN_START"
ELEMENT_SPAWN_PIT = "SPAWN_PIT"
ELEMENT_SPAWN_HOTLAP = "SPAWN_HOTLAP"
ELEMENT_TIMING_GATE = "TIMING_GATE"

# Valores por defecto para superficies físicas (surfaces.ini)
SURFACE_DEFAULTS = {
    "ROAD": {
        "FRICTION": 0.98,
        "DAMPING": 0.0,
        "WAV_PITCH": 0.0,
        "FF_EFFECT": "NULL",
        "DIRT_ADD": 0.0,
        "IS_VALID_TRACK": 1,
        "BLACK_FLAG_TIME": 0,
        "SIN_HEIGHT": 0.0,
        "SIN_LENGTH": 0.0,
        "IS_PITLANE": 0,
        "VIBRATION_GAIN": 0.0,
        "VIBRATION_LENGTH": 0.0,
    },
    "KERB": {
        "FRICTION": 0.92,
        "DAMPING": 0.0,
        "WAV_PITCH": 0.0,
        "FF_EFFECT": "NULL",
        "DIRT_ADD": 0.0,
        "IS_VALID_TRACK": 1,
        "BLACK_FLAG_TIME": 0,
        "SIN_HEIGHT": 0.005,
        "SIN_LENGTH": 0.15,
        "IS_PITLANE": 0,
        "VIBRATION_GAIN": 0.25,
        "VIBRATION_LENGTH": 0.20,
    },
    "GRASS": {
        "FRICTION": 0.55,
        "DAMPING": 0.1,
        "WAV_PITCH": 0.0,
        "FF_EFFECT": "NULL",
        "DIRT_ADD": 0.05,
        "IS_VALID_TRACK": 0,
        "BLACK_FLAG_TIME": 5,
        "SIN_HEIGHT": 0.03,
        "SIN_LENGTH": 0.5,
        "IS_PITLANE": 0,
        "VIBRATION_GAIN": 0.0,
        "VIBRATION_LENGTH": 0.0,
    },
    "SAND": {
        "FRICTION": 0.40,
        "DAMPING": 0.25,
        "WAV_PITCH": 0.0,
        "FF_EFFECT": "NULL",
        "DIRT_ADD": 0.10,
        "IS_VALID_TRACK": 0,
        "BLACK_FLAG_TIME": 10,
        "SIN_HEIGHT": 0.05,
        "SIN_LENGTH": 0.3,
        "IS_PITLANE": 0,
        "VIBRATION_GAIN": 0.0,
        "VIBRATION_LENGTH": 0.0,
    },
    "PIT": {
        "FRICTION": 0.95,
        "DAMPING": 0.0,
        "WAV_PITCH": 0.0,
        "FF_EFFECT": "NULL",
        "DIRT_ADD": 0.0,
        "IS_VALID_TRACK": 1,
        "BLACK_FLAG_TIME": 0,
        "SIN_HEIGHT": 0.0,
        "SIN_LENGTH": 0.0,
        "IS_PITLANE": 1,
        "VIBRATION_GAIN": 0.0,
        "VIBRATION_LENGTH": 0.0,
    },
    "WALL": {
        "FRICTION": 0.10,
        "DAMPING": 0.0,
        "WAV_PITCH": 0.0,
        "FF_EFFECT": "NULL",
        "DIRT_ADD": 0.0,
        "IS_VALID_TRACK": 0,
        "BLACK_FLAG_TIME": 0,
        "SIN_HEIGHT": 0.0,
        "SIN_LENGTH": 0.0,
        "IS_PITLANE": 0,
        "VIBRATION_GAIN": 0.0,
        "VIBRATION_LENGTH": 0.0,
    },
}
