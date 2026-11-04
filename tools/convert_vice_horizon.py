#!/usr/bin/env python3
"""Write packs/vice-horizon/pack.toml from Vice Horizon 1.8.2's config/tokens.json.

    python3 tools/convert_vice_horizon.py references/vice-horizon-source/config/tokens.json

Colours that Vice Horizon's generator computed (Konsole faint and intense colours, the inactive
selection text) are worked out here with its own formula, so the pack holds their values.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def vh_mix(a, b, t):            # Vice Horizon's mix: t = share of b, Python's round()
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(rgb(a), rgb(b)))


def main(path):
    t = json.loads(Path(path).read_text())
    col = {k: v["hex"].upper() for k, v in t["palette"].items()}
    col.update({k: v["hex"].upper() for k, v in t["derived"].items()})
    ref = lambda v: col[v] if v in col else v.upper()   # noqa: E731
    L = ["# Vice Horizon - Miami-sunset palette: Midnight Violet (Dark) and Shell Blush (Light).",
         "# The Linux Workbench. Converted from Vice Horizon 1.8.2's config/tokens.json by",
         "# tools/convert_vice_horizon.py; edit this file from now on.", "",
         "[theme]", 'id = "vice-horizon"', 'name = "Vice Horizon"', 'command = "vice-horizon"',
         'brand = "The Linux Workbench"', 'version = "0.1.0"                     # first release on the engine (was 1.8.2)',
         'license = "GPL-3.0-or-later"', 'editions = ["dark", "light"]',
         'lookandfeel_id = "org.thelinuxworkbench.vicehorizon"',
         'previous_ids = ["org.digitalcohesion.vicehorizon"]',
         'parts = ["kde-colors", "konsole"]', "", "[colours]"]
    for k, v in t["palette"].items():
        L.append(f'{k} = "{v["hex"].upper()}"    # {v["label"]}')
    for k, v in t["derived"].items():
        L.append(f'{k} = "{v["hex"].upper()}"')
    for e, title in (("dark", "Dark"), ("light", "Light")):
        roles = t["variants"][e]
        r = {k: ref(v) for k, v in roles.items()}
        L += ["", "# " + "-" * 77 + " " + title, f"[edition.{e}]", f'name = "{title}"', "", f"[edition.{e}.roles]"]
        L += [f'{k} = "{v}"' for k, v in roles.items()]
        sel_inactive = vh_mix(r["selection_fg"], r["selection_bg"], 0.25)
        L += ["", f"[edition.{e}.kde.Selection]          # Vice Horizon's text colours on a selection",
              f'ForegroundInactive = "{sel_inactive}"', 'ForegroundActive = "peach_glow"', 'ForegroundLink = "peach_glow"',
              'ForegroundVisited = "horizon_pink"', 'ForegroundNegative = "peach_glow"', 'ForegroundNeutral = "peach_glow"',
              'ForegroundPositive = "palm_mint"']
        term = t["terminal"][e]
        bg, fg = ref(term["background"]), ref(term["foreground"])
        normal = [ref(x) for x in term["normal"]]
        L += ["", f"[edition.{e}.terminal]", f'background = "{term["background"]}"',
              f'background_intense = "{vh_mix(bg, col["palm_violet"], 0.08)}"', f'foreground = "{term["foreground"]}"',
              f'foreground_faint = "{vh_mix(fg, bg, 0.35)}"',
              f'foreground_intense = "{"peach_glow" if e == "dark" else "deep_plum"}"',
              "normal = [" + ", ".join(f'"{x}"' for x in term["normal"]) + "]",
              "bright = [" + ", ".join(f'"{x}"' for x in term["bright"]) + "]",
              "faint = [" + ", ".join(f'"{vh_mix(n, bg, 0.35)}"' for n in normal) + "]"]
    out = ROOT / "packs/vice-horizon/pack.toml"
    out.write_text("\n".join(L) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
