"""DirtySet-aware incremental world renderer.

Caches the static terrain background once, then per tick only re-blits pixels for
entities present in the DirtySet-derived dirty-id set. Reuses src/core/dirty.py's
real DirtySet (exposed on kernel._status.dirty_set) -- no parallel dirty-tracking
mechanism. Promoted from experiments/spatial_rendering/prototype/render_incremental.py
(TCK-20260821-WORLD-RENDER-CORE).
"""
from __future__ import annotations

from typing import Any, Optional, Set

from src.rendering.png_writer import write_png
from src.rendering.render import (
    BLOCKED_OUTLINE,
    BUILDING_COLOR,
    DEFAULT_TERRAIN_COLOR,
    ENTITY_COLOR_DEAD,
    terrain_color,
)

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

        # I-frame: build once. terrain -> buildings -> blocked_outline, matching
        # render.py's DRAW_ORDER for the static (non-entity) layers. blocked_tiles/
        # building_tiles do not change during a run (no DirtySet domain tracks them),
        # so they belong in the static background cache, not the per-tick entity
        # update path -- this keeps the incremental frame consistent with a full
        # render() of the same state, not just its terrain layer.
        self.background = [DEFAULT_TERRAIN_COLOR] * (self.width * self.height)
        for (tx, ty), tval in terrain.items():
            gx, gy = tx - self.min_x, ty - self.min_y
            if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
                c = terrain_color(tval)
                for sy in range(scale):
                    for sx in range(scale):
                        px, py = gx * scale + sx, gy * scale + sy
                        self.background[py * self.width + px] = c

        for (bx, by), _btype in getattr(state, "building_tiles", {}).items():
            gx, gy = bx - self.min_x, by - self.min_y
            if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
                for sy in range(scale):
                    for sx in range(scale):
                        px, py = gx * scale + sx, gy * scale + sy
                        self.background[py * self.width + px] = BUILDING_COLOR

        for (bx, by) in getattr(state, "blocked_tiles", set()):
            gx, gy = bx - self.min_x, by - self.min_y
            if 0 <= gx < self.grid_w and 0 <= gy < self.grid_h:
                for sx in range(scale):
                    px = gx * scale + sx
                    self.background[(gy * scale) * self.width + px] = BLOCKED_OUTLINE
                    self.background[(gy * scale + scale - 1) * self.width + px] = BLOCKED_OUTLINE

        self.frame = list(self.background)  # current live pixel buffer
        self.last_entity_pos: dict[int, tuple[int, int]] = {}

        # I-frame completion: seed every currently-active entity's position onto the
        # frame at construction time, alive or dead (TCK-20260822-HOTFIX-INCREMENTAL-
        # DEATH-RECOLOR-GAP: a corpse present at construction must render
        # ENTITY_COLOR_DEAD, matching render()'s own alive/dead branch, not be
        # silently dropped to background). Without this, an entity that never becomes
        # movement/lifecycle-dirty for the lifetime of the renderer would never be
        # drawn at all, since update() only touches ids present in a dirty set --
        # the initial snapshot must be a complete frame (matching render()'s
        # unconditional per-entity draw), not just the static background.
        for eid, ent in state.entities.items():
            if getattr(ent.lifecycle, "active", True):
                x, y = ent.navigation.position
                gx, gy = int(x) - self.min_x, int(y) - self.min_y
                color = ENTITY_COLOR_ALIVE if ent.combat.alive else ENTITY_COLOR_DEAD
                self._blit_cell(gx, gy, color)
                self.last_entity_pos[eid] = (int(x), int(y))

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

    def update(self, state, dirty_entity_ids: Set[int]) -> None:
        """Only touches entities flagged dirty this tick — the core optimization."""
        for eid in dirty_entity_ids:
            ent = state.entities.get(eid)
            old_pos = self.last_entity_pos.get(eid)
            if old_pos is not None:
                self._restore_background_cell(old_pos[0] - self.min_x, old_pos[1] - self.min_y)
            if ent is not None and getattr(ent.lifecycle, "active", True):
                x, y = ent.navigation.position
                gx, gy = int(x) - self.min_x, int(y) - self.min_y
                color = ENTITY_COLOR_ALIVE if ent.combat.alive else ENTITY_COLOR_DEAD
                self._blit_cell(gx, gy, color)
                self.last_entity_pos[eid] = (int(x), int(y))
            else:
                self.last_entity_pos.pop(eid, None)

    def save(self, path: str) -> None:
        write_png(path, self.width, self.height, self.frame)


def dirty_entity_ids_for_render(kernel_status: Any, all_entity_ids: Set[int]) -> Set[int]:
    """Resolves which entity ids the incremental renderer should touch this tick.

    dirty_set is only ever set on kernel._status by Kernel._run_hard_law_checks
    (src/engine/kernel.py), and only when non-None -- otherwise the attribute is
    deleted. getattr(..., None) is the correct existence check, matching this
    codebase's own get_relevant_entity_ids fallback convention (src/core/dirty.py).
    Absent dirty_set (first frame / no prior tick) falls back to a full render.
    """
    ds = getattr(kernel_status, "dirty_set", None)
    if ds is None:
        return set(all_entity_ids)
    return ds.movement_entities | ds.lifecycle_entities
