#!/usr/bin/env python3
"""Copy a theme's released files into references/<pack>/, for `python3 -m engine compare`.

    python3 tools/import_reference.py vice-horizon  VICE_HORIZON_SOURCE_DIR_OR_ZIP
    python3 tools/import_reference.py waypoint      WAYPOINT_RELEASE_DIR_OR_ZIP

references/ is not part of the repository (it holds tens of megabytes of icons). Each reference
gets a reference.json with where it came from and how its folders map onto the engine's layout,
which is the layout Waypoint's releases already use (color-schemes/, konsole/, plasma/ ...).
"""
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# engine folder -> folder in the theme's own tree (longest prefix wins)
LAYOUTS = {
    "vice-horizon": {
        "color-schemes/": "kde/colors/",
        "konsole/": "kde/konsole/",
        "plasma/desktoptheme/": "kde/plasma/desktoptheme/",
        "look-and-feel/org.thelinuxworkbench.vicehorizon.": "kde/plasma/look-and-feel/org.digitalcohesion.vicehorizon.",
        "look-and-feel/": "kde/plasma/look-and-feel/",
        "hicolor/": "assets/brand/hicolor/",
        "wallpapers/": "kde/plasma/wallpapers/",
        "aurorae/themes/": "kde/aurorae/",
        "Kvantum/": "kde/kvantum/",
        "cursors/": "kde/cursors/",
        "icons/": "assets/icons/",
        "gtk/": "kde/gtk/",
        "panel-colorizer/": "kde/panel/panel-colorizer/",
        "panel/": "kde/panel/",
        "fastfetch/": "kde/fastfetch/",
        "bin/": "kde/bin/",
        "widgets/": "kde/widgets/",
        "sddm/": "kde/optional-components/sddm/",
    },
    "waypoint": {"look-and-feel/org.thelinuxworkbench.waypoint.": "look-and-feel/org.waypoint."},   # else the same
}
# old names in each reference, read as the new ones when comparing
RENAME = {
    "vice-horizon": {"org.digitalcohesion.vicehorizon": "org.thelinuxworkbench.vicehorizon", "DigitalCohesion": "The Linux Workbench", "1.8.2": "0.1.0", "1.4.5": "0.1.0"},
    "waypoint": {"org.waypoint.": "org.thelinuxworkbench.waypoint.", "DigitalCohesion": "The Linux Workbench", "0.5.0": "0.1.0"},
}
# changes made on purpose, with the reason
ACCEPT = {
    "vice-horizon": [
        {
            "path": "icons/*/apps/scalable/*",
            "why": "app tiles have no light edge or top highlight (Kahlil, 5 Nov 2026: a stray line at panel sizes)"
        },
        {
            "path": "hicolor/*",
            "why": "new logo: the V with the striped sun, midnight tile (Dark) and pink tile (Light) (Kahlil, 12 Nov 2026)"
        },
        {
            "path": "icons/*/apps/*/vice-horizon-launcher.png",
            "why": "new logo, as above (the launcher's fixed sizes in the icon theme)"
        },
        {
            "path": "icons/*/categories/scalable/*",
            "why": "category tiles have no light edge or top highlight (Kahlil, 5 Nov 2026)"
        },
        {
            "path": "icons/*/index.theme",
            "why": "small-size tiles (apps|categories/small, up to 32 px) with a bigger glyph (Kahlil, 5 Nov 2026)"
        },
        {
            "path": "panel-colorizer/*",
            "why": "top and bottom margins at most 2 px, so the Task Manager's icons are bigger (Kahlil, 5 Nov 2026)"
        },
        {
            "path": "panel-colorizer/* Cards*/settings.json",
            "why": "Cards has no panel bar behind the cards now, like Pills (Kahlil, 5 Nov 2026)"
        },
        {
            "path": "panel-colorizer/* Pills*/settings.json",
            "why": "the top panel is 32 px now (was 36), so the pills' round ends are 16 px (Kahlil, 5 Nov 2026)"
        },
        {
            "path": "wallpapers/*/metadata.json",
            "why": "the wallpaper package says what it is (Description) and its Version, as Waypoint's does"
        },
        {
            "path": "panel/*-panel.js",
            "why": "one panel script for every theme (Vice Horizon's, plus Waypoint's record of the look; 32 px; replaces any The Linux Workbench theme's panel)"
        },
        {
            "path": "widgets/README.md",
            "why": "the bundled widgets are shared by every theme now"
        },
        {
            "path": "look-and-feel/*",
            "why": "one Global Theme template for every theme: new ids, the shared panel script with the Fancy preset, the splash comment"
        },
        {
            "path": "bin/*",
            "why": "one set of programs for every theme: names per edition from the pack, generic wording"
        },
        {
            "path": "fastfetch/*",
            "why": "one Fastfetch tool for every theme: switches over from any sibling theme's logo"
        },
        {
            "path": "sddm/README.md",
            "why": "generic wording (every theme has the SDDM helper now)"
        },
        {
            "path": "LICENSE",
            "why": "one LICENSE for every theme, naming the release layout's folders"
        },
        {
            "path": "LICENSES/*",
            "why": "the same licences, the texts as shipped with the parts they come from"
        },
        {
            "path": "README.md",
            "why": "one README for every theme"
        },
        {
            "path": "CHANGELOG.md",
            "why": "the 0.1.0 entry"
        }
    ],
    "waypoint": [
        {
            "path": "plasma/desktoptheme/*/metadata.json",
            "why": "Plasma 6 metadata: X-Plasma-API-Minimum-Version 6.0 replaces X-Plasma-API 5.0"
        },
        {
            "path": "plasma/desktoptheme/*/widgets/tabbar.svgz",
            "why": "the open-widget line's corner pieces are hidden too (Vice Horizon 1.8's fix, now in every theme)"
        },
        {
            "path": "icons/*",
            "why": "icons redrawn by the shared icon generator in Waypoint's style (Kahlil's choice A, 4 Nov 2026)"
        },
        {
            "path": "gtk/*/CREDITS",
            "why": "GTK 4 now ships its widget images too, so CREDITS names both assets folders"
        },
        {
            "path": "panel-colorizer/*",
            "why": "the shared panel looks in Waypoint's colours (Kahlil, 5 Nov 2026)"
        },
        {
            "path": "panel/*-panel.js",
            "why": "one panel script for every theme (Vice Horizon's, plus Waypoint's record of the look; 32 px)"
        },
        {
            "path": "widgets/*",
            "why": "one copy of the bundled widgets for every theme (Vice Horizon's; same versions, a few more files)"
        },
        {
            "path": "look-and-feel/*",
            "why": "one Global Theme template for every theme: new ids, the shared panel script with the Fancy preset, the splash comment"
        },
        {
            "path": "bin/*",
            "why": "Waypoint now uses the shared programs (Vice Horizon's, filled in with Waypoint's names); see DESIGN.md for the behaviour changes"
        },
        {
            "path": "fastfetch/*",
            "why": "one Fastfetch tool for every theme"
        },
        {
            "path": "install.sh",
            "why": "the shared installer"
        },
        {
            "path": "uninstall.sh",
            "why": "the shared uninstaller"
        },
        {
            "path": "tests/*",
            "why": "one test suite for every theme (Vice Horizon's, run against each pack)"
        },
        {
            "path": "LICENSE",
            "why": "one LICENSE for every theme, naming the release layout's folders"
        },
        {
            "path": "LICENSES/*",
            "why": "the same licences, the texts as shipped with the parts they come from"
        },
        {
            "path": "README.md",
            "why": "one README for every theme"
        },
        {
            "path": "CHANGELOG.md",
            "why": "the 0.1.0 entry"
        }
    ]
}
# files the engine adds that the release didn't have
NEW_OK = {
    "vice-horizon": [
        "icons/*/apps/small/*",
        "icons/*/categories/small/*",
        "install.sh",
        "uninstall.sh",
        "setup.sh",
        "lib/*",
        "*/COPYING",
        "*/COPYING.LGPL-3",
        "*/CREDITS",
        "cursors/*/cursors_scalable/*",
        "tests/*",
        "README.md",
        "CHANGELOG.md",
        "LICENSES/*"
    ],
    "waypoint": [
        "cursors/*/aliases.txt",
        "gtk/*/gtk-4.0/assets/*",
        "gtk/*/gtk-4.0/gtk-dark.css",
        "gtk/*/index.theme",
        "icons/*",
        "widgets/*",
        "setup.sh",
        "lib/*",
        "sddm/*",
        "gtk/gtk-2.0.gtkrc.in",
        "bin/*",
        "VERSION",
        "*/COPYING",
        "tests/*",
        "README.md",
        "CHANGELOG.md",
        "LICENSES/*"
    ]
}
# what to copy from each kind of tree
KEEP = {
    "vice-horizon": ["kde", "assets/icons", "assets/wallpapers", "assets/brand", "VERSION", "LICENSE", "LICENSES"],
    "waypoint": None,                   # everything in the release
}


