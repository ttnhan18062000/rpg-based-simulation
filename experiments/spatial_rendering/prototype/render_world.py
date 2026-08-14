"""Prototype: compile a real world, run it, render a real PNG frame from AuthoritativeState.

Run from repo root: .venv/bin/python3 experiments/spatial_rendering/prototype/render_world.py

Not production code — validates the rendering proposal's technical assumptions:
- terrain vocabulary, coordinate system, sparse-dict handling
- pure-Python PNG output (no new dependency)
- what a real compiled+ticked world actually looks like spatially
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

# Ported aesthetic from frontend/src/constants/colors.ts, re-keyed by the REAL string
# vocabulary found by actually compiling and inspecting real worlds (sandbox_world,
# dungeon_crawl) — NOT the vocabulary a static grep of src/ predicted. Real compiled
# data contains a confirmed casing bug: 'PLAIN' and 'plain' coexist as distinct dict
# keys in the same world (961 lowercase + 6593 uppercase instances in sandbox_world).
# Lookup below normalizes to uppercase specifically to route around this, but the bug
# itself is a real finding, not something to silently paper over — see PROPOSAL.md.
TERRAIN_COLORS: dict[str, tuple[int, int, int]] = {
    "WALL": (0x55, 0x5B, 0x73),
    "PLAIN": (0x4A, 0x60, 0x30),
    "FOREST": (0x1B, 0x3A, 0x1B),
    "CAVE": (0x3A, 0x30, 0x40),
    "RUIN": (0x4A, 0x40, 0x35),
    "GRASS": (0x7A, 0xA0, 0x50),  # confirmed never emitted by any world tested (§5d) — kept as a defensive entry, given a distinct color rather than left colliding with PLAIN
    "DESERT": (0x3A, 0x34, 0x20),
    "SWAMP": (0x2A, 0x2A, 0x3A),
    "MOUNTAIN": (0x3A, 0x3A, 0x3A),
    "RIVER": (0x2E, 0x5C, 0x8A),  # confirmed real, live terrain type (highland_traverse) — was entirely missing, the opposite bug from GRASS: real value with no color, not a fake value colliding with one
    "ROAD": (0x5A, 0x50, 0x40),
    "SNOW": (0xC8, 0xD8, 0xE8),
    "TOWN": (0x2D, 0x4A, 0x3E),
    "VOLCANIC": (0x5A, 0x2A, 0x1A),
    "FLOOR": (0x1A, 0x1D, 0x27),
}
DEFAULT_TERRAIN_COLOR = (0xFF, 0x00, 0xFF)  # loud magenta — unknown terrain must be obvious, never silently blend in


def terrain_color(raw_value: str) -> tuple[int, int, int]:
    return TERRAIN_COLORS.get(raw_value.upper(), DEFAULT_TERRAIN_COLOR)
BUILDING_COLOR = (0xC0, 0x80, 0x40)
ENTITY_COLOR_ALIVE = (0x4A, 0x9E, 0xFF)
ENTITY_COLOR_DEAD = (0x60, 0x30, 0x30)
BLOCKED_OUTLINE = (0xFF, 0x50, 0x50)


def render(state, out_path: str, scale: int = 6) -> dict:
    """Renders state to a PNG. Returns stats dict for reporting."""
    terrain = state.terrain
    building_tiles = getattr(state, "building_tiles", {})
    blocked_tiles = getattr(state, "blocked_tiles", set())

    all_positions = list(terrain.keys())
    entity_positions = []
    for ent in state.entities.values():
        if not getattr(ent.lifecycle, "active", True):
            continue
        x, y = ent.navigation.position
        entity_positions.append((int(x), int(y), ent.combat.alive))
        all_positions.append((int(x), int(y)))

    if not all_positions:
        raise RuntimeError("No terrain or entity positions found — nothing to render")

    xs = [p[0] for p in all_positions]
    ys = [p[1] for p in all_positions]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = (max_x - min_x + 1) * scale
    height = (max_y - min_y + 1) * scale

    grid_w = max_x - min_x + 1
    grid_h = max_y - min_y + 1
    pixels = [DEFAULT_TERRAIN_COLOR] * (grid_w * grid_h)

    terrain_histogram: dict[str, int] = {}
    for (tx, ty), tval in terrain.items():
        gx, gy = tx - min_x, ty - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            pixels[gy * grid_w + gx] = terrain_color(tval)
        terrain_histogram[tval] = terrain_histogram.get(tval, 0) + 1

    for (bx, by), _btype in building_tiles.items():
        gx, gy = bx - min_x, by - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            pixels[gy * grid_w + gx] = BUILDING_COLOR

    # Upscale to `scale`x for visibility, then overlay entities as filled scale x scale blocks.
    out_pixels = [DEFAULT_TERRAIN_COLOR] * (width * height)
    for gy in range(grid_h):
        for gx in range(grid_w):
            c = pixels[gy * grid_w + gx]
            for sy in range(scale):
                for sx in range(scale):
                    out_pixels[(gy * scale + sy) * width + (gx * scale + sx)] = c

    blocked_count_rendered = 0
    for (bx, by) in blocked_tiles:
        gx, gy = bx - min_x, by - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            blocked_count_rendered += 1
            for sx in range(scale):
                out_pixels[(gy * scale) * width + (gx * scale + sx)] = BLOCKED_OUTLINE
                out_pixels[(gy * scale + scale - 1) * width + (gx * scale + sx)] = BLOCKED_OUTLINE

    for ex, ey, alive in entity_positions:
        gx, gy = ex - min_x, ey - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            color = ENTITY_COLOR_ALIVE if alive else ENTITY_COLOR_DEAD
            for sy in range(scale):
                for sx in range(scale):
                    out_pixels[(gy * scale + sy) * width + (gx * scale + sx)] = color

    write_png(out_path, width, height, out_pixels)

    return {
        "width_px": width,
        "height_px": height,
        "grid_w": grid_w,
        "grid_h": grid_h,
        "terrain_tile_count": len(terrain),
        "terrain_histogram": terrain_histogram,
        "building_tile_count": len(building_tiles),
        "blocked_tile_count": len(blocked_tiles),
        "blocked_tiles_within_bounds": blocked_count_rendered,
        "entity_count": len(entity_positions),
        "bounds": (min_x, min_y, max_x, max_y),
    }


def main() -> None:
    world_id = sys.argv[1] if len(sys.argv) > 1 else "sandbox_world"
    ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    seed = 42

    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, compile_report = WorldCompiler.compile(spec, seed=seed)
    print(f"Compiled {world_id}: entities={compile_report['entity_count']} hash={compile_report['state_hash']}")

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)

    stats0 = render(state, str(out_dir / f"{world_id}_tick0.png"))
    print(f"Rendered tick 0: {stats0}")

    profile = RuntimeProfile(
        name="RENDER_PROTO", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024, max_cpu_percent=90.0, max_worker_count=0,
        max_tick_budget_ms=50.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0,
    )
    rng = DeterministicRNG(seed)
    kernel = Kernel(profile=profile, state=state, rng=rng, world_id=world_id)
    for _ in range(ticks):
        kernel.tick_once()

    stats_n = render(kernel._state, str(out_dir / f"{world_id}_tick{ticks}.png"))
    print(f"Rendered tick {ticks}: {stats_n}")


if __name__ == "__main__":
    main()
