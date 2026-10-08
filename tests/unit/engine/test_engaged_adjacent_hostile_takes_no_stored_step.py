"""CONFLICT-04 at the movement layer: leaving an engagement is a decision.

An entity with an engaged, perceived, hostile entity orthogonally adjacent takes no step from a STORED target (an idle walk toward
an objective, a held move) or from a bare per-tick reaffirm of a held move's target; it steps only on a target a decision sets this
tick (a target set together with an ENTITY_MOVE task update). Adjacency to a hostile that is not engaged with it, or only
diagonal, changes nothing. Divergence 2.89.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, TaskComponent
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
from src.engine.candidate_selector import MovementCandidateSelector as MCS

STORED = (40.0, 40.0)


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


def _walker(task_kind="ENTITY_ACT", payload=None):
    e = _fighter(1, (10.0, 10.0), Faction.HERO_GUILD)
    return replace(e, navigation=replace(e.navigation, target=STORED, movement_mode=MovementMode.PURSUE),
                   task=TaskComponent(work_kind=task_kind, payload=dict(payload or {})))


def _hostile(pos=(10.0, 11.0), targets_walker=True):
    m = _fighter(2, pos, Faction.MONSTER_HORDE)
    return replace(m, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1} if targets_walker else {}))


def _target(walker, hostile, update=None):
    ents = {1: walker, 2: hostile}
    return MCS.movement_target(walker, update, ents, MCS.position_index(ents))


DECISION = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(20.0, 20.0)),
                        task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": (20.0, 20.0)}))
REAFFIRM = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=STORED))
STRATEGIC_SEED = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(70.0, 50.0)))


def test_an_idle_walker_beside_an_engaged_hostile_takes_no_step_from_its_stored_target():
    assert _target(_walker(), _hostile()) is None


def test_a_held_regroup_move_beside_an_engaged_hostile_takes_no_step():
    held = _walker("ENTITY_MOVE", {"target_position": STORED, "reason": "REGROUP"})
    assert _target(held, _hostile()) is None


def test_the_executors_bare_reaffirm_and_a_strategic_seed_are_not_decisions():
    held = _walker("ENTITY_MOVE", {"target_position": STORED, "reason": "REGROUP"})
    assert _target(held, _hostile(), REAFFIRM) is None
    assert _target(_walker(), _hostile(), STRATEGIC_SEED) is None


def test_a_decision_this_tick_still_steps():
    assert _target(_walker(), _hostile(), DECISION) == (20.0, 20.0)
    held = _walker("ENTITY_MOVE", {"target_position": STORED, "reason": "REGROUP"})
    assert _target(held, _hostile(), DECISION) == (20.0, 20.0)


def test_the_hostile_naming_the_walker_or_the_walker_naming_the_hostile_both_engage():
    named_by_walker = _walker("ENTITY_MOVE", {"target_id": 2, "target_position": STORED, "reason": "BRACKETING"})
    assert _target(named_by_walker, _hostile(targets_walker=False)) is None


@pytest.mark.parametrize("hostile", [
    _hostile(targets_walker=False),            # adjacent but not engaged: unchanged
    _hostile(pos=(11.0, 11.0)),                # diagonal: not orthogonally adjacent
    _hostile(pos=(10.0, 14.0)),                # far away
], ids=["not-engaged", "diagonal", "far"])
def test_other_neighbours_change_nothing(hostile):
    assert _target(_walker(), hostile) == STORED


def test_a_dead_hostile_changes_nothing():
    dead = _hostile()
    dead = replace(dead, combat=replace(dead.combat, alive=False))
    assert _target(_walker(), dead) == STORED


def test_the_candidate_selector_does_not_offer_the_walker_a_move_but_offers_it_one_without_the_hostile():
    walker = _walker()
    beside = AuthoritativeState(tick=5, seed=1, entities={1: walker, 2: _hostile()})
    alone = AuthoritativeState(tick=5, seed=1, entities={1: walker, 2: _hostile(pos=(10.0, 14.0))})
    assert 1 not in MCS.select(beside, None, [1])
    assert 1 in MCS.select(alone, None, [1])


# --- a decided flight keeps stepping; every other blocked held move is released to the brain ---------------------------------

from types import SimpleNamespace

from src.config.profiles import PROD_SMALL
from src.core.concurrency_law import WorkClass
from src.core.work import WorkItem
from src.engine.executor import LocalSequentialExecutor
from src.engine.worker_logic import default_simulation_worker
from src.platform.rng import DeterministicRNG

FLIGHTS = ("PANIC_RETREAT", "SAFETY_PRESSURE_RETREAT", "LEASH_RETURN")
RELEASED = ("REGROUP", "INTERCEPTING", "BRACKETING", "SEEK_COVER", None)


def _held(reason):
    payload = {"target_position": STORED}
    if reason:
        payload["reason"] = reason
    return _walker("ENTITY_MOVE", payload)


@pytest.mark.parametrize("reason", FLIGHTS)
def test_a_decided_flight_keeps_its_stored_target_steps_beside_an_engaged_hostile(reason):
    assert _target(_held(reason), _hostile()) == STORED
    assert MCS.move_ends_here(_held(reason), {1: _held(reason), 2: _hostile()}) is False


@pytest.mark.parametrize("reason", RELEASED)
def test_every_other_held_move_beside_an_engaged_hostile_is_released_to_the_brain(reason):
    held = _held(reason)
    assert MCS.move_ends_here(held, {1: held, 2: _hostile()}) is True
    assert MCS.move_ends_here(held, {1: held, 2: _hostile(pos=(10.0, 14.0))}) is False  # no hostile adjacent: keeps walking
    assert MCS.move_ends_here(held, {1: held, 2: _hostile(targets_walker=False)}) is False  # adjacent but not engaged


def test_an_idle_entity_is_not_a_held_move():
    idle = _walker()
    assert MCS.move_ends_here(idle, {1: idle, 2: _hostile()}) is False


def _completion_shape(update):
    return (update.task.work_kind_set, dict(update.task.payload_set), bool(update.navigation.target_clear), update.navigation.target_set)


@pytest.mark.parametrize("reason,released", [("REGROUP", True), ("INTERCEPTING", True), (None, True), ("PANIC_RETREAT", False)])
def test_the_two_dispatchers_release_or_keep_a_blocked_held_move_identically(reason, released):
    """LocalSequentialExecutor and default_simulation_worker (the concurrent adapter's worker) ask the same helper."""
    held, hostile = _held(reason), _hostile()
    state = AuthoritativeState(tick=5, seed=42, world_time=5, entities={1: held, 2: hostile})
    item = WorkItem(owner_id=1, work_id="5:1:ENTITY_MOVE", work_class=WorkClass.CRITICAL, work_kind="ENTITY_MOVE", payload=held.task.payload)
    local = LocalSequentialExecutor().execute([item], state, DeterministicRNG(42), PROD_SMALL)[0].update
    packet = SimpleNamespace(packet_id="pk", work_id="w", work_class=WorkClass.CRITICAL, class_priority=0, local_priority=0,
                             work_kind="ENTITY_MOVE", payload=held.task.payload, subject=held, all_entities={1: held, 2: hostile})
    worker = default_simulation_worker(packet)[0].update
    if released:
        assert _completion_shape(local) == _completion_shape(worker) == ("ENTITY_ACT", {}, True, None)
    else:
        assert local.task is None and worker.task is None
        assert local.navigation.target_set == worker.navigation.target_set == STORED
