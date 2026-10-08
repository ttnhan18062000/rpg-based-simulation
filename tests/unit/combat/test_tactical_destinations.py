"""Retreat / stalemate-break destinations are region-contained, never a sentinel coordinate.

Governing Rules: MOV-01, LOC-01, LOC-03, MOV-03 (docs/world_rules/space-environment/).
Each branch test asserts non-empty inputs before any containment check, and fails on the old
literal-(0.0, 0.0) code: the regions used here all start at x,y >= 5, so (0, 0) is outside them.
"""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, RegionState, TaskComponent
from src.engine.tactical import TacticalDecisionSystem
from src.engine.tactical_destinations import (
    RETREAT_STEP,
    WANDER_RADIUS,
    containing_region,
    retreat_destination,
    wander_destination,
)

REGION = RegionState(id="field", name="Field", bounds=(5, 5, 30, 30))
OTHER = RegionState(id="far", name="Far", bounds=(100, 100, 120, 120))


def _entity(eid, faction, hp=100, pos=(10.0, 10.0)):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid)
        .kind("hero" if role == EntityRole.HERO else "monster")
        .location(*pos)
        .identity(role=role, faction=faction)
        .combat(hp=hp, max_hp=100, attack_range=1, readiness=100.0, alive=hp > 0)
        .lifecycle(active=True)
        .build()
    )


def _state(*entities, regions=(REGION,), tick=1):
    return AuthoritativeState(
        tick=tick, seed=42, world_time=tick,
        entities={e.id: e for e in entities},
        regions={r.id: r for r in regions},
    )


def _inside_some_region(state, pos):
    return containing_region(state, pos) is not None


class TestContainingRegion:
    def test_strict_bounds_no_nearest_centre_fallback(self):
        state = _state(regions=(REGION, OTHER))
        assert containing_region(state, (10.0, 10.0)).id == "field"
        # (0, 0) is nearest to "field"'s centre, but outside every region's bounds.
        assert containing_region(state, (0.0, 0.0)) is None

    def test_overlapping_bounds_resolve_by_sorted_id(self):
        a = RegionState(id="a", name="A", bounds=(0, 0, 10, 10))
        b = RegionState(id="b", name="B", bounds=(0, 0, 10, 10))
        assert containing_region(_state(regions=(b, a)), (5.0, 5.0)).id == "a"


class TestRetreatDestination:
    def test_moves_away_from_threat_and_stays_in_region(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(20.0, 20.0))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 18.0))
        state = _state(me, foe)
        dest = retreat_destination(state, me, [foe])
        assert dest == (20.0, 20.0 + RETREAT_STEP)
        assert _inside_some_region(state, dest)

    def test_clamps_to_region_bounds(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(20.0, 28.0))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 26.0))
        state = _state(me, foe)
        assert retreat_destination(state, me, [foe]) == (20.0, 30.0)

    def test_cornered_holds_when_no_home_region(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(20.0, 30.0))  # on the far edge already
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 28.0))
        assert retreat_destination(_state(me, foe), me, [foe]) is None

    def test_no_threat_vector_holds(self):
        me = _entity(1, Faction.HERO_GUILD)
        assert retreat_destination(_state(me), me, []) is None

    def test_home_region_used_when_set_and_no_away_vector(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(20.0, 30.0))
        me = replace(me, strategic=replace(me.strategic, home_region_id="far"))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 28.0))
        state = _state(me, foe, regions=(REGION, OTHER))
        assert retreat_destination(state, me, [foe]) == OTHER.center

    def test_entity_outside_every_region_gets_no_away_vector(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(0.0, 0.0))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(1.0, 1.0))
        assert retreat_destination(_state(me, foe), me, [foe]) is None


class TestWanderDestination:
    def test_nearby_contained_and_seeded(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(20.0, 20.0))
        state = _state(me)
        dest = wander_destination(state, me)
        assert _inside_some_region(state, dest)
        assert abs(dest[0] - 20.0) <= WANDER_RADIUS and abs(dest[1] - 20.0) <= WANDER_RADIUS
        assert dest == wander_destination(state, me)  # same inputs, same answer

    def test_varies_with_tick_and_entity(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(20.0, 20.0))
        other = _entity(2, Faction.HERO_GUILD, pos=(20.0, 20.0))
        a = wander_destination(_state(me, other, tick=1), me)
        assert a != wander_destination(_state(me, other, tick=2), me)
        assert a != wander_destination(_state(me, other, tick=1), other)

    def test_outside_every_region_holds(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(0.0, 0.0))
        assert wander_destination(_state(me), me) is None


class TestBranchesNeverTargetTheOrigin:
    """Through evaluate_entity_intent: each previously-literal branch, on a region-bearing state."""

    def _assert_in_region(self, state, update, reason):
        assert update.task.payload_set["reason"] == reason
        target = update.task.payload_set["target_position"]
        assert target == update.navigation.target_set
        assert target != (0.0, 0.0)
        assert _inside_some_region(state, target)

    def test_low_hp_engaged_retreat(self):
        me = _entity(1, Faction.HERO_GUILD, hp=10, pos=(20.0, 20.0))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 21.0))
        state = _state(me, foe)
        assert state.entities  # non-vacuous
        self._assert_in_region(state, TacticalDecisionSystem.evaluate_entity_intent(state, me), "PANIC_RETREAT")

    def test_panic_gate_retreat(self):
        # hp < 10% adds 0.8 panic, tripping emotion.is_fleeing before the hostile scan.
        me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(20.0, 20.0))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 21.0))
        state = _state(me, foe)
        assert state.entities
        self._assert_in_region(state, TacticalDecisionSystem.evaluate_entity_intent(state, me), "PANIC_RETREAT")

    def test_stalemate_break(self):
        me = _entity(1, Faction.HERO_GUILD, pos=(20.0, 20.0))
        me = replace(me, task=TaskComponent(payload={"target_id": 2, "stale_ticks": 11}))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 23.0))  # not adjacent: the breaker is for chases (CONFLICT-04)
        state = _state(me, foe)
        assert state.entities
        self._assert_in_region(state, TacticalDecisionSystem.evaluate_entity_intent(state, me), "STALEMATE_BREAK")

    def test_entity_outside_every_region_holds_instead_of_going_to_origin(self):
        me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(50.0, 50.0))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(50.0, 51.0))
        state = _state(me, foe)
        update = TacticalDecisionSystem.evaluate_entity_intent(state, me)
        assert update.task.payload_set["target_position"] == (50.0, 50.0)
