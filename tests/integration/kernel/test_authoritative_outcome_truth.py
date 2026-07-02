import pytest
from unittest.mock import MagicMock

from src.core.builder import V2EntityBuilder
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, StateUpdate
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
        max_tick_budget_ms=10000.0,
    )

    from src.core.lifecycle import LifecycleOutcome
    replay = MagicMock()
    replay.get_stats.return_value = {"backlog_kb": 0}
    replay.emit = MagicMock()
    replay.finalize.return_value = LifecycleOutcome.SUCCESS
    replay.replay_metrics.return_value = {"pending_replay_flushes": 0}

    executor = MagicMock()
    executor.set_concurrency_limit = MagicMock()

    scheduler = MagicMock()

    rng = MagicMock()
    rng.get_state.return_value = None

    return {
        "profile": profile,
        "rng": rng,
        "scheduler": scheduler,
        "governor": ResourceGovernor(),
        "status": RuntimeStatus(),
        "replay": replay,
        "executor": executor,
    }


def test_replay_sources_from_refined_update(mock_deps):
    """
    Law:
        Replay-visible truth must be sourced from authoritative post-refine
        outcomes, not from raw worker proposals.

    Scenario:
        Worker directly proposes:

            EntityUpdate(new_position=(0, 0), moved_this_tick=True)

        for entity 2.

        This is not a valid semantic movement intent. It is a direct final
        position mutation. In the latest source architecture, direct final
        movement is rejected by TrustBoundaryPhase before MovementPhase or
        OccupancyPhase can process it.

    Expected:
        The replay-visible REFINED_UPDATE must contain the authoritative
        trust-boundary rejection:

            failure_reason == "UNTRUSTED_DIRECT_MOVEMENT"

        It must not expose the raw worker proposal as the refined truth.

    Important distinction:
        OCCUPANCY_CONFLICT belongs to OccupancyPhase and should be tested
        separately with an already-authoritative movement result.

        Raw worker direct new_position does not reach OccupancyPhase because
        TrustBoundaryPhase strips it first.

    Fraud this catches:
        - replay emits raw worker proposals instead of refined updates
        - kernel applies worker results before authoritative refinement
        - trust-boundary rejection is present in state but absent from replay
        - replay event is emitted before AuthoritativeApplyPipeline.refine(...)
        - raw direct new_position reaches replay as authoritative truth
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
    try:
        # Raw worker proposal intentionally tries to bypass the movement system by
        # directly setting final position. This must never become authoritative.
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

        mock_deps["executor"]._source_packets = {
            "100:0": source_packet,
        }
        mock_deps["executor"].execute.return_value = [res_2]

        # No scheduled work is needed for this test because executor is mocked
        # to return the worker result directly.
        mock_deps["scheduler"].select_work.return_value = ([], 0)

        kernel._phase_init()
        kernel._phase_scheduling()
        kernel._phase_collection()
        kernel._phase_resolution()

        calls = mock_deps["replay"].emit.call_args_list

        refined_update_events = [
            call[0][0]
            for call in calls
            if call[0][0].event_type == "REFINED_UPDATE"
        ]

        assert refined_update_events, (
            "Expected at least one REFINED_UPDATE replay event"
        )

        raw_like_refined_events = []
        trust_rejection_events = []

        for event in refined_update_events:
            emitted_update = event.payload["update"]
            emitted_entity_update = emitted_update.entity_updates.get(2)

            if emitted_entity_update is None:
                continue

            if emitted_entity_update == proposed_upd:
                raw_like_refined_events.append(event)

            if (
                emitted_entity_update.new_position is None
                and emitted_entity_update.moved_this_tick is False
                and emitted_entity_update.navigation is not None
                and emitted_entity_update.navigation.failure_reason
                == "UNTRUSTED_DIRECT_MOVEMENT"
            ):
                trust_rejection_events.append(event)

        assert not raw_like_refined_events, (
            "REFINED_UPDATE must never emit the raw worker proposal as "
            "authoritative truth"
        )

        assert trust_rejection_events, (
            "Expected a REFINED_UPDATE event containing authoritative "
            "UNTRUSTED_DIRECT_MOVEMENT rejection for entity 2"
        )

        emitted_update = trust_rejection_events[-1].payload["update"]
        emitted_entity_update = emitted_update.entity_updates[2]

        assert emitted_entity_update.new_position is None
        assert emitted_entity_update.moved_this_tick is False
        assert emitted_entity_update.navigation is not None
        assert (
            emitted_entity_update.navigation.failure_reason
            == "UNTRUSTED_DIRECT_MOVEMENT"
        )

        # Replay must contain the refined authoritative result, not the raw worker
        # proposal.
        assert emitted_entity_update != proposed_upd

        assert (
            emitted_update.rejections_delta.get("UNTRUSTED_DIRECT_MOVEMENT", 0)
            >= 1
        )

        assert any(
            event.actor_id == 2
            and event.action_kind == "GLOBAL_PROPOSAL"
            and event.reason == "UNTRUSTED_DIRECT_MOVEMENT"
            for event in emitted_update.rejection_events
        )
    finally:
        kernel.shutdown(timeout_s=1.0)
    
    
def test_occupancy_phase_rejects_authoritative_position_overlap():
    """
    Law:
        OccupancyPhase rejects final authoritative movement results that would
        place an entity into an occupied tile.

    Why this is separate from trust-boundary replay tests:
        TrustBoundaryPhase rejects raw worker direct new_position proposals
        before they reach OccupancyPhase.

        This test calls OccupancyPhase directly with an already-authoritative
        movement result. That is the correct scope for OCCUPANCY_CONFLICT.

    Scenario:
        Entity 1 already occupies (0, 0).
        Entity 2 has an authoritative movement result proposing (0, 0).

    Expected:
        Entity 2 movement is rejected with OCCUPANCY_CONFLICT.
    """
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
        .location(1.0, 0.0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )

    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={
            1: e1,
            2: e2,
        },
    )

    update = StateUpdate(
        entity_updates={
            2: EntityUpdate(
                entity_id=2,
                new_position=(0.0, 0.0),
                moved_this_tick=True,
            )
        }
    )

    from src.engine.pipeline_phases.occupancy import OccupancyPhase

    refined = OccupancyPhase.resolve(state, update)
    entity_update = refined.entity_updates[2]

    assert entity_update.new_position is None
    assert entity_update.moved_this_tick is False
    assert entity_update.navigation is not None
    assert entity_update.navigation.failure_reason == "OCCUPANCY_CONFLICT"

    assert refined.rejections_delta.get("OCCUPANCY_CONFLICT", 0) == 1

    assert any(
        event.actor_id == 2
        and event.action_kind == "MOVE"
        and event.reason == "OCCUPANCY_CONFLICT"
        for event in refined.rejection_events
    )