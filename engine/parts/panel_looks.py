"""Panel looks: panel-colorizer/<Name> <Look>[ Light]/settings.json - presets for the Panel
Colorizer widget (luisbocanegra/plasma-panel-colorizer), six looks, each with a Light twin:

  Normal       a solid, fully opaque bar
  Transparent  a see-through, blurred bar
  Invisible    no bar and no backgrounds; Dark: light text with a soft dark shadow,
               Light: dark text with a light halo
  Cards        each widget on its own card, no bar behind them (like Pills; 5 Nov 2026)
  Pills        no bar; each group of widgets is one pill with fully rounded ends
  Fancy        the default

This is Vice Horizon's panel-looks.py. The templates (templates/panel-colorizer/) are its Dark
presets; their three theme colours are swapped for the pack's from [theme.panel]:

  shadow = "#121022"       the dark of shadows and section backgrounds   (Vice Horizon: Midnight Black)
  accent = "#857DB5"       hover, open and attention outlines             (Palm Violet)
  light  = "#FEFCFC"       light text and the Light twins' sections       (Soft White)
  ink    = "#2F1F2B"       the Light twins' text                          (Deep Plum)
  light_shadow = "#A77091" the Light twins' shadows                      (Rose Shadow)
  height = 32              the top panel's height in px (every theme: 32 since 5 Nov 2026 evening; was 40, before that 36)
  light_bar = 0.5          how solid the Light twins' bar is (Natura: 0.82, its semi-translucent rice)

Top and bottom margins (the bar's and each widget's) are at most 2 px (5 Nov 2026; were 3-5), so
the Task Manager's icons fill most of the 32 px bar.

The Light twins never use Panel Colorizer's "Complementary" colour set (it stays dark in both
editions). A preset may carry a block named after the theme (Vice Horizon: "viceHorizon") with
options that are not Panel Colorizer's (Pills: {"islands": true} -> its Widget Islands switch).
"""
import copy
import json

from ..colour import is_hex
from ..pack import Pack
from . import TEMPLATES

LOOKS = ("Normal", "Transparent", "Invisible", "Cards", "Pills", "Fancy")
VMARGIN = 2      # largest top/bottom margin of the bar and of each widget (px)
HEIGHT = 32      # the top panel's height (px); a radius of half of it gives a pill its round ends
VH = {"shadow": "#121022", "accent": "#857DB5", "light": "#FEFCFC", "ink": "#2F1F2B", "light_shadow": "#A77091"}


