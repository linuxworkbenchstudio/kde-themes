"""Kvantum theme: Kvantum/<name>/<name>.{kvconfig,svg} - Kvantum's KvArc / KvArcDark, recoloured.

KvArc (Tsu Jan, GPL-3.0) gives the structure: SVG elements, frame sizes, behaviour. Every colour
is moved onto the pack's palette by the rules in [edition.<id>.kvantum]:

  special   = {"#5294e2" = "selection_bg", ...}   exact Arc colours -> pack colours, first
  saturated = 0.35            below this HLS saturation a colour is a neutral
  lightness = [0.12, 0.92]    outside this HLS lightness a colour is a neutral too (optional)
  neutral   = "lightness"     neutrals on `ramp` = [[lightness, colour], ...] by HLS lightness
            | "luminance"     neutrals between `anchors` = [[arc colour, colour], ...] by luminance
  hues      = [{from, to, ...}]  hue ranges (degrees, from <= hue < to, may wrap past 360), first
                              match wins; each gives one of
                                colour = "name"                  a fixed colour
                                steps  = [[lightness, colour], ...]  the first step the colour is
                                                                 darker than
                                family = "name", reference = "#5294E2"  the family of `family`,
                                                                 keeping the lightness offset
                                                                 from `reference`
                              and kind = "accent" marks Arc's accent (for `focus`)
                              Colours no rule matches are neutrals.
  short_hex = true            also recolour #rgb in colour attributes
  alpha_hex = true            also recolour #rrggbbaa (keeping the alpha)
  on_accent = "selection_fg"  white glyphs on checked boxes and radios, and pressed/toggled text
  focus     = "#566170"       keyboard-focus rings in a quiet neutral instead of the accent
  disabled_buttons = 0.45     add *-disabled button frames (Kvantum would use *-normal)
  text      = "text"          Arc's own text colour (white on dark, black on light) -> this,
                              keeping its alpha; "opaque" maps it and drops strong alpha instead
  general   = {"window.color" = "window_bg", "inactive.highlight.color" = {mix = [a, b, 0.35]}}
  settings  = {...}           [%General] values;  hacks = {...}  [Hacks] values

A pack without [edition.<id>.kvantum] gets defaults() - rules built from its colour roles.

Vice Horizon's kvantum.py (lightness ramp, colour steps) and Waypoint's build_kvantum.py
(luminance anchors, accent family) are both these rules, so both releases come out as they were.
"""
from __future__ import annotations

import colorsys
import re
import xml.parsers.expat

from ..colour import luminance, rgb
from ..pack import Edition, Pack
from ..recolour import resolver
from . import TEMPLATES

SRC = {"dark": "KvArcDark", "light": "KvArc"}
NAMED = {"white": "#ffffff", "black": "#000000"}
HEX6 = re.compile(r"#([0-9A-Fa-f]{6})\b")
HEX68 = re.compile(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?(?![0-9a-fA-F])")
SHORT = re.compile(r"((?:fill|stroke|stop-color|color|flood-color)\s*[:=]\s*\"?)#([0-9A-Fa-f]{3})\b(?![0-9A-Fa-f])")
ON_ACCENT_ELEMENTS = re.compile(r"^(menu-)?(checkbox|radio)-(checked|tristate)-")
FOCUS_ELEMENTS = re.compile(r"^(common|lineedit|scrollbarslider|resize-grip)-focused")
ON_ACCENT_KEYS = {("ItemView", "text.press.color"), ("ItemView", "text.toggle.color"),
                  ("PanelButtonCommand", "text.press.color"), ("PanelButtonCommand", "text.toggle.color"),
                  ("MenuItem", "text.focus.color"), ("MenuBarItem", "text.focus.color")}
ON_ACCENT_PH, FOCUS_PH = "#ONACCENTX", "#FOCUSNEUTRALX"


def _hls(h: str):
    r, g, b = (c / 255 for c in rgb(h))
    return colorsys.rgb_to_hls(r, g, b)


def _hex(c) -> str:
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(x))) for x in c)


