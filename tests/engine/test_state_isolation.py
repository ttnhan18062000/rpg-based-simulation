import pytest
from src.core.state import AuthoritativeState, EntityState
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile
from src.platform.rng import DeterministicRNG
from src.core.updates import EntityUpdate
from src.core.builder import V2EntityBuilder

def get_test_profile(max_workers: int = 0) -> RuntimeProfile:
    from src.config.profiles import HardwareClass
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
    # 1. Setup state with one entity via V2EntityBuilder
    entity = (V2EntityBuilder(1)
              .at((0, 0))
              .readiness(100.0)
              .build())
              
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
    from src.engine.domain_logic import SimulationDomainLogic
    
    original_brain = SimulationDomainLogic.execute_brain
    
    def malicious_brain(state_ctx, entity_ctx):
        # ATTEMPT MUTATION
        # Note: state_ctx.entities is a MappingProxyType in V2
        try:
            state_ctx.entities[1] = (V2EntityBuilder(1)
                                     .at((666, 666))
                                     .build())
        except Exception as e:
            # Re-raise so pytest.raises captures it
            raise e
        return original_brain(state_ctx, entity_ctx)
    
    SimulationDomainLogic.execute_brain = malicious_brain
    
    try:
        # This should trigger either TypeError (MappingProxyType) or ProtocolViolationError (_guard_stability)
        with pytest.raises(Exception) as excinfo:
            kernel.tick_once()
        
        # MappingProxyType raises TypeError on __setitem__
        # Kernel raises ProtocolViolationError on hash mismatch (if it survives to the guard)
        err_msg = str(excinfo.value)
        assert any(msg in err_msg for msg in ["Isolation Breach", "MappingProxyType", "item assignment", "does not support item assignment", "Authoritative mutation attempted"])
    finally:
        SimulationDomainLogic.execute_brain = original_brain

def test_deep_freeze_efficacy():
    """
    Verify that deep_freeze actually prevents mutation.
    """
    from src.core.immutability import deep_freeze
    from src.core.state import ReadOnlyDict
    
    d = {"a": [1, 2, 3], "b": {"c": 4}}
    frozen = deep_freeze(d)
    
    assert isinstance(frozen, ReadOnlyDict)
    assert isinstance(frozen["a"], tuple)
    
    with pytest.raises(TypeError):
        frozen["a"] = 5
        
    with pytest.raises(TypeError):
        frozen["b"]["c"] = 5
