"""The one position-to-region rule (Mechanics Bible 06, LOC-08: authored precedence).

Regions may overlap, so a point can lie inside several. This module defines, once, which region such a
point belongs to. Every position-to-region lookup in the engine and in the systems applies it, so an
event is credited to the same region by whoever asks, and the region's hazard is the same one.

The answer is **authored precedence**, never derived from area, distance or any mutable region state.
The resolved world carries the final total order as the order of its region list
(``WorldSpec.regions`` -> ``state.regions`` insertion order), produced at assembly by
``src/worldassembly/region_precedence.py`` from declared precedence, containment (the contained region
wins) and declaration order. This function therefore only has to take the first region in that order
that contains the point.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Optional, Tuple

if TYPE_CHECKING:
    from src.core.state import RegionState


def resolve_region_among(candidates: Iterable["RegionState"], x: float, y: float) -> Optional["RegionState"]:
    """Pick the region a point belongs to from ``candidates``.

    1. Membership is inclusive on all four edges: ``x_min <= x <= x_max`` and ``y_min <= y <= y_max``.
       This is the range ``WorldCompiler`` paints terrain over and places entities in, so a tile on a
       region's far edge belongs to that region.
    2. ``candidates`` are in resolved precedence order (``state.regions`` insertion order, highest
       precedence first); the first region that contains the point wins.
    3. No candidate contains the point: ``None``. That is unclaimed space, not an error.
    """
    for region in candidates:
        x_min, y_min, x_max, y_max = region.bounds
        if x_min <= x <= x_max and y_min <= y <= y_max:
            return region
    return None


def _remember_extent(state: Any, extent: Any) -> None:
    """Cache the extent on a state that has the slot; a slotted context without it (a reconstruction context) stays uncached."""
    if hasattr(state, "_regions_global_bounds"):
        object.__setattr__(state, "_regions_global_bounds", extent)


def world_extent(state: Any) -> Optional[Tuple[float, float, float, float]]:
    """The one authoritative extent of the world: ``(x_min, y_min, x_max, y_max)``, or None when none is declared.

    The world declares no map size of its own; its topology is the declared regions (Bible 06, declarative topology), so
    the extent is the union of the region bounds, inclusive on all four edges. A tile outside it is not part of the world.
    ``state`` is any object that carries ``regions`` (a worker context included); one without them has no declared extent.
    The result is cached on the state under ``_regions_global_bounds`` (False records "none declared")."""
    cached = getattr(state, "_regions_global_bounds", None)
    if cached is False:
        return None
    if cached is not None:
        return cached  # type: ignore[no-any-return]
    regions = getattr(state, "regions", None)
    if not regions:
        _remember_extent(state, False)
        return None
    x_min = y_min = float("inf")
    x_max = y_max = float("-inf")
    for r in regions.values():
        x_min = min(x_min, r.bounds[0])
        y_min = min(y_min, r.bounds[1])
        x_max = max(x_max, r.bounds[2])
        y_max = max(y_max, r.bounds[3])
    extent = (x_min, y_min, x_max, y_max)
    _remember_extent(state, extent)
    return extent


def is_inside_world(state: Any, pos: Tuple[float, float]) -> bool:
    """True when ``pos`` lies inside the world extent (inclusive); True when no extent is declared (nothing to violate)."""
    extent = world_extent(state)
    if extent is None:
        return True
    return extent[0] <= pos[0] <= extent[2] and extent[1] <= pos[1] <= extent[3]
