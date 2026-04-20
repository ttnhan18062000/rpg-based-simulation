import sys
import os
import json
import logging
from pathlib import Path

# Add src_v2 to path
sys.path.append(os.getcwd())

from src_v2.perf.bench_harness import BenchHarness
from src_v2.core.state import AuthoritativeState, EntityState
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.core.enums import Direction, MovementIntention

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_idle_state() -> AuthoritativeState:
    return AuthoritativeState(tick=1, seed=42, entities={})

def create_movement_stress_state(count: int = 100) -> AuthoritativeState:
    entities = {}
    for i in range(count):
        eid = 100 + i
        x, y = float(i % 10), float(i // 10)
        entities[eid] = EntityState(
            id=eid, kind="actor", position=(x, y), readiness=100.0,
            properties={"work_kind": "ENTITY_MOVE", "payload": {"target_position": (x, y + 1)}}
        )
    return AuthoritativeState(tick=1, seed=42, entities=entities)

def create_harvest_stress_state(count: int = 100) -> AuthoritativeState:
    from src_v2.core.state import ResourceNodeState, InteractionComponent, InventoryComponent
    entities = {}
    nodes = {}
    for i in range(count):
        eid = 200 + i
        nid = 1000 + i
        x, y = float(i % 10), float(i // 10)
        nodes[nid] = ResourceNodeState(id=nid, kind="iron", position=(x, y), yields_item="iron", remaining_charges=10, max_charges=10, required_ticks=3)
        entities[eid] = EntityState(
            id=eid, kind="miner", position=(x, y), readiness=100.0,
            interaction=InteractionComponent(target_node_id=nid, progress=0),
            inventory=InventoryComponent(max_slots=20)
        )
    return AuthoritativeState(tick=1, seed=42, entities=entities, resource_nodes=nodes)

def create_integrated_loop_state(count: int = 100) -> AuthoritativeState:
    # 50% moving, 50% harvesting
    from src_v2.core.state import ResourceNodeState, InteractionComponent, InventoryComponent
    entities = {}
    nodes = {}
    for i in range(count):
        eid = 300 + i
        nid = 2000 + i
        x, y = float(i % 10), float(i // 10)
        if i % 2 == 0:
            # Moving
            entities[eid] = EntityState(id=eid, kind="hero", position=(x, y), readiness=100.0, properties={"work_kind": "ENTITY_MOVE", "payload": {"target_position": (x + 1, y + 1)}})
        else:
            # Harvesting
            nodes[nid] = ResourceNodeState(id=nid, kind="herb", position=(x, y), yields_item="herb", remaining_charges=5, max_charges=5, required_ticks=2)
            entities[eid] = EntityState(id=eid, kind="hero", position=(x, y), readiness=100.0, interaction=InteractionComponent(target_node_id=nid, progress=0), inventory=InventoryComponent(max_slots=5))
    return AuthoritativeState(tick=1, seed=42, entities=entities, resource_nodes=nodes)

def get_profile(name, max_workers=0):
    return RuntimeProfile(
        name=name,
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=80.0,
        max_worker_count=max_workers,
        max_queue_depth=500,
        max_tick_budget_ms=16.6,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0
    )

def run_all_benchmarks():
    # 1. Define Profiles to test
    profiles = [
        get_profile("bench_sequential", max_workers=0),
        get_profile("bench_concurrent", max_workers=4)
    ]

    # 2. Scenarios
    scenarios = [
        ("IDLE_BASELINE", create_idle_state()),
        ("MOVEMENT_STRESS_100", create_movement_stress_state(100)),
        ("HARVEST_STRESS_100", create_harvest_stress_state(100)),
        ("INTEGRATED_LOOP_100", create_integrated_loop_state(100))
    ]

    results = []
    output_dir = Path("reports/performance")
    output_dir.mkdir(parents=True, exist_ok=True)

    for profile in profiles:
        harness = BenchHarness(profile)
        for name, state in scenarios:
            res = harness.run_benchmark(name, state, warmup_ticks=50, sample_ticks=200)
            results.append(res)
            logger.info(f"Done: {profile.name} x {name} -> {res['avg_tps']:.1f} TPS")

    # 3. Export Baseline
    baseline_path = output_dir / "baseline.json"
    with open(baseline_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Performance baseline saved to {baseline_path}")

if __name__ == "__main__":
    run_all_benchmarks()
