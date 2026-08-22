"""Deterministic batch/QA world renderer for AuthoritativeState.

Renders a static frame of an AuthoritativeState to a PNG. Pure read-only function
of state content: no wall-clock dependency, no reliance on hash-randomized ordering.
Promoted from experiments/spatial_rendering/prototype/render_world.py
(TCK-20260821-WORLD-RENDER-CORE).

Terrain-string casing (real content mixes 'PLAIN'/'plain'/'forest' as distinct dict
keys — see docs/plans/world_rendering/idea_world_rendering_core.md) is normalized here,
at the render boundary only. This is a workaround, not a fix — the underlying casing
inconsistency in src/worldbuilding/compiler.py / content YAML is explicitly out of
scope for this module.
"""
from __future__ import annotations

import os

from src.rendering.png_writer import write_png

# Ported aesthetic from frontend/src/constants/colors.ts, re-keyed by the REAL string
# vocabulary found by actually compiling and inspecting real worlds (sandbox_world,
# dungeon_crawl) -- NOT the vocabulary a static grep of src/ predicted. Real compiled
# data contains a confirmed casing bug: 'PLAIN' and 'plain' coexist as distinct dict
# keys in the same world (961 lowercase + 6593 uppercase instances in sandbox_world).
# Lookup below normalizes to uppercase specifically to route around this, but the bug
# itself is a real finding, not something to silently paper over.
TERRAIN_COLORS: dict[str, tuple[int, int, int]] = {
    "WALL": (0x55, 0x5B, 0x73),
    "PLAIN": (0x4A, 0x60, 0x30),
    "FOREST": (0x1B, 0x3A, 0x1B),
    "CAVE": (0x3A, 0x30, 0x40),
    "RUIN": (0x4A, 0x40, 0x35),
    "GRASS": (0x7A, 0xA0, 0x50),  # confirmed never emitted by any world tested -- kept as a defensive entry, given a distinct color rather than left colliding with PLAIN
    "DESERT": (0x3A, 0x34, 0x20),
    "SWAMP": (0x2A, 0x2A, 0x3A),
    "MOUNTAIN": (0x3A, 0x3A, 0x3A),
    "RIVER": (0x2E, 0x5C, 0x8A),  # confirmed real, live terrain type (highland_traverse)
    "ROAD": (0x5A, 0x50, 0x40),
    "SNOW": (0xC8, 0xD8, 0xE8),
    "TOWN": (0x2D, 0x4A, 0x3E),
    "VOLCANIC": (0x5A, 0x2A, 0x1A),
    "FLOOR": (0x1A, 0x1D, 0x27),
}
DEFAULT_TERRAIN_COLOR = (0xFF, 0x00, 0xFF)  # loud magenta -- unknown terrain must be obvious, never silently blend in


def terrain_color(raw_value: str) -> tuple[int, int, int]:
    """Normalizes terrain-string casing at the render boundary. Unrecognized values
    get the loud DEFAULT_TERRAIN_COLOR fallback -- never silently mismapped onto an
    existing color."""
    return TERRAIN_COLORS.get(raw_value.upper(), DEFAULT_TERRAIN_COLOR)


BUILDING_COLOR = (0xC0, 0x80, 0x40)
ENTITY_COLOR_ALIVE = (0x4A, 0x9E, 0xFF)
ENTITY_COLOR_DEAD = (0x60, 0x30, 0x30)
BLOCKED_OUTLINE = (0xFF, 0x50, 0x50)

# Pins the compositing order across state collections. Cross-collection composition
# order is the one real determinism/visual risk in this renderer -- within-collection
# dict/set iteration is already stable (insertion-ordered dicts, non-randomized int-tuple
# set hashing), but which layer paints over which at overlapping tiles (e.g. a building
# tile that is also flagged blocked) must be a fixed, explicit sequence, never implicitly
# derived from convenient iteration order. render() below must follow this literal order.
DRAW_ORDER = ("terrain", "buildings", "blocked_outline", "entities")


def render(state, out_path: str, scale: int = 6) -> dict:
    """Renders state to a PNG at out_path. Read-only: never mutates state. Returns a
    stats dict (histogram, counts, bounds) for reporting."""
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

    # DRAW_ORDER[0]: terrain
    terrain_histogram: dict[str, int] = {}
    for (tx, ty), tval in terrain.items():
        gx, gy = tx - min_x, ty - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            pixels[gy * grid_w + gx] = terrain_color(tval)
        terrain_histogram[tval] = terrain_histogram.get(tval, 0) + 1

    # DRAW_ORDER[1]: buildings
    for (bx, by), _btype in building_tiles.items():
        gx, gy = bx - min_x, by - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            pixels[gy * grid_w + gx] = BUILDING_COLOR

    # Upscale to `scale`x for visibility, then overlay blocked outlines and entities
    # as filled scale x scale blocks.
    out_pixels = [DEFAULT_TERRAIN_COLOR] * (width * height)
    for gy in range(grid_h):
        for gx in range(grid_w):
            c = pixels[gy * grid_w + gx]
            for sy in range(scale):
                for sx in range(scale):
                    out_pixels[(gy * scale + sy) * width + (gx * scale + sx)] = c

    # DRAW_ORDER[2]: blocked_outline
    blocked_count_rendered = 0
    for (bx, by) in blocked_tiles:
        gx, gy = bx - min_x, by - min_y
        if 0 <= gx < grid_w and 0 <= gy < grid_h:
            blocked_count_rendered += 1
            for sx in range(scale):
                out_pixels[(gy * scale) * width + (gx * scale + sx)] = BLOCKED_OUTLINE
                out_pixels[(gy * scale + scale - 1) * width + (gx * scale + sx)] = BLOCKED_OUTLINE

    # DRAW_ORDER[3]: entities
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


def render_output_path(base_dir: str, run_id: str, filename: str) -> str:
    """Resolves the storage path for a render artifact under
    {base_dir}/{run_id}/renders/{filename}. Does not route through
    RunArtifactRepository.resolve_path -- that method's file_key mapping is
    single-filename-per-key and has no entry for a directory of per-tick PNGs.
    Callers are responsible for os.makedirs(os.path.dirname(path), exist_ok=True)
    before writing; the renders/ subdirectory does not exist by default under a
    fresh run directory."""
    return os.path.join(base_dir, run_id, "renders", filename)
