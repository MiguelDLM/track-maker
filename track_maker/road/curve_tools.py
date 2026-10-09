"""Herramientas para la creación, edición y peralte (tilt/banking) de splines de carretera."""

import math
import bpy
from mathutils import Vector
from ..core.constants import COLLECTION_ROOT, COLLECTION_ROAD_VISUAL
from ..core.utils import get_or_create_collection


class TRACKMAKER_OT_CreateRoadSpline(bpy.types.Operator):
    """Crea una curva 3D Bézier inicial configurada para modelado de carreteras."""

    bl_idname = "track_maker.create_road_spline"
    bl_label = "Crear Spline de Carretera"
    bl_options = {"REGISTER", "UNDO"}

    spline_type: bpy.props.EnumProperty(
        name="Tipo de Trazado",
        items=[
            ("CLOSED_LOOP", "Bucle Cerrado (Circuito)", "Crea un óvalo/circuito de pruebas cerrado"),
            ("OPEN_SECTION", "Tramo Abierto (Carretera)", "Crea un tramo de carretera abierta A-B con curvas"),
        ],
        default="CLOSED_LOOP",
    )

    radius: bpy.props.FloatProperty(
        name="Radio / Escala",
        description="Dimensión general del trazado inicial en metros",
        default=60.0,
        min=10.0,
        max=500.0,
        unit="LENGTH",
    )

    def execute(self, context):
        cursor_loc = context.scene.cursor.location.copy()

        curve_data = bpy.data.curves.new(name="TM_Road_Centerline", type="CURVE")
        curve_data.dimensions = "3D"
        curve_data.resolution_u = 24
        curve_data.twist_mode = "MINIMUM"  # Minimiza rotaciones extrañas a lo largo de 3D

        spline = curve_data.splines.new(type="BEZIER")

        if self.spline_type == "CLOSED_LOOP":
            spline.use_cyclic_u = True
            r = self.radius
            # Crear 4 puntos Bézier formando un circuito de prueba con curvas y rectas
            spline.bezier_points.add(3)  # Ya tiene 1 por defecto, total 4

            points_data = [
                # (co, handle_left, handle_right)
                (Vector((-r, -r * 0.5, 0.0)), Vector((-r, -r * 0.8, 0.0)), Vector((-r, r * 0.2, 0.0))),
                (Vector((-r * 0.4, r, 2.0)), Vector((-r * 0.8, r, 1.0)), Vector((0.0, r, 2.5))),
                (Vector((r, r * 0.4, 4.0)), Vector((r * 0.3, r * 0.8, 3.5)), Vector((r, -r * 0.2, 3.0))),
                (Vector((r * 0.2, -r, 1.0)), Vector((r * 0.7, -r, 2.0)), Vector((-r * 0.4, -r, 0.5))),
            ]

            for i, (co, hl, hr) in enumerate(points_data):
                bp = spline.bezier_points[i]
                bp.co = co + cursor_loc
                bp.handle_left = hl + cursor_loc
                bp.handle_right = hr + cursor_loc
                bp.handle_left_type = "ALIGNED"
                bp.handle_right_type = "ALIGNED"

        else:  # OPEN_SECTION
            spline.use_cyclic_u = False
            l = self.radius * 2.0
            spline.bezier_points.add(3)

            points_data = [
                (Vector((0.0, 0.0, 0.0)), Vector((0.0, -20.0, 0.0)), Vector((0.0, 30.0, 0.0))),
                (Vector((40.0, l * 0.33, 4.0)), Vector((20.0, l * 0.25, 2.5)), Vector((60.0, l * 0.42, 5.5))),
                (Vector((-30.0, l * 0.66, 9.0)), Vector((-10.0, l * 0.55, 7.5)), Vector((-50.0, l * 0.75, 10.5))),
                (Vector((10.0, l, 15.0)), Vector((0.0, l - 30.0, 13.5)), Vector((20.0, l + 30.0, 16.5))),
            ]

            for i, (co, hl, hr) in enumerate(points_data):
                bp = spline.bezier_points[i]
                bp.co = co + cursor_loc
                bp.handle_left = hl + cursor_loc
                bp.handle_right = hr + cursor_loc
                bp.handle_left_type = "ALIGNED"
                bp.handle_right_type = "ALIGNED"

        curve_obj = bpy.data.objects.new(name="Spline_Carretera", object_data=curve_data)
        curve_obj["track_element_type"] = "ROAD_SPLINE"

        col = get_or_create_collection(COLLECTION_ROAD_VISUAL, parent_name=COLLECTION_ROOT)
        col.objects.link(curve_obj)

        # Seleccionar y activar el nuevo spline
        bpy.ops.object.select_all(action="DESELECT")
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj

        self.report({"INFO"}, f"Spline de carretera '{curve_obj.name}' creado correctamente.")
        return {"FINISHED"}


