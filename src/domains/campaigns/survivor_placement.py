"""
src/domains/campaigns/survivor_placement.py
────────────────────────────────────────────────────────────────────────────────
Real position resolution for survivor-reconstructed entities —
TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION.

CampaignOrchestrator._build_initial_state()'s survivor-reconstruction branch (episode N>0)
previously left every reconstructed entity at NavigationComponent's own dataclass default,
(0.0, 0.0) — identical for every survivor, tripping LAW-SPAWN-OCCUPANCY immediately. This module
carries each survivor's real EntityCarryForward.last_position forward and validates it against
the new episode's own (differently-seeded) terrain/building layout, falling back to a
deterministic probe and then an expanding search — never a shared constant — when the carried
position is no longer walkable.

Batch B's TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION mechanism
(src/worldassembly/resolver.py's `_resolve_spawn_position`) is NOT reused directly: it requires a
`spawn_region` string, which no survivor has (see
TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP). `_DECONFLICT_PROBE_OFFSETS` and
`_hash_point_in_bounds` — the region-agnostic pieces — are reused directly.
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

from src.core.state import EntityState
from src.engine.legality import LegalityServiceV2
from src.worldassembly.resolver import _DECONFLICT_PROBE_OFFSETS, _hash_point_in_bounds

logger = logging.getLogger(__name__)


class SurvivorReconstructionContext:
    """A minimal stand-in for `AuthoritativeState`, passed to
    `LegalityServiceV2.verify_occupancy()` during survivor reconstruction.

    `__slots__` here is DELIBERATELY EXHAUSTIVE — this exact list, no more. Do not add
    attributes without reading this docstring's own reasoning first.

    `verify_occupancy()`'s own dynamic-entity-occupancy check has three sub-paths
    (`src/engine/legality.py:96-115`): an `occupancy_snapshot` fast path, a cached
    `SpatialQueryService.get_occupancy_map()` path, and a direct uncached `.entities` scan. Only
    the last one is safe when this context object is reused across a reconstruction loop that
    mutates `.entities` in place — `get_occupancy_map()` caches its result onto the *context
    object itself* via `object.__setattr__(state, "_occupancy_map_cache", mapping)`, keyed only
    by object identity, with no invalidation. Reusing one context across the survivor loop would
    otherwise silently return a stale occupancy map on every call after the first.

    This class reaches the uncached path deterministically *because* its restricted `__slots__`
    has no room for `_occupancy_map_cache` (or `occupancy_snapshot`, or `occupancy_map`) —
    `object.__setattr__` raises `AttributeError` when `get_occupancy_map()` tries to write the
    cache, `verify_occupancy()`'s own `except (AttributeError, TypeError)` catches it, and the
    direct scan runs instead, every single call. Adding a slot for any reason — including one of
    those three names, or something unrelated that happens to make room for a `__dict__` fallback
    — silently re-enables the cached path and the staleness bug returns with no visible cause.

    See `test_reconstruction_context_slots_force_uncached_occupancy_scan`
    (`tests/unit/domains/campaigns/test_survivor_placement.py`) before touching this list — it
    encodes the exact mutate-between-two-calls reproduction that motivated this design.
    """

    __slots__ = ("terrain", "blocked_tiles", "buildings", "building_tiles", "transient_claims", "entities")

    def __init__(
        self,
        terrain: dict,
        blocked_tiles: set,
        buildings: dict,
        entities: Dict[int, EntityState],
    ) -> None:
        self.terrain = terrain
        self.blocked_tiles = blocked_tiles
        self.buildings = buildings
        self.building_tiles = None  # forces verify_occupancy()'s own `buildings`-dict fallback scan
        self.transient_claims: list = []
        self.entities = entities


def _region_label_for(pos: Tuple[int, int], regions: dict) -> str:
    """Best-effort region name for an exhaustion-warning message. Not used for legality —
    only for making the log line locatable. Returns "unknown" if no authored region's bounds
    contain `pos` (a survivor's carried/probed position is not required to stay in-region)."""
    for region in regions.values():
        min_x, min_y, max_x, max_y = region.bounds
        if min_x <= pos[0] <= max_x and min_y <= pos[1] <= max_y:
            return region.id
    return "unknown"


def _log_exhaustion_warning(
    entity_id: int, region_label: str, tile: Tuple[int, int]
) -> None:
    # Message shape mirrors src/worldbuilding/compiler.py:489-495's own LAW-SPAWN-OCCUPANCY
    # exhaustion-warning precedent, deliberately, rather than inventing a new one.
    logger.warning(
        "entity %s could not be placed on a free tile near its carried last-known position "
        "(region '%s') -- search area is fully packed; LAW-SPAWN-OCCUPANCY will still flag "
        "tile %s",
        entity_id, region_label, tile,
    )


def resolve_survivor_position(
    entity_id: int,
    last_position: Optional[Tuple[float, float]],
    ctx: SurvivorReconstructionContext,
    world_width: int,
    world_height: int,
    regions: dict,
) -> Tuple[float, float]:
    """
    Resolve a real, validity-checked, deconflicted position for one reconstructed survivor.

    Chain: carried `last_position` (or a deterministic per-entity fallback origin if missing,
    e.g. a survivor carried forward before this field existed) -> `verify_occupancy()` -> a
    deterministic probe (`_DECONFLICT_PROBE_OFFSETS`) -> an expanding growing-radius search,
    clamped to `[0, world_width-1] x [0, world_height-1]` (a world-level clamp, not a region one
    — this fix anchors on last-known-position, not an authored region) -> if genuinely exhausted,
    a logged warning and the last-probed candidate anyway, mirroring `compiler.py`'s own
    exhaustion precedent. **Never** collapses to a shared constant — that reproduces the original
    bug in a narrower form.

    Caller owns writing the accepted position back into the entity's own `navigation.position`
    and re-inserting it into `ctx.entities` before resolving the next survivor, so later calls
    in the same reconstruction pass see it via the single-authority `verify_occupancy()` check.
    """
    max_x, max_y = world_width - 1, world_height - 1

    def clamp(x: int, y: int) -> Tuple[int, int]:
        return (min(max(x, 0), max_x), min(max(y, 0), max_y))

    if last_position is not None:
        origin = clamp(int(last_position[0]), int(last_position[1]))
    else:
        origin = clamp(*_hash_point_in_bounds(f"survivor_{entity_id}", (0, 0, max_x, max_y)))

    ok, _reason = LegalityServiceV2.verify_occupancy(origin, ctx, ignore_entity_id=entity_id)
    if ok:
        return (float(origin[0]), float(origin[1]))

    last_candidate = origin
    for dx, dy in _DECONFLICT_PROBE_OFFSETS:
        candidate = clamp(origin[0] + dx, origin[1] + dy)
        last_candidate = candidate
        ok, _reason = LegalityServiceV2.verify_occupancy(candidate, ctx, ignore_entity_id=entity_id)
        if ok:
            return (float(candidate[0]), float(candidate[1]))

    # The fixed probe ring is exhausted -- expand rather than collapsing to a constant.
    max_radius = max(world_width, world_height)
    for radius in range(3, max_radius + 1):
        for dx in range(-radius, radius + 1):
            for dy in (-radius, radius):
                candidate = clamp(origin[0] + dx, origin[1] + dy)
                last_candidate = candidate
                ok, _reason = LegalityServiceV2.verify_occupancy(
                    candidate, ctx, ignore_entity_id=entity_id
                )
                if ok:
                    return (float(candidate[0]), float(candidate[1]))
        for dy in range(-radius + 1, radius):
            for dx in (-radius, radius):
                candidate = clamp(origin[0] + dx, origin[1] + dy)
                last_candidate = candidate
                ok, _reason = LegalityServiceV2.verify_occupancy(
                    candidate, ctx, ignore_entity_id=entity_id
                )
                if ok:
                    return (float(candidate[0]), float(candidate[1]))

    region_label = _region_label_for(last_candidate, regions)
    _log_exhaustion_warning(entity_id, region_label, last_candidate)
    return (float(last_candidate[0]), float(last_candidate[1]))
