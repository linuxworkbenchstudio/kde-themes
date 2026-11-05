"""Release documents: README.md, CHANGELOG.md, LICENSE and LICENSES/ at the top of the release.

README and LICENSE are templates/docs/, filled in for the pack; CHANGELOG.md is the pack's own
(packs/<pack>/CHANGELOG.md); LICENSES/ holds every licence text the parts use.
"""
from ..pack import Pack
from . import TEMPLATES


def folder(pack: Pack) -> str:
    """The release's top folder (and zip name): Waypoint-0.1.0, Vice-Horizon-0.1.0 ..."""
    return f"{pack.name.replace(' ', '-')}-{pack.version}"


def build(pack: Pack) -> dict:
    tagline = pack.raw.get("theme", {}).get("programs", {}).get("tagline", f"{pack.name} for KDE Plasma 6.")
    values = {"@@NAME@@": pack.name, "@@VERSION@@": pack.version, "@@BRAND@@": pack.brand,
              "@@COMMAND@@": pack.command, "@@TAGLINE@@": tagline, "@@FOLDER@@": folder(pack)}
    out = {}
    for name in ("README.md", "LICENSE"):
        text = (TEMPLATES / "docs" / name).read_text(encoding="utf-8")
        for k, v in values.items():
            text = text.replace(k, v)
        out[name] = text
    log = pack.root / "CHANGELOG.md"
    if log.is_file():
        out["CHANGELOG.md"] = log.read_text(encoding="utf-8")
    for p in sorted((TEMPLATES / "licences").glob("*.txt")):
        out[f"LICENSES/{p.name}"] = p.read_text(encoding="utf-8")
    return out
