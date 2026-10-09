"""Generador de mallas de carretera: Visual (ROAD_) y Física optimizada (1ROAD_) para Assetto Corsa."""

import math
import bpy
import bmesh
from mathutils import Vector, Matrix
from ..core.constants import (
    COLLECTION_ROOT,
    COLLECTION_ROAD_VISUAL,
    COLLECTION_ROAD_PHYSICS,
    PREFIX_PHYS_ROAD,
    PREFIX_PHYS_WALL,
    PREFIX_PHYS_KERB,
    ELEMENT_ROAD_VISUAL,
    ELEMENT_ROAD_PHYSICS,
    ELEMENT_WALL,
)
from ..core.utils import get_or_create_collection
from .profile_generator import generate_cross_section_profile, RoadProfilePoint


def get_or_create_material(name: str, color_rgba: tuple[float, float, float, float], roughness: float = 0.8) -> bpy.types.Material:
    """Crea o reutiliza un material básico para previsualización en el Viewport."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = color_rgba
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
    return mat


def sample_curve_evaluated(curve_obj: bpy.types.Object, step_length: float = None, resolution_multiplier: int = 1) -> list[dict]:
    """Evalúa la curva y retorna una lista de muestras ordenadas con posición, tangente, normal y peralte (tilt)."""
    # Usar una copia evaluada de la curva
    curve = curve_obj.data
    spline = curve.splines[0]
    is_cyclic = spline.use_cyclic_u

    # Convertir temporalmente a bmesh o evaluar puntos
    # Para máxima compatibilidad matemática, calculamos puntos a lo largo de los segmentos Bézier
    bezier_points = spline.bezier_points
    num_bp = len(bezier_points)

    if num_bp < 2:
        return []

    # Determinar número de muestras por tramo
    if step_length and step_length > 0.05:
        # Calcular longitud aproximada total de la curva
        approx_len = 0.0
        for i in range(num_bp if is_cyclic else num_bp - 1):
            next_i = (i + 1) % num_bp
            approx_len += (bezier_points[next_i].co - bezier_points[i].co).length
        samples_count = max(8, int(approx_len / step_length))
    else:
        samples_count = num_bp * max(4, curve.resolution_u * resolution_multiplier)

    samples = []
    total_segments = num_bp if is_cyclic else num_bp - 1

    # Interpolar puntos con algoritmo de De Casteljau en cada tramo Bézier
    samples_per_seg = max(2, samples_count // total_segments)

    accum_distance = 0.0
    last_pos = None

    for seg_idx in range(total_segments):
        bp0 = bezier_points[seg_idx]
        bp1 = bezier_points[(seg_idx + 1) % num_bp]

        p0 = curve_obj.matrix_world @ bp0.co
        p1 = curve_obj.matrix_world @ bp0.handle_right
        p2 = curve_obj.matrix_world @ bp1.handle_left
        p3 = curve_obj.matrix_world @ bp1.co

        tilt0 = bp0.tilt
        tilt1 = bp1.tilt

        # No repetir el último punto en cada segmento
        steps = samples_per_seg if seg_idx < total_segments - 1 else samples_per_seg + (0 if is_cyclic else 1)

        for s in range(steps):
            t = s / samples_per_seg
            t_inv = 1.0 - t

            # Posición cúbica Bézier B(t)
            pos = (
                (t_inv ** 3) * p0
                + 3 * (t_inv ** 2) * t * p1
                + 3 * t_inv * (t ** 2) * p2
                + (t ** 3) * p3
            )

            # Tangente primera derivada B'(t)
            tangent = (
                3 * (t_inv ** 2) * (p1 - p0)
                + 6 * t_inv * t * (p2 - p1)
                + 3 * (t ** 2) * (p3 - p2)
            )

            if tangent.length > 0.0001:
                tangent = tangent.normalized()
            else:
                tangent = Vector((0.0, 1.0, 0.0))

            # Peralte interpolado
            tilt = (t_inv * tilt0) + (t * tilt1)

            if last_pos is not None:
                accum_distance += (pos - last_pos).length
            last_pos = pos

            samples.append({
                "pos": pos,
                "tangent": tangent,
                "tilt": tilt,
                "dist": accum_distance,
            })

    return samples


class TRACKMAKER_OT_GenerateRoadMeshes(bpy.types.Operator):
    """Genera la Malla Visual (ROAD_) y la Malla Física subdividida para AC (1ROAD_)."""

    bl_idname = "track_maker.generate_road_meshes"
    bl_label = "Generar Mallas (Visual y Física AC)"
    bl_options = {"REGISTER", "UNDO"}

    create_visual: bpy.props.BoolProperty(
        name="Crear Malla Visual",
        description="Genera la malla ROAD_ con bordillos, materiales y UVs",
        default=True,
    )

    create_physics: bpy.props.BoolProperty(
        name="Crear Malla Física (1ROAD_)",
        description="Genera el colisionador 1ROAD_ con subdivisión uniforme de 0.3m para FFB",
        default=True,
    )

    def execute(self, context):
        curve_obj = context.active_object
        if not curve_obj or curve_obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto de tipo Curva de carretera.")
            return {"CANCELLED"}

        road_cfg = context.scene.track_maker_road
        base_name = road_cfg.road_name or "Pista"
        is_cyclic = curve_obj.data.splines[0].use_cyclic_u

        # Crear materiales de previsualización
        mat_road = get_or_create_material("MAT_TM_Asphalt", (0.12, 0.12, 0.13, 1.0), 0.85)
        mat_kerb = get_or_create_material("MAT_TM_Kerb", (0.80, 0.15, 0.15, 1.0), 0.60)
        mat_sidewalk = get_or_create_material("MAT_TM_Sidewalk", (0.50, 0.50, 0.50, 1.0), 0.90)
        mat_wall = get_or_create_material("MAT_TM_Wall", (0.35, 0.37, 0.40, 1.0), 0.70)
        mat_grass = get_or_create_material("MAT_TM_Grass", (0.18, 0.28, 0.14, 1.0), 0.95)

        # -------------------------------------------------------------
        # 1. GENERACIÓN DE LA MALLA VISUAL (ROAD_)
        # -------------------------------------------------------------
        if self.create_visual:
            vis_samples = sample_curve_evaluated(
                curve_obj,
                step_length=None,
                resolution_multiplier=road_cfg.visual_resolution_y // 12,
            )

            if len(vis_samples) >= 2:
                vis_profile = generate_cross_section_profile(
                    road_width=road_cfg.road_width,
                    subdivisions_x=road_cfg.road_subdivisions_x,
                    has_crown=road_cfg.has_crown,
                    crown_height=road_cfg.crown_height,
                    has_kerbs=road_cfg.has_kerbs,
                    kerb_width=road_cfg.kerb_width,
                    kerb_height=road_cfg.kerb_height,
                    has_sidewalks=road_cfg.has_sidewalks,
                    sidewalk_width=road_cfg.sidewalk_width,
                    has_shoulders=getattr(road_cfg, "has_shoulders", True),
                    shoulder_width=getattr(road_cfg, "shoulder_width", 2.5),
                    shoulder_slope=getattr(road_cfg, "shoulder_slope", 0.15),
                    has_walls=road_cfg.has_walls,
                    wall_height=road_cfg.wall_height,
                    for_physics_only=False,
                )

                vis_mesh_name = f"ROAD_{base_name}"
                if vis_mesh_name in bpy.data.objects:
                    bpy.data.objects.remove(bpy.data.objects[vis_mesh_name], do_unlink=True)

                bm_vis = bmesh.new()
                uv_layer = bm_vis.loops.layers.uv.new("UVMap")

                num_rings = len(vis_samples)
                num_pts = len(vis_profile)

                # Generar vértices en anillos ordenados
                rings_verts = []
                world_up = Vector((0.0, 0.0, 1.0))

                for sample in vis_samples:
                    center_pos = sample["pos"]
                    tangent = sample["tangent"]
                    tilt = sample["tilt"]

                    # Base ortonormal
                    right_vec = tangent.cross(world_up)
                    if right_vec.length < 0.001:
                        right_vec = Vector((1.0, 0.0, 0.0))
                    else:
                        right_vec = right_vec.normalized()

                    up_vec = right_vec.cross(tangent).normalized()

                    # Aplicar peralte (tilt) rotando right_vec y up_vec sobre el eje tangent
                    if abs(tilt) > 0.0001:
                        rot_mat = Matrix.Rotation(tilt, 3, tangent)
                        right_vec = rot_mat @ right_vec
                        up_vec = rot_mat @ up_vec

                    ring = []
                    for pt in vis_profile:
                        vert_pos = center_pos + (right_vec * pt.offset_x) + (up_vec * pt.offset_z)
                        v = bm_vis.verts.new(vert_pos)
                        ring.append(v)
                    rings_verts.append(ring)

                bm_vis.verts.ensure_lookup_table()

                # Generar caras cuadriláteras entre anillos contiguos
                rings_count = num_rings if is_cyclic else num_rings - 1
                for r in range(rings_count):
                    r_next = (r + 1) % num_rings
                    ring_a = rings_verts[r]
                    ring_b = rings_verts[r_next]

                    dist_a = vis_samples[r]["dist"]
                    dist_b = vis_samples[r_next]["dist"] if r_next > 0 else (vis_samples[r]["dist"] + 1.0)
                    v_coord_a = dist_a * road_cfg.uv_tiling_v
                    v_coord_b = dist_b * road_cfg.uv_tiling_v

                    for p in range(num_pts - 1):
                        v0 = ring_a[p]
                        v1 = ring_b[p]
                        v2 = ring_b[p + 1]
                        v3 = ring_a[p + 1]

                        face = bm_vis.faces.new((v0, v1, v2, v3))
                        face.material_index = vis_profile[p].mat_index
                        face.smooth = True

                        # Mapeo UV procedural exacto
                        u_a = vis_profile[p].u_coord
                        u_b = vis_profile[p + 1].u_coord

                        for loop in face.loops:
                            if loop.vert == v0:
                                loop[uv_layer].uv = (u_a, v_coord_a)
                            elif loop.vert == v1:
                                loop[uv_layer].uv = (u_a, v_coord_b)
                            elif loop.vert == v2:
                                loop[uv_layer].uv = (u_b, v_coord_b)
                            elif loop.vert == v3:
                                loop[uv_layer].uv = (u_b, v_coord_a)

                vis_mesh_data = bpy.data.meshes.new(vis_mesh_name)
                bm_vis.to_mesh(vis_mesh_data)
                bm_vis.free()

                vis_mesh_data.materials.append(mat_road)
                vis_mesh_data.materials.append(mat_kerb)
                vis_mesh_data.materials.append(mat_sidewalk)
                vis_mesh_data.materials.append(mat_wall)
                vis_mesh_data.materials.append(mat_grass)

                vis_obj = bpy.data.objects.new(vis_mesh_name, vis_mesh_data)
                vis_obj["track_element_type"] = ELEMENT_ROAD_VISUAL

                col_vis = get_or_create_collection(COLLECTION_ROAD_VISUAL, parent_name=COLLECTION_ROOT)
                col_vis.objects.link(vis_obj)

        # -------------------------------------------------------------
        # 2. GENERACIÓN DE LA MALLA FÍSICA (1ROAD_)
        # -------------------------------------------------------------
        if self.create_physics:
            # Malla física evaluada a paso constante de 0.2m - 0.4m para el Force Feedback de Kunos
            step_len = max(0.15, road_cfg.physics_subdivision_y)
            phys_samples = sample_curve_evaluated(curve_obj, step_length=step_len)

            if len(phys_samples) >= 2:
                # Perfil físico puro (asfalto + arcenes exteriores para colisiones)
                phys_profile = generate_cross_section_profile(
                    road_width=road_cfg.road_width,
                    subdivisions_x=road_cfg.road_subdivisions_x,
                    has_crown=road_cfg.has_crown,
                    crown_height=road_cfg.crown_height,
                    has_kerbs=False,
                    has_sidewalks=False,
                    has_shoulders=getattr(road_cfg, "has_shoulders", True),
                    shoulder_width=getattr(road_cfg, "shoulder_width", 2.5),
                    shoulder_slope=getattr(road_cfg, "shoulder_slope", 0.15),
                    has_walls=False,
                    for_physics_only=True,
                )

                phys_mesh_name = f"{PREFIX_PHYS_ROAD}{base_name}"
                if phys_mesh_name in bpy.data.objects:
                    bpy.data.objects.remove(bpy.data.objects[phys_mesh_name], do_unlink=True)

                bm_phys = bmesh.new()

                num_rings_p = len(phys_samples)
                num_pts_p = len(phys_profile)

                rings_verts_p = []
                world_up = Vector((0.0, 0.0, 1.0))

                for sample in phys_samples:
                    center_pos = sample["pos"]
                    tangent = sample["tangent"]
                    tilt = sample["tilt"]

                    right_vec = tangent.cross(world_up)
                    if right_vec.length < 0.001:
                        right_vec = Vector((1.0, 0.0, 0.0))
                    else:
                        right_vec = right_vec.normalized()

                    up_vec = right_vec.cross(tangent).normalized()

                    if abs(tilt) > 0.0001:
                        rot_mat = Matrix.Rotation(tilt, 3, tangent)
                        right_vec = rot_mat @ right_vec
                        up_vec = rot_mat @ up_vec

                    ring = []
                    for pt in phys_profile:
                        vert_pos = center_pos + (right_vec * pt.offset_x) + (up_vec * pt.offset_z)
                        v = bm_phys.verts.new(vert_pos)
                        ring.append(v)
                    rings_verts_p.append(ring)

                bm_phys.verts.ensure_lookup_table()

                # Generar caras trianguladas (vital para el motor de colisiones de AC)
                rings_count_p = num_rings_p if is_cyclic else num_rings_p - 1
                for r in range(rings_count_p):
                    r_next = (r + 1) % num_rings_p
                    ring_a = rings_verts_p[r]
                    ring_b = rings_verts_p[r_next]

                    for p in range(num_pts_p - 1):
                        v0 = ring_a[p]
                        v1 = ring_b[p]
                        v2 = ring_b[p + 1]
                        v3 = ring_a[p + 1]

                        # Dos triángulos por cuadrilátero para asegurar coplanaridad física
                        f1 = bm_phys.faces.new((v0, v1, v2))
                        f2 = bm_phys.faces.new((v0, v2, v3))
                        f1.smooth = True
                        f2.smooth = True

                phys_mesh_data = bpy.data.meshes.new(phys_mesh_name)
                bm_phys.to_mesh(phys_mesh_data)
                bm_phys.free()

                # Asignar material físico básico
                phys_mesh_data.materials.append(mat_road)

                phys_obj = bpy.data.objects.new(phys_mesh_name, phys_mesh_data)
                phys_obj["track_element_type"] = ELEMENT_ROAD_PHYSICS
                phys_obj.display_type = "WIRE"  # Evita Z-fighting con la malla visual en el Viewport

                col_phys = get_or_create_collection(COLLECTION_ROAD_PHYSICS, parent_name=COLLECTION_ROOT)
                col_phys.objects.link(phys_obj)


        self.report({"INFO"}, f"Mallas generadas: Visual (ROAD_{base_name}) y Física ({PREFIX_PHYS_ROAD}{base_name})")
        return {"FINISHED"}


classes = (TRACKMAKER_OT_GenerateRoadMeshes,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

