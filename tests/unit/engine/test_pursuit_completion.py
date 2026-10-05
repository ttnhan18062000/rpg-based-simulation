"""An entity-tracking combat ENTITY_MOVE ends when its live target is in attack reach, or is dead or gone.

TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK: the tactical pass creates a pursuit
move once, the scheduler re-runs it as movement without re-deciding (Sticky-Task Law), and nothing ended it, so an
entity next to its target at full readiness never got to choose ATTACK. Each test builds the situation directly;
the "must not change" cases pin that the rule is narrow.
"""
from dataclasses import replace
from types import SimpleNamespace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, TaskComponent
from src.core.updates import NavigationUpdate
from src.core.work import WorkClass, WorkItem
from src.config.profiles import PROD_SMALL
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.executor import LocalSequentialExecutor
from src.engine.worker_logic import default_simulation_worker
from src.platform.rng import DeterministicRNG

REACH = MovementCandidateSelector.tracked_move_complete


def _entity(eid, pos, *, faction, hp=100, attack_range=1):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid)
        .kind("hero" if role == EntityRole.HERO else "monster")
        .location(*pos)
        .identity(role=role, faction=faction)
        .combat(hp=hp, max_hp=100, attack_range=attack_range, readiness=100.0, alive=hp > 0)
        .lifecycle(active=True)
        .build()
    )


def _pursuer(pos=(10.0, 10.0), *, mode=MovementMode.PURSUE, target_id=2, attack_range=1, reason=None):
    e = _entity(1, pos, faction=Faction.HERO_GUILD, attack_range=attack_range)
    nav = replace(e.navigation, movement_mode=mode, target=(10.0, 11.0))
    payload = {"target_id": target_id, "target_position": (10.0, 11.0)}
    if reason is not None:
        payload["reason"] = reason
    task = TaskComponent(work_kind="ENTITY_MOVE", payload=payload)
    return replace(e, navigation=nav, task=task)


# (movement mode, payload reason) of each entity-tracking combat move the tactical pass issues
PURSUIT = (MovementMode.PURSUE, None)
INTERCEPT = (MovementMode.INTERCEPT, "INTERCEPTING")
BRACKETING = (MovementMode.REPOSITION, "BRACKETING")
KITING = (MovementMode.RETREAT, "KITING")  # constructed: the corpus has no kiting move
COMBAT_POSITIONING = (PURSUIT, INTERCEPT, BRACKETING, KITING)
IN_REACH_ENDS = (PURSUIT, INTERCEPT, BRACKETING)  # kiting intends to hold range


def _entities(pursuer, target):
    return {pursuer.id: pursuer, target.id: target}


