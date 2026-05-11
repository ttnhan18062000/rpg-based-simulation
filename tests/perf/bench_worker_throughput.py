import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

from src.core.state import AuthoritativeState, EntityState
from src.core.work import WorkItem, WorkClass
from src.platform.rng import DeterministicRNG
from src.config.profiles import PROD_DEFAULT
from src.engine.executor import ConcurrentExecutionAdapter
from src.engine.worker_manager import WorkerManager
from src.engine.worker_logic import default_simulation_worker

def bench_worker_throughput(as_json: bool = False):
    count = 5000
    entities = {}
    for i in range(1, count + 1):
        entities[i] = EntityState(id=i, kind="goblin")
    
    state = AuthoritativeState(tick=100, seed=42, entities=entities)
    rng = DeterministicRNG(base_seed=42)
    
    work_items = []
    for i in range(1, count + 1):
        work_items.append(WorkItem(
            work_id=f"work_{i}",
            owner_id=i,
            work_kind="ENTITY_ACT",
            work_class=WorkClass.CRITICAL,
            priority=i % 100,
            payload={"action": "wait"}
        ))

    manager = WorkerManager(max_workers=4, max_queue_depth=10000)
    adapter = ConcurrentExecutionAdapter(manager)
    
    # Warm up
    adapter.execute(work_items[:100], state, rng, PROD_DEFAULT)
    
    # Benchmark
    start = time.perf_counter_ns()
    results = adapter.execute(work_items, state, rng, PROD_DEFAULT)
    end = time.perf_counter_ns()
    
    duration_ms = (end - start) / 1e6
    throughput = len(work_items) / (duration_ms / 1000)
    
    stats = manager.get_stats()
    
    report = {
        "scenario": "worker_throughput_5000",
        "entity_count": count,
        "duration_ms": duration_ms,
        "throughput_ips": throughput,
        "worker_utilization": stats["worker_utilization"],
        "max_capacity": stats["max_capacity"]
    }

    if as_json:
        import json
        print(json.dumps(report, indent=2))
    else:
        print(f"Executed {len(work_items)} items in {duration_ms:.2f}ms")
        print(f"Throughput: {throughput:.2f} items/sec")
        print(f"Results returned: {len(results)}")
    
    # Save to latest report
    import os
    import json
    REPORT_DIR = Path("reports/perf")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_DIR / "latest.json", "w") as f:
        json.dump(report, f, indent=2)
    
    manager.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    as_json = "--json" in sys.argv
    bench_worker_throughput(as_json)
