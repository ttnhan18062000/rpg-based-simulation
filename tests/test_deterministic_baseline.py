import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, InventoryComponent

def test_world_init_determinism():
    """Verify that identical seeds produce bit-identical initial states."""
    def create_test_world(seed: int):
        # Simulate a scenario setup
        entities = {
            1: (
                V2EntityBuilder(1)
                .kind("hero")
                .location(10.0, 10.0)
                .identity(role=1)
                .build()
            ),
            2: (
                V2EntityBuilder(2)
                .kind("npc")
                .location(5.0, 5.0)
                .inventory(gold=100)
                .build()
            )
        }
        return AuthoritativeState(
            tick=0,
            seed=seed,
            entities=entities,
            global_resources={"wood": 0.0, "gold": 1000.0},
            town_tiles={(10, 10), (11, 10)}
        )

    state1 = create_test_world(42)
    state2 = create_test_world(42)
    state3 = create_test_world(43)
    
    # Use the new fingerprint logic
    f1 = state1.fingerprint()
    f2 = state2.fingerprint()
    f3 = state3.fingerprint()
    
    assert f1["state_hash"] == f2["state_hash"]
    assert f1["state_hash"] != f3["state_hash"]

def test_subsystem_order_documentation():
    """
    Verify that AuthoritativeApplyPipeline.refine follows the documented
    hardened phase order.

    Important ordering law:
        Resource transactions must resolve before strategic blocker resolution.

    Why:
        Material blockers such as `blocker_mat_iron_ore` can only be cleared
        correctly after the authoritative inventory/resource transaction phase
        has applied pending item changes.

    Fraud this catches:
        - strategic blockers are resolved against stale inventory
        - redirection runs before material acquisition is known
        - crafting/resource loop gets stuck or returns home too early
        - source comments claim one phase order while code runs another
    """
    import inspect
    from src.engine.pipeline import AuthoritativeApplyPipeline

    source = inspect.getsource(AuthoritativeApplyPipeline.refine)

    expected_order = [
        "TownResolutionSystem.resolve",
        "ShopSystem.enforce",
        "BlacksmithSystem.enforce",

        # Combat may appear here in your local pipeline. Include it if present.
        "AuthoritativeApplyPipeline._route_combat_intent",

        "WorldDynamicsSystem.resolve_dynamics",
        "BuildingSabotageSystem.resolve",

        "AuthoritativeApplyPipeline._route_interaction_intent",
        "InteractionSystem.enforce",

        "AuthoritativeApplyPipeline._route_movement_intent",
        "AuthoritativeApplyPipeline._resolve_occupancy_conflicts",

        "LifecycleSystem.resolve_lifecycle",
        "QuestResolutionSystem.enforce",

        # Must be before blocker resolution.
        "AuthoritativeApplyPipeline._resolve_resource_transactions",

        # Must be after resources, before redirection.
        "StrategicIntelligenceSystem.resolve_blockers",
        "StrategicIntelligenceSystem.evaluate_biological_concerns",
        "StrategicRedirectionSystem.enforce",

        "EvolutionSystem.evaluate",
    ]

    positions = {}

    for system in expected_order:
        pos = source.find(system)
        assert pos != -1, f"System call {system} not found in pipeline"
        positions[system] = pos

    for earlier, later in zip(expected_order, expected_order[1:]):
        assert positions[earlier] < positions[later], (
            f"System call order is wrong:\n"
            f"Expected `{earlier}` before `{later}`.\n"
            f"Actual positions: {earlier}={positions[earlier]}, "
            f"{later}={positions[later]}"
        )

def test_full_tick_determinism():
    """Law: A full simulation tick must be bit-identical given identical state and seed."""
    from src.engine.kernel import Kernel
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.core.updates import EntityUpdate, NavigationUpdate
    from src.core.worker_protocol import WorkerResult
    from src.core.work import WorkClass
    
    profile = RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=100.0
    )
    
    def run_one_tick(seed: int):
        e1 = (
                V2EntityBuilder(1)
                .kind("hero")
                .location(0.0, 0.0)
                .build()
            )
        from dataclasses import replace
        e1 = replace(e1, navigation=replace(e1.navigation, target=(1.0, 1.0)))
        
        state = AuthoritativeState(tick=1, seed=seed, world_time=10, entities={1: e1})
        
        from src.platform.rng import DeterministicRNG
        rng = DeterministicRNG(seed)
        
        # Mock executor to return a movement proposal
        from unittest.mock import MagicMock
        executor = MagicMock()
        res_1 = WorkerResult(
            source_packet_id="1:0",
            work_id="1:1:M",
            entity_id=1,
            work_class=WorkClass.CRITICAL,
            update=EntityUpdate(entity_id=1, new_position=(1.0, 0.0), moved_this_tick=True)
        )
        executor.execute.return_value = [res_1]
        executor._source_packets = {"1:0": MagicMock(packet_id="1:0", work_id="1:1:M", subject=e1)}
        
        kernel = Kernel(
            profile=profile,
            state=state,
            rng=rng,
            executor=executor
        )
        
        # Manually run stages
        kernel._phase_init()
        kernel._phase_scheduling()
        kernel._phase_collection()
        kernel._phase_resolution()
        
        return kernel._state.fingerprint()

    f1 = run_one_tick(42)
    f2 = run_one_tick(42)
    f3 = run_one_tick(43)
    
    assert f1["state_hash"] == f2["state_hash"]
    assert f1["state_hash"] != f3["state_hash"] # Different seeds now affect the hash directly
