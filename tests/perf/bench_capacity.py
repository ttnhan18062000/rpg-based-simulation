import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.core.dirty import DirtySet
from src.engine.pipeline_phases.capacity_enforcement import CapacityEnforcementPhase
from src.core.strategic import StrategicComponent, LeadState

def bench_capacity_enforcement():
    # Setup 5000 entities
    entities = {}
    for i in range(5000):
        entities[i] = EntityState(id=i, kind="goblin")
    
    state = AuthoritativeState(tick=100, seed=42, entities=entities)
    
    # 1. Update with only 1 dirty entity
    strategic_upd = StrategicUpdate(
        leads_add_or_update=[LeadState(id=f"lead_{j}", kind="test", subject="test") for j in range(20)]
    )
    entity_updates = {0: EntityUpdate(entity_id=0, strategic=strategic_upd)}
    
    dirty = DirtySet(strategic_entities={0})
    update = StateUpdate(entity_updates=entity_updates, dirty_set=dirty)
    
    # Benchmark
    start = time.perf_counter_ns()
    for _ in range(100):
        CapacityEnforcementPhase.enforce(state, update)
    end = time.perf_counter_ns()
    
    avg_ms = (end - start) / 1e6 / 100
    print(f"CapacityEnforcementPhase (1 dirty, 5000 total) avg: {avg_ms:.4f}ms")
    
    # 2. Compare with full dirty (simulating old O(N) behavior if we hadn't optimized)
    # Actually, we can't easily "un-optimize" but we can see the current cost.
    
    # Let's see what happens if many are dirty
    dirty_many = DirtySet(strategic_entities=set(range(100)))
    update_many = StateUpdate(
        entity_updates={i: EntityUpdate(entity_id=i, strategic=strategic_upd) for i in range(100)},
        dirty_set=dirty_many
    )
    
    start = time.perf_counter_ns()
    for _ in range(100):
        CapacityEnforcementPhase.enforce(state, update_many)
    end = time.perf_counter_ns()
    
    avg_many_ms = (end - start) / 1e6 / 100
    print(f"CapacityEnforcementPhase (100 dirty, 5000 total) avg: {avg_many_ms:.4f}ms")

if __name__ == "__main__":
    bench_capacity_enforcement()
