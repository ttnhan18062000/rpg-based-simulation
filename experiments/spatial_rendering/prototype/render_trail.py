"""Prototype: track one entity's position across many ticks, render as a breadcrumb trail
on a single frame — the concrete "screenshot tracking" ask from the proposal's origin.

Run from repo root: .venv/bin/python3 experiments/spatial_rendering/prototype/render_trail.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.platform.rng import DeterministicRNG
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from png_writer import write_png  # noqa: E402
from render_world import terrain_color, DEFAULT_TERRAIN_COLOR, BLOCKED_OUTLINE  # noqa: E402


def main() -> None:
    world_id = sys.argv[1] if len(sys.argv) > 1 else "sandbox_world"
    total_ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    sample_every = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    scale = 6

    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, compile_report = WorldCompiler.compile(spec, seed=42)
    print(f"Compiled {world_id}: entities={compile_report['entity_count']}")

    tracked_id = next(iter(state.entities.keys()))
    print(f"Tracking entity_id={tracked_id}")

    profile = RuntimeProfile(
        name="TRAIL_PROTO", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024, max_cpu_percent=90.0, max_worker_count=0,
        max_tick_budget_ms=50.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0,
    )
    rng = DeterministicRNG(42)
    kernel = Kernel(profile=profile, state=state, rng=rng, world_id=world_id)

    trail: list[tuple[int, int, int]] = []  # (tick, x, y)
    for t in range(total_ticks):
        kernel.tick_once()
        if t % sample_every == 0:
            ent = kernel._state.entities.get(tracked_id)
            if ent is not None and ent.lifecycle.active:
                x, y = ent.navigation.position
                trail.append((t, int(x), int(y)))

    print(f"Trail samples: {trail}")

    final_state = kernel._state
    terrain = final_state.terrain
    all_positions = list(terrain.keys()) + [(x, y) for _, x, y in trail]
    xs = [p[0] for p in all_positions]
    ys = [p[1] for p in all_positions]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    grid_w, grid_h = max_x - min_x + 1, max_y - min_y + 1
    width, height = grid_w * scale, grid_h * scale

    pixels = [DEFAULT_TERRAIN_COLOR] * (grid_w * grid_h)
    for (tx, ty), tval in terrain.items():
        gx, gy = tx - min_x, ty - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            pixels[gy * grid_w + gx] = terrain_color(tval)

    out_pixels = [DEFAULT_TERRAIN_COLOR] * (width * height)
    for gy in range(grid_h):
        for gx in range(grid_w):
            c = pixels[gy * grid_w + gx]
            for sy in range(scale):
                for sx in range(scale):
                    out_pixels[(gy * scale + sy) * width + (gx * scale + sx)] = c

    # Trail: older = dimmer, newest = brightest yellow, drawn as scale x scale blocks
    # with a thin connecting line between consecutive samples for readability.
    n = len(trail)
    for i, (_tick, x, y) in enumerate(trail):
        gx, gy = x - min_x, y - min_y
        brightness = 0.3 + 0.7 * (i / max(1, n - 1))
        color = (int(255 * brightness), int(255 * brightness), int(40 * brightness))
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            for sy in range(scale):
                for sx in range(scale):
                    out_pixels[(gy * scale + sy) * width + (gx * scale + sx)] = color
        if i > 0:
            _, px, py = trail[i - 1]
            pgx, pgy = px - min_x, py - min_y
            steps = max(abs(gx - pgx), abs(gy - pgy), 1)
            for s in range(steps + 1):
                lx = int(pgx + (gx - pgx) * s / steps)
                ly = int(pgy + (gy - pgy) * s / steps)
                if 0 <= lx < grid_w and 0 <= ly < grid_h:
                    cx = lx * scale + scale // 2
                    cy = ly * scale + scale // 2
                    if 0 <= cx < width and 0 <= cy < height:
                        out_pixels[cy * width + cx] = (200, 200, 60)

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{world_id}_trail_e{tracked_id}.png"
    write_png(str(out_path), width, height, out_pixels)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
