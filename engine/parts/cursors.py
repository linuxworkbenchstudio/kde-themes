"""Cursors: share/icons/<name>/ (cursors/<name>/ in the release) - Waypoint's recoloured Breeze cursors, recoloured again per pack.

Xcursor images are premultiplied ARGB: every pixel is taken as the nearest blend of two colours
of the pack's cursor map and rebuilt from their targets (Vice Horizon's method). Aliases are
written both as links and as aliases.txt, which the installer turns back into links.
"""
import re
import struct

from ..files import Link
from ..pack import Edition, Pack
from ..recolour import resolver
from . import TEMPLATES

HEX = re.compile(r"#([0-9a-fA-F]{6})(?![0-9a-fA-F])")


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def xcursor_recolour(data: bytes, cmap: dict) -> bytes:
    import numpy as np
    src = np.array([_rgb(k) for k in cmap], dtype=np.float64)
    dstc = np.array([_rgb(v) for v in cmap.values()], dtype=np.float64)
    buf = bytearray(data)
    ntoc = struct.unpack_from("<I", buf, 12)[0]
    for i in range(ntoc):
        t, _sub, pos = struct.unpack_from("<III", buf, 16 + 12 * i)
        if t != 0xFFFD0002:
            continue
        w, h = struct.unpack_from("<II", buf, pos + 16)
        off = pos + 36
        px = np.frombuffer(bytes(buf[off:off + 4 * w * h]), dtype="<u4").copy()
        a = ((px >> 24) & 0xFF).astype(np.float64)
        rgbp = np.stack([(px >> 16) & 0xFF, (px >> 8) & 0xFF, px & 0xFF], axis=1).astype(np.float64)
        nz = a > 0
        rgb = np.zeros_like(rgbp)
        rgb[nz] = np.clip(rgbp[nz] * 255.0 / a[nz, None], 0, 255)
        best_err = np.full(len(px), np.inf)
        out = rgb.copy()
        k = len(src)
        for p in range(k):
            for q in range(k):
                d = src[q] - src[p]
                dd = (d * d).sum()
                tt = np.zeros(len(px)) if dd == 0 else np.clip(((rgb - src[p]) @ d) / dd, 0, 1)
                approx = src[p] + tt[:, None] * d
                err = ((rgb - approx) ** 2).sum(axis=1)
                better = err < best_err
                best_err[better] = err[better]
                out[better] = dstc[p] + tt[better, None] * (dstc[q] - dstc[p])
        keep = best_err > 30 ** 2           # far from any blend (status colours): unchanged
        out[keep] = rgb[keep]
        prem = np.clip(np.rint(out * a[:, None] / 255.0), 0, 255).astype(np.uint32)
        newpx = (px & 0xFF000000) | (prem[:, 0] << 16) | (prem[:, 1] << 8) | prem[:, 2]
        buf[off:off + 4 * w * h] = newpx.astype("<u4").tobytes()
    return bytes(buf)


def build_edition(pack: Pack, ed: Edition) -> dict:
    name = pack.file_name("cursors", ed)
    resolve = resolver(pack, ed)
    spec = (ed.raw.get("recolour") or {}).get("cursors", {})
    cmap = {k.lower(): resolve(v) for k, v in spec.items()}     # ordered: the blend pairs follow it
    src = TEMPLATES / "cursors" / ed.template
    base = f"cursors/{name}/"
    out = {}
    for f in sorted(p for p in src.rglob("*") if p.is_file() and p.name != "LINKS"):
        rel = f.relative_to(src).as_posix()
        data = f.read_bytes()
        if cmap and rel.startswith("cursors/"):
            data = xcursor_recolour(data, cmap)
        elif cmap and f.suffix == ".svg":
            data = HEX.sub(lambda m: cmap.get("#" + m.group(1).lower(), m.group(0)), data.decode()).encode()
        out[base + rel] = data
    aliases = []
    links = src / "LINKS"
    for line in (links.read_text().splitlines() if links.is_file() else []):
        rel, target = line.split("\t")
        out[base + rel] = Link(target)
        if rel.startswith("cursors/") and "/" not in rel[len("cursors/"):]:
            aliases.append(f"{rel[len('cursors/'):]} {target}")
    out[base + "aliases.txt"] = ("# alias target   (install.sh recreates these as symlinks inside cursors/)\n"
                                 + "\n".join(aliases) + "\n")
    out[base + "index.theme"] = (f"[Icon Theme]\nName={pack.name} Cursors {ed.name}\n"
                                 f"Comment={pack.describe('cursors', ed)}\nInherits=breeze_cursors\n")
    return out


def build(pack: Pack) -> dict:
    out = {}
    for ed in pack.editions.values():
        out.update(build_edition(pack, ed))
    return out
