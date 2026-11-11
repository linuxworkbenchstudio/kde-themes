"""COSMIC: cosmic/<Slug>-<Edition>.ron (one theme per edition) and cosmic/wallpapers/.

Each .ron is a COSMIC theme as COSMIC Settings imports and exports it (Appearance > Import):
its ThemeBuilder, checked against COSMIC Epoch 1.11 (libcosmic 430f3d4). COSMIC works out
everything else (borders, muted and disabled text, hover, selection, text on accent) from
these colours, so only these roles carry over:

  bg_color                window_bg            text_tint      text
  primary_container_bg    surface_raised       accent         accent
  secondary_container_bg  button_bg            window_hint    accent (the active window outline)
  neutral_tint            border               success, warning, destructive
                                                              positive, neutral, negative

[edition.<id>.cosmic] can change any of them (a role, a colour name or #RRGGBB) and set:

  roundness = "round"           "round" | "slightly-round" | "square" (COSMIC's three presets)
  gaps = [0, 8]                 window gaps: outer, inner
  active_hint = 3               width of the active window outline
  frosted = ["panel", ...]      blurred see-through parts: "windows", "panel", "applets",
                                "system", "maximized"
  blur = "medium"               how see-through the frosted parts are: "extremely-low" (0.90)
                                ... "extremely-high-2" (0.60)
  mode = "dark"                 "dark" | "light" (default: from window_bg)

Wallpapers: one picture per edition (the largest 16:9 one) from art/wallpaper/images (Light) and
images_dark (Dark). COSMIC 1.11 shows one wallpaper whatever the mode; you pick it in Settings.
"""
from ..colour import is_hex, luminance
from ..pack import Pack

COLOUR_KEYS = {   # builder field -> default role
    "bg_color": "window_bg",
    "primary_container_bg": "surface_raised",
    "secondary_container_bg": "button_bg",
    "neutral_tint": "border",
    "text_tint": "text",
    "accent": "accent",
    "success": "positive",
    "warning": "neutral",
    "destructive": "negative",
    "window_hint": "accent",
}
OPTION_KEYS = {"roundness", "gaps", "active_hint", "frosted", "blur", "mode"}

ROUNDNESS = {   # radius_0, xs, s, m, l, xl
    "round": (0, 4, 8, 16, 32, 160),
    "slightly-round": (0, 2, 8, 8, 8, 8),
    "square": (0, 2, 2, 2, 2, 2),
}
def _kebab(name: str) -> str:
    out = ""
    for ch in name:
        if ch.isupper() and out:
            out += "-"
        elif ch.isdigit():
            out += "-"
        out += ch.lower()
    return out


BLUR = {_kebab(n): n for n in (
    "ExtremelyLow", "ExtremelyLow2", "VeryLow", "VeryLow2", "Low", "Low2", "Medium", "Medium2",
    "High", "High2", "VeryHigh", "VeryHigh2", "ExtremelyHigh", "ExtremelyHigh2")}
FROSTED = {"windows": "frosted_windows", "system": "frosted_system_interface", "panel": "frosted_panel",
           "applets": "frosted_applets", "maximized": "frosted_maximized_apps"}

