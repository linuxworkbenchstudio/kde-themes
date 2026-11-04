#!/usr/bin/env python3
"""Make templates/ from a Waypoint KDE release zip (0.5.0 is the one the engine was checked with).

    python3 tools/make_templates.py Waypoint-KDE-0.5.0.zip

The templates are Waypoint's Plasma Style, window borders and cursors, without the files the
engine writes itself (metadata, colours, names, credits). Symbolic links in the zip (cursor aliases)
are listed in each template's LINKS file as "path<TAB>target" instead of being stored.
"""
import shutil
import stat
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "templates"
PARTS = {   # release folder (after the top folder) -> template folder, files left out, renames
    "plasma/desktoptheme/waypoint-{e}/": ("plasma-style/{e}", {"metadata.json", "colors", "CREDITS", "COPYING"}, {}),
    "aurorae/themes/Waypoint-{E}/": ("aurorae/{e}", {"metadata.desktop"}, {"Waypoint-{E}rc": "decorationrc"}),
    "cursors/Waypoint-Cursors-{E}/": ("cursors/{e}", {"index.theme"}, {}),
}
LICENCES = {"plasma/desktoptheme/waypoint-dark/COPYING": "licences/LGPL-2.0-or-later.txt"}


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    if OUT.exists():
        shutil.rmtree(OUT)
    z = zipfile.ZipFile(argv[1])
    top = z.namelist()[0].split("/")[0] + "/"
    counts = {}
    links = {}
    for info in z.infolist():
        name = info.filename[len(top):] if info.filename.startswith(top) else info.filename
        if info.is_dir():
            continue
        if name in LICENCES:
            p = OUT / LICENCES[name]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(z.read(info))
        for e, E in (("dark", "Dark"), ("light", "Light")):
            for prefix, (dest, skip, renames) in PARTS.items():
                pre = prefix.format(e=e, E=E)
                if not name.startswith(pre):
                    continue
                rel = name[len(pre):]
                if rel in skip:
                    continue
                rel = {k.format(E=E): v for k, v in renames.items()}.get(rel, rel)
                d = dest.format(e=e)
                if stat.S_ISLNK(info.external_attr >> 16):
                    links.setdefault(d, []).append(f"{rel}\t{z.read(info).decode()}")
                    continue
                p = OUT / d / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(z.read(info))
                counts[d] = counts.get(d, 0) + 1
    for d, lines in links.items():
        (OUT / d / "LINKS").write_text("\n".join(sorted(lines)) + "\n")
    for d in sorted(counts):
        print(f"{d}: {counts[d]} files, {len(links.get(d, []))} links")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
