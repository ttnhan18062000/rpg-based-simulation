"""Memory profiling runner for rpg-based-simulation.

Usage:
    python3 scripts/profile_memory.py --suite certification
    python3 scripts/profile_memory.py --suite certification --memray
    python3 scripts/profile_memory.py --suite certification --save-baseline
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SUITE_PATHS: dict[str, list[str]] = {
    "certification": ["tests/certification/"],
    "observability": ["tests/unit/observability/"],
    "full": ["tests/", "--ignore=tests/perf/"],
}

REPORTS_DIR = Path("reports/profiling")

BASE_PYTEST_FLAGS = [
    "--resource-budget", "off",
    "-p", "no:cacheprovider",
    "--tb=short",
]


def check_memray() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "memray", "--version"],
        capture_output=True,
    )
    return result.returncode == 0


def run_suite(suite: str, use_memray: bool, save_baseline: bool) -> int:
    if suite not in SUITE_PATHS:
        print(f"Unknown suite '{suite}'. Valid: {', '.join(SUITE_PATHS)}", file=sys.stderr)
        return 1

    if use_memray and not check_memray():
        print(
            "Memray is not installed. Install it with:\n"
            "    pip install memray\n"
            "Then re-run with --memray.",
            file=sys.stderr,
        )
        return 1

    paths = SUITE_PATHS[suite]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    if use_memray:
        bin_file = f"memray-{suite}-{timestamp}.bin"
        stacks_file = REPORTS_DIR / f"{suite}-{timestamp}.txt"

        cmd = [
            sys.executable, "-m", "memray", "run",
            "-o", bin_file,
            "-m", "pytest",
        ] + BASE_PYTEST_FLAGS + paths

        print(f"Running: {' '.join(cmd)}")
        ret = subprocess.run(cmd).returncode

        # Convert binary to flamegraph-friendly text report
        if Path(bin_file).exists():
            subprocess.run(
                [sys.executable, "-m", "memray", "flamegraph", bin_file,
                 "-o", str(stacks_file)],
                check=False,
            )
            print(f"Report written to {stacks_file}")
    else:
        cmd = [sys.executable, "-m", "pytest"] + BASE_PYTEST_FLAGS + paths
        print(f"Running: {' '.join(cmd)}")
        ret = subprocess.run(cmd).returncode

    peak_rss_mb = _get_peak_rss_mb()
    print(f"Peak RSS: {peak_rss_mb:.1f} MB")

    baseline_file = REPORTS_DIR / "baseline.json"
    if save_baseline:
        baseline_data = {
            "suite": suite,
            "peak_rss_mb": peak_rss_mb,
            "timestamp": timestamp,
        }
        baseline_file.write_text(json.dumps(baseline_data, indent=2))
        print(f"Baseline saved to {baseline_file}")
    elif baseline_file.exists():
        baseline = json.loads(baseline_file.read_text())
        if baseline.get("suite") == suite:
            baseline_rss = baseline["peak_rss_mb"]
            delta = peak_rss_mb - baseline_rss
            pct = (delta / baseline_rss * 100) if baseline_rss else 0
            sign = "+" if delta >= 0 else ""
            print(f"vs baseline ({baseline['timestamp']}): {sign}{delta:.1f} MB ({sign}{pct:.1f}%)")
            if pct > 10:
                print(f"WARNING: Memory regression > 10% vs baseline ({pct:.1f}%)", file=sys.stderr)

    return ret


def _get_peak_rss_mb() -> float:
    try:
        import resource
        peak_kb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        # Linux: ru_maxrss in KB; macOS: bytes
        if sys.platform == "darwin":
            return peak_kb / (1024 * 1024)
        return peak_kb / 1024
    except Exception:
        return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Memory profiling runner")
    parser.add_argument(
        "--suite",
        choices=list(SUITE_PATHS),
        default="certification",
        help="Which test suite to run (default: certification)",
    )
    parser.add_argument(
        "--memray",
        action="store_true",
        help="Wrap run with Memray memory profiler",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save peak RSS as baseline for future comparisons",
    )
    args = parser.parse_args()
    return run_suite(args.suite, args.memray, args.save_baseline)


if __name__ == "__main__":
    sys.exit(main())
