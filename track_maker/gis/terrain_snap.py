"""Algoritmos de proyección vertical (Raycast), adaptación topográfica a LiDAR y suavizado de pendientes."""

import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def get_terrain_bvh_and_matrix(terrain_obj: bpy.types.Object, depsgraph: bpy.types.Depsgraph) -> tuple[BVHTree, any]:
    """Construye un árbol espacial BVH a partir de la malla de terreno para raycasting ultrarrápido."""
    eval_obj = terrain_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    bvh = BVHTree.FromMesh(mesh)
    matrix_world = terrain_obj.matrix_world.copy()
    eval_obj.to_mesh_clear()
    return bvh, matrix_world


def raycast_vertical_to_terrain(
    point_world: Vector,
    bvh: BVHTree,
    terrain_matrix_inv: any,
    terrain_matrix: any,
    ray_height: float = 500.0,
) -> tuple[Vector | None, Vector | None]:
    """Lanza un rayo vertical hacia abajo contra el terreno.
    Retorna la posición de impacto en el espacio mundo y la normal de la superficie.
    """
    origin_world = Vector((point_world.x, point_world.y, point_world.z + ray_height))
    direction_world = Vector((0.0, 0.0, -1.0))

    # Transformar rayo al espacio local del terreno
    origin_local = terrain_matrix_inv @ origin_world
    direction_local = (terrain_matrix_inv.to_3x3() @ direction_world).normalized()

    hit_loc, hit_norm, hit_idx, hit_dist = bvh.ray_cast(origin_local, direction_local, ray_height * 2.5)

    if hit_loc is not None:
        hit_world = terrain_matrix @ hit_loc
        norm_world = (terrain_matrix.to_3x3() @ hit_norm).normalized()
        return hit_world, norm_world

    return None, None


class TRACKMAKER_OT_SnapCurveToTerrain(bpy.types.Operator):
    """Proyecta los puntos de control del spline central sobre la topografía real de la malla LiDAR."""

    bl_idname = "track_maker.snap_curve_to_terrain"
    bl_label = "Proyectar Spline al Terreno LiDAR"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj or active_obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona una Curva de carretera activa.")
            return {"CANCELLED"}

        gis_cfg = context.scene.track_maker_gis
        terrain_name = gis_cfg.target_terrain_name

        terrain_obj = None
        if terrain_name and terrain_name in bpy.data.objects:
            terrain_obj = bpy.data.objects[terrain_name]
        else:
            # Buscar en objetos seleccionados si alguno es una malla
            for obj in context.selected_objects:
                if obj != active_obj and obj.type == "MESH":
                    terrain_obj = obj
                    break

        if not terrain_obj:
            self.report(
                {"ERROR"},
                "No se encontró la malla de terreno LiDAR. Selecciona la malla o especifica su nombre en el panel.",
            )
            return {"CANCELLED"}

        depsgraph = context.evaluated_depsgraph_get()
        bvh, terrain_mat = get_terrain_bvh_and_matrix(terrain_obj, depsgraph)
        terrain_mat_inv = terrain_mat.inverted()

        curve = active_obj.data
        offset_z = gis_cfg.snap_elevation_offset
        match_banking = gis_cfg.match_terrain_banking

        snapped_count = 0
        world_mat = active_obj.matrix_world

        world_up = Vector((0.0, 0.0, 1.0))

        for spline in curve.splines:
            for bp in spline.bezier_points:
                co_world = world_mat @ bp.co
                hit_pos, hit_norm = raycast_vertical_to_terrain(co_world, bvh, terrain_mat_inv, terrain_mat)

                if hit_pos is not None:
                    delta_z = (hit_pos.z + offset_z) - co_world.z

                    # Desplazar punto y tiradores en Z manteniendo continuidad
                    bp.co.z += delta_z
                    bp.handle_left.z += delta_z
                    bp.handle_right.z += delta_z
                    snapped_count += 1

                    # Cálculo del peralte real a partir de la normal del terreno
                    if match_banking and hit_norm is not None:
                        tangent = (bp.handle_right - bp.handle_left).normalized()
                        if tangent.length > 0.001:
                            right_vec = tangent.cross(world_up).normalized()
                            # Componente transversal de la normal del terreno
                            transversal_slope = right_vec.dot(hit_norm)
                            # Inclinación en radianes (limitada a máximo +- 30 grados)
                            clamped_slope = max(-0.5, min(0.5, transversal_slope))
                            bp.tilt = math.asin(clamped_slope)

        # Forzar actualización de la curva
        curve.update_tag()

        self.report(
            {"INFO"},
            f"Proyección completada: {snapped_count} puntos adaptados a la topografía de '{terrain_obj.name}'.",
        )
        return {"FINISHED"}


