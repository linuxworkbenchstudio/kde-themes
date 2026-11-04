"""KDE colour schemes: share/color-schemes/<Name>-<Edition>.colors"""
from ..colour import csv
from ..pack import Edition, Pack

# Breeze's own colour effects; every theme so far keeps them.
EFFECTS = """[ColorEffects:Disabled]
Color=112,111,110
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=false
Color=112,111,110
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0
"""


def _group(name: str, bg: str, bg_alt: str, k: dict, *, text: str, muted: str, active: str,
           link: str, visited: str, inactive: str | None = None, decorations: bool = True,
           hover: str | None = None) -> str:
    lines = [f"[{name}]", f"BackgroundNormal={csv(bg)}", f"BackgroundAlternate={csv(bg_alt)}"]
    if decorations:
        lines += [f"DecorationFocus={csv(k['accent'])}", f"DecorationHover={csv(hover or k['muted'])}"]
    lines += [f"ForegroundNormal={csv(text)}", f"ForegroundInactive={csv(inactive or muted)}",
              f"ForegroundActive={csv(active)}", f"ForegroundLink={csv(link)}",
              f"ForegroundVisited={csv(visited)}", f"ForegroundNegative={csv(k['negative'])}",
              f"ForegroundNeutral={csv(k['neutral'])}", f"ForegroundPositive={csv(k['positive'])}"]
    return "\n".join(lines) + "\n"


def color_scheme(pack: Pack, ed: Edition) -> str:
    k = ed.kde
    c = pack.editions[k["complementary"]].kde if k["complementary"] in pack.editions else k
    std = dict(text=k["text"], muted=k["muted"], active=k["accent"], link=k["link"], visited=k["visited"])
    out = [EFFECTS,
           _group("Colors:Button", k["button"], k["button_alt"], k, **std),
           _group("Colors:Selection", k["accent"], k["accent_bright"], k, text=k["on_accent"],
                  muted=k["selection_bright_text"], active=k["selection_bright_text"],
                  link=k["on_accent"], visited=k["on_accent"]),
           _group("Colors:Tooltip", k["tooltip"], k["tooltip_alt"], k, decorations=False, **std),
           _group("Colors:View", k["view"], k["view_alt"], k, **std),
           _group("Colors:Window", k["window"], k["window_alt"], k, **std),
           _group("Colors:Header", k["header"], k["header_alt"], k, **std),
           _group("Colors:Header][Inactive", k["header"], k["header_alt"], k, **std),
           _group("Colors:Complementary", c["window"], c["window_alt"], c, text=c["text"], muted=c["muted"],
                  active=c["accent"], link=c["link"], visited=c["visited"], hover=c["muted"]),
           "\n".join(["[WM]",
                      f"activeBackground={csv(k['titlebar'])}", f"activeBlend={csv(k['titlebar'])}",
                      f"activeForeground={csv(k['text'])}",
                      f"inactiveBackground={csv(k['titlebar_inactive'])}",
                      f"inactiveBlend={csv(k['titlebar_inactive'])}",
                      f"inactiveForeground={csv(k['muted'])}"]) + "\n",
           "\n".join(["[General]", f"ColorScheme={pack.file_name('color_scheme', ed)}",
                      f"Name={pack.display(ed)}", "shadeSortColumn=true"]) + "\n",
           "[KDE]\ncontrast=4\nwidgetStyle=Breeze\n"]
    return "\n".join(out) + "\n"


def build(pack: Pack) -> dict[str, str]:
    return {f"color-schemes/{pack.file_name('color_scheme', ed)}.colors": color_scheme(pack, ed)
            for ed in pack.editions.values()}
