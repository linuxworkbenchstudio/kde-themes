"""Colour values: #RRGGBB strings in, the formats KDE and Konsole want out."""
import re

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def is_hex(value) -> bool:
    return isinstance(value, str) and bool(HEX.match(value))


def rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def to_hex(r: int, g: int, b: int) -> str:
    return "#%02X%02X%02X" % (r, g, b)


def csv(value: str) -> str:
    """#1C222A -> 28,34,42 (KDE colour schemes and Konsole)."""
    return "%d,%d,%d" % rgb(value)


def mix(a: str, b: str, amount: float) -> str:
    """amount of a over b (0..1), rounded half up per channel."""
    ca, cb = rgb(a), rgb(b)
    return to_hex(*(int(x * amount + y * (1 - amount) + 0.5) for x, y in zip(ca, cb)))


def luminance(value: str) -> float:
    """Relative luminance (WCAG), 0..1."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(value)
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two colours, 1..21."""
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
