"""Global Theme: look-and-feel/<lookandfeel_id>.<edition>/ - what System Settings > Global Theme
applies in one go: colours, Plasma Style, window decoration, icons, cursors, wallpaper, splash,
and (when "Desktop and window layout" is ticked) the top panel with the default look, Fancy.

[theme.lookandfeel] (optional):  widget_style = "Breeze" (or "kvantum")
Texts: [edition.<id>.text] lookandfeel = the description shown in System Settings.
The splash images and previews come from the brand part (packs/<pack>/art/).
"""
import json

from ..pack import Pack
from . import TEMPLATES
from .panel_layout import build as panel_script
from .panel_looks import Looks


def build(pack: Pack) -> dict:
    spec = pack.raw.get("theme", {}).get("lookandfeel", {})
    looks = dict(Looks(pack).all())
    script = next(iter(panel_script(pack).values()))
    prefix = pack.id.upper().replace("-", "_")
    out = {}
    for ed in pack.editions.values():
        lid = f"{pack.lookandfeel_id}.{ed.id}"
        base = f"look-and-feel/{lid}/"
        out[base + "COPYING"] = (TEMPLATES / "licences" / "GPL-3.0-or-later.txt").read_text(encoding="utf-8")
        out[base + "metadata.json"] = json.dumps({
            "KPackageStructure": "Plasma/LookAndFeel",
            "KPlugin": {"Authors": [{"Name": pack.brand}], "Category": "",
                        "Description": pack.describe("lookandfeel", ed), "Id": lid, "License": pack.license,
                        "Name": pack.display(ed), "Version": pack.version, "Website": pack.website},
            "X-Plasma-APIVersion": "2", "X-Plasma-MainScript": "defaults"}, indent=4) + "\n"
        n = lambda kind: pack.file_name(kind, ed)   # noqa: E731
        out[base + "contents/defaults"] = (
            f"[kdeglobals][General]\nColorScheme={n('color_scheme')}\n\n"
            f"[kdeglobals][Icons]\nTheme={n('icons')}\n\n"
            f"[kdeglobals][KDE]\nwidgetStyle={spec.get('widget_style', 'Breeze')}\n\n"
            f"[kcminputrc][Mouse]\ncursorTheme={n('cursors')}\n\n"
            f"[plasmarc][Theme]\nname={n('plasma_style')}\n\n"
            "[kwinrc][WindowSwitcher]\nLayoutName=org.kde.breeze.desktop\n\n"
            f"[kwinrc][org.kde.kdecoration2]\nlibrary=org.kde.kwin.aurorae\ntheme=__aurorae__svg__{n('aurorae')}\n\n"
            f"[ksplashrc][KSplash]\nEngine=KSplashQML\nTheme={lid}\n\n"
            f"[Wallpaper]\nImage={pack.name.replace(' ', '-')}\n")
        # every splash has a dark picture behind it, so it takes the Dark edition's colours
        dark = ed if ed.template == "dark" else next(e for e in pack.editions.values() if e.template == "dark")
        out[base + "contents/splash/Splash.qml"] = ((TEMPLATES / "lookandfeel" / "Splash.qml").read_text(encoding="utf-8")
                                                   .replace("@VARIANT@", ed.id).replace("@NAME@", pack.name)
                                                   .replace("@BG@", dark.roles["base_bg"]).replace("@LINE@", dark.roles["accent"])
                                                   .replace("@TEXT@", dark.roles["text"]))
        preset = f"{pack.name} Fancy" + (" Light" if ed.template == "light" else "")
        out[base + "contents/layouts/org.kde.plasma.desktop-layout.js"] = (
            f"// Global Theme layout = the {pack.name} top panel (panel/{pack.command}-panel.js).\n"
            "// Only used when you tick 'Desktop and window layout' in System Settings > Global Theme.\n"
            f"// Styled by Panel Colorizer's \"{pack.name} Fancy\" preset when Panel Colorizer is installed.\n"
            f"var {prefix}_FANCY = {json.dumps(looks[preset], separators=(',', ':'))};\n"
            f"var {prefix}_STYLE_NAME = \"{preset}\";\n" + script)
    return out