def unpack(src: Path) -> tuple[Path, tempfile.TemporaryDirectory | None]:
    if src.is_dir():
        return src, None
    tmp = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(src) as z:
        z.extractall(tmp.name)
    top = [p for p in Path(tmp.name).iterdir()]
    return (top[0] if len(top) == 1 and top[0].is_dir() else Path(tmp.name)), tmp


def main(argv):
    if len(argv) != 3 or argv[1] not in LAYOUTS:
        print(__doc__)
        return 2
    pack, src = argv[1], Path(argv[2])
    tree, tmp = unpack(src)
    # a source archive may wrap the tree one level deeper
    if pack == "vice-horizon" and not (tree / "kde").is_dir():
        inner = [p for p in tree.iterdir() if (p / "kde").is_dir()]
        if inner:
            tree = inner[0]
    if pack == "waypoint" and not (tree / "color-schemes").is_dir():
        inner = [p for p in tree.rglob("color-schemes") if p.is_dir()]
        if inner:
            tree = inner[0].parent
    dest = ROOT / "references" / pack
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    keep = KEEP[pack]
    if keep is None:
        shutil.copytree(tree, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    else:
        for k in keep:
            p = tree / k
            if p.is_dir():
                shutil.copytree(p, dest / k, ignore=shutil.ignore_patterns("__pycache__"))
            elif p.is_file():
                (dest / k).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest / k)
    version = (dest / "VERSION").read_text().strip() if (dest / "VERSION").is_file() else ""
    (dest / "reference.json").write_text(json.dumps(
        {"pack": pack, "origin": str(src), "version": version, "map": LAYOUTS[pack], "rename": RENAME[pack],
         "accept": ACCEPT[pack], "new_ok": NEW_OK[pack]}, indent=1) + "\n")
    n = sum(1 for p in dest.rglob("*") if p.is_file())
    print(f"{n} files from {src} in {dest}")
    if tmp:
        tmp.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
