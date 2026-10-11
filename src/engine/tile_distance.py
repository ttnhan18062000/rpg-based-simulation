"""Manhattan distance between the whole tiles two positions stand on: a leaf module, so legality and the appraisal can share it without an import cycle."""
from __future__ import annotations

from typing import Tuple


def manhattan_tile_distance(a: Tuple[float, float], b: Tuple[float, float]) -> int:
    """Manhattan distance between the whole tiles two positions stand on (COMB-001; MOV-07, Decision 25: each coordinate reads as `int(pos)`, as every tile lookup does)."""
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))
