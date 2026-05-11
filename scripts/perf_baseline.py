import json
import os
import subprocess
import sys
from datetime import datetime

BASELINE_PATH = "reports/perf/baseline.json"
LATEST_PATH = "reports/perf/latest.json"

def run_benchmarks():
    print("🚀 Running performance benchmarks...")
    # Run the benchmark script
    # We'll use the existing bench_worker_throughput.py but ensure it outputs JSON
    try:
        result = subprocess.run(
            [sys.executable, "tests/perf/bench_worker_throughput.py", "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        # Assuming the script prints the JSON to stdout or writes to latest.json
        # For now, let's assume it writes to reports/perf/latest.json
        print("✅ Benchmarks completed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Benchmarks failed: {e.stderr}")
        sys.exit(1)

def update_baseline():
    if not os.path.exists(LATEST_PATH):
        print(f"❌ Latest report not found at {LATEST_PATH}")
        sys.exit(1)
    
    with open(LATEST_PATH, 'r') as f:
        latest = json.load(f)
    
    latest["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
    with open(BASELINE_PATH, 'w') as f:
        json.dump(latest, f, indent=2)
    
    print(f"✅ Baseline updated at {BASELINE_PATH}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--update":
        update_baseline()
    else:
        run_benchmarks()
