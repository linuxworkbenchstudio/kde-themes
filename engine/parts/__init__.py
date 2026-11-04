"""Each part turns a pack into files: build(pack) -> {relative path: text}.

Parts are added here as they move over from Waypoint and Vice Horizon; see DESIGN.md for the list.
"""
from . import kde_colors, konsole

PARTS = {
    "kde-colors": kde_colors,
    "konsole": konsole,
}
