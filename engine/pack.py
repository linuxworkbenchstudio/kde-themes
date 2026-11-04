"""Theme packs: one pack.toml per theme, read and checked here.

A pack has named colours ([colours], shared by every edition) and, per edition, colour roles
([edition.<id>.roles]: window_bg, view_bg, text, accent, ...). Everything else refers to a role
name, a colour name, another edition's role ("dark.window_bg") or gives #RRGGBB. The engine turns
the names into colours, so every generated file agrees with the pack.
"""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .colour import is_hex, mix

# ----------------------------------------------------------------------------- roles
# the roles every edition gives
ROLES_REQUIRED = ("window_bg", "view_bg", "border", "text", "text_muted", "text_disabled",
                  "accent", "selection_bg", "selection_fg", "negative", "neutral", "positive")
# the others, and what each falls back to (in this order, so a fallback can use an earlier one)
ROLES_OPTIONAL = {
    "view_alt_bg": "window_bg",         # alternate rows
    "header_bg": "window_bg",           # title bars, headers
    "header_inactive_bg": "window_bg",
    "button_bg": "view_alt_bg",
    "button_alt_bg": "window_bg",
    "surface_raised": "view_alt_bg",    # popups, cards
    "hover_bg": "button_bg",
    "sidebar_bg": "window_bg",
    "border_strong": "border",
    "base_bg": "view_bg",               # deepest surface: terminal background, inactive title bar
    "selection_alt_bg": "accent",
    "hover_decoration": "accent",
    "highlight": "accent",
    "warm": "accent",
    "link": "accent",
    "visited": "text_muted",
    "active_text": "accent",
    "suggested_bg": "accent",
    "suggested_fg": "selection_fg",
    "destructive_bg": "negative",
    "destructive_fg": "selection_fg",
    "notification": "accent",
    "tooltip_bg": "surface_raised",
    "tooltip_fg": "text",
    "complementary_bg": "window_bg",
    "complementary_fg": "text",
    "osd_bg": "window_bg",
}
ROLES = ROLES_REQUIRED + tuple(ROLES_OPTIONAL)

KDE_GROUPS = ("Window", "View", "Button", "Selection", "Tooltip", "Complementary", "Header", "Header][Inactive")
KDE_KEYS = ("BackgroundNormal", "BackgroundAlternate", "DecorationFocus", "DecorationHover", "ForegroundNormal",
            "ForegroundInactive", "ForegroundActive", "ForegroundLink", "ForegroundVisited", "ForegroundNegative",
            "ForegroundNeutral", "ForegroundPositive")
WM_KEYS = ("activeBackground", "activeBlend", "activeForeground", "inactiveBackground", "inactiveBlend", "inactiveForeground")
KDE_SETTINGS = {"effects_colour": "window_bg", "change_selection_colour": True, "widget_style": "",
                "complementary": "dark"}

TERMINAL_SETTINGS = {
    "background": "base_bg", "background_faint": None, "background_intense": "window_bg",
    "foreground": "text", "foreground_faint": "text_muted", "foreground_intense": "#FFFFFF",
    "faint_amount": 0.55,       # faint ANSI colours: this much of the colour over the background
    "opacity": 1.0, "blur": False,
}

THEME_KEYS = {"id", "name", "command", "brand", "version", "license", "editions", "names",
              "lookandfeel_id", "previous_ids", "parts", "website", "fastfetch", "gtk"}
