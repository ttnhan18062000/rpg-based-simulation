"""TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE (owner decision memo row 88).

A hostile acts on a subject only by an act: its current task attacks or pursues the subject, or it took hp from the subject by a hit inside one brain cadence.
Wounded, adjacent, closing without an act and outmatched are AGENCY-07 reasons that flight is warranted; they are not acts. `last_hit_tick` is the typed tick
of the last hit, written with `last_attacker_id` and hashed with it.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, TaskComponent
from src.core.updates import CombatUpdate, EntityUpdate
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.scheduler import NEED_WAKE_CADENCE
from src.engine.tactical_threat import ThreatTerm, hostile_acts_on, present_threat_terms

TICK = 500


def _subject(**combat):
    return V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(hp=100, max_hp=100, alive=True, **combat).build()


def _hostile(task=None, mode=MovementMode.WANDER, at=(1.0, 0.0)):
    h = (V2EntityBuilder(2).kind("monster").location(*at).identity(faction=Faction.MONSTER_HORDE)
         .combat(hp=100, max_hp=100, alive=True, readiness=100.0).navigation(movement_mode=mode).build())
    return replace(h, task=task) if task is not None else h


def _acts(hostile, subject=None, tick=TICK):
    return hostile_acts_on(hostile, subject or _subject(), tick)


# ---- (a) the typed work ---------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("action", ["ATTACK", "SKILL"])
def test_an_attack_act_aimed_at_the_subject_acts(action):
    assert _acts(_hostile(TaskComponent(work_kind="ENTITY_ACT", payload={"action": action, "target_id": 1})))


@pytest.mark.parametrize("mode", [MovementMode.PURSUE, MovementMode.INTERCEPT])
def test_a_pursuit_or_intercept_aimed_at_the_subject_acts(mode):
    assert _acts(_hostile(TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (0.0, 0.0), "target_id": 1}), mode=mode))


def test_bracketing_acts_only_when_its_typed_target_is_the_subject():
    task = lambda target: TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (2.0, 2.0), "reason": "BRACKETING", "target_id": target})
    assert _acts(_hostile(task(1), mode=MovementMode.REPOSITION))
    assert not _acts(_hostile(task(9), mode=MovementMode.REPOSITION))


def test_an_attack_aimed_at_someone_else_does_not_act_on_the_subject():
    assert not _acts(_hostile(TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 9})))


@pytest.mark.parametrize("task,mode", [
    (TaskComponent(work_kind="ENTITY_ACT", payload={"action": "HOLD", "reason": "WATCH_HOSTILE", "target_id": 1}), MovementMode.WANDER),
    (TaskComponent(work_kind="ENTITY_ACT", payload={"action": "HOLD", "reason": "HOLD_CHOKEPOINT", "target_id": 1}), MovementMode.HOLD),
    (TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (0.0, 0.0), "reason": "KITING", "target_id": 1}), MovementMode.RETREAT),
    (TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (0.0, 0.0), "reason": "SEEK_COVER", "target_id": 1}), MovementMode.REPOSITION),
    (TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (0.0, 0.0), "reason": "GUARDING_ALLY", "target_id": 1}), MovementMode.GUARD),
    (TaskComponent(work_kind="ENTITY_ACT", payload={"action": "INTERACT", "target_id": 1}), MovementMode.WANDER),
])
def test_a_bare_target_id_on_watching_guarding_kiting_cover_or_holds_is_not_an_act(task, mode):
    assert not _acts(_hostile(task, mode=mode))


def test_a_stale_attack_task_still_counts_until_the_hostiles_next_decision():
    """A known property (memo row 88 item 5): a task kept current counts with no reach test, at most one decision late (the lag class of C5)."""
    far = _hostile(TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1}), at=(9.0, 0.0))
    assert _acts(far)


# ---- the states are not acts ---------------------------------------------------------------------------------------------------------------------

def test_wounded_adjacent_closing_and_outmatched_are_threat_terms_but_not_acts():
    subject = replace(_subject(), combat=replace(_subject().combat, hp=30, max_hp=100))
    hostile = replace(_hostile(at=(1.0, 0.0)), navigation=replace(_hostile().navigation, last_position=(4.0, 0.0)),
                      combat=replace(_hostile().combat, atk=80, max_hp=400, hp=400))
    terms = present_threat_terms(subject, [hostile])
    assert {ThreatTerm.WOUNDED, ThreatTerm.ADJACENT, ThreatTerm.CLOSING, ThreatTerm.OUTMATCHED} <= set(terms)
    assert not hostile_acts_on(hostile, subject, TICK)


# ---- (b) the hit window ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("ago,expected", [(0, True), (NEED_WAKE_CADENCE, True), (NEED_WAKE_CADENCE + 1, False)])
def test_a_hit_by_the_hostile_acts_for_one_brain_cadence(ago, expected):
    subject = _subject()
    subject = replace(subject, combat=replace(subject.combat, last_attacker_id=2, last_hit_tick=TICK - ago))
    assert _acts(_hostile(), subject) is expected


def test_a_hit_by_another_body_does_not_make_this_hostile_act():
    subject = _subject()
    subject = replace(subject, combat=replace(subject.combat, last_attacker_id=99, last_hit_tick=TICK))
    assert not _acts(_hostile(), subject)


def test_a_never_hit_subject_has_no_last_hit():
    assert _subject().combat.last_hit_tick is None
    assert not _acts(_hostile())


# ---- last_hit_tick: written by the patch with its attacker, hashed ---------------------------------------------------------------------------

def _apply(entity, combat_update):
    return ApplyPath._apply_entity_update(entity, EntityUpdate(entity_id=entity.id, combat=combat_update))


def test_a_damaging_hit_writes_the_attacker_and_the_tick_together():
    hit = _apply(_subject(), CombatUpdate(damage_taken=5, hp_delta=-5, attacker_id=2, hit_tick_set=TICK))
    assert (hit.combat.last_attacker_id, hit.combat.last_hit_tick) == (2, TICK)


def test_a_zero_damage_or_attackerless_update_leaves_the_last_hit_alone():
    base = _apply(_subject(), CombatUpdate(damage_taken=5, hp_delta=-5, attacker_id=2, hit_tick_set=TICK))
    for update in (CombatUpdate(hp_delta=-3, hazard_damage=3), CombatUpdate(attacker_id=7, outcome_kind="REJECTED", hit_tick_set=TICK + 5)):
        after = _apply(base, update)
        assert (after.combat.last_attacker_id, after.combat.last_hit_tick) == (2, TICK)


def test_the_combat_resolution_stamps_the_tick_of_the_hit():
    from src.engine.combat import CombatResolutionSystem

    attacker = replace(_hostile(), combat=replace(_hostile().combat, atk=50))
    state = AuthoritativeState(tick=TICK, seed=1, entities={1: _subject(), 2: attacker})
    update = CombatResolutionSystem.resolve_attack(attacker, state.entities[1], state)
    assert update.damage_taken > 0 and update.attacker_id == 2 and update.hit_tick_set == TICK


def test_last_hit_tick_is_canonical_state_and_in_the_proof_digest():
    """Typed durable state, emitted in the canonical dict (None when never hit), and hashed by the v3 proof digest
    (TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS; it was excluded under v2 by perf ruling PERF-D5 (ii))."""
    never = _subject()
    assert never.combat.to_canonical_dict()["last_hit_tick"] is None
    hit = replace(never, combat=replace(never.combat, last_hit_tick=TICK))
    assert hit.combat.to_canonical_dict()["last_hit_tick"] == TICK

    def digest(entity):
        return CanonicalStateHasher.get_hash(AuthoritativeState(tick=3, seed=1, entities={1: entity}))

    assert digest(hit) != digest(never)  # changing last_hit_tick alone changes get_hash
    assert CanonicalStateHasher.to_canonical_data(AuthoritativeState(tick=3, seed=1, entities={1: hit}))["entities"]["1"]["combat"]["last_hit_tick"] == TICK


def test_last_hit_tick_survives_a_scenario_checkpoint_round_trip():
    """The checkpoint pickles the state, so the excluded-from-digest field is still carried across save and restore."""
    import pickle

    subject = replace(_subject(), combat=replace(_subject().combat, last_attacker_id=2, last_hit_tick=TICK))
    state = AuthoritativeState(tick=3, seed=1, entities={1: subject})
    restored = pickle.loads(pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL))
    assert (restored.entities[1].combat.last_attacker_id, restored.entities[1].combat.last_hit_tick) == (2, TICK)
