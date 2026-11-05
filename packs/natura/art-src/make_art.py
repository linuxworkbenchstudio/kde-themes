#!/usr/bin/env python3
"""Natura's artwork, from the two supplied wallpapers (art-src/supplied-{dark,light}.png).

    python3 packs/natura/art-src/make_art.py

writes packs/natura/art/ (what the engine's brand and icons parts read):
  wallpaper/images{,_dark}/{3840x2160,2560x1440,1920x1080}.jpg, screenshot.png
  hicolor/<size>/apps/natura-launcher.png (16-512), natura.png / natura-light.png (32-512),
  hicolor/scalable/apps/natura{,-light,-launcher}.svg
  splash/<edition>/{background.jpg, wordmark.png, preview.png}
  previews/<edition>/{preview.png, fullscreenpreview.png}
  fastfetch/natura-logo.txt
The mark is the wallpaper's own picture: the vermillion sun setting behind two sage hills, over
still water. Needs Pillow, OpenCV (wallpaper cleaning) and Playwright's Chromium (SVG rendering).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

HERE = Path(__file__).resolve().parent
ART = HERE.parent / "art"
INK, INK_VIEW, INK_HEADER, RICE, RICE_VIEW, SAND = "#1C1C1C", "#161616", "#242424", "#F4F3EF", "#FBFAF7", "#EAE2D2"
VERMILLION, KILN, SAGE_MIST, SAGE, SAGE_DEEP = "#E05A47", "#B8432F", "#C9D6C3", "#9DBF94", "#4E6347"
WALL_SIZES = ((3840, 2160), (2560, 1440), (1920, 1080))
LAUNCHER_SIZES = (16, 22, 24, 32, 48, 64, 96, 128, 256, 512)
APP_SIZES = (32, 48, 64, 128, 256, 512)


def mark(size=64, tile="dark"):
    """The Natura mark in a 64-unit box. tile: "dark" (ink tile), "light" (rice tile), None (round)."""
    if tile == "light":
        bg = f'<rect x="4" y="4" width="56" height="56" rx="14" fill="url(#bg)" stroke="#D3C9B6" stroke-width="1"/>'
        stops = (RICE_VIEW, SAND)
        hill_back, hill_front, water = "#B7CCAE", "#7E9F74", "#FFFFFF"
    else:
        stops = (INK_HEADER, INK_VIEW)
        bg = (f'<rect x="4" y="4" width="56" height="56" rx="14" fill="url(#bg)"/>' if tile else
              '<circle cx="32" cy="32" r="29" fill="url(#bg)"/>')
        hill_back, hill_front, water = "#6E8F66", SAGE_DEEP, RICE
    clip = '<rect x="4" y="4" width="56" height="56" rx="14"/>' if tile else '<circle cx="32" cy="32" r="29"/>'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 64 64">
<!-- Natura mark - original artwork, CC-BY-SA-4.0 (The Linux Workbench) -->
<defs>
<linearGradient id="bg" x1="0" y1="4" x2="0" y2="60" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{stops[0]}"/><stop offset="1" stop-color="{stops[1]}"/></linearGradient>
<linearGradient id="sun" x1="0" y1="13" x2="0" y2="41" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{VERMILLION}"/><stop offset="1" stop-color="#F2A58C"/></linearGradient>
<clipPath id="c">{clip}</clipPath>
</defs>
{bg}
<g clip-path="url(#c)">
<circle cx="38" cy="27" r="13" fill="url(#sun)"/>
<path d="M2 41C11 31 18 29 26 33S41 34 48 30 60 30 66 34V66H2z" fill="{hill_back}"/>
<path d="M2 45C12 38 20 37 30 41S48 41 66 37V66H2z" fill="{hill_front}"/>
<rect x="2" y="47" width="64" height="20" fill="{stops[1]}"/>
<path d="M14 51.5h36M21 55.5h22" stroke="{water}" stroke-opacity=".55" stroke-width="1.6" stroke-linecap="round"/>
<path d="M33 51.5h10" stroke="{VERMILLION}" stroke-opacity=".9" stroke-width="1.6" stroke-linecap="round"/>
</g>
</svg>
"""


def wordmark(colour):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="420" viewBox="0 0 1600 420">
{mark(320, None).replace('<svg ', '<svg x="40" y="50" ', 1).split('\n', 1)[0]}{mark(320, None).split('\n', 1)[1]}
<text x="420" y="262" font-family="Inter" font-weight="300" font-size="176" letter-spacing="34" fill="{colour}">NATURA</text>
</svg>"""


def render(svgs: dict):
    """{out_path: (svg text, width, height)} rendered with Chromium (transparent background)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for out, (svg, w, h) in svgs.items():
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.set_content(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
            el = pg.query_selector("svg")
            el.evaluate(f'e => {{ e.setAttribute("width", {w}); e.setAttribute("height", {h}); }}')
            out.parent.mkdir(parents=True, exist_ok=True)
            el.screenshot(path=str(out), omit_background=True)
            pg.close()
        b.close()


def braille(svg: str, cols=40, rows=13) -> str:
    """The mark as Braille text for Fastfetch: $1 sun, $2 hills (2 x 4 dots per character)."""
    tmp = HERE / ".mark.png"
    render({tmp: (svg, cols * 2 * 4, rows * 4 * 4)})
    a = np.asarray(Image.open(tmp).convert("RGBA").resize((cols * 2, rows * 4), Image.LANCZOS)).astype(int)
    tmp.unlink()
    sun = np.array([0xE0, 0x5A, 0x47])
    lines = []
    bits = ((0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80))
    for r in range(rows):
        line, cur = "", None
        for c in range(cols):
            code, kinds = 0, []
            for dx, dy, bit in bits:
                px = a[r * 4 + dy, c * 2 + dx]
                if px[3] > 110:
                    code |= bit
                    kinds.append("$1" if px[0] > px[1] + 50 else "$2")
            if code:
                k = max(set(kinds), key=kinds.count)
                if k != cur:
                    line += k
                    cur = k
                line += chr(0x2800 + code)
            else:
                line += " "
        lines.append(line.rstrip())
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines) + "\n"


