"""Recolouring template artwork (Plasma Style SVGs, window borders, cursors) to a pack's colours.

The templates are Waypoint's own files. A pack without a [edition.<id>.recolour] table gets them
unchanged (that is Waypoint). Otherwise each #rrggbb in a template becomes:

1. itself, if it is a mask or pure black/white (`keep`);
2. the pack's colour for it, if `map` lists it;
3. for greys (Waypoint's graphite/steel neutrals): a point on a lightness ramp through the `map`
   colours, between `ramp_ends` (darkest, lightest);
4. for Waypoint's amber family: the first `accent` step whose lightness it reaches;
5. for Breeze's highlight blue: `highlight`;
6. otherwise itself (status colours and the like).

This is Vice Horizon's port-waypoint.py, made general. The colour maths (lightness by HLS, the
rounding in the ramp) is the same, so Vice Horizon's files come out as they were released.
"""
from __future__ import annotations

import colorsys
import re

from .colour import is_hex, rgb

HEX = re.compile(r"#([0-9a-fA-F]{6})(?![0-9a-fA-F])")
KEEP = {"#ff00ff", "#00ff00", "#000000", "#ffffff"}


def _hls(h: str):
    r, g, b = (c / 255 for c in rgb(h))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, l, s


def _mix_b(a: str, b: str, t: float) -> str:          # share t of b, Python round (as Vice Horizon)
    ra, rb = rgb(a), rgb(b)
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ra, rb))


class Recolour:
    def __init__(self, spec: dict | None, resolve):
        """spec: the pack's [edition.<id>.recolour] table; resolve(name) -> #RRGGBB."""
        self.active = bool(spec)
        spec = spec or {}
        self.map = {k.lower(): resolve(v) for k, v in spec.get("map", {}).items()}
        self.keep = {k.lower() for k in spec.get("keep", KEEP)}
        ends = [resolve(x) for x in spec.get("ramp_ends", ["#000000", "#FFFFFF"])]
        pts = sorted((_hls(k)[1], v) for k, v in self.map.items())
        self.ramp = [(0.0, ends[0])] + pts + [(1.0, ends[1])]
        self.accent = [(float(l), resolve(c)) for l, c in spec.get("accent", [])]
        self.highlight = resolve(spec["highlight"]) if "highlight" in spec else None
        self.files = {name: {k.lower(): resolve(v) for k, v in m.items()} for name, m in spec.get("files", {}).items()}

    def _ramp(self, l: float) -> str:
        for (l0, c0), (l1, c1) in zip(self.ramp, self.ramp[1:]):
            if l0 <= l <= l1:
                return _mix_b(c0, c1, 0 if l1 == l0 else (l - l0) / (l1 - l0))
        return self.ramp[-1][1]

    def colour(self, h: str) -> str:
        h = h.lower()
        if h in self.keep:
            return h
        if h in self.map:
            return self.map[h]
        hue, l, s = _hls(h)
        if s < 0.30 or (190 <= hue <= 235 and s < 0.45):          # graphite / steel neutrals
            return self._ramp(l)
        if self.accent and 18 <= hue <= 48 and s >= 0.30:          # Waypoint's amber family
            for threshold, c in self.accent:
                if l >= threshold:
                    return c
            return self.accent[-1][1]
        if self.highlight and 190 <= hue <= 215:                   # Breeze highlight blue
            return self.highlight
        return h

    def text(self, text: str, file: str | None = None) -> str:
        if not self.active:
            return text
        override = self.files.get(file or "", {})

        def sub(m):
            src = "#" + m.group(1).lower()
            if src in override:
                return override[src]
            new = self.colour(src)
            return new if new != src else m.group(0)
        return HEX.sub(sub, text)


def resolver(pack, edition):
    """name -> #RRGGBB, for recolour tables: a role, a colour name or a hex value."""
    def resolve(v):
        if is_hex(v):
            return v.upper()
        if v in edition.roles:
            return edition.roles[v]
        if v in pack.colours:
            return pack.colours[v]
        raise KeyError(f"{v!r} is not a role, a colour name or a #RRGGBB colour")
    return resolve
