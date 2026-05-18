import sys
import os
import time
from unittest.mock import MagicMock, patch
import dataclasses

# Ensure local imports work
sys.path.append(os.getcwd())

from src.perf.scenarios import build_idle_state, build_movement_state
from src.engine.apply import ApplyPath
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.cadence import SystemCadence

def profile_replace_churn():
    print("\n--- Profiling dataclasses.replace Churn ---")
    
    state = build_idle_state(entity_count=1000)
    cadence = SystemCadence()
    
    with patch("dataclasses.replace", wraps=dataclasses.replace) as mock_replace:
        start_time = time.time()
        new_state = ApplyPath.apply_passive(state, cadence=cadence)
        duration = (time.time() - start_time) * 1000
        print(f"apply_passive (1000 idle entities): {duration:.2f}ms, replace calls: {mock_replace.call_count}")

    # Test with SOME changes
    # Every 10th entity has a biological update due
    cadence_bio = SystemCadence(biological=10)
    with patch("dataclasses.replace", wraps=dataclasses.replace) as mock_replace:
        start_time = time.time()
        new_state = ApplyPath.apply_passive(state, cadence=cadence_bio)
        duration = (time.time() - start_time) * 1000
        print(f"apply_passive (1000 entities, 10% bio due): {duration:.2f}ms, replace calls: {mock_replace.call_count}")

    # StateUpdate.merge Benchmark
    base_upd = StateUpdate()
    updates = [StateUpdate(entity_updates={i: EntityUpdate(entity_id=i, new_position=(float(i), float(i)))}) for i in range(100)]
    
    start = time.perf_counter()
    merged = base_upd
    for u in updates:
        merged = merged.merge(u)
    dur_serial = (time.perf_counter() - start) * 1000
    
    start = time.perf_counter()
    merged_batch = base_upd.merge_many(updates)
    dur_batch = (time.perf_counter() - start) * 1000
    
    print(f"StateUpdate.merge (100 serial): {dur_serial:.2f}ms")
    print(f"StateUpdate.merge_many (100 batch): {dur_batch:.2f}ms")

def profile_dirty_set_cost():
    print("\n--- Profiling DirtySet.from_update Cost ---")
    state = build_idle_state(entity_count=1000)
    
    from src.core.dirty import DirtySet
    
    # 1. Empty update
    update_empty = StateUpdate()
    start_time = time.time()
    for _ in range(100):
        ds = DirtySet.from_update(state, update_empty)
    duration = (time.time() - start_time) * 1000 / 100
    print(f"DirtySet.from_update (1000 entities, empty update): {duration:.4f}ms per call")

    # 2. Full update (1000 entities)
    update_full = StateUpdate(entity_updates={i: EntityUpdate(entity_id=i, new_position=(1.0, 1.0)) for i in range(1, 1001)})
    start_time = time.time()
    for _ in range(100):
        ds = DirtySet.from_update(state, update_full)
    duration = (time.time() - start_time) * 1000 / 100
    print(f"DirtySet.from_update (1000 entities, full update): {duration:.4f}ms per call")

if __name__ == "__main__":
    profile_replace_churn()
    profile_dirty_set_cost()