def main():
    clean = HERE / "clean_wallpapers.py"
    walls = {}
    for e in ("light", "dark"):
        out = HERE / f".clean-{e}.png"
        subprocess.run([sys.executable, str(clean), str(HERE / f"supplied-{e}.png"), str(out), e], check=True)
        walls[e] = Image.open(out).convert("RGB")
        out.unlink()
    for e, folder in (("light", "images"), ("dark", "images_dark")):
        d = ART / "wallpaper" / folder
        d.mkdir(parents=True, exist_ok=True)
        for w, h in WALL_SIZES:
            walls[e].resize((w, h), Image.LANCZOS).save(d / f"{w}x{h}.jpg", quality=92, optimize=True)
    walls["dark"].resize((400, 225), Image.LANCZOS).save(ART / "wallpaper" / "screenshot.png", optimize=True)

    hic = ART / "hicolor"
    sc = hic / "scalable/apps"
    sc.mkdir(parents=True, exist_ok=True)
    svgs = {"natura": mark(64, "dark"), "natura-light": mark(64, "light"), "natura-launcher": mark(64, None)}
    for n, s in svgs.items():
        (sc / f"{n}.svg").write_text(s)
    jobs = {}
    for n in LAUNCHER_SIZES:
        jobs[hic / f"{n}x{n}/apps/natura-launcher.png"] = (svgs["natura-launcher"], n, n)
    for n in APP_SIZES:
        jobs[hic / f"{n}x{n}/apps/natura.png"] = (svgs["natura"], n, n)
        jobs[hic / f"{n}x{n}/apps/natura-light.png"] = (svgs["natura-light"], n, n)
    tmpd = HERE / ".tmp"
    jobs[tmpd / "wordmark-dark.png"] = (wordmark(RICE), 1600, 420)
    jobs[tmpd / "wordmark-light.png"] = (wordmark(INK), 1600, 420)
    render(jobs)

    for e in ("dark", "light"):
        d = ART / "splash" / e
        d.mkdir(parents=True, exist_ok=True)
        # the splash is dark in both editions (it shows before the desktop): the Dark picture,
        # softened and dimmed behind the mark
        bg = walls["dark"].filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.62)
        bg.save(d / "background.jpg", quality=90, optimize=True)
        wm = Image.open(tmpd / "wordmark-dark.png").convert("RGBA")
        wm.save(d / "wordmark.png", optimize=True)
        pv = bg.resize((1280, 720), Image.LANCZOS).convert("RGBA")
        w = wm.resize((480, 126), Image.LANCZOS)
        pv.alpha_composite(w, ((1280 - 480) // 2, (720 - 126) // 2 - 20))
        pv.convert("RGB").save(d / "preview.png", optimize=True)

        p = ART / "previews" / e
        p.mkdir(parents=True, exist_ok=True)
        full = walls[e].resize((1920, 1080), Image.LANCZOS).convert("RGBA")
        bar = Image.new("RGBA", (1920, 36), (0x24, 0x24, 0x24, 235) if e == "dark" else (0xF4, 0xF3, 0xEF, 209))
        full.alpha_composite(bar, (0, 0))
        icon = Image.open(hic / "24x24/apps/natura-launcher.png").convert("RGBA")
        full.alpha_composite(icon, (8, 6))
        full.convert("RGB").save(p / "fullscreenpreview.png", optimize=True)
        full.convert("RGB").resize((480, 270), Image.LANCZOS).save(p / "preview.png", optimize=True)
    for f in tmpd.glob("*"):
        f.unlink()
    tmpd.rmdir()

    ff = ART / "fastfetch"
    ff.mkdir(parents=True, exist_ok=True)
    # the mark without its disc: sun, two hills ending at the waterline, and the water lines
    logo = f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="40" viewBox="4 12 56 36">
<circle cx="38" cy="27" r="13" fill="{VERMILLION}"/>
<path d="M6 41C13 33 19 31 26 34S41 35 48 31 56 31 58 33V44H6z" fill="{SAGE}"/>
<path d="M6 44C14 39 21 38 30 41S48 41 58 38V44z" fill="{SAGE_DEEP}"/>
<path d="M14 47h30" stroke="{SAGE}" stroke-width="1.8" stroke-linecap="round"/>
</svg>"""
    (ff / "natura-logo.txt").write_text(braille(logo))
    print("Natura artwork in", ART)


if __name__ == "__main__":
    main()
