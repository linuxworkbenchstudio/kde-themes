"""Bundled widgets: widgets/ - KVitals and Panel Colorizer, unchanged third-party copies shared by
every theme (templates/widgets/, with their own licences). The installer offers them when the
system doesn't have them."""
from ..pack import Pack
from . import TEMPLATES


def build(pack: Pack) -> dict:
    root = TEMPLATES / "widgets"
    return {f"widgets/{p.relative_to(root).as_posix()}": p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}
