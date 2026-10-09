"""Generador de árbol de Geometry Nodes (Blender 4.2+) para previsualización interactiva en tiempo real."""

import bpy


def get_or_create_road_geo_nodes_tree() -> bpy.types.GeometryNodeTree:
    """Crea o recupera el árbol de Geometry Nodes procedural para carreteras."""
    tree_name = "TM_Road_GeoNodes_Generator"

    if tree_name in bpy.data.node_groups:
        return bpy.data.node_groups[tree_name]

    # Crear árbol de nodos para Blender 4.x
    tree = bpy.data.node_groups.new(name=tree_name, type="GeometryNodeTree")

    # Configuración de interfaz (Sockets) compatible con Blender 4.0+
    if hasattr(tree, "interface"):
        # API Blender 4.0+
        tree.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        tree.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        
        sock_width = tree.interface.new_socket(name="Anchura Calzada", in_out="INPUT", socket_type="NodeSocketFloat")
        sock_width.default_value = 9.0
        sock_width.min_value = 2.0
        sock_width.max_value = 50.0

        sock_res = tree.interface.new_socket(name="Paso Muestreo", in_out="INPUT", socket_type="NodeSocketFloat")
        sock_res.default_value = 0.5
        sock_res.min_value = 0.1
        sock_res.max_value = 5.0
    else:
        # Fallback para versiones anteriores
        tree.inputs.new("NodeSocketGeometry", "Geometry")
        tree.outputs.new("NodeSocketGeometry", "Geometry")

    # Nodos internos
    nodes = tree.nodes
    links = tree.links

    input_node = nodes.new("NodeGroupInput")
    input_node.location = (-400, 0)

    output_node = nodes.new("NodeGroupOutput")
    output_node.location = (600, 0)

    # Resample Curve
    resample_node = nodes.new("GeometryNodeResampleCurve")
    resample_node.location = (-200, 100)
    resample_node.mode = "LENGTH"

    # Perfil: Curve Line primitive
    profile_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    profile_line.location = (-200, -150)

    # Control de anchura: Math divide / multiply para el perfil
    math_half = nodes.new("ShaderNodeMath")
    math_half.operation = "DIVIDE"
    math_half.location = (-400, -150)
    math_half.inputs[1].default_value = 2.0

    math_neg = nodes.new("ShaderNodeMath")
    math_neg.operation = "MULTIPLY"
    math_neg.location = (-300, -250)
    math_neg.inputs[1].default_value = -1.0

    # Combine XYZ para extremo inicial y final del perfil
    comb_start = nodes.new("ShaderNodeCombineXYZ")
    comb_start.location = (-100, -300)

    comb_end = nodes.new("ShaderNodeCombineXYZ")
    comb_end.location = (-100, -150)

    # Curve to Mesh
    curve_to_mesh = nodes.new("GeometryNodeCurveToMesh")
    curve_to_mesh.location = (150, 0)

    # Set Shade Smooth
    smooth_node = nodes.new("GeometryNodeSetShadeSmooth")
    smooth_node.location = (350, 0)

    # Conexiones de nodos
    # 1. Geometría a Resample
    links.new(input_node.outputs["Geometry"], resample_node.inputs["Curve"])

    # 2. Paso de longitud desde Input
    if "Paso Muestreo" in input_node.outputs:
        links.new(input_node.outputs["Paso Muestreo"], resample_node.inputs["Length"])
    else:
        resample_node.inputs["Length"].default_value = 0.5

    # 3. Anchura a mitad positiva y negativa
    if "Anchura Calzada" in input_node.outputs:
        links.new(input_node.outputs["Anchura Calzada"], math_half.inputs[0])
    links.new(math_half.outputs["Value"], comb_end.inputs["X"])
    links.new(math_half.outputs["Value"], math_neg.inputs[0])
    links.new(math_neg.outputs["Value"], comb_start.inputs["X"])

    # 4. Línea de perfil
    links.new(comb_start.outputs["Vector"], profile_line.inputs["Start"])
    links.new(comb_end.outputs["Vector"], profile_line.inputs["End"])

    # 5. Curve to Mesh
    links.new(resample_node.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    links.new(profile_line.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

    # 6. Smooth y Salida
    links.new(curve_to_mesh.outputs["Mesh"], smooth_node.inputs["Geometry"])
    links.new(smooth_node.outputs["Geometry"], output_node.inputs["Geometry"])

    return tree


class TRACKMAKER_OT_AttachRoadGeoNodes(bpy.types.Operator):
    """Añade o actualiza el modificador de Geometry Nodes para previsualizar la carretera interactiva."""

    bl_idname = "track_maker.attach_road_geo_nodes"
    bl_label = "Previsualizar con Geometry Nodes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != "CURVE":
            self.report({"ERROR"}, "Selecciona una Curva para aplicar Geometry Nodes.")
            return {"CANCELLED"}

        road_cfg = context.scene.track_maker_road

        tree = get_or_create_road_geo_nodes_tree()

        # Buscar si ya existe el modificador
        mod = None
        for m in obj.modifiers:
            if m.type == "NODES" and m.node_group == tree:
                mod = m
                break

        if not mod:
            mod = obj.modifiers.new(name="TM_Road_Generator", type="NODES")
            mod.node_group = tree

        # Actualizar valores
        if "Socket_2" in mod:  # Anchura
            mod["Socket_2"] = road_cfg.road_width
        if "Socket_3" in mod:  # Paso
            mod["Socket_3"] = road_cfg.physics_subdivision_y

        self.report({"INFO"}, f"Geometry Nodes aplicado a '{obj.name}' (Previsualización en tiempo real activa).")
        return {"FINISHED"}


classes = (TRACKMAKER_OT_AttachRoadGeoNodes,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

