"""Minimal, dependency-free PNG encoder used by the batch/QA world renderer.

Pure `struct` + `zlib` — no third-party imports. Promoted from
experiments/spatial_rendering/prototype/png_writer.py (TCK-20260821-WORLD-RENDER-CORE).
"""
from __future__ import annotations

import struct
import zlib


def write_png(path: str, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    """pixels: flat row-major list of (r, g, b) tuples, length width*height."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type 0 (None) per scanline
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw += bytes((r, g, b))

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit depth, color type 2 (RGB)
    idat = zlib.compress(bytes(raw), 9)

    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))
