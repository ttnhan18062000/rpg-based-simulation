
import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState, RegionState, EntityState, ItemStack
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile
from src.core.updates import ResourceTransferIntent, EntityUpdate
from pathlib import Path
import tempfile
import shutil

def test_transaction_trace_determinism():
    """
    Law: Authoritative decision traces must be identical across same-seed executions.
    This test verifies that rejected transactions are correctly logged and stable.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dir = Path(tmp_dir) / "run_1"
        
        profile = RuntimeProfile(
            name="test",
            hardware_class="class_b",
            max_ram_mb=256,
            max_cpu_percent=50.0,
            max_worker_count=0,
            max_queue_depth=100,
            max_replay_buffer_kb=1024,
            max_observability_budget_percent=10.0,
            max_tick_budget_ms=100.0,
            sampling_interval_ticks=1
        )
        
        # 1. Setup world with a resource node and an entity with full inventory
        region = RegionState(id="reg1", name="Region 1", bounds=(0, 0, 128, 128), owner_faction_id=1)
        
        from src.core.state import CombatComponent, InventoryComponent
        # Entity 1: Full inventory (cap 2 is implicit in resolver logic, but here we just fill it)
        ent1 = EntityState(
            id=1,
            kind="hero",
            position=(10, 10),
            combat=CombatComponent(hp=100, max_hp=100, alive=True),
            inventory=InventoryComponent(
                items=[ItemStack(item_id="stone", quantity=1), ItemStack(item_id="wood", quantity=1)],
                gold=0
            )
        )
        
        state = AuthoritativeState(
            tick=1,
            seed=42,
            entities={1: ent1},
            regions={"reg1": region}
        )
        
        rng = DeterministicRNG(42)
        kernel = Kernel(profile, state, rng)
        
        # Manually inject a failing intent (Harvesting while full)
        intent = ResourceTransferIntent(
            source_id="node_99",
            source_kind="NODE",
            items_add=[ItemStack(item_id="iron", quantity=1)],
            transfer_kind="HARVEST"
        )
        
        # We need to bypass the scheduler to force this intent for testing
        # We'll mock the executor result or just inject it into the pipeline
        
        from src.core.worker_protocol import WorkerResult, ResultStatus
        from src.core.updates import StateUpdate, EntityUpdate
        from src.core.work import WorkClass
        
        res = WorkerResult(
            source_packet_id="p1",
            work_id="w1",
            entity_id=1,
            work_class=WorkClass.CRITICAL,
            status=ResultStatus.SUCCESS,
            update=EntityUpdate(entity_id=1, resource_transfers=[intent])
        )
        
        # Manually run the resolution phase with this result
        kernel._final_results = [res]
        kernel._phase_resolution()
        
        # Check if trace contains the failure
        trace = kernel._state.transaction_trace
        assert len(trace) > 0, "No transaction trace recorded"
        assert any("FAIL" in t and "Entity 1" in t and "INVENTORY_FULL" in t for t in trace), f"Rejection not found in trace: {trace}"
        
        # 2. Replay Verification
        # Run another kernel with same seed/state and verify trace is bit-identical
        state2 = AuthoritativeState(
            tick=1,
            seed=42,
            entities={1: ent1},
            regions={"reg1": region}
        )
        rng2 = DeterministicRNG(42)
        kernel2 = Kernel(profile, state2, rng2)
        kernel2._final_results = [res]
        kernel2._phase_resolution()
        
        assert kernel2._state.transaction_trace == kernel._state.transaction_trace, "Transaction traces differ across same-seed runs"
        
        # Verify it's in the REFINED_UPDATE event too (mock replay manager check)
        # For simplicity, we just check the state update trace we added.
        print(f"[DEBUG] Trace: {trace[0]}")
