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


classes = (
    TRACKMAKER_OT_CreateRoadSpline,
    TRACKMAKER_OT_ToggleSplineCyclic,
    TRACKMAKER_OT_SetCurveTilt,
    TRACKMAKER_OT_AutoBankCurve,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
