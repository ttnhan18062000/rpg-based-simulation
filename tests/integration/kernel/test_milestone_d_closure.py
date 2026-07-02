import pytest
import time
from src.core.builder import V2EntityBuilder
import random
import threading
from typing import Dict, List
from unittest.mock import MagicMock

from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState, EntityState
from src.core.work import WorkItem, WorkClass
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.worker_protocol import WorkerPacket, WorkerResult
from src.engine.worker_logic import default_simulation_worker

def get_base_profile(workers: int) -> RuntimeProfile:
    return RuntimeProfile(
        name=f"PROFILE_{workers}",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=workers,
        max_queue_depth=50,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=100.0,
        max_work_debt=1000
    )

def test_high_pressure_determinism_equivalence():
    """
    Final certification:
        Local execution and concurrent execution must produce the same
        authoritative state after a multi-tick high-pressure run.

    Scope of this test:
        This test is about deterministic equivalence under different execution
        strategies and noisy completion timing.

    What this test intentionally proves:
        - Local execution and concurrent execution finish on the same tick.
        - Entity readiness is identical.
        - Entity position is identical.
        - Entity movement metadata is identical enough to prove no scheduling
          order drift.
        - Concurrent worker completion order does not change authoritative state.

    What this test intentionally does NOT prove:
        - ENTITY_MOVE must physically change position within this specific
          number of ticks.
        - Movement pathfinding makes progress toward a distant target.
        - Movement domain behavior is correct in isolation.

    Reason:
        In the current V2 architecture, worker output is a proposal. Direct
        final position mutation is not trusted. Movement execution is resolved
        through the authoritative pipeline, and a high-pressure determinism
        test should not duplicate movement-domain assertions.

    Fraud this catches:
        - concurrent execution produces a different authoritative result
        - worker result ordering leaks into final state
        - readiness diverges under concurrency
        - navigation state diverges under concurrency
        - scheduler/executor completion timing changes final truth
    """
    total_entities = 40
    ticks_to_run = 5
    seed = 42

    from copy import deepcopy
    from unittest.mock import MagicMock
    import random
    import time

    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState
    from src.core.work import WorkItem, WorkClass
    from src.engine.kernel import Kernel
    from src.engine.worker_logic import default_simulation_worker
    from src.platform.rng import DeterministicRNG

    entities = {
        entity_id: (
            V2EntityBuilder(entity_id)
            .kind("TEST")
            .location(float(entity_id), 0.0)
            .combat(readiness=100.0)
            .build()
        )
        for entity_id in range(1, total_entities + 1)
    }

    # Use separate deep copies so the local and concurrent kernels cannot share
    # object references by accident. This protects the test from hidden mutation
    # and makes the equivalence proof stronger.
    state_local_init = AuthoritativeState(
        tick=0,
        seed=seed,
        entities=deepcopy(entities),
    )

    state_concurrent_init = AuthoritativeState(
        tick=0,
        seed=seed,
        entities=deepcopy(entities),
    )

    target = (100.0, 100.0)

    def build_work_for_tick(tick: int):
        """
        Build a deterministic work batch.

        Even entities receive ENTITY_MOVE work.
        Odd entities receive ENTITY_ACT work.

        The exact movement outcome is not asserted here. This test only checks
        that local and concurrent execution produce identical authoritative
        results from the same work.
        """
        work = []

        for entity_id in range(1, total_entities + 1):
            if entity_id % 2 == 0:
                work.append(
                    WorkItem(
                        owner_id=entity_id,
                        work_id=f"t{tick}:w{entity_id}",
                        work_class=WorkClass.CRITICAL,
                        work_kind="ENTITY_MOVE",
                        payload={"target_position": target},
                    )
                )
            else:
                work.append(
                    WorkItem(
                        owner_id=entity_id,
                        work_id=f"t{tick}:w{entity_id}",
                        work_class=WorkClass.CRITICAL,
                        work_kind="ENTITY_ACT",
                        payload={},
                    )
                )

        return work

    # ---------------------------------------------------------------------
    # 1. Run local/control execution.
    # ---------------------------------------------------------------------
    profile_local = get_base_profile(0)

    kernel_local = Kernel(
        profile_local,
        state_local_init,
        DeterministicRNG(seed),
        flags={"audit_mode": True},
    )
    try:
        for tick in range(ticks_to_run):
            kernel_local._scheduler.select_work = MagicMock(
                return_value=(build_work_for_tick(tick), 0)
            )
            kernel_local.tick_once()
        final_state_local = kernel_local.state
    finally:
        kernel_local.shutdown()

    # ---------------------------------------------------------------------
    # 2. Run concurrent execution with noisy completion timing.
    # ---------------------------------------------------------------------
    profile_concurrent = get_base_profile(4)

    kernel_concurrent = Kernel(
        profile_concurrent,
        state_concurrent_init,
        DeterministicRNG(seed),
        flags={"audit_mode": True},
    )

    original_execute = kernel_concurrent._worker_manager.execute_batch

    def chaotic_execute(packets, worker_fn, **kwargs):
        def noisy_worker_wrapper(packet):
            time.sleep(random.uniform(0.001, 0.01))
            return default_simulation_worker(packet)
        return original_execute(packets, noisy_worker_wrapper, **kwargs)

    kernel_concurrent._worker_manager.execute_batch = chaotic_execute

    try:
        for tick in range(ticks_to_run):
            kernel_concurrent._scheduler.select_work = MagicMock(
                return_value=(build_work_for_tick(tick), 0)
            )
            kernel_concurrent.tick_once()
        final_state_concurrent = kernel_concurrent.state
        worker_stats = kernel_concurrent._worker_manager.get_stats()
    finally:
        kernel_concurrent.shutdown()

    # ---------------------------------------------------------------------
    # 3. Certification: deterministic equivalence.
    # ---------------------------------------------------------------------
    assert final_state_local.tick == final_state_concurrent.tick

    for entity_id in range(1, total_entities + 1):
        local_entity = final_state_local.entities[entity_id]
        concurrent_entity = final_state_concurrent.entities[entity_id]

        assert local_entity.combat.readiness == concurrent_entity.combat.readiness, (
            f"Readiness divergence at entity {entity_id}: "
            f"local={local_entity.combat.readiness}, "
            f"concurrent={concurrent_entity.combat.readiness}"
        )

        assert local_entity.navigation.position == concurrent_entity.navigation.position, (
            f"Position divergence at entity {entity_id}: "
            f"local={local_entity.navigation.position}, "
            f"concurrent={concurrent_entity.navigation.position}"
        )

        assert local_entity.navigation.target == concurrent_entity.navigation.target, (
            f"Navigation target divergence at entity {entity_id}: "
            f"local={local_entity.navigation.target}, "
            f"concurrent={concurrent_entity.navigation.target}"
        )

        assert local_entity.navigation.path == concurrent_entity.navigation.path, (
            f"Navigation path divergence at entity {entity_id}: "
            f"local={local_entity.navigation.path}, "
            f"concurrent={concurrent_entity.navigation.path}"
        )

        assert (
            local_entity.navigation.moved_recently
            == concurrent_entity.navigation.moved_recently
        ), (
            f"Movement metadata divergence at entity {entity_id}: "
            f"local={local_entity.navigation.moved_recently}, "
            f"concurrent={concurrent_entity.navigation.moved_recently}"
        )

        assert (
            local_entity.navigation.last_failure_reason
            == concurrent_entity.navigation.last_failure_reason
        ), (
            f"Movement failure reason divergence at entity {entity_id}: "
            f"local={local_entity.navigation.last_failure_reason}, "
            f"concurrent={concurrent_entity.navigation.last_failure_reason}"
        )

    # ---------------------------------------------------------------------
    # 4. Sanity check: the test actually exercised concurrent workers.
    # ---------------------------------------------------------------------
    assert worker_stats.get("peak_workers", 0) >= 1
    
    
