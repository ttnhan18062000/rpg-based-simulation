import json
import sys
from pathlib import Path

def generate_report():
    """
    Generate a summary performance report from the matrix JSON results.
    M5 Law: Reports must be clear, comparable, and include phase-level breakdown.
    """
    input_dir = Path("reports/perf")
    matrix_file = input_dir / "matrix_full.json"
    
    if not matrix_file.exists():
        # Try to find individual JSONs if matrix_full is missing
        json_files = list(input_dir.glob("*.json"))
        if not json_files or (len(json_files) == 1 and json_files[0].name == "baseline.json"):
            print(f"Error: No matrix results found in {input_dir}. Run scripts/run_benchmarks.py first.")
            return
        results = []
        for jf in json_files:
            if jf.name in ["matrix_full.json", "baseline.json"]: continue
            with open(jf, "r") as f:
                results.append(json.load(f))
    else:
        with open(matrix_file, "r") as f:
            results = json.load(f)

    print("\n" + "="*80)
    print(" V2 ENGINE PERFORMANCE MATRIX SUMMARY")
    print("="*80)
    print(f"{'Scenario':<12} | {'Scale':>6} | {'Mode':<10} | {'TPS':>8} | {'p95 ms':>8} | {'RSS MB':>8}")
    print("-" * 65)

    # Sort by scenario, then scale, then mode
    # Some results might not have the matrix_* keys if they are from older runs
    results.sort(key=lambda x: (x.get("matrix_scenario", ""), x.get("matrix_scale", 0), x.get("matrix_mode", "")))

    for res in results:
        scenario = res.get("matrix_scenario", res.get("scenario_id", "unknown"))
        scale = res.get("matrix_scale", "n/a")
        mode = res.get("matrix_mode", "n/a")
        tps = res.get("compute_tps", 0.0)
        p95 = res.get("tick_ms", {}).get("p95", 0.0)
        rss = res.get("mem_rss_mb", {}).get("max", 0.0)
        
        print(f"{scenario:<12} | {scale:>6} | {mode:<10} | {tps:>8.1f} | {p95:>8.2f} | {rss:>8.1f}")

    # Phase Breakdown for the largest mixed scenario
    largest_mixed = [r for r in results if r.get("matrix_scenario") == "mixed"]
    if largest_mixed:
        # Get the one with largest scale
        res = max(largest_mixed, key=lambda x: x.get("matrix_scale", 0))
        print(f"\nPhase Cost Distribution ({res['matrix_scenario']} {res['matrix_scale']} {res['matrix_mode']}):")
        breakdown = res.get("phase_breakdown", {})
        sorted_phases = sorted(breakdown.items(), key=lambda x: x[1].get("avg", 0), reverse=True)
        for phase, stats in sorted_phases:
            print(f"  {phase:<30}: {stats.get('avg', 0):>6.2f}ms (avg), {stats.get('p95', 0):>6.2f}ms (p95)")

    print("="*80 + "\n")

if __name__ == "__main__":
    generate_report()