LNF_ID = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*){2,}$")      # org.thelinuxworkbench.waypoint
OLD_ID = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$")         # older ids can be shorter
NAME_DEFAULTS = {
    # file and scheme names. {Name} "Vice Horizon", {Slug} "Vice-Horizon", {Compact} "ViceHorizon",
    # {Edition} "Dark". Keep these once a theme has users: renaming the files leaves people's
    # settings pointing at names that no longer exist.
    "color_scheme": "{Slug}-{Edition}",
    "konsole": "{Slug}-{Edition}",
    "plasma_style": "{Slug}-{Edition}",
    "aurorae": "{Slug}-{Edition}",
    "cursors": "{Slug}-Cursors-{Edition}",
    "kvantum": "{Slug}-{Edition}",
    "gtk": "{Slug}-{Edition}",
    "icons": "{Slug}-{Edition}",
}
EDITION_KEYS = {"name", "roles", "kde", "terminal", "text", "recolour", "template", "kvantum", "gtk"}
TEXT_DEFAULTS = {   # descriptions in the theme's metadata; {Name} and {Edition} are filled in
    "plasma": "{Name} {Edition} Plasma style",
    "decoration": "{Name} {Edition} window decoration",
    "cursors": "Breeze cursors recoloured for {Name} {Edition} (GPL-2.0-or-later, KDE)",
    "kvantum_author": "{Brand} (derived from Kvantum KvArc by Tsu Jan, GPL-3.0)",
    "kvantum_comment": "{Name} {Edition} Kvantum theme (based on KvArc)",
    "kvantum_svg": "",                 # a comment at the top of the Kvantum SVG; empty for none
    # GTK stylesheets: {Edition} the compiled edition (Dark in gtk-dark.css), {Theme} the folder's
    # edition, {version} gtk-3.0 / gtk-4.0, {file} gtk.css / gtk-dark.css
    "gtk3_header": "/* {Name} {Edition} - GTK 3 ({Brand}). GTK 3's own Adwaita theme (LGPL-2.1-or-later),\n"
                   "   compiled with the {Name} palette. */\n\n",
    "gtk4_header": "/* {Name} {Edition} - GTK 4 ({Brand}). GTK's own theme (LGPL-2.1-or-later),\n"
                   "   compiled with the {Name} palette. Needs GTK 4.16+. */\n\n",
}


class PackError(Exception):
    def __init__(self, path: Path, problems: list[str]):
        self.problems = problems
        super().__init__(f"{path}:\n  " + "\n  ".join(problems))