class Looks:
    def __init__(self, pack: Pack):
        spec = pack.raw.get("theme", {}).get("panel", {})
        res = lambda v: v.upper() if is_hex(v) else pack.colours[v]   # noqa: E731
        self.c = {k: res(spec.get(k, v)) for k, v in VH.items()}
        self.key = spec.get("key", pack.id.split("-")[0] + "".join(w.title() for w in pack.id.split("-")[1:]))
        self.name = pack.name
        self.light_bar = float(spec.get("light_bar", 0.5))
        self.height = int(spec.get("height", HEIGHT))

    def tpl(self, name):
        text = (TEMPLATES / "panel-colorizer" / f"{name}.json").read_text(encoding="utf-8")
        for k in ("shadow", "accent", "light"):
            text = text.replace(VH[k], self.c[k])
        return json.loads(text)

    @staticmethod
    def colour(c, *, enabled=True, custom=None, system=None, colour_set="View", alpha=None):
        c["enabled"] = enabled
        if custom:
            c["sourceType"], c["custom"] = 0, custom
        if system:
            c["sourceType"], c["systemColor"], c["systemColorSet"] = 1, system, colour_set
        if alpha is not None:
            c["alpha"] = alpha

    def bar(self, g, alpha, blur):
        p = g["panel"]["normal"]
        p["enabled"], p["blurBehind"] = True, blur
        self.colour(p["backgroundColor"], system="backgroundColor", alpha=alpha)
        p["radius"]["enabled"] = p["margin"]["enabled"] = False
        p["shadow"]["background"]["enabled"] = False
        b = p["border"]   # a hairline along the bottom edge
        b["enabled"], b["customSides"] = True, True
        b["custom"]["widths"] = {"left": 0, "right": 0, "top": 0, "bottom": 1}
        self.colour(b["color"], system="textColor", alpha=0.1)

    @staticmethod
    def no_bar(g):
        p = g["panel"]["normal"]
        p["enabled"], p["blurBehind"] = False, False
        p["backgroundColor"]["enabled"] = False
        p["border"]["enabled"] = False
        p["shadow"]["background"]["enabled"] = False

    @staticmethod
    def hide_plasma_bar(g):
        g["nativePanel"]["background"] = {"enabled": True, "opacity": 0, "shadow": False}

    def plain_widgets(self, g):
        w = g["widgets"]["normal"]
        w["backgroundColor"]["enabled"] = False
        w["border"]["enabled"] = False
        w["shadow"]["background"]["enabled"] = False
        for sec in ("widgets", "trayWidgets"):
            self.colour(g[sec]["normal"]["foregroundColor"], system="textColor")

    def lighten_preset(self, o, path=()):
        """Light: a semi-translucent light bar (blurred), lighter sections, ink text."""
        c = self.c
        if isinstance(o, dict):
            if "custom" in o and "sourceType" in o and isinstance(o.get("custom"), str):
                role = next((p for p in reversed(path) if p.endswith("Color")), "")
                bar = "panel" in path and "widgets" not in path and "trayWidgets" not in path
                if o["sourceType"] == 1 and o.get("systemColorSet") == "Complementary":
                    o["systemColorSet"] = "View"
                    if role == "backgroundColor" and bar:
                        o["alpha"] = self.light_bar
                if o["custom"].upper() == c["shadow"] and role == "backgroundColor":
                    o["custom"] = c["light"]
                    o["alpha"] = self.light_bar if bar else 0.68
                elif o["custom"].upper() == c["light"] and role == "foregroundColor":
                    o["custom"] = c["ink"]
                elif o["custom"].upper() == c["shadow"] and "shadow" in path:
                    o["custom"] = c["light_shadow"]
                    o["alpha"] = min(float(o.get("alpha", 1)), 0.35)
            for k, val in o.items():
                self.lighten_preset(val, path + (k,))
        elif isinstance(o, list):
            for x in o:
                self.lighten_preset(x, path)

    def normal(self):
        d = self.tpl("base"); g = d["globalSettings"]
        self.bar(g, 1.0, False); self.hide_plasma_bar(g); self.plain_widgets(g)
        return d

    def transparent(self):
        d = self.tpl("base"); g = d["globalSettings"]
        self.bar(g, 0.45, True); self.hide_plasma_bar(g); self.plain_widgets(g)
        return d

    def invisible(self, variant):
        d = self.tpl("base")
        if variant == "light":
            self.lighten_preset(d)
        g = d["globalSettings"]
        self.no_bar(g); self.hide_plasma_bar(g); self.plain_widgets(g)
        c = self.c
        text, glow, size, dy, a = ((c["light"], c["shadow"], 3, 1, 0.8) if variant == "dark"
                                   else (c["ink"], c["light"], 4, 0, 0.95))
        for sec in ("widgets", "trayWidgets"):
            w = g[sec]["normal"]
            self.colour(w["foregroundColor"], custom=text, alpha=1)
            sh = w["shadow"]["foreground"]
            sh["enabled"], sh["size"], sh["xOffset"], sh["yOffset"] = True, size, 0, dy
            self.colour(sh["color"], custom=glow, alpha=a)
        return d

    def pills(self):
        d = self.tpl("islands"); g = d["globalSettings"]
        self.no_bar(g); self.hide_plasma_bar(g)
        w = g["widgets"]["normal"]
        w["radius"] = {"enabled": True, "corner": {k: self.height // 2 for k in ("topLeft", "topRight", "bottomRight", "bottomLeft")}}
        w["shadow"]["background"]["enabled"] = False
        d[self.key] = {"islands": True}
        return d

    def cards(self):
        d = self.tpl("cards"); g = d["globalSettings"]
        self.no_bar(g); self.hide_plasma_bar(g)
        return d

    def lighten(self, d, look):
        light = copy.deepcopy(d)
        self.lighten_preset(light)
        g = light["globalSettings"]
        if look == "Normal":
            g["panel"]["normal"]["backgroundColor"]["alpha"] = 1.0
        elif look == "Transparent":
            g["panel"]["normal"]["backgroundColor"]["alpha"] = 0.55   # a light bar needs a little more body
        return light

    @staticmethod
    def slim(d):
        """Cap the top and bottom margins, so icons get most of the bar's height."""
        g = d["globalSettings"]
        for sec in ("panel", "widgets", "trayWidgets"):
            side = g[sec]["normal"].get("margin", {}).get("side")
            if side:
                for k in ("top", "bottom"):
                    side[k] = min(side.get(k, 0), VMARGIN)
        return d

    def all(self):
        for look in LOOKS:
            dark = {"Normal": self.normal, "Transparent": self.transparent, "Invisible": lambda: self.invisible("dark"),
                    "Cards": self.cards, "Pills": self.pills, "Fancy": lambda: self.tpl("fancy")}[look]()
            light = self.invisible("light") if look == "Invisible" else self.lighten(dark, look)
            for name, data in ((f"{self.name} {look}", self.slim(dark)), (f"{self.name} {look} Light", self.slim(light))):
                if name.endswith("Light"):
                    assert "Complementary" not in json.dumps(data), f"{name} uses the Complementary colour set"
                yield name, data


def build(pack: Pack) -> dict:
    # compact: a preset travels through qdbus as one argument (Linux caps one argument at 128 KiB)
    return {f"panel-colorizer/{name}/settings.json": json.dumps(data, separators=(",", ":")) + "\n"
            for name, data in Looks(pack).all()}
