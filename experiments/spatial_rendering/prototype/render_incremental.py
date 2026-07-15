"""Prototype: dirty-set-aware incremental rendering vs. full re-render per frame.

Reuses src/core/dirty.py's real DirtySet (PERF-006) — already computed by the Kernel every
tick and exposed on kernel._status.dirty_set — rather than building parallel change-tracking.

Video-codec analogy: the cached background is an I-frame (expensive, rendered once); each
subsequent frame is a P-frame (cheap, only touches what DirtySet says changed).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.platform.rng import DeterministicRNG
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from render_world import terrain_color, DEFAULT_TERRAIN_COLOR  # noqa: E402
from png_writer import write_png  # noqa: E402

ENTITY_COLOR_ALIVE = (0x4A, 0x9E, 0xFF)


class IncrementalRenderer:
    """Caches the static background once; subsequent frames only touch dirty entities."""

    def __init__(self, state, scale: int = 3) -> None:
        self.scale = scale
        terrain = state.terrain
        xs = [p[0] for p in terrain.keys()]
        ys = [p[1] for p in terrain.keys()]
        self.min_x, self.max_x = min(xs), max(xs)
        self.min_y, self.max_y = min(ys), max(ys)
        self.grid_w = self.max_x - self.min_x + 1
        self.grid_h = self.max_y - self.min_y + 1
        self.width = self.grid_w * scale
        self.height = self.grid_h * scale

        # I-frame: build once.
        self.background = [DEFAULT_TERRAIN_COLOR] * (self.width * self.height)
        for (tx, ty), tval in terrain.items():
            gx, gy = tx - self.min_x, ty - self.min_y
            if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
                c = terrain_color(tval)
                for sy in range(scale):
                    for sx in range(scale):
                        px, py = gx * scale + sx, gy * scale + sy
                        self.background[py * self.width + px] = c

        self.frame = list(self.background)  # current live pixel buffer
        self.last_entity_pos: dict[int, tuple[int, int]] = {}

    def _blit_cell(self, gx: int, gy: int, color: tuple) -> None:
        if not (0 <= gx < self.grid_w and 0 <= gy < self.grid_h):
            return
        for sy in range(self.scale):
            for sx in range(self.scale):
                px, py = gx * self.scale + sx, gy * self.scale + sy
                self.frame[py * self.width + px] = color

    def _restore_background_cell(self, gx: int, gy: int) -> None:
        if not (0 <= gx < self.grid_w and 0 <= gy < self.grid_h):
            return
        for sy in range(self.scale):
            for sx in range(self.scale):
                px, py = gx * self.scale + sx, gy * self.scale + sy
                self.frame[py * self.width + px] = self.background[py * self.width + px]

    def update(self, state, dirty_entity_ids: set[int]) -> None:
        """Only touches entities flagged dirty this tick — the core optimization."""
        for eid in dirty_entity_ids:
            ent = state.entities.get(eid)
            old_pos = self.last_entity_pos.get(eid)
            if old_pos is not None:
                self._restore_background_cell(old_pos[0] - self.min_x, old_pos[1] - self.min_y)
            if ent is not None and getattr(ent.lifecycle, "active", True) and ent.combat.alive:
                x, y = ent.navigation.position
                gx, gy = int(x) - self.min_x, int(y) - self.min_y
                self._blit_cell(gx, gy, ENTITY_COLOR_ALIVE)
                self.last_entity_pos[eid] = (int(x), int(y))
            else:
                self.last_entity_pos.pop(eid, None)

    def full_redraw_entities(self, state) -> None:
        """Baseline comparison: redraw every entity every frame, no dirty-set filtering."""
        self.frame = list(self.background)
        for eid, ent in state.entities.items():
            if getattr(ent.lifecycle, "active", True) and ent.combat.alive:
                x, y = ent.navigation.position
                self._blit_cell(int(x) - self.min_x, int(y) - self.min_y, ENTITY_COLOR_ALIVE)

    def save(self, path: str) -> None:
        write_png(path, self.width, self.height, self.frame)


def main() -> None:
    world_id = sys.argv[1] if len(sys.argv) > 1 else "wilderness_survival"
    n_ticks = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, report = WorldCompiler.compile(spec, seed=42)
    print(f"Compiled {world_id}: entities={report['entity_count']}, terrain_tiles={len(state.terrain)}")

    profile = RuntimeProfile(
        name="INCR", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=2048, max_cpu_percent=90.0, max_worker_count=0,
        max_tick_budget_ms=300.0, max_queue_depth=100,
        max_replay_buffer_kb=4096, max_observability_budget_percent=5.0,
    )

    # --- Baseline: tick, THEN separately time a full re-render (background + all entities) ---
    rng = DeterministicRNG(42)
    kernel = Kernel(profile=profile, state=state, rng=rng, world_id=world_id)
    renderer_baseline = IncrementalRenderer(kernel._state)  # background built once either way
    render_only_baseline_ms = 0.0
    for _ in range(n_ticks):
        kernel.tick_once()
        t0 = time.perf_counter()
        renderer_baseline.full_redraw_entities(kernel._state)
        render_only_baseline_ms += (time.perf_counter() - t0) * 1000
    renderer_baseline.save(str(Path(__file__).resolve().parent / "output" / f"{world_id}_incr_baseline.png"))

    # --- Incremental: tick, THEN separately time only-dirty-entity updates ---
    state2, _ = WorldCompiler.compile(spec, seed=42)
    rng2 = DeterministicRNG(42)
    kernel2 = Kernel(profile=profile, state=state2, rng=rng2, world_id=world_id)
    renderer_incr = IncrementalRenderer(kernel2._state)
    dirty_hits = 0
    render_only_incr_ms = 0.0
    for _ in range(n_ticks):
        kernel2.tick_once()
        ds = getattr(kernel2._status, "dirty_set", None)
        dirty_ids = (ds.movement_entities | ds.lifecycle_entities) if ds is not None else set(kernel2._state.entities.keys())
        dirty_hits += len(dirty_ids)
        t0 = time.perf_counter()
        renderer_incr.update(kernel2._state, dirty_ids)
        render_only_incr_ms += (time.perf_counter() - t0) * 1000
    renderer_incr.save(str(Path(__file__).resolve().parent / "output" / f"{world_id}_incr_final.png"))

    print(f"\n[render-only cost, tick cost excluded]")
    print(f"Baseline (full entity redraw every frame): {render_only_baseline_ms:.2f}ms total, {render_only_baseline_ms/n_ticks:.4f}ms/frame")
    print(f"Incremental (DirtySet-filtered):            {render_only_incr_ms:.2f}ms total, {render_only_incr_ms/n_ticks:.4f}ms/frame")
    print(f"Avg dirty (movement|lifecycle) entities/tick: {dirty_hits/n_ticks:.1f} (of {report['entity_count']} total)")
    if render_only_incr_ms > 0:
        print(f"Render-only speedup: {render_only_baseline_ms/render_only_incr_ms:.2f}x")


if __name__ == "__main__":
    main()
