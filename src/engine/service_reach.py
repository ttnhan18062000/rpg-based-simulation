"""
Where a subject may use a building's service (MOV-07, SURV-06).

A building's own tile is not enterable, so a walker that reaches a building ends orthogonally adjacent
to it (MOV-07: adjacency is orthogonal). A service that demanded the subject stand ON the building tile
could therefore never be used. A subject is within reach of a building's service when it stands on one of
the building's tiles or on an orthogonal neighbour of one. The offsets are in a fixed order so a subject
beside two buildings always resolves to the same one. A caller that needs a particular service passes
``kinds`` so a nearer building of another kind cannot shadow the one that serves it.

Compiled worlds declare buildings in ``state.buildings`` (``state.building_tiles`` is empty there), so the
building position map is the source of truth; ``building_tiles`` is still honoured for states that fill it.
"""
from __future__ import annotations

from typing import Any, Collection, Optional, Tuple

from src.engine.spatial_query import SpatialQueryService

Tile = Tuple[int, int]

_REACH_OFFSETS = ((0, 0), (0, -1), (1, 0), (0, 1), (-1, 0))


def building_kind_at(state: Any, tile: Tile) -> Optional[str]:
    """The kind of the building on exactly `tile`, or None."""
    building = SpatialQueryService.get_building_at(state, tile)
    if building is not None:
        return building.kind
    # A worker's read-only packet carries `buildings` and `building_map` but no `building_tiles`: a missing map means no kind.
    building_tiles = getattr(state, "building_tiles", None)
    kind: Optional[str] = building_tiles.get(tile) if building_tiles is not None else None
    return kind


def service_tile(state: Any, tile: Tile, kinds: Optional[Collection[str]] = None) -> Optional[Tile]:
    """The building tile whose service `tile` can use, or None when no building (of one of `kinds`, when given) is in reach."""
    for dx, dy in _REACH_OFFSETS:
        candidate = (tile[0] + dx, tile[1] + dy)
        kind = building_kind_at(state, candidate)
        if kind is not None and (kinds is None or kind in kinds):
            return candidate
    return None


def service_at(state: Any, tile: Tile, kinds: Optional[Collection[str]] = None) -> Tuple[Tile, Optional[str]]:
    """(building tile, kind) of the building (of one of `kinds`, when given) whose service `tile` can use; (`tile`, None) when none is in reach."""
    found = service_tile(state, tile, kinds)
    return (found or tile), (building_kind_at(state, found) if found else None)
