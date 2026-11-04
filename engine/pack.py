"""Theme packs: one pack.toml per theme, read and checked here.

A pack gives each edition (dark, light) a small named palette. Everything else in the pack
refers to those names ("raised", "accent") or gives a #RRGGBB value directly; a name can also
point into another edition ("dark.window"). The engine turns the names into colours, so a theme's
colours live in one place and every generated file agrees with them.
"""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .colour import is_hex

# ----------------------------------------------------------------------------- the format
# palette names every edition must give, and the optional ones with what they fall back to
PALETTE_REQUIRED = ("window", "raised", "line", "text", "muted", "disabled",
                    "accent", "accent_bright", "on_accent", "negative", "neutral", "positive")
PALETTE_OPTIONAL = {
    "base": "window",       # the deepest surface: terminal background, inactive title bar
    "control": "raised",    # buttons
    "link": "accent",
    "visited": "muted",
}

# which palette colour fills each slot of the KDE colour scheme (an edition can override any)
KDE_DEFAULTS = {
    "window": "window", "window_alt": "raised",
    "view": "window", "view_alt": "raised",
    "header": "window", "header_alt": "raised",
    "button": "control", "button_alt": "window",
    "tooltip": "window", "tooltip_alt": None,        # None: same as tooltip
    "titlebar": "window", "titlebar_inactive": "base",
    "text": "text", "muted": "muted",
    "accent": "accent", "accent_bright": "accent_bright", "on_accent": "on_accent",
    "selection_bright_text": "#FFFFFF",
    "link": "link", "visited": "visited",
    "negative": "negative", "neutral": "neutral", "positive": "positive",
    "complementary": "dark",     # the edition whose colours panels and OSDs use (dark in both)
}

TERMINAL_DEFAULTS = {
    "background": "base", "background_faint": None, "background_intense": "window",
    "foreground": "text", "foreground_faint": "muted", "foreground_intense": "#FFFFFF",
    "faint_amount": 0.55,       # faint ANSI colours: this much of the colour over the background
    "opacity": 1.0, "blur": False,
}

THEME_KEYS = {"id", "name", "command", "brand", "version", "license", "editions", "names",
              "lookandfeel_id", "previous_ids", "parts", "website"}
LNF_ID = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*){2,}$")   # org.thelinuxworkbench.waypoint
OLD_ID = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$")     # older ids can be shorter (org.waypoint)
NAME_DEFAULTS = {
    # file and scheme names. {Name} "Vice Horizon", {Slug} "Vice-Horizon", {Compact} "ViceHorizon",
    # {Edition} "Dark". Keep these as they are once a theme has users: renaming the files leaves
    # people's settings pointing at names that no longer exist.
    "color_scheme": "{Slug}-{Edition}",
    "konsole": "{Slug}-{Edition}",
}


class PackError(Exception):
    def __init__(self, path: Path, problems: list[str]):
        self.problems = problems
        super().__init__(f"{path}:\n  " + "\n  ".join(problems))


@dataclass
class Edition:
    id: str                         # "dark"
    name: str                       # "Dark"
    palette: dict[str, str]         # every name resolved to #RRGGBB
    kde: dict[str, str]
    terminal: dict
    ansi: list[tuple[str, str]]     # (normal, intense) x 8, resolved
    ansi_faint: list[str | None]


@dataclass
class Pack:
    root: Path
    id: str
    name: str
    command: str
    brand: str
    version: str
    license: str
    names: dict[str, str]
    lookandfeel_id: str = ""        # Global Theme id without the edition: org.thelinuxworkbench.waypoint
    previous_ids: list[str] = field(default_factory=list)   # older ids, removed on upgrade
    parts: list[str] = field(default_factory=list)          # the parts the engine makes for this theme
    website: str = ""
    editions: dict[str, Edition] = field(default_factory=dict)

    def file_name(self, kind: str, edition: Edition) -> str:
        return self.names[kind].format(Name=self.name, Slug=self.name.replace(" ", "-"),
                                       Compact=self.name.replace(" ", ""), Edition=edition.name)

    def display(self, edition: Edition) -> str:
        return f"{self.name} {edition.name}"


