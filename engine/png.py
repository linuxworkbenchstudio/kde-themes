"""Just enough PNG for the engine: 8-bit greyscale / RGB / RGBA, not interlaced (GTK's assets).

read(data) -> (width, height, rows)   rows: list of lists of (r, g, b, a)
write(width, height, rows) -> bytes   always RGBA, compressed deterministically
"""
import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


def _chunks(data: bytes):
    if data[:8] != SIGNATURE:
        raise ValueError("not a PNG")
    pos = 8
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        yield kind, data[pos + 8:pos + 8 + n]
        pos += 12 + n


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def read(data: bytes):
    idat, head = b"", None
    for kind, body in _chunks(data):
        if kind == b"IHDR":
            head = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
    w, h, depth, ctype, _, _, interlace = head
    if depth != 8 or ctype not in CHANNELS or interlace:
        raise ValueError(f"unsupported PNG (depth {depth}, colour type {ctype}, interlace {interlace})")
    bpp = CHANNELS[ctype]
    raw = zlib.decompress(idat)
    stride = w * bpp
    prev = bytearray(stride)
    rows = []
    for y in range(h):
        f = raw[y * (stride + 1)]
        line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            line[i] = (line[i] + (0, a, b, (a + b) // 2, _paeth(a, b, c))[f]) & 0xFF
        prev = line
        px = []
        for x in range(w):
            p = line[x * bpp:(x + 1) * bpp]
            px.append({1: (p[0], p[0], p[0], 255), 2: (p[0], p[0], p[0], p[1]),
                       3: (p[0], p[1], p[2], 255), 4: tuple(p)}[bpp])
        rows.append(px)
    return w, h, rows


def write(w: int, h: int, rows) -> bytes:
    raw = b"".join(b"\0" + bytes(c for px in row for c in px) for row in rows)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    return (SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def same_pixels(a: bytes, b: bytes) -> bool:
    try:
        return read(a) == read(b)
    except (ValueError, zlib.error, struct.error, TypeError):
        return False
