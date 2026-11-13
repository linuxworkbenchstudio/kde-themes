#!/usr/bin/env python3
"""Build a theme's release: the download zip, and the KDE Store packages.

    python3 tools/release.py PACK [PACK ...] [--skip-tests] [--out dist/releases]

For each pack, into OUT/<Folder>/ (e.g. dist/releases/Waypoint-0.1.0/):
  <Folder>.zip                 the full theme with install.sh (the main download)
  <Name>-COSMIC-<ver>.zip      the COSMIC theme as its own download: Dark and Light .ron files,
                               wallpapers, install.sh / uninstall.sh (the KDE zip does not hold it)
  store/                       one package per KDE Store category, each installable by Plasma's
                               "Get New ..." or by unpacking into the usual folder:
                               Global Themes, Plasma Styles, window decorations, colour schemes,
                               Konsole, cursors, icons, Kvantum, GTK, wallpaper
  CHECKSUMS.sha256
Before packing, the built theme is checked: tests/validate.sh (every program parses, every JSON
and SVG reads) and, unless --skip-tests, the full test suite tests/run-tests.sh (installs,
switches and uninstalls in a throw-away home; about 40 minutes per theme). A failure stops it.
The zip holds no symbolic links (the installer makes the cursor aliases from aliases.txt); the
cursor packages for the Store keep them. Files are sorted and dated SOURCE_DATE_EPOCH (or the day
of the build), so the same input gives the same zip. Refuses to overwrite an existing release.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine.__main__ import build  # noqa: E402
from engine.files import Link  # noqa: E402
from engine.pack import load  # noqa: E402
from engine.parts.docs import folder  # noqa: E402

JUNK = ("__pycache__", ".pyc", ".vh-tmp.", "~", ".DS_Store")


def stamp() -> float:
    if os.environ.get("SOURCE_DATE_EPOCH"):
        return float(os.environ["SOURCE_DATE_EPOCH"])
    t = time.gmtime()
    return time.mktime((t.tm_year, t.tm_mon, t.tm_mday, 0, 0, 0, 0, 0, 0)) - time.timezone


def stage(pack, where: Path) -> Path:
    top = where / folder(pack)
    for rel, value in build(pack).items():
        p = top / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, Link):
            p.symlink_to(value.target)
        elif isinstance(value, bytes):
            p.write_bytes(value)
        else:
            p.write_text(value, encoding="utf-8")
            if value.startswith("#!"):
                p.chmod(0o755)
    return top


def check(top: Path, tests: bool) -> None:
    print("  validate:", end=" ", flush=True)
    r = subprocess.run(["bash", "tests/validate.sh"], cwd=top, capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip())
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    if tests:
        print("  test suite (about 40 minutes) ...", flush=True)
        extra = ["--allow-root"] if os.geteuid() == 0 else []
        r = subprocess.run(["bash", "tests/run-tests.sh", "--no-static"], cwd=top, capture_output=True, text=True,
                           env=dict(os.environ, **({"EXTRA": " ".join(extra)} if extra else {})))
        plain = [l for l in r.stdout.splitlines() if "passed" in l and "failed" in l]
        print("  " + (plain[-1].strip() if plain else "no summary"))
        if r.returncode or not plain or " 0 failed" not in plain[-1]:
            fails = [l for l in r.stdout.splitlines() if "FAIL" in l]
            sys.exit("test suite failed:\n" + "\n".join(fails[:40]))
    for p in sorted(top.rglob("*"), reverse=True):    # what the checks left behind
        if any(j in p.name for j in JUNK) or p.name == "__pycache__":
            shutil.rmtree(p) if p.is_dir() and not p.is_symlink() else p.unlink()


def files_of(top: Path):
    return sorted(p for p in top.rglob("*") if p.is_file() or p.is_symlink())


def make_zip(top: Path, out: Path, when: float) -> None:
    dt = time.gmtime(when)[:6]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files_of(top):
            if p.is_symlink():
                continue
            info = zipfile.ZipInfo(f"{top.name}/{p.relative_to(top).as_posix()}", dt)
            info.external_attr = (0o100755 if os.access(p, os.X_OK) else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())


def make_tar(paths: list[Path], base: Path, out: Path, when: float) -> None:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as t:
        for root in paths:
            for p in [root, *(sorted(root.rglob("*")) if root.is_dir() and not root.is_symlink() else [])]:
                info = t.gettarinfo(str(p), arcname=p.relative_to(base).as_posix())
                info.mtime, info.uid, info.gid, info.uname, info.gname = int(when), 0, 0, "", ""
                info.mode = 0o755 if (p.is_dir() or os.access(p, os.X_OK)) and not p.is_symlink() else 0o644
                if p.is_file() and not p.is_symlink():
                    with open(p, "rb") as fh:
                        t.addfile(info, fh)
                else:
                    t.addfile(info)
    import gzip
    out.write_bytes(gzip.compress(buf.getvalue(), compresslevel=9, mtime=int(when)))


def store(pack, top: Path, out: Path, when: float) -> list[Path]:
    """One package per KDE Store category."""
    out.mkdir()
    slug = pack.name.replace(" ", "-")
    made = []

    def tar(name, paths, base):
        paths = [p for p in paths if p.exists()]
        if paths:
            dest = out / f"{name}.tar.gz"
            make_tar(paths, base, dest, when)
            made.append(dest)
    for ed in pack.editions.values():
        E = ed.name
        tar(f"{slug}-{E}-Global-Theme", [top / f"look-and-feel/{pack.lookandfeel_id}.{ed.id}"], top / "look-and-feel")
        tar(f"{slug}-{E}-Plasma-Style", [top / "plasma/desktoptheme" / pack.file_name("plasma_style", ed)], top / "plasma/desktoptheme")
        tar(f"{slug}-{E}-Window-Decoration", [top / "aurorae/themes" / pack.file_name("aurorae", ed)], top / "aurorae/themes")
        tar(f"{slug}-{E}-Cursors", [top / "cursors" / pack.file_name("cursors", ed)], top / "cursors")
        tar(f"{slug}-{E}-Kvantum", [top / "Kvantum" / pack.file_name("kvantum", ed)], top / "Kvantum")
        tar(f"{slug}-{E}-GTK", [top / "gtk" / pack.file_name("gtk", ed)], top / "gtk")
        cs = top / "color-schemes" / f"{pack.file_name('color_scheme', ed)}.colors"
        if cs.is_file():
            shutil.copy2(cs, out / cs.name)
            made.append(out / cs.name)
    icons = sorted({pack.file_name("icons", ed) for ed in pack.editions.values()})
    for name in icons:
        tar(f"{name}-Icons" if "Icons" not in name else name, [top / "icons" / name], top / "icons")
    tar(f"{slug}-Konsole", sorted((top / "konsole").glob("*")), top / "konsole")
    tar(f"{slug}-Wallpaper", [top / "wallpapers" / slug], top / "wallpapers")
    return made


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("packs", nargs="+")
    ap.add_argument("--skip-tests", action="store_true", help="validate only (not for a public release)")
    ap.add_argument("--out", default=str(ROOT / "dist" / "releases"))
    a = ap.parse_args(argv)
    when = stamp()
    for spec in a.packs:
        pack = load(ROOT / "packs" / spec if not Path(spec).exists() else spec)
        dest = Path(a.out) / folder(pack)
        if dest.exists():
            sys.exit(f"{dest} exists - remove it first")
        print(f"{pack.name} {pack.version}")
        work = Path(a.out) / f".stage-{pack.id}"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        top = stage(pack, work)
        check(top, not a.skip_tests)
        dest.mkdir(parents=True)
        cosmic_top = None
        if (top / "cosmic").is_dir():   # COSMIC is its own download
            cosmic_top = work / f"{pack.name.replace(' ', '-')}-COSMIC-{pack.version}"
            shutil.move(str(top / "cosmic"), str(cosmic_top))
        z = dest / f"{folder(pack)}.zip"
        make_zip(top, z, when)
        made = [z]
        if cosmic_top:
            cz = dest / f"{cosmic_top.name}.zip"
            make_zip(cosmic_top, cz, when)
            made.append(cz)
        made += store(pack, top, dest / "store", when)
        (dest / "CHECKSUMS.sha256").write_text("".join(f"{sha(p)}  {p.relative_to(dest).as_posix()}\n" for p in made))
        shutil.rmtree(work)
        mb = z.stat().st_size / 1e6
        print(f"  {z.relative_to(Path(a.out))}  {mb:.1f} MB; "
              + (f"{cosmic_top.name}.zip; " if cosmic_top else "")
              + f"{len(made) - (2 if cosmic_top else 1)} Store packages; CHECKSUMS.sha256")
    return 0


if __name__ == "__main__":
    sys.exit(main())
