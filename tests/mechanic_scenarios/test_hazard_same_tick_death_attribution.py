"""TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND (scripted H-series).

Death attribution rule (Mechanics Bible 01 §4, "Death Attribution (Same-Tick Causes)"): a death
records the first cause, in pipeline phase order, whose own effect was sufficient to take the subject
from hp > 0 to hp <= 0. Combat resolves before world dynamics, which resolves before the lifecycle
phase. All scenarios are scripted (not the live corpus world, whose population varies run to run).
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.lifecycle_systems.lifecycle import LifecycleSystem
from src.systems.world_systems.generator import EntityGenerator

DRAIN = 10  # hazard_level 1.0 -> int(1.0 * 10)


def _state(hp, hazard_level=1.0, tick=5):
    ent = (
        V2EntityBuilder(1).kind("goblin").location(0.0, 0.0)
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
        .combat(hp=hp, max_hp=100)
        .lifecycle(active=True, age_ticks=0, max_age_ticks=100_000)
        .build()
    )
    region = RegionState(id="r1", name="R", bounds=(-5, -5, 5, 5), hazard_level=hazard_level,
                         hazard_kind="ARCANE_CORRUPTION")
    return AuthoritativeState(tick=tick, seed=42, entities={1: ent}, regions={"r1": region})


def _pipeline(state, combat=None):
    """world_dynamics -> resolve_lifecycle -> apply, in the pipeline's declared phase order."""
    ups = {1: EntityUpdate(entity_id=1, combat=combat)} if combat is not None else {}
    refined = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(entity_updates=ups), EntityGenerator(42))
    refined = LifecycleSystem.resolve_lifecycle(state, refined)
    return refined, ApplyPath.apply_generation(state, refined)


def test_combat_kill_plus_hazard_records_the_combat_death_and_keeps_hazard_observable():
    state = _state(hp=3)
    kill = CombatUpdate(hp_delta=-3, alive_set=False, outcome_kind="KILL", attacker_id=9, damage_taken=3)
    refined, nxt = _pipeline(state, kill)
    c = refined.entity_updates[1].combat
    assert c.outcome_kind == "KILL"  # never overwritten by HAZARD
    assert c.hazard_damage == DRAIN  # hazard application still carried independently
    assert c.attacker_id == 9
    life = nxt.entities[1].lifecycle
    assert life.death_reason == "COMBAT" and life.is_permadeath is True and life.active is False


def test_combat_non_lethal_plus_decisive_hazard_records_hazard():
    state = _state(hp=12)
    survive = CombatUpdate(hp_delta=-3, alive_set=True, outcome_kind="SURVIVE", attacker_id=9, damage_taken=3)
    refined, nxt = _pipeline(state, survive)
    assert refined.entity_updates[1].combat.outcome_kind == "HAZARD"
    assert refined.entity_updates[1].combat.alive_set is False
    life = nxt.entities[1].lifecycle
    assert life.death_reason == "HAZARD" and life.is_permadeath is True and life.active is False
    assert nxt.entities[1].combat.hp == 0  # 12 - 3 - 10 floors at 0


def test_terminal_defeat_plus_hazard_keeps_the_defeat_classification():
    state = _state(hp=3)
    defeat = CombatUpdate(hp_delta=-3, alive_set=False, outcome_kind="DEFEAT", attacker_id=9)
    refined, nxt = _pipeline(state, defeat)
    assert refined.entity_updates[1].combat.outcome_kind == "DEFEAT"
    assert nxt.entities[1].lifecycle.death_reason == "DEFEAT"


def test_hazard_only_lethal_drain_is_recorded_and_deactivated_not_a_zombie():
    state = _state(hp=DRAIN)
    refined, nxt = _pipeline(state)
    assert refined.entity_updates[1].combat.outcome_kind == "HAZARD"
    ent = nxt.entities[1]
    assert ent.combat.hp == 0
    assert ent.lifecycle.active is False and ent.lifecycle.death_reason == "HAZARD"
    assert ent.lifecycle.death_tick is not None and ent.lifecycle.is_permadeath is True
    # a later life-due tick must not resurrect or re-classify the corpse
    again = ApplyPath.apply_generation(nxt, LifecycleSystem.resolve_lifecycle(nxt, StateUpdate()))
    assert again.entities[1].lifecycle.active is False
    assert again.entities[1].lifecycle.death_reason == "HAZARD"


def test_hazard_only_non_lethal_drain_keeps_the_hazard_discriminant_and_records_no_death():
    state = _state(hp=50)
    refined, nxt = _pipeline(state)
    c = refined.entity_updates[1].combat
    assert c.outcome_kind == "HAZARD" and c.hazard_damage == DRAIN and c.alive_set is True
    assert nxt.entities[1].lifecycle.active is True and nxt.entities[1].lifecycle.death_reason is None
    assert nxt.entities[1].combat.hp == 40


def test_hazardous_region_without_drain_never_produces_a_hazard_death():
    """LIMIT-04: being in a hazardous region is not a cause; only a nonzero drain is."""
    state = _state(hp=1, hazard_level=0.0)
    refined, nxt = _pipeline(state)
    assert 1 not in refined.entity_updates or refined.entity_updates[1].combat is None
    assert nxt.entities[1].lifecycle.death_reason is None


def test_hazard_never_flips_alive_set_false_back_to_true():
    state = _state(hp=100)  # arithmetic leaves HP positive after the 10 drain
    already = CombatUpdate(hp_delta=0, alive_set=False, outcome_kind="SURVIVE")
    refined = WorldDynamicsSystem.resolve_dynamics(
        state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=already)}), EntityGenerator(42))
    assert refined.entity_updates[1].combat.alive_set is False


def test_hazard_arithmetic_is_not_double_counted_with_combat_hp_delta():
    state = _state(hp=50)
    survive = CombatUpdate(hp_delta=-7, alive_set=True, outcome_kind="SURVIVE", attacker_id=9)
    refined, nxt = _pipeline(state, survive)
    assert refined.entity_updates[1].combat.hp_delta == -7 - DRAIN
    assert nxt.entities[1].combat.hp == 50 - 7 - DRAIN


def test_world_dynamics_does_not_mutate_the_input_state():
    state = _state(hp=DRAIN)
    before = state.entities[1]
    _pipeline(state)
    assert state.entities[1] is before and state.entities[1].combat.hp == DRAIN
    assert state.entities[1].lifecycle.active is True


def test_terminal_outcome_set_is_the_learning_layers_defeated_set():
    from src.core.combat_constants import TERMINAL_COMBAT_OUTCOME_KINDS
    from src.domains.combat_engagement.learning_outcome import _DEFEATED_OUTCOME_KINDS
    assert set(TERMINAL_COMBAT_OUTCOME_KINDS) == set(_DEFEATED_OUTCOME_KINDS)
