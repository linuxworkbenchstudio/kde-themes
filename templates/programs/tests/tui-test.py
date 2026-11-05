#!/usr/bin/env python3
"""Drive @@NAME@@ Setup / Settings through a pseudo-terminal like a person would.

  tests/tui-test.py setup-defaults | setup-choices | setup-later | setup-addons | setup-gtk-off | setup-look | setup-narrow | setup-addons-80 | setup-steps-80 | setup-quit
                    | settings-addons-80 | settings-quit-80 | settings-about-80
                    | settings-uninstall | settings-uninstall-no
                    | setup-install | settings-status | settings-addons
Prints the lines to check (ADDONS:/COMMAND:/THEN:, INSTALLED, STATUS-OK, NOTHING); exit status 0
when the app ran cleanly. setup-install really installs into $HOME (use a throw-away home).
"""
import os
import pty
import shutil
import re
import select
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UP, DOWN, RIGHT, LEFT = "\x1bOA", "\x1bOB", "\x1bOC", "\x1bOD"   # keypad (application) mode
PLAIN = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b[()][0-9A-Z]|\x1b[>=]")


def drive(argv, keys, desktop="KDE", cols=100, rows=34, path=None):
    """keys: strings to type, or ("wait", text) to wait until text is on screen."""
    pid, fd = pty.fork()
    if pid == 0:
        env = dict(os.environ, TERM="xterm-256color", ESCDELAY="25", LINES=str(rows), COLUMNS=str(cols),
                   XDG_CURRENT_DESKTOP=desktop)
        if path:
            env["PATH"] = path
        os.chdir(ROOT)
        os.execvpe(argv[0], argv, env)
    out = b""

    def pump(t, until=None):
        nonlocal out
        end = time.time() + t
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                try:
                    out += os.read(fd, 65536)
                except OSError:
                    return
            if until and until in PLAIN.sub("", out.decode("utf-8", "replace")):
                return
    pump(1.5)
    snap = None
    for k in keys:
        if k == "SNAP":            # remember the screen as it is now (screen tests), then go on
            snap = len(out)
            continue
        if isinstance(k, tuple):
            pump(240, until=k[1])
            pump(0.5)
        else:
            os.write(fd, k.encode())
            pump(0.5)
    pump(2.0)
    try:
        _, status = os.waitpid(pid, 0)
    except ChildProcessError:
        status = 0
    if snap is not None:
        return out[:snap].decode("utf-8", "replace"), status
    return out.decode("utf-8", "replace"), status


def no_addons_path():
    """A PATH without the programs @@NAME@@ offers, so every add-on shows as missing."""
    import tempfile
    d = tempfile.mkdtemp(prefix="vh-noaddons-")
    hide = ("dbus-monitor", "kvantummanager", "fastfetch", "qdbus", "yay", "paru", "plasma-", "kreadconfig", "kwriteconfig")
    for src in os.environ.get("PATH", "/usr/bin:/bin").split(":"):
        if not os.path.isdir(src):
            continue
        for n in os.listdir(src):
            if n.startswith(hide) or os.path.exists(os.path.join(d, n)):
                continue
            try:
                os.symlink(os.path.join(src, n), os.path.join(d, n))
            except OSError:
                pass
    return d


def final_screen(out, rows, cols):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import vtscreen
    return vtscreen.screen(out, rows, cols)