class Rules:
    def __init__(self, spec: dict, resolve):
        self.resolve = resolve
        self.special = {k.lower(): resolve(v) for k, v in spec.get("special", {}).items()}
        self.saturated = float(spec.get("saturated", 0.35))
        self.lightness = spec.get("lightness")
        self.neutral = spec.get("neutral", "lightness")
        self.ramp = [(float(l), resolve(c)) for l, c in spec.get("ramp", [])]
        self.anchors = sorted((luminance(resolve(a)), rgb(resolve(b))) for a, b in spec.get("anchors", []))
        self.hues = spec.get("hues", [])

    def _neutral(self, h: str) -> str:
        if self.neutral == "luminance":
            pts, x = self.anchors, luminance(h)
            if x <= pts[0][0]:
                return _hex(pts[0][1])
            for (l0, c0), (l1, c1) in zip(pts, pts[1:]):
                if l0 <= x <= l1:
                    t = 0 if l1 == l0 else (x - l0) / (l1 - l0)
                    return _hex([a + (b - a) * t for a, b in zip(c0, c1)])
            return _hex(pts[-1][1])
        l = _hls(h)[1]
        for (l0, c0), (l1, c1) in zip(self.ramp, self.ramp[1:]):
            if l0 <= l <= l1:
                t = 0 if l1 == l0 else (l - l0) / (l1 - l0)
                a, b = rgb(c0), rgb(c1)
                return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))
        return self.ramp[-1][1]

    def rule(self, h: str):
        hh, l, s = _hls(h)
        if s < self.saturated:
            return None
        if self.lightness and not (self.lightness[0] < l < self.lightness[1]):
            return None
        deg = hh * 360
        for r in self.hues:
            a, b = r["from"], r["to"]
            if (a <= deg < b) if a < b else (deg >= a or deg < b):
                return r
        return None

    def colour(self, h: str) -> str:
        if h.lower() in self.special:
            return self.special[h.lower()]
        r = self.rule(h)
        if r is None:
            return self._neutral(h)
        if "colour" in r:
            return self.resolve(r["colour"])
        l = _hls(h)[1]
        if "steps" in r:
            for threshold, c in r["steps"]:
                if l < threshold:
                    return self.resolve(c)
            return self.resolve(r["steps"][-1][1])
        th, tl, ts = _hls(self.resolve(r["family"]))
        nl = max(0.05, min(0.95, tl + (l - _hls(r["reference"])[1])))
        return _hex(c * 255 for c in colorsys.hls_to_rgb(th, nl, ts))

    def is_accent(self, h: str) -> bool:
        r = self.rule(h)
        return bool(r and r.get("kind") == "accent")


def _elements(text: str, pattern, change):
    """Apply change(segment) inside every element whose id matches pattern."""
    starts, spans, depth = {}, [], []
    p = xml.parsers.expat.ParserCreate()
    data = text.encode("utf-8")

    def start(tag, at):
        i = at.get("id", "")
        depth.append(i if pattern.match(i) else None)
        if depth[-1]:
            starts[len(depth)] = p.CurrentByteIndex

    def end(tag):
        if depth[-1]:
            spans.append((starts.pop(len(depth)), p.CurrentByteIndex))
        depth.pop()
    p.StartElementHandler, p.EndElementHandler = start, end
    p.Parse(data, True)
    out, pos = [], 0
    for a, b in sorted(spans):
        if a < pos:
            continue
        out += [data[pos:a].decode("utf-8"), change(data[a:b].decode("utf-8"))]
        pos = b
    out.append(data[pos:].decode("utf-8"))
    return "".join(out)


def _mark_on_accent(seg: str) -> str:
    def near_white(m):
        v = NAMED.get(m.group(3).lower(), {"#fff": "#ffffff"}.get(m.group(3).lower(), m.group(3).lower()))
        return m.group(1) + m.group(2) + ON_ACCENT_PH if luminance(v) > 0.85 else m.group(0)
    return re.sub(r"(?i)(fill|stroke|stop-color|color)(\s*[:=]\s*\"?)(#[0-9a-f]{6}|#fff|white)\b", near_white, seg)


def add_disabled_buttons(svg: str, opacity: float) -> str:
    """Kvantum falls back to *-normal when *-disabled is missing, so disabled buttons look live.
    Clone every button-normal* element as button-disabled* at reduced opacity."""
    data = svg.encode("utf-8")
    spans, starts, depth = [], {}, []
    p = xml.parsers.expat.ParserCreate()

    def start(tag, at):
        i = at.get("id", "")
        hit = re.fullmatch(r"button-normal(-(top|bottom|left|right|topleft|topright|bottomleft|bottomright))?", i)
        depth.append(i if hit and not any(depth) else None)
        if depth[-1]:
            a = p.CurrentByteIndex
            tag_end = data.index(b">", a)
            starts[len(depth)] = (a, tag_end + 1 if data[tag_end - 1:tag_end] == b"/" else None)

    def end(tag):
        if depth[-1]:
            a, fixed = starts.pop(len(depth))
            spans.append((a, fixed or data.index(b">", p.CurrentByteIndex) + 1))
        depth.pop()
    p.StartElementHandler, p.EndElementHandler = start, end
    p.Parse(data, True)
    clones = []
    for a, b in spans:
        frag = data[a:b].decode("utf-8")
        frag = re.sub(r'id="button-normal', 'id="button-disabled', frag, count=1)
        frag = re.sub(r'id="(?!button-disabled)([^"]+)"', r'id="\1-dis"', frag)   # keep ids unique
        frag = re.sub(r"^<(\w+)", rf'<\1 opacity="{opacity}"', frag, count=1)
        clones.append(frag)
    if not clones:
        return svg
    pos = svg.rindex("</svg>")
    return svg[:pos] + "\n".join(clones) + "\n" + svg[pos:]