# ----------------------------------------------------------------------------- loading
def load(path: str | Path) -> Pack:
    path = Path(path)
    file = path / "pack.toml" if path.is_dir() else path
    with open(file, "rb") as f:
        data = tomllib.load(f)
    problems: list[str] = []

    theme = data.get("theme", {})
    for k in theme:
        if k not in THEME_KEYS:
            problems.append(f"[theme] {k}: not a known setting ({', '.join(sorted(THEME_KEYS))})")
    for k in ("id", "name", "command", "brand", "version", "lookandfeel_id"):
        if not isinstance(theme.get(k), str) or not theme.get(k):
            problems.append(f"[theme] {k}: missing")
    lnf = theme.get("lookandfeel_id", "")
    if lnf and not LNF_ID.match(lnf):
        problems.append(f"[theme] lookandfeel_id = {lnf!r}: needs a lowercase dotted id like org.thelinuxworkbench.mytheme")
    prev = theme.get("previous_ids", [])
    if not (isinstance(prev, list) and all(isinstance(x, str) and OLD_ID.match(x) for x in prev)):
        problems.append("[theme] previous_ids: needs a list of dotted ids")
    from .parts import PARTS          # here, not at the top: the parts import this module
    parts = theme.get("parts", list(PARTS))
    for x in parts:
        if x not in PARTS:
            problems.append(f"[theme] parts: {x!r} is not a part ({', '.join(PARTS)})")
    names = dict(NAME_DEFAULTS)
    for k, v in theme.get("names", {}).items():
        if k not in NAME_DEFAULTS:
            problems.append(f"[theme.names] {k}: not a known file name ({', '.join(NAME_DEFAULTS)})")
        names[k] = v
    edition_ids = theme.get("editions", ["dark", "light"])

    raw = data.get("edition", {})
    for e in raw:
        if e not in edition_ids:
            problems.append(f"[edition.{e}]: not listed in [theme] editions")

    # palettes first, so that names can point into other editions
    palettes: dict[str, dict[str, str]] = {}
    for e in edition_ids:
        ed = raw.get(e)
        if ed is None:
            problems.append(f"[edition.{e}]: missing")
            continue
        pal = dict(ed.get("palette", {}))
        for k, v in pal.items():
            if k not in PALETTE_REQUIRED and k not in PALETTE_OPTIONAL:
                problems.append(f"[edition.{e}.palette] {k}: not a palette name")
            elif not is_hex(v):
                problems.append(f"[edition.{e}.palette] {k} = {v!r}: needs a #RRGGBB colour")
        for k in PALETTE_REQUIRED:
            if k not in pal:
                problems.append(f"[edition.{e}.palette] {k}: missing")
        for k, fallback in PALETTE_OPTIONAL.items():
            pal.setdefault(k, pal.get(fallback, "#000000"))
        palettes[e] = pal

    def colour(value, where: str, e: str) -> str:
        if is_hex(value):
            return value.upper()
        if isinstance(value, str):
            ed, _, name = value.rpartition(".")
            pal = palettes.get(ed or e)
            if pal is not None and name in pal:
                return pal[name].upper()
        problems.append(f"{where} = {value!r}: not a palette name or a #RRGGBB colour")
        return "#000000"

    pack = Pack(path if path.is_dir() else path.parent, theme.get("id", ""), theme.get("name", ""),
                theme.get("command", ""), theme.get("brand", ""), theme.get("version", ""),
                theme.get("license", "GPL-3.0-or-later"), names, lnf, list(prev) if isinstance(prev, list) else [],
                [x for x in parts if x in PARTS], theme.get("website", ""))

    for e in edition_ids:
        ed = raw.get(e)
        if ed is None or e not in palettes:
            continue
        pal = {k: v.upper() for k, v in palettes[e].items()}
        # KDE slots
        kde_in = ed.get("kde", {})
        for k in kde_in:
            if k not in KDE_DEFAULTS:
                problems.append(f"[edition.{e}.kde] {k}: not a KDE colour slot")
        kde = {}
        for k, default in KDE_DEFAULTS.items():
            v = kde_in.get(k, default)
            if k == "complementary":
                if v not in edition_ids:
                    problems.append(f"[edition.{e}.kde] complementary = {v!r}: not an edition")
                kde[k] = v
            elif v is None:
                continue
            else:
                kde[k] = colour(v, f"[edition.{e}.kde] {k}", e)
        kde.setdefault("tooltip_alt", kde["tooltip"])
        # terminal
        term_in = ed.get("terminal", {})
        for k in term_in:
            if k not in TERMINAL_DEFAULTS and k not in ("ansi", "ansi_faint"):
                problems.append(f"[edition.{e}.terminal] {k}: not a terminal setting")
        term = {}
        for k, default in TERMINAL_DEFAULTS.items():
            v = term_in.get(k, default)
            if k in ("faint_amount", "opacity"):
                if not isinstance(v, (int, float)) or not 0 <= v <= 1:
                    problems.append(f"[edition.{e}.terminal] {k} = {v!r}: needs a number from 0 to 1")
                term[k] = float(v)
            elif k == "blur":
                term[k] = bool(v)
            elif v is not None:
                term[k] = colour(v, f"[edition.{e}.terminal] {k}", e)
        term.setdefault("background_faint", term["background"])
        ansi_in = term_in.get("ansi", [])
        ansi = []
        if len(ansi_in) != 8:
            problems.append(f"[edition.{e}.terminal] ansi: needs 8 [normal, intense] pairs, has {len(ansi_in)}")
        for i, pair in enumerate(ansi_in[:8]):
            if not (isinstance(pair, list) and len(pair) == 2):
                problems.append(f"[edition.{e}.terminal] ansi[{i}]: needs [normal, intense]")
                ansi.append(("#000000", "#000000"))
                continue
            ansi.append((colour(pair[0], f"[edition.{e}.terminal] ansi[{i}][0]", e),
                         colour(pair[1], f"[edition.{e}.terminal] ansi[{i}][1]", e)))
        faint_in = term_in.get("ansi_faint", [None] * 8)
        faint = [None if v in (None, "", "auto") else colour(v, f"[edition.{e}.terminal] ansi_faint[{i}]", e)
                 for i, v in enumerate(list(faint_in) + [None] * (8 - len(faint_in)))][:8]
        pack.editions[e] = Edition(e, ed.get("name", e.title()), pal, kde, term, ansi, faint)

    if problems:
        raise PackError(file, problems)
    return pack
