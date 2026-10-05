"""A pursuit ENTITY_MOVE ends when the live target is in attack reach.

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

REACH = MovementCandidateSelector.pursuit_reached_attack_range


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


def _pursuer(pos=(10.0, 10.0), *, mode=MovementMode.PURSUE, target_id=2, attack_range=1):
    e = _entity(1, pos, faction=Faction.HERO_GUILD, attack_range=attack_range)
    nav = replace(e.navigation, movement_mode=mode, target=(10.0, 11.0))
    task = TaskComponent(work_kind="ENTITY_MOVE", payload={"target_id": target_id, "target_position": (10.0, 11.0)})
    return replace(e, navigation=nav, task=task)


def _entities(pursuer, target):
    return {pursuer.id: pursuer, target.id: target}


class TestPursuitReachedAttackRange:
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

    def test_dead_target_is_left_to_the_existing_path(self):
        p = _pursuer()
        t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE, hp=0)
        assert REACH(p, _entities(p, t)) is False

    def test_missing_target_is_left_to_the_existing_path(self):
        p = _pursuer()
        assert REACH(p, {p.id: p}) is False

    def test_non_pursuit_moves_with_a_target_id_keep_their_own_lifecycle(self):
        for mode in (MovementMode.GUARD, MovementMode.REPOSITION, MovementMode.RETREAT, MovementMode.WANDER):
            p = _pursuer(mode=mode)
            t = _entity(2, (10.0, 11.0), faction=Faction.MONSTER_HORDE)
            assert REACH(p, _entities(p, t)) is False, mode

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


def test_completion_update_names_its_entity():
    p = _pursuer()
    assert MovementCandidateSelector.pursuit_completion_update(p).entity_id == p.id
    assert isinstance(NavigationUpdate(target_clear=True), NavigationUpdate)
