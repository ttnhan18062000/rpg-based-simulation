import pytest
from types import MappingProxyType
from src_legacy.core.immutability import deep_freeze
from src_legacy.core.state import EntityState, CombatComponent, InventoryComponent
from src_legacy.core.builder import V2EntityBuilder

@pytest.mark.v2_contract
def test_deep_freeze_primitives():
    assert deep_freeze(1) == 1
    assert deep_freeze("hello") == "hello"
    assert deep_freeze(True) is True
    assert deep_freeze(None) is None

@pytest.mark.v2_contract
def test_deep_freeze_collections():
    # Test Dict
    d = {"a": [1, 2], "b": {"c": 3}}
    frozen_d = deep_freeze(d)
    
    assert isinstance(frozen_d, MappingProxyType)
    assert isinstance(frozen_d["a"], tuple)
    assert isinstance(frozen_d["b"], MappingProxyType)
    
    with pytest.raises(TypeError):
        frozen_d["a"] = 1
    
    # Test List
    l = [1, [2, 3], {"d": 4}]
    frozen_l = deep_freeze(l)
    
    assert isinstance(frozen_l, tuple)
    assert isinstance(frozen_l[1], tuple)
    assert isinstance(frozen_l[2], MappingProxyType)

@pytest.mark.v2_contract
def test_deep_freeze_entity():
    # Create an entity with mutable properties
    builder = V2EntityBuilder(42)
    entity = builder.kind("hero").at((10, 10)).build()
    
    # Manually inject a mutable list into properties
    # Note: Builder creates frozen state, but we can use replace to inject mutables if we want to test freeze
    from dataclasses import replace
    entity = replace(entity, properties={"tags": ["fast", "strong"]})
    
    frozen_entity = deep_freeze(entity)
    
    assert isinstance(frozen_entity.properties, MappingProxyType)
    assert isinstance(frozen_entity.properties["tags"], tuple)
    
    # Verify we can't mutate
    with pytest.raises(TypeError):
        frozen_entity.properties["tags"] = []

@pytest.mark.v2_contract
def test_mutation_leak_prevention():
    """
    Simulation of a worker attempting to 'cheat' by mutating the subject's properties.
    """
    from src_legacy.core.work import WorkItem, WorkClass
    from src_legacy.core.state import AuthoritativeState
    from src_legacy.engine.executor import ConcurrentExecutionAdapter
    from src_legacy.engine.worker_manager import WorkerManager
    from src_legacy.platform.rng import DeterministicRNG
    from src_legacy.config.profiles import RuntimeProfile, HardwareClass
    
    # 1. Setup State
    builder = V2EntityBuilder(1)
    e1 = builder.kind("hero").at((0,0)).build()
    # Inject a mutable dict
    from dataclasses import replace
    e1 = replace(e1, properties={"inventory": {"gold": 10}})
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1})
    
    # 2. Setup Malicious Worker
    def malicious_worker(packet):
        # Attempt to cheat!
        try:
            packet.subject.properties["inventory"]["gold"] = 1000000
        except TypeError:
            # Expected if frozen
            pass
        
        from src_legacy.core.worker_protocol import WorkerResult, ResultStatus
        from src_legacy.core.updates import EntityUpdate
        return WorkerResult(
            source_packet_id=packet.packet_id,
            work_id=packet.work_id,
            entity_id=packet.subject.id,
            work_class=packet.work_class,
            update=EntityUpdate(entity_id=packet.subject.id),
            status=ResultStatus.SUCCESS
        )

    # 3. Execute via Adapter
    wm = WorkerManager(max_workers=1)
    adapter = ConcurrentExecutionAdapter(wm)
    
    profile = RuntimeProfile(
        name="test", hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=512, max_cpu_percent=100.0, max_worker_count=1, max_queue_depth=10,
        max_replay_buffer_kb=1024, max_observability_budget_percent=10.0, max_tick_budget_ms=100.0
    )
    
    work_item = WorkItem(owner_id=1, work_id="1:1:ENTITY_ACT", work_class=WorkClass.CRITICAL, work_kind="ENTITY_ACT")
    
    # Monkey-patch WM to use our malicious worker
    wm.execute_batch = lambda packets, logic, concurrency_limit: [malicious_worker(p) for p in packets]
    
    adapter.execute([work_item], state, DeterministicRNG(1), profile)
    
    # 4. Verify Authoritative State is UNCHANGED
    assert state.entities[1].properties["inventory"]["gold"] == 10
