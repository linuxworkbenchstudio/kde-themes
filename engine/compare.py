"""How much of a released theme the engine reproduces: python3 -m engine compare PACK [REFERENCE]

Each file the engine makes is looked up in the reference (references/<pack>/ by default) and
counted as:
  exact          byte for byte the same
  same settings  an INI or JSON file with the same sections, keys and values in another order,
                 or a PNG image with the same pixels
  engine adds    an INI file where every released setting is the same and the engine adds more
                 (the engine may add settings; it must never change or drop a released one)
  changed on purpose   differs, and reference.json "accept" says why (e.g. Plasma 6 metadata keys)
  different      exists in the reference but differs (the first few lines of difference are shown)
  new            the reference has no such file (expected when it matches reference.json "new_ok")

reference.json "rename" turns old names in the reference into new ones before comparing (the
brand, the version: DigitalCohesion -> The Linux Workbench, 0.5.0 -> 0.1.0).
.svgz files are compared unpacked; links by their target.
Coverage is the share of the reference's theme files that the engine already makes exactly or
with the same settings.
"""
import fnmatch
import gzip
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from . import png
from .files import Link

INI_SUFFIXES = {".colors", ".colorscheme", ".profile", ".kvconfig", ".desktop", ".theme", ""}
# files in a reference that are not part of the theme itself
NOT_THEME = ("reference.json", "VERSION", "LICENSE", "LICENSES/")


def ini(text: str):
    out, sec = {}, ""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            sec = line
            out.setdefault(sec, {})
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            out.setdefault(sec, {})[k.strip()] = v.strip()
        else:
            return None                 # not an INI file
    return out


@dataclass
class Report:
    reference: Path
    total: int = 0
    exact: list = field(default_factory=list)
    same: list = field(default_factory=list)
    adds: list = field(default_factory=list)            # (path, keys the engine adds)
    accepted: list = field(default_factory=list)        # (path, why)
    different: list = field(default_factory=list)       # (path, first difference)
    new: list = field(default_factory=list)
    new_ok: list = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return self.covered / self.total if self.total else 0.0

    @property
    def covered(self) -> int:
        return len(self.exact) + len(self.same) + len(self.adds) + len(self.accepted)


def reference_path(rel: str, mapping: dict) -> str:
    best = ""
    for prefix in mapping:
        if rel.startswith(prefix) and len(prefix) > len(best):
            best = prefix
    return mapping[best] + rel[len(best):] if best else rel


def first_difference(a: str, b: str) -> str:
    pa, pb = ini(a), ini(b)
    if pa is not None and pb is not None:
        for sec in list(pb) + [s for s in pa if s not in pb]:
            for k in sorted(set(pa.get(sec, {})) | set(pb.get(sec, {}))):
                x, y = pa.get(sec, {}).get(k), pb.get(sec, {}).get(k)
                if x != y:
                    return f"{sec} {k}: engine {x!r}, released {y!r}"
    for i, (x, y) in enumerate(zip(a.splitlines(), b.splitlines()), 1):
        if x != y:
            return f"line {i}: engine {x!r}, released {y!r}"
    return "different length"


def _released(target: Path, rename: dict):
    """The reference file as text (renamed), or bytes when it isn't text."""
    if target.is_symlink():
        return Link(os.readlink(target))
    data = target.read_bytes()
    if target.suffix == ".svgz":
        try:
            data = gzip.decompress(data)
        except OSError:
            return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    for old, new in rename.items():
        text = text.replace(old, new)
    return text


def _mine(rel: str, value):
    if isinstance(value, Link):
        return value
    if isinstance(value, bytes):
        if rel.endswith(".svgz"):
            value = gzip.decompress(value)
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value
    return value


def compare(files: dict, ref: Path) -> Report:
    meta = json.loads((ref / "reference.json").read_text())
    mapping = meta.get("map", {})
    rename = meta.get("rename", {})
    accept = meta.get("accept", [])
    new_ok = meta.get("new_ok", [])
    r = Report(ref)
    # aliases the reference lists in an aliases.txt instead of storing links: "name target" per line
    listed = {}
    for a in ref.rglob("aliases.txt"):
        for line in a.read_text().splitlines():
            if line and not line.startswith("#") and len(line.split()) == 2:
                name, tgt = line.split()
                listed[(a.parent / "cursors" / name).as_posix()] = tgt
    theme_files = [p for p in ref.rglob("*") if (p.is_file() or p.is_symlink())
                   and not any(p.relative_to(ref).as_posix().startswith(x) for x in NOT_THEME)]
    r.total = len(theme_files)
    for rel, value in sorted(files.items()):
        target = ref / reference_path(rel, mapping)
        if isinstance(value, Link) and not (target.is_file() or target.is_symlink()) and target.as_posix() in listed:
            ok = listed[target.as_posix()] == value.target
            (r.exact if ok else r.different).append(rel if ok else (rel, f"aliases.txt has {listed[target.as_posix()]}"))
            continue
        if not (target.is_file() or target.is_symlink()):
            (r.new_ok if any(fnmatch.fnmatch(rel, pat) for pat in new_ok) else r.new).append(rel)
            continue
        released, mine = _released(target, rename), _mine(rel, value)
        if isinstance(mine, Link):
            # a zip unpacked without links leaves a small file holding the target's name
            ok = (released == mine) or (isinstance(released, str) and released == mine.target)
            (r.exact if ok else r.different).append(rel if ok else (rel, f"link to {mine.target}"))
            continue
        why = next((a["why"] for a in accept if fnmatch.fnmatch(rel, a["path"])), None)
        if released == mine:
            r.exact.append(rel)
        elif rel.endswith(".png") and isinstance(mine, bytes) and isinstance(released, bytes) \
                and png.same_pixels(mine, released):
            r.same.append(rel)
        elif isinstance(mine, bytes) or isinstance(released, bytes):
            (r.accepted.append((rel, why)) if why else r.different.append((rel, "binary content differs")))
        elif Path(rel).suffix in INI_SUFFIXES and ini(mine) is not None and ini(released) is not None:
            a_, b_ = ini(mine), ini(released)
            if a_ == b_:
                r.same.append(rel)
            elif all(sec in a_ and all(a_[sec].get(k) == v for k, v in kv.items()) for sec, kv in b_.items()):
                extra = [f"{sec}{k}" for sec, kv in a_.items() for k in kv if k not in b_.get(sec, {})]
                r.adds.append((rel, extra))
            elif why:
                r.accepted.append((rel, why))
            else:
                r.different.append((rel, first_difference(mine, released)))
        elif Path(rel).suffix == ".json" and _json_equal(mine, released):
            r.same.append(rel)
        elif why:
            r.accepted.append((rel, why))
        else:
            r.different.append((rel, first_difference(mine, released)))
    return r


def _json_equal(a: str, b: str) -> bool:
    try:
        return json.loads(a) == json.loads(b)
    except ValueError:
        return False
