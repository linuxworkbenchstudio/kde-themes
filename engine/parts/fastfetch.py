"""Fastfetch design: fastfetch/design/config.jsonc - the theme's Fastfetch layout with its logo.

The layout (modules, padding) is templates/fastfetch/config.json; the pack gives the logo's
colours in [theme.fastfetch]:

  logo_colours = ["amber", "text"]     $1, $2 ... in the logo file: a colour (24-bit) or "text"
                                       (the terminal's own text colour)

The logo file itself (fastfetch/design/<command>-logo.txt) is artwork, made with the others.
"""
import json

from ..colour import is_hex, rgb
from ..pack import Pack
from . import TEMPLATES


def ansi(pack: Pack, value: str) -> str:
    if value == "text":
        return "39"
    if not is_hex(value):
        value = pack.colours[value]
    return "38;2;%d;%d;%d" % rgb(value)


def build(pack: Pack) -> dict:
    spec = pack.raw.get("theme", {}).get("fastfetch", {})
    first = next(iter(pack.editions.values()))
    colours = spec.get("logo_colours", [first.roles["accent"], "text"])
    config = json.loads((TEMPLATES / "fastfetch" / "config.json").read_text(encoding="utf-8"))
    config["logo"]["source"] = f"~/.config/fastfetch/{pack.command}-logo.txt"
    config["logo"]["color"] = {str(i): ansi(pack, c) for i, c in enumerate(colours, 1)}
    return {"fastfetch/design/config.jsonc": json.dumps(config, indent=2, ensure_ascii=False) + "\n"}