class TRACKMAKER_OT_ToggleSplineCyclic(bpy.types.Operator):
    """Alterna el spline activo entre circuito cerrado y tramo abierto."""

    bl_idname = "track_maker.toggle_spline_cyclic"
    bl_label = "Alternar Abierto / Cerrado"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto de tipo Curva.")
            return {"CANCELLED"}

        curve = obj.data
        for spline in curve.splines:
            spline.use_cyclic_u = not spline.use_cyclic_u

        state = "Cerrado (Circuito)" if curve.splines[0].use_cyclic_u else "Abierto (Tramo A-B)"
        self.report({"INFO"}, f"Spline cambiado a modo: {state}")
        return {"FINISHED"}


class TRACKMAKER_OT_SetCurveTilt(bpy.types.Operator):
    """Aplica un ángulo de peralte (tilt) en grados a los puntos de control seleccionados."""

    bl_idname = "track_maker.set_curve_tilt"
    bl_label = "Fijar Peralte (Tilt)"
    bl_options = {"REGISTER", "UNDO"}

    tilt_angle_degrees: bpy.props.FloatProperty(
        name="Ángulo de Peralte (°)",
        description="Inclinación transversal de la pista en grados (+ inclina a derecha, - a izquierda)",
        default=5.0,
        min=-45.0,
        max=45.0,
    )

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto de tipo Curva en Modo Edición.")
            return {"CANCELLED"}

        curve = obj.data
        rad = math.radians(self.tilt_angle_degrees)
        modified = 0

        for spline in curve.splines:
            for bp in spline.bezier_points:
                if bp.select_control_point:
                    bp.tilt = rad
                    modified += 1

        if modified == 0:
            # Si ninguno estaba seleccionado explícitamente, aplicar a todos
            for spline in curve.splines:
                for bp in spline.bezier_points:
                    bp.tilt = rad
                    modified += 1

        self.report({"INFO"}, f"Peralte fijado a {self.tilt_angle_degrees:.1f}° en {modified} puntos.")
        return {"FINISHED"}


class TRACKMAKER_OT_AutoBankCurve(bpy.types.Operator):
    """Calcula automáticamente el peralte natural de las curvas según el radio de curvatura."""

    bl_idname = "track_maker.auto_bank_curve"
    bl_label = "Calcular Auto-Peralte"
    bl_options = {"REGISTER", "UNDO"}

    max_banking_deg: bpy.props.FloatProperty(
        name="Peralte Máximo (°)",
        description="Límite máximo de inclinación en grados para curvas muy cerradas",
        default=8.0,
        min=1.0,
        max=25.0,
    )

    speed_factor: bpy.props.FloatProperty(
        name="Factor de Agresividad",
        description="Multiplicador de intensidad de peralte",
        default=1.0,
        min=0.1,
        max=3.0,
    )

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto Curva para calcular el peralte.")
            return {"CANCELLED"}

        curve = obj.data
        max_rad = math.radians(self.max_banking_deg)

        for spline in curve.splines:
            points = spline.bezier_points
            n = len(points)
            if n < 3:
                continue

            for i in range(n):
                prev_i = (i - 1) % n if spline.use_cyclic_u else max(0, i - 1)
                next_i = (i + 1) % n if spline.use_cyclic_u else min(n - 1, i + 1)

                p_prev = points[prev_i].co
                p_curr = points[i].co
                p_next = points[next_i].co

                v1 = (p_curr - p_prev).to_2d()
                v2 = (p_next - p_curr).to_2d()

                if v1.length == 0 or v2.length == 0:
                    continue

                v1_norm = v1.normalized()
                v2_norm = v2.normalized()

                # Producto cruzado 2D para detectar giro izquierda/derecha
                cross_z = (v1_norm.x * v2_norm.y) - (v1_norm.y * v2_norm.x)
                angle_diff = v1_norm.angle(v2_norm, 0.0)

                # Dirección de peralte: hacia el interior de la curva
                sign = 1.0 if cross_z > 0 else -1.0
                bank_angle = math.copysign(min(max_rad, angle_diff * self.speed_factor * 0.8), sign)

                points[i].tilt = bank_angle

        self.report({"INFO"}, "Auto-peralte calculado y aplicado a lo largo de la curva.")
        return {"FINISHED"}