def main():
    case = sys.argv[1]
    setup = ["python3", "-I", "bin/@@COMMAND@@-setup", ROOT, "--print-command"]
    addons = ("wait", "Add-ons")
    if case == "setup-defaults":       # Start, Continue, defaults, add-ons as offered, Install
        o, st = drive(setup, ["\r", "\r", "\r", addons, "\r", "\r"])
    elif case == "setup-choices":      # Light, Pills, Fastfetch design, sync off, dim off
        ff = RIGHT if shutil.which("fastfetch") else RIGHT * 2      # recolour (installed) or leave alone > design
        o, st = drive(setup, ["\r", "\r", RIGHT, DOWN, DOWN + RIGHT * 5, DOWN, DOWN + ff, DOWN + RIGHT, DOWN + RIGHT, "\r",
                              addons, "\r", "\r"])
    elif case == "setup-later":        # switch on later, keep my panel
        o, st = drive(setup, ["\r", "\r", LEFT, DOWN + LEFT, "\r", addons, "\r", "\r"])
    elif case == "setup-addons":       # Standard panel look: no Panel Colorizer needed
        o, st = drive(setup, ["\r", "\r", DOWN * 2 + LEFT, "\r", addons, "\r", "\r"])
    elif case == "setup-gtk-off":      # GTK apps: Leave alone (the last row)
        o, st = drive(setup, ["\r", "\r", DOWN * 7 + RIGHT, "\r", addons, "\r", "\r"])
    elif case == "setup-look":         # each panel look by name: Invisible
        o, st = drive(setup, ["\r", "\r", DOWN * 2 + RIGHT * 3, "\r", addons, "\r", "\r"])
    elif case == "setup-narrow":       # a 72-column terminal: the look row shows "‹ Pills ›  6 of 7"
        o, st = drive(setup, ["\r", "\r", DOWN * 2 + RIGHT * 5, "q", "q", "q"], cols=72)
        plain = PLAIN.sub("", o)
        # curses redraws only what changed, so check the counter and the Pills hint, not "6 of 7" whole
        print("NARROW-OK" if " of 7" in plain and "pill with fully rounded ends" in plain else plain[-800:])
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "setup-addons-80":   # 80 x 24, every add-on listed: rows, Continue, help and keys apart
        o, st = drive(setup, ["\r", "\r", DOWN * 4 + RIGHT * 2, "\r", addons, DOWN * 2, "SNAP", "q", "q", "q", "q"],
                      cols=80, rows=24, path=no_addons_path())
        sc = final_screen(o, 24, 80)
        labels = ["Kvantum", "Plasma GTK settings", "qdbus", "dbus-monitor", "KVitals", "Panel Colorizer", "Fastfetch", "Papirus icons"]
        rowof = {l: next((i for i, r in enumerate(sc) if r[4:6].strip() in "✘✔" and r[6:].startswith(l)), -1) for l in labels}
        cont = next((i for i, r in enumerate(sc) if r.strip() == "Continue"), -1)
        keys = next((i for i, r in enumerate(sc) if r.strip().startswith("↑↓ move")), -1)
        help_rows = [r for r in sc[cont + 1:keys] if r.strip()]
        ok = (all(v >= 0 for v in rowof.values()) and max(rowof.values()) < cont < keys == 22 and help_rows
              and not any(r.rstrip().endswith("-") for r in sc) and all(len(r) <= 79 for r in sc))
        print("ADDONS80-OK" if ok else "\n".join(sc) + f"\nrows={rowof} continue={cont} keys={keys}")
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "settings-addons-80":  # 80 x 24, every add-on missing: every row shows, the "why" below
        o, st = drive(["python3", "-I", "bin/@@COMMAND@@-settings"], [DOWN * 3 + "\r", "SNAP", "q", "q"], cols=80, rows=24,
                      path=no_addons_path())
        sc = final_screen(o, 24, 80)
        labels = ["Kvantum", "qdbus", "dbus-monitor", "KVitals", "Panel Colorizer", "Fastfetch", "Plasma GTK settings", "Papirus icons", "Back"]
        rows_ = [next((i for i, r in enumerate(sc) if r.strip().lstrip("✘✔ ").startswith(l) and "missing" in r or r.strip() == l), -1) for l in labels]
        keys = next((i for i, r in enumerate(sc) if r.strip().startswith("↑↓ move")), -1)
        ok = all(0 <= y < keys - 1 for y in rows_) and keys == 22 and "missing - the @@NAME@@ app style" in sc[keys - 1] \
            and all(len(r) <= 79 for r in sc)
        print("SADDONS80-OK" if ok else "\n".join(sc) + f"\nrows={rows_} keys={keys}")
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "setup-steps-80":    # every step name fits at 80 columns
        o, st = drive(setup, ["\r", "SNAP", "q", "q", "q"], cols=80, rows=24)
        sc = final_screen(o, 24, 80)
        line = next((r for r in sc if "Welcome" in r and "System" in r), "")
        print("STEPS80-OK" if all(n in line for n in ("Welcome", "System", "Choices", "Add-ons", "Review", "Install", "Done"))
              else "\n".join(sc))
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "settings-quit-80":  # 80 x 24: open, go into a page and back, quit - no Python/curses error
        o, st = drive(["python3", "-I", "bin/@@COMMAND@@-settings"], [DOWN * 3 + "\r", "q", "q"], cols=80, rows=24)
        print("SQUIT80-OK" if "Traceback" not in o and "_curses.error" not in o and os.WEXITSTATUS(st) == 0 else o[-600:])
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "settings-about-80":  # About at 80 x 24: version, edition, GTK theme, installed, Uninstall
        o, st = drive(["python3", "-I", "bin/@@COMMAND@@-settings"], [UP * 2 + "\r", "SNAP", "q", "q"], cols=80, rows=24)
        sc = final_screen(o, 24, 80)
        keys = next((i for i, r in enumerate(sc) if r.strip().startswith("↑↓ move")), -1)
        want = ["Version", "Edition", "GTK apps", "Installed", "Uninstall @@NAME@@", "Back"]
        at = [next((i for i, r in enumerate(sc) if r.strip().startswith(w)), -1) for w in want]
        ok = keys == 22 and all(0 <= y < keys for y in at) and all(len(r) <= 79 for r in sc) and "Traceback" not in o
        print("ABOUT80-OK" if ok else "\n".join(sc) + f"\nat={at} keys={keys}")
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "settings-uninstall-no":   # About > Uninstall > No: back on About, nothing changed
        o, st = drive(["python3", "-I", "bin/@@COMMAND@@-settings"], [UP * 2 + "\r", "\r", "\r", "SNAP", "q", "q"],
                      cols=80, rows=24)
        sc = final_screen(o, 24, 80)
        print("NO-OK" if any("Uninstall @@NAME@@" in r for r in sc) and "Traceback" not in o else "\n".join(sc))
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "settings-uninstall":      # About > Uninstall > Yes: runs it, closes with the message
        o, st = drive(["python3", "-I", "bin/@@COMMAND@@-settings"],
                      [UP * 2 + "\r", "\r", DOWN + "\r", ("wait", "Settings has closed")], cols=80, rows=24)
        plain = PLAIN.sub("", o)
        clean = "Traceback" not in o and "_curses.error" not in o and os.WIFEXITED(st) and os.WEXITSTATUS(st) == 0
        print("UNINSTALLED-OK" if clean and "@@NAME@@ is uninstalled. @@NAME@@ Settings has closed." in plain
              else plain[-1500:] + f"\nstatus={st}")
        sys.exit(0)
    elif case == "setup-quit":
        o, st = drive(setup, ["q"])
    elif case == "setup-install":      # the real thing (stubbed Plasma), then Close
        o, st = drive(setup[:-1], ["\r", "\r", "\r", addons, "\r", "\r", ("wait", "Full log"), UP, "\r"])
        plain = PLAIN.sub("", o)
        print("INSTALLED" if "@@NAME@@ is installed" in plain else plain[-1500:])
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "settings-status":    # open Status, go back, quit
        o, st = drive(["python3", "-I", "bin/@@COMMAND@@-settings"], [DOWN * 4 + "\r", "x", "q"])
        plain = PLAIN.sub("", o)
        print("STATUS-OK" if "Installed" in plain and "Edition" in plain else plain[-400:])
        sys.exit(1 if "Traceback" in o else 0)
    elif case == "settings-addons":    # open Add-ons, back, quit
        o, st = drive(["python3", "-I", "bin/@@COMMAND@@-settings"], [DOWN * 3 + "\r", "q", "q"])
        plain = PLAIN.sub("", o)
        print("ADDONS-OK" if "Panel Colorizer" in plain and "Kvantum" in plain and "Papirus" in plain else plain[-400:])
        sys.exit(1 if "Traceback" in o else 0)
    else:
        sys.exit("unknown case")
    lines = [m.group(0).strip() for m in (re.search(r"(ADDONS|COMMAND|THEN): .*", PLAIN.sub("", l)) for l in o.splitlines()) if m]
    print("\n".join(lines) if lines else ("NOTHING" if "Nothing was changed" in o else PLAIN.sub("", o)[-600:]))
    sys.exit(1 if "Traceback" in o else 0)


if __name__ == "__main__":
    main()
