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

from typing import TYPE_CHECKING, Iterable, Optional

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
