"""Icon theme: icons/<name>/ - about 145 folder types, 600 apps, 260 file types, devices, categories.

The drawing is Vice Horizon's icon generator (engine/icons/, original artwork CC-BY-SA-4.0, with
small symbols from KDE Breeze, LGPL-3.0-or-later). Its artwork uses 28 colours; a pack gives its
own colour for each in

  [theme.icons.map]          "#EFA1A1" = "accent", ...   (every edition)
  [edition.<id>.icons.map]   the same, for one edition

and the generator runs with those colours swapped into its source, so gradients, mixes and
shades all come from the pack's colours. Colours a pack doesn't map stay as they are.
[theme.icons.style] (optional) gives every icon of a kind one look instead of per-type colours:
  tile = [top, bottom]           every app and category tile
  folder = [top, bottom, back]   every folder (front gradient, back flap)
  page = [top, bottom]           every file-type page
  pages = {pdf = [top, bottom], ...}   pages of one family (text, code, pdf, image, audio ...)
  bar = "accent"                 a short bar in this colour under the glyph on app tiles and file
                                 pages (Waypoint's amber bar); the glyph moves up to make room
App and category tiles have no light edge or top highlight (removed 5 Nov 2026: at panel sizes they
read as a stray line). Below 33 px (panel, Task Manager, menus) they come from apps|categories/small:
the glyph scaled up to fill about 70% of the tile and no bar, so it stays readable.
[theme.icons] also takes `comment` (index.theme) and `inherits_dark` / `inherits_light`.
The theme's own brand icons (launcher, app icon) come from packs/<pack>/art/hicolor/.
"""
from __future__ import annotations

import re
import sys
import tempfile
import types
from pathlib import Path

from ..pack import Pack
from ..recolour import resolver
from . import TEMPLATES

ICONS = Path(__file__).resolve().parent.parent / "icons"
MODULES = ("icons_base", "icons_extra", "icons_more", "icons_set")
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")
INHERITS = {"dark": "Papirus-Dark,breeze-dark,Adwaita,hicolor", "light": "Papirus,breeze,Adwaita,hicolor"}
COMMENT = ("{Name} folders, app, device and file-type icons (glyphs partly from KDE Breeze, "
           "LGPL-3.0-or-later); everything else inherits from Papirus, Breeze or Adwaita")


def load(colours: dict, name: str) -> dict:
    """The generator's modules with `colours` ({#RRGGBB: #RRGGBB}) and the theme name swapped in."""
    saved = {m: sys.modules.get(m) for m in MODULES}
    mods = {}
    try:
        for m in MODULES:
            src = (ICONS / f"{m}.py").read_text(encoding="utf-8")
            src = HEX.sub(lambda h: colours.get(h.group(0).upper(), h.group(0)), src)
            src = src.replace("Vice Horizon", name)
            mod = types.ModuleType(m)
            mod.__file__ = str(ICONS / f"{m}.py")
            sys.modules[m] = mod
            exec(compile(src, mod.__file__, "exec"), mod.__dict__)
            mods[m] = mod
    finally:
        for m, old in saved.items():
            if old is None:
                sys.modules.pop(m, None)
            else:
                sys.modules[m] = old
    return mods


GLYPH = re.compile(r'\n<g(?: fill="[^"]*")? opacity="\.95">')
# (glyph centre before, glyph centre after, scale, bar y) for app tiles and file pages
BAR = {"app icon": (24, 21, 0.86, 36.6), "file-type icon": (30, 27.6, 0.86, 37)}


def _bar(text: str, colour: str) -> str:
    """Move the glyph up and put a short bar under it (app tiles and file pages only)."""
    kind = next((k for k in BAR if k in text[:400]), None)
    m = GLYPH.search(text)
    end = text.rfind("\n</svg>")
    if not kind or not m or end < m.start():
        return text
    c0, c1, sc, y = BAR[kind]
    body = text[m.start() + 1:end]
    return (text[:m.start()] + f'\n<g transform="translate(24 {c1}) scale({sc}) translate(-24 -{c0})">{body}</g>'
            f'\n<rect x="19" y="{y}" width="10" height="2.4" rx="1" fill="{colour}"/>' + text[end:])