class TRACKMAKER_OT_StartSurfaceDraw(bpy.types.Operator):
    """Inicia el modo interactivo para dibujar la curva del circuito directamente sobre el relieve 3D."""

    bl_idname = "track_maker.start_surface_draw"
    bl_label = "Dibujar Pista sobre Terreno"
    bl_description = "Activa el pincel de curvas con proyección sobre la superficie de la montaña"
    bl_options = {"REGISTER", "UNDO"}

    curve_name: bpy.props.StringProperty(
        name="Nombre del Trazado",
        default="Spline_Pista_Terreno",
    )

    offset_z: bpy.props.FloatProperty(
        name="Desfase sobre Terreno (m)",
        default=0.08,
        min=0.01,
        max=1.0,
        unit="LENGTH",
    )

    new_curve: bpy.props.BoolProperty(
        name="Crear Nueva Curva",
        description="Crea un objeto de curva nuevo e independiente en lugar de modificar la activa",
        default=True,
    )

    def execute(self, context):
        # 1. Localizar objeto de terreno objetivo
        gis_cfg = getattr(context.scene, "track_maker_gis", None)
        target_name = getattr(gis_cfg, "target_terrain_name", "TM_Terrain") if gis_cfg else "TM_Terrain"
        terrain_obj = bpy.data.objects.get(target_name)

        if not terrain_obj or terrain_obj.type != "MESH":
            for obj in bpy.data.objects:
                if obj.type == "MESH" and obj.get("gis_is_terrain", False):
                    terrain_obj = obj
                    break

        if not terrain_obj and context.active_object and context.active_object.type == "MESH":
            terrain_obj = context.active_object

        if not terrain_obj:
            self.report(
                {"WARNING"},
                "No se encontró terreno 3D en la escena ('TM_Terrain'). Crea o importa un terreno primero.",
            )

        # 2. Obtener o crear el objeto de curva
        active_obj = context.active_object
        if not self.new_curve and active_obj and active_obj.type == "CURVE":
            curve_obj = active_obj
        else:
            curve_data = bpy.data.curves.new(name=f"{self.curve_name}_Data", type="CURVE")
            curve_data.dimensions = "3D"
            curve_data.twist_mode = "MINIMUM"
            curve_data.resolution_u = 24
            curve_obj = bpy.data.objects.new(self.curve_name, curve_data)
            curve_obj["track_element_type"] = "ROAD_SPLINE"

            col = get_or_create_collection(COLLECTION_ROAD_VISUAL, parent_name=COLLECTION_ROOT)
            col.objects.link(curve_obj)

        # 3. Configurar ajustes de pintura de curva sobre superficie en Blender
        tool_settings = context.scene.tool_settings
        if hasattr(tool_settings, "curve_paint_settings"):
            cps = tool_settings.curve_paint_settings
            cps.depth_mode = "SURFACE"
            cps.surface_offset = self.offset_z
            cps.use_offset_absolute = True
            cps.curve_type = "BEZIER"
            if hasattr(cps, "use_corners_detect"):
                cps.use_corners_detect = False

        # Configurar ajuste magnético (snapping)
        tool_settings.use_snap = True
        try:
            tool_settings.snap_elements = {'FACE_PROJECT'}
        except Exception:
            try:
                tool_settings.snap_elements = {'FACE'}
            except Exception:
                pass

        # 4. Seleccionar la curva y entrar en modo EDIT
        for o in context.selected_objects:
            o.select_set(False)
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj

        if curve_obj.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")

        # 5. Activar la herramienta builtin.draw
        view3d_area = next((a for a in context.screen.areas if a.type == "VIEW_3D"), None) if context.screen else None
        try:
            if view3d_area:
                with context.temp_override(area=view3d_area):
                    bpy.ops.wm.tool_set_by_id(name="builtin.draw")
            else:
                bpy.ops.wm.tool_set_by_id(name="builtin.draw")
        except Exception:
            pass

        self.report(
            {"INFO"},
            "✏️ Modo Dibujo activado: Haz clic y arrastra con el ratón sobre el relieve para trazar tu circuito.",
        )
        return {"FINISHED"}


