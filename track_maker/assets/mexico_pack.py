"""Biblioteca de Assets Procedurales 'Mexico-Pack' para Carreteras y Autopistas de Assetto Corsa.

Incluye elementos auténticos de la infraestructura vial y urbana mexicana:
- Barreras de concreto New Jersey (camellón central con vialetas reflectivas).
- Barreras de contención metálicas SCT (Armco W-Beam con terminal amortiguador).
- Malla ciclónica perimetral con alambre de púas (zona aeroportuaria/baldíos).
- Señalética oficial SCT: Pórticos superiores con destinos reales (Guadalajara, Aeropuerto, Chapala),
  señales reglamentarias de velocidad máxima y señales preventivas de curva.
- Luminarias de autopista de doble brazo y postes de concreto CFE con transformador.
- Edificios icónicos de carretera: Tienda OXXO, Gasolinera con marquesina, Nave industrial
  y Casa autoconstruida mexicana con tinaco Rotoplas en la azotea y varillas expuestas.
"""

from __future__ import annotations
import math
import bpy
import bmesh
from mathutils import Vector, Matrix


# =============================================================================
# GESTIÓN DE MATERIALES PROCEDURALES MEXICANOS
# =============================================================================

def get_or_create_mexican_material(
    name: str,
    base_color: tuple[float, float, float, float],
    roughness: float = 0.5,
    metallic: float = 0.0,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    """Obtiene o crea un material PBR calibrado para Assetto Corsa y Blender."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")

    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = base_color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
        if emission_color and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission_strength

    return mat


def setup_mexico_materials() -> dict[str, bpy.types.Material]:
    """Inicializa la paleta oficial de materiales mexicanos."""
    return {
        "concrete_jersey": get_or_create_mexican_material("MAT_TM_Concrete_Jersey", (0.58, 0.57, 0.54, 1.0), roughness=0.85),
        "galvanized_steel": get_or_create_mexican_material("MAT_TM_Metal_Galvanized", (0.65, 0.67, 0.70, 1.0), roughness=0.35, metallic=0.85),
        "yellow_reflector": get_or_create_mexican_material("MAT_TM_Reflector_Yellow", (1.0, 0.75, 0.0, 1.0), roughness=0.2, emission_color=(1.0, 0.75, 0.0, 1.0), emission_strength=1.5),
        "white_reflector": get_or_create_mexican_material("MAT_TM_Reflector_White", (0.95, 0.95, 0.95, 1.0), roughness=0.2, emission_color=(1.0, 1.0, 1.0, 1.0), emission_strength=1.5),
        "sct_green": get_or_create_mexican_material("MAT_TM_Sign_Green_SCT", (0.0, 0.28, 0.15, 1.0), roughness=0.4),
        "sct_yellow": get_or_create_mexican_material("MAT_TM_Sign_Yellow_SCT", (0.95, 0.68, 0.05, 1.0), roughness=0.4),
        "sct_white": get_or_create_mexican_material("MAT_TM_Sign_White", (0.90, 0.90, 0.90, 1.0), roughness=0.4),
        "sct_red": get_or_create_mexican_material("MAT_TM_Sign_Red", (0.80, 0.05, 0.05, 1.0), roughness=0.4),
        "sct_black": get_or_create_mexican_material("MAT_TM_Sign_Black", (0.05, 0.05, 0.05, 1.0), roughness=0.6),
        "oxxo_red": get_or_create_mexican_material("MAT_TM_Oxxo_Red", (0.85, 0.08, 0.08, 1.0), roughness=0.3),
        "oxxo_yellow": get_or_create_mexican_material("MAT_TM_Oxxo_Yellow", (0.98, 0.80, 0.05, 1.0), roughness=0.3),
        "pemex_green": get_or_create_mexican_material("MAT_TM_Pemex_Green", (0.02, 0.45, 0.22, 1.0), roughness=0.3),
        "rotoplas_black": get_or_create_mexican_material("MAT_TM_Rotoplas_Black", (0.08, 0.08, 0.09, 1.0), roughness=0.55),
        "mexican_brick": get_or_create_mexican_material("MAT_TM_Brick_Mexican", (0.72, 0.35, 0.25, 1.0), roughness=0.9),
        "industrial_sheet": get_or_create_mexican_material("MAT_TM_Industrial_Sheet", (0.75, 0.77, 0.80, 1.0), roughness=0.4, metallic=0.7),
        "cfe_concrete": get_or_create_mexican_material("MAT_TM_CFE_Concrete", (0.50, 0.50, 0.48, 1.0), roughness=0.9),
        "asphalt_ground": get_or_create_mexican_material("MAT_TM_Asphalt_Ground", (0.15, 0.15, 0.16, 1.0), roughness=0.85),
    }


# =============================================================================
# 1. BARRERAS Y CONTENCIONES
# =============================================================================

def build_new_jersey_barrier_mesh(length: float = 3.0, height: float = 0.85) -> bpy.types.Mesh:
    """Genera la malla clásica del muro central de concreto New Jersey con vialeta reflectiva."""
    mesh_name = f"Mesh_Barrier_NewJersey_{int(length)}m"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    # Perfil transversal New Jersey estándar (eje X e Y, extruido en Y):
    # Base ancha (0.60m) -> Chaflán vertical (0.075m) -> Pendiente inferior -> Pendiente superior -> Coronamiento (0.20m)
    profile = [
        (-0.30, 0.00),
        (-0.30, 0.08),
        (-0.20, 0.26),
        (-0.10, height),
        ( 0.10, height),
        ( 0.20, 0.26),
        ( 0.30, 0.08),
        ( 0.30, 0.00),
    ]

    # Crear vértices en extremos Y = 0 y Y = length
    verts_start = [bm.verts.new(Vector((x, 0.0, z))) for x, z in profile]
    verts_end = [bm.verts.new(Vector((x, length, z))) for x, z in profile]

    # Caras laterales longitudinales
    n = len(profile)
    for i in range(n - 1):
        v0 = verts_start[i]
        v1 = verts_start[i + 1]
        v2 = verts_end[i + 1]
        v3 = verts_end[i]
        face = bm.faces.new([v0, v1, v2, v3])
        face.material_index = 0

    # Tapas en los extremos
    bm.faces.new(verts_start)
    bm.faces.new(list(reversed(verts_end)))

    # Base inferior
    bm.faces.new([verts_start[0], verts_end[0], verts_end[-1], verts_start[-1]])

    # Agregar "Vialeta" reflectiva trapezoidal en la cresta central
    v_sz = 0.06
    v_h = 0.02
    v_y = length / 2.0
    v_verts = [
        bm.verts.new(Vector((-v_sz, v_y - v_sz, height))),
        bm.verts.new(Vector(( v_sz, v_y - v_sz, height))),
        bm.verts.new(Vector(( v_sz, v_y + v_sz, height))),
        bm.verts.new(Vector((-v_sz, v_y + v_sz, height))),
        bm.verts.new(Vector((-v_sz * 0.7, v_y - v_sz * 0.7, height + v_h))),
        bm.verts.new(Vector(( v_sz * 0.7, v_y - v_sz * 0.7, height + v_h))),
        bm.verts.new(Vector(( v_sz * 0.7, v_y + v_sz * 0.7, height + v_h))),
        bm.verts.new(Vector((-v_sz * 0.7, v_y + v_sz * 0.7, height + v_h))),
    ]
    # Caras de la vialeta
    top_f = bm.faces.new(v_verts[4:8])
    top_f.material_index = 1
    for i in range(4):
        next_i = (i + 1) % 4
        f = bm.faces.new([v_verts[i], v_verts[next_i], v_verts[next_i + 4], v_verts[i + 4]])
        f.material_index = 1

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["concrete_jersey"])
    mesh.materials.append(mats["yellow_reflector"])
    return mesh


def build_armco_barrier_mesh(length: float = 4.0, height: float = 0.75) -> bpy.types.Mesh:
    """Genera la barrera metálica galvanizada SCT con perfil W y postes en H."""
    mesh_name = f"Mesh_Barrier_Armco_{int(length)}m"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    # Perfil W-Beam (ondulado)
    # y va a lo largo de length, X es transversal, Z es altura
    beam_w_profile = [
        (-0.02, 0.40),
        ( 0.05, 0.48),
        (-0.02, 0.58),
        ( 0.05, 0.67),
        (-0.02, 0.75),
    ]

    # Riel longitudinal
    r_start = [bm.verts.new(Vector((x, 0.0, z))) for x, z in beam_w_profile]
    r_end = [bm.verts.new(Vector((x, length, z))) for x, z in beam_w_profile]

    for i in range(len(beam_w_profile) - 1):
        f = bm.faces.new([r_start[i], r_start[i + 1], r_end[i + 1], r_end[i]])
        f.material_index = 0

    # Postes en H cada 2.0 metros
    post_positions = [0.2, length / 2.0, length - 0.2]
    for py in post_positions:
        pw = 0.05
        pd = 0.08
        pz = height
        p_verts = [
            bm.verts.new(Vector((-pw - 0.05, py - pd, 0.0))),
            bm.verts.new(Vector((-0.05, py - pd, 0.0))),
            bm.verts.new(Vector((-0.05, py + pd, 0.0))),
            bm.verts.new(Vector((-pw - 0.05, py + pd, 0.0))),
            bm.verts.new(Vector((-pw - 0.05, py - pd, pz))),
            bm.verts.new(Vector((-0.05, py - pd, pz))),
            bm.verts.new(Vector((-0.05, py + pd, pz))),
            bm.verts.new(Vector((-pw - 0.05, py + pd, pz))),
        ]
        # Caras del poste
        for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]:
            pf = bm.faces.new([p_verts[i] for i in idxs])
            pf.material_index = 0

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["galvanized_steel"])
    return mesh


# =============================================================================
# 2. SEÑALÉTICA VIAL MEXICANA (NORMA SCT)
# =============================================================================

def build_sct_gantry_mesh(
    span_width: float = 14.0,
    clearance: float = 5.8,
    dest_left: str = "GUADALAJARA CENTRO",
    dest_right: str = "AEROPUERTO / CHAPALA",
) -> bpy.types.Mesh:
    """Genera un pórtico monumental verde SCT que cruza la autopista con letreros informativos."""
    mesh_name = f"Mesh_Gantry_SCT_{int(span_width)}m"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    truss_r = 0.15
    tot_h = clearance + 2.2
    hw = span_width / 2.0

    # Columnas laterales izquierda (-hw) y derecha (+hw)
    for col_x in (-hw, hw):
        c_verts = [
            bm.verts.new(Vector((col_x - truss_r, -truss_r, 0.0))),
            bm.verts.new(Vector((col_x + truss_r, -truss_r, 0.0))),
            bm.verts.new(Vector((col_x + truss_r,  truss_r, 0.0))),
            bm.verts.new(Vector((col_x - truss_r,  truss_r, 0.0))),
            bm.verts.new(Vector((col_x - truss_r, -truss_r, tot_h))),
            bm.verts.new(Vector((col_x + truss_r, -truss_r, tot_h))),
            bm.verts.new(Vector((col_x + truss_r,  truss_r, tot_h))),
            bm.verts.new(Vector((col_x - truss_r,  truss_r, tot_h))),
        ]
        for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]:
            f = bm.faces.new([c_verts[i] for i in idxs])
            f.material_index = 0

    # Viga transversal superior
    b_verts = [
        bm.verts.new(Vector((-hw, -truss_r, tot_h - 0.4))),
        bm.verts.new(Vector(( hw, -truss_r, tot_h - 0.4))),
        bm.verts.new(Vector(( hw,  truss_r, tot_h - 0.4))),
        bm.verts.new(Vector((-hw,  truss_r, tot_h - 0.4))),
        bm.verts.new(Vector((-hw, -truss_r, tot_h))),
        bm.verts.new(Vector(( hw, -truss_r, tot_h))),
        bm.verts.new(Vector(( hw,  truss_r, tot_h))),
        bm.verts.new(Vector((-hw,  truss_r, tot_h))),
    ]
    for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (0, 1, 2, 3), (4, 5, 6, 7)]:
        f = bm.faces.new([b_verts[i] for i in idxs])
        f.material_index = 0

    # Dos tableros verdes SCT suspendidos (Izquierdo y Derecho)
    panel_w = span_width * 0.38
    panel_h = 1.6
    panel_z = clearance + 0.3

    for px_center in (-span_width * 0.22, span_width * 0.22):
        p_min_x = px_center - panel_w / 2.0
        p_max_x = px_center + panel_w / 2.0
        p_verts = [
            bm.verts.new(Vector((p_min_x, -truss_r - 0.05, panel_z))),
            bm.verts.new(Vector((p_max_x, -truss_r - 0.05, panel_z))),
            bm.verts.new(Vector((p_max_x, -truss_r - 0.02, panel_z))),
            bm.verts.new(Vector((p_min_x, -truss_r - 0.02, panel_z))),
            bm.verts.new(Vector((p_min_x, -truss_r - 0.05, panel_z + panel_h))),
            bm.verts.new(Vector((p_max_x, -truss_r - 0.05, panel_z + panel_h))),
            bm.verts.new(Vector((p_max_x, -truss_r - 0.02, panel_z + panel_h))),
            bm.verts.new(Vector((p_min_x, -truss_r - 0.02, panel_z + panel_h))),
        ]
        # Cara frontal verde SCT
        front_f = bm.faces.new([p_verts[0], p_verts[1], p_verts[5], p_verts[4]])
        front_f.material_index = 1
        # Borde y reverso en gris galvanizado
        for idxs in [(1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (0, 1, 2, 3)]:
            f = bm.faces.new([p_verts[i] for i in idxs])
            f.material_index = 0

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["galvanized_steel"])
    mesh.materials.append(mats["sct_green"])
    return mesh


def build_sct_speed_sign_mesh(speed_limit: int = 80) -> bpy.types.Mesh:
    """Genera una señal reglamentaria circular mexicana de límite de velocidad."""
    mesh_name = f"Mesh_Sign_Speed_{speed_limit}"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    # Poste tubular metálico
    post_h = 2.4
    p_r = 0.04
    p_verts = [
        bm.verts.new(Vector((-p_r, -p_r, 0.0))),
        bm.verts.new(Vector(( p_r, -p_r, 0.0))),
        bm.verts.new(Vector(( p_r,  p_r, 0.0))),
        bm.verts.new(Vector((-p_r,  p_r, 0.0))),
        bm.verts.new(Vector((-p_r, -p_r, post_h))),
        bm.verts.new(Vector(( p_r, -p_r, post_h))),
        bm.verts.new(Vector(( p_r,  p_r, post_h))),
        bm.verts.new(Vector((-p_r,  p_r, post_h))),
    ]
    for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        f = bm.faces.new([p_verts[i] for i in idxs])
        f.material_index = 0

    # Disco circular blanco con aro rojo (16 lados)
    disc_radius = 0.42
    disc_z = post_h - 0.1
    segs = 16
    outer_verts = []
    inner_ring_verts = []
    center_v = bm.verts.new(Vector((0.0, -0.05, disc_z)))

    for i in range(segs):
        ang = (2.0 * math.pi * i) / segs
        x = disc_radius * math.cos(ang)
        z = disc_z + disc_radius * math.sin(ang)
        outer_verts.append(bm.verts.new(Vector((x, -0.05, z))))
        # Aro rojo interior
        ix = disc_radius * 0.75 * math.cos(ang)
        iz = disc_z + disc_radius * 0.75 * math.sin(ang)
        inner_ring_verts.append(bm.verts.new(Vector((ix, -0.05, iz))))

    # Caras del aro rojo exterior
    for i in range(segs):
        next_i = (i + 1) % segs
        f = bm.faces.new([outer_verts[i], outer_verts[next_i], inner_ring_verts[next_i], inner_ring_verts[i]])
        f.material_index = 1  # sct_red

    # Caras del centro blanco
    for i in range(segs):
        next_i = (i + 1) % segs
        f = bm.faces.new([inner_ring_verts[i], inner_ring_verts[next_i], center_v])
        f.material_index = 2  # sct_white

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["galvanized_steel"])
    mesh.materials.append(mats["sct_red"])
    mesh.materials.append(mats["sct_white"])
    return mesh


# =============================================================================
# 3. LUMINARIAS Y POSTES DE INFRAESTRUCTURA
# =============================================================================

def build_highway_lighting_mesh(height: float = 10.0, is_double: bool = True) -> bpy.types.Mesh:
    """Genera una luminaria moderna de autopista de acero con brazo(s) para camellón."""
    mesh_name = f"Mesh_Highway_Light_{int(height)}m_{'Double' if is_double else 'Single'}"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    # Mástil cónico octogonal
    bot_r = 0.16
    top_r = 0.08
    segs = 8
    bot_v = []
    top_v = []

    for i in range(segs):
        ang = (2.0 * math.pi * i) / segs
        bx = bot_r * math.cos(ang)
        by = bot_r * math.sin(ang)
        bot_v.append(bm.verts.new(Vector((bx, by, 0.0))))

        tx = top_r * math.cos(ang)
        ty = top_r * math.sin(ang)
        top_v.append(bm.verts.new(Vector((tx, ty, height))))

    for i in range(segs):
        next_i = (i + 1) % segs
        f = bm.faces.new([bot_v[i], bot_v[next_i], top_v[next_i], top_v[i]])
        f.material_index = 0

    # Brazos curvos (eje X hacia derecha e izquierda)
    arms = [-1.0, 1.0] if is_double else [1.0]
    for side in arms:
        arm_reach = 2.4 * side
        arm_tip_z = height + 1.2

        # Lámpara LED
        lamp_w = 0.25
        lamp_l = 0.60
        lx = arm_reach
        lamp_verts = [
            bm.verts.new(Vector((lx - lamp_w * 0.5, -lamp_l * 0.5, arm_tip_z))),
            bm.verts.new(Vector((lx + lamp_w * 0.5, -lamp_l * 0.5, arm_tip_z))),
            bm.verts.new(Vector((lx + lamp_w * 0.5,  lamp_l * 0.5, arm_tip_z))),
            bm.verts.new(Vector((lx - lamp_w * 0.5,  lamp_l * 0.5, arm_tip_z))),
            bm.verts.new(Vector((lx - lamp_w * 0.5, -lamp_l * 0.5, arm_tip_z + 0.15))),
            bm.verts.new(Vector((lx + lamp_w * 0.5, -lamp_l * 0.5, arm_tip_z + 0.15))),
            bm.verts.new(Vector((lx + lamp_w * 0.5,  lamp_l * 0.5, arm_tip_z + 0.15))),
            bm.verts.new(Vector((lx - lamp_w * 0.5,  lamp_l * 0.5, arm_tip_z + 0.15))),
        ]
        # Cara emisora inferior
        bottom_f = bm.faces.new([lamp_verts[0], lamp_verts[1], lamp_verts[2], lamp_verts[3]])
        bottom_f.material_index = 1  # white_reflector / led emission

        for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]:
            f = bm.faces.new([lamp_verts[i] for i in idxs])
            f.material_index = 0

        # Tubo del brazo
        bm.faces.new([
            top_v[0 if side > 0 else 4],
            top_v[1 if side > 0 else 5],
            lamp_verts[5],
            lamp_verts[4],
        ]).material_index = 0

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["galvanized_steel"])
    mesh.materials.append(mats["white_reflector"])
    return mesh


# =============================================================================
# 4. EDIFICIOS EMBLEMÁTICOS DE CARRETERA (MEXICO PACK)
# =============================================================================

def build_oxxo_store_mesh(width: float = 12.0, depth: float = 9.0, height: float = 4.2) -> bpy.types.Mesh:
    """Genera la tienda de conveniencia OXXO con marquesina roja/amarilla y estacionamiento frontal."""
    mesh_name = "Mesh_Building_Oxxo_Store"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    hw = width / 2.0
    hd = depth / 2.0

    # Bloque principal del edificio
    b_verts = [
        bm.verts.new(Vector((-hw, -hd, 0.0))),
        bm.verts.new(Vector(( hw, -hd, 0.0))),
        bm.verts.new(Vector(( hw,  hd, 0.0))),
        bm.verts.new(Vector((-hw,  hd, 0.0))),
        bm.verts.new(Vector((-hw, -hd, height))),
        bm.verts.new(Vector(( hw, -hd, height))),
        bm.verts.new(Vector(( hw,  hd, height))),
        bm.verts.new(Vector((-hw,  hd, height))),
    ]
    # Caras laterales y techo
    for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]:
        f = bm.faces.new([b_verts[i] for i in idxs])
        f.material_index = 0  # concreto claro

    # Marquesina OXXO frontal en la fachada (Y = -hd)
    # Franja roja superior (0.8m alto) y franja amarilla inferior (0.4m alto)
    canopy_h = 1.2
    canopy_d = 1.0
    canopy_z = height - 0.2

    c_verts = [
        bm.verts.new(Vector((-hw - 0.2, -hd - canopy_d, canopy_z - canopy_h))),
        bm.verts.new(Vector(( hw + 0.2, -hd - canopy_d, canopy_z - canopy_h))),
        bm.verts.new(Vector(( hw + 0.2, -hd, canopy_z - canopy_h))),
        bm.verts.new(Vector((-hw - 0.2, -hd, canopy_z - canopy_h))),
        bm.verts.new(Vector((-hw - 0.2, -hd - canopy_d, canopy_z))),
        bm.verts.new(Vector(( hw + 0.2, -hd - canopy_d, canopy_z))),
        bm.verts.new(Vector(( hw + 0.2, -hd, canopy_z))),
        bm.verts.new(Vector((-hw - 0.2, -hd, canopy_z))),
    ]
    # Cara frontal de la marquesina (rojo Oxxo)
    front_canopy = bm.faces.new([c_verts[0], c_verts[1], c_verts[5], c_verts[4]])
    front_canopy.material_index = 1  # oxxo_red

    # Fondo amarillo Oxxo
    bot_canopy = bm.faces.new([c_verts[0], c_verts[1], c_verts[2], c_verts[3]])
    bot_canopy.material_index = 2  # oxxo_yellow

    for idxs in [(1, 2, 6, 5), (3, 0, 4, 7), (4, 5, 6, 7)]:
        f = bm.faces.new([c_verts[i] for i in idxs])
        f.material_index = 1

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["cfe_concrete"])
    mesh.materials.append(mats["oxxo_red"])
    mesh.materials.append(mats["oxxo_yellow"])
    return mesh


def build_gas_station_mesh(width: float = 20.0, depth: float = 14.0, clearance: float = 5.2) -> bpy.types.Mesh:
    """Genera una gasolinera mexicana (tipo Pemex/OXXO Gas) con marquesina, bombas e islas de repostaje."""
    mesh_name = "Mesh_Building_Gas_Station"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    hw = width / 2.0
    hd = depth / 2.0
    roof_h = 1.0

    # Gran cubierta superior (Marquesina)
    c_verts = [
        bm.verts.new(Vector((-hw, -hd, clearance))),
        bm.verts.new(Vector(( hw, -hd, clearance))),
        bm.verts.new(Vector(( hw,  hd, clearance))),
        bm.verts.new(Vector((-hw,  hd, clearance))),
        bm.verts.new(Vector((-hw, -hd, clearance + roof_h))),
        bm.verts.new(Vector(( hw, -hd, clearance + roof_h))),
        bm.verts.new(Vector(( hw,  hd, clearance + roof_h))),
        bm.verts.new(Vector((-hw,  hd, clearance + roof_h))),
    ]
    # Caras de la marquesina con franja verde Pemex
    for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        f = bm.faces.new([c_verts[i] for i in idxs])
        f.material_index = 0  # pemex_green

    bm.faces.new([c_verts[0], c_verts[1], c_verts[2], c_verts[3]]).material_index = 1  # blanco plafón
    bm.faces.new([c_verts[4], c_verts[5], c_verts[6], c_verts[7]]).material_index = 2  # lámina industrial

    # 4 Columnas de soporte
    col_x_offsets = [-hw * 0.5, hw * 0.5]
    col_y_offsets = [-hd * 0.4, hd * 0.4]

    for cx in col_x_offsets:
        for cy in col_y_offsets:
            cr = 0.35
            p_v = [
                bm.verts.new(Vector((cx - cr, cy - cr, 0.0))),
                bm.verts.new(Vector((cx + cr, cy - cr, 0.0))),
                bm.verts.new(Vector((cx + cr, cy + cr, 0.0))),
                bm.verts.new(Vector((cx - cr, cy + cr, 0.0))),
                bm.verts.new(Vector((cx - cr, cy - cr, clearance))),
                bm.verts.new(Vector((cx + cr, cy - cr, clearance))),
                bm.verts.new(Vector((cx + cr, cy + cr, clearance))),
                bm.verts.new(Vector((cx - cr, cy + cr, clearance))),
            ]
            for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
                bm.faces.new([p_v[i] for i in idxs]).material_index = 1

    # 2 Islas de bombas de gasolina
    for cy in col_y_offsets:
        iw = 5.0
        id_ = 1.2
        ih = 0.20
        i_v = [
            bm.verts.new(Vector((-iw, cy - id_, 0.0))),
            bm.verts.new(Vector(( iw, cy - id_, 0.0))),
            bm.verts.new(Vector(( iw, cy + id_, 0.0))),
            bm.verts.new(Vector((-iw, cy + id_, 0.0))),
            bm.verts.new(Vector((-iw, cy - id_, ih))),
            bm.verts.new(Vector(( iw, cy - id_, ih))),
            bm.verts.new(Vector(( iw, cy + id_, ih))),
            bm.verts.new(Vector((-iw, cy + id_, ih))),
        ]
        for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]:
            bm.faces.new([i_v[i] for i in idxs]).material_index = 1

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["pemex_green"])
    mesh.materials.append(mats["sct_white"])
    mesh.materials.append(mats["industrial_sheet"])
    return mesh


def build_industrial_warehouse_mesh(width: float = 24.0, depth: float = 35.0, height: float = 7.5) -> bpy.types.Mesh:
    """Genera una nave industrial/bodega logística de lámina acanalada típica del corredor de Chapala."""
    mesh_name = "Mesh_Building_Industrial_Warehouse"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    hw = width / 2.0
    hd = depth / 2.0
    ridge_h = height + 2.5

    # Estructura principal con techo a dos aguas
    w_verts = [
        bm.verts.new(Vector((-hw, -hd, 0.0))),
        bm.verts.new(Vector(( hw, -hd, 0.0))),
        bm.verts.new(Vector(( hw,  hd, 0.0))),
        bm.verts.new(Vector((-hw,  hd, 0.0))),
        bm.verts.new(Vector((-hw, -hd, height))),
        bm.verts.new(Vector(( hw, -hd, height))),
        bm.verts.new(Vector(( hw,  hd, height))),
        bm.verts.new(Vector((-hw,  hd, height))),
        bm.verts.new(Vector((0.0, -hd, ridge_h))),  # cumbrera frontal
        bm.verts.new(Vector((0.0,  hd, ridge_h))),  # cumbrera trasera
    ]

    # Paredes laterales
    bm.faces.new([w_verts[1], w_verts[2], w_verts[6], w_verts[5]]).material_index = 0
    bm.faces.new([w_verts[3], w_verts[0], w_verts[4], w_verts[7]]).material_index = 0

    # Fachada frontal con piñón a dos aguas
    bm.faces.new([w_verts[0], w_verts[1], w_verts[5], w_verts[8], w_verts[4]]).material_index = 0
    # Fachada trasera
    bm.faces.new([w_verts[2], w_verts[3], w_verts[7], w_verts[9], w_verts[6]]).material_index = 0

    # Techos inclinados de lámina
    bm.faces.new([w_verts[4], w_verts[8], w_verts[9], w_verts[7]]).material_index = 0
    bm.faces.new([w_verts[8], w_verts[5], w_verts[6], w_verts[9]]).material_index = 0

    # Portón metálico de carga en la fachada frontal
    gate_w = 4.0
    gate_h = 4.5
    g_verts = [
        bm.verts.new(Vector((-gate_w * 0.5, -hd - 0.05, 0.0))),
        bm.verts.new(Vector(( gate_w * 0.5, -hd - 0.05, 0.0))),
        bm.verts.new(Vector(( gate_w * 0.5, -hd - 0.05, gate_h))),
        bm.verts.new(Vector((-gate_w * 0.5, -hd - 0.05, gate_h))),
    ]
    gate_f = bm.faces.new(g_verts)
    gate_f.material_index = 1  # acero galvanizado

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["industrial_sheet"])
    mesh.materials.append(mats["galvanized_steel"])
    return mesh


def build_mexican_house_with_tinaco_mesh(width: float = 8.0, depth: float = 10.0, height: float = 5.5) -> bpy.types.Mesh:
    """Genera una casa mexicana de 2 pisos con pretil en la azotea, tinaco Rotoplas negro y castillos con varillas."""
    mesh_name = "Mesh_Building_Mexican_House"
    if mesh_name in bpy.data.meshes:
        return bpy.data.meshes[mesh_name]

    mats = setup_mexico_materials()
    bm = bmesh.new()

    hw = width / 2.0
    hd = depth / 2.0

    # Cuerpo principal de la casa
    h_verts = [
        bm.verts.new(Vector((-hw, -hd, 0.0))),
        bm.verts.new(Vector(( hw, -hd, 0.0))),
        bm.verts.new(Vector(( hw,  hd, 0.0))),
        bm.verts.new(Vector((-hw,  hd, 0.0))),
        bm.verts.new(Vector((-hw, -hd, height))),
        bm.verts.new(Vector(( hw, -hd, height))),
        bm.verts.new(Vector(( hw,  hd, height))),
        bm.verts.new(Vector((-hw,  hd, height))),
    ]
    for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]:
        f = bm.faces.new([h_verts[i] for i in idxs])
        f.material_index = 0  # ladrillo / estuco mexicano

    # Pretil perimetral en la azotea (0.6m alto)
    p_h = 0.6
    p_verts = [
        bm.verts.new(Vector((-hw, -hd, height + p_h))),
        bm.verts.new(Vector(( hw, -hd, height + p_h))),
        bm.verts.new(Vector(( hw,  hd, height + p_h))),
        bm.verts.new(Vector((-hw,  hd, height + p_h))),
    ]
    for i in range(4):
        next_i = (i + 1) % 4
        bm.faces.new([h_verts[4 + i], h_verts[4 + next_i], p_verts[next_i], p_verts[i]]).material_index = 0

    # TINACO ROTOPLAS NEGRO en la azotea (cilindro en una esquina de la azotea)
    t_center = Vector((-hw * 0.5, hd * 0.4, height + 0.1))
    t_radius = 0.65
    t_h = 1.10
    segs = 12
    t_bot = []
    t_top = []

    for i in range(segs):
        ang = (2.0 * math.pi * i) / segs
        tx = t_center.x + t_radius * math.cos(ang)
        ty = t_center.y + t_radius * math.sin(ang)
        t_bot.append(bm.verts.new(Vector((tx, ty, t_center.z))))
        t_top.append(bm.verts.new(Vector((tx, ty, t_center.z + t_h))))

    for i in range(segs):
        next_i = (i + 1) % segs
        bm.faces.new([t_bot[i], t_bot[next_i], t_top[next_i], t_top[i]]).material_index = 1  # rotoplas_black

    bm.faces.new(t_top).material_index = 1

    # CASTILLOS CON VARILLAS SALIENDO EN LAS 4 ESQUINAS (ICÓNICO MEXICANO)
    for cx in (-hw, hw):
        for cy in (-hd, hd):
            # Castillo de concreto sobresaliente (0.8m)
            col_sz = 0.20
            c_bot_z = height + p_h
            c_top_z = c_bot_z + 0.4
            cv = [
                bm.verts.new(Vector((cx - col_sz, cy - col_sz, c_bot_z))),
                bm.verts.new(Vector((cx + col_sz, cy - col_sz, c_bot_z))),
                bm.verts.new(Vector((cx + col_sz, cy + col_sz, c_bot_z))),
                bm.verts.new(Vector((cx - col_sz, cy + col_sz, c_bot_z))),
                bm.verts.new(Vector((cx - col_sz, cy - col_sz, c_top_z))),
                bm.verts.new(Vector((cx + col_sz, cy - col_sz, c_top_z))),
                bm.verts.new(Vector((cx + col_sz, cy + col_sz, c_top_z))),
                bm.verts.new(Vector((cx - col_sz, cy + col_sz, c_top_z))),
            ]
            for idxs in [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]:
                bm.faces.new([cv[i] for i in idxs]).material_index = 2  # concreto cfe

            # 4 Varillas de acero corrugado de 3/8" saliendo hacia arriba (+0.9m)
            for vx in (-0.08, 0.08):
                for vy in (-0.08, 0.08):
                    v0 = bm.verts.new(Vector((cx + vx, cy + vy, c_top_z)))
                    v1 = bm.verts.new(Vector((cx + vx, cy + vy, c_top_z + 0.9)))
                    bm.edges.new([v0, v1])

    mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(mesh)
    bm.free()

    mesh.materials.append(mats["mexican_brick"])
    mesh.materials.append(mats["rotoplas_black"])
    mesh.materials.append(mats["cfe_concrete"])
    return mesh
