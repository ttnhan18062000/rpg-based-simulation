from src.core.state import AuthoritativeState
from src.engine.scheduler import DeterministicScheduler
from src.core.work import WorkClass
from src.core.builder import V2EntityBuilder

def test_deferred_drain_selection():
    """Verify that the scheduler selects DEFERRED work if debt exists."""
    state = AuthoritativeState(tick=1, seed=42, work_debt={"subsys_A": 2})
    
    scheduler = DeterministicScheduler()
    work = scheduler.select_work(state)[0]
    
    assert len(work) == 1
    assert work[0].work_class == WorkClass.DEFERRED
    assert work[0].owner_id == "subsys_A"
    assert work[0].work_kind == "DRAIN_DEBT"


def test_deferred_drain_ordering():
    """Verify stable ordering within the DEFERRED bucket."""
    state = AuthoritativeState(tick=1, seed=42, work_debt={
        "B": 1, 
        "A": 5
    })
    
    scheduler = DeterministicScheduler()
    work = scheduler.select_work(state)[0]
    
    assert len(work) == 2
    assert work[0].owner_id == "A"
    assert work[1].owner_id == "B"


def test_deferred_vs_periodic_priority():
    """Verify Bucket ranking: Critical -> Periodic -> Deferred."""
    # Periodic is due at tick 1. Entity is ready at readiness 100. Debt exists.
    from src.engine.scheduler import PeriodicDefinition
    from src.core.state import EntityState
    
    p_def = PeriodicDefinition(subsystem_id="P", work_kind="ACT", cadence=1)
    state = AuthoritativeState(tick=1, seed=42, 
        entities={1: V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(readiness=100.0).task(work_kind="ENTITY_MOVE").build()},
        periodic_due_ticks={"P": 1},
        work_debt={"D": 1}
    )
    
    scheduler = DeterministicScheduler(periodic_defs=[p_def])
    work = scheduler.select_work(state)[0]
    
    # 1. Critical (ID 1)
    # 2. Periodic (P)
    # 3. Deferred (D)
    assert [w.work_class for w in work] == [
        WorkClass.CRITICAL, 
        WorkClass.PERIODIC, 
        WorkClass.DEFERRED
    ]
