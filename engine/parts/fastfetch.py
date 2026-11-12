"""Fastfetch design: fastfetch/design/config.jsonc - the theme's Fastfetch layout in its colours.

The layout (modules, padding) is templates/fastfetch/config.json. It has no logo file: Fastfetch
shows the distro's own logo, coloured 1 = accent, 2 = the terminal's text, 3 = muted (repeating),
and the keys and title in the accent (the Dark edition's colours; the installer's recolour step
sets Dark or Light). Theme logos for Fastfetch are left out for now (Kahlil, 12 Nov 2026).
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
    dark = next((e for e in pack.editions.values() if e.template == "dark"), next(iter(pack.editions.values())))
    accent, muted = ansi(pack, dark.roles["accent"]), ansi(pack, dark.roles["text_muted"])
    config = json.loads((TEMPLATES / "fastfetch" / "config.json").read_text(encoding="utf-8"))
    config["logo"]["color"] = {str(i): (accent, "39", muted)[(i - 1) % 3] for i in range(1, 10)}
    config["display"]["color"] = {"keys": accent, "title": accent, "separator": muted, "output": "39"}
    return {"fastfetch/design/config.jsonc": json.dumps(config, indent=2, ensure_ascii=False) + "\n"}