def recolour_svg(svg: str, spec: dict, rules: Rules, resolve) -> str:
    if spec.get("on_accent"):
        svg = _elements(svg, ON_ACCENT_ELEMENTS, _mark_on_accent)
    if spec.get("focus"):
        svg = _elements(svg, FOCUS_ELEMENTS,
                        lambda seg: HEX6.sub(lambda m: FOCUS_PH if rules.is_accent("#" + m.group(1)) else m.group(0), seg))
    if spec.get("alpha_hex"):
        svg = HEX68.sub(lambda m: rules.colour("#" + m.group(1)) + (m.group(2) or ""), svg)
    else:
        svg = HEX6.sub(lambda m: rules.colour("#" + m.group(1)), svg)
    if spec.get("short_hex"):
        svg = SHORT.sub(lambda m: m.group(1) + rules.colour("#" + "".join(c * 2 for c in m.group(2))), svg)
    if spec.get("on_accent"):
        svg = svg.replace(ON_ACCENT_PH, resolve(spec["on_accent"]))
    if spec.get("focus"):
        svg = svg.replace(FOCUS_PH, resolve(spec["focus"]))
    if "disabled_buttons" in spec:
        svg = add_disabled_buttons(svg, spec["disabled_buttons"])
    return svg


def _text_value(value: str, spec: dict, rules: Rules, resolve, dark: bool) -> str:
    v = NAMED.get(value.strip().lower(), value.strip())
    m = re.fullmatch(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?", v)
    if not m:
        return value
    base, alpha = "#" + m.group(1).lower(), m.group(2) or ""
    mode = spec.get("text", "opaque")
    if mode == "opaque":
        _, l, s = _hls(base)
        if alpha and int(alpha, 16) >= 0xB4 and s < 0.1 and l in (0.0, 1.0):
            alpha = ""                       # Arc's translucent black/white text -> opaque text
        return rules.colour(base) + alpha
    if base == ("#ffffff" if dark else "#000000"):
        return resolve(mode) + alpha
    return rules.colour(base) + alpha


def recolour_kvconfig(cfg: str, spec: dict, rules: Rules, resolve, dark: bool, author: str, comment: str) -> str:
    general = {k: _general(v, resolve) for k, v in spec.get("general", {}).items()}
    tables = {"%General": dict(spec.get("settings", {}), author=author, comment=comment),
              "Hacks": spec.get("hacks", {})}
    tables = {sec: {k: _ini(v) for k, v in kv.items()} for sec, kv in tables.items()}
    out, section, seen = [], None, set()

    def flush():
        missing = [f"{k}={v}" for k, v in tables.get(section, {}).items() if k not in seen]
        # missing keys go at the end of their section, before the blank line that closes it
        i = len(out)
        while i > 0 and not out[i - 1].strip():
            i -= 1
        out[i:i] = missing

    for line in cfg.splitlines():
        sm = re.match(r"^\[(.+)\]\s*$", line)
        if sm:
            flush()
            section, seen = sm.group(1), set()
            out.append(line)
            continue
        km = re.match(r"^([\w.\-]+)=(.*)$", line)
        if not km:
            out.append(line)
            continue
        key, val = km.groups()
        if key in tables.get(section, {}):
            val = tables[section][key]
            seen.add(key)
        elif section == "GeneralColors" and key in general:
            val = general[key]
        elif (section, key) in ON_ACCENT_KEYS and spec.get("on_accent"):
            val = resolve(spec["on_accent"])
        else:
            val = _text_value(val, spec, rules, resolve, dark)
        out.append(f"{key}={val}")
    flush()
    return "\n".join(out) + "\n"


def _ini(v) -> str:
    return ("true" if v else "false") if isinstance(v, bool) else str(v)


def _general(v, resolve) -> str:
    if isinstance(v, dict):                  # {mix = [a, b, t]}: share t of b
        a, b, t = v["mix"]
        ra, rb = rgb(resolve(a)), rgb(resolve(b))
        return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ra, rb))
    return resolve(v)


