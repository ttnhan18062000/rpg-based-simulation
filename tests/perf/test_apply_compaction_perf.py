import time
import pytest
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate
from src.engine.compactor import StateUpdateCompactor
from src.engine.apply import ApplyPath


def test_apply_compaction_performance_gain():
    """
    Demonstrates the throughput improvement when compacting 5000 entity updates.
    Scenario: 5000 entities where 80% of updates are no-ops or redundant property updates.
    """
    count = 5000
    entities = {}
    for i in range(1, count + 1):
        entities[i] = (
            V2EntityBuilder(i)
            .kind("WARRIOR")
            .location(10.0, 20.0)
            .identity(properties={"faction": "Guard", "status": "Patrolling"})
            .build()
        )

    state = AuthoritativeState(tick=100, seed=42, world_time=100, entities=entities)

    updates = {}
    for i in range(1, count + 1):
        if i % 5 == 0:
            # 20% meaningful combat updates
            updates[i] = EntityUpdate(
                entity_id=i, combat=CombatUpdate(hp_delta=-10)
            )
        elif i % 5 == 1:
            # 20% zero-delta combat updates (no-op)
            updates[i] = EntityUpdate(
                entity_id=i, combat=CombatUpdate(hp_delta=0)
            )
        elif i % 5 == 2:
            # 20% redundant property updates (no-op)
            updates[i] = EntityUpdate(
                entity_id=i, property_updates={"status": "Patrolling"}
            )
        elif i % 5 == 3:
            # 20% redundant kind/position updates (no-op)
            updates[i] = EntityUpdate(
                entity_id=i, kind_set="WARRIOR", new_position=(10.0, 20.0)
            )
        else:
            # 20% empty updates (no-op)
            updates[i] = EntityUpdate(entity_id=i)

    raw_update = StateUpdate(entity_updates=updates)

    # 1. Measure raw ApplyPath performance
    t0 = time.perf_counter_ns()
    raw_state = ApplyPath.apply_generation(state, raw_update)
    raw_ms = (time.perf_counter_ns() - t0) / 1e6

    # 2. Measure compaction + ApplyPath performance
    t1 = time.perf_counter_ns()
    compacted_update, metrics = StateUpdateCompactor.compact_with_metrics(state, raw_update)
    compacted_state = ApplyPath.apply_generation(state, compacted_update)
    compacted_ms = (time.perf_counter_ns() - t1) / 1e6

    print(f"\n--- Compaction Benchmark (N={count}) ---")
    print(f"Raw Updates: {metrics.raw_entity_updates}")
    print(f"Compacted Updates: {metrics.compacted_entity_updates}")
    print(f"Dropped No-op Updates: {metrics.dropped_noop_updates}")
    print(f"Property Prunings: {metrics.property_prunings}")
    print(f"Raw ApplyPath Duration: {raw_ms:.2f}ms")
    print(f"Compacted (Compaction + ApplyPath) Duration: {compacted_ms:.2f}ms")

    # Verify semantic equivalence
    assert raw_state.fingerprint() == compacted_state.fingerprint()
    assert metrics.compacted_entity_updates == count // 5
