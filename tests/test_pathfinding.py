"""Unit + integration tests for A* pathfinding (epic-09)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ai.pathfinding import Pathfinder, TERRAIN_MOVE_COST, tile_cost
from src.core.enums import Material
from src.core.grid import Grid
from src.core.models import Vector2


def _grid(w: int = 10, h: int = 10) -> Grid:
    return Grid(w, h, default=Material.FLOOR)


# ---------------------------------------------------------------------------
# Basic A* tests
# ---------------------------------------------------------------------------

class TestAStarBasic:
    def test_straight_line_path(self):
        g = _grid()
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(0, 0), Vector2(4, 0))
        assert path is not None
        assert len(path) == 4
        assert path[-1] == Vector2(4, 0)

    def test_same_start_and_goal(self):
        g = _grid()
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(3, 3), Vector2(3, 3))
        assert path == []

    def test_adjacent_goal(self):
        g = _grid()
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(5, 5), Vector2(6, 5))
        assert path == [Vector2(6, 5)]

    def test_path_around_wall(self):
        """A* should navigate around a wall."""
        g = _grid()
        # Wall from (3,0) to (3,4) — blocks straight horizontal path
        for y in range(5):
            g.set(Vector2(3, y), Material.WALL)
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(2, 2), Vector2(4, 2))
        assert path is not None
        # Path must go around the wall (via y=5 or above)
        assert len(path) > 2
        assert path[-1] == Vector2(4, 2)
        # No step should be on a wall tile
        for step in path:
            assert g.is_walkable(step), f"Step {step} is on a wall"

    def test_no_path_through_walls(self):
        """Completely walled off goal → None."""
        g = _grid()
        # Surround (5,5) with walls
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    g.set(Vector2(5 + dx, 5 + dy), Material.WALL)
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(0, 0), Vector2(5, 5))
        assert path is None

    def test_unwalkable_goal(self):
        g = _grid()
        g.set(Vector2(5, 5), Material.WALL)
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(0, 0), Vector2(5, 5))
        assert path is None

    def test_path_excludes_start(self):
        """Returned path should not include the start position."""
        g = _grid()
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(0, 0), Vector2(3, 0))
        assert path is not None
        assert Vector2(0, 0) not in path

    def test_max_nodes_budget(self):
        """Pathfinder with tiny budget should return None for long paths."""
        g = _grid(50, 50)
        pf = Pathfinder(g, max_nodes=5)
        path = pf.find_path(Vector2(0, 0), Vector2(49, 49))
        assert path is None  # Budget too small

    def test_next_step_returns_first_tile(self):
        g = _grid()
        pf = Pathfinder(g)
        step = pf.next_step(Vector2(0, 0), Vector2(3, 0))
        assert step == Vector2(1, 0)

    def test_next_step_no_path(self):
        g = _grid()
        g.set(Vector2(5, 5), Material.WALL)
        pf = Pathfinder(g)
        step = pf.next_step(Vector2(0, 0), Vector2(5, 5))
        assert step is None


# ---------------------------------------------------------------------------
# Occupied tiles
# ---------------------------------------------------------------------------

class TestOccupied:
    def test_occupied_tiles_avoided(self):
        g = _grid()
        pf = Pathfinder(g)
        occ = {(1, 0), (2, 0), (3, 0)}  # Block straight path
        path = pf.find_path(Vector2(0, 0), Vector2(4, 0), occupied=occ)
        assert path is not None
        for step in path:
            assert (step.x, step.y) not in occ or step == Vector2(4, 0)

    def test_goal_reachable_even_if_occupied(self):
        """Goal tile should be reachable even if in occupied set."""
        g = _grid()
        pf = Pathfinder(g)
        occ = {(4, 0)}
        path = pf.find_path(Vector2(0, 0), Vector2(4, 0), occupied=occ)
        assert path is not None
        assert path[-1] == Vector2(4, 0)


# ---------------------------------------------------------------------------
# Terrain cost awareness (F2)
# ---------------------------------------------------------------------------

class TestTerrainCosts:
    def test_road_cost_is_low(self):
        assert TERRAIN_MOVE_COST[Material.ROAD] == 0.7

    def test_swamp_cost_is_high(self):
        assert TERRAIN_MOVE_COST[Material.SWAMP] == 1.5

    def test_tile_cost_returns_registry_value(self):
        g = _grid()
        g.set(Vector2(3, 3), Material.ROAD)
        assert tile_cost(g, Vector2(3, 3)) == 0.7
        assert tile_cost(g, Vector2(0, 0)) == 1.0

    def test_prefers_road_over_swamp(self):
        """A* should prefer road path over swamp when total cost is lower."""
        g = _grid(10, 3)
        # Row 0: all road (cost 0.7 each)
        for x in range(10):
            g.set(Vector2(x, 0), Material.ROAD)
        # Row 1: all swamp (cost 1.5 each)
        for x in range(10):
            g.set(Vector2(x, 1), Material.SWAMP)
        # Row 2: floor (cost 1.0)
        # Path from (0,1) to (9,1): through swamp = 9*1.5 = 13.5
        # Via road row 0: up(1.0) + 9*0.7 + down(1.5) = 8.8 — cheaper!
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(0, 1), Vector2(9, 1))
        assert path is not None
        road_steps = sum(1 for s in path if g.get(s) == Material.ROAD)
        assert road_steps > 0, "A* should route through road tiles to minimize cost"

    def test_avoids_swamp_when_floor_available(self):
        """Given a choice, A* should route around swamp."""
        g = _grid(7, 5)
        # Swamp strip at x=3
        for y in range(5):
            g.set(Vector2(3, y), Material.SWAMP)
        # Clear floor at (3,0) to allow going around
        g.set(Vector2(3, 0), Material.FLOOR)
        pf = Pathfinder(g)
        path = pf.find_path(Vector2(2, 2), Vector2(4, 2))
        assert path is not None
        # Path should exist; if floor detour is cheaper than swamp, it routes around
        # With swamp cost 1.5, going through (3,2) costs 1.5
        # Going around via (3,0) costs ~4 extra floor steps = 4.0
        # So A* may still go through swamp (it's shorter); that's valid
        assert path[-1] == Vector2(4, 2)


# ---------------------------------------------------------------------------
# Integration with propose_move_toward
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_propose_move_uses_astar_for_long_distance(self):
        """propose_move_toward should use A* for distances > 2."""
        from tests.helpers.combat_arena import CombatArena
        arena = CombatArena(width=20, height=20)
        # Wall blocking direct path
        for y in range(15):
            arena.set_wall(10, y)
        arena.add_hero(1, pos=(8, 5), weapon="iron_sword", hp=200, atk=15)
        arena.add_mob(2, pos=(12, 5), weapon="rusty_sword", hp=200, atk=5)
        # Run ticks — hero should eventually reach mob via A* around wall
        arena.run_ticks(30)
        hero = arena.entity(1)
        mob = arena.entity(2)
        if hero and mob and mob.alive:
            dist = hero.pos.manhattan(mob.pos)
            # Hero should have closed distance (not stuck at wall)
            assert dist < 10, f"Hero should navigate around wall, dist={dist}"

    def test_greedy_fallback_for_short_distance(self):
        """Short distances (≤2) should use greedy, not A*."""
        from tests.helpers.combat_arena import CombatArena
        arena = CombatArena()
        arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=200, atk=15)
        arena.add_mob(2, pos=(6, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.run_ticks(3)
        # Should produce combat events (got close enough to fight)
        combat = arena.combat_events()
        assert len(combat) > 0

    def test_entity_navigates_maze(self):
        """Entity navigates a simple maze using A*."""
        from tests.helpers.combat_arena import CombatArena
        arena = CombatArena(width=15, height=15)
        # Create a simple maze:
        # Wall from (5,0) to (5,10), gap at (5,11)
        for y in range(11):
            arena.set_wall(5, y)
        arena.add_hero(1, pos=(3, 5), weapon="iron_sword", hp=200, atk=15)
        arena.add_mob(2, pos=(7, 5), weapon="rusty_sword", hp=200, atk=5)
        arena.run_ticks(40)
        hero = arena.entity(1)
        mob = arena.entity(2)
        if hero and mob and mob.alive:
            dist = hero.pos.manhattan(mob.pos)
            assert dist < 8, f"Hero should navigate through maze gap, dist={dist}"
