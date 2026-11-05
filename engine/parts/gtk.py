"""GTK 3 and GTK 4 for GTK apps on Plasma: gtk/<name>/{gtk-3.0,gtk-4.0}/ and index.theme.

GTK's own themes (GTK 3.24 Adwaita, GTK 4.16 Default; templates/gtk/, LGPL-2.1-or-later) are
compiled with the pack's colours, so every widget, state and shade comes from GTK's own rules:

  [edition.<id>.gtk.vars]       (default: DEFAULT_VARS, from the roles) GTK colour variables for both versions ($base_color, $bg_color,
                                $selected_bg_color ...); a variable a version doesn't have is skipped
  [edition.<id>.gtk."gtk-3.0"]  more variables for one version only (also "gtk-4.0")
      values: a role or colour name, #RRGGBB, or SCSS ("darken($role_border, 8%)"); every role is
      available to SCSS as $role_<name>, every pack colour as $colour_<name>
  [theme.gtk.replace]           "gtk-4.0/_common.scss" = [[old, new], ...]: edits to GTK's own files
  [theme.gtk.png]               recolour GTK 3's pre-rendered slider and text-handle images:
                                accent_hue, accent_saturation, neutral_hue, neutral_saturation
  packs/<pack>/gtk/<version>.scss           house details, compiled in (sees $variant and $role_*)
  packs/<pack>/gtk/<version>-<edition>.css  house details appended as written

gtk.css is the edition; gtk-dark.css is the dark edition, for apps that ask for dark. Only the
images the stylesheets use are shipped. Needs Dart Sass 1.78.0 (the version the releases were
compiled with; 1.79 rounds colours differently): $SASS, `sass` on PATH, or .cache/dart-sass/sass
(python3 tools/get_sass.py fetches it).
"""
from __future__ import annotations

import colorsys
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import png
from ..colour import is_hex
from ..pack import Pack
from ..recolour import resolver
from . import TEMPLATES

SASS_VERSION = "1.78.0"
ENTRY = {"gtk-3.0": {"light": "gtk-contained.scss", "dark": "gtk-contained-dark.scss"},
         "gtk-4.0": {"light": "Default-light.scss", "dark": "Default-dark.scss"}}
ROOT = Path(__file__).resolve().parent.parent.parent


def sass() -> str:
    for c in (os.environ.get("SASS"), shutil.which("sass"), str(ROOT / ".cache/dart-sass/sass")):
        if c and Path(c).is_file():
            v = subprocess.run([c, "--version"], capture_output=True, text=True).stdout.strip()
            if v == SASS_VERSION:
                return c
            raise RuntimeError(f"{c} is Dart Sass {v}; the GTK part needs {SASS_VERSION} "
                               "(python3 tools/get_sass.py, or set SASS)")
    raise RuntimeError(f"Dart Sass {SASS_VERSION} not found: python3 tools/get_sass.py, or set SASS")


def _value(v, resolve) -> str:
    try:
        return resolve(v)
    except KeyError:
        return str(v)                           # SCSS


def _colours(text: str, values: dict) -> str:
    def sub(m):
        name = m.group(1)
        return f"${name}: {values[name]};" if name in values else m.group(0)
    return re.sub(r"^\$([a-z_]+):[^\n]*;", sub, text, flags=re.M)


def _recolour_png(data: bytes, spec: dict) -> bytes:
    """Adwaita's greys -> the pack's neutral hue (same lightness); Adwaita blue -> the accent hue."""
    w, h, rows = png.read(data)
    ah, as_ = spec["accent_hue"] / 360, spec["accent_saturation"]
    nh, ns = spec["neutral_hue"] / 360, spec["neutral_saturation"]
    out = []
    for row in rows:
        new = []
        for r, g, b, a in row:
            if a == 0:
                new.append((r, g, b, a))
                continue
            hh, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if s > 0.3 and 0.5 < hh < 0.72:
                hh, s = ah, as_
            elif s < 0.2:
                hh, s = nh, min(ns, s + 0.12) if l < 0.97 else 0
            nr, ng, nb = colorsys.hls_to_rgb(hh, l, s)
            new.append((round(nr * 255), round(ng * 255), round(nb * 255), a))
        out.append(new)
    return png.write(w, h, out)


# GTK variables for a pack without its own [edition.<id>.gtk.vars]: from its roles
DEFAULT_VARS = {
    "base_color": "view_bg", "text_color": "text", "bg_color": "window_bg", "fg_color": "text",
    "selected_fg_color": "selection_fg", "selected_bg_color": "selection_bg",
    "selected_borders_color": "darken($selected_bg_color, 12%)", "borders_color": "border",
    "alt_borders_color": "if($variant == 'light', darken($role_border, 8%), lighten($role_border, 6%))",
    "link_color": "link", "link_visited_color": "visited", "headerbar_color": "header_bg",
    "headerbar_bg_color": "header_bg", "menu_color": "surface_raised", "popover_bg_color": "surface_raised",
    "popover_hover_color": "hover_bg", "menu_selected_color": "hover_bg", "scrollbar_slider_active_color": "accent",
    "warning_color": "neutral", "error_color": "negative", "success_color": "positive",
    "destructive_color": "destructive_bg", "osd_fg_color": "complementary_fg", "osd_text_color": "complementary_fg",
    "osd_bg_color": "transparentize($role_osd_bg, 0.1)", "sidebar_bg_color": "sidebar_bg",
    "drop_target_color": "accent", "insensitive_fg_color": "text_disabled", "suggested_bg_color": "suggested_bg",
    "suggested_border_color": "darken($role_suggested_bg, 10%)", "checkradio_bg_color": "$selected_bg_color",
    "checkradio_borders_color": "darken($checkradio_bg_color, 15%)",
    "focus_border_color": "transparentize($role_accent, 0.35)",
}