@dataclass
class Edition:
    id: str                         # "dark"
    name: str                       # "Dark"
    roles: dict[str, str]           # every role, resolved to #RRGGBB
    kde: dict                       # groups -> {key: colour or None}, wm, settings
    terminal: dict
    ansi: list[tuple[str, str]]     # (normal, bright) x 8
    ansi_faint: list[str | None]
    raw: dict = field(default_factory=dict)     # the edition's table as written, for later parts
    text: dict = field(default_factory=dict)
    template: str = ""                          # which template edition its artwork starts from


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
    lookandfeel_id: str = ""
    previous_ids: list[str] = field(default_factory=list)
    parts: list[str] = field(default_factory=list)
    website: str = ""
    colours: dict[str, str] = field(default_factory=dict)
    editions: dict[str, Edition] = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    def file_name(self, kind: str, edition: Edition) -> str:
        return self.names[kind].format(Name=self.name, Slug=self.name.replace(" ", "-"), id=self.id,
                                       Compact=self.name.replace(" ", ""), Edition=edition.name, edition=edition.id)

    def describe(self, kind: str, edition: Edition) -> str:
        return edition.text[kind].format(Name=self.name, Edition=edition.name, Brand=self.brand, Version=self.version)

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
        prev = []
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

    colours = {}
    for k, v in data.get("colours", {}).items():
        if not is_hex(v):
            problems.append(f"[colours] {k} = {v!r}: needs a #RRGGBB colour")
        elif k in ROLES:
            problems.append(f"[colours] {k}: is a role name; give colours their own names")
        else:
            colours[k] = v.upper()

    raw = data.get("edition", {})
    for e in raw:
        if e not in edition_ids:
            problems.append(f"[edition.{e}]: not listed in [theme] editions")

    # roles first, so that later values can point into any edition
    roles_by_ed: dict[str, dict[str, str]] = {}
    for e in edition_ids:
        ed = raw.get(e)
        if ed is None:
            problems.append(f"[edition.{e}]: missing")
            continue
        given = ed.get("roles", {})
        roles: dict[str, str] = {}
        for k, v in given.items():
            if k not in ROLES:
                problems.append(f"[edition.{e}.roles] {k}: not a role")
        for k in ROLES_REQUIRED:
            if k not in given:
                problems.append(f"[edition.{e}.roles] {k}: missing")
        for k in ROLES:
            v = given.get(k)
            if v is None:
                fb = ROLES_OPTIONAL.get(k)
                roles[k] = roles.get(fb, "#000000") if fb else "#000000"
                continue
            if is_hex(v):
                roles[k] = v.upper()
            elif v in colours:
                roles[k] = colours[v]
            elif v in roles:            # an earlier role of the same edition
                roles[k] = roles[v]
            else:
                problems.append(f"[edition.{e}.roles] {k} = {v!r}: not a colour name or a #RRGGBB colour")
                roles[k] = "#000000"
        roles_by_ed[e] = roles

    def colour(value, where: str, e: str) -> str:
        if is_hex(value):
            return value.upper()
        if isinstance(value, str):
            if value in colours:
                return colours[value]
            ed, _, name = value.rpartition(".")
            r = roles_by_ed.get(ed or e)
            if r is not None and name in r:
                return r[name]
        problems.append(f"{where} = {value!r}: not a role, a colour name or a #RRGGBB colour")
        return "#000000"

    pack = Pack(path if path.is_dir() else path.parent, theme.get("id", ""), theme.get("name", ""),
                theme.get("command", ""), theme.get("brand", ""), theme.get("version", ""),
                theme.get("license", "GPL-3.0-or-later"), names, lnf, list(prev),
                [x for x in parts if x in PARTS], theme.get("website", ""), colours, raw=data)

    for e in edition_ids:
        ed = raw.get(e)
        if ed is None or e not in roles_by_ed:
            continue
        r = roles_by_ed[e]
        for k in ed:
            if k not in EDITION_KEYS:
                problems.append(f"[edition.{e}] {k}: not a known table ({', '.join(sorted(EDITION_KEYS))})")
        text = dict(TEXT_DEFAULTS)
        for k, v in ed.get("text", {}).items():
            if k not in TEXT_DEFAULTS:
                problems.append(f"[edition.{e}.text] {k}: not a known text ({', '.join(TEXT_DEFAULTS)})")
            text[k] = v
        template = ed.get("template", e if e in ("dark", "light") else "dark")
        if template not in ("dark", "light"):
            problems.append(f"[edition.{e}] template = {template!r}: needs \"dark\" or \"light\"")
        kde = _kde(ed.get("kde", {}), r, e, edition_ids, colour, problems)
        term, ansi, faint = _terminal(ed.get("terminal", {}), e, colour, problems)
        pack.editions[e] = Edition(e, ed.get("name", e.title()), r, kde, term, ansi, faint, ed, text, template)

    # Complementary comes from another edition's roles: resolve now that all are loaded
    for ed in pack.editions.values():
        src = pack.editions.get(ed.kde["settings"]["complementary"], ed)
        comp = _group_defaults("Complementary", src.roles)
        comp.update(ed.kde["groups"].pop("_complementary_overrides"))
        ed.kde["groups"]["Complementary"] = comp

    if problems:
        raise PackError(file, problems)
    return pack


def _group_defaults(group: str, r: dict) -> dict:
    """Vice Horizon's mapping, the engine's default."""
    def g(bg, alt, fg, inactive=None):
        return {"BackgroundNormal": bg, "BackgroundAlternate": alt, "DecorationFocus": r["accent"],
                "DecorationHover": r["hover_decoration"], "ForegroundNormal": fg,
                "ForegroundInactive": inactive or r["text_muted"], "ForegroundActive": r["active_text"],
                "ForegroundLink": r["link"], "ForegroundVisited": r["visited"], "ForegroundNegative": r["negative"],
                "ForegroundNeutral": r["neutral"], "ForegroundPositive": r["positive"]}
    if group == "Window":
        return g(r["window_bg"], r["view_alt_bg"], r["text"])
    if group == "View":
        return g(r["view_bg"], r["view_alt_bg"], r["text"])
    if group == "Button":
        return g(r["button_bg"], r["button_alt_bg"], r["text"])
    if group == "Selection":
        s = g(r["selection_bg"], r["selection_alt_bg"], r["selection_fg"],
              inactive=mix(r["selection_fg"], r["selection_bg"], 0.75))
        s.update(DecorationFocus=r["selection_alt_bg"], DecorationHover=r["highlight"])
        return s
    if group == "Tooltip":
        return g(r["tooltip_bg"], r["view_alt_bg"], r["tooltip_fg"])
    if group == "Complementary":
        return g(r["window_bg"], r["surface_raised"], r["text"])
    if group == "Header":
        return g(r["header_bg"], r["window_bg"], r["text"])
    if group == "Header][Inactive":
        return g(r["header_inactive_bg"], r["header_bg"], r["text_muted"])
    raise KeyError(group)


