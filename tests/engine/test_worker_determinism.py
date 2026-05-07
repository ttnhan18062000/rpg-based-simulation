import pytest
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState, EntityState
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.core.work import WorkItem, WorkClass
from unittest.mock import MagicMock
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction


def _profile(name: str, max_workers: int) -> RuntimeProfile:
    return RuntimeProfile(
        name=name,
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=max_workers,
        max_queue_depth=10,
        max_replay_buffer_kb=0,
        max_tick_budget_ms=10.0,
        max_observability_budget_percent=5.0,
    )


def _make_entity(entity_id: int):
    """
    Build a valid deterministic actor for concurrency equivalence tests.

    Each entity starts on a unique tile and moves to a unique tile, so the
    test avoids occupancy conflicts and combat/tactical randomness.
    """
    x = float(entity_id * 2)

    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(x, 0.0)
        .identity(
            role=EntityRole.HERO,
            faction=Faction.HERO_GUILD,
        )
        .combat(
            hp=100,
            max_hp=100,
            alive=True,
            readiness=100.0,
        )
        .lifecycle(active=True)
        .build()
    )


def _make_move_work(entity_id: int) -> WorkItem:
    x = float(entity_id * 2)

    return WorkItem(
        owner_id=entity_id,
        work_id=f"w:{entity_id}",
        work_class=WorkClass.CRITICAL,
        work_kind="ENTITY_MOVE",
        payload={
            "target_position": (x + 1.0, 0.0),
        },
    )


def test_concurrency_determinism_equivalence():
    """
    M8 Law:
        Local execution and concurrent execution must produce the same
        authoritative state for the same seed, input state, and work list.

    Important:
        This test should not assert a hardcoded readiness drain from an empty
        ENTITY_ACT payload. Empty ENTITY_ACT is not a meaningful deterministic
        action in V2.

    Fraud this catches:
        - concurrent worker result ordering changes authoritative outcome
        - local and concurrent paths apply different movement semantics
        - same seed/input produces different final positions or readiness
    """
    profile_local = _profile("LOCAL", max_workers=0)
    profile_concurrent = _profile("CONCURRENT", max_workers=4)

    entities = {
        i: _make_entity(i)
        for i in range(1, 11)
    }

    state_start = AuthoritativeState(
        tick=0,
        seed=42,
        entities=entities,
    )

    work_items = [
        _make_move_work(i)
        for i in range(1, 11)
    ]

    kernel_local = Kernel(
        profile_local,
        state_start,
        DeterministicRNG(42),
    )
    kernel_local._scheduler.select_work = MagicMock(
        return_value=(work_items, 0)
    )

    kernel_local.tick_once()
    final_state_local = kernel_local._state

    kernel_concurrent = Kernel(
        profile_concurrent,
        state_start,
        DeterministicRNG(42),
    )
    kernel_concurrent._scheduler.select_work = MagicMock(
        return_value=(work_items, 0)
    )

    kernel_concurrent.tick_once()
    final_state_concurrent = kernel_concurrent._state

    assert final_state_local.tick == final_state_concurrent.tick

    for eid in range(1, 11):
        local_entity = final_state_local.entities[eid]
        concurrent_entity = final_state_concurrent.entities[eid]

        assert local_entity.navigation.position == concurrent_entity.navigation.position
        assert local_entity.combat.readiness == concurrent_entity.combat.readiness

        expected_x = float(eid * 2) + 1.0
        assert local_entity.navigation.position == (expected_x, 0.0)


def test_race_resistance_via_sorting():
    """
    Verify that results are sorted by ID so that application order 
    is independent of thread completion noise.
    """
    from src.engine.worker_manager import WorkerManager
    from src.core.worker_protocol import WorkerPacket, WorkerResult
    from src.core.updates import EntityUpdate
    import time
    
    manager = WorkerManager(max_workers=4)
    
    def slow_worker(packet: WorkerPacket) -> WorkerResult:
        # Artificial delay based on ID to jumble completion order
        # Lower IDs sleep longer so they should finish LATER
        delay = (10 - packet.subject.id) * 0.01 
        time.sleep(delay)
        return WorkerResult(
            source_packet_id=packet.packet_id, 
            work_id=packet.work_id,
            entity_id=packet.subject.id, 
            work_class=packet.work_class,
            update=EntityUpdate(entity_id=packet.subject.id, readiness_delta=float(packet.subject.id))
        )

    packets = [
        WorkerPacket(
            packet_id=f"test:{i}", 
            work_id=f"w:{i}",
            tick=0, world_time=0, seed=i, 
            work_class=WorkClass.CRITICAL,
            subject=V2EntityBuilder(i).build(), 
            neighbor_view=[], 
            work_kind="ACT", 
            payload={}
        )
        for i in range(1, 6) # IDs 1 to 5
    ]
    
    results = manager.execute_batch(packets, slow_worker)
    
    # VERIFY: Results are sorted by ID 1, 2, 3, 4, 5
    # Even though ID 5 finished much earlier than ID 1.
    result_ids = [r.entity_id for r in results]
    assert result_ids == [1, 2, 3, 4, 5]
    manager.shutdown()
