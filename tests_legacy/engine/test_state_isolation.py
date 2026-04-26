import pytest
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.engine.kernel import Kernel
from src_legacy.config.profiles import RuntimeProfile
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.core.updates import EntityUpdate

def get_test_profile(max_workers: int = 0) -> RuntimeProfile:
    from src_legacy.config.profiles import HardwareClass
    return RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=80.0,
        max_worker_count=max_workers,
        max_queue_depth=100,
        max_replay_buffer_kb=4096,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=50.0
    )

def test_state_mutation_protection():
    """
    Verify that authoritative state is protected from mutation during decision logic.
    M8 Law: Isolation Breach must raise ProtocolViolationError or be prevented by immutability.
    """
    # 1. Setup state with one entity
    entity = EntityState(id=1, kind="hero", position=(0,0), readiness=100.0)
    # Ensure entity is registered in scheduler/work_debt if needed
    state = AuthoritativeState(
        tick=1, 
        seed=42, 
        entities={1: entity},
        work_debt={"ENTITY_BRAIN": 0}
    )
    
    profile = get_test_profile(max_workers=0) # Sequential
    rng = DeterministicRNG(42)
    kernel = Kernel(profile, state, rng, flags={"audit_mode": True})
    
    # 2. Monkeypatch a system to attempt mutation
    from src_legacy.engine.domain_logic import SimulationDomainLogic
    
    original_brain = SimulationDomainLogic.execute_brain
    
    def malicious_brain(state_ctx, entity_ctx):
        # ATTEMPT MUTATION
        state_ctx.entities[1] = EntityState(id=1, kind="mutated", position=(666, 666))
        return original_brain(state_ctx, entity_ctx)
    
    SimulationDomainLogic.execute_brain = malicious_brain
    
    try:
        # This should trigger either TypeError (MappingProxyType) or ProtocolViolationError (_guard_stability)
        with pytest.raises(Exception) as excinfo:
            kernel.tick_once()
        
        # MappingProxyType raises TypeError on __setitem__
        # Kernel raises ProtocolViolationError on hash mismatch (if it survives to the guard)
        err_msg = str(excinfo.value)
        assert "Isolation Breach" in err_msg or "MappingProxyType" in err_msg or "item assignment" in err_msg
    finally:
        SimulationDomainLogic.execute_brain = original_brain

def test_deep_freeze_efficacy():
    """
    Verify that deep_freeze actually prevents mutation.
    """
    from src_legacy.core.immutability import deep_freeze
    from types import MappingProxyType
    
    d = {"a": [1, 2, 3], "b": {"c": 4}}
    frozen = deep_freeze(d)
    
    assert isinstance(frozen, MappingProxyType)
    assert isinstance(frozen["a"], tuple)
    
    with pytest.raises(TypeError):
        frozen["a"] = 5
        
    with pytest.raises(TypeError):
        frozen["b"]["c"] = 5