def _kde(table: dict, r: dict, e: str, edition_ids, colour, problems) -> dict:
    settings = dict(KDE_SETTINGS)
    groups: dict[str, dict] = {}
    for k, v in table.items():
        if k in KDE_SETTINGS:
            settings[k] = v
        elif k not in KDE_GROUPS and k not in ("WM",):
            problems.append(f"[edition.{e}.kde] {k}: not a KDE colour group or setting "
                            f"({', '.join(KDE_GROUPS + ('WM',) + tuple(KDE_SETTINGS))})")
    if settings["complementary"] not in edition_ids:
        problems.append(f"[edition.{e}.kde] complementary = {settings['complementary']!r}: not an edition")
    settings["effects_colour"] = colour(settings["effects_colour"], f"[edition.{e}.kde] effects_colour", e)

    def overrides(name, allowed):
        out = {}
        for k, v in table.get(name, {}).items():
            if k not in allowed:
                problems.append(f"[edition.{e}.kde.{name}] {k}: not a key of this group")
            elif v == "":
                out[k] = None                       # leave the key out
            else:
                out[k] = colour(v, f"[edition.{e}.kde.{name}] {k}", e)
        return out

    for gname in KDE_GROUPS:
        if gname == "Complementary":
            groups["_complementary_overrides"] = overrides(gname, KDE_KEYS)
            continue
        grp = _group_defaults(gname, r)
        grp.update(overrides(gname, KDE_KEYS))
        groups[gname] = grp
    wm = {"activeBackground": r["header_bg"], "activeBlend": r["text"], "activeForeground": r["text"],
          "inactiveBackground": r["header_inactive_bg"], "inactiveBlend": r["text_muted"],
          "inactiveForeground": r["text_muted"]}
    wm.update(overrides("WM", WM_KEYS))
    return {"groups": groups, "wm": wm, "settings": settings}


def _terminal(t: dict, e: str, colour, problems):
    term = {}
    for k in t:
        if k not in TERMINAL_SETTINGS and k not in ("normal", "bright", "faint"):
            problems.append(f"[edition.{e}.terminal] {k}: not a terminal setting")
    for k, default in TERMINAL_SETTINGS.items():
        v = t.get(k, default)
        if k in ("faint_amount", "opacity"):
            if not isinstance(v, (int, float)) or not 0 <= v <= 1:
                problems.append(f"[edition.{e}.terminal] {k} = {v!r}: needs a number from 0 to 1")
                v = default
            term[k] = float(v)
        elif k == "blur":
            term[k] = bool(v)
        elif v is not None:
            term[k] = colour(v, f"[edition.{e}.terminal] {k}", e)
    term.setdefault("background_faint", term["background"])
    normal, bright = t.get("normal", []), t.get("bright", [])
    if len(normal) != 8 or len(bright) != 8:
        problems.append(f"[edition.{e}.terminal] normal and bright: need 8 colours each "
                        f"(have {len(normal)} and {len(bright)})")
    ansi = [(colour(n, f"[edition.{e}.terminal] normal[{i}]", e), colour(b, f"[edition.{e}.terminal] bright[{i}]", e))
            for i, (n, b) in enumerate(zip(normal[:8], bright[:8]))]
    ansi += [("#000000", "#000000")] * (8 - len(ansi))
    faint_in = list(t.get("faint", [])) + ["auto"] * 8
    faint = [None if v in ("", "auto") else colour(v, f"[edition.{e}.terminal] faint[{i}]", e)
             for i, v in enumerate(faint_in[:8])]
    return term, ansi, faint
