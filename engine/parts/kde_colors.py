"""KDE colour schemes: share/color-schemes/<Name>-<Edition>.colors"""
from ..colour import csv
from ..pack import KDE_KEYS, WM_KEYS, Edition, Pack

ORDER = ("Button", "Selection", "Tooltip", "View", "Window", "Header", "Header][Inactive", "Complementary")


def color_scheme(pack: Pack, ed: Edition) -> str:
    s = ed.kde["settings"]
    eff = csv(s["effects_colour"])
    out = [f"""[ColorEffects:Disabled]
Color={eff}
ColorAmount=0
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2
""", f"""[ColorEffects:Inactive]
ChangeSelectionColor={'true' if s['change_selection_colour'] else 'false'}
Color={eff}
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0
"""]
    for name in ORDER:
        g = ed.kde["groups"][name]
        out.append("\n".join([f"[Colors:{name}]"] + [f"{k}={csv(g[k])}" for k in KDE_KEYS if g.get(k)]) + "\n")
    wm = ed.kde["wm"]
    out.append("\n".join(["[WM]"] + [f"{k}={csv(wm[k])}" for k in WM_KEYS if wm.get(k)]) + "\n")
    out.append("\n".join(["[General]", f"ColorScheme={pack.file_name('color_scheme', ed)}",
                          f"Name={pack.display(ed)}", "shadeSortColumn=true"]) + "\n")
    out.append("[KDE]\ncontrast=4\n" + (f"widgetStyle={s['widget_style']}\n" if s["widget_style"] else ""))
    return "\n".join(out) + "\n"


def build(pack: Pack) -> dict[str, str]:
    return {f"color-schemes/{pack.file_name('color_scheme', ed)}.colors": color_scheme(pack, ed)
            for ed in pack.editions.values()}
