from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.engine.scheduler import DeterministicScheduler, PeriodicDefinition
from src_v2.core.work import WorkClass


def test_bucket_prioritization():
    """Verify that Critical work is always scheduled before Periodic work."""
    p_def = PeriodicDefinition(subsystem_id="cleanup", action_type="GC", cadence=1)
    # Entity ID is 100, but it should come before "cleanup" if both are due.
    state = AuthoritativeState(tick=1, seed=42, 
        entities={100: EntityState(id=100, kind="hero", position=(0,0), readiness=100.0)},
        periodic_due_ticks={"cleanup": 1}
    )
    
    scheduler = DeterministicScheduler(periodic_defs=[p_def])
    work = scheduler.select_work(state)
    
    assert len(work) == 2
    assert work[0].work_class == WorkClass.CRITICAL
    assert work[1].work_class == WorkClass.PERIODIC


def test_dual_periodic_ordering():
    """Verify stable ordering within the Periodic bucket."""
    defs = [
        PeriodicDefinition(subsystem_id="B_sys", action_type="ACT", cadence=1),
        PeriodicDefinition(subsystem_id="A_sys", action_type="ACT", cadence=1),
    ]
    state = AuthoritativeState(tick=1, seed=42, periodic_due_ticks={"A_sys": 1, "B_sys": 1})
    
    scheduler = DeterministicScheduler(periodic_defs=defs)
    work = scheduler.select_work(state)
    
    # Bucket 1: Critical (None)
    # Bucket 2: Periodic (A_sys, then B_sys)
    assert work[0].owner_id == "A_sys"
    assert work[1].owner_id == "B_sys"
