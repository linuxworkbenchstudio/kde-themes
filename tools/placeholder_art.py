#!/usr/bin/env python3
"""Placeholder artwork for a pack that has none yet, drawn from the pack's own colours.

    python3 tools/placeholder_art.py packs/<pack> [LETTER]

writes packs/<pack>/art/ (what the engine's brand and icons parts read):
  wallpaper/images{,_dark}/{3840x2160,2560x1440,1920x1080}.jpg, screenshot.png
  hicolor/<size>/apps/<command>-launcher.png (16-512), <command>.png / <command>-light.png (32-512),
  hicolor/scalable/apps/<command>{,-light,-launcher}.svg
  splash/<edition>/{background.jpg, wordmark.png, preview.png}
  previews/<edition>/{preview.png, fullscreenpreview.png}
  fastfetch/<command>-logo.txt
The mark is one letter (V, T or C; default: the first letter of the name's last word) in the
accent colour on a tile; wallpapers and splash backgrounds are plain gradients marked
"placeholder". The real artwork replaces all of it. Needs Pillow.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine.colour import mix, rgb  # noqa: E402
from engine.pack import load  # noqa: E402

WALL_SIZES = ((3840, 2160), (2560, 1440), (1920, 1080))
LAUNCHER_SIZES = (16, 22, 24, 32, 48, 64, 96, 128, 256, 512)
APP_SIZES = (32, 48, 64, 128, 256, 512)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
# strokes in a 64-unit box: lines as point lists, arcs as (cx, cy, r, start, end) in degrees
LETTERS = {
    "V": [[(20, 20), (32, 45), (44, 20)]],
    "T": [[(19, 21), (45, 21)], [(32, 21), (32, 45)]],
    "C": [(33, 32, 12.5, 50, 310)],
}
STROKE = 6


def gradient(size, top, bottom):
    w, h = size
    col = Image.new("RGB", (1, h))
    a, b = rgb(top), rgb(bottom)
    col.putdata([tuple(round(x + (y - x) * i / max(1, h - 1)) for x, y in zip(a, b)) for i in range(h)])
    return col.resize((w, h))


def mark_png(size, letter, top, bottom, ink, edge=None, round_=False):
    s = max(size * 4, 256)
    u = s / 64
    tile = gradient((s, s), top, bottom).convert("RGBA")
    mask = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(mask)
    if round_:
        d.ellipse((3 * u, 3 * u, 61 * u, 61 * u), fill=255)
    else:
        d.rounded_rectangle((4 * u, 4 * u, 60 * u, 60 * u), radius=14 * u, fill=255)
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(tile, (0, 0), mask)
    d = ImageDraw.Draw(out)
    if edge and not round_:
        d.rounded_rectangle((4 * u, 4 * u, 60 * u, 60 * u), radius=14 * u, outline=edge, width=max(1, round(u)))
    r = STROKE * u / 2
    for stroke in LETTERS[letter]:
        if isinstance(stroke, tuple):
            cx, cy, rad, a0, a1 = stroke
            d.arc(((cx - rad) * u - r, (cy - rad) * u - r, (cx + rad) * u + r, (cy + rad) * u + r), a0, a1, fill=ink, width=round(2 * r))
        else:
            pts = [(x * u, y * u) for x, y in stroke]
            d.line(pts, fill=ink, width=round(2 * r), joint="curve")
            for x, y in pts:
                d.ellipse((x - r, y - r, x + r, y + r), fill=ink)
    return out.resize((size, size), Image.LANCZOS)


def mark_svg(name, letter, top, bottom, ink, edge=None, round_=False):
    shape = ('<circle cx="32" cy="32" r="29" fill="url(#bg)"/>' if round_ else
             '<rect x="4" y="4" width="56" height="56" rx="14" fill="url(#bg)"'
             + (f' stroke="{edge}" stroke-width="1"' if edge else "") + "/>")
    paths = []
    for stroke in LETTERS[letter]:
        if isinstance(stroke, tuple):
            import math
            cx, cy, rad, a0, a1 = stroke
            p = lambda a: (cx + rad * math.cos(math.radians(a)), cy + rad * math.sin(math.radians(a)))  # noqa: E731
            (x0, y0), (x1, y1) = p(a0), p(a1)
            paths.append(f"M{x0:.2f} {y0:.2f}A{rad} {rad} 0 {1 if a1 - a0 > 180 else 0} 1 {x1:.2f} {y1:.2f}")
        else:
            paths.append("M" + "L".join(f"{x} {y}" for x, y in stroke))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">\n'
            f"<!-- {name} mark - placeholder, CC-BY-SA-4.0 (The Linux Workbench) -->\n"
            f'<defs><linearGradient id="bg" x1="0" y1="4" x2="0" y2="60" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/></linearGradient></defs>\n'
            f"{shape}\n"
            f'<path d="{" ".join(paths)}" fill="none" stroke="{ink}" stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round"/>\n'
            "</svg>\n")


def label(im, text, colour, size, y):
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, size)
    w = d.textlength(text, font=font)
    d.text(((im.width - w) / 2, y), text, fill=colour, font=font)


def scene(size, name, r, mark):
    """A wallpaper-like picture: gradient, the mark in the middle, the name and "placeholder"."""
    w, h = size
    im = gradient(size, r["header_bg"], r["view_bg"]).convert("RGBA")
    m = mark.resize((h // 4, h // 4), Image.LANCZOS)
    im.alpha_composite(m, ((w - m.width) // 2, h // 2 - m.height))
    label(im, name, r["text"], h // 14, h // 2 + h // 40)
    label(im, "placeholder artwork", r["text_muted"], h // 40, h // 2 + h // 8)
    return im.convert("RGB")


def main(argv):
    pack = load(argv[1])
    letter = (argv[2] if len(argv) > 2 else pack.name.split()[-1][0]).upper()
    if letter not in LETTERS:
        sys.exit(f"No drawing for the letter {letter!r}: give one of {', '.join(LETTERS)}")
    art = pack.root / "art"
    eds = {e.template: e for e in pack.editions.values()}
    dark, light = eds["dark"].roles, eds["light"].roles
    cmd = pack.command

    def save(rel, im, **kw):
        p = art / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        im.save(p, **kw)

    def text(rel, s):
        p = art / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(s, encoding="utf-8")

    looks = {   # file stem -> (top, bottom, letter colour, edge, round)
        f"{cmd}-launcher": (dark["header_bg"], dark["view_bg"], dark["accent"], None, True),
        cmd: (dark["header_bg"], dark["view_bg"], dark["accent"], None, False),
        f"{cmd}-light": (light["view_bg"], light["header_bg"], light["selection_bg"], light["border"], False),
    }
    for stem, (top, bottom, ink, edge, rnd) in looks.items():
        text(f"hicolor/scalable/apps/{stem}.svg", mark_svg(pack.name, letter, top, bottom, ink, edge, rnd))
        for n in (LAUNCHER_SIZES if rnd else APP_SIZES):
            save(f"hicolor/{n}x{n}/apps/{stem}.png", mark_png(n, letter, top, bottom, ink, edge, rnd), optimize=True)

    big = {"dark": mark_png(512, letter, *looks[cmd]), "light": mark_png(512, letter, *looks[f"{cmd}-light"])}
    for sub, r, m in (("images", light, big["light"]), ("images_dark", dark, big["dark"])):
        full = scene(WALL_SIZES[0], pack.name, r, m)
        for w, h in WALL_SIZES:
            save(f"wallpaper/{sub}/{w}x{h}.jpg", full.resize((w, h), Image.LANCZOS), quality=88, optimize=True)
    save("wallpaper/screenshot.png", scene((1600, 900), pack.name, dark, big["dark"]).resize((400, 225), Image.LANCZOS), optimize=True)

    for ed in pack.editions.values():
        r, m = ed.roles, big[ed.template]
        # the splash is dark in both editions (as the other themes')
        save(f"splash/{ed.id}/background.jpg", gradient(WALL_SIZES[0], dark["header_bg"], dark["view_bg"]), quality=88, optimize=True)
        word = Image.new("RGBA", (1600, 420), (0, 0, 0, 0))
        label(word, pack.name, dark["text"], 230, 70)
        save(f"splash/{ed.id}/wordmark.png", word, optimize=True)
        sp = gradient((1280, 720), dark["header_bg"], dark["view_bg"]).convert("RGBA")
        label(sp, pack.name, dark["text"], 110, 280)
        save(f"splash/{ed.id}/preview.png", sp.convert("RGB"), optimize=True)
        pv = scene((1920, 1080), pack.display(ed), r, m)
        save(f"previews/{ed.id}/fullscreenpreview.png", pv, optimize=True)
        save(f"previews/{ed.id}/preview.png", pv.resize((480, 270), Image.LANCZOS), optimize=True)

    # Fastfetch logo: $1 the tile, $2 the letter (16 rows of 30 half-width cells)
    cells = mark_png(64, letter, "#FFFFFF", "#FFFFFF", "#000000").convert("RGBA").resize((30, 16), Image.LANCZOS)
    rows = []
    for y in range(16):
        row, last = "", None
        for x in range(30):
            pr, _, _, pa = cells.getpixel((x, y))
            c = None if pa < 128 else ("$2" if pr < 128 else "$1")
            row += " " if c is None else ((c if c != last else "") + "█")
            last = c if c else last
        rows.append(row.rstrip())
    text(f"fastfetch/{cmd}-logo.txt", "\n".join(rows) + "\n")
    print(f"{pack.name}: placeholder artwork written to {art}")


if __name__ == "__main__":
    main(sys.argv)
