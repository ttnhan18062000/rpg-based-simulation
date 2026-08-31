from __future__ import annotations
from typing import Optional, Set, Tuple


def nearest_town_tile(
    town_tiles: Set[Tuple[int, int]],
    position: Tuple[float, float],
) -> Optional[Tuple[float, float]]:
    """Deterministic nearest-tile-to-position lookup over town_tiles.

    Tie-break: lowest (x, y) among tiles at equal minimum distance -- `min()`'s key
    function makes the result independent of `town_tiles` set iteration order.
    """
    if not town_tiles:
        return None
    best = min(
        town_tiles,
        key=lambda t: ((t[0] - position[0]) ** 2 + (t[1] - position[1]) ** 2, t[0], t[1]),
    )
    return (float(best[0]), float(best[1]))
