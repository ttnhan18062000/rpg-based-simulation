"""The masks' own sheet at 8x: rows edge / outer_corner / inner_corner, columns v1 v2 v3; opaque = white on a dark cell with a 4 px depth guide. Pure Python PNG writer. Usage: python mask_sheet.py <out.png>"""
import struct, sys, zlib
from pathlib import Path
from tests.visual_assets.test_border_masks import KINDS, VARIANTS, committed_masks, SIZE

Z, GAP, BG, CELL, FILL, GUIDE = 8, 8, (17, 24, 39), (40, 48, 66), (255, 255, 255), (90, 60, 60)
masks = committed_masks()
W = len(VARIANTS) * (SIZE * Z + GAP) + GAP
H = len(KINDS) * (SIZE * Z + GAP) + GAP
img = [[BG] * W for _ in range(H)]
for r, kind in enumerate(KINDS):
    for c, variant in enumerate(VARIANTS):
        ox, oy = GAP + c * (SIZE * Z + GAP), GAP + r * (SIZE * Z + GAP)
        for y in range(SIZE * Z):
            for x in range(SIZE * Z):
                px, py = x // Z, y // Z
                colour = FILL if (px, py) in masks[(kind, variant)] else (GUIDE if (py == 4 and px < 16) or (px == 11 and py < 4) else CELL)
                img[oy + y][ox + x] = colour
raw = b"".join(b"\x00" + bytes(ch for p in row for ch in p) for row in img)
chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
Path(sys.argv[1]).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
