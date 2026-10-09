"""Panel de Escenario, Infraestructura y 'Mexico Pack' en el Sidebar de Blender."""

import bpy
from ..core.constants import BL_CATEGORY


class TRACKMAKER_PT_PropsPanel(bpy.types.Panel):
    """Subpanel para generación de barreras, señalética SCT, iluminación y edificios mexicanos."""

    bl_label = "Escenario & Mexico Pack"
    bl_idname = "TRACKMAKER_PT_props_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = BL_CATEGORY
    bl_parent_id = "TRACKMAKER_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props_cfg = scene.track_maker_props

        # ---------------------------------------------------------
        # 1. BARRERAS Y CONTENCIONES VIALES (1WALL_)
        # ---------------------------------------------------------
        box_bar = layout.box()
        box_bar.label(text="Barreras y Contenciones (1WALL_ AC)", icon="MOD_ARRAY")

        col_bar = box_bar.column(align=True)
        col_bar.prop(props_cfg, "barrier_type", text="Modelo")
        col_bar.prop(props_cfg, "barrier_side", text="Ubicación")
        col_bar.prop(props_cfg, "barrier_offset", text="Desfase Lateral")

        row_b_btns = box_bar.row(align=True)
        row_b_btns.operator("track_maker.populate_barriers", text="🚧 Generar Barreras", icon="ADD")
        row_b_btns.operator("track_maker.clear_barriers", text="Limpiar", icon="TRASH")

        # ---------------------------------------------------------
        # 2. SEÑALÉTICA VIAL OFICIAL SCT
        # ---------------------------------------------------------
        box_sign = layout.box()
        box_sign.label(text="Señalética Oficial SCT (México)", icon="DRIVER_DISTANCE")

        col_sign = box_sign.column(align=True)
        col_sign.prop(props_cfg, "speed_limit", text="Velocidad Máxima")
        col_sign.prop(props_cfg, "gantry_interval", text="Paso de Pórticos")

        row_s_btns = box_sign.row(align=True)
        row_s_btns.operator("track_maker.populate_signage", text="🚸 Generar Señalética SCT", icon="ADD")
        row_s_btns.operator("track_maker.clear_signage", text="Limpiar", icon="TRASH")

        # ---------------------------------------------------------
        # 3. ALUMBRADO DE AUTOPISTA (CSP COMPATIBLE)
        # ---------------------------------------------------------
        box_light = layout.box()
        box_light.label(text="Luminarias de Autopista (Nocturno CSP)", icon="LIGHT_SUN")

        col_light = box_light.column(align=True)
        col_light.prop(props_cfg, "light_placement", text="Posición")
        col_light.prop(props_cfg, "light_spacing", text="Separación")

        row_l_btns = box_light.row(align=True)
        row_l_btns.operator("track_maker.populate_lighting", text="💡 Generar Luminarias", icon="ADD")
        row_l_btns.operator("track_maker.clear_lighting", text="Limpiar", icon="TRASH")

        # ---------------------------------------------------------
        # 4. EDIFICIOS TEMÁTICOS (MEXICO PACK)
        # ---------------------------------------------------------
        box_bld = layout.box()
        box_bld.label(text="Poblado Mexicano (OXXO, Pemex, Bodegas)", icon="COMMUNITY")

        col_bld = box_bld.column(align=True)
        col_bld.prop(props_cfg, "building_density", text="Densidad", slider=True)
        col_bld.prop(props_cfg, "building_setback", text="Retranqueo (m)")
        col_bld.prop(props_cfg, "building_spacing", text="Paso entre Lotes")

        box_bld.label(text="Incluye: OXXO, Pemex, Naves y Casas con Tinaco", icon="INFO")

        row_bld_btns = box_bld.row(align=True)
        row_bld_btns.operator("track_maker.populate_buildings", text="🏪 Poblar Edificios", icon="ADD")
        row_bld_btns.operator("track_maker.clear_buildings", text="Limpiar", icon="TRASH")

        # ---------------------------------------------------------
        # 5. GOOGLE 3D TILES Y FOTOGRAMETRÍA EXTERNA
        # ---------------------------------------------------------
        box_geo = layout.box()
        box_geo.label(text="Fotogrametría Google 3D Tiles", icon="WORLD")

        col_geo = box_geo.column(align=True)
        col_geo.prop(props_cfg, "google_maps_api_key", text="API Key")

        row_g_btns = box_geo.column(align=True)
        row_g_btns.operator("track_maker.import_google_3d_tiles", text="🌐 Conectar Google 3D Tiles", icon="IMPORT")
        row_g_btns.operator("track_maker.align_external_photogrammetry", text="🎯 Alinear Malla Externa (Blosm)", icon="SNAP_ON")


classes = (TRACKMAKER_PT_PropsPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
