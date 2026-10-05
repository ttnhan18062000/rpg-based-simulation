"""Region-contained tactical destinations for retreat and stalemate-break wandering.

Pure functions: they read the state and the entity and return a destination or ``None``.
They never mutate state; the caller turns the result into a ``NavigationUpdate``.

Governing Rules (docs/world_rules/space-environment/): MOV-01 (a destination must be valid),
LOC-01 / LOC-03 (containment is a real relationship, an entity outside every region is outside
the declared spatial model), MOV-03 (holding position is a legitimate outcome).

Retreat and wander are different semantics and deliberately do not share a derivation.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Iterable, Optional, Tuple

from src.core.enums import Domain
from src.platform.rng import DeterministicRNG

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, RegionState

Position = Tuple[float, float]

# One perception radius (get_neighbor_view radius in TacticalDecisionSystem): a retreating entity
# aims for the point that far beyond itself along the away-vector, so it keeps clear of the
# threat horizon it is reacting to.
RETREAT_STEP = 10.0
# Half-width of the square a stalemate-breaking entity wanders within.
WANDER_RADIUS = 5.0
_EPSILON = 1e-9


def _manhattan(a: Position, b: Position) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def containing_region(state: "AuthoritativeState", pos: Position) -> Optional["RegionState"]:
    """The region whose bounds contain ``pos``, or None.

    Strict bounds only. ``RegionService.find_region_at`` falls back to the nearest region centre,
    which would call a point outside every region "inside" one; that is exactly the defect here.
    Iterates in sorted id order so overlapping bounds resolve the same way every run.
    """
    px, py = pos
    for region_id in sorted(state.regions):
        region = state.regions[region_id]
        xmin, ymin, xmax, ymax = region.bounds
        if xmin <= px <= xmax and ymin <= py <= ymax:
            return region
    return None


def _clamp_into(region: "RegionState", pos: Position) -> Position:
    xmin, ymin, xmax, ymax = region.bounds
    return (min(max(pos[0], float(xmin)), float(xmax)), min(max(pos[1], float(ymin)), float(ymax)))


def retreat_destination(
    state: "AuthoritativeState",
    entity: "EntityState",
    threats: Iterable["EntityState"],
) -> Optional[Position]:
    """Where a retreating entity should head, or None when no valid destination exists.

    1. Away from the perceived threats, clamped to stay inside the entity's current region.
       Uses only the threats the caller already perceives and the entity's own position.
    2. Otherwise (no threat vector, or cornered so the clamped point is no farther from the
       nearest threat) the entity's own ``strategic.home_region_id`` region, when set and present.
    3. Otherwise None: the caller holds position (MOV-03). Never a sentinel coordinate.
    """
    here: Position = entity.navigation.position
    region = containing_region(state, here)
    threat_positions = sorted(t.navigation.position for t in threats)

    if region is not None and threat_positions:
        away_x = sum(here[0] - p[0] for p in threat_positions)
        away_y = sum(here[1] - p[1] for p in threat_positions)
        norm = math.hypot(away_x, away_y)
        if norm > _EPSILON:
            candidate = _clamp_into(
                region,
                (here[0] + away_x / norm * RETREAT_STEP, here[1] + away_y / norm * RETREAT_STEP),
            )
            nearest_now = min(_manhattan(here, p) for p in threat_positions)
            nearest_then = min(_manhattan(candidate, p) for p in threat_positions)
            if nearest_then > nearest_now + _EPSILON:
                return candidate

    home_id = entity.strategic.home_region_id
    home = state.regions.get(home_id) if home_id else None
    if home is not None:
        return home.center
    return None


def wander_destination(state: "AuthoritativeState", entity: "EntityState") -> Optional[Position]:
    """A seeded, nearby, region-contained point for a stalemate-breaking entity, or None.

    None when the entity is itself outside every region: there is no region to stay inside, so
    the caller holds position rather than inventing a destination.
    """
    here: Position = entity.navigation.position
    region = containing_region(state, here)
    if region is None:
        return None
    rng = DeterministicRNG(state.seed)
    dx = (rng.get_float(Domain.TACTICAL, state.tick, entity.id, 0) * 2.0 - 1.0) * WANDER_RADIUS
    dy = (rng.get_float(Domain.TACTICAL, state.tick, entity.id, 1) * 2.0 - 1.0) * WANDER_RADIUS
    return _clamp_into(region, (here[0] + dx, here[1] + dy))
