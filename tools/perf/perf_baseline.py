"""Run the scenario benchmark suite, or promote its result to the baseline.

Default: run ``tools/perf/run_perf_baseline.py`` (the one writer of ``reports/perf/latest.json``).
``--update``: validate ``latest.json`` and copy it to ``reports/perf/baseline.json``.

``--update`` refuses anything that is not a scenario-keyed dict of ``BenchHarness`` result dicts,
because ``tools/release/generate_optimization_proof.py`` reads ``baseline.json`` in exactly that
shape (TCK-20261004-PERF-LATEST-JSON-SINGLE-WRITER).
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

BASELINE_PATH = "reports/perf/baseline.json"
LATEST_PATH = "reports/perf/latest.json"
RUN_SCRIPT = "tools/perf/run_perf_baseline.py"

# Every scenario entry must carry these keys (compute_tps may be given as its legacy alias avg_tps).
REQUIRED_KEYS = ("scenario_id", "profile", "sample_ticks", "tick_ms", "mem_rss_mb")


def validate_latest(data):
    """Return None when ``data`` is a valid scenario-keyed result, else a message naming the problem."""
    if not isinstance(data, dict) or not data:
        return "latest.json must be a non-empty dict keyed by scenario id"
    for key, entry in data.items():
        if not isinstance(entry, dict):
            return f"entry {key!r} is not a dict (not a scenario-keyed benchmark result)"
        missing = [k for k in REQUIRED_KEYS if k not in entry]
        if "compute_tps" not in entry and "avg_tps" not in entry:
            missing.append("compute_tps")
        if missing:
            return f"entry {key!r} is missing {', '.join(missing)}"
        if entry["scenario_id"] != key:
            return f"entry {key!r} has scenario_id {entry['scenario_id']!r}, expected {key!r}"
    return None


def run_benchmarks():
    print("Running performance benchmarks (scenario suite)...")
    try:
        subprocess.run([sys.executable, RUN_SCRIPT], capture_output=True, text=True, check=True)
        print("Benchmarks completed.")
    except subprocess.CalledProcessError as e:
        print(f"Benchmarks failed: {e.stderr}")
        return 1
    return 0


def update_baseline():
    if not os.path.exists(LATEST_PATH):
        print(f"Latest report not found at {LATEST_PATH}")
        return 1

    with open(LATEST_PATH, "r") as f:
        try:
            latest = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Refusing to promote: {LATEST_PATH} is not valid JSON ({e})")
            return 1

    problem = validate_latest(latest)
    if problem:
        print(f"Refusing to promote {LATEST_PATH}: {problem}. {BASELINE_PATH} is unchanged.")
        return 1

    latest["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
    with open(BASELINE_PATH, "w") as f:
        json.dump(latest, f, indent=2)

    print(f"Baseline updated at {BASELINE_PATH}")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--update":
        return update_baseline()
    return run_benchmarks()


if __name__ == "__main__":
    sys.exit(main())
