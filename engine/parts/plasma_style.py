"""Plasma Style: share/plasma/desktoptheme/<name>/ - Waypoint's (Breeze-based) SVGs, recoloured."""
import gzip
import json

from ..pack import Edition, Pack
from ..recolour import Recolour, resolver
from . import TEMPLATES, kde_colors

CREDITS = """{Name} Plasma Style, part of {Name} for KDE Plasma 6 ({brand}).
Based on KDE's Breeze Plasma Style, (C) the KDE Visual Design Group and contributors.
Licence: GNU Library General Public License, version 2 or later (LGPL-2.0-or-later); the full
text is in COPYING next to this file.
"""


def hide_open_widget_line(svg: str) -> str:
    """No line under a top-panel widget whose popup is open (every theme).

    Plasma marks an open panel widget with widgets/tabbar's north-active-tab frame; its bottom edge
    is a 3 px accent line that, on a floating panel, lands below the bar. The bottom piece and its
    two corners are made transparent; the elements stay, so the frame keeps its size.
    (Vice Horizon 1.8's fix; Waypoint 0.5.0 hid only the middle piece.)"""
    import re
    for gid in ("north-active-tab-bottom", "north-active-tab-bottomleft", "north-active-tab-bottomright"):
        i = svg.index(f'id="{gid}"')
        start = svg.rfind("<g", 0, i)
        end = svg.index("</g>", i)
        group = svg[start:end]
        group = re.sub(r'(class="ColorScheme-ButtonFocus"[^>]*?)fill-opacity:1', r"\1fill-opacity:0", group)
        group = re.sub(r'(style="fill:currentColor;)fill-opacity:1([^"]*"[^>]*class="ColorScheme-ButtonFocus")',
                       r"\1fill-opacity:0\2", group)
        svg = svg[:start] + group + svg[end:]
    return svg


def svg_text(data: bytes, gz: bool) -> str:
    return (gzip.decompress(data) if gz else data).decode("utf-8")


def build_edition(pack: Pack, ed: Edition) -> dict:
    name = pack.file_name("plasma_style", ed)
    rc = Recolour(ed.raw.get("recolour"), resolver(pack, ed))
    src = TEMPLATES / "plasma-style" / ed.template
    out = {}
    for f in sorted(p for p in src.rglob("*") if p.is_file()):
        rel = f.relative_to(src).as_posix()
        data = f.read_bytes()
        fix = rel == "widgets/tabbar.svgz"
        if f.suffix in (".svgz", ".svg") and (rc.active or fix):
            gz = f.suffix == ".svgz"
            text = rc.text(svg_text(data, gz), f"plasma/{rel}")
            if fix:
                text = hide_open_widget_line(text)
            data = gzip.compress(text.encode("utf-8"), compresslevel=9, mtime=0) if gz else text.encode("utf-8")
        out[f"plasma/desktoptheme/{name}/{rel}"] = data
    meta = {"KPlugin": {"Authors": [{"Name": pack.brand}, {"Name": "Based on Breeze by the KDE Visual Design Group"}],
                        "Category": "", "Description": pack.describe("plasma", ed), "EnabledByDefault": True,
                        "Id": name, "License": "LGPL-2.0-or-later", "Name": pack.display(ed),
                        "Version": pack.version, "Website": pack.website},
            "X-Plasma-API-Minimum-Version": "6.0", "KPackageStructure": "Plasma/Theme"}
    base = f"plasma/desktoptheme/{name}/"
    out[base + "metadata.json"] = json.dumps(meta, indent=2) + "\n"
    out[base + "colors"] = kde_colors.color_scheme(pack, ed)
    out[base + "COPYING"] = (TEMPLATES / "licences/LGPL-2.0-or-later.txt").read_bytes()
    out[base + "CREDITS"] = CREDITS.format(Name=pack.name, brand=pack.brand)
    return out


def build(pack: Pack) -> dict:
    out = {}
    for ed in pack.editions.values():
        out.update(build_edition(pack, ed))
    return out
