"""Herramientas de gestión de cámara y visor 3D para escenarios GIS a escala real (kilométricos).

Resuelve el problema de mallas invisibles o cortadas en Blender debido al plano de recorte
lejano por defecto (clip_end = 1000m), ajustándolo automáticamente al tamaño del terreno
y enfocando la vista en la geometría generada.
"""

from __future__ import annotations
import bpy


def adjust_viewport_clipping(context, max_dimension_m: float):
    """Ajusta automáticamente el límite de distancia (clip_end) en visores 3D y cámaras activas.

    En terrenos reales de 5 km, 15 km o 30 km, el plano de corte por defecto de Blender (1,000m)
    corta la malla haciéndola invisible o transparente al hacer zoom hacia atrás.
    Esta función expande el plano lejano para cubrir toda la escena sin artefactos de precisión.
    """
    required_clip = max(2000.0, float(max_dimension_m) * 3.0)

    # 1. Ajustar todas las vistas 3D abiertas
    screen = getattr(context, "screen", None)
    if screen:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        if space.clip_end < required_clip:
                            space.clip_end = required_clip

    # 2. Ajustar la cámara activa si existe
    cam = context.scene.camera
    if cam and hasattr(cam.data, "clip_end") and cam.data.clip_end < required_clip:
        cam.data.clip_end = required_clip


def frame_active_object(context):
    """Enfoca y centra la vista 3D en el objeto activo seleccionado."""
    screen = getattr(context, "screen", None)
    if not screen:
        return

    for area in screen.areas:
        if area.type == "VIEW_3D":
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            if region:
                try:
                    with context.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_selected()
                except Exception:
                    pass
                break


class TRACKMAKER_OT_FrameGISView(bpy.types.Operator):
    """Ajusta el visor 3D (clip_end) y enfoca el terreno o carretera activa."""

    bl_idname = "track_maker.frame_gis_view"
    bl_label = "Enfocar Terreno / Pista en Visor 3D"
    bl_description = "Aumenta la distancia de visión para evitar que el terreno se corte y centra la cámara"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active = context.active_object
        max_dim = 15000.0
        if active:
            max_dim = max(active.dimensions.x, active.dimensions.y, 5000.0)

        adjust_viewport_clipping(context, max_dim)
        frame_active_object(context)
        self.report({"INFO"}, f"Visor 3D ajustado (distancia de visión adaptada a escala real).")
        return {"FINISHED"}


classes = (
    TRACKMAKER_OT_FrameGISView,
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
