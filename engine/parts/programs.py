"""Programs: the installer and uninstaller, the theme command, Settings, Setup, the login sync
helper, the Fastfetch tool and the SDDM helper - one set of templates (templates/programs/, from
Vice Horizon 1.8.2, see tools/port_programs.py) filled in for each pack.

[theme.programs] (optional texts and colours):
  tagline       one line on Setup's welcome screen
  dark_surface / light_surface   how Settings names the editions ("Dark - Midnight Violet")
  dark_hint / light_hint         Setup's line for each edition
  bar = [4 colours]              the coloured rule under the programs' headings
The terminal colours come from the Dark edition's roles (accent, warm, link, muted ...).
"""
import json

from ..colour import rgb
from ..pack import Pack
from . import TEMPLATES
from .panel_layout import PACKS, key

KINDS = ("color_scheme", "konsole", "plasma_style", "aurorae", "cursors", "kvantum", "gtk", "icons")
FILES = {"install.sh": "install.sh", "uninstall.sh": "uninstall.sh", "setup.sh": "setup.sh",
         "lib/common.sh": "lib/common.sh", "bin/THEME": "bin/{c}", "bin/THEME-settings": "bin/{c}-settings",
         "bin/THEME-setup": "bin/{c}-setup", "bin/THEME-settings.desktop": "bin/{c}-settings.desktop",
         "bin/THEME-sync.desktop": "bin/{c}-sync.desktop", "fastfetch/THEME-fastfetch.py": "fastfetch/{c}-fastfetch.py",
         "fastfetch/install-fastfetch-colours.sh": "fastfetch/install-fastfetch-colours.sh",
         "sddm/apply-sddm-background.sh": "sddm/apply-sddm-background.sh", "sddm/README.md": "sddm/README.md"}


def xterm256(h: str) -> int:
    """Nearest xterm-256 colour (the 6x6x6 cube or the grey ramp)."""
    r, g, b = rgb(h)
    steps = (0, 95, 135, 175, 215, 255)
    q = lambda v: min(range(6), key=lambda i: abs(steps[i] - v))   # noqa: E731
    cube = (q(r), q(g), q(b))
    cc = tuple(steps[i] for i in cube)
    grey = min(range(24), key=lambda i: abs(8 + 10 * i - (r + g + b) / 3))
    gv = 8 + 10 * grey
    d_cube = sum((x - y) ** 2 for x, y in zip(cc, (r, g, b)))
    d_grey = sum((gv - y) ** 2 for y in (r, g, b))
    return 16 + 36 * cube[0] + 6 * cube[1] + cube[2] if d_cube <= d_grey else 232 + grey


def other_packs(pack):
    from ..pack import load
    out = []
    for p in sorted(PACKS.iterdir()):
        if (p / "pack.toml").is_file() and p.name != pack.id:
            try:
                out.append(load(p))
            except Exception:       # noqa: BLE001 - a broken sibling pack must not stop this one
                pass
    return out


def names_sh(pack) -> str:
    cases = []
    for kind in KINDS:
        for ed in pack.editions.values():
            cases.append(f"    {kind}:{ed.name}) echo '{pack.file_name(kind, ed)}' ;;")
    words = sorted({pack.name.replace(' ', '-'), pack.name.replace(' ', ''), pack.command,
                    pack.lookandfeel_id.rsplit('.', 1)[-1]} | {i.rsplit('.', 1)[-1] for i in pack.previous_ids})
    return ("# ---- names of this theme's files, per edition (filled in by the theme engine)\n"
            "tw_name() {   # kind edition(Dark|Light) -> file or theme name\n"
            '  case "$1:$2" in\n' + "\n".join(cases) + "\n    *) return 1 ;;\n  esac\n}\n"
            "tw_mine() {   # value -> true when it is one of this theme's names (any edition, old ids too)\n"
            '  case "$1" in ' + "|".join(f"*{w}*" for w in words) + ") return 0 ;; esac\n  return 1\n}")