EDGES = re.compile(r'\n?<rect x="4" y="4" width="40" height="1\.4" fill="#FFFFFF" opacity="\.4"/>'
                   r'|\n<rect x="4\.5" y="4\.5" width="39" height="39" rx="9\.5" fill="none" stroke="#FFFFFF" stroke-opacity="[\d.]*"/>')
SMALL = 1.3          # glyph scale on the small tiles
SMALL_MAX = 32       # largest size the small tiles are used for


def _no_edges(text: str) -> str:
    """A tile without its light edge and top highlight."""
    return EDGES.sub("", text).replace('<g clip-path="url(#c)">\n<rect', '<g clip-path="url(#c)"><rect')


def _small(text: str) -> str | None:
    """The small-size tile: glyph scaled up about the tile's centre (no bar), or None for non-tiles."""
    if "app icon" not in text[:400]:
        return None
    m = GLYPH.search(text)
    end = text.rfind("\n</svg>")
    if not m or end < m.start():
        return None
    body = text[m.start() + 1:end]
    return (text[:m.start()] + f'\n<g transform="translate(24 24) scale({SMALL}) translate(-24 -24)">{body}</g>'
            + text[end:])


def _map(pack: Pack, ed) -> dict:
    resolve = resolver(pack, ed)
    spec = dict(pack.raw.get("theme", {}).get("icons", {}).get("map", {}))
    spec.update(ed.raw.get("icons", {}).get("map", {}))
    return {k.upper(): resolve(v) for k, v in spec.items()}


def _index(pack: Pack, ed, name: str, M) -> str:
    theme = pack.raw.get("theme", {}).get("icons", {})
    variant = "dark" if ed.template == "dark" else "light"
    inherits = theme.get(f"inherits_{variant}", INHERITS[variant])
    sizes = M["icons_base"].LAUNCHER_SIZES
    dirs = M["icons_set"].index_dirs()
    return ("[Icon Theme]\n"
            f"Name={pack.display(ed) if '{Edition}' in pack.names['icons'] or 'names' in ed.raw else pack.name}\n"
            f"Comment={theme.get('comment', COMMENT).format(Name=pack.name)}\n"
            f"Inherits={inherits}\n"
            "Example=folder\n"
            "Directories=" + ",".join(f"apps/{n}" for n in sizes) + ",apps/small,categories/small,"
            + ",".join(d for d, *_ in dirs) +
            ",places/scalable,apps/scalable,mimetypes/scalable,devices/scalable\n\n"
            + "".join(f"[apps/{n}]\nContext=Applications\nSize={n}\nType=Fixed\n\n" for n in sizes)
            + "".join(f"[{d}/small]\nContext={c}\nSize={SMALL_MAX}\nMinSize=16\nMaxSize={SMALL_MAX}\nType=Scalable\n\n"
                      for d, c in (("apps", "Applications"), ("categories", "Categories")))
            + "".join(f"[{d}]\nContext={c}\nSize={n}\n" + ("Type=Fixed\n\n" if t == "Fixed" else "MinSize=16\nMaxSize=512\nType=Scalable\n\n")
                      for d, c, n, t in dirs) +
            "[places/scalable]\n"
            "Context=Places\nSize=48\nMinSize=16\nMaxSize=512\nType=Scalable\n\n"
            "[apps/scalable]\n"
            "Context=Applications\nSize=48\nMinSize=16\nMaxSize=512\nType=Scalable\n\n"
            "[mimetypes/scalable]\n"
            "Context=MimeTypes\nSize=48\nMinSize=16\nMaxSize=512\nType=Scalable\n\n"
            "[devices/scalable]\n"
            "Context=Devices\nSize=48\nMinSize=16\nMaxSize=512\nType=Scalable\n")


