"""D75 route step (divergence 2.128): a bounded A* over the declared terrain cost; the route leaves the greedy way only when it is cheaper."""
from __future__ import annotations

from src.engine import route_search
from src.engine.route_search import RoutePlanStore as MovementPlanCache


class _State:
    def __init__(self, terrain, cache, tick):
        self.terrain = terrain
        self.route_plans = cache
        self.tick = tick


def _grid(w, h, default="plain", **rows):
    t = {(x, y): default for x in range(w) for y in range(h)}
    return t


def _step(terrain, start, goal, cache=None, tick=0, eid=1):
    cache = cache or MovementPlanCache()
    return route_search.route_next_step(eid, start, goal, _State(terrain, cache, tick)), cache


def test_uniform_ground_takes_the_greedy_way():
    step, cache = _step(_grid(20, 20), (0, 0), (10, 4))
    assert step is None
    assert cache.detours == 0


def test_a_road_beside_a_slow_line_is_preferred():
    # the greedy walk from (0,0) to (10,0) runs along y=0 over swamp (3.0 a tile); a road along y=1 costs 0.5 a tile
    t = _grid(12, 3)
    for x in range(12):
        t[(x, 0)] = "swamp"
        t[(x, 1)] = "road"
    step, cache = _step(t, (0, 0), (10, 0))
    assert step == (0, 1)
    assert cache.detours == 1


def test_a_wide_mountain_ridge_is_walked_around():
    t = _grid(16, 12)
    for x in range(5, 10):
        for y in range(0, 6):
            t[(x, y)] = "mountain"
    step, cache = _step(t, (3, 3), (12, 3))
    assert step is not None and cache.detours == 1
    path, _, capped = route_search.search(t, (3, 3), (12, 3))
    assert not capped and all(t[p] != "mountain" for p in path)


def test_the_cap_falls_back_to_the_greedy_step_and_is_counted(monkeypatch):
    t = _grid(40, 40)
    for x in range(40):
        t[(x, 0)] = "swamp"
        t[(x, 1)] = "road"
    monkeypatch.setattr(route_search, "ROUTE_NODE_CAP", 5)
    monkeypatch.setattr(route_search, "search", lambda terrain, s, g, node_cap=5: (None, 5, True))
    step, cache = _step(t, (0, 0), (30, 0))
    assert step is None
    assert cache.fallbacks == 1 and cache.searches == 1


def test_a_stored_detour_is_followed_without_a_new_search():
    t = _grid(12, 3)
    for x in range(12):
        t[(x, 0)] = "swamp"
        t[(x, 1)] = "road"
    cache = MovementPlanCache()
    s1, _ = _step(t, (0, 0), (10, 0), cache=cache, tick=0)
    assert s1 == (0, 1) and cache.searches == 1
    s2, _ = _step(t, (0, 1), (10, 0), cache=cache, tick=1)
    assert s2 == (1, 1) and cache.searches == 1 and cache.plan_hits == 1


def test_the_verdict_greedy_is_as_cheap_is_stored_too():
    cache = MovementPlanCache()
    t = _grid(20, 20)
    _step(t, (0, 0), (10, 4), cache=cache, tick=0)
    _step(t, (1, 0), (10, 4), cache=cache, tick=1)
    assert cache.searches == 1 and cache.plan_hits == 1


def test_an_unknown_map_takes_the_greedy_step():
    step, cache = _step({}, (0, 0), (5, 5))
    assert step is None and cache.searches == 0


def test_the_search_is_deterministic():
    t = _grid(15, 15)
    for x in range(15):
        t[(x, 7)] = "road"
    a = route_search.search(t, (0, 0), (14, 14))
    b = route_search.search(t, (0, 0), (14, 14))
    assert a == b


def test_the_route_costs_no_more_than_the_greedy_walk():
    t = _grid(15, 15)
    for y in range(15):
        t[(7, y)] = "swamp"
    path, _, _ = route_search.search(t, (0, 7), (14, 7))
    cost = sum(route_search._tile_cost(t, p) for p in path)
    assert cost <= route_search.greedy_walk_cost(t, (0, 7), (14, 7)) + 1e-9
