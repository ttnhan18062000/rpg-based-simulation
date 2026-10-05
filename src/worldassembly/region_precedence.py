"""Region precedence ordering (LOC-08, owner decision 13).

Where region bounds overlap, a contested point belongs to the region with the higher authored
precedence. This module turns a composition's declarations into the **total order** the resolved world
carries as the order of its region list; every consumer (the runtime lookup, terrain paint, the hazard
a tile applies) reads that one order, highest precedence first.

Rules, in force order:
  * a declaration (``winner`` over each id in ``over``) is honoured for the pairs it names;
  * otherwise, if one region's bounds fully contain the other's, the CONTAINED region wins (3a);
  * any other undeclared overlap keeps the resolved declaration order, earlier wins, and is reported
    as an advisory (3b, 3c);
  * a region that owns no tile under the resulting order is an error (3c).
Declarations live with the composition (``world.yaml``) and name region ids as they appear in that
composition, because the same bare id can name different bounds in different worlds.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Set, Tuple

from src.worldbuilding.schema import InvalidWorldSpecError, RegionSpec


@dataclass(frozen=True)
class PrecedenceReport:
    """What ordering did, for the assembly report."""
    undeclared_partial_overlaps: List[Tuple[str, str, int]] = field(default_factory=list)  # (earlier, later, tiles)
    containment_resolutions: List[Tuple[str, str]] = field(default_factory=list)  # (contained winner, container)
    owned_tiles: Dict[str, int] = field(default_factory=dict)


def _tiles(bounds: Sequence[float]) -> Set[Tuple[int, int]]:
    x0, y0, x1, y1 = (int(b) for b in bounds)
    return {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}


def _overlap_tiles(a: Sequence[float], b: Sequence[float]) -> int:
    w = min(int(a[2]), int(b[2])) - max(int(a[0]), int(b[0])) + 1
    h = min(int(a[3]), int(b[3])) - max(int(a[1]), int(b[1])) + 1
    return w * h if w > 0 and h > 0 else 0


def _contains(outer: Sequence[float], inner: Sequence[float]) -> bool:
    return (int(outer[0]) <= int(inner[0]) and int(outer[1]) <= int(inner[1])
            and int(outer[2]) >= int(inner[2]) and int(outer[3]) >= int(inner[3]))


def order_regions(regions: Sequence[RegionSpec], declarations: Sequence,
                  module_declarations: Sequence = ()) -> Tuple[List[RegionSpec], PrecedenceReport]:
    """Return ``regions`` in resolved precedence order (highest first) and a report.

    ``declarations`` are the composition's (objects with ``winner: str`` and ``over: Sequence[str]``);
    ``module_declarations`` are those a module declared among its own regions, already carrying composition
    ids (namespace prefix applied). A composition declaration overrides a module declaration for the pair
    it names. Raises ``InvalidWorldSpecError`` for an unknown id, a self-declaration, a precedence cycle, or
    a region that owns no tile.
    """
    by_id = {r.id: r for r in regions}
    index = {r.id: i for i, r in enumerate(regions)}
    composition_pairs = {(d.winner, loser) for d in declarations for loser in d.over}
    # a composition declaration overrides a module declaration for the pair it names (clause 3)
    module_pairs = {(d.winner, loser) for d in module_declarations for loser in d.over
                    if (loser, d.winner) not in composition_pairs}
    declared: Set[Tuple[str, str]] = composition_pairs | module_pairs  # (winner, loser)
    for winner, loser in sorted(declared):
        if winner not in by_id:
            raise InvalidWorldSpecError(f"Region precedence names unknown region '{winner}' (known: {sorted(by_id)})")
        if loser not in by_id:
            raise InvalidWorldSpecError(f"Region precedence '{winner}' over unknown region '{loser}' (known: {sorted(by_id)})")
        if loser == winner:
            raise InvalidWorldSpecError(f"Region precedence declares '{winner}' over itself")

    edges: Set[Tuple[str, str]] = set(declared)
    containment: List[Tuple[str, str]] = []
    partial: List[Tuple[str, str, int]] = []
    ids = [r.id for r in regions]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            n = _overlap_tiles(by_id[a].bounds, by_id[b].bounds)
            if n == 0 or (a, b) in declared or (b, a) in declared:
                continue
            a_in_b, b_in_a = _contains(by_id[b].bounds, by_id[a].bounds), _contains(by_id[a].bounds, by_id[b].bounds)
            if a_in_b and not b_in_a:
                edges.add((a, b)); containment.append((a, b))
            elif b_in_a and not a_in_b:
                edges.add((b, a)); containment.append((b, a))
            else:
                partial.append((a, b, n))  # earlier-declared wins: no edge, order is kept

    # Kahn's algorithm, always taking the earliest-declared ready region, so unconstrained regions keep
    # their declaration order and a winner moves ahead of its losers only as far as it has to.
    losers_of: Dict[str, List[str]] = {i: [] for i in ids}
    indegree = {i: 0 for i in ids}
    for w, l in edges:
        losers_of[w].append(l)
        indegree[l] += 1
    heap = [index[i] for i in ids if indegree[i] == 0]
    heapq.heapify(heap)
    order: List[str] = []
    while heap:
        cur = ids[heapq.heappop(heap)]
        order.append(cur)
        for l in losers_of[cur]:
            indegree[l] -= 1
            if indegree[l] == 0:
                heapq.heappush(heap, index[l])
    if len(order) != len(ids):
        stuck = sorted(i for i in ids if i not in set(order))
        raise InvalidWorldSpecError(f"Region precedence contains a cycle among {stuck}")

    ordered = [by_id[i] for i in order]
    owned: Dict[str, int] = {}
    claimed: Set[Tuple[int, int]] = set()
    for r in ordered:
        t = _tiles(r.bounds)
        owned[r.id] = len(t - claimed)
        claimed |= t
    empty = [r_id for r_id, n in owned.items() if n == 0]
    if empty:
        raise InvalidWorldSpecError(
            f"Region(s) {empty} own no tile under the resolved precedence order: a declared region that contains "
            f"nothing breaks LOC-01/LOC-03. Fix the declaration or the geometry."
        )
    # report (earlier, later) in FINAL order for the partial overlaps
    pos = {r_id: n for n, r_id in enumerate(order)}
    partial = [(a, b, n) if pos[a] < pos[b] else (b, a, n) for a, b, n in partial]
    return ordered, PrecedenceReport(partial, containment, owned)
