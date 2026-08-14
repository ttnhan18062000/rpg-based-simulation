"""Prototype: numpy-vectorized background rasterization vs. the pure-Python nested-loop
version in render_world.py — testing whether a heavier drawing-tool dependency is worth it.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from render_world import terrain_color, DEFAULT_TERRAIN_COLOR  # noqa: E402
from png_writer import write_png  # noqa: E402


def render_numpy(state, out_path: str, scale: int = 3) -> float:
    terrain = state.terrain
    xs = [p[0] for p in terrain.keys()]
    ys = [p[1] for p in terrain.keys()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    grid_w, grid_h = max_x - min_x + 1, max_y - min_y + 1

    t0 = time.perf_counter()

    # Build the low-res grid as a numpy uint8 array (H, W, 3), default-filled.
    grid = np.full((grid_h, grid_w, 3), DEFAULT_TERRAIN_COLOR, dtype=np.uint8)
    for (tx, ty), tval in terrain.items():
        gx, gy = tx - min_x, ty - min_y
        grid[gy, gx] = terrain_color(tval)

    # Vectorized upscale: repeat each pixel scale x scale — no Python-level pixel loop.
    upscaled = np.repeat(np.repeat(grid, scale, axis=0), scale, axis=1)

    raster_ms = (time.perf_counter() - t0) * 1000

    height, width = upscaled.shape[:2]
    flat_pixels = [tuple(p) for p in upscaled.reshape(-1, 3)]
    write_png(out_path, width, height, flat_pixels)
    return raster_ms


def main() -> None:
    world_id = sys.argv[1] if len(sys.argv) > 1 else "wilderness_survival"
    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, report = WorldCompiler.compile(spec, seed=42)
    print(f"Compiled {world_id}: terrain_tiles={len(state.terrain)}")

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    ms = render_numpy(state, str(out_dir / f"{world_id}_numpy.png"))
    print(f"numpy raster-only time: {ms:.2f}ms (background build + vectorized upscale, excludes PNG write and the still-Python per-tile terrain dict loop)")


if __name__ == "__main__":
    main()
