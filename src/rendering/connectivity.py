"""Whole-map walkable-region connectivity via BFS flood-fill.

Ported from the inline example at experiments/spatial_rendering/PROPOSAL.md:362-380
(TCK-20260821-VISUAL-CONNECTIVITY-METRIC). That algorithm ran as one-off verification
code and was never saved as a named prototype script under experiments/spatial_rendering/
prototype/ (PROPOSAL.md:470), so unlike src/rendering/render.py's promotion from a
committed prototype file, this module ports the algorithm's shape directly from the
proposal doc, adapted to walk a walkability predicate instead of a tiles_of_type set
and to return a richer structured result.

The walkability rule is fixed to exactly the first two checks of
LegalityServiceV2.verify_occupancy (src/engine/legality.py:71-77): a tile is walkable
iff terrain.get(pos) != "WALL" and pos not in blocked_tiles. Steps 3-5 of
verify_occupancy (buildings, transient claims, live entity occupancy) are deliberately
not ported here — they are data-lookups against mutable per-tick state, out of scope for
this pure geometry computation.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectivityResult:
    walkable_count: int
    component_count: int
    component_sizes: list[int]
    percent_reachable: float


def is_walkable(
    pos: tuple[int, int],
    terrain: dict,
    blocked_tiles: set,
) -> bool:
    if terrain.get(pos) == "WALL":
        return False
    if pos in blocked_tiles:
        return False
    return True


def analyze_connectivity(
    terrain: dict[tuple[int, int], str],
    blocked_tiles: set[tuple[int, int]],
) -> ConnectivityResult:
    walkable_tiles = {
        pos for pos in terrain.keys() if is_walkable(pos, terrain, blocked_tiles)
    }

    visited: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start in walkable_tiles:
        if start in visited:
            continue
        comp: list[tuple[int, int]] = []
        q: deque[tuple[int, int]] = deque([start])
        visited.add(start)
        while q:
            x, y = q.popleft()
            comp.append((x, y))
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nb = (x + dx, y + dy)
                # Membership must be checked against the precomputed walkable_tiles set,
                # not by re-calling is_walkable(nb, ...) directly: is_walkable treats any
                # coordinate absent from terrain (terrain.get returns None != "WALL") as
                # walkable, so an unbounded re-check here would flood-fill outward forever
                # past the edge of any terrain dict that isn't fully wall-enclosed.
                if nb in walkable_tiles and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
        components.append(comp)

    walkable_count = len(walkable_tiles)
    component_count = len(components)
    component_sizes = sorted((len(c) for c in components), reverse=True)
    percent_reachable = (
        (component_sizes[0] / walkable_count) * 100.0 if walkable_count > 0 else 0.0
    )

    return ConnectivityResult(
        walkable_count=walkable_count,
        component_count=component_count,
        component_sizes=component_sizes,
        percent_reachable=percent_reachable,
    )
