import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState, RegionState, EntityState, ItemStack
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.updates import ResourceTransferIntent, EntityUpdate
from pathlib import Path
import tempfile
from src.core.builder import V2EntityBuilder


def test_transaction_trace_determinism():
    """
    Law: Authoritative decision traces must be identical across same-seed executions.
    This test verifies that rejected transactions are correctly logged and stable.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        profile = RuntimeProfile(
            name="test",
            hardware_class=HardwareClass.CLASS_B,
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
        region = RegionState(id="reg1", name="Region 1", bounds=(0.0, 0.0, 128.0, 128.0), owner_faction_id=1)
        
        # Entity 1: Full inventory (cap 16 is default in V2EntityBuilder)
        # We'll fill it with 16 items to trigger INVENTORY_FULL
        items = [ItemStack(f"item_{i}") for i in range(16)]
        ent1 = (V2EntityBuilder(1)
                .location(10.0, 10.0)
                .inventory(gold=100, items=items)
                .combat(readiness=100.0)
                .build())
        
        state = AuthoritativeState(
            tick=1,
            seed=42,
            entities={1: ent1},
            regions={"reg1": region}
        )
        
        rng = DeterministicRNG(42)
        kernel = Kernel(profile, state, rng, flags={"audit_mode": True})
        
        # Manually inject a failing intent (Harvesting while full)
        intent = ResourceTransferIntent(
            source_id="node_99",
            source_kind="NODE",
            items_add=[ItemStack(item_id="iron", quantity=1)],
            transfer_kind="HARVEST"
        )
        
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
        kernel._phase_advancement()
        
        # Check if trace contains the failure
        trace = kernel._state.transaction_trace
        assert len(trace) > 0, "No transaction trace recorded"
        # In V2, inventory limit is strictly enforced in _resolve_resource_transactions
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
        kernel2 = Kernel(profile, state2, rng2, flags={"audit_mode": True})
        kernel2._final_results = [res]
        kernel2._phase_resolution()
        kernel2._phase_advancement()
        
        assert kernel2._state.transaction_trace == kernel._state.transaction_trace, "Transaction traces differ across same-seed runs"