class TRACKMAKER_OT_SmoothCurveElevation(bpy.types.Operator):
    """Suaviza las variaciones bruscas de cota vertical para filtrar ruido del escaneo LiDAR."""

    bl_idname = "track_maker.smooth_curve_elevation"
    bl_label = "Suavizar Pendiente Vertical (Filtro LiDAR)"
    bl_options = {"REGISTER", "UNDO"}

    smoothing_factor: bpy.props.FloatProperty(
        name="Factor de Suavizado",
        description="Fuerza del filtro laplaciano (0.0 = sin cambio, 1.0 = máxima atenuación)",
        default=0.5,
        min=0.1,
        max=0.9,
    )

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj or active_obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto de tipo Curva.")
            return {"CANCELLED"}

        gis_cfg = context.scene.track_maker_gis
        passes = gis_cfg.smoothing_passes
        curve = active_obj.data
        alpha = self.smoothing_factor

        for spline in curve.splines:
            points = spline.bezier_points
            n = len(points)
            if n < 3:
                continue

            is_cyclic = spline.use_cyclic_u

            for _ in range(passes):
                z_original = [bp.co.z for bp in points]

                start_idx = 0 if is_cyclic else 1
                end_idx = n if is_cyclic else n - 1

                for i in range(start_idx, end_idx):
                    prev_i = (i - 1) % n
                    next_i = (i + 1) % n

                    z_avg = (z_original[prev_i] + z_original[next_i]) / 2.0
                    new_z = (1.0 - alpha) * z_original[i] + (alpha * z_avg)
                    delta = new_z - points[i].co.z

                    points[i].co.z = new_z
                    points[i].handle_left.z += delta
                    points[i].handle_right.z += delta

        curve.update_tag()
        self.report({"INFO"}, f"Pendiente vertical suavizada ({passes} pasadas aplicadas).")
        return {"FINISHED"}


def terraform_terrain_to_road(
    terrain_obj: bpy.types.Object,
    spline_obj: bpy.types.Object,
    road_width: float = 12.0,
    clearance: float = 0.20,
    falloff: float = 4.0,
) -> int:
    """Modifica la cota Z de los vértices del terreno directamente debajo de la calzada para evitar penetraciones."""
    from mathutils import kdtree

    if not terrain_obj or terrain_obj.type != "MESH":
        raise ValueError("El objeto de terreno debe ser una malla (MESH).")
    if not spline_obj or spline_obj.type != "CURVE" or not spline_obj.data.splines:
        raise ValueError("El trazado debe ser una curva (CURVE) con al menos un spline.")

    spline = spline_obj.data.splines[0]
    mat_spline = spline_obj.matrix_world
    mat_terrain = terrain_obj.matrix_world
    inv_terrain = mat_terrain.inverted()

    # Muestrear puntos de la curva
    if spline.type == "BEZIER":
        raw_pts = [mat_spline @ bp.co for bp in spline.bezier_points]
    else:
        raw_pts = [mat_spline @ p.co.to_3d() for p in spline.points]

    if len(raw_pts) < 2:
        return 0

    # Subdividir linealmente para tener muestras densas cada ~5m
    dense_pts = []
    for i in range(len(raw_pts) - 1):
        p_a = raw_pts[i]
        p_b = raw_pts[i + 1]
        seg_len = (p_b - p_a).length
        steps = max(1, int(seg_len / 5.0))
        for s in range(steps):
            dense_pts.append(p_a.lerp(p_b, s / steps))
    dense_pts.append(raw_pts[-1])

    # Construir KDTree con las muestras del eje de carretera
    kd = kdtree.KDTree(len(dense_pts))
    for idx, pt in enumerate(dense_pts):
        kd.insert(pt, idx)
    kd.balance()

    mesh = terrain_obj.data
    half_w = road_width / 2.0
    total_w = half_w + falloff
    modified_count = 0

    for v in mesh.vertices:
        v_world = mat_terrain @ v.co
        near_pt, near_idx, dist_3d = kd.find(v_world)
        dist_2d = math.hypot(v_world.x - near_pt.x, v_world.y - near_pt.y)

        if dist_2d <= total_w:
            road_z = near_pt.z
            target_z = road_z - clearance

            if dist_2d <= half_w:
                # Directamente bajo la calzada: deprimir si sobresale
                if v_world.z > target_z:
                    new_w = Vector((v_world.x, v_world.y, target_z))
                    v.co = inv_terrain @ new_w
                    modified_count += 1
            else:
                # Zona de transición / talud
                t = (dist_2d - half_w) / falloff
                blend_target = target_z * (1.0 - t) + v_world.z * t
                if v_world.z > blend_target:
                    new_w = Vector((v_world.x, v_world.y, blend_target))
                    v.co = inv_terrain @ new_w
                    modified_count += 1

    if modified_count > 0:
        mesh.update()

    return modified_count


class TRACKMAKER_OT_TerraformTerrain(bpy.types.Operator):
    """Conforma el relieve del terreno bajo la carretera (Desmonte) para que la montaña no perfore el asfalto."""

    bl_idname = "track_maker.terraform_terrain"
    bl_label = "Conformar Terreno bajo Calzada"
    bl_description = "Hunde los salientes del relieve DEM bajo la carretera para evitar que el terreno perfore el asfalto"
    bl_options = {"REGISTER", "UNDO"}

    clearance: bpy.props.FloatProperty(
        name="Holgura Bajo Asfalto (m)",
        description="Distancia de seguridad por debajo de la cota de asfalto",
        default=0.20,
        min=0.05,
        max=1.0,
        unit="LENGTH",
    )

    falloff: bpy.props.FloatProperty(
        name="Margen de Transición (m)",
        description="Anchura del talud de transición fuera de la calzada",
        default=4.0,
        min=1.0,
        max=20.0,
        unit="LENGTH",
    )

    def execute(self, context):
        gis_cfg = context.scene.track_maker_gis
        terrain_obj = bpy.data.objects.get(gis_cfg.target_terrain_name or "TM_Terrain")
        spline_obj = context.active_object if (context.active_object and context.active_object.type == "CURVE") else bpy.data.objects.get("Spline_Route_AB")

        if not terrain_obj or terrain_obj.type != "MESH":
            self.report({"ERROR"}, "No se encontró el objeto de terreno ('TM_Terrain').")
            return {"CANCELLED"}
        if not spline_obj or spline_obj.type != "CURVE":
            self.report({"ERROR"}, "No se encontró el spline de la carretera.")
            return {"CANCELLED"}

        road_cfg = getattr(context.scene, "track_maker_road", None)
        road_w = getattr(road_cfg, "road_width", 12.0) if road_cfg else 12.0
        if getattr(road_cfg, "has_shoulders", False):
            road_w += getattr(road_cfg, "shoulder_width", 2.5) * 2.0

        try:
            modified = terraform_terrain_to_road(
                terrain_obj=terrain_obj,
                spline_obj=spline_obj,
                road_width=road_w,
                clearance=self.clearance,
                falloff=self.falloff,
            )
            self.report({"INFO"}, f"🏔️ Terreno conformado: {modified} vértices adaptados bajo la calzada.")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error conformando terreno: {e}")
            return {"CANCELLED"}


classes = (
    TRACKMAKER_OT_SnapCurveToTerrain,
    TRACKMAKER_OT_SmoothCurveElevation,
    TRACKMAKER_OT_TerraformTerrain,
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