class TRACKMAKER_OT_FinishSurfaceDraw(bpy.types.Operator):
    """Finaliza el dibujo de pista interactivo, saliendo del modo edición y ajustando las tangentes."""

    bl_idname = "track_maker.finish_surface_draw"
    bl_label = "Finalizar Dibujo de Pista"
    bl_description = "Sale del modo edición y optimiza los puntos dibujados"
    bl_options = {"REGISTER", "UNDO"}

    auto_handles: bpy.props.BoolProperty(
        name="Suavizar Tangentes (Auto)",
        default=True,
    )

    def execute(self, context):
        active = context.active_object
        if not active or active.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto de Curva.")
            return {"CANCELLED"}

        if active.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")

        curve = active.data
        total_pts = 0
        pts_coords = []
        for spline in curve.splines:
            if spline.type == "BEZIER":
                for bp in spline.bezier_points:
                    if self.auto_handles:
                        bp.handle_left_type = "AUTO"
                        bp.handle_right_type = "AUTO"
                    pts_coords.append(active.matrix_world @ bp.co)
                    total_pts += 1
            elif spline.type == "POLY":
                for p in spline.points:
                    pts_coords.append(active.matrix_world @ p.co.to_3d())
                    total_pts += 1

        # Actualizar telemetría si se dibujaron puntos
        if len(pts_coords) >= 2:
            total_dist_m = 0.0
            for i in range(1, len(pts_coords)):
                total_dist_m += (pts_coords[i] - pts_coords[i - 1]).length
            gis_cfg = getattr(context.scene, "track_maker_gis", None)
            if gis_cfg:
                gis_cfg.route_info_distance = total_dist_m / 1000.0
                v_scale = getattr(gis_cfg, "vertical_scale", 1.0) or 1.0
                base_z = getattr(gis_cfg, "anchor_elevation_z", 0.0) or 0.0
                real_alts = [(p.z / v_scale) + base_z for p in pts_coords]
                gis_cfg.route_info_min_elev = min(real_alts)
                gis_cfg.route_info_max_elev = max(real_alts)
                gis_cfg.route_info_climb = max(real_alts) - min(real_alts)

        self.report({"INFO"}, f"✅ Trazado completado con {total_pts} puntos de control.")
        return {"FINISHED"}


class TRACKMAKER_OT_ProjectCurveToTerrain(bpy.types.Operator):
    """Proyecta todos los puntos de la curva sobre la superficie de la malla de terreno (Raycast BVH)."""

    bl_idname = "track_maker.project_curve_to_terrain"
    bl_label = "Proyectar Curva sobre el Terreno"
    bl_description = "Ajusta la altura Z de cada punto del trazado a la cota exacta de la montaña subyacente"
    bl_options = {"REGISTER", "UNDO"}

    offset_z: bpy.props.FloatProperty(
        name="Desfase sobre Terreno (m)",
        default=0.08,
        min=0.0,
        max=2.0,
        unit="LENGTH",
    )

    def execute(self, context):
        active = context.active_object
        if not active or active.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto de Curva para proyectar.")
            return {"CANCELLED"}

        was_edit = (active.mode == "EDIT")
        if was_edit:
            bpy.ops.object.mode_set(mode="OBJECT")

        gis_cfg = getattr(context.scene, "track_maker_gis", None)
        target_name = getattr(gis_cfg, "target_terrain_name", "TM_Terrain") if gis_cfg else "TM_Terrain"
        terrain_obj = bpy.data.objects.get(target_name)

        if not terrain_obj or terrain_obj.type != "MESH":
            for obj in bpy.data.objects:
                if obj.type == "MESH" and (obj.get("gis_is_terrain", False) or "terrain" in obj.name.lower()):
                    terrain_obj = obj
                    break

        if not terrain_obj or terrain_obj.type != "MESH":
            self.report({"ERROR"}, "No se encontró ningún objeto de terreno tipo MESH en la escena.")
            return {"CANCELLED"}

        from mathutils import bvhtree
        depsgraph = context.evaluated_depsgraph_get()
        bvh = bvhtree.BVHTree.FromObject(terrain_obj, depsgraph)
        mat_terrain = terrain_obj.matrix_world
        inv_terrain = mat_terrain.inverted()
        mat_curve = active.matrix_world
        inv_curve = mat_curve.inverted()

        projected_count = 0
        curve_data = active.data

        for spline in curve_data.splines:
            if spline.type == "BEZIER":
                for bp in spline.bezier_points:
                    pt_world = mat_curve @ bp.co
                    ray_origin_w = Vector((pt_world.x, pt_world.y, 10000.0))
                    ray_dir_w = Vector((0.0, 0.0, -1.0))

                    ray_orig_loc = inv_terrain @ ray_origin_w
                    ray_dir_loc = (inv_terrain.to_3x3() @ ray_dir_w).normalized()

                    hit_loc, _, _, _ = bvh.ray_cast(ray_orig_loc, ray_dir_loc)
                    if hit_loc:
                        hit_world = mat_terrain @ hit_loc
                        new_pt_world = Vector((pt_world.x, pt_world.y, hit_world.z + self.offset_z))
                        delta_co = (inv_curve @ new_pt_world) - bp.co
                        bp.co += delta_co
                        bp.handle_left += delta_co
                        bp.handle_right += delta_co
                        projected_count += 1
            elif spline.type == "POLY":
                for p in spline.points:
                    pt_world = mat_curve @ p.co.to_3d()
                    ray_origin_w = Vector((pt_world.x, pt_world.y, 10000.0))
                    ray_dir_w = Vector((0.0, 0.0, -1.0))

                    ray_orig_loc = inv_terrain @ ray_origin_w
                    ray_dir_loc = (inv_terrain.to_3x3() @ ray_dir_w).normalized()

                    hit_loc, _, _, _ = bvh.ray_cast(ray_orig_loc, ray_dir_loc)
                    if hit_loc:
                        hit_world = mat_terrain @ hit_loc
                        new_pt_world = Vector((pt_world.x, pt_world.y, hit_world.z + self.offset_z))
                        p.co = (inv_curve @ new_pt_world).to_4d()
                        projected_count += 1

        if was_edit:
            bpy.ops.object.mode_set(mode="EDIT")

        self.report({"INFO"}, f"📐 {projected_count} puntos proyectados con éxito sobre '{terrain_obj.name}'.")
        return {"FINISHED"}


