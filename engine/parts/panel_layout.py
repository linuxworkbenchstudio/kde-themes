"""Top panel layout: panel/<command>-panel.js - a Plasma script that builds the theme's top panel:

  Launcher | gap | Task Manager | space | Clock | space | KVitals | gap | System Tray

templates/panel/panel.js, filled in for the pack. [theme.panel] height (px, default 40) is the
panel's height. The script replaces an earlier panel of this theme or of any other The Linux
Workbench theme (they share the layout), pins only apps the system has, and records the Panel
Colorizer preset and look it was built with, so `<command> dark|light` can restyle it.
"""
from ..pack import Pack
from . import TEMPLATES
from .panel_looks import HEIGHT

PACKS = TEMPLATES.parent / "packs"


def key(pack_id: str) -> str:
    """vice-horizon -> viceHorizon (the panel's config keys: viceHorizonPanel, viceHorizonStyle ...)"""
    first, *rest = pack_id.split("-")
    return first + "".join(w.title() for w in rest)


def build(pack: Pack) -> dict:
    spec = pack.raw.get("theme", {}).get("panel", {})
    keys = sorted({key(p.name) + "Panel" for p in PACKS.iterdir() if (p / "pack.toml").is_file()} | {key(pack.id) + "Panel"})
    text = (TEMPLATES / "panel" / "panel.js").read_text(encoding="utf-8")
    for k, v in {"@NAME@": pack.name, "@PREFIX@": pack.id.upper().replace("-", "_"), "@KEY@": key(pack.id),
                 "@COMMAND@": pack.command, "@HEIGHT@": str(int(spec.get("height", HEIGHT))),
                 "@PANEL_KEYS@": "[" + ", ".join(f'"{k}"' for k in keys) + "]"}.items():
        text = text.replace(k, v)
    return {f"panel/{pack.command}-panel.js": text}
