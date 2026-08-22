"""Tests for src.rendering.connectivity's BFS whole-map walkable-region analysis.

TCK-20260821-VISUAL-CONNECTIVITY-METRIC. Synthetic-fixture tests use plain
terrain/blocked_tiles dict/set fixtures directly (no AuthoritativeState construction
needed — analyze_connectivity is pure geometry over just those two fields). The final
test loads the real dungeon_crawl corpus world to reproduce documented evidence.
"""
from __future__ import annotations

from src.rendering.connectivity import analyze_connectivity
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository


def test_connected_map_is_one_component_fully_reachable():
    terrain = {(x, y): "PLAIN" for x in range(5) for y in range(5)}
    blocked_tiles: set[tuple[int, int]] = set()

    result = analyze_connectivity(terrain, blocked_tiles)

    assert result.walkable_count == 25
    assert result.component_count == 1
    # Single component: percent_reachable = (largest component / total walkable) * 100 = 100.0
    assert result.percent_reachable == 100.0


def test_two_disconnected_islands_reports_correct_component_count():
    terrain: dict[tuple[int, int], str] = {}
    # Island A: 3x3 block at x in [0, 2]
    for x in range(3):
        for y in range(3):
            terrain[(x, y)] = "PLAIN"
    # WALL barrier column at x == 3 separates the two islands
    for y in range(3):
        terrain[(3, y)] = "WALL"
    # Island B: 3x3 block at x in [4, 6]
    for x in range(4, 7):
        for y in range(3):
            terrain[(x, y)] = "PLAIN"
    blocked_tiles: set[tuple[int, int]] = set()

    result = analyze_connectivity(terrain, blocked_tiles)

    assert result.component_count == 2
    assert result.walkable_count == 18
    # Dominant-region formula: largest component / total walkable. Equal-size islands (9/9)
    # exercise the tie case via max()/component_sizes[0]: (9 / 18) * 100.0 == 50.0
    assert result.percent_reachable == 50.0


def test_three_disconnected_islands_reports_correct_component_count():
    terrain: dict[tuple[int, int], str] = {}
    # Island A: 3x3 block (9 tiles) at x in [0, 2]
    for x in range(3):
        for y in range(3):
            terrain[(x, y)] = "PLAIN"
    terrain[(3, 0)] = "WALL"
    terrain[(3, 1)] = "WALL"
    terrain[(3, 2)] = "WALL"
    # Island B: 3x2 block (6 tiles) at x in [4, 6]
    for x in range(4, 7):
        for y in range(2):
            terrain[(x, y)] = "PLAIN"
    terrain[(7, 0)] = "WALL"
    terrain[(7, 1)] = "WALL"
    # Island C: single column (3 tiles) at x == 8
    for y in range(3):
        terrain[(8, y)] = "PLAIN"
    blocked_tiles: set[tuple[int, int]] = set()

    result = analyze_connectivity(terrain, blocked_tiles)

    assert result.component_count == 3
    assert result.walkable_count == 18
    # Dominant-region formula, largest island's share: (9 / 18) * 100.0 == 50.0
    assert result.percent_reachable == 50.0


def test_blocked_tiles_alone_can_fragment_connectivity():
    # No WALL terrain anywhere: proves blocked_tiles alone (not terrain) is consulted.
    terrain = {(x, y): "PLAIN" for x in range(5) for y in range(3)}
    blocked_tiles = {(2, 0), (2, 1), (2, 2)}

    result = analyze_connectivity(terrain, blocked_tiles)

    assert result.component_count >= 2
    assert result.walkable_count == 15 - len(blocked_tiles)


def test_does_not_mutate_authoritative_state():
    terrain = {(x, y): "PLAIN" for x in range(4) for y in range(4)}
    terrain[(1, 1)] = "WALL"
    blocked_tiles = {(2, 2)}

    terrain_before = dict(terrain)
    blocked_before = set(blocked_tiles)

    result_1 = analyze_connectivity(terrain, blocked_tiles)
    result_2 = analyze_connectivity(terrain, blocked_tiles)

    assert result_1 == result_2
    assert terrain == terrain_before
    assert blocked_tiles == blocked_before


def test_dungeon_crawl_matches_documented_evidence():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state, _report = WorldCompiler.compile(spec, seed=42)

    result = analyze_connectivity(state.terrain, state.blocked_tiles)

    assert result.walkable_count == 15245
    assert result.component_count == 1
    assert result.percent_reachable == 100.0
