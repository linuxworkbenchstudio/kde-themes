"""Brand artwork: the theme's own pictures, laid out where Plasma looks for them.

packs/<pack>/art/ holds the finished artwork (made with the theme's design tools, or supplied):
  hicolor/<size>/apps/<command>*.png|svg    launcher and app icons    -> hicolor/
  wallpaper/images/, images_dark/, screenshot.png                     -> wallpapers/<Slug>/
  splash/<edition>/{background.jpg, wordmark.png, preview.png}        -> the Global Theme's splash
  previews/<edition>/{preview.png, fullscreenpreview.*}               -> the Global Theme's previews
  fastfetch/<command>-logo.txt                                        -> fastfetch/design/
Plasma picks wallpapers/<Slug>/contents/images_dark/ under dark colour schemes by itself.
"""
import json

from ..pack import Pack


def _files(root, prefix):
    return {f"{prefix}{p.relative_to(root).as_posix()}": p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()} if root.is_dir() else {}


def build(pack: Pack) -> dict:
    art = pack.root / "art"
    out = _files(art / "hicolor", "hicolor/")
    slug = pack.name.replace(" ", "-")
    wall = art / "wallpaper"
    if wall.is_dir():
        out.update(_files(wall, f"wallpapers/{slug}/contents/"))
        from . import TEMPLATES
        out[f"wallpapers/{slug}/COPYING"] = (TEMPLATES / "licences" / "CC-BY-SA-4.0.txt").read_text(encoding="utf-8")
        out[f"wallpapers/{slug}/metadata.json"] = json.dumps({"KPlugin": {
            "Id": slug, "Name": pack.name, "Description": "Dark and Light versions follow the colour scheme",
            "Authors": [{"Name": pack.brand}], "License": "CC-BY-SA-4.0", "Version": pack.version}},
            indent=2) + "\n"
    for ed in pack.editions.values():
        lnf = f"look-and-feel/{pack.lookandfeel_id}.{ed.id}/contents/"
        out.update(_files(art / "splash" / ed.id, lnf + "splash/images/"))
        out.update(_files(art / "previews" / ed.id, lnf + "previews/"))
    out.update(_files(art / "fastfetch", "fastfetch/design/"))
    return out
