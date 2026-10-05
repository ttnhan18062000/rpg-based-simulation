"""Region precedence ordering (LOC-08, owner decision 13).

Where region bounds overlap, a contested point belongs to the region with the higher authored precedence. This module
turns a composition's declarations into the **total order** the resolved world carries as the order of its region list;
every consumer (the runtime lookup, terrain paint, the hazard a tile applies) reads that one order, highest precedence
first.

Rules, in force order:
  * a declaration (``winner`` over each id in ``over``) is honoured for the pairs it names, and a composition declaration
    overrides a module declaration for the pair it names;
  * otherwise, if one region's bounds fully contain the other's, the CONTAINED region wins (3a);
  * any other undeclared overlap keeps the resolved declaration order, earlier wins, and is reported as an advisory (3b);
  * a region that owns no tile under the resulting order is an error (3c).
Declarations live with the module (its own regions) and with the composition (``world.yaml``, cross-module), because the
same bare region id can name different bounds in different worlds.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

from src.worldbuilding.schema import InvalidWorldSpecError, RegionSpec

Pair = Tuple[str, str]  # (winner, loser)


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


def _declared_pairs(ids: Sequence[str], declarations: Sequence, module_declarations: Sequence) -> Set[Pair]:
    """The declared (winner, loser) pairs; a composition declaration overrides a module one for its pair. Validated."""
    composition = {(d.winner, loser) for d in declarations for loser in d.over}
    module = {(d.winner, loser) for d in module_declarations for loser in d.over if (loser, d.winner) not in composition}
    known = set(ids)
    for winner, loser in sorted(composition | module):
        for region_id in (winner, loser):
            if region_id not in known:
                raise InvalidWorldSpecError(f"Region precedence names unknown region '{region_id}' (known: {sorted(known)})")
        if winner == loser:
            raise InvalidWorldSpecError(f"Region precedence declares '{winner}' over itself")
    return composition | module


def _implicit_edges(regions: Sequence[RegionSpec], declared: Set[Pair]) -> Tuple[Set[Pair], List[Pair], List[Tuple[str, str, int]]]:
    """3a containment edges and the 3b undeclared partial overlaps, for pairs with no declaration."""
    edges: Set[Pair] = set()
    containment: List[Pair] = []
    partial: List[Tuple[str, str, int]] = []
    for i, a in enumerate(regions):
        for b in regions[i + 1:]:
            n = _overlap_tiles(a.bounds, b.bounds)
            if n == 0 or (a.id, b.id) in declared or (b.id, a.id) in declared:
                continue
            a_inside, b_inside = _contains(b.bounds, a.bounds), _contains(a.bounds, b.bounds)
            if a_inside != b_inside:
                pair = (a.id, b.id) if a_inside else (b.id, a.id)
                edges.add(pair)
                containment.append(pair)
            else:
                partial.append((a.id, b.id, n))  # earlier-declared wins: no edge, order is kept
    return edges, containment, partial


def _topological_order(ids: Sequence[str], edges: Set[Pair]) -> List[str]:
    """Kahn's algorithm taking the earliest-declared ready region, so a winner moves ahead of its losers only as far as it
    has to and unconstrained regions keep their declaration order."""
    index = {r: i for i, r in enumerate(ids)}
    losers_of: Dict[str, List[str]] = {r: [] for r in ids}
    indegree = {r: 0 for r in ids}
    for winner, loser in edges:
        losers_of[winner].append(loser)
        indegree[loser] += 1
    ready = [index[r] for r in ids if indegree[r] == 0]
    heapq.heapify(ready)
    order: List[str] = []
    while ready:
        current = ids[heapq.heappop(ready)]
        order.append(current)
        for loser in losers_of[current]:
            indegree[loser] -= 1
            if indegree[loser] == 0:
                heapq.heappush(ready, index[loser])
    if len(order) != len(ids):
        raise InvalidWorldSpecError(f"Region precedence contains a cycle among {sorted(set(ids) - set(order))}")
    return order


def _owned_tile_counts(ordered: Sequence[RegionSpec]) -> Dict[str, int]:
    owned: Dict[str, int] = {}
    claimed: Set[Tuple[int, int]] = set()
    for region in ordered:
        tiles = _tiles(region.bounds)
        owned[region.id] = len(tiles - claimed)
        claimed |= tiles
    return owned


def order_regions(regions: Sequence[RegionSpec], declarations: Sequence,
                  module_declarations: Sequence = ()) -> Tuple[List[RegionSpec], PrecedenceReport]:
    """Return ``regions`` in resolved precedence order (highest first) and a report.

    ``declarations`` are the composition's (objects with ``winner: str`` and ``over: Sequence[str]``);
    ``module_declarations`` are those a module declared among its own regions, already carrying composition ids
    (namespace prefix applied). Raises ``InvalidWorldSpecError`` for an unknown id, a self-declaration, a precedence
    cycle, or a region that owns no tile.
    """
    ids = [r.id for r in regions]
    by_id = {r.id: r for r in regions}
    declared = _declared_pairs(ids, declarations, module_declarations)
    implicit, containment, partial = _implicit_edges(regions, declared)
    order = _topological_order(ids, declared | implicit)
    ordered = [by_id[r] for r in order]
    owned = _owned_tile_counts(ordered)
    empty = [r for r, n in owned.items() if n == 0]
    if empty:
        raise InvalidWorldSpecError(
            f"Region(s) {empty} own no tile under the resolved precedence order: a declared region that contains "
            f"nothing breaks LOC-01/LOC-03. Fix the declaration or the geometry."
        )
    position = {r: n for n, r in enumerate(order)}
    partial = [(a, b, n) if position[a] < position[b] else (b, a, n) for a, b, n in partial]
    return ordered, PrecedenceReport(partial, containment, owned)


def module_precedence(modules: Mapping[str, Any], refs: Mapping[str, Any]) -> List[Any]:
    """Each module's own ``region_precedence`` declarations, with the namespace prefix its region ids get in the
    composition (``modules`` maps module id to spec, ``refs`` maps module id to its composition ref)."""
    out: List[Any] = []
    for module_id, spec in modules.items():
        ns = refs[module_id].namespace
        prefix = f"{ns}_" if ns else ""
        out.extend(type(d)(winner=f"{prefix}{d.winner}", over=[f"{prefix}{o}" for o in d.over])
                   for d in getattr(spec, "region_precedence", ()))
    return out


def precedence_ordered_regions(regions: Mapping[str, RegionSpec], composition: Any, modules: Mapping[str, Any],
                               refs: Mapping[str, Any]) -> List[RegionSpec]:
    """The assembled regions in resolved precedence order: the order of ``WorldSpec.regions``."""
    return order_regions(list(regions.values()), composition.region_precedence, module_precedence(modules, refs))[0]


def precedence_advisories(regions: Mapping[str, RegionSpec], composition: Any, modules: Mapping[str, Any],
                          refs: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """One ``LOC-08`` assembly-report warning per undeclared partial overlap (3b)."""
    report = order_regions(list(regions.values()), composition.region_precedence, module_precedence(modules, refs))[1]
    return [{"rule_id": "LOC-08", "severity": "WARNING", "path": "regions",
             "message": f"Regions '{a}' and '{b}' partially overlap ({n} tiles) with no declared precedence; "
                        f"'{a}' wins by resolved declaration order (LOC-08 3b)."}
            for a, b, n in report.undeclared_partial_overlaps]


def first_region_at(ordered: Sequence[Any], x: int, y: int) -> Any:
    """The first region of ``ordered`` (resolved precedence order) whose bounds contain tile (x, y), else None.

    ``WorldCompiler`` paints a tile only for the region this returns, so a tile's terrain-owning region is the region the
    runtime lookup (``core.region_resolution.resolve_region_among``) returns for it (LOC-08 refutation test 1).
    """
    for region in ordered:
        x0, y0, x1, y1 = region.bounds
        if x0 <= x <= x1 and y0 <= y <= y1:
            return region
    return None