# COSMIC's own picks for the accent chooser and the neutral ramp (libcosmic model/dark.ron and
# light.ron); the builder colours above override what the theme takes from them.
_STOCK = {
    "dark": dict(
        neutral=["#000000", "#030303", "#161616", "#2E2E2E", "#484848", "#636363", "#808080", "#9E9E9E",
                 "#BEBEBE", "#DEDEDE", "#FFFFFF"],
        accent_blue="#63D0DF", accent_indigo="#A1C0EB", accent_purple="#E79CFE", accent_pink="#FF9CB1",
        accent_red="#FDA1A0", accent_orange="#FFAD00", accent_yellow="#F7E062", accent_green="#92CF9C",
        accent_warm_grey="#CABAB4", ext_warm_grey="#9B8E8A", ext_orange="#FFAD00", ext_yellow="#FEDB40",
        ext_blue="#48B9C7", ext_purple="#CF7DFF", ext_pink="#F93A83", ext_indigo="#3E88FF"),
    "light": dict(
        neutral=["#FFFFFF", "#DEDEDE", "#BEBEBE", "#9E9E9E", "#808080", "#636363", "#484848", "#2E2E2E",
                 "#161616", "#030303", "#000000"],
        accent_blue="#00525A", accent_indigo="#2E496D", accent_purple="#68217C", accent_pink="#86043A",
        accent_red="#78292E", accent_orange="#624000", accent_yellow="#534800", accent_green="#185529",
        accent_warm_grey="#554742", ext_warm_grey="#9B8E8A", ext_orange="#FBB86C", ext_yellow="#F7E062",
        ext_blue="#6ACAD8", ext_purple="#D58CFF", ext_pink="#FF9CDD", ext_indigo="#95C4FC"),
}
SPACING = (("space_none", 0), ("space_xxxs", 4), ("space_xxs", 8), ("space_xs", 12), ("space_s", 16),
           ("space_m", 24), ("space_l", 32), ("space_xl", 48), ("space_xxl", 64), ("space_xxxl", 128))


def _hex(c: str) -> str:
    return f'"{c.upper()}FF"'


def settings(pack: Pack, ed) -> dict:
    """The edition's COSMIC settings, checked and resolved to colours."""
    spec = ed.raw.get("cosmic", {})
    where = f"[edition.{ed.id}.cosmic]"
    problems = []

    def colour(key, value):
        if isinstance(value, str):
            if is_hex(value):
                return value.upper()
            if value in ed.roles:
                return ed.roles[value]
            if value in pack.colours:
                return pack.colours[value]
        problems.append(f"{where} {key} = {value!r}: not a role, a colour name or a #RRGGBB colour")
        return "#000000"

    for k in spec:
        if k not in COLOUR_KEYS and k not in OPTION_KEYS:
            problems.append(f"{where} {k}: not a known setting ({', '.join([*COLOUR_KEYS, *sorted(OPTION_KEYS)])})")
    out = {k: colour(k, spec.get(k, role)) for k, role in COLOUR_KEYS.items()}

    out["roundness"] = spec.get("roundness", "round")
    if out["roundness"] not in ROUNDNESS:
        problems.append(f"{where} roundness = {out['roundness']!r}: one of {', '.join(ROUNDNESS)}")
    gaps = spec.get("gaps", [0, 8])
    if not (isinstance(gaps, list) and len(gaps) == 2 and all(isinstance(g, int) and 0 <= g <= 64 for g in gaps)):
        problems.append(f"{where} gaps = {gaps!r}: two whole numbers 0-64 (outer, inner)")
    out["gaps"] = gaps
    hint = spec.get("active_hint", 3)
    if not (isinstance(hint, int) and 0 <= hint <= 16):
        problems.append(f"{where} active_hint = {hint!r}: a whole number 0-16")
    out["active_hint"] = hint
    frosted = spec.get("frosted", [])
    for f in frosted:
        if f not in FROSTED:
            problems.append(f"{where} frosted: {f!r} is not one of {', '.join(FROSTED)}")
    out["frosted"] = frosted
    out["blur"] = spec.get("blur", "medium")
    if out["blur"] not in BLUR:
        problems.append(f"{where} blur = {out['blur']!r}: one of {', '.join(BLUR)}")
    mode = spec.get("mode", "dark" if luminance(ed.roles["window_bg"]) < 0.5 else "light")
    if mode not in ("dark", "light"):
        problems.append(f"{where} mode = {mode!r}: dark or light")
    out["mode"] = mode
    if problems:
        raise ValueError(f"{pack.root / 'pack.toml'}:\n  " + "\n  ".join(problems))
    return out


