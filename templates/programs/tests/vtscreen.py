"""A tiny terminal emulator for the screen tests: the escape codes curses sends -> the final
screen as text rows (enough for @@NAME@@ Setup and Settings)."""
import re


def screen(data, rows=24, cols=80):
    grid = [[(" ", None, None, False) for _ in range(cols)] for _ in range(rows)]
    y = x = 0; cf = cb = None; bold = False
    top, bot = 0, rows - 1
    blank = lambda: [(" ", None, None, False) for _ in range(cols)]
    i = 0; n = len(data)
    while i < n:
        c = data[i]
        if c == "\x1b":
            m = re.match(r"\x1b\[([?>]?)([0-9;]*)([@A-Za-z])", data[i:])
            if m:
                priv, args, cmd = m.groups(); a = [int(v) if v else 0 for v in args.split(";")] if args else []
                g = lambda k, d=1: (a[k] if len(a) > k and a[k] else d)
                if not priv:
                    if cmd == "H": y, x = g(0) - 1, g(1) - 1
                    elif cmd == "d": y = g(0) - 1
                    elif cmd == "G": x = g(0) - 1
                    elif cmd == "A": y -= g(0)
                    elif cmd == "B": y += g(0)
                    elif cmd == "C": x += g(0)
                    elif cmd == "D": x -= g(0)
                    elif cmd == "K":
                        m_ = g(0, 0)
                        rng = range(x, cols) if m_ == 0 else range(0, x + 1) if m_ == 1 else range(cols)
                        for xx in rng: grid[y][xx] = (" ", None, cb, False)
                    elif cmd == "r":
                        top, bot = (g(0) - 1, g(1, rows) - 1) if a else (0, rows - 1); y = x = 0
                    elif cmd == "L":
                        for _ in range(g(0)):
                            if top <= y <= bot: grid.insert(y, blank()); del grid[bot + 1]
                    elif cmd == "M":
                        for _ in range(g(0)):
                            if top <= y <= bot: del grid[y]; grid.insert(bot, blank())
                    elif cmd == "S":
                        for _ in range(g(0)): del grid[top]; grid.insert(bot, blank())
                    elif cmd == "T":
                        for _ in range(g(0)): del grid[bot]; grid.insert(top, blank())
                    elif cmd == "P":
                        k_ = g(0); row = grid[y]
                        grid[y] = row[:x] + row[x + k_:] + [(" ", None, None, False)] * k_
                    elif cmd == "X":
                        for xx in range(x, min(cols, x + g(0))): grid[y][xx] = (" ", None, cb, False)
                    elif cmd == "J" and g(0, 0) == 2:
                        grid = [[(" ", None, None, False) for _ in range(cols)] for _ in range(rows)]
                    elif cmd == "J" and g(0, 0) == 0:
                        for yy in range(y, rows):
                            for xx in range(x if yy == y else 0, cols): grid[yy][xx] = (" ", None, None, False)
                    elif cmd == "m":
                        a = a or [0]; k = 0
                        while k < len(a):
                            v = a[k]
                            if v == 0: cf = cb = None; bold = False
                            elif v == 1: bold = True
                            elif v == 39: cf = None
                            elif v == 49: cb = None
                            elif v == 38 and k + 2 < len(a) and a[k+1] == 5: cf = a[k+2]; k += 2
                            elif v == 48 and k + 2 < len(a) and a[k+1] == 5: cb = a[k+2]; k += 2
                            k += 1
                i += m.end(); continue
            if data[i:i+2] == "\x1bM":
                if y == top: del grid[bot]; grid.insert(top, blank())
                else: y -= 1
                i += 2; continue
            m = re.match(r"\x1b[()][0-9A-Z]|\x1b[>=78]|\x1b\][^\x07]*\x07", data[i:])
            i += m.end() if m else 1; continue
        if c == "\r": x = 0
        elif c == "\n":
            if y == bot: del grid[top]; grid.insert(bot, blank())
            else: y += 1
        elif c == "\b": x = max(0, x - 1)
        elif c >= " ":
            if 0 <= y < rows and 0 <= x < cols: grid[y][x] = (c, cf, cb, bold)
            x += 1
        i += 1
    return ["".join(ch for ch, *_ in row).rstrip() for row in grid]