def build(pack: Pack) -> dict:
    spec = pack.raw.get("theme", {}).get("programs", {})
    eds = list(pack.editions.values())
    dark = next((e for e in eds if e.template == "dark"), eds[0])
    light = next((e for e in eds if e.template == "light"), eds[-1])
    r = dark.roles
    others = other_packs(pack)
    profiles = sorted({f"{p.file_name('konsole', e)}.profile" for p in [pack, *others] for e in p.editions.values()})
    ff = pack.raw.get("theme", {}).get("fastfetch", {})
    from .fastfetch import ansi
    logo = {str(i): ansi(pack, c) for i, c in enumerate(ff.get("logo_colours", [r["accent"], "text"]), 1)}
    bar = spec.get("bar", [r["warm"], r["accent"], r["highlight"], r["link"]])
    bar = [rgb(c if c.startswith("#") else (r.get(c) or pack.colours[c])) for c in bar]
    trip = lambda h: "%d;%d;%d" % rgb(h)   # noqa: E731
    values = {
        "@@NAMES_SH@@": names_sh(pack),
        "@@NAMES_PY@@": "NAMES = " + json.dumps({k: {e.name: pack.file_name(k, e) for e in eds} for k in KINDS}) + "   # this theme's file names, per edition",
        "@@PROFILES@@": "|".join(profiles),
        "@@OLD_LNF@@": " ".join(pack.previous_ids),
        "@@SIBLINGS@@": json.dumps(sorted(p.command for p in others)),
        "@@FF_PALETTE@@": json.dumps({"dark": {"accent": rgb(dark.roles["accent"]), "muted": rgb(dark.roles["text_muted"])},
                                      "light": {"accent": rgb(light.roles["link"]), "muted": rgb(light.roles["text_muted"])}}),
        "@@FF_LOGO@@": json.dumps({"dark": logo, "light": logo}),
        "@@BAR_R@@": " ".join(str(c[0]) for c in bar), "@@BAR_G@@": " ".join(str(c[1]) for c in bar),
        "@@BAR_B@@": " ".join(str(c[2]) for c in bar),
        "@@TAGLINE@@": spec.get("tagline", f"A {pack.name} theme for KDE Plasma 6, in Dark and Light."),
        "@@DARK_SURFACE@@": spec.get("dark_surface", f"{pack.name} Dark"),
        "@@LIGHT_SURFACE@@": spec.get("light_surface", f"{pack.name} Light"),
        "@@DARK_HINT@@": spec.get("dark_hint", "Dark surfaces, the theme's accent."),
        "@@LIGHT_HINT@@": spec.get("light_hint", "Light surfaces with a see-through top bar."),
        "@@NAME@@": pack.name, "@@UPPER@@": pack.name.upper(), "@@COMMAND@@": pack.command,
        "@@SLUG@@": pack.name.replace(" ", "-"), "@@COMPACT@@": pack.name.replace(" ", ""),
        "@@PREFIX@@": pack.id.upper().replace("-", "_"), "@@KEY@@": key(pack.id),
        "@@LNF@@": pack.lookandfeel_id, "@@BRAND@@": pack.brand,
    }
    for role, name in (("ACCENT", "accent"), ("WARM", "warm"), ("HIGHLIGHT", "selection_alt_bg"), ("LINK", "link"),
                       ("MUTED", "text_muted"), ("OK", "positive"), ("ERR", "negative"), ("WARN", "neutral")):
        values[f"@@RGB_{role}@@"] = trip(r[name])
        values[f"@@X_{role}@@"] = str(xterm256(r[name]))
    values["@@X_ON_ACCENT@@"] = str(xterm256(r["selection_fg"] if r["selection_bg"] == r["accent"] else dark.roles["base_bg"]))
    out = {}
    root = TEMPLATES / "programs"
    for src, dst in FILES.items():
        text = (root / src).read_text(encoding="utf-8")
        for k in sorted(values, key=len, reverse=True):
            text = text.replace(k, values[k])
        if "@@" in text:
            left = sorted({w for w in text.split() if "@@" in w})[:5]
            raise ValueError(f"templates/programs/{src}: placeholders left: {left}")
        out[dst.format(c=pack.command)] = text
    out["VERSION"] = pack.version + "\n"
    return out
