#!/usr/bin/env python3
"""
Performance CI Regression Tracker.
Compares current performance results against a stored baseline.
"""
import json
import sys
from pathlib import Path
import subprocess

BASELINE_PATH = Path("reports/perf/baseline.json")
LATEST_PATH = Path("reports/perf/latest.json")
THRESHOLD_PERCENT = 10.0  # Allow 10% variance

def run_benchmarks():
    print("[*] Running benchmarks...")
    subprocess.run([sys.executable, "scripts/run_perf_baseline.py"], check=True)

def compare():
    if not LATEST_PATH.exists():
        print("[!] Latest results not found.")
        return False
        
    if not BASELINE_PATH.exists():
        print("[!] Baseline not found. Setting current results as baseline.")
        BASELINE_PATH.write_text(LATEST_PATH.read_text())
        return True

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)
    with open(LATEST_PATH) as f:
        latest = json.load(f)

    regressions = []
    
    # We focus on p95_tick_compute_ms for high-load scenarios
    critical_scenarios = ["MOVEMENT_1000", "MIXED_1000", "COMBAT_100"]
    
    for scenario_id in critical_scenarios:
        if scenario_id not in latest or scenario_id not in baseline:
            print(f"[?] Scenario {scenario_id} missing in one of the reports.")
            continue
            
        b_p95 = baseline[scenario_id]["p95_tick_compute_ms"]
        l_p95 = latest[scenario_id]["p95_tick_compute_ms"]
        
        diff_percent = ((l_p95 - b_p95) / b_p95) * 100
        
        if diff_percent > THRESHOLD_PERCENT:
            regressions.append(
                f"REGRESSION: {scenario_id} p95 increased by {diff_percent:.2f}% "
                f"({b_p95:.2f}ms -> {l_p95:.2f}ms)"
            )
        elif diff_percent < -THRESHOLD_PERCENT:
            print(f"[+] IMPROVEMENT: {scenario_id} p95 decreased by {abs(diff_percent):.2f}% "
                  f"({b_p95:.2f}ms -> {l_p95:.2f}ms)")
        else:
            print(f"[-] STABLE: {scenario_id} p95 within threshold ({diff_percent:+.2f}%)")

    if regressions:
        print("\n[!] Performance Regressions Detected:")
        for r in regressions:
            print(f"  - {r}")
        return False
    
    print("\n[+] Performance check passed.")
    return True

if __name__ == "__main__":
    run_benchmarks()
    if not compare():
        sys.exit(1)
    sys.exit(0)
