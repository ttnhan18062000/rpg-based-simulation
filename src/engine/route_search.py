"""Routes weigh terrain cost (D75 route step, MOV-04, divergence 2.128).

`MovementSystem._route_step` asks this module for the next tile toward a target. The old route (`NavigationSystem.get_next_step`) is the greedy axis-dominant
step: it ignores the terrain. Here a bounded A* over the declared terrain cost (`src/content/terrain_cost.py`) finds the cheapest route; the entity leaves the
greedy way only when that route is CHEAPER than the greedy walk, so on uniform ground the route is exactly the old one.

What it plans over: terrain cost only. Static obstacles (walls, buildings) and other entities are left to the sidestep and reroute ladder in `resolve_move`,
as before. It reads the TRUE terrain map (`state.terrain`), as common knowledge of the land (owner ruling D75/D76): a known shortcut, knowledge-limited routing is a
later step. No hazard enters the weights: the route weighs move cost only.

Bounded: at most `ROUTE_NODE_CAP` nodes are expanded per search. A search that reaches the cap is a FALLBACK to the greedy step and is counted
(`MovementPlanCache.route_fallbacks`). Plans live in `MovementPlanCache` (`route_paths`): a cheaper path is stored whole and followed while the entity stays on
it; a "greedy is as cheap" verdict is stored for the plan lifetime, so a search runs once per leg, not once per step. Deterministic: fixed neighbour order,
ties broken by (f, h, x, y), no hashing of unordered sets.
"""
from __future__ import annotations

import heapq
from typing import Any, Dict, List, Optional, Tuple

from src.content.terrain_cost import (
    DEFAULT_TERRAIN_ID,
    UnknownTerrainError,
    terrain_cost,
)

# The most nodes one search expands (one constant, here). A search that hits it falls back to the greedy step and is counted as a fallback.
ROUTE_NODE_CAP = 3000
# How long (ticks) a stored path or "greedy is as cheap" verdict stays valid.
ROUTE_PLAN_TICKS = 10
# Expired plans are pruned once the store holds more than this many.
ROUTE_PLAN_LIMIT = 5000

Tile = Tuple[int, int]
_NEIGHBOURS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class RoutePlanStore:
    """The route plans and the search counters (the route step's metric events), held on `AuthoritativeState.route_plans` and carried from state to state by
    the apply path. A derived cache: dropping it only costs a new search, and it is outside the state hash.

    `paths`: (entity, goal tile) -> (path or None for "greedy is as cheap", valid_until_tick, tile -> index on the path)."""

    __slots__ = ("paths", "searches", "nodes_expanded", "fallbacks", "detours", "plan_hits")

    def __init__(self) -> None:
        self.paths: Dict[Tuple[int, Tile], Tuple[Optional[List[Tile]], int, Dict[Tile, int]]] = {}
        self.searches = 0
        self.nodes_expanded = 0
        self.fallbacks = 0
        self.detours = 0
        self.plan_hits = 0

    def prune(self, tick: int) -> None:
        """Drop expired plans once the store is large (bounded memory)."""
        if len(self.paths) > ROUTE_PLAN_LIMIT:
            for key in [k for k, v in self.paths.items() if v[1] < tick]:
                del self.paths[key]


def _tile_cost(terrain: Dict[Tile, str], tile: Tile) -> Optional[float]:
    """The declared cost of the tile, or None for an id the catalog does not know (a test wall, say): the route then stays greedy."""
    try:
        return terrain_cost(terrain.get(tile, DEFAULT_TERRAIN_ID))
    except UnknownTerrainError:
        return None


def greedy_walk_cost(terrain: Dict[Tile, str], start: Tile, goal: Tile) -> Optional[float]:
    """The terrain cost of the walk `NavigationSystem.get_next_step` would take (axis-dominant, a tie takes the y axis), obstacles ignored; None if it crosses a tile the catalog does not know."""
    x, y = start
    total = 0.0
    while (x, y) != goal:
        dx, dy = goal[0] - x, goal[1] - y
        if abs(dx) > abs(dy):
            x += 1 if dx > 0 else -1
        else:
            y += 1 if dy > 0 else -1
        c = _tile_cost(terrain, (x, y))
        if c is None:
            return None
        total += c
    return total


