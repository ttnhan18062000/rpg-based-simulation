"""Owner decision 32 ("notice and decide"): an unengaged perceived hostile coming adjacent prompts a fresh decision.

The scheduler wakes the brain of an entity beside such a hostile every ADJACENCY_WAKE_COOLDOWN (2) ticks ahead of its cadence; the decision follows
the entity's own combat-engagement verdict toward that target: ignore keeps the walk (a KEEP_WALKING ENTITY_MOVE decision), avoid steps away
(AVOID_HOSTILE, a decided flight), anything else fights as before.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, RegionState, TaskComponent
from src.engine.cadence import SystemCadence
from src.engine.policy import GovernorPolicy
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
from src.engine.candidate_selector import MovementCandidateSelector as MCS
from src.engine.scheduler import ADJACENCY_WAKE_COOLDOWN, DeterministicScheduler
from src.engine.tactical_hold import notice_unengaged_hostile

GOAL = (40.0, 40.0)


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _fighter(eid, pos, faction):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (V2EntityBuilder(eid).kind("hero" if role == EntityRole.HERO else "monster").location(*pos)
            .identity(role=role, faction=faction).combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True)
            .lifecycle(active=True).build())


def _walker(posture=None, target=GOAL, task=None):
    e = _fighter(1, (10.0, 10.0), Faction.HERO_GUILD)
    props = dict(e.identity.properties)
    if posture:
        props["last_combat_posture"], props["last_combat_posture_target"] = posture, 2
    return replace(e, navigation=replace(e.navigation, target=target, movement_mode=MovementMode.PURSUE),
                   identity=replace(e.identity, properties=props), task=task or TaskComponent(work_kind="ENTITY_ACT", payload={}))


def _hostile(pos=(10.0, 11.0), targets_walker=False):
    m = _fighter(2, pos, Faction.MONSTER_HORDE)
    return replace(m, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1} if targets_walker else {}))


def _ents(walker, hostile):
    return {1: walker, 2: hostile}


def test_the_predicate_is_true_for_an_adjacent_unengaged_perceived_hostile_only():
    w = _walker()
    assert MCS.unengaged_adjacent_hostile(w, _ents(w, _hostile())) is True
    assert MCS.unengaged_adjacent_hostile(w, _ents(w, _hostile(targets_walker=True))) is False  # engaged: CONFLICT-04's case
    assert MCS.unengaged_adjacent_hostile(w, _ents(w, _hostile(pos=(11.0, 11.0)))) is False      # diagonal
    assert MCS.unengaged_adjacent_hostile(w, _ents(w, _hostile(pos=(10.0, 14.0)))) is False      # far


def _brain_items(walker, hostile, tick):
    state = AuthoritativeState(tick=tick, seed=1, entities=_ents(walker, hostile))
    items, _dropped = DeterministicScheduler().select_work(state, GovernorPolicy(system_cadence=SystemCadence(strategic_intelligence=10)))
    return [i for i in items if i.owner_id == 1 and i.work_kind == "ENTITY_BRAIN"]


def test_the_scheduler_wakes_the_brain_of_an_entity_beside_an_unengaged_hostile_within_the_cooldown():
    woken_ticks = [t for t in range(1, 1 + 2 * ADJACENCY_WAKE_COOLDOWN) if _brain_items(_walker(), _hostile(), t)]
    assert len(woken_ticks) == 2 and woken_ticks[1] - woken_ticks[0] == ADJACENCY_WAKE_COOLDOWN
    far = [t for t in range(1, 1 + 2 * ADJACENCY_WAKE_COOLDOWN) if _brain_items(_walker(), _hostile(pos=(10.0, 14.0)), t)]
    assert far == []  # without the hostile it waits for its cadence (tick 10 + id parity not in this window)


def test_a_held_move_is_woken_but_an_action_holder_and_an_engaged_pair_are_not():
    held = _walker(task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": GOAL, "reason": "REGROUP"}))
    assert any(_brain_items(held, _hostile(), t) for t in (1, 2))
    attacking = _walker(task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 9}))
    assert not any(_brain_items(attacking, _hostile(), t) for t in (1, 2, 3, 4))
    assert not any(_brain_items(_walker(), _hostile(targets_walker=True), t) for t in (1, 2, 3, 4))


def _state(w, h):
    field = RegionState(id="field", name="Field", bounds=(0, 0, 60, 60))
    return AuthoritativeState(tick=5, seed=1, entities=_ents(w, h), regions={"field": field})


def test_ignore_keeps_the_walk_as_an_entity_move_decision_the_movement_rule_counts():
    w, h = _walker(posture="ignore"), _hostile()
    update = notice_unengaged_hostile(_state(w, h), w, h, [h], None)
    assert update.task.work_kind_set == "ENTITY_MOVE" and update.task.payload_set["reason"] == "KEEP_WALKING"
    assert update.navigation.target_set == GOAL
    assert MCS.movement_target(w, update, _ents(w, h)) == GOAL  # a decision this tick: not blocked
    no_goal = _walker(posture="ignore", target=None)
    plain = notice_unengaged_hostile(_state(no_goal, h), no_goal, h, [h], None)
    assert plain.task is None and plain.navigation is None  # nothing to re-issue: it stays idle and the strategic pass seeds the walk


def test_avoid_steps_away_as_a_decided_flight():
    w, h = _walker(posture="avoid"), _hostile()
    update = notice_unengaged_hostile(_state(w, h), w, h, [h], None)
    assert update.task.payload_set["reason"] == "AVOID_HOSTILE" and update.navigation.movement_mode_set == MovementMode.RETREAT
    held = _walker(task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": GOAL, "reason": "AVOID_HOSTILE"}))
    assert MCS.is_decided_flight(held) is True


@pytest.mark.parametrize("posture", [None, "engage", "probe", "skirmish", "watch", "retreat", "panic_flee", "vengeance_engage"])
def test_any_other_verdict_leaves_the_decision_to_fight_as_before(posture):
    w, h = _walker(posture=posture), _hostile()
    assert notice_unengaged_hostile(_state(w, h), w, h, [h], None) is None


def test_an_engaged_or_non_adjacent_target_is_not_noticed():
    w = _walker(posture="ignore")
    for h in (_hostile(targets_walker=True), _hostile(pos=(10.0, 14.0))):
        assert notice_unengaged_hostile(_state(w, h), w, h, [h], None) is None


def test_a_keep_walking_move_ends_on_arrival_and_not_before():
    arrived = _walker(task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (10.0, 10.0), "reason": "KEEP_WALKING"}))
    en_route = _walker(task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": GOAL, "reason": "KEEP_WALKING"}))
    assert MCS.move_ends_here(arrived, {1: arrived}) is True
    assert MCS.move_ends_here(en_route, {1: en_route}) is False
