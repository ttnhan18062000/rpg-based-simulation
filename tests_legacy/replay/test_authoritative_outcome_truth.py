import pytest
from unittest.mock import MagicMock
from src_legacy.engine.kernel import Kernel
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.core.updates import StateUpdate, EntityUpdate
from src_legacy.core.worker_protocol import WorkerPacket, WorkerResult, ResultStatus
from src_legacy.core.work import WorkClass

@pytest.fixture
def mock_deps():
    from src_legacy.config.profiles import RuntimeProfile, HardwareClass
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
    return {
        "profile": profile,
        "rng": MagicMock(),
        "scheduler": MagicMock(),
        "governor": MagicMock(),
        "status": MagicMock(),
        "replay": MagicMock(),
        "executor": MagicMock(),
    }

def test_replay_sources_from_refined_update(mock_deps):
    """
    Law: Replay-visible truth must be sourced from authoritative post-apply outcomes.
    Scenario: Worker proposes a move, but pipeline REJECTS it due to conflict.
    The replay MUST see the rejection (new_position=None), not the proposal.
    """
    profile = mock_deps["profile"]
    
    # 1. Setup state: Entity 1 at (0,0), Entity 2 at (1,1)
    e1 = EntityState(id=1, kind="H", position=(0.0, 0.0), active=True)
    e2 = EntityState(id=2, kind="H", position=(1.0, 1.0), active=True)
    state = AuthoritativeState(tick=100, seed=42, world_time=1000, entities={1: e1, 2: e2})
    
    kernel = Kernel(
        profile=profile,
        state=state,
        rng=mock_deps["rng"],
        scheduler=mock_deps["scheduler"],
        governor=mock_deps["governor"],
        status=mock_deps["status"],
        replay=mock_deps["replay"],
        executor=mock_deps["executor"]
    )
    
    # 2. Mock worker result: Entity 2 proposes move to (0,0) [CONFLICT]
    proposed_upd = EntityUpdate(entity_id=2, new_position=(0.0, 0.0), moved_this_tick=True)
    res_2 = WorkerResult(
        source_packet_id="100:0",
        work_id="100:1:TEST",
        entity_id=2,
        work_class=WorkClass.CRITICAL,
        update=proposed_upd
    )
    
    source_packet = WorkerPacket(
        packet_id="100:0",
        work_id="100:1:TEST",
        tick=100,
        world_time=1000,
        seed=42,
        work_class=WorkClass.CRITICAL,
        subject=e2,
        neighbor_view=[],
        work_kind="TEST",
        payload={}
    )
    mock_deps["executor"]._source_packets = {"100:0": source_packet}
    mock_deps["executor"].execute.return_value = [res_2]
    mock_deps["governor"].evaluate.return_value = MagicMock(concurrency_limit=1)
    mock_deps["scheduler"].select_work.return_value = ([], 0)
    
    # 3. Run one tick
    # We need to reach _phase_resolution
    kernel._phase_init()
    kernel._phase_scheduling()
    kernel._phase_collection()
    kernel._phase_resolution()
    
    # 4. Verify replay emission
    # Get the last call to replay.emit
    calls = mock_deps["replay"].emit.call_args_list
    # Find the REFINED_UPDATE call
    refined_update_call = next(c for c in calls if c[0][0].event_type == "REFINED_UPDATE")
    emitted_update = refined_update_call[0][0].payload["update"]
    
    # The emitted update MUST have the move REJECTED (refined by pipeline)
    assert emitted_update.entity_updates[2].new_position is None
    assert emitted_update.entity_updates[2].navigation.failure_reason == "OCCUPANCY_CONFLICT"
    
    # It MUST NOT be the raw proposed update
    assert emitted_update.entity_updates[2] != proposed_upd