def theme_ron(pack: Pack, ed) -> str:
    s = settings(pack, ed)
    stock = _STOCK[s["mode"]]
    palette = [("name", f'"{pack.display(ed)}"'),
               ("bright_red", _hex(s["destructive"])), ("bright_green", _hex(s["success"])),
               ("bright_orange", _hex(s["warning"])),
               ("gray_1", _hex(s["bg_color"])), ("gray_2", _hex(s["primary_container_bg"]))]
    palette += [(f"neutral_{i}", _hex(c)) for i, c in enumerate(stock["neutral"])]
    palette += [(k, _hex(v)) for k, v in stock.items() if k != "neutral"]
    radii = dict(zip(("radius_0", "radius_xs", "radius_s", "radius_m", "radius_l", "radius_xl"),
                     ROUNDNESS[s["roundness"]]))

    lines = [f"// {pack.display(ed)} for COSMIC - {pack.brand}, version {pack.version}",
             "// Import in COSMIC Settings > Desktop > Appearance > Import.",
             "(",
             f"    palette: {s['mode'].capitalize()}((",
             *[f"        {k}: {v}," for k, v in palette],
             "    )),",
             "    spacing: (",
             *[f"        {k}: {v}," for k, v in SPACING],
             "    ),",
             "    corner_radii: (",
             *[f"        {k}: ({', '.join([f'{float(r):.1f}'] * 4)})," for k, r in radii.items()],
             "    ),"]
    for k in ("neutral_tint", "bg_color", "primary_container_bg", "secondary_container_bg", "text_tint",
              "accent", "success", "warning", "destructive"):
        lines.append(f"    {k}: Some({_hex(s[k])}),")
    lines += [f"    frosted: {BLUR[s['blur']]},",
              f"    gaps: ({s['gaps'][0]}, {s['gaps'][1]}),",
              f"    active_hint: {s['active_hint']},",
              f"    window_hint: Some({_hex(s['window_hint'])}),"]
    lines += [f"    {field}: {'true' if key in s['frosted'] else 'false'}," for key, field in FROSTED.items()]
    lines.append(")")
    return "\n".join(lines) + "\n"


def _wallpaper(folder):
    """The largest 16:9 picture in a wallpaper folder (or the largest, if none is 16:9)."""
    pics = []
    for p in folder.glob("*.*") if folder.is_dir() else []:
        try:
            w, h = (int(x) for x in p.stem.split("x"))
        except ValueError:
            continue
        pics.append((w * 9 == h * 16, w * h, p))
    return max(pics)[2] if pics else None


README = """# {Name} for COSMIC

{Name} Dark and {Name} Light as COSMIC themes, with the wallpapers. Made for COSMIC Epoch 1.11.

## Theme

1. Open COSMIC Settings > Desktop > Appearance.
2. Choose Dark or Light at the top, then Import, and pick `{dark}` or `{light}` from this folder.
   Do this once for each mode.

COSMIC works out the rest of the theme (borders, hover, selection) from these colours, and
passes them on to GTK 4 and Qt (qt5ct/qt6ct) apps.

## Wallpaper

Open COSMIC Settings > Desktop > Wallpaper, choose "Add image" and pick the wallpaper from
`wallpapers/` for the mode you use. COSMIC 1.11 shows one wallpaper in both modes.

## Not in COSMIC

The KDE parts of {Name} (Plasma Style, window borders, Kvantum, panel looks, splash screen,
Konsole profiles and the login screen) have no COSMIC equivalent.

Licence: {licence}. {Brand}.
"""


def build(pack: Pack) -> dict:
    out = {}
    slug = pack.name.replace(" ", "-")
    names = {}
    for ed in pack.editions.values():
        name = pack.file_name("cosmic", ed) + ".ron"
        names[ed.id] = name
        out[f"cosmic/{name}"] = theme_ron(pack, ed)
        folder = "images_dark" if settings(pack, ed)["mode"] == "dark" else "images"
        pic = _wallpaper(pack.root / "art" / "wallpaper" / folder)
        if pic:
            out[f"cosmic/wallpapers/{slug}-{ed.name}{pic.suffix.lower()}"] = pic.read_bytes()
    out["cosmic/README.md"] = README.format(Name=pack.name, Brand=pack.brand, licence=pack.license,
                                            dark=names.get("dark", ""), light=names.get("light", ""))
    return out
