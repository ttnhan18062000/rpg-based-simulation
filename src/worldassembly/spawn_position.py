"""
src/worldassembly/spawn_position.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION

Deterministic spawn placement: a hashed point inside a region's bounds, de-conflicted against positions already claimed in one resolve() call. Pure
functions of their arguments (no RNG, no module state). Used by the compile-profile resolver and by survivor placement (campaigns).
"""
from __future__ import annotations

import hashlib
import logging
from typing import Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def hash_point_in_bounds(key: str, bounds: Tuple[int, int, int, int]) -> Tuple[int, int]:
    """
    Deterministic (pure function of key + bounds, no RNG) point inside a region's
    [min_x, min_y, max_x, max_y] bounds -- TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION.
    """
    min_x, min_y, max_x, max_y = bounds
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    # RegionSpec.validate_bounds guarantees min_x <= max_x and min_y <= max_y, so these are
    # always >= 1 -- no zero-division guard needed, and no off-by-one beyond max_x/max_y either
    # (a degenerate min_x == max_x region correctly always yields x == min_x).
    num_x_positions = max_x - min_x + 1
    num_y_positions = max_y - min_y + 1
    x = min_x + (int.from_bytes(digest[0:4], "big") % num_x_positions)
    y = min_y + (int.from_bytes(digest[4:8], "big") % num_y_positions)
    return (x, y)


# Deterministic fixed probe sequence for de-confliction, tried in this exact order.
DECONFLICT_PROBE_OFFSETS: Tuple[Tuple[int, int], ...] = (
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (-1, -1), (1, -1), (-1, 1),
    (2, 0), (-2, 0), (0, 2), (0, -2),
)


def resolve_spawn_position(
    key: str,
    spawn_region: Optional[str],
    region_bounds: Dict[str, Tuple[int, int, int, int]],
    claimed: Dict[str, Set[Tuple[int, int]]],
) -> Optional[Tuple[float, float]]:
    """
    Real per-entity spatial placement, anchored on the population's own authored `spawn_region`
    -- TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION.

    Returns None when spawn_region is unset or not a known region (caller falls back to
    WorldEntitySpawner's own default_position). `claimed` must be a dict local to one resolve()
    call -- never module/instance state -- so this stays a pure function of that call's spec.

    De-confliction is required, not optional: multiple populations sharing one spawn_region is
    the documented normal case (compiler.py's region_declared_population aggregation comment),
    confirmed against real corpus content (bandit_road_trade_pressure.yaml and others -- see
    investigation.md) where two populations necessarily resolve to the same single region.
    """
    if not spawn_region:
        return None
    bounds = region_bounds.get(spawn_region)
    if bounds is None:
        return None

    region_claimed = claimed.setdefault(spawn_region, set())
    candidate = hash_point_in_bounds(key, bounds)
    if candidate not in region_claimed:
        region_claimed.add(candidate)
        return (float(candidate[0]), float(candidate[1]))

    min_x, min_y, max_x, max_y = bounds
    for dx, dy in DECONFLICT_PROBE_OFFSETS:
        probe = (
            min(max(candidate[0] + dx, min_x), max_x),
            min(max(candidate[1] + dy, min_y), max_y),
        )
        if probe not in region_claimed:
            region_claimed.add(probe)
            return (float(probe[0]), float(probe[1]))

    # Probe sequence exhausted. This is NOT necessarily a degenerate (too-small) region -- the
    # probe set is 12 fixed offsets covering only a +/-2 box (13 candidate positions) around the
    # hash point, so exhaustion is also reachable in a large region whose local neighborhood
    # around that one point happens to be saturated, even with thousands of free tiles
    # elsewhere in the same region. Falling back beats raising and failing the compile, but the
    # fallback is a REAL, observable degradation: it reintroduces exactly the
    # LAW-OCCUPANCY-COLLISION condition this ticket exists to eliminate. Must not be silent --
    # log it so a future occurrence is diagnosable in one grep, not another multi-day trace.
    logger.warning(
        "Spawn-position de-confliction exhausted its probe sequence for key=%r in "
        "spawn_region=%r -- falling back to an already-claimed position %r, which will "
        "trigger a real LAW-OCCUPANCY-COLLISION violation for this entity.",
        key, spawn_region, candidate,
    )
    region_claimed.add(candidate)
    return (float(candidate[0]), float(candidate[1]))
