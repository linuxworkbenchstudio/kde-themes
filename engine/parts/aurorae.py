"""Window decoration: share/aurorae/themes/<name>/ - Waypoint's Aurorae SVGs, recoloured."""
from ..pack import Edition, Pack
from ..recolour import Recolour, resolver
from . import TEMPLATES

META = """[Desktop Entry]
Name={display}
Comment={comment}
X-KDE-PluginInfo-Author={brand}
X-KDE-PluginInfo-Name={name}
X-KDE-PluginInfo-Version={version}
X-KDE-PluginInfo-License=GPL-3.0-or-later
X-KDE-PluginInfo-Category=
X-KDE-PluginInfo-EnabledByDefault=true
"""


def build(pack: Pack) -> dict:
    out = {}
    for ed in pack.editions.values():
        name = pack.file_name("aurorae", ed)
        rc = Recolour(ed.raw.get("recolour"), resolver(pack, ed))
        base = f"aurorae/themes/{name}/"
        for f in sorted((TEMPLATES / "aurorae" / ed.template).iterdir()):
            text = f.read_text(encoding="utf-8")
            target = f"{name}rc" if f.name == "decorationrc" else f.name
            out[base + target] = rc.text(text, f"aurorae/{f.name}")
        out[base + "COPYING"] = (TEMPLATES / "licences" / "GPL-3.0-or-later.txt").read_text(encoding="utf-8")
        out[base + "metadata.desktop"] = META.format(display=pack.display(ed), comment=pack.describe("decoration", ed),
                                                      brand=pack.brand, name=name, version=pack.version)
    return out
