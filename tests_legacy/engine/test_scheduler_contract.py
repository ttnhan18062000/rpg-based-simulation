import pytest
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.engine.scheduler import DeterministicScheduler, PeriodicDefinition
from src_legacy.core.work import WorkClass


def test_readiness_driven_selection():
    """Verify that only entities at or above 100.0 readiness are selected."""
    state = AuthoritativeState(tick=1, seed=42, entities={
        1: EntityState(id=1, kind="hero", position=(0,0), readiness=100.0),
        2: EntityState(id=2, kind="hero", position=(0,0), readiness=99.9),
        3: EntityState(id=3, kind="hero", position=(0,0), readiness=150.0),
    })
    
    scheduler = DeterministicScheduler()
    work = scheduler.select_work(state)[0]
    
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
    work = scheduler.select_work(state)[0]
    
    assert [w.owner_id for w in work] == [1, 2, 3]


def test_periodic_selection():
    """Verify that periodic tasks are selected when due."""
    p_def = PeriodicDefinition(subsystem_id="weather", work_kind="UPDATE", cadence=10)
    scheduler = DeterministicScheduler(periodic_defs=[p_def])
    
    # Tick 0: Weather is due (due_tick=0)
    state_0 = AuthoritativeState(tick=0, seed=42, periodic_due_ticks={"weather": 0})
    work_0, _ = scheduler.select_work(state_0)
    assert any(w.owner_id == "weather" for w in work_0)
    
    # Tick 5: Weather is NOT due (due_tick=10)
    state_5 = AuthoritativeState(tick=5, seed=42, periodic_due_ticks={"weather": 10})
    work_5, _ = scheduler.select_work(state_5)
    assert not any(w.owner_id == "weather" for w in work_5)


def test_full_work_hierarchy():
    """Verify Critical > Periodic > Deferred hierarchy."""
    state = AuthoritativeState(
        tick=10, 
        seed=1,
        entities={1: EntityState(id=1, kind="hero", position=(0,0), readiness=100.0)},
        periodic_due_ticks={"weather": 10},
        work_debt={"system_x": 1}
    )
    p_def = PeriodicDefinition(subsystem_id="weather", work_kind="UPDATE", cadence=10)
    scheduler = DeterministicScheduler(periodic_defs=[p_def])
    
    work, _ = scheduler.select_work(state)
    
    assert len(work) == 3
    assert work[0].work_class == WorkClass.CRITICAL
    assert work[1].work_class == WorkClass.PERIODIC
    assert work[2].work_class == WorkClass.DEFERRED


def test_deferred_tiebreak():
    """Verify that Deferred items are sorted by Owner ID ASC."""
    state = AuthoritativeState(tick=1, seed=1, work_debt={"z": 10, "a": 5, "m": 1})
    scheduler = DeterministicScheduler()
    work, _ = scheduler.select_work(state)
    
    assert [w.owner_id for w in work] == ["a", "m", "z"]


def test_mixed_periodic_tiebreak():
    """Verify Periodic tasks sorted by (due_tick, subsystem_id)."""
    p_defs = [
        PeriodicDefinition(subsystem_id="weather", work_kind="W", cadence=10),
        PeriodicDefinition(subsystem_id="daily", work_kind="D", cadence=10),
        PeriodicDefinition(subsystem_id="hourly", work_kind="H", cadence=10),
    ]
    scheduler = DeterministicScheduler(periodic_defs=p_defs)
    
    state = AuthoritativeState(tick=100, seed=1, periodic_due_ticks={
        "weather": 100,
        "daily": 90,
        "hourly": 100
    })
    
    work, _ = scheduler.select_work(state)
    
    # Expected order: 
    # 1. daily (due 90)
    # 2. hourly (due 100, 'h' < 'w')
    # 3. weather (due 100)
    assert [w.owner_id for w in work] == ["daily", "hourly", "weather"]


def test_governor_gating_non_auth_periodic():
    """Verify non-authoritative periodic work is dropped per policy."""
    from src_legacy.engine.policy import GovernorPolicy
    
    p_defs = [
        PeriodicDefinition(subsystem_id="auth_sys", work_kind="A", cadence=10, is_authoritative=True),
        PeriodicDefinition(subsystem_id="non_auth_sys", work_kind="N", cadence=10, is_authoritative=False),
    ]
    scheduler = DeterministicScheduler(periodic_defs=p_defs)
    state = AuthoritativeState(tick=10, seed=1, periodic_due_ticks={"auth_sys": 0, "non_auth_sys": 0})
    
    # 1. ALLOWED
    policy_allow = GovernorPolicy(allow_non_authoritative_periodic=True)
    work_allow, dropped_allow = scheduler.select_work(state, policy_allow)
    assert len(work_allow) == 2
    assert dropped_allow == 0
    
    # 2. DISALLOWED (SURVIVAL mode logic)
    policy_drop = GovernorPolicy(allow_non_authoritative_periodic=False)
    work_drop, dropped_drop = scheduler.select_work(state, policy_drop)
    assert len(work_drop) == 1
    assert work_drop[0].owner_id == "auth_sys"
    assert dropped_drop == 1