def _compile(pack: Pack, ed, version: str, binary: str) -> str:
    spec = ed.raw.get("gtk", {})
    resolve = resolver(pack, ed)
    values = {k: _value(v, resolve) for k, v in spec.get("vars", DEFAULT_VARS).items()}
    values.update({k: _value(v, resolve) for k, v in spec.get(version, {}).items()})
    replace = pack.raw.get("theme", {}).get("gtk", {}).get("replace", {})
    layer = pack.root / "gtk" / f"{version}.scss"
    variant = "dark" if ed.template == "dark" else "light"
    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / version
        shutil.copytree(TEMPLATES / "gtk" / version, work, ignore=shutil.ignore_patterns("assets"))
        for name, edits in replace.items():
            d, f = name.split("/", 1)
            if d != version:
                continue
            text = (work / f).read_text(encoding="utf-8")
            for old, new in edits:
                if old not in text:
                    raise ValueError(f"[theme.gtk.replace] {name}: {old!r} not found")
                text = text.replace(old, new)
            (work / f).write_text(text, encoding="utf-8")
        tokens = "".join(f"$role_{k}: {v};\n" for k, v in ed.roles.items())
        tokens += "".join(f"$colour_{k}: {v};\n" for k, v in pack.colours.items())
        c = (work / "_colors.scss").read_text(encoding="utf-8")
        (work / "_colors.scss").write_text(tokens + _colours(c, values), encoding="utf-8")
        entry = work / ENTRY[version][variant]
        if layer.is_file():
            shutil.copy(layer, work / "_pack-layer.scss")
            entry.write_text(entry.read_text(encoding="utf-8") + "@import 'pack-layer';\n", encoding="utf-8")
        res = subprocess.run([binary, "--no-source-map", "--quiet", "--style=expanded", str(entry)],
                             capture_output=True, text=True)
        if res.returncode:
            raise RuntimeError(f"sass failed for {pack.id} {ed.id} {version}:\n{res.stderr}")
        return res.stdout


CREDITS = """{Name} {Edition} — GTK 3 and GTK 4 theme, part of {Name} for KDE Plasma 6 ({Brand}).

Based on GTK's own themes: GTK 3.24 Adwaita (gtk-3.0) and GTK 4.16 Default (gtk-4.0),
compiled with the {Name} colours, plus {Name} details. The widget images in the assets folders
come from GTK.
GTK and its themes: (C) the GTK Team and contributors, https://gitlab.gnome.org/GNOME/gtk
Licence: GNU Lesser General Public License, version 2.1 or later (LGPL-2.1-or-later); the
full text is in COPYING next to this file.
"""

INDEX = """[Desktop Entry]
Type=X-GNOME-Metatheme
Name={display}
Comment={display} for GTK 3 and GTK 4 apps on KDE Plasma
Encoding=UTF-8

[X-GNOME-Metatheme]
GtkTheme={name}
IconTheme={icons}
CursorTheme={cursors}
"""


def build(pack: Pack) -> dict:
    binary = sass()
    theme = pack.raw.get("theme", {}).get("gtk", {})
    eds = list(pack.editions.values())
    dark = next((e for e in eds if e.template == "dark"), eds[0])
    licence = (TEMPLATES / "licences" / "LGPL-2.1-or-later.txt").read_text(encoding="utf-8")
    css = {(e.id, v): _compile(pack, e, v, binary) for e in eds for v in ENTRY}
    out = {}
    for ed in eds:
        name = pack.file_name("gtk", ed)
        base = f"gtk/{name}/"
        for version in ENTRY:
            d = base + version + "/"
            files = {"gtk.css": ed, "gtk-dark.css": dark}
            used = set()
            for fname, src in files.items():
                key = "gtk3_header" if version == "gtk-3.0" else "gtk4_header"
                head = src.text[key].format(Name=pack.name, Edition=src.name, Theme=ed.name, Brand=pack.brand,
                                            Version=pack.version, version=version, file=fname)
                layer = pack.root / "gtk" / f"{version}-{src.id}.css"
                text = head + css[(src.id, version)] + (layer.read_text(encoding="utf-8") if layer.is_file() else "")
                out[d + fname] = text
                used |= set(re.findall(r'url\("assets/([^"]+)"\)', text))
            for a in sorted(used):
                data = (TEMPLATES / "gtk" / version / "assets" / a).read_bytes()
                if version == "gtk-3.0" and "png" in theme and a.endswith(".png") and a.startswith(("slider-", "text-select-")):
                    data = _recolour_png(data, theme["png"])
                out[d + "assets/" + a] = data
            out[d + "COPYING"] = licence
            out[d + "CREDITS"] = CREDITS.format(Name=pack.name, Edition=ed.name, Brand=pack.brand)
        out[base + "index.theme"] = INDEX.format(display=pack.display(ed), name=name,
                                                 icons=pack.file_name("icons", ed),
                                                 cursors=pack.file_name("cursors", ed))
    out["gtk/gtk-2.0.gtkrc.in"] = (f"# {pack.name} {pack.version} - GTK 2 apps use the system's Breeze GTK 2 theme.\n"
                                   f"# Written by the {pack.name} installer; removed again by its uninstaller.\n"
                                   'include "@BASE@"\n')
    return out
