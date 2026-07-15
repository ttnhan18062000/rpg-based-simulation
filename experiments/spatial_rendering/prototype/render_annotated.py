"""Prototype: an agent-oriented annotated variant — coordinate gridlines + axis tick labels
burned into the image — vs. the plain human-oriented render, to test whether the two review
modes genuinely need different image treatments (not just assert it).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from png_writer import write_png  # noqa: E402
from render_world import terrain_color, DEFAULT_TERRAIN_COLOR  # noqa: E402

# Minimal 3x5 bitmap digits — just enough for axis coordinate labels.
DIGITS: dict[str, list[str]] = {
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
}


def draw_text(pixels: list, width: int, height: int, x0: int, y0: int, text: str, color: tuple) -> None:
    cx = x0
    for ch in text:
        glyph = DIGITS.get(ch)
        if glyph is None:
            cx += 4
            continue
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    px, py = cx + gx, y0 + gy
                    if 0 <= px < width and 0 <= py < height:
                        pixels[py * width + px] = color
        cx += 4


def render_annotated(state, out_path: str, scale: int = 6, grid_every: int = 10) -> None:
    terrain = state.terrain
    all_positions = list(terrain.keys())
    for ent in state.entities.values():
        if getattr(ent.lifecycle, "active", True):
            x, y = ent.navigation.position
            all_positions.append((int(x), int(y)))

    xs = [p[0] for p in all_positions]
    ys = [p[1] for p in all_positions]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    grid_w, grid_h = max_x - min_x + 1, max_y - min_y + 1
    margin = 20  # room for axis labels
    width, height = grid_w * scale + margin, grid_h * scale + margin

    out_pixels = [(20, 20, 20)] * (width * height)
    for (tx, ty), tval in terrain.items():
        gx, gy = tx - min_x, ty - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            c = terrain_color(tval)
            for sy in range(scale):
                for sx in range(scale):
                    px, py = margin + gx * scale + sx, margin + gy * scale + sy
                    out_pixels[py * width + px] = c

    for ent in state.entities.values():
        if not getattr(ent.lifecycle, "active", True):
            continue
        x, y = ent.navigation.position
        gx, gy = int(x) - min_x, int(y) - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            for sy in range(scale):
                for sx in range(scale):
                    px, py = margin + gx * scale + sx, margin + gy * scale + sy
                    out_pixels[py * width + px] = (0x4A, 0x9E, 0xFF)

    GRID_LINE = (255, 255, 255)
    for gx in range(0, grid_w, grid_every):
        px = margin + gx * scale
        for py in range(margin, height):
            out_pixels[py * width + px] = GRID_LINE
        draw_text(out_pixels, width, height, px + 1, 2, str(min_x + gx), GRID_LINE)
    for gy in range(0, grid_h, grid_every):
        py = margin + gy * scale
        for px in range(margin, width):
            out_pixels[py * width + px] = GRID_LINE
        draw_text(out_pixels, width, height, 2, py + 1, str(min_y + gy), GRID_LINE)

    write_png(out_path, width, height, out_pixels)


if __name__ == "__main__":
    world_id = sys.argv[1] if len(sys.argv) > 1 else "dungeon_crawl"
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, report = WorldCompiler.compile(spec, seed=42)
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{world_id}_annotated.png"
    render_annotated(state, str(out_path))
    print(f"Wrote {out_path}")