class TestTrackedMoveComplete:
    def test_adjacent_live_target_completes_the_pursuit(self):
        p = _pursuer()
        t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE)
        assert REACH(p, _entities(p, t)) is True

    def test_target_two_tiles_away_does_not_for_a_melee_entity(self):
        p = _pursuer()
        t = _entity(2, (10.0, 12.0), faction=Faction.MONSTER_HORDE)
        assert REACH(p, _entities(p, t)) is False

    def test_ranged_entity_completes_at_its_range(self):
        p = _pursuer(attack_range=5)
        t = _entity(2, (10.0, 14.0), faction=Faction.MONSTER_HORDE)
        assert REACH(p, _entities(p, t)) is True

    def test_uses_the_targets_live_position_not_the_navigation_snapshot(self):
        # The snapshot (nav target and payload target_position) says (10, 11), adjacent; the target has moved.
        p = _pursuer()
        t = _entity(2, (10.0, 30.0), faction=Faction.MONSTER_HORDE)
        assert REACH(p, _entities(p, t)) is False

    def test_dead_target_ends_a_pursuit(self):
        p = _pursuer()
        t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE, hp=0)
        assert REACH(p, _entities(p, t)) is True

    def test_missing_target_ends_a_pursuit(self):
        p = _pursuer()
        assert REACH(p, {p.id: p}) is True

    def test_dead_or_missing_target_ends_every_combat_positioning_move(self):
        for mode, reason in COMBAT_POSITIONING:
            p = _pursuer(mode=mode, reason=reason)
            dead = _entity(2, (10.0, 30.0), faction=Faction.MONSTER_HORDE, hp=0)
            assert REACH(p, _entities(p, dead)) is True, (mode, reason, "dead")
            assert REACH(p, {p.id: p}) is True, (mode, reason, "missing")

    def test_inactive_target_ends_a_combat_positioning_move(self):
        for mode, reason in COMBAT_POSITIONING:
            p = _pursuer(mode=mode, reason=reason)
            t = _entity(2, (10.0, 30.0), faction=Faction.MONSTER_HORDE)
            t = replace(t, lifecycle=replace(t.lifecycle, active=False))
            assert REACH(p, _entities(p, t)) is True, (mode, reason)

    def test_in_reach_ends_pursuit_intercept_and_bracketing(self):
        for mode, reason in IN_REACH_ENDS:
            p = _pursuer(mode=mode, reason=reason)
            t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE)
            assert REACH(p, _entities(p, t)) is True, (mode, reason)

    def test_out_of_reach_live_target_keeps_every_combat_positioning_move(self):
        for mode, reason in COMBAT_POSITIONING:
            p = _pursuer(mode=mode, reason=reason)
            t = _entity(2, (10.0, 14.0), faction=Faction.MONSTER_HORDE)
            assert REACH(p, _entities(p, t)) is False, (mode, reason)

    def test_kiting_holds_range_so_a_live_adjacent_target_does_not_end_it(self):
        p = _pursuer(mode=KITING[0], reason=KITING[1])
        t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE)
        assert REACH(p, _entities(p, t)) is False

    def test_moves_that_are_not_combat_positioning_keep_their_own_lifecycle(self):
        # guarding a leader, seeking cover, a plain retreat or a wander that carries a target_id: untouched even
        # when the target is adjacent, dead or gone (their lifecycles are their own tickets')
        cases = [
            (MovementMode.GUARD, "CONTRACT_OBLIGATION_GUARD"),
            (MovementMode.GUARD, None),
            (MovementMode.REPOSITION, "SEEK_COVER"),
            (MovementMode.REPOSITION, None),
            (MovementMode.RETREAT, "PANIC_RETREAT"),
            (MovementMode.RETREAT, None),
            (MovementMode.WANDER, None),
            (MovementMode.REGROUP, None),
        ]
        for mode, reason in cases:
            p = _pursuer(mode=mode, reason=reason)
            live = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE)
            dead = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE, hp=0)
            assert REACH(p, _entities(p, live)) is False, (mode, reason, "live")
            assert REACH(p, _entities(p, dead)) is False, (mode, reason, "dead")
            assert REACH(p, {p.id: p}) is False, (mode, reason, "missing")

    def test_pursuit_without_a_target_id_is_unchanged(self):
        p = _pursuer()
        p = replace(p, task=TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (10.0, 11.0)}))
        t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE)
        assert REACH(p, _entities(p, t)) is False


def _assert_completion(update):
    assert update.task.work_kind_set == "ENTITY_ACT"
    assert update.task.payload_set == {}  # the idle-task encoding the scheduler reclassifies back to the brain
    assert update.navigation.target_clear is True