class TRACKMAKER_OT_SmoothSpline(bpy.types.Operator):
    """Suaviza el trazado de la curva activa para eliminar sacudidas y mejorar las trazadas de competición."""

    bl_idname = "track_maker.smooth_spline"
    bl_label = "Suavizar Trazado"
    bl_description = "Aplica suavizado a los puntos de control del trazado"
    bl_options = {"REGISTER", "UNDO"}

    iterations: bpy.props.IntProperty(
        name="Iteraciones",
        default=2,
        min=1,
        max=10,
    )

    def execute(self, context):
        active = context.active_object
        if not active or active.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto de Curva.")
            return {"CANCELLED"}

        was_edit = (active.mode == "EDIT")
        if not was_edit:
            bpy.ops.object.mode_set(mode="EDIT")

        bpy.ops.curve.select_all(action="SELECT")
        for _ in range(self.iterations):
            try:
                bpy.ops.curve.smooth()
            except Exception:
                pass

        if not was_edit:
            bpy.ops.object.mode_set(mode="OBJECT")

        self.report({"INFO"}, f"〰️ Trazado suavizado ({self.iterations} pasadas).")
        return {"FINISHED"}


class TRACKMAKER_OT_AutoPlaceABGates(bpy.types.Operator):
    """Coloca automáticamente las puertas de Salida y Meta (AC_AB_START / AC_AB_FINISH) en la curva activa."""

    bl_idname = "track_maker.auto_place_ab_gates"
    bl_label = "Colocar Puertas Salida/Meta AC"
    bl_description = "Crea los objetos AC_AB_START_L/R y AC_AB_FINISH_L/R en los extremos del tramo"
    bl_options = {"REGISTER", "UNDO"}

    gate_width: bpy.props.FloatProperty(
        name="Anchura de Puerta (m)",
        default=16.0,
        min=4.0,
        max=50.0,
        unit="LENGTH",
    )

    def execute(self, context):
        active = context.active_object
        if not active or active.type != "CURVE":
            self.report({"ERROR"}, "Selecciona un objeto de Curva para colocar las puertas.")
            return {"CANCELLED"}

        from ..gis.stage_builder import place_ab_timing_gates_on_curve

        try:
            gates = place_ab_timing_gates_on_curve(context, active, gate_width=self.gate_width)
            if hasattr(context.scene, "track_maker_circuit"):
                context.scene.track_maker_circuit.circuit_type = "HILLCLIMB_AB"

            self.report(
                {"INFO"},
                f"🏁 Puertas de tramo creadas en '{active.name}': {gates[0].name}, {gates[2].name}.",
            )
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error colocando puertas AC: {e}")
            return {"CANCELLED"}


classes = (
    TRACKMAKER_OT_CreateRoadSpline,
    TRACKMAKER_OT_ToggleSplineCyclic,
    TRACKMAKER_OT_SetCurveTilt,
    TRACKMAKER_OT_AutoBankCurve,
    TRACKMAKER_OT_StartSurfaceDraw,
    TRACKMAKER_OT_FinishSurfaceDraw,
    TRACKMAKER_OT_ProjectCurveToTerrain,
    TRACKMAKER_OT_SmoothSpline,
    TRACKMAKER_OT_AutoPlaceABGates,
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