def _trace(parent: Dict[Tile, Tile], start: Tile, goal: Tile) -> List[Tile]:
    """The path start -> goal (excluding start) from the parent links."""
    path: List[Tile] = []
    tile = goal
    while tile != start:
        path.append(tile)
        tile = parent[tile]
    path.reverse()
    return path


class _Frontier:
    """The state of one search: cheapest known cost to each tile, parent links, the closed set and the open heap."""

    def __init__(self, terrain: Dict[Tile, str], start: Tile, goal: Tile) -> None:
        self.terrain = terrain
        self.goal = goal
        self.g: Dict[Tile, float] = {start: 0.0}
        self.parent: Dict[Tile, Tile] = {}
        self.closed: set = set()
        h0 = abs(goal[0] - start[0]) + abs(goal[1] - start[1])
        self.heap: List[Tuple[float, int, int, int]] = [(float(h0), h0, start[0], start[1])]

    def relax(self, tile: Tile) -> None:
        """Push each unclosed in-world neighbour of `tile` that a cheaper way reaches (fixed neighbour order)."""
        for dx, dy in _NEIGHBOURS:
            nxt = (tile[0] + dx, tile[1] + dy)
            if nxt in self.closed or nxt not in self.terrain:
                continue
            step_cost = _tile_cost(self.terrain, nxt)
            if step_cost is None:
                continue
            ng = self.g[tile] + step_cost
            if ng < self.g.get(nxt, float("inf")):
                self.g[nxt] = ng
                self.parent[nxt] = tile
                h = abs(self.goal[0] - nxt[0]) + abs(self.goal[1] - nxt[1])
                heapq.heappush(self.heap, (ng + h, h, nxt[0], nxt[1]))


def search(terrain: Dict[Tile, str], start: Tile, goal: Tile, node_cap: int = ROUTE_NODE_CAP) -> Tuple[Optional[List[Tile]], int, bool]:
    """Cheapest route start -> goal over `terrain` cost: (path excluding start, nodes expanded, hit the cap). Only tiles in `terrain` are in the world."""
    fr = _Frontier(terrain, start, goal)
    nodes = 0
    while fr.heap:
        _, _, x, y = heapq.heappop(fr.heap)
        tile = (x, y)
        if tile in fr.closed:
            continue
        if tile == goal:
            return _trace(fr.parent, start, goal), nodes, False
        fr.closed.add(tile)
        nodes += 1
        if nodes >= node_cap:
            return None, nodes, True
        fr.relax(tile)
    return None, nodes, False


def _store(state: Any) -> RoutePlanStore:
    store = getattr(state, "route_plans", None)
    if store is None:
        store = RoutePlanStore()
        object.__setattr__(state, "route_plans", store)
    return store


def route_next_step(entity_id: int, start: Tile, goal: Tile, state: Any) -> Optional[Tile]:
    """The next tile on a cheaper-than-greedy route, or None to take the greedy step (also when the search is over its cap or the map is unknown).
    Plans live in `state.route_plans`; `state.tick` dates them."""
    terrain = getattr(state, "terrain", None)
    if not terrain or start == goal or start not in terrain:
        return None
    store, tick = _store(state), getattr(state, "tick", 0)
    plan = store.paths.get((entity_id, goal))
    if plan is not None and plan[1] >= tick:
        if plan[0] is None:
            store.plan_hits += 1
            return None
        if start in plan[2]:
            store.plan_hits += 1
            idx = plan[2][start]
            return plan[0][idx + 1] if idx + 1 < len(plan[0]) else None
    path, nodes, capped = search(terrain, start, goal)
    store.searches += 1
    store.nodes_expanded += nodes
    store.fallbacks += 1 if capped else 0
    store.prune(tick)
    greedy = greedy_walk_cost(terrain, start, goal)
    if path is None or greedy is None or greedy <= sum(_tile_cost(terrain, t) or 0.0 for t in path) + 1e-9:
        store.paths[(entity_id, goal)] = (None, tick + ROUTE_PLAN_TICKS, {})
        return None
    full = [start] + path
    store.paths[(entity_id, goal)] = (full, tick + ROUTE_PLAN_TICKS, {t: i for i, t in enumerate(full)})
    store.detours += 1
    return path[0]
