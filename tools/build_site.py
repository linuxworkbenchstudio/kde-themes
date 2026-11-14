#!/usr/bin/env python3
"""Build the website into site/: a home page with every theme, and one page per theme.

    python3 tools/build_site.py            writes site/ (published by .github/workflows/pages.yml)

Everything comes from the packs: names, taglines, versions, palettes (Dark and Light), the
launcher logo and the wallpapers. A pack whose wallpaper is still placeholder artwork
([theme.site] placeholder_wallpaper = true) gets a hero drawn from its palette instead.
Each theme page follows the reader's light/dark setting, with a switch; it shows the theme's
own Dark or Light colours.
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.colour import contrast  # noqa: E402
from engine.pack import load  # noqa: E402

REPO = "linuxworkbenchstudio/lwbs-themes"
GITHUB = f"https://github.com/{REPO}"
KOFI = "https://ko-fi.com/linuxworkbench"
ORDER = ["waypoint", "vice-horizon", "natura", "vacation", "vintage-trail", "core"]
SWATCHES = [("window_bg", "Background"), ("surface_raised", "Surface"), ("button_bg", "Raised"),
            ("text", "Text"), ("text_muted", "Muted"), ("accent", "Accent"),
            ("positive", "Success"), ("neutral", "Warning"), ("negative", "Error")]
FEATURES = [
    ("Global Theme", "Dark and Light, with its own splash screen and wallpapers."),
    ("Plasma Style and colours", "Panels, popups and widgets, colour schemes and window borders."),
    ("Apps", "A Kvantum style for Qt apps and a GTK theme for Firefox, GIMP and Inkscape, switched with the rest."),
    ("Icons and cursors", "About 145 folder types, 600 app tiles and 260 file types; Breeze cursors recoloured."),
    ("Top panel", "Launcher, tasks, a centred clock and system stats, in six looks from Normal to Fancy."),
    ("Terminal", "Konsole colour schemes and profiles, and Fastfetch in the theme's colours."),
    ("One command", "Switch everything between Dark and Light, with a Settings app for the rest."),
    ("COSMIC too", "Dark and Light themes and wallpapers for the COSMIC desktop."),
]

E = html.escape


def rgb_triplet(hexcol: str) -> str:
    return ", ".join(str(int(hexcol[i:i + 2], 16)) for i in (1, 3, 5))


def editions(pack):
    eds = list(pack.editions.values())
    dark = next(e for e in eds if e.template == "dark")
    light = next((e for e in eds if e.template == "light"), dark)
    return dark, light


def css_vars(ed) -> str:
    r = ed.roles
    on_accent = max((r["base_bg"], r["text"], "#FFFFFF", "#000000"), key=lambda c: contrast(c, r["accent"]))
    return (f"--bg: {r['window_bg']}; --deep: {r['base_bg']}; --surface: {r['surface_raised']}; "
            f"--raised: {r['button_bg']}; --line: {r['border']}; --text: {r['text']}; "
            f"--muted: {r['text_muted']}; --accent: {r['accent']}; --on-accent: {on_accent}; "
            f"--accent-rgb: {rgb_triplet(r['accent'])};")


BASE_CSS = """
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.6 "Inter", system-ui, -apple-system, "Segoe UI", sans-serif; }
a { color: var(--accent); }
img { max-width: 100%; display: block; }
.wrap { max-width: 1120px; margin: 0 auto; padding: 0 16px; }
header.top { position: sticky; top: 0; z-index: 5; backdrop-filter: blur(12px);
  background: color-mix(in srgb, var(--bg) 82%, transparent); border-bottom: 1px solid var(--line); }
header.top .wrap { display: flex; align-items: center; gap: 16px; height: 56px; }
.brand { color: var(--text); text-decoration: none; font-weight: 650; letter-spacing: .02em; white-space: nowrap; }
@media (max-width: 520px) { .brand small { display: none; } header.top .wrap { gap: 10px; } }
.brand small { color: var(--muted); font-weight: 500; margin-left: 6px; }
.spacer { flex: 1; }
.navlink { color: var(--muted); text-decoration: none; font-size: 14px; }
.navlink:hover { color: var(--text); }
.switch { display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 2px; }
.switch button { font: inherit; font-size: 13px; border: 0; background: none; color: var(--muted);
  padding: 4px 12px; border-radius: 999px; cursor: pointer; }
