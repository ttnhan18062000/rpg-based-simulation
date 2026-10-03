"""Colour parsing, formatting and small colour maths shared by the schema and the technique modules."""

from __future__ import annotations

import re

from visual_assets.drawing.errors import AdapterError

_HEX = re.compile(r"^#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?$")


def hex_to_rgba(value: str) -> tuple[int, int, int, int]:
    m = _HEX.fullmatch(value) if isinstance(value, str) else None
    if not m:
        raise AdapterError("color must be #rrggbb or #rrggbbaa")
    rgb, a = m.group(1), m.group(2) or "ff"
    return (int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16), int(a, 16))


def rgba_to_hex(r: int, g: int, b: int, a: int = 255) -> str:
    base = f"#{r:02x}{g:02x}{b:02x}"
    return base if a == 255 else base + f"{a:02x}"


def norm_hex(value: str) -> str:
    """Canonical 8-digit lowercase form, as Aseprite readback reports it."""
    return rgba_to_hex(*hex_to_rgba(value)).ljust(9, "f") if len(value) == 7 else value.lower()


def luma(rgb) -> float:
    """Rec.709 luma on 0..255 sRGB values (perceptual enough for value-separation checks)."""
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def hue_toward(h: float, target: float, amount: float) -> float:
    """Move hue `h` (degrees) toward `target` along the shortest arc by at most `amount` degrees."""
    delta = (target - h + 180.0) % 360.0 - 180.0
    step = max(-amount, min(amount, delta))
    return (h + step) % 360.0
