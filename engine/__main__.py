"""python3 -m engine build PACK [--out DIR] [--part NAME ...]
   python3 -m engine check PACK              read and validate a pack, print its palette
   python3 -m engine compare PACK [REF]      how much of the released theme the engine reproduces"""
import argparse
import sys
from pathlib import Path

from .colour import contrast
from .files import Link
from .pack import PackError, load
from .parts import PARTS


def build(pack, parts=None) -> dict[str, str]:
    out = {}
    for name, part in PARTS.items():  # noqa: B007
        if name not in pack.parts or (parts and name not in parts):
            continue
        for path, text in part.build(pack).items():
            if path in out:
                raise RuntimeError(f"two parts write {path}")
            out[path] = text
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="engine", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("pack")
    b.add_argument("--out", default="dist")
    b.add_argument("--part", action="append", choices=sorted(PARTS))
    c = sub.add_parser("check")
    c.add_argument("pack")
    m = sub.add_parser("compare")
    m.add_argument("pack")
    m.add_argument("reference", nargs="?")
    a = ap.parse_args(argv)
    try:
        pack = load(a.pack)
    except PackError as e:
        print(f"The pack has problems:\n  " + "\n  ".join(e.problems), file=sys.stderr)
        return 1
    if a.cmd == "compare":
        from .compare import compare
        ref = Path(a.reference) if a.reference else Path(__file__).resolve().parent.parent / "references" / pack.id
        if not (ref / "reference.json").is_file():
            print(f"No reference at {ref}: import one with tools/import_reference.py", file=sys.stderr)
            return 1
        r = compare(build(pack), ref)
        made = r.covered + len(r.different) + len(r.new) + len(r.new_ok)
        print(f"{pack.name}: the engine makes {made} files (parts: {', '.join(pack.parts) or 'none yet'})")
        print(f"  exact {len(r.exact)}, same settings {len(r.same)}, engine adds settings {len(r.adds)}, "
              f"changed on purpose {len(r.accepted)}, different {len(r.different)}, "
              f"new {len(r.new)} (+{len(r.new_ok)} expected)")
        for rel, why in r.accepted[:5]:
            print(f"  on purpose: {rel}: {why}")
        for rel, extra in r.adds[:10]:
            print(f"  adds: {rel}: {', '.join(extra[:6])}{' ...' if len(extra) > 6 else ''}")
        for rel, why in r.different[:20]:
            print(f"  different: {rel}\n      {why}")
        for rel in r.new[:10]:
            print(f"  new: {rel}")
        print(f"  coverage: {r.covered} of {r.total} released theme files ({r.coverage:.1%})")
        return 1 if r.different else 0
    if a.cmd == "check":
        print(f"{pack.name} {pack.version} ({pack.brand}), command '{pack.command}', Global Theme {pack.lookandfeel_id}.dark/.light")
        if pack.previous_ids:
            print(f"  replaces: {', '.join(pack.previous_ids)}")
        print(f"  parts made by the engine: {', '.join(pack.parts) or 'none yet'}")
        for ed in pack.editions.values():
            print(f"\n{pack.display(ed)}")
            r_ = ed.roles
            for k in ("window_bg", "view_bg", "header_bg", "button_bg", "border", "text", "text_muted", "accent",
                      "selection_bg", "selection_fg", "link", "negative", "neutral", "positive"):
                print(f"  {k:14} {r_[k]}")
            for label, fg, bg in (("text on window", r_["text"], r_["window_bg"]), ("muted on window", r_["text_muted"], r_["window_bg"]),
                                  ("link on view", r_["link"], r_["view_bg"]), ("selection text", r_["selection_fg"], r_["selection_bg"])):
                r = contrast(fg, bg)
                print(f"  contrast {label:16} {r:5.2f}:1{'   below 4.5:1' if r < 4.5 else ''}")
        return 0
    root = Path(a.out) / pack.id
    files = build(pack, a.part)
    for rel, value in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, Link):
            if p.is_symlink() or p.exists():
                p.unlink()
            p.symlink_to(value.target)
        elif isinstance(value, bytes):
            p.write_bytes(value)
        else:
            p.write_text(value, encoding="utf-8")
            if value.startswith("#!"):          # programs stay runnable
                p.chmod(0o755)
    print(f"{len(files)} files written to {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
