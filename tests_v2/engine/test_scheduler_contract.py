import pytest
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.engine.scheduler import DeterministicScheduler, PeriodicDefinition
from src_v2.core.work import WorkClass


def test_readiness_driven_selection():
    """Verify that only entities at or above 100.0 readiness are selected."""
    state = AuthoritativeState(tick=1, seed=42, entities={
        1: EntityState(id=1, kind="hero", position=(0,0), readiness=100.0),
        2: EntityState(id=2, kind="hero", position=(0,0), readiness=99.9),
        3: EntityState(id=3, kind="hero", position=(0,0), readiness=150.0),
    })
    
    scheduler = DeterministicScheduler()
    work = scheduler.select_work(state)
    
    # Expect 2 entity actions (ID 1 and 3)
    # Order should be Readiness DESC (3 then 1)
    assert len(work) == 2
    assert work[0].owner_id == 3
    assert work[1].owner_id == 1


def test_deterministic_tiebreak():
    """Verify that same-readiness entities are sorted by EntityID ASC."""
    state = AuthoritativeState(tick=1, seed=42, entities={
        3: EntityState(id=3, kind="hero", position=(0,0), readiness=100.0),
        1: EntityState(id=1, kind="hero", position=(0,0), readiness=100.0),
        2: EntityState(id=2, kind="hero", position=(0,0), readiness=100.0),
    })
    
    scheduler = DeterministicScheduler()
    work = scheduler.select_work(state)
    
    assert [w.owner_id for w in work] == [1, 2, 3]


def test_periodic_selection():
    """Verify that periodic tasks are selected when due."""
    p_def = PeriodicDefinition(subsystem_id="weather", action_type="UPDATE", cadence=10)
    scheduler = DeterministicScheduler(periodic_defs=[p_def])
    
    # Tick 0: Weather is due (due_tick=0)
    state_0 = AuthoritativeState(tick=0, seed=42, periodic_due_ticks={"weather": 0})
    work_0 = scheduler.select_work(state_0)
    assert any(w.owner_id == "weather" for w in work_0)
    
    # Tick 5: Weather is NOT due (due_tick=10)
    state_5 = AuthoritativeState(tick=5, seed=42, periodic_due_ticks={"weather": 10})
    work_5 = scheduler.select_work(state_5)
    assert not any(w.owner_id == "weather" for w in work_5)