class TestDispatchers:
    def _state(self, pursuer, target):
        return AuthoritativeState(tick=5, seed=42, world_time=5, entities=_entities(pursuer, target))

    def test_local_executor_ends_a_pursuit_that_reached_range(self):
        p = _pursuer()
        t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE)
        item = WorkItem(owner_id=1, work_id="5:1:ENTITY_MOVE", work_class=WorkClass.CRITICAL,
                        work_kind="ENTITY_MOVE", payload=p.task.payload)
        results = LocalSequentialExecutor().execute([item], self._state(p, t), DeterministicRNG(42), PROD_SMALL)
        assert results, "the executor must return a result for the entity"
        _assert_completion(results[0].update)

    def test_local_executor_keeps_pursuing_when_out_of_range(self):
        p = _pursuer()
        t = _entity(2, (10.0, 14.0), faction=Faction.MONSTER_HORDE)
        item = WorkItem(owner_id=1, work_id="5:1:ENTITY_MOVE", work_class=WorkClass.CRITICAL,
                        work_kind="ENTITY_MOVE", payload=p.task.payload)
        results = LocalSequentialExecutor().execute([item], self._state(p, t), DeterministicRNG(42), PROD_SMALL)
        assert results[0].update.navigation.target_set == (10.0, 14.0)  # live-tracked, as before
        assert results[0].update.task is None

    def test_concurrent_worker_ends_a_pursuit_that_reached_range(self):
        p = _pursuer()
        t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE)
        packet = SimpleNamespace(
            packet_id="pk", work_id="w", work_class=WorkClass.CRITICAL, class_priority=0, local_priority=0,
            work_kind="ENTITY_MOVE", payload=p.task.payload, subject=p, all_entities=_entities(p, t),
        )
        results = default_simulation_worker(packet)
        assert results
        _assert_completion(results[0].update)

    def test_concurrent_worker_keeps_pursuing_when_out_of_range(self):
        p = _pursuer()
        t = _entity(2, (10.0, 14.0), faction=Faction.MONSTER_HORDE)
        packet = SimpleNamespace(
            packet_id="pk", work_id="w", work_class=WorkClass.CRITICAL, class_priority=0, local_priority=0,
            work_kind="ENTITY_MOVE", payload=p.task.payload, subject=p, all_entities=_entities(p, t),
        )
        results = default_simulation_worker(packet)
        assert results[0].update.navigation.target_set == (10.0, 14.0)
        assert results[0].update.task is None


    def test_local_executor_ends_a_bracketing_move_whose_target_died(self):
        p = _pursuer(mode=BRACKETING[0], reason=BRACKETING[1])
        t = _entity(2, (10.0, 30.0), faction=Faction.MONSTER_HORDE, hp=0)
        item = WorkItem(owner_id=1, work_id="5:1:ENTITY_MOVE", work_class=WorkClass.CRITICAL,
                        work_kind="ENTITY_MOVE", payload=p.task.payload)
        results = LocalSequentialExecutor().execute([item], self._state(p, t), DeterministicRNG(42), PROD_SMALL)
        _assert_completion(results[0].update)

    def test_concurrent_worker_ends_an_intercept_move_whose_target_died(self):
        p = _pursuer(mode=INTERCEPT[0], reason=INTERCEPT[1])
        t = _entity(2, (10.0, 30.0), faction=Faction.MONSTER_HORDE, hp=0)
        packet = SimpleNamespace(
            packet_id="pk", work_id="w", work_class=WorkClass.CRITICAL, class_priority=0, local_priority=0,
            work_kind="ENTITY_MOVE", payload=p.task.payload, subject=p, all_entities=_entities(p, t),
        )
        results = default_simulation_worker(packet)
        _assert_completion(results[0].update)

    def test_local_executor_keeps_a_guard_move_whose_target_died(self):
        p = _pursuer(mode=MovementMode.GUARD, reason="CONTRACT_OBLIGATION_GUARD")
        t = _entity(2, (10.0, 30.0), faction=Faction.MONSTER_HORDE, hp=0)
        item = WorkItem(owner_id=1, work_id="5:1:ENTITY_MOVE", work_class=WorkClass.CRITICAL,
                        work_kind="ENTITY_MOVE", payload=p.task.payload)
        results = LocalSequentialExecutor().execute([item], self._state(p, t), DeterministicRNG(42), PROD_SMALL)
        assert results[0].update.task is None  # not ended: guarding keeps its own lifecycle


def test_completion_update_names_its_entity():
    p = _pursuer()
    assert MovementCandidateSelector.tracked_move_completion_update(p).entity_id == p.id
    assert isinstance(NavigationUpdate(target_clear=True), NavigationUpdate)
