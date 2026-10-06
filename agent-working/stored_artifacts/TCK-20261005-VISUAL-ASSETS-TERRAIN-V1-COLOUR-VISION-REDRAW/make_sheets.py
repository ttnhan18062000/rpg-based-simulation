"""Evidence sheets for the re-tint: before/after (old and new tile side by side, 4x) and the new 2 x 2 repeat sheet (4x). Pure Python PNG writer.
Usage: python make_sheets.py <dir with the old previews named <visual key>.png> <out dir>"""
import struct, sys, zlib
from pathlib import Path
from tests.visual_assets import set_colour_vision as sv

def png(path, w, h, rows):
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in rows)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))

def px(t): return [tuple(round(c * 255) for c in p) for p in t]

old_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
new = {k: px(t) for k, t in sv.draft_tiles("terrain-v1").items()}
old = {k: px(sv.tile_from_preview((old_dir / f"{k}.png").read_bytes())) for k in new}
keys = sorted(new)
Z, GAP, COLS, BG = 4, 6, 4, (17, 24, 39)

def sheet(cell_w, cell_h, draw, name):
    rows_n = -(-len(keys) // COLS)
    W, H = COLS * (cell_w + GAP) + GAP, rows_n * (cell_h + GAP) + GAP
    img = [[BG] * W for _ in range(H)]
    for i, k in enumerate(keys):
        ox, oy = GAP + (i % COLS) * (cell_w + GAP), GAP + (i // COLS) * (cell_h + GAP)
        for y, row in enumerate(draw(k)):
            img[oy + y][ox:ox + len(row)] = row
    png(out / name, W, H, img)

def scaled(t, rep=1):
    n = 16 * rep
    return [[t[((y % 16) * 16) + (x % 16)] for x in range(n) for _ in range(Z)] for y in range(n) for _ in range(Z)]

def ba(k):
    a, b = scaled(old[k]), scaled(new[k])
    return [ra + [(255, 255, 255)] * 2 + rb for ra, rb in zip(a, b)]

sheet(2 * 16 * Z + 2, 16 * Z, ba, "before_after_sheet.png")
sheet(32 * Z, 32 * Z, lambda k: scaled(new[k], 2), "repeat_sheet_after.png")
print("order (row-major, 4 per row):", keys)