def build_edition(pack: Pack, ed) -> dict:
    M = load(_map(pack, ed), pack.name)
    B, X, MO, S = (M[m] for m in MODULES)
    style = pack.raw.get("theme", {}).get("icons", {}).get("style", {})
    resolve = resolver(pack, ed)
    if "tile" in style:
        t = tuple(resolve(c) for c in style["tile"])
        for d in (X.FAM, MO.TILE):
            for k in d:
                d[k] = t
    if "page" in style or "pages" in style:
        fixed = tuple(resolve(c) for c in style["page"]) if "page" in style else None
        per = {k: tuple(resolve(c) for c in v) for k, v in style.get("pages", {}).items()}

        def pg(k, was):
            return per.get(k, fixed or was)
        for k, (was, names) in X.FILES.items():
            X.FILES[k] = (pg(k, was), names)
        for d in (MO.MORE_FILES, S.FILE_FAMILIES):
            for k, (was, sym, names) in d.items():
                d[k] = (pg(k, was), sym, names)
    if "folder" in style:
        f = tuple(resolve(c) for c in style["folder"])
        for d in (MO.FAM, S.FAM):
            for k in d:
                d[k] = f
        for k, v in B.FOLDERS.items():
            B.FOLDERS[k] = f + (v[3],)
    variant = "dark" if ed.template == "dark" else "light"
    name = pack.file_name("icons", ed)
    art = pack.root / "art" / "hicolor"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        S.ROOT, S.VENDOR = root, TEMPLATES / "icons" / "breeze-symbols"
        S._cache.clear()
        base = Path(name)

        def write(path, text):
            p = root / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

        write(base / "index.theme", _index(pack, ed, name, M))
        for svg in sorted((art / "scalable/apps").glob("*.svg")) if (art / "scalable/apps").is_dir() else []:
            if svg.stem != f"{pack.command}-launcher":   # the launcher goes in as fixed sizes
                write(base / "apps/scalable" / svg.name, svg.read_text(encoding="utf-8"))
        out = {}
        # Plasma looks a name up in this theme first and, when it isn't here, tries the shorter
        # "<command>" (the app icon) before hicolor: fixed-size launcher folders, listed first, win.
        for n in B.LAUNCHER_SIZES:
            png = art / f"{n}x{n}/apps/{pack.command}-launcher.png"
            if png.is_file():
                out[f"icons/{name}/apps/{n}/{png.name}"] = png.read_bytes()
        for fname, (top, bottom, back, glyph) in B.FOLDERS.items():
            write(base / "places/scalable" / f"{fname}.svg", B.folder_svg(top, bottom, back, glyph, pack.version))
        # Dolphin and GTK look up the MIME-type icon first; without these an inherited theme's
        # folder wins over ours in file views
        top, bottom, back, glyph = B.FOLDERS["folder"]
        for mname in ("inode-directory", "folder"):
            write(base / "mimetypes/scalable" / f"{mname}.svg", B.folder_svg(top, bottom, back, glyph, pack.version))
        X.write_all(write, base, pack.version)
        MO.write_all(write, base, pack.version, lambda *a: B.folder_svg(*a, pack.version), variant)
        S.write_all(write, base, pack.version, variant)
        bar = resolve(style["bar"]) if "bar" in style else None
        for p in sorted(root.rglob("*")):
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                text = p.read_text(encoding="utf-8")
                if "app icon" in text[:400]:
                    text = _no_edges(text)
                    parts = rel.split("/")
                    small = _small(text) if parts[1] in ("apps", "categories") and parts[2] == "scalable" else None
                    if small:
                        out[f"icons/{parts[0]}/{parts[1]}/small/{parts[3]}"] = small
                if bar:
                    text = _bar(text, bar)
                out[f"icons/{rel}"] = text
    licences = TEMPLATES / "licences"
    out[f"icons/{name}/COPYING"] = (licences / "CC-BY-SA-4.0.txt").read_text(encoding="utf-8")
    out[f"icons/{name}/COPYING.LGPL-3"] = (licences / "LGPL-3.0-or-later.txt").read_text(encoding="utf-8")
    out[f"icons/{name}/CREDITS"] = (
        f"{pack.display(ed)} icons - part of {pack.name} ({pack.brand}).\n\n"
        "Folders, app tiles, file pages and devices: original artwork from Vice Horizon's icon set,\n"
        f"in {pack.name}'s colours. Licence: CC-BY-SA-4.0 (COPYING).\n"
        "Small symbols on some icons: KDE Breeze icons (C) 2014 Uri Herrera and others,\n"
        "https://invent.kde.org/frameworks/breeze-icons. Licence: LGPL-3.0-or-later (COPYING.LGPL-3).\n"
        "No third-party logos are reproduced; every app gets a generic picture of what it does.\n")
    return out


def build(pack: Pack) -> dict:
    out, names = {}, set()
    for ed in pack.editions.values():
        name = pack.file_name("icons", ed)
        if name in names:           # one icon theme for every edition (Waypoint): the first edition's
            continue
        names.add(name)
        out.update(build_edition(pack, ed))
    return out
