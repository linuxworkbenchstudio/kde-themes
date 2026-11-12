#!/usr/bin/env python3
"""@@NAME@@ colours for Fastfetch: recolours the user's own Fastfetch config, nothing else.

    @@COMMAND@@-fastfetch.py                     preview: show the changes as a diff (writes nothing)
    @@COMMAND@@-fastfetch.py --apply             write them (the original is kept, see below)
    @@COMMAND@@-fastfetch.py --restore           put the original config back
Options: --variant dark|light|auto (auto: from KDE's colour scheme, else dark)
         --config FILE   recolour this file instead of the one Fastfetch would use
         --from FILE     start from FILE (e.g. a backup) instead of the current config
         --if-applied    only act if @@NAME@@ colours were applied before (for `@@COMMAND@@ dark|light`)

What changes (only colour values; layout, modules, logo, keys and formats stay as they are):
  display.color             keys + title = @@NAME@@ accent, separator = muted, output = terminal text
  logo.color                1 = accent, 2 = terminal text, 3 = muted (repeating up to 9);
                            a The Linux Workbench theme logo (<theme>-logo.txt, from an older
                            design) is swapped for the distro's own logo
  modules[].keyColor        accent (only where the module already sets one)
  modules[].outputColor     terminal text (only where already set)
  title module color        user/host accent, @ muted (only where already set)
Left alone on purpose: percent/temperature/bar colours (they mean good/warning/critical),
the "colors" module, and {#..} colour codes written inside key or format strings (reported).

Which file: the same search Fastfetch does ($XDG_CONFIG_HOME, ~/.config, ~, $XDG_CONFIG_DIRS,
/etc/xdg, /etc; config.jsonc before config.json5). A file in your home folder is edited in place,
keeping comments and formatting. A system-wide file is copied into ~/.config/fastfetch first.
No config at all: Fastfetch's own default layout is written (from `fastfetch --gen-config`
when Fastfetch is installed), then recoloured.
Backups: the first --apply keeps the untouched file as <config>.@@COMMAND@@-original; every
--apply keeps the file it replaced as <config>.@@COMMAND@@-previous. Nothing is deleted.
Needs only Python 3 (standard library). No network, no root.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# @@NAME@@ palette (from the theme pack). Raw 24-bit ANSI codes work in every Fastfetch version.
PALETTE = @@FF_PALETTE@@
THEMES = ["@@COMMAND@@", *@@SIBLINGS@@]   # The Linux Workbench themes (their old Fastfetch logos)
TEXT = "39"            # the terminal's own text colour (default foreground)
DEFAULT_MODULES = ["title", "separator", "os", "host", "kernel", "uptime", "packages", "shell",
                   "display", "de", "wm", "wmtheme", "theme", "icons", "font", "cursor", "terminal",
                   "terminalfont", "cpu", "gpu", "memory", "swap", "disk", "localip", "battery",
                   "poweradapter", "locale", "break", "colors"]
SCHEMA = "https://github.com/fastfetch-cli/fastfetch/raw/dev/doc/json_schema.json"


def rgb(c):
    return "38;2;%d;%d;%d" % c


def colours(variant):
    p = PALETTE[variant]
    accent, muted = rgb(p["accent"]), rgb(p["muted"])
    return {
        "display": {"keys": accent, "title": accent, "separator": muted, "output": TEXT},
        "logo": {str(i): (accent, TEXT, muted)[(i - 1) % 3] for i in range(1, 10)},
        "key": accent, "output": TEXT,
        "title": {"user": accent, "at": muted, "host": accent},
    }


# ---------------------------------------------------------------- JSONC / JSON5 reader with spans
class Node:
    def __init__(self, kind, start, end):
        self.kind, self.start, self.end = kind, start, end
        self.members = []      # obj: [(key, key_start, value_node)]
        self.items = []        # arr: [value_node]
        self.text = ""         # scalar source text

    def get(self, key):
        for k, _, v in self.members:
            if k == key:
                return v
        return None


class Parser:
    def __init__(self, s):
        self.s, self.i = s, 0

    def err(self, msg):
        line = self.s.count("\n", 0, self.i) + 1
        raise ValueError(f"{msg} (line {line})")

    def ws(self):
        s = self.s
        while self.i < len(s):
            c = s[self.i]
            if c in " \t\r\n﻿":
                self.i += 1
            elif s.startswith("//", self.i):
                j = s.find("\n", self.i)
                self.i = len(s) if j < 0 else j + 1
            elif s.startswith("/*", self.i):
                j = s.find("*/", self.i + 2)
                if j < 0:
                    self.err("unclosed comment")
                self.i = j + 2
            else:
                break

    def string(self):
        q, start = self.s[self.i], self.i
        self.i += 1
        while self.i < len(self.s):
            c = self.s[self.i]
            if c == "\\":
                self.i += 2
                continue
            self.i += 1
            if c == q:
                raw = self.s[start:self.i]
                try:
                    val = json.loads(raw if q == '"' else '"' + raw[1:-1].replace('"', '\\"') + '"')
                except ValueError:
                    val = raw[1:-1]
                return val, start
        self.err("unclosed string")

    def bare(self):
        start = self.i
        while self.i < len(self.s) and (self.s[self.i].isalnum() or self.s[self.i] in "_$+-.@"):
            self.i += 1
        if self.i == start:
            self.err(f"unexpected character {self.s[self.i]!r}")
        return self.s[start:self.i], start

    def value(self):
        self.ws()
        if self.i >= len(self.s):
            self.err("unexpected end of file")
        c = self.s[self.i]
        if c == "{":
            n = Node("obj", self.i, 0)
            self.i += 1
            while True:
                self.ws()
                if self.s[self.i:self.i + 1] == "}":
                    self.i += 1
                    break
                key, ks = self.string() if self.s[self.i] in "\"'" else self.bare()
                self.ws()
                if self.s[self.i:self.i + 1] != ":":
                    self.err("expected ':'")
                self.i += 1
                n.members.append((key, ks, self.value()))
                self.ws()
                if self.s[self.i:self.i + 1] == ",":
                    self.i += 1
                elif self.s[self.i:self.i + 1] != "}":
                    self.err("expected ',' or '}'")
            n.end = self.i
            return n
        if c == "[":
            n = Node("arr", self.i, 0)
            self.i += 1
            while True:
                self.ws()
                if self.s[self.i:self.i + 1] == "]":
                    self.i += 1
                    break
                n.items.append(self.value())
                self.ws()
                if self.s[self.i:self.i + 1] == ",":
                    self.i += 1
                elif self.s[self.i:self.i + 1] != "]":
                    self.err("expected ',' or ']'")
            n.end = self.i
            return n
        if c in "\"'":
            val, start = self.string()
            n = Node("str", start, self.i)
            n.text = val
            return n
        text, start = self.bare()
        n = Node("lit", start, self.i)
        n.text = text
        return n


def parse(s):
    p = Parser(s)
    root = p.value()
    p.ws()
    if p.i != len(s):
        p.err("extra text after the config")
    if root.kind != "obj":
        raise ValueError("the config is not a JSON object")
    return root


def parse_value(s):
    p = Parser(s)
    v = p.value()
    p.ws()
    if p.i != len(s):
        p.err("extra text")
    return v


def to_py(n):
    if n.kind == "obj":
        return {k: to_py(v) for k, _, v in n.members}
    if n.kind == "arr":
        return [to_py(v) for v in n.items]
    return (n.kind, n.text)


# ---------------------------------------------------------------- edits
def jdump(v):
    return json.dumps(v, ensure_ascii=False)


def indent_at(s, pos):
    line_start = s.rfind("\n", 0, pos) + 1
    j = line_start
    while j < len(s) and s[j] in " \t":
        j += 1
    return s[line_start:j]


class Editor:
    def __init__(self, s):
        self.s, self.edits, self.log = s, [], []

    def replace(self, node, text, what):
        try:
            same = to_py(node) == to_py(parse_value(text))
        except ValueError:
            same = False
        if not same:
            self.edits.append((node.start, node.end, text))
            self.log.append(f"set {what}")

    def insert_member(self, obj, key, text, what):
        """Add "key": text to obj (after "$schema" if there is one, else first), matching its indentation."""
        s = self.s
        schema = [m for m in obj.members if m[0] == "$schema"]
        if schema:
            ind = indent_at(s, schema[0][1])
            self.edits.append((schema[0][2].end, schema[0][2].end, f",\n{ind}{jdump(key)}: {text}"))
            self.log.append(f"add {what}")
            return
        if obj.members:
            ind = indent_at(s, obj.members[0][1])
            first_on_new_line = "\n" in s[obj.start + 1:obj.members[0][1]]
            ins = (f"\n{ind}{jdump(key)}: {text}," if first_on_new_line else f" {jdump(key)}: {text},")
        else:
            ind = indent_at(s, obj.start)
            ins = f"\n{ind}{UNIT[0]}{jdump(key)}: {text}\n{ind}"
            if s[obj.start + 1:obj.end - 1].strip():      # only comments inside: keep them after
                ins = f"\n{ind}{UNIT[0]}{jdump(key)}: {text}"
        self.edits.append((obj.start + 1, obj.start + 1, ins))
        self.log.append(f"add {what}")

    def set_member(self, obj, key, text, what):
        v = obj.get(key)
        if v is None:
            self.insert_member(obj, key, text, what)
        else:
            self.replace(v, text, what)

    def result(self):
        out = self.s
        for a, b, t in sorted(self.edits, key=lambda e: (e[0], e[1]), reverse=True):
            out = out[:a] + t + out[b:]
        return out


UNIT = ["  "]          # indent step of the file being edited (set by recolour)


def pretty_obj(d, ind):
    """A small object on several lines, indented to sit at `ind`."""
    inner = ind + UNIT[0]
    return "{\n" + ",\n".join(f"{inner}{jdump(k)}: {jdump(v)}" for k, v in d.items()) + f"\n{ind}}}"


def recolour(text, variant):
    c = colours(variant)
    root = parse(text)
    ed = Editor(text)
    notes = []

    # display.color
    rind = indent_at(text, root.members[0][1]) if root.members else "  "
    UNIT[0] = rind or "  "
    disp = root.get("display")
    if disp is None:
        ed.insert_member(root, "display", "{\n" + f'{rind}{UNIT[0]}"color": ' + pretty_obj(c["display"], rind + UNIT[0])
                         + f"\n{rind}}}", "display.color")
    elif disp.kind == "obj":
        col = disp.get("color")
        ind = indent_at(text, col.start if col else (disp.members[0][1] if disp.members else disp.start))
        ed.set_member(disp, "color", pretty_obj(c["display"], ind), "display.color")
    else:
        notes.append("'display' is not an object; left alone")

    # logo.color
    logo = root.get("logo")
    if logo is None:
        ed.insert_member(root, "logo", "{\n" + f'{rind}{UNIT[0]}"color": ' + jdump(c["logo"]) + f"\n{rind}}}", "logo.color")
    elif logo.kind == "obj":
        typ = logo.get("type")
        if typ is not None and typ.kind == "str" and typ.text in ("none", "kitty", "kitty-direct", "kitty-icat",
                                                               "sixel", "iterm", "chafa", "raw"):
            notes.append(f"logo type '{typ.text}' is a picture or none; its colours were left alone")
        elif (logo.get("source") is not None and logo.get("source").kind == "str"
              and any(f"{o}-logo" in logo.get("source").text for o in THEMES)):
            # an older The Linux Workbench design with a theme logo: same layout, the distro's logo
            other = next(o for o in THEMES if f"{o}-logo" in logo.get("source").text)
            keep = [f"{jdump(k)}: {text[v.start:v.end]}" for k, _, v in logo.members
                    if k not in ("type", "source", "color")]          # padding and the like, as written
            ed.replace(logo, "{ " + ", ".join([*keep, f'"color": {jdump(c["logo"])}']) + " }",
                       f"logo ({other} logo -> your distro's logo)")
        else:
            ed.set_member(logo, "color", jdump(c["logo"]), "logo.color")
    elif logo.kind == "str":
        if logo.text.lower() == "none":
            notes.append("logo is 'none'; nothing to colour")
        else:                       # "logo": "arch"  ->  same logo, with colours
            ed.replace(logo, "{ " + f'"source": {jdump(logo.text)}, "color": {jdump(c["logo"])}' + " }",
                       f"logo.color (logo '{logo.text}' kept)")
    else:
        notes.append("'logo' is not set as a name or object; left alone")

    # modules: only colours they already set
    mods = root.get("modules")
    if mods is not None and mods.kind == "arr":
        for i, m in enumerate(mods.items):
            if m.kind != "obj":
                continue
            tnode = m.get("type")
            t = tnode.text.lower() if tnode is not None and tnode.kind == "str" else f"#{i + 1}"
            for k, val in (("keyColor", c["key"]), ("outputColor", c["output"])):
                if m.get(k) is not None:
                    ed.replace(m.get(k), jdump(val), f"modules[{t}].{k}")
            if t == "title" and m.get("color") is not None and m.get("color").kind == "obj":
                ed.replace(m.get("color"), jdump(c["title"]), "modules[title].color")
    inline = text.count("{#")
    if inline:
        notes.append(f"{inline} inline colour code(s) like {{#31}} inside key/format strings were left as written")

    new = ed.result()
    parse(new)                       # must still read back
    return new, ed.log, notes


# ---------------------------------------------------------------- locating the config
def config_dirs():
    home = Path.home()
    dirs = []
    if os.environ.get("XDG_CONFIG_HOME"):
        dirs.append(Path(os.environ["XDG_CONFIG_HOME"]))
    dirs += [home / ".config", home]
    dirs += [Path(d) for d in os.environ.get("XDG_CONFIG_DIRS", "").split(":") if d]
    dirs += [Path("/etc/xdg"), Path("/etc")]
    out = []
    for d in dirs:
        if d not in out:
            out.append(d)
    return out


def user_dir():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "fastfetch"


def find_config():
    for d in config_dirs():
        for name in ("config.jsonc", "config.json5"):
            p = d / "fastfetch" / name
            if p.is_file():
                return p
    return None


def in_home(p):
    try:
        p.resolve().relative_to(Path.home().resolve())
        return True
    except ValueError:
        return False


def default_config_text():
    ff = shutil.which("fastfetch")
    if ff:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "config.jsonc"
            try:
                subprocess.run([ff, "--gen-config", str(out)], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=60, check=True)
                t = out.read_text(encoding="utf-8")
                root = parse(t)
                if root.get("modules") is not None:
                    return t, "Fastfetch's default layout (fastfetch --gen-config)"
            except Exception:
                pass
    t = json.dumps({"$schema": SCHEMA, "modules": DEFAULT_MODULES}, indent=2) + "\n"
    return t, "Fastfetch's standard default layout"


def detect_variant():
    kg = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "kdeglobals"
    try:
        for line in kg.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("ColorScheme="):
                return "light" if "light" in line.lower() else "dark"
    except OSError:
        pass
    return "dark"


def check_with_fastfetch(text, suffix):
    """Run the real Fastfetch on the new config (if installed) so a bad file is never written."""
    ff = shutil.which("fastfetch")
    if not ff:
        return None
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / ("config" + suffix)
        p.write_text(text, encoding="utf-8")
        try:
            r = subprocess.run([ff, "--config", str(p), "--pipe", "true"], stdout=subprocess.DEVNULL,
                               stderr=subprocess.PIPE, timeout=60)
        except Exception as e:                       # noqa: BLE001
            return f"could not run fastfetch: {e}"
        if r.returncode != 0:
            return (r.stderr.decode(errors="replace").strip() or f"exit code {r.returncode}")
    return None


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Recolour your Fastfetch config with the @@NAME@@ palette.")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    ap.add_argument("--variant", choices=("dark", "light", "auto"), default="auto")
    ap.add_argument("--config", help="recolour this file")
    ap.add_argument("--from", dest="src", help="start from this file instead of the current config")
    ap.add_argument("-q", "--quiet", action="store_true", help="no diff, just a summary")
    ap.add_argument("--if-applied", action="store_true",
                    help="do nothing unless @@NAME@@ colours were applied before (used by `@@COMMAND@@ dark|light`)")
    a = ap.parse_args()
    variant = detect_variant() if a.variant == "auto" else a.variant

    found = Path(a.config).expanduser() if a.config else find_config()
    if a.restore:
        target = found if (found and in_home(found)) else None
        if not target:
            print("No Fastfetch config in your home folder to restore.")
            return 0
        orig = target.with_name(target.name + ".@@COMMAND@@-original")
        created = target.with_name(target.name + ".@@COMMAND@@-created")
        aside = target.with_name(f"{target.name}.@@COMMAND@@-undone-{time.strftime('%Y%m%d-%H%M%S')}")
        if orig.exists():
            shutil.move(str(target), str(aside))
            shutil.move(str(orig), str(target))
            print(f"Restored your original {target}  (the @@NAME@@-coloured one is kept as {aside.name})")
        elif created.exists():
            shutil.move(str(target), str(aside))
            created.unlink()
            print(f"Moved the @@NAME@@-made {target.name} aside to {aside.name}; Fastfetch is back to its default.")
        else:
            print(f"{target} was not changed by @@NAME@@ (no .@@COMMAND@@-original next to it); nothing to restore.")
        return 0

    if a.if_applied:
        if not (found and in_home(found) and any(found.with_name(found.name + x).exists()
                                                 for x in (".@@COMMAND@@-original", ".@@COMMAND@@-created"))):
            return 0

    # what we start from, and where it will be written
    created = False
    if a.src:
        base_path = Path(a.src).expanduser()
        text = base_path.read_text(encoding="utf-8")
        target = found if (found and in_home(found)) else user_dir() / ("config.json5" if base_path.suffix == ".json5" else "config.jsonc")
        origin = f"{base_path} (as you asked)"
        created = not (found and in_home(found))
    elif found and in_home(found):
        text, target, origin = found.read_text(encoding="utf-8"), found, f"your config {found}"
    elif found:
        text = found.read_text(encoding="utf-8")
        target = user_dir() / found.name
        origin = f"the system-wide config {found} (copied to {target}, the system file is not touched)"
        created = True
    else:
        text, origin = default_config_text()
        target = user_dir() / "config.jsonc"
        created = True


    try:
        new, log, notes = recolour(text, variant)
    except ValueError as e:
        print(f"Could not read {origin}: {e}\nNothing was changed.", file=sys.stderr)
        return 1

    print(f"@@NAME@@ Fastfetch colours ({variant}) — {'APPLY' if a.apply else 'PREVIEW (nothing is written; use --apply)'}")
    print(f"  from:  {origin}")
    print(f"  to:    {target}")
    for l in log:
        print(f"  - {l}")
    for n in notes:
        print(f"  note: {n}")
    if new == text and not created:
        print("  Already in @@NAME@@ colours; nothing to do.")
        return 0
    if not a.quiet:
        diff = difflib.unified_diff(text.splitlines(), new.splitlines(), "before", "after", lineterm="", n=1)
        print("\n".join("    " + d for d in diff))

    problem = check_with_fastfetch(new, target.suffix)
    if problem:
        print(f"Fastfetch rejected the recoloured config: {problem}\nNothing was written.", file=sys.stderr)
        return 1
    if not shutil.which("fastfetch"):
        print("  (Fastfetch is not installed yet; the config will be ready when it is.)")

    if not a.apply:
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    orig = target.with_name(target.name + ".@@COMMAND@@-original")
    if target.exists():
        if not orig.exists() and not target.with_name(target.name + ".@@COMMAND@@-created").exists():
            shutil.copy2(target, orig)
        shutil.copy2(target, target.with_name(target.name + ".@@COMMAND@@-previous"))
    elif created:
        target.with_name(target.name + ".@@COMMAND@@-created").write_text(
            "This Fastfetch config was created by @@NAME@@; `--restore` moves it aside.\n", encoding="utf-8")
    tmp = target.with_name(target.name + ".@@COMMAND@@-tmp")
    tmp.write_text(new, encoding="utf-8")
    os.replace(tmp, target)
    print("Written." if a.quiet else f"Written. Undo with:  {sys.argv[0]} --restore")
    return 0


if __name__ == "__main__":
    sys.exit(main())