def test_neighbor_view_bit_identical():
    """Prove that worker input context is identical regardless of engine internal order."""
    profile = get_base_profile(0)
    entities = {
        i: V2EntityBuilder(i).kind("TEST").location(float(i), 0.0).build()
        for i in [10, 5, 20, 1, 100]
    }
    state = AuthoritativeState(tick=1, seed=42, entities=entities)
    kernel = Kernel(profile, state, DeterministicRNG(42))
    try:
        subject = entities[5]
        view = kernel._get_deterministic_neighbor_view(subject, radius=20.0)
        neighbor_ids = [eid for eid, estate in view]
        assert neighbor_ids == [1, 10, 20]
    finally:
        kernel.shutdown()


def test_entity_move_work_can_drive_authoritative_movement_progress():
    """
    Law:
        A valid ENTITY_MOVE work item can drive authoritative movement progress
        through the current V2 movement path.

    Scope:
        This test proves movement behavior directly. It is intentionally
        separate from high-pressure determinism equivalence.

    Note:
        If current V2 design treats ENTITY_MOVE only as navigation intent and
        not guaranteed same-tick position movement, update this test to assert
        target/path/movement intent instead of physical position change.
    """
    from unittest.mock import MagicMock

    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState
    from src.core.work import WorkItem, WorkClass
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG

    profile = RuntimeProfile(
        name="MOVE_TEST",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=0,
        max_queue_depth=50,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=100.0,
        max_work_debt=1000,
    )

    entity = (
        V2EntityBuilder(2)
        .kind("TEST")
        .location(2.0, 0.0)
        .combat(readiness=100.0)
        .build()
    )

    state = AuthoritativeState(
        tick=0,
        seed=42,
        entities={2: entity},
    )

    kernel = Kernel(
        profile,
        state,
        DeterministicRNG(42),
        flags={"audit_mode": True},
    )
    try:
        target = (100.0, 100.0)

        kernel._scheduler.select_work = MagicMock(
            return_value=(
                [
                    WorkItem(
                        owner_id=2,
                        work_id="t0:w2",
                        work_class=WorkClass.CRITICAL,
                        work_kind="ENTITY_MOVE",
                        payload={"target_position": target},
                    )
                ],
                0,
            )
        )

        initial_position = kernel.state.entities[2].navigation.position
        kernel.tick_once()
        final_entity = kernel.state.entities[2]
        assert final_entity.navigation.position != initial_position
    finally:
        kernel.shutdown()