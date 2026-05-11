from __future__ import annotations
import json
import time
from pathlib import Path
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_idle_state, build_resource_state, build_movement_state, build_combat_arena_state, build_strategic_state, build_mixed_state

import logging

# Suppress engine debug noise during benchmarks
logging.getLogger().setLevel(logging.WARNING)

REPORTS_DIR = Path("reports/perf")
LATEST_PATH = REPORTS_DIR / "latest.json"

def main():
    """
    Runs a full suite of performance benchmarks and aggregates results into latest.json.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}
    
    scenarios = [
        ("IDLE_100", PERF_PROFILES["PERF_512MB_LOCAL"], build_idle_state(entity_count=100), {"resolution": 100.0}),
        ("IDLE_500", PERF_PROFILES["PERF_1GB_LOCAL"], build_idle_state(entity_count=500), {"resolution": 100.0}),
        ("IDLE_1000", PERF_PROFILES["PERF_2GB_LOCAL"], build_idle_state(entity_count=1000), {"resolution": 100.0}),
        ("IDLE_5000", PERF_PROFILES["PERF_4GB_LOCAL"], build_idle_state(entity_count=5000), {"resolution": 100.0}),
        ("MOVEMENT_1000", PERF_PROFILES["PERF_2GB_LOCAL"], build_movement_state(entity_count=1000), {"resolution": 100.0}),
        ("RESOURCE_1000", PERF_PROFILES["PERF_2GB_LOCAL"], build_resource_state(entity_count=1000, node_count=500), {"resolution": 100.0}),
        ("COMBAT_100", PERF_PROFILES["PERF_2GB_LOCAL"], build_combat_arena_state(team_a_count=50, team_b_count=50), {"resolution": 100.0}),
        ("STRATEGIC_500", PERF_PROFILES["PERF_2GB_LOCAL"], build_strategic_state(entity_count=500), {"resolution": 100.0}),
        ("MIXED_1000", PERF_PROFILES["PERF_4GB_CONC"], build_mixed_state(entity_count=1000), {"resolution": 100.0}),
    ]
    
    for scenario_id, profile, state, budgets in scenarios:
        print(f"[*] Running {scenario_id} ({profile.name})...")
        harness = BenchHarness(profile)
        result = harness.run_benchmark(
            scenario_id=scenario_id,
            initial_state=state,
            warmup_ticks=10,
            sample_ticks=50,
            phase_budgets=budgets
        )
        results[scenario_id] = result
        print(f"    p95: {result['p95_tick_compute_ms']:.2f}ms | TPS: {result['avg_tps']:.1f} | RSS: {result['peak_rss_mb']:.1f}MB")

    with open(LATEST_PATH, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[+] Baseline complete. Results saved to {LATEST_PATH}")

if __name__ == "__main__":
    main()
