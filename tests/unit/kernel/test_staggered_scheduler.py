import pytest
from src.core.state import AuthoritativeState
from src.engine.scheduler import DeterministicScheduler
from src.engine.policy import GovernorPolicy
from src.engine.cadence import SystemCadence
from src.core.builder import V2EntityBuilder

@pytest.fixture
def scheduler():
    return DeterministicScheduler()

@pytest.fixture
def base_state():
    return AuthoritativeState(seed=42, tick=0, entities={})

def test_staggered_brain_gating(scheduler, base_state):
    """ENTITY_BRAIN should be gated by strategic_intelligence cadence."""
    # Entity ID 1, Cadence 10.
    # should_run(tick, 1, 10) -> (tick + 1) % 10 == 0
    # True for tick 9, 19, etc.
    e1 = V2EntityBuilder(1).combat(readiness=100.0).task(work_kind="ENTITY_BRAIN").build()
    
    cadence = SystemCadence(strategic_intelligence=10)
    policy = GovernorPolicy(system_cadence=cadence)
    
    # Tick 0: (0+1)%10 = 1 != 0 -> GATED
    state_0 = AuthoritativeState(tick=0, seed=42, entities={1: e1})
    work_0, _ = scheduler.select_work(state_0, policy)
    assert len(work_0) == 0
    
    # Tick 9: (9+1)%10 = 0 -> SELECTED
    state_9 = AuthoritativeState(tick=9, seed=42, entities={1: e1})
    work_9, _ = scheduler.select_work(state_9, policy)
    assert len(work_9) == 1
    assert work_9[0].owner_id == 1

def test_staggered_idle_act_gating(scheduler, base_state):
    """Idle ENTITY_ACT (empty payload) should be gated."""
    e1 = V2EntityBuilder(1).combat(readiness=100.0).task(work_kind="ENTITY_ACT", payload={}).build()
    
    cadence = SystemCadence(strategic_intelligence=10)
    policy = GovernorPolicy(system_cadence=cadence)
    
    # Tick 0: GATED
    state_0 = AuthoritativeState(tick=0, seed=42, entities={1: e1})
    work_0, _ = scheduler.select_work(state_0, policy)
    assert len(work_0) == 0
    
    # Tick 9: SELECTED
    state_9 = AuthoritativeState(tick=9, seed=42, entities={1: e1})
    work_9, _ = scheduler.select_work(state_9, policy)
    assert len(work_9) == 1

def test_critical_act_not_gated(scheduler, base_state):
    """Non-idle ENTITY_ACT (with payload) should NEVER be gated."""
    e1 = V2EntityBuilder(1).combat(readiness=100.0).task(work_kind="ENTITY_ACT", payload={"action": "INTERACT"}).build()
    
    cadence = SystemCadence(strategic_intelligence=10)
    policy = GovernorPolicy(system_cadence=cadence)
    
    # Tick 0: NOT GATED (even though cadence says it should be if it were idle)
    state_0 = AuthoritativeState(tick=0, seed=42, entities={1: e1})
    work_0, _ = scheduler.select_work(state_0, policy)
    assert len(work_0) == 1
    assert work_0[0].payload == {"action": "INTERACT"}

def test_move_not_gated(scheduler, base_state):
    """ENTITY_MOVE should NEVER be gated."""
    e1 = V2EntityBuilder(1).combat(readiness=100.0).task(work_kind="ENTITY_MOVE").build()
    
    cadence = SystemCadence(strategic_intelligence=10)
    policy = GovernorPolicy(system_cadence=cadence)
    
    # Tick 0: NOT GATED
    state_0 = AuthoritativeState(tick=0, seed=42, entities={1: e1})
    work_0, _ = scheduler.select_work(state_0, policy)
    assert len(work_0) == 1
    assert work_0[0].work_kind == "ENTITY_MOVE"