OPAQUE = ("kaffeine,kmplayer,subtitlecomposer,kdenlive,vlc,avidemux,avidemux2_qt4,avidemux3_qt4,avidemux3_qt5,"
          "kamoso,QtCreator,VirtualBox,VirtualBoxVM,trojita,dragon,digikam,lyx,krita,obs,libreoffice,soffice.bin,"
          "blender,freecad,qgis")


def defaults(dark: bool) -> dict:
    """Rules for a pack without its own: Arc's neutrals onto the pack's roles by luminance, Arc's
    blues to the accent family, its reds to the negative family; translucent windows and menus."""
    anchors = ([["#000000", "#000000"], ["#2F343F", "base_bg"], ["#383C4A", "window_bg"], ["#404552", "button_bg"],
                ["#5A616E", "border"], ["#92959D", "text_muted"], ["#D3DAE3", "text"], ["#FFFFFF", "#FFFFFF"]]
               if dark else
               [["#000000", "#000000"], ["#323232", "text"], ["#7B7B7B", "text_muted"], ["#CFD6E6", "border"],
                ["#F5F6F7", "window_bg"], ["#FFFFFF", "view_bg"]])
    return {
        "neutral": "luminance", "anchors": anchors, "lightness": [0.12, 0.92],
        "hues": [{"from": 185, "to": 300, "kind": "accent", "family": "accent", "reference": "#5294E2"},
                 {"from": 340, "to": 20, "family": "negative", "reference": "#F04A50"}],
        "short_hex": True, "alpha_hex": True, "on_accent": "selection_fg", "focus": "border_strong",
        "disabled_buttons": 0.45, "text": "text",
        "general": {"window.color": "window_bg", "base.color": "view_bg", "alt.base.color": "view_alt_bg",
                    "button.color": "button_bg", "light.color": "border" if dark else "#FFFFFF",
                    "mid.light.color": "button_bg", "dark.color": "#000000" if dark else "border_strong",
                    "mid.color": "base_bg" if dark else "border", "highlight.color": "selection_bg",
                    "inactive.highlight.color": {"mix": ["selection_bg", "window_bg", 0.35]},
                    "text.color": "text", "window.text.color": "text", "button.text.color": "text",
                    "disabled.text.color": "text_disabled", "tooltip.text.color": "tooltip_fg",
                    "highlight.text.color": "selection_fg", "link.color": "link", "link.visited.color": "visited",
                    "progress.indicator.text.color": "selection_fg"},
        "settings": {"translucent_windows": True, "blurring": True, "popup_blurring": True,
                     "reduce_window_opacity": 30, "reduce_menu_opacity": 30, "no_inactiveness": True,
                     "splitter_width": 1, "menu_blur_radius": 6, "tooltip_blur_radius": 6, "opaque": OPAQUE},
        "hacks": {"blur_translucent": True, "transparent_dolphin_view": True, "respect_darkness": True},
    }


def build(pack: Pack) -> dict:
    out = {}
    licence = (TEMPLATES / "licences" / "GPL-3.0-or-later.txt").read_text(encoding="utf-8")
    for ed in pack.editions.values():
        spec = ed.raw.get("kvantum") or defaults(ed.template == "dark")
        resolve = resolver(pack, ed)
        rules = Rules(spec, resolve)
        name = pack.file_name("kvantum", ed)
        src = SRC[ed.template]
        svg = recolour_svg((TEMPLATES / "kvantum" / f"{src}.svg").read_text(encoding="utf-8"), spec, rules, resolve)
        header = pack.describe("kvantum_svg", ed)
        if header:
            svg = svg.replace("<svg", f"<!-- {header} -->\n<svg", 1)
        cfg = recolour_kvconfig((TEMPLATES / "kvantum" / f"{src}.kvconfig").read_text(encoding="utf-8"), spec, rules,
                                resolve, ed.template == "dark", pack.describe("kvantum_author", ed),
                                pack.describe("kvantum_comment", ed))
        base = f"Kvantum/{name}/"
        out[base + f"{name}.svg"] = svg
        out[base + f"{name}.kvconfig"] = cfg
        out[base + "COPYING"] = licence
    return out