.switch button[aria-pressed="true"] { background: var(--accent); color: var(--on-accent); }
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 10px;
  font-weight: 600; text-decoration: none; border: 1px solid transparent; }
.btn.primary { background: var(--accent); color: var(--on-accent); }
.btn.ghost { border-color: color-mix(in srgb, currentColor 35%, transparent); color: inherit; }
h1, h2, h3 { line-height: 1.2; margin: 0; }
h2 { font-size: 24px; margin-bottom: 20px; }
section { padding: 56px 0; border-top: 1px solid var(--line); }
footer { padding: 32px 0 48px; color: var(--muted); font-size: 14px; border-top: 1px solid var(--line); }
code, pre { font-family: "JetBrains Mono", ui-monospace, "DejaVu Sans Mono", monospace; font-size: 14px; }
pre { background: var(--deep); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px;
  overflow-x: auto; margin: 0; }
"""

THEME_CSS = """
.hero { position: relative; min-height: min(78vh, 640px); display: flex; align-items: flex-end;
  color: #fff; background: var(--deep) center / cover no-repeat; overflow: hidden; }
.hero::after { content: ""; position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0) 35%, rgba(0,0,0,.62) 100%); }
.hero.drawn { background: radial-gradient(1200px 520px at 70% 10%, rgba(var(--accent-rgb), .35), transparent 60%),
  linear-gradient(160deg, var(--surface), var(--deep)); color: var(--text); }
