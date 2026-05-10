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
    Verify that decision logic cannot mutate authoritative state.

    Law:
        Entity decision logic must receive a read-only authoritative state view.
        Attempting to mutate state.entities must raise immediately.

    Why this test does not use Kernel.tick_once:
        Kernel scheduling may choose ENTITY_ACT, ENTITY_MOVE, or no work.
        This law specifically targets ENTITY_BRAIN isolation, so the test
        directly executes an ENTITY_BRAIN WorkItem through LocalSequentialExecutor.

    Fraud this catches:
        - ENTITY_BRAIN receives mutable state.entities
        - LocalSequentialExecutor bypasses read-only state protection
        - mutation attempt is silently ignored instead of blocked
    """
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction
    from src.core.state import AuthoritativeState
    from src.core.work import WorkItem, WorkClass
    from src.engine.executor import LocalSequentialExecutor
    from src.platform.rng import DeterministicRNG
    from src.engine.domain_logic import SimulationDomainLogic

    profile = RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=80.0,
        max_worker_count=0,
        max_queue_depth=100,
        max_replay_buffer_kb=4096,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=50.0,
    )

    entity = (
        V2EntityBuilder(1)
        .kind("agent")
        .location(0.0, 0.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        work_debt={"ENTITY_BRAIN": 0},
    )

    executor = LocalSequentialExecutor()
    rng = DeterministicRNG(42)

    original_brain = SimulationDomainLogic.execute_brain

    def malicious_brain(state_ctx, entity_ctx):
        state_ctx.entities[1] = (
            V2EntityBuilder(1)
            .kind("mutated")
            .location(666.0, 666.0)
            .build()
        )
        return original_brain(state_ctx, entity_ctx)

    SimulationDomainLogic.execute_brain = malicious_brain

    try:
        work = [
            WorkItem(
                owner_id=1,
                work_id="1:1:ENTITY_BRAIN",
                work_kind="ENTITY_BRAIN",
                work_class=WorkClass.CRITICAL,
                payload={},
            )
        ]

        with pytest.raises(Exception) as excinfo:
            executor.execute(work, state, rng, profile)

        err_msg = str(excinfo.value)
        assert any(
            msg in err_msg
            for msg in [
                "MappingProxyType",
                "item assignment",
                "does not support item assignment",
                "Authoritative mutation attempted",
                "ReadOnlyDict",
            ]
        )
    finally:
        SimulationDomainLogic.execute_brain = original_brain
        
        
def test_authoritative_state_entities_are_read_only():
    """
    Verify that AuthoritativeState protects the entity map itself.
    """
    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState

    entity = (
        V2EntityBuilder(1)
        .kind("agent")
        .location(0.0, 0.0)
        .build()
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
    )

    with pytest.raises(Exception):
        state.entities[1] = entity


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
