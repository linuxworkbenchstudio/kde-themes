#!/usr/bin/env python3
"""Make templates/programs/ from Vice Horizon 1.8.2's programs (the base for every theme's).

    python3 tools/port_programs.py VICE_HORIZON_SOURCE_DIR

Vice Horizon's installer, uninstaller, shared library, theme command, Settings, Setup, Fastfetch
tool and SDDM helper become templates: its names turn into @@PLACEHOLDERS@@ that
engine/parts/programs.py fills in per pack, its source-tree paths into the release layout, and
per-edition file names into tw_name calls (Waypoint names its Konsole files WaypointDark, its
Plasma Style waypoint-dark ...). Run once; the templates are then edited by hand and kept.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "templates" / "programs"
FILES = {   # source -> template
    "install.sh": "install.sh", "uninstall.sh": "uninstall.sh", "setup.sh": "setup.sh",
    "scripts/lib/vh-common.sh": "lib/common.sh",
    "kde/bin/vice-horizon": "bin/THEME", "kde/bin/vice-horizon-settings": "bin/THEME-settings",
    "kde/bin/vice-horizon-setup": "bin/THEME-setup",
    "kde/bin/vice-horizon-settings.desktop": "bin/THEME-settings.desktop",
    "kde/bin/vice-horizon-sync.desktop": "bin/THEME-sync.desktop",
    "kde/fastfetch/vice-horizon-fastfetch.py": "fastfetch/THEME-fastfetch.py",
    "kde/fastfetch/install-fastfetch-colours.sh": "fastfetch/install-fastfetch-colours.sh",
    "kde/optional-components/sddm/apply-sddm-background.sh": "sddm/apply-sddm-background.sh",
    "kde/optional-components/sddm/README.md": "sddm/README.md",
}
# source tree -> release layout (longest first)
LAYOUT = [("kde/plasma/look-and-feel/", "look-and-feel/"), ("kde/plasma/desktoptheme/", "plasma/desktoptheme/"),
          ("kde/plasma/wallpapers/", "wallpapers/"), ("kde/panel/panel-colorizer/", "panel-colorizer/"),
          ("kde/optional-components/sddm", "sddm"), ("kde/colors/", "color-schemes/"), ("kde/aurorae/", "aurorae/themes/"),
          ("kde/kvantum/", "Kvantum/"), ("kde/konsole/", "konsole/"), ("kde/cursors/", "cursors/"), ("kde/gtk/", "gtk/"),
          ("kde/panel/", "panel/"), ("kde/widgets", "widgets"), ("kde/bin/", "bin/"), ("kde/fastfetch/", "fastfetch/"),
          ("assets/icons/", "icons/"), ("assets/brand/hicolor", "hicolor"), ("scripts/lib/vh-common.sh", "lib/common.sh")]
# per-edition names, in shell ($T = Dark/Light) - most specific first
SH_NAMES = [
    ("Vice-Horizon-Cursors-$T_", '$(tw_name cursors "$T_")'),
    ("Vice-Horizon-Cursors-$T", '$(tw_name cursors "$T")'),
    ("color-schemes/Vice-Horizon-$T.colors", 'color-schemes/$(tw_name color_scheme "$T").colors'),
    ("desktoptheme/Vice-Horizon-$T", 'desktoptheme/$(tw_name plasma_style "$T")'),
    ("aurorae/themes/Vice-Horizon-$T", 'aurorae/themes/$(tw_name aurorae "$T")'),
    ("__aurorae__svg__Vice-Horizon-$T", '__aurorae__svg__$(tw_name aurorae "$T")'),
    ("Kvantum/Vice-Horizon-$T", 'Kvantum/$(tw_name kvantum "$T")'),
    ("kvantummanager --set \"Vice-Horizon-$T\"", 'kvantummanager --set "$(tw_name kvantum "$T")"'),
    ("kvantummanager --set Vice-Horizon-$T", 'kvantummanager --set $(tw_name kvantum "$T")'),
    ("konsole/Vice-Horizon-$T.", 'konsole/$(tw_name konsole "$T").'),
    ("gtk/Vice-Horizon-$T", 'gtk/$(tw_name gtk "$T")'),
    ("themes/Vice-Horizon-$T", 'themes/$(tw_name gtk "$T")'),
    ("icons/Vice-Horizon-$T", 'icons/$(tw_name icons "$T")'),
    ("plasma-apply-colorscheme \"Vice-Horizon-$T\"", 'plasma-apply-colorscheme "$(tw_name color_scheme "$T")"'),
    ("plasma-apply-colorscheme Vice-Horizon-$T", 'plasma-apply-colorscheme $(tw_name color_scheme "$T")'),
    ("plasma-apply-desktoptheme \"Vice-Horizon-$T\"", 'plasma-apply-desktoptheme "$(tw_name plasma_style "$T")"'),
    ("plasma-apply-desktoptheme Vice-Horizon-$T", 'plasma-apply-desktoptheme $(tw_name plasma_style "$T")'),
    ("\"$ic\" \"Vice-Horizon-$T\"", '"$ic" "$(tw_name icons "$T")"'),
    ("vh_gtk_set \"Vice-Horizon-$T\"", 'vh_gtk_set "$(tw_name gtk "$T")"'),
    ("GTK apps: Vice-Horizon-$T", 'GTK apps: $(tw_name gtk "$T")'),
    ("wallpapers/Vice-Horizon", "wallpapers/@@SLUG@@"),
]
WORDS = [   # theme names -> placeholders (after the paths and per-edition names)
    ("org.digitalcohesion.vicehorizon", "@@LNF@@"), ("DigitalCohesion", "@@BRAND@@"),
    ("VICE_HORIZON", "@@PREFIX@@"), ("viceHorizon", "@@KEY@@"), ("ViceHorizon", "@@COMPACT@@"),
    ("Vice-Horizon", "@@SLUG@@"), ("vice-horizon", "@@COMMAND@@"), ("VICE HORIZON", "@@UPPER@@"),
    ("Vice Horizon", "@@NAME@@"), ("vh-common.sh", "common.sh"),
]


def port(text: str) -> str:
    for a, b in LAYOUT:
        text = text.replace(a, b)
    for a, b in SH_NAMES:
        text = text.replace(a, b)
    for a, b in WORDS:
        text = text.replace(a, b)
    return text


def main(argv):
    if len(argv) != 2 or argv[1].startswith("-"):
        print(__doc__)
        return 2
    src = Path(argv[1])
    for s, d in FILES.items():
        text = port((src / s).read_text(encoding="utf-8"))
        p = OUT / d
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        left = [f"{i}: {l.strip()[:110]}" for i, l in enumerate(text.splitlines(), 1)
                if re.search(r"Vice|vicehorizon|-Horizon|sunset|coral|Midnight|Soft White|Waypoint|waypoint", l)]
        print(f"{d}: {len(left)} lines to check")
        for l in left:
            print("   ", l)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
