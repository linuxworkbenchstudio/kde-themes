"""Each part turns a pack into files: build(pack) -> {relative path: str | bytes | Link}.

Parts are added here as they move over from Waypoint and Vice Horizon; see DESIGN.md for the list.
"""
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent.parent / "templates"

from . import aurorae, brand, docs, cursors, fastfetch, gtk, icons, kde_colors, konsole, kvantum, lookandfeel, panel_layout, programs, panel_looks, plasma_style, widgets  # noqa: E402

PARTS = {
    "kde-colors": kde_colors,
    "konsole": konsole,
    "plasma-style": plasma_style,
    "aurorae": aurorae,
    "cursors": cursors,
    "kvantum": kvantum,
    "fastfetch": fastfetch,
    "gtk": gtk,
    "icons": icons,
    "brand": brand,
    "panel-looks": panel_looks,
    "panel-layout": panel_layout,
    "widgets": widgets,
    "lookandfeel": lookandfeel,
    "programs": programs,
    "docs": docs,
}
