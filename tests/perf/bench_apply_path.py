import sys
import time
import logging
from pathlib import Path
sys.path.append(str(Path.cwd()))
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.apply import ApplyPath

def bench_apply_path():
    count = 5000
    entities = {}
    for i in range(1, count + 1):
        entities[i] = EntityState(id=i, kind="goblin")
    
    state = AuthoritativeState(tick=100, seed=42, entities=entities)
    
    # Scenario 1: Mixed updates (50% no-op, 50% small update)
    updates = {}
    for i in range(1, count + 1):
        if i % 2 == 0:
            updates[i] = EntityUpdate(entity_id=i, readiness_delta=1.0)
        else:
            updates[i] = EntityUpdate(entity_id=i) # NO-OP
            
    state_update = StateUpdate(entity_updates=updates)
    
    pipeline = ApplyPath()
    
    # Warm up
    ApplyPath.apply_generation(state, state_update)
    
    # Benchmark
    start = time.perf_counter_ns()
    new_state = ApplyPath.apply_generation(state, state_update)
    end = time.perf_counter_ns()
    
    duration_ms = (end - start) / 1e6
    print(f"Applied {count} updates (50% no-op) in {duration_ms:.2f}ms")
    
    # Scenario 2: All no-op
    no_op_updates = {i: EntityUpdate(entity_id=i) for i in range(1, count + 1)}
    no_op_state_update = StateUpdate(entity_updates=no_op_updates)
    
    start = time.perf_counter_ns()
    ApplyPath.apply_generation(state, no_op_state_update)
    end = time.perf_counter_ns()
    
    duration_ms = (end - start) / 1e6
    print(f"Applied {count} all no-op updates in {duration_ms:.2f}ms")

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    bench_apply_path()
