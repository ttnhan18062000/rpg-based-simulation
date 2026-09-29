from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_idle_state, build_resource_state, build_mixed_state

import logging

# Suppress engine debug noise during benchmarks
logging.getLogger().setLevel(logging.WARNING)

REPORTS_DIR = Path("reports/perf/profiles")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def run_suite():
    """
    Runs benchmarks across RAM profiles to identify the best production default.
    """
    profiles_to_test = [
        PERF_PROFILES["PERF_512MB_CONC"],
        PERF_PROFILES["PERF_1GB_CONC"],
        PERF_PROFILES["PERF_2GB_CONC"],
        PERF_PROFILES["PERF_4GB_CONC"],
    ]
    
    # We use smaller entity counts for fast verification during this turn,
    # but enough to show a trend.
    workloads = [
        ("IDLE_50", build_idle_state(entity_count=50)),
        ("IDLE_100", build_idle_state(entity_count=100)),
        ("IDLE_250", build_idle_state(entity_count=250)),
        ("MIXED_100", build_mixed_state(entity_count=100)),
    ]
    
    summary = {}
    
    for profile in profiles_to_test:
        print(f"\n[*] Testing Profile: {profile.name} ({profile.max_ram_mb}MB)")
        profile_results = {}
        for scenario_id, state in workloads:
            print(f"    - Running {scenario_id}...")
            harness = BenchHarness(profile)
            try:
                result = harness.run_benchmark(
                    scenario_id=scenario_id,
                    initial_state=state,
                    warmup_ticks=10,
                    sample_ticks=10
                )
                profile_results[scenario_id] = {
                    "p95_ms": result["tick_ms"]["p95"],
                    "avg_tps": result["avg_tps"],
                    "peak_rss": result["mem_rss_mb"]["max"]
                }
                print(f"      p95: {result['tick_ms']['p95']:.2f}ms | RSS: {result['mem_rss_mb']['max']:.1f}MB")
            except Exception as e:
                print(f"      [!] FAILED: {e}")
                profile_results[scenario_id] = "CRASHED"
        
        summary[profile.name] = profile_results
        
    with open(REPORTS_DIR / "comparison.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n[+] Comparison complete. Results saved to {REPORTS_DIR / 'comparison.json'}")

if __name__ == "__main__":
    run_suite()
