"""Icon theme: icons/<name>/ - about 145 folder types, 600 apps, 260 file types, devices, categories.

The drawing is Vice Horizon's icon generator (engine/icons/, original artwork CC-BY-SA-4.0, with
small symbols from KDE Breeze, LGPL-3.0-or-later). Its artwork uses 28 colours; a pack gives its
own colour for each in

  [theme.icons.map]          "#EFA1A1" = "accent", ...   (every edition)
  [edition.<id>.icons.map]   the same, for one edition

and the generator runs with those colours swapped into its source, so gradients, mixes and
shades all come from the pack's colours. Colours a pack doesn't map stay as they are.
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
            f"Name={pack.display(ed)}\n"
            f"Comment={theme.get('comment', COMMENT).format(Name=pack.name)}\n"
            f"Inherits={inherits}\n"
            "Example=folder\n"
            "Directories=" + ",".join(f"apps/{n}" for n in sizes) + ","
            + ",".join(d for d, *_ in dirs) +
            ",places/scalable,apps/scalable,mimetypes/scalable,devices/scalable\n\n"
            + "".join(f"[apps/{n}]\nContext=Applications\nSize={n}\nType=Fixed\n\n" for n in sizes)
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
        for p in sorted(root.rglob("*")):
            if p.is_file():
                out[f"icons/{p.relative_to(root).as_posix()}"] = p.read_text(encoding="utf-8")
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
    out = {}
    for ed in pack.editions.values():
        out.update(build_edition(pack, ed))
    return out
