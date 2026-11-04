"""Konsole: share/konsole/<Name>-<Edition>.colorscheme and .profile"""
from ..colour import csv, mix
from ..pack import Edition, Pack


def _entry(name: str, colour: str) -> str:
    return f"[{name}]\nColor={csv(colour)}\n"


def colorscheme(pack: Pack, ed: Edition) -> str:
    t = ed.terminal
    parts = [_entry("Background", t["background"]), _entry("BackgroundFaint", t["background_faint"]),
             _entry("BackgroundIntense", t["background_intense"])]
    for i, (normal, intense) in enumerate(ed.ansi):
        faint = ed.ansi_faint[i] or mix(normal, t["background"], t["faint_amount"])
        parts += [_entry(f"Color{i}", normal), _entry(f"Color{i}Faint", faint), _entry(f"Color{i}Intense", intense)]
    parts += [_entry("Foreground", t["foreground"]), _entry("ForegroundFaint", t["foreground_faint"]),
              _entry("ForegroundIntense", t["foreground_intense"])]
    opacity = ("%g" % t["opacity"])
    parts.append("\n".join(["[General]", "Anchor=0.5,0.5", f"Blur={'true' if t['blur'] else 'false'}",
                            "ColorRandomization=false", f"Description={pack.display(ed)}", "FillStyle=Tile",
                            f"Opacity={opacity}", "Wallpaper=", "WallpaperFlipType=NoFlip",
                            "WallpaperOpacity=1"]) + "\n")
    return "\n".join(parts)


def profile(pack: Pack, ed: Edition) -> str:
    return (f"[Appearance]\nColorScheme={pack.file_name('konsole', ed)}\n\n"
            f"[General]\nName={pack.display(ed)}\nParent=FALLBACK/\n\n"
            "[Scrolling]\nHistoryMode=2\n")


def build(pack: Pack) -> dict[str, str]:
    out = {}
    for ed in pack.editions.values():
        stem = pack.file_name("konsole", ed)
        out[f"konsole/{stem}.colorscheme"] = colorscheme(pack, ed)
        out[f"konsole/{stem}.profile"] = profile(pack, ed)
    return out
