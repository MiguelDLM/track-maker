"""Generador de perfiles transversales para carreteras, bordillos, banquetas y muros."""

import math


class RoadProfilePoint:
    """Representa un vértice en la sección transversal 2D de la carretera."""

    def __init__(self, offset_x: float, offset_z: float, u_coord: float, surface_type: str, mat_index: int):
        self.offset_x = offset_x
        self.offset_z = offset_z
        self.u_coord = u_coord
        self.surface_type = surface_type  # 'ROAD', 'KERB', 'SIDEWALK', 'WALL'
        self.mat_index = mat_index


def generate_cross_section_profile(
    road_width: float = 9.0,
    subdivisions_x: int = 6,
    has_crown: bool = True,
    crown_height: float = 0.06,
    has_kerbs: bool = True,
    kerb_width: float = 0.40,
    kerb_height: float = 0.12,
    has_sidewalks: bool = False,
    sidewalk_width: float = 1.80,
    has_walls: bool = False,
    wall_height: float = 0.90,
    for_physics_only: bool = False,
) -> list[RoadProfilePoint]:
    """Genera la lista ordenada de puntos (de izquierda a derecha) que definen el perfil transversal."""
    profile: list[RoadProfilePoint] = []
    half_width = road_width / 2.0

    # 1. PUNTOS DEL ASFALTO PRINCIPAL (ROAD)
    road_points: list[RoadProfilePoint] = []
    num_pts = max(2, subdivisions_x + 1)

    for i in range(num_pts):
        t = i / (num_pts - 1)  # 0.0 a 1.0
        x = -half_width + (t * road_width)

        # Bombeo central parabólico z(x) = H * (1 - (x / half_width)^2)
        if has_crown and crown_height > 0.0:
            norm_x = x / half_width
            z = crown_height * (1.0 - (norm_x * norm_x))
        else:
            z = 0.0

        road_points.append(
            RoadProfilePoint(
                offset_x=x,
                offset_z=z,
                u_coord=t,
                surface_type="ROAD",
                mat_index=0,
            )
        )

    # Si es solo para la malla física pura (1ROAD_), devolvemos únicamente el asfalto (y opcional bordillos)
    if for_physics_only:
        return road_points

    # 2. BORDILLOS / PIANOS / BANQUETAS (KERB)
    left_kerb: list[RoadProfilePoint] = []
    right_kerb: list[RoadProfilePoint] = []

    if has_kerbs and kerb_width > 0.0:
        # Bordillo izquierdo: desde el borde exterior del bordillo hasta el borde del asfalto
        edge_x_l = -half_width
        outer_x_l = -half_width - kerb_width

        left_kerb.append(
            RoadProfilePoint(
                offset_x=outer_x_l,
                offset_z=kerb_height,
                u_coord=0.0,
                surface_type="KERB",
                mat_index=1,
            )
        )
        left_kerb.append(
            RoadProfilePoint(
                offset_x=edge_x_l,
                offset_z=kerb_height,
                u_coord=0.5,
                surface_type="KERB",
                mat_index=1,
            )
        )
        # Caída vertical / chaflán al asfalto
        left_kerb.append(
            RoadProfilePoint(
                offset_x=edge_x_l,
                offset_z=0.0,
                u_coord=1.0,
                surface_type="KERB",
                mat_index=1,
            )
        )

        # Bordillo derecho: desde el borde del asfalto hacia el exterior
        edge_x_r = half_width
        outer_x_r = half_width + kerb_width

        right_kerb.append(
            RoadProfilePoint(
                offset_x=edge_x_r,
                offset_z=0.0,
                u_coord=0.0,
                surface_type="KERB",
                mat_index=1,
            )
        )
        right_kerb.append(
            RoadProfilePoint(
                offset_x=edge_x_r,
                offset_z=kerb_height,
                u_coord=0.5,
                surface_type="KERB",
                mat_index=1,
            )
        )
        right_kerb.append(
            RoadProfilePoint(
                offset_x=outer_x_r,
                offset_z=kerb_height,
                u_coord=1.0,
                surface_type="KERB",
                mat_index=1,
            )
        )

    # 3. BANQUETAS PEATONALES (SIDEWALK)
    left_sidewalk: list[RoadProfilePoint] = []
    right_sidewalk: list[RoadProfilePoint] = []

    if has_sidewalks and sidewalk_width > 0.0:
        sw_start_l = -half_width - (kerb_width if has_kerbs else 0.0)
        sw_end_l = sw_start_l - sidewalk_width
        sw_z = kerb_height if has_kerbs else 0.15

        left_sidewalk.append(
            RoadProfilePoint(
                offset_x=sw_end_l,
                offset_z=sw_z,
                u_coord=0.0,
                surface_type="SIDEWALK",
                mat_index=2,
            )
        )
        left_sidewalk.append(
            RoadProfilePoint(
                offset_x=sw_start_l,
                offset_z=sw_z,
                u_coord=1.0,
                surface_type="SIDEWALK",
                mat_index=2,
            )
        )

        sw_start_r = half_width + (kerb_width if has_kerbs else 0.0)
        sw_end_r = sw_start_r + sidewalk_width

        right_sidewalk.append(
            RoadProfilePoint(
                offset_x=sw_start_r,
                offset_z=sw_z,
                u_coord=0.0,
                surface_type="SIDEWALK",
                mat_index=2,
            )
        )
        right_sidewalk.append(
            RoadProfilePoint(
                offset_x=sw_end_r,
                offset_z=sw_z,
                u_coord=1.0,
                surface_type="SIDEWALK",
                mat_index=2,
            )
        )

    # 4. BARRERAS / MUROS (WALL)
    left_wall: list[RoadProfilePoint] = []
    right_wall: list[RoadProfilePoint] = []

    if has_walls and wall_height > 0.0:
        w_base_x_l = (
            -half_width
            - (kerb_width if has_kerbs else 0.0)
            - (sidewalk_width if has_sidewalks else 0.0)
        )
        w_base_z_l = kerb_height if (has_kerbs or has_sidewalks) else 0.0

        left_wall.append(
            RoadProfilePoint(
                offset_x=w_base_x_l,
                offset_z=w_base_z_l + wall_height,
                u_coord=0.0,
                surface_type="WALL",
                mat_index=3,
            )
        )
        left_wall.append(
            RoadProfilePoint(
                offset_x=w_base_x_l,
                offset_z=w_base_z_l,
                u_coord=1.0,
                surface_type="WALL",
                mat_index=3,
            )
        )

        w_base_x_r = (
            half_width
            + (kerb_width if has_kerbs else 0.0)
            + (sidewalk_width if has_sidewalks else 0.0)
        )
        w_base_z_r = kerb_height if (has_kerbs or has_sidewalks) else 0.0

        right_wall.append(
            RoadProfilePoint(
                offset_x=w_base_x_r,
                offset_z=w_base_z_r,
                u_coord=0.0,
                surface_type="WALL",
                mat_index=3,
            )
        )
        right_wall.append(
            RoadProfilePoint(
                offset_x=w_base_x_r,
                offset_z=w_base_z_r + wall_height,
                u_coord=1.0,
                surface_type="WALL",
                mat_index=3,
            )
        )

    # Ensamblar el perfil completo ordenado de extremo izquierdo a extremo derecho
    profile = left_wall + left_sidewalk + left_kerb + road_points + right_kerb + right_sidewalk + right_wall
    return profile
