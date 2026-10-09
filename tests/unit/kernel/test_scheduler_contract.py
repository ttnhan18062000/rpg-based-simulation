import pytest
from src.core.state import AuthoritativeState, EntityState
from src.engine.scheduler import DeterministicScheduler
from src.core.work import WorkClass
from src.core.builder import V2EntityBuilder


def test_readiness_driven_selection():
    """
    Brain tasks (ENTITY_BRAIN, idle ENTITY_ACT) bypass the readiness gate.
    Only ENTITY_ACT with a payload or ENTITY_MOVE requires >= 100.0 readiness
    (Action Readiness Law, COMB-266).
    """
    e1 = V2EntityBuilder(1).combat(readiness=100.0).build()
    e2 = V2EntityBuilder(2).combat(readiness=99.9).build()
    e3 = V2EntityBuilder(3).combat(readiness=150.0).build()

    state = AuthoritativeState(tick=1, seed=42, entities={1: e1, 2: e2, 3: e3})

    scheduler = DeterministicScheduler()
    work, _ = scheduler.select_work(state)

    # All three selected as ENTITY_BRAIN (brain is never readiness-gated)
    assert len(work) == 3
    assert all(w.work_kind == "ENTITY_BRAIN" for w in work)
    # Order: readiness DESC, then owner_id ASC
    assert [w.owner_id for w in work] == [3, 1, 2]


def test_action_readiness_gate():
    """ENTITY_ACT with a non-empty payload requires 100.0 readiness."""
    from dataclasses import replace as dc_replace
    from src.core.state import TaskComponent

    e_low = dc_replace(
        V2EntityBuilder(4).combat(readiness=50.0).build(),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 99}),
    )
    e_full = dc_replace(
        V2EntityBuilder(5).combat(readiness=100.0).build(),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 99}),
    )

    state = AuthoritativeState(tick=1, seed=42, entities={4: e_low, 5: e_full})

    scheduler = DeterministicScheduler()
    work, _ = scheduler.select_work(state)

    assert len(work) == 1
    assert work[0].owner_id == 5


def test_deterministic_tiebreak():
    """Verify that same-readiness entities are sorted by EntityID ASC."""
    e1 = V2EntityBuilder(1).combat(readiness=100.0).build()
    e2 = V2EntityBuilder(2).combat(readiness=100.0).build()
    e3 = V2EntityBuilder(3).combat(readiness=100.0).build()
    
    state = AuthoritativeState(tick=1, seed=42, entities={3: e3, 1: e1, 2: e2})
    
    scheduler = DeterministicScheduler()
    work, _ = scheduler.select_work(state)
    
    assert [w.owner_id for w in work] == [1, 2, 3]


def test_the_scheduler_selects_only_entity_work():
    """Every work item is CRITICAL entity work. Periodic and deferred (DRAIN_DEBT) selection is gone, so a state that still carries the
    removed fields yields nothing beyond its entities, and the scheduler sheds nothing."""
    e1 = V2EntityBuilder(1).combat(readiness=100.0).build()
    state = AuthoritativeState(tick=10, seed=1, entities={1: e1}, periodic_due_ticks={"weather": 10}, work_debt={"system_x": 1})

    work, dropped = DeterministicScheduler().select_work(state)

    assert [w.owner_id for w in work] == [1]
    assert {w.work_class for w in work} == {WorkClass.CRITICAL}
    assert dropped == 0

