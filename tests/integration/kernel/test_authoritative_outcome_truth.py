import pytest
from unittest.mock import MagicMock

from src.core.builder import V2EntityBuilder
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate
from src.core.worker_protocol import WorkerPacket, WorkerResult
from src.core.work import WorkClass
from src.core.enums import EntityRole, Faction
from src.engine.governor import ResourceGovernor
from src.engine.runtime_status import RuntimeStatus


@pytest.fixture
def mock_deps():
    from src.config.profiles import RuntimeProfile, HardwareClass

    profile = RuntimeProfile(
        name="test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=100.0,
    )

    replay = MagicMock()
    replay.get_stats.return_value = {"backlog_kb": 0}
    replay.emit = MagicMock()

    executor = MagicMock()
    executor.set_concurrency_limit = MagicMock()

    scheduler = MagicMock()

    return {
        "profile": profile,
        "rng": MagicMock(),
        "scheduler": scheduler,
        "governor": ResourceGovernor(),
        "status": RuntimeStatus(),
        "replay": replay,
        "executor": executor,
    }


def test_replay_sources_from_refined_update(mock_deps):
    """
    Law:
        Replay-visible truth must be sourced from authoritative post-apply
        outcomes, not from raw worker proposals.

    Scenario:
        Worker proposes that entity 2 moves into entity 1's occupied tile.
        The authoritative pipeline must reject the move with
        OCCUPANCY_CONFLICT.

    Fraud this catches:
        - replay emits raw worker proposals instead of refined updates
        - kernel applies worker results before authoritative refinement
        - conflict rejection is present in state but absent from replay
        - replay event is emitted before AuthoritativeApplyPipeline.refine(...)
    """
    profile = mock_deps["profile"]

    e1 = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )

    e2 = (
        V2EntityBuilder(2)
        .kind("hero")
        .location(1.0, 1.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )

    state = AuthoritativeState(
        tick=100,
        seed=42,
        world_time=1000,
        entities={
            1: e1,
            2: e2,
        },
    )

    kernel = Kernel(
        profile=profile,
        state=state,
        rng=mock_deps["rng"],
        scheduler=mock_deps["scheduler"],
        governor=mock_deps["governor"],
        status=mock_deps["status"],
        replay=mock_deps["replay"],
        executor=mock_deps["executor"],
    )

    proposed_upd = EntityUpdate(
        entity_id=2,
        new_position=(0.0, 0.0),
        moved_this_tick=True,
    )

    res_2 = WorkerResult(
        source_packet_id="100:0",
        work_id="100:1:TEST",
        entity_id=2,
        work_class=WorkClass.CRITICAL,
        update=proposed_upd,
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
        payload={},
    )

    mock_deps["executor"]._source_packets = {"100:0": source_packet}
    mock_deps["executor"].execute.return_value = [res_2]

    # No scheduled work is needed for this test because executor is mocked
    # to return the worker result directly.
    mock_deps["scheduler"].select_work.return_value = ([], 0)

    kernel._phase_init()
    kernel._phase_scheduling()
    kernel._phase_collection()
    kernel._phase_resolution()

    calls = mock_deps["replay"].emit.call_args_list

    refined_update_call = next(
        c for c in calls
        if c[0][0].event_type == "REFINED_UPDATE"
    )

    emitted_update = refined_update_call[0][0].payload["update"]

    emitted_entity_update = emitted_update.entity_updates[2]

    assert emitted_entity_update.new_position is None
    assert emitted_entity_update.navigation is not None
    assert emitted_entity_update.navigation.failure_reason == "OCCUPANCY_CONFLICT"

    # Replay must contain the refined authoritative result, not the raw worker
    # proposal.
    assert emitted_entity_update != proposed_upd