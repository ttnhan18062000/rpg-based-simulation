"""
Where a subject may use a building's service (MOV-07, SURV-06).

A building's own tile is not enterable, so a walker that reaches a building ends orthogonally adjacent
to it (MOV-07: adjacency is orthogonal). A service that demanded the subject stand ON the building tile
could therefore never be used. A subject is within reach of a building's service when it stands on one of
the building's tiles or on an orthogonal neighbour of one. The offsets are in a fixed order so a subject
beside two buildings always resolves to the same one.

Compiled worlds declare buildings in ``state.buildings`` (``state.building_tiles`` is empty there), so the
building position map is the source of truth; ``building_tiles`` is still honoured for states that fill it.
"""
from __future__ import annotations

from typing import Any, Optional, Tuple

Tile = Tuple[int, int]

_REACH_OFFSETS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))


def building_kind_at(state: Any, tile: Tile) -> Optional[str]:
    """The kind of the building on exactly `tile`, or None."""
    from src.engine.spatial_query import SpatialQueryService
    building = SpatialQueryService.get_building_at(state, tile)
    if building is not None:
        return building.kind
    return state.building_tiles.get(tile)


def service_tile(state: Any, tile: Tile) -> Optional[Tile]:
    """The building tile whose service `tile` can use, or None when no building is within reach."""
    for dx, dy in _REACH_OFFSETS:
        candidate = (tile[0] + dx, tile[1] + dy)
        if building_kind_at(state, candidate) is not None:
            return candidate
    return None