.hero.drawn::after { display: none; }
.hero .wrap { position: relative; z-index: 1; width: 100%; padding-bottom: 48px; }
.hero .logo { width: 88px; height: 88px; filter: drop-shadow(0 8px 24px rgba(0,0,0,.35)); }
.hero h1 { font-size: clamp(36px, 7vw, 64px); margin: 18px 0 8px; letter-spacing: -.01em; }
.hero p { font-size: 18px; max-width: 560px; margin: 0 0 24px; opacity: .92; }
.hero .actions { display: flex; flex-wrap: wrap; gap: 12px; }
.hero .version { font-size: 13px; opacity: .8; margin-top: 16px; }
.hero:not(.drawn) .btn.ghost { color: #fff; }
.swatches { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 10px; }
@media (max-width: 520px) { .sw i { height: 44px; } }
.sw { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; background: var(--surface); }
.sw i { display: block; height: 64px; }
.sw div { padding: 8px 10px; font-size: 13px; }
.sw b { display: block; font-weight: 600; }
.sw span { color: var(--muted); font-family: ui-monospace, monospace; font-size: 12px; }
.features { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 16px; }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 18px; }
.card h3 { font-size: 16px; margin-bottom: 6px; }
.card p { margin: 0; color: var(--muted); font-size: 15px; }
.steps { display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
.steps ol { margin: 0 0 12px; padding-left: 20px; color: var(--muted); }
.steps h3 { font-size: 16px; margin-bottom: 10px; }
.note { color: var(--muted); font-size: 14px; }
"""

HOME_CSS = """
.intro { padding: 72px 0 40px; }
.intro h1 { font-size: clamp(32px, 6vw, 52px); letter-spacing: -.01em; }
.intro p { color: var(--muted); font-size: 18px; max-width: 620px; margin: 14px 0 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; padding-bottom: 64px; }
.tile { display: block; text-decoration: none; color: var(--text); border-radius: 16px; overflow: hidden;
  border: 1px solid var(--line); background: var(--surface); transition: transform .15s ease, border-color .15s ease; }
.tile:hover { transform: translateY(-2px); border-color: var(--accent); }
.tile .pic { aspect-ratio: 16 / 9; background: center / cover no-repeat; position: relative; }
.tile .pic img { position: absolute; left: 16px; bottom: 16px; width: 56px; height: 56px;
  filter: drop-shadow(0 6px 16px rgba(0,0,0,.35)); }
.tile .txt { padding: 14px 16px 18px; }
.tile h2 { font-size: 20px; margin: 0 0 4px; }
.badge { font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 99px; margin-left: 6px; vertical-align: middle;
  background: color-mix(in srgb, var(--accent) 22%, transparent); color: var(--text); }
.roadmap { color: var(--muted); }
.btn.soon { border-color: color-mix(in srgb, currentColor 45%, transparent); opacity: .85; cursor: default; }
.tile p { margin: 0; color: var(--muted); font-size: 15px; }
.dots { display: flex; gap: 6px; margin-top: 12px; }
.dots i { width: 14px; height: 14px; border-radius: 50%; border: 1px solid rgba(127,127,127,.35); }
"""

SWITCH_JS = """
<script>
(function () {
  var root = document.documentElement, key = "lwbs-mode", saved = null;
  try { saved = localStorage.getItem(key); } catch (e) {}
  function set(mode, keep) {
    var m = mode || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    root.setAttribute("data-mode", m);
    document.querySelectorAll("[data-show]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.show === m)); });
    if (keep) { try { localStorage.setItem(key, m); } catch (e) {} }
  }
  set(saved);
  document.querySelectorAll("[data-show]").forEach(function (b) { b.addEventListener("click", function () { set(b.dataset.show, true); }); });
  matchMedia("(prefers-color-scheme: light)").addEventListener("change", function () { if (!saved) set(null); });
})();
</script>"""


def page(title, description, css, body, head_extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700&display=swap" rel="stylesheet">
{head_extra}<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def wallpaper(pack, dest: Path, which: str) -> str | None:
    """Copy one wallpaper (1600 px wide) next to the page; None for placeholder artwork."""
    if pack.raw.get("theme", {}).get("site", {}).get("placeholder_wallpaper"):
        return None
    src = pack.root / "art" / "wallpaper" / ("images_dark" if which == "dark" else "images") / "1920x1080.jpg"
    if not src.is_file():
        return None
    name = f"wallpaper-{which}.jpg"
    Image.open(src).convert("RGB").resize((1600, 900), Image.LANCZOS).save(dest / name, quality=82, optimize=True, progressive=True)
    return name


def theme_page(pack, out: Path):
    dest = out / pack.id
    dest.mkdir(parents=True)
    dark, light = editions(pack)
    shutil.copyfile(pack.root / f"art/hicolor/scalable/apps/{pack.command}-launcher.svg", dest / "logo.svg") \
        if (pack.root / f"art/hicolor/scalable/apps/{pack.command}-launcher.svg").is_file() else \
        shutil.copyfile(pack.root / f"art/hicolor/256x256/apps/{pack.command}-launcher.png", dest / "logo.png")
    logo = "logo.svg" if (dest / "logo.svg").is_file() else "logo.png"
    walls = {m: wallpaper(pack, dest, m) for m in ("dark", "light")}
    tagline = pack.raw.get("theme", {}).get("programs", {}).get("tagline",
                                                                 f"A {pack.name} theme for KDE Plasma 6, in Dark and Light.")
    css = (BASE_CSS + THEME_CSS
           + f":root, :root[data-mode='dark'] {{ {css_vars(dark)} }}\n"
           + f"@media (prefers-color-scheme: light) {{ :root:not([data-mode='dark']) {{ {css_vars(light)} }} }}\n"
           + f":root[data-mode='light'] {{ {css_vars(light)} }}\n"
           + "".join(f":root{sel} .hero {{ background-image: url('{walls[m]}'); }}\n"
                     for m, sel in (("dark", ""), ("light", "[data-mode='light']")) if walls[m])
           + (f"@media (prefers-color-scheme: light) {{ :root:not([data-mode='dark']) .hero {{ background-image: url('{walls['light']}'); }} }}\n"
              if walls["light"] else ""))
    hero_cls = "hero" if walls["dark"] else "hero drawn"
    soon = pack.raw.get("theme", {}).get("site", {}).get("status") == "coming-soon"
    folder = f"{pack.name.replace(' ', '-')}-{pack.version}"
    slug = pack.name.replace(" ", "-")
    INSTALL_BLOCK = f"""<section><div class="wrap">
  <h2>Install</h2>
  <div class="steps">
    <div><h3>KDE Plasma 6</h3>
      <ol><li>Download <code>{E(folder)}.zip</code> and unzip it.</li><li>Run the installer: a guided setup in the terminal. Nothing changes until you press Install.</li></ol>
      <pre>cd {E(folder)}
./install.sh</pre>
      <p class="note">Afterwards, <code>{E(pack.command)} dark</code> or <code>{E(pack.command)} light</code> switches everything.</p></div>
    <div><h3>COSMIC</h3>
      <ol><li>Download <code>{E(slug)}-COSMIC-{E(pack.version)}.zip</code> (a separate download) and unzip it.</li><li>Run <code>./install.sh</code>: it puts the two theme files and the wallpapers in place. Nothing in COSMIC changes by itself.</li><li>Open COSMIC Settings › Desktop › Appearance, choose Dark or Light, then Import, and pick the matching <code>.ron</code> file.</li><li>Pick the wallpaper in Settings › Desktop › Wallpaper › Add image.</li></ol></div>
  </div>
</div></section>
"""
    SOON_BLOCK = f"""<section><div class="wrap">
  <h2>Coming soon</h2>
  <p>{E(pack.name)} is not released yet. It is still being tested on real desktops. The first release will be on <a href="{GITHUB}/releases">GitHub Releases</a>; follow the repository or <a href="{KOFI}">Ko-fi</a> to hear when it lands.</p>
</div></section>
"""

    def swatches(ed):
        return "".join(f'<div class="sw"><i style="background:{ed.roles[k]}"></i><div><b>{E(label)}</b>'
                       f'<span>{ed.roles[k]}</span></div></div>' for k, label in SWATCHES)

    body = f"""<header class="top"><div class="wrap">
  <a class="brand" href="../">The Linux Workbench <small>themes</small></a>
  <span class="spacer"></span>
  <div class="switch" role="group" aria-label="Edition"><button data-show="dark" aria-pressed="true">Dark</button><button data-show="light" aria-pressed="false">Light</button></div>
  <a class="navlink" href="{GITHUB}">GitHub</a>
</div></header>
<main>
<div class="{hero_cls}"><div class="wrap">
  <img class="logo" src="{logo}" alt="{E(pack.name)} logo" width="88" height="88">
  <h1>{E(pack.name)}</h1>
  <p>{E(tagline)}</p>
  <div class="actions">
    {'<span class="btn soon">Coming soon</span>' if soon else f'<a class="btn primary" href="{GITHUB}/releases?q={E(pack.name)}">Download</a>'}
    <a class="btn ghost" href="{GITHUB}/tree/main/packs/{pack.id}">Source</a>
  </div>
  <div class="version">{'Coming soon' if soon else 'Version ' + E(pack.version)} · KDE Plasma 6 and COSMIC · {E(pack.license)}</div>
</div></div>

<section><div class="wrap">
  <h2>Palette</h2>
  <div class="swatches" data-for="dark">{swatches(dark)}</div>
</div></section>

<section><div class="wrap">
  <h2>What you get</h2>
  <div class="features">{''.join(f'<div class="card"><h3>{E(t)}</h3><p>{E(d)}</p></div>' for t, d in FEATURES)}</div>
</div></section>

{SOON_BLOCK if soon else INSTALL_BLOCK}
</main>
<footer><div class="wrap">{E(pack.name)} by The Linux Workbench · Code {E(pack.license)}, wallpapers all rights reserved (free to use as wallpapers) · <a href="../">All themes</a> · <a href="{KOFI}">Support on Ko-fi</a></div></footer>
{SWITCH_JS}"""
    # the swatches follow the edition shown
    body = body.replace(f'<div class="swatches" data-for="dark">{swatches(dark)}</div>',
                        f'<div class="swatches only-dark">{swatches(dark)}</div><div class="swatches only-light">{swatches(light)}</div>')
    css += (".only-light { display: none; }\n"
            ":root[data-mode='light'] .only-light { display: grid; } :root[data-mode='light'] .only-dark { display: none; }\n"
            "@media (prefers-color-scheme: light) { :root:not([data-mode='dark']) .only-light { display: grid; }"
            " :root:not([data-mode='dark']) .only-dark { display: none; } }\n")
    (dest / "index.html").write_text(page(f"{pack.name} — The Linux Workbench",
                                          f"{pack.name}: {tagline}", css, body), encoding="utf-8")
    return {"id": pack.id, "name": pack.name, "tagline": tagline, "logo": f"{pack.id}/{logo}",
            "wall": f"{pack.id}/{walls['dark']}" if walls["dark"] else None,
            "dots": [dark.roles[k] for k in ("window_bg", "surface_raised", "accent", "text")],
            "soon": soon, "deep": dark.roles["base_bg"], "surface": dark.roles["surface_raised"], "accent": dark.roles["accent"]}


def home(cards, out: Path):
    neutral_dark = ("--bg: #15171c; --deep: #0f1115; --surface: #1d2027; --raised: #262a33; --line: #2c3039; "
                    "--text: #eef0f4; --muted: #a2a8b4; --accent: #9db8ff; --on-accent: #0f1115; --accent-rgb: 157, 184, 255;")
    neutral_light = ("--bg: #f6f6f4; --deep: #ecece8; --surface: #ffffff; --raised: #f0f0ed; --line: #e1e1dc; "
                     "--text: #1d2027; --muted: #5d6370; --accent: #3e63c9; --on-accent: #ffffff; --accent-rgb: 62, 99, 201;")
    css = (BASE_CSS + HOME_CSS + f":root {{ {neutral_dark} }}\n"
           f"@media (prefers-color-scheme: light) {{ :root {{ {neutral_light} }} }}\n")
    now = ", ".join(c["name"] for c in cards if not c["soon"])
    later = ", ".join(c["name"] for c in cards if c["soon"]) or "more themes"
    tiles = []
    for c in cards:
        bg = (f"background-image: url('{c['wall']}');" if c["wall"] else
              f"background: radial-gradient(600px 260px at 75% 0%, {c['accent']}55, transparent 60%), "
              f"linear-gradient(160deg, {c['surface']}, {c['deep']});")
        tiles.append(f"""<a class="tile" href="{c['id']}/"><div class="pic" style="{bg}"><img src="{c['logo']}" alt="" width="56" height="56"></div>
<div class="txt"><h2>{E(c['name'])}{' <span class="badge">Coming soon</span>' if c['soon'] else ''}</h2><p>{E(c['tagline'])}</p>
<div class="dots">{''.join(f'<i style="background:{d}"></i>' for d in c['dots'])}</div></div></a>""")
    body = f"""<header class="top"><div class="wrap">
  <a class="brand" href="./">The Linux Workbench <small>themes</small></a>
  <span class="spacer"></span><a class="navlink" href="{GITHUB}">GitHub</a>
</div></header>
<main class="wrap">
  <div class="intro"><h1>Desktop themes for workstations</h1>
  <p>Six complete themes for KDE Plasma 6 and COSMIC, each in Dark and Light: colours, apps, icons, cursors, panel, terminal and wallpapers, switched with one command.</p>
  <p class="roadmap"><b>Out now:</b> {E(now)}. <b>Coming next:</b> {E(later)}. Questions or problems? Use <a href="{GITHUB}/issues">GitHub Issues</a> or the comments on KDE-look.org.</p></div>
  <div class="grid">{''.join(tiles)}</div>
</main>
<footer><div class="wrap">The Linux Workbench · <a href="{GITHUB}">Source on GitHub</a> · <a href="{GITHUB}/issues">Report a problem</a> · <a href="{KOFI}">Support on Ko-fi</a></div></footer>"""
    (out / "index.html").write_text(page("The Linux Workbench themes",
                                         "Six desktop themes for KDE Plasma 6 and COSMIC, in Dark and Light.", css, body),
                                    encoding="utf-8")


def build(out: Path = ROOT / "site") -> Path:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    cards = [theme_page(load(ROOT / "packs" / pid), out) for pid in ORDER]
    home(cards, out)
    (out / ".nojekyll").write_text("")
    (out / "themes.json").write_text(json.dumps([{k: c[k] for k in ("id", "name", "tagline")} for c in cards], indent=1) + "\n")
    return out


if __name__ == "__main__":
    print("wrote", build())
