"""How much of a released theme the engine reproduces: python3 -m engine compare PACK [REFERENCE]

Each file the engine makes is looked up in the reference (references/<pack>/ by default) and
counted as:
  exact          byte for byte the same
  same settings  an INI or JSON file with the same sections, keys and values in another order
  engine adds    an INI file where every released setting is the same and the engine adds more
                 (the engine may add settings; it must never change or drop a released one)
  different      exists in the reference but differs (the first few lines of difference are shown)
  new            the reference has no such file
Coverage is the share of the reference's theme files that the engine already makes exactly or
with the same settings.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

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
    different: list = field(default_factory=list)       # (path, first difference)
    new: list = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return (len(self.exact) + len(self.same) + len(self.adds)) / self.total if self.total else 0.0


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


def compare(files: dict[str, str], ref: Path) -> Report:
    meta = json.loads((ref / "reference.json").read_text())
    mapping = meta.get("map", {})
    r = Report(ref)
    theme_files = [p for p in ref.rglob("*") if p.is_file()
                   and not any(p.relative_to(ref).as_posix().startswith(x) for x in NOT_THEME)]
    r.total = len(theme_files)
    for rel, text in sorted(files.items()):
        target = ref / reference_path(rel, mapping)
        if not target.is_file():
            r.new.append(rel)
            continue
        released = target.read_text(encoding="utf-8", errors="replace")
        if released == text:
            r.exact.append(rel)
        elif Path(rel).suffix in INI_SUFFIXES and ini(text) is not None and ini(released) is not None:
            mine, theirs = ini(text), ini(released)
            if mine == theirs:
                r.same.append(rel)
            elif all(sec in mine and all(mine[sec].get(k) == v for k, v in kv.items()) for sec, kv in theirs.items()):
                extra = [f"{sec}{k}" for sec, kv in mine.items() for k in kv if k not in theirs.get(sec, {})]
                r.adds.append((rel, extra))
            else:
                r.different.append((rel, first_difference(text, released)))
        elif Path(rel).suffix == ".json" and _json_equal(text, released):
            r.same.append(rel)
        else:
            r.different.append((rel, first_difference(text, released)))
    return r


def _json_equal(a: str, b: str) -> bool:
    try:
        return json.loads(a) == json.loads(b)
    except ValueError:
        return False
