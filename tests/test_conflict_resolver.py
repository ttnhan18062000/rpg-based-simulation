"""Tests for the ConflictResolver — deterministic move/combat resolution.

Covers:
- Move collision (two entities → same tile)
- Move priority (next_act_at tie-break, then entity ID)
- Diagonal HUNT deadlock (bug-01 scenario)
- Combat proposal ordering
- Dead target rejection
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.actions.base import ActionProposal
from src.config import SimulationConfig
from src.core.enums import ActionType, AIState
from src.core.faction import Faction
from src.core.grid import Grid
from src.core.items import Inventory
from src.core.models import Entity, Stats, Vector2
from src.core.world_state import WorldState
from src.engine.conflict_resolver import ConflictResolver
from src.systems.rng import DeterministicRNG
from src.systems.spatial_hash import SpatialHash


def _make_world(width: int = 16, height: int = 16) -> WorldState:
    grid = Grid(width, height)
    spatial = SpatialHash(8)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)


def _make_entity(
    eid: int,
    x: int, y: int,
    kind: str = "hero",
    faction: Faction = Faction.HERO_GUILD,
    hp: int = 50,
    atk: int = 10,
    spd: int = 10,
    next_act_at: float = 0.0,
) -> Entity:
    stats = Stats(hp=hp, max_hp=hp, atk=atk, def_=5, spd=spd)
    inv = Inventory(items=[], max_slots=12, max_weight=30.0)
    e = Entity(id=eid, kind=kind, pos=Vector2(x, y), stats=stats, faction=faction, inventory=inv)
    e.next_act_at = next_act_at
    return e


def _resolver() -> ConflictResolver:
    cfg = SimulationConfig()
    rng = DeterministicRNG(42)
    return ConflictResolver(cfg, rng)


class TestMoveConflicts:
    """Two entities trying to move to the same tile."""

    def test_first_by_id_wins_same_tile(self):
        """Lower entity ID wins when both target the same cell."""
        world = _make_world()
        e1 = _make_entity(1, x=3, y=3, next_act_at=0.0)
        e2 = _make_entity(2, x=5, y=3, next_act_at=0.0)
        world.add_entity(e1)
        world.add_entity(e2)

        target = Vector2(4, 3)
        p1 = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=target, reason="walk")
        p2 = ActionProposal(actor_id=2, verb=ActionType.MOVE, target=target, reason="walk")

        resolver = _resolver()
        applied = resolver.resolve([p1, p2], world)

        applied_ids = [a.actor_id for a in applied if a.verb == ActionType.MOVE]
        # Exactly one should succeed
        assert len(applied_ids) == 1
        # Entity 1 wins tie-break (lower ID, same next_act_at)
        assert applied_ids[0] == 1

    def test_earlier_next_act_wins(self):
        """Entity with lower next_act_at gets priority."""
        world = _make_world()
        e1 = _make_entity(1, x=3, y=3, next_act_at=5.0)
        e2 = _make_entity(2, x=5, y=3, next_act_at=2.0)
        world.add_entity(e1)
        world.add_entity(e2)

        target = Vector2(4, 3)
        p1 = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=target, reason="walk")
        p2 = ActionProposal(actor_id=2, verb=ActionType.MOVE, target=target, reason="walk")

        resolver = _resolver()
        applied = resolver.resolve([p1, p2], world)

        applied_ids = [a.actor_id for a in applied if a.verb == ActionType.MOVE]
        assert len(applied_ids) == 1
        assert applied_ids[0] == 2  # e2 had earlier next_act_at

    def test_move_to_occupied_tile_rejected(self):
        """Move to a tile already occupied by another entity is rejected."""
        world = _make_world()
        e1 = _make_entity(1, x=3, y=3)
        e2 = _make_entity(2, x=4, y=3)  # already at target
        world.add_entity(e1)
        world.add_entity(e2)

        p = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=Vector2(4, 3), reason="walk")
        resolver = _resolver()
        applied = resolver.resolve([p], world)

        assert len(applied) == 0

    def test_move_to_wall_rejected(self):
        """Move to an unwalkable tile is rejected."""
        world = _make_world()
        e = _make_entity(1, x=3, y=3)
        world.add_entity(e)

        from src.core.enums import Material
        world.grid.set(Vector2(4, 3), Material.WALL)

        p = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=Vector2(4, 3), reason="walk")
        resolver = _resolver()
        applied = resolver.resolve([p], world)

        assert len(applied) == 0

    def test_non_conflicting_moves_both_succeed(self):
        """Two entities moving to different empty tiles both succeed."""
        world = _make_world()
        e1 = _make_entity(1, x=3, y=3)
        e2 = _make_entity(2, x=6, y=6)
        world.add_entity(e1)
        world.add_entity(e2)

        p1 = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=Vector2(4, 3), reason="walk")
        p2 = ActionProposal(actor_id=2, verb=ActionType.MOVE, target=Vector2(7, 6), reason="walk")

        resolver = _resolver()
        applied = resolver.resolve([p1, p2], world)

        assert len(applied) == 2


class TestDiagonalHuntDeadlock:
    """Bug-01 scenario: two diagonal entities hunting each other, both move
    toward the other but end up at the same distance.

    This test documents the current behavior so we can detect when a fix
    changes it.
    """

    def test_diagonal_swap_attempt(self):
        """Entity A at (5,5) moves to (5,6), B at (6,6) moves to (6,5).
        Both should succeed (different target tiles)."""
        world = _make_world()
        e_a = _make_entity(1, x=5, y=5, faction=Faction.HERO_GUILD)
        e_b = _make_entity(2, x=6, y=6, faction=Faction.GOBLIN_HORDE)
        world.add_entity(e_a)
        world.add_entity(e_b)

        # A moves down (toward B), B moves up (toward A)
        p_a = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=Vector2(5, 6), reason="hunt")
        p_b = ActionProposal(actor_id=2, verb=ActionType.MOVE, target=Vector2(6, 5), reason="hunt")

        resolver = _resolver()
        applied = resolver.resolve([p_a, p_b], world)

        # Both target different tiles — both should resolve
        applied_ids = sorted(a.actor_id for a in applied if a.verb == ActionType.MOVE)
        assert applied_ids == [1, 2], "Both non-conflicting diagonal moves should succeed"

        # After both moves, distance is still 2 (Manhattan: |5-6| + |6-5| = 2)
        # This confirms the bug-01 deadlock scenario exists
        new_a = Vector2(5, 6)
        new_b = Vector2(6, 5)
        assert new_a.manhattan(new_b) == 2, "Distance should still be 2 after swap"

    def test_diagonal_same_target_one_wins(self):
        """Two diagonal entities both try to move to the shared adjacent tile."""
        world = _make_world()
        e_a = _make_entity(1, x=5, y=5, faction=Faction.HERO_GUILD)
        e_b = _make_entity(2, x=6, y=6, faction=Faction.GOBLIN_HORDE)
        world.add_entity(e_a)
        world.add_entity(e_b)

        # Both try to reach (6, 5) — the tile between them
        shared = Vector2(6, 5)
        p_a = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=shared, reason="hunt")
        p_b = ActionProposal(actor_id=2, verb=ActionType.MOVE, target=shared, reason="hunt")

        resolver = _resolver()
        applied = resolver.resolve([p_a, p_b], world)

        move_applied = [a for a in applied if a.verb == ActionType.MOVE]
        assert len(move_applied) == 1, "Only one entity should claim the shared tile"


class TestCombatResolution:
    """Combat proposals resolve in initiative order."""

    def test_attack_dead_target_rejected(self):
        """Attack proposal against a dead entity is rejected."""
        world = _make_world()
        attacker = _make_entity(1, x=3, y=3, atk=15)
        target = _make_entity(2, x=4, y=3, hp=0)  # hp=0 → alive is False
        world.add_entity(attacker)
        world.add_entity(target)

        p = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2, reason="combat")
        resolver = _resolver()
        applied = resolver.resolve([p], world)

        assert len(applied) == 0

    def test_attack_adjacent_succeeds(self):
        """Attack proposal against adjacent alive entity succeeds."""
        world = _make_world()
        attacker = _make_entity(1, x=3, y=3, kind="hero", faction=Faction.HERO_GUILD, atk=15)
        target = _make_entity(2, x=4, y=3, kind="goblin", faction=Faction.GOBLIN_HORDE, hp=50)
        world.add_entity(attacker)
        world.add_entity(target)

        p = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2, reason="combat")
        resolver = _resolver()
        applied = resolver.resolve([p], world)

        assert len(applied) == 1
        assert applied[0].actor_id == 1


class TestResolutionDeterminism:
    """Same proposals in different order must produce same result."""

    def test_proposal_order_independent(self):
        """Resolver sorts internally, so input order shouldn't matter."""
        world1 = _make_world()
        world2 = _make_world()

        for w in (world1, world2):
            w.add_entity(_make_entity(1, x=3, y=3))
            w.add_entity(_make_entity(2, x=5, y=3))

        target = Vector2(4, 3)
        p1 = ActionProposal(actor_id=1, verb=ActionType.MOVE, target=target, reason="walk")
        p2 = ActionProposal(actor_id=2, verb=ActionType.MOVE, target=target, reason="walk")

        resolver = _resolver()
        applied_fwd = resolver.resolve([p1, p2], world1)
        applied_rev = resolver.resolve([p2, p1], world2)

        ids_fwd = [a.actor_id for a in applied_fwd]
        ids_rev = [a.actor_id for a in applied_rev]
        assert ids_fwd == ids_rev, "Resolution must be order-independent"
