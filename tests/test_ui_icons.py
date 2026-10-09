"""Prueba de integridad de iconos de UI para evitar TypeErrors en UILayout.operator() y UILayout.label()."""

import os
import re
import unittest

# Conjunto de iconos válidos de Blender utilizados en la extensión
VALID_BLENDER_ICONS = {
    "ADD",
    "AUTO",
    "BRUSH_DATA",
    "CANCEL",
    "CHECKBOX_HLT",
    "CHECKMARK",
    "CURVE_DATA",
    "CURVE_PATH",
    "DRIVER_DISTANCE",
    "DRIVER_ROTATIONAL_DIFFERENCE",
    "DUPLICATE",
    "EMPTY_DATA",
    "ERROR",
    "EXPORT",
    "FILE_FOLDER",
    "FILE_REFRESH",
    "GRAPH",
    "GREASEPENCIL",
    "IMPORT",
    "INFO",
    "IPO_BEZIER",
    "LOOP_FORWARDS",
    "MESH_ICOSPHERE",
    "MOD_BEVEL",
    "MOD_EDGESPLIT",
    "NODETREE",
    "ORIENTATION_GIMBAL",
    "PANEL_CLOSE",
    "PHYSICS",
    "PINNED",
    "PLAY",
    "PRESET",
    "SMOOTHCURVE",
    "SNAP_FACE",
    "SNAP_INCREMENT",
    "SNAP_ON",
    "SNAP_VOLUME",
    "SORTTIME",
    "SYSTEM",
    "TIME",
    "TOOL_SETTINGS",
    "TRACKING",
    "TRACKING_FORWARDS",
    "TRASH",
    "URL",
    "VIEWZOOM",
    "VIEW_CAMERA",
    "WORLD",
    "X",
}


class TestUIIcons(unittest.TestCase):

    def test_all_ui_icons_are_valid(self):
        """Verifica que ningún archivo de UI utilice nombres de iconos inexistentes en Blender."""
        ui_dir = os.path.join(os.path.dirname(__file__), "..", "track_maker", "ui")
        invalid_icons = {}

        for root, _, files in os.walk(ui_dir):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", encoding="utf-8") as fp:
                        content = fp.read()
                    matches = re.findall(r'icon=[\'"]([A-Z0-9_]+)[\'"]', content)
                    for ico in matches:
                        if ico not in VALID_BLENDER_ICONS:
                            invalid_icons.setdefault(ico, []).append(f)

        self.assertEqual(
            invalid_icons,
            {},
            f"Se encontraron iconos no válidos en la UI: {invalid_icons}",
        )


if __name__ == "__main__":
    unittest.main()
