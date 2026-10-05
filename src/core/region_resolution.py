"""The one position-to-region rule.

Regions may overlap (Mechanics Bible 06, Region Overlap Resolution), so a point can lie inside several.
This module defines, once, which region such a point belongs to. Every position-to-region lookup in the
engine and in the systems applies it, so that an event is credited to the same region by whoever asks.
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
    2. The region with the SMALLEST AREA, ``(x_max - x_min) * (y_max - y_min)`` (the area formula the rest
       of the codebase already uses), wins: the most specific containing region.
    3. Equal areas: the region that comes first in ``candidates`` wins. Callers pass candidates in
       declaration order (``state.regions`` insertion order), so ties go to the earlier-declared region.
    4. No candidate contains the point: ``None``. That is unclaimed space, not an error.
    """
    best: Optional["RegionState"] = None
    best_area = 0.0
    for region in candidates:
        x_min, y_min, x_max, y_max = region.bounds
        if x_min <= x <= x_max and y_min <= y <= y_max:
            area = (x_max - x_min) * (y_max - y_min)
            if best is None or area < best_area:
                best, best_area = region, area
    return best
