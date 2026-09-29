#!/usr/bin/env python3
"""
memory_probe.py — memory and resource debugging tool for the RPG simulation engine.

Usage:
    python scripts/memory_probe.py                          # lightweight inline report
    python scripts/memory_probe.py --output report.json    # also write JSON
    python scripts/memory_probe.py --simulate-leak         # demonstrate worker thread leak
    python scripts/memory_probe.py --flamegraph            # memray HTML flamegraph (requires memray)
    python scripts/memory_probe.py --flamegraph --simulate-leak --output reports/leak.html
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.tools.memory_probe import (
    MemoryReport,
    MemorySnapshot,
    assert_no_worker_leak,
    count_drain_workers,
    count_event_recorders,
    snapshot_end,
    snapshot_start,
)


# ---------------------------------------------------------------------------
# Workload
# ---------------------------------------------------------------------------

def run_workload(simulate_leak: bool = False, leak_count: int = 3) -> None:
    """
    Minimal workload that exercises QueueDrainWorker and EventRecorder lifecycles.

    Uses QueueDrainWorker directly to avoid Kernel filesystem/observability overhead.
    With --simulate-leak: creates N workers without calling stop(), leaving threads alive.
    Without --simulate-leak: creates 1 worker, starts it, and stops it cleanly.
    """
    from src.observability.queue import BoundedObservabilityQueue, QueueDrainWorker

    if simulate_leak:
        # Create workers without stopping them to demonstrate a real leak
        for _ in range(leak_count):
            queue = BoundedObservabilityQueue(max_size=100)
            worker = QueueDrainWorker(queue=queue)
            worker.start()
        # Intentionally no stop() calls
    else:
        queue = BoundedObservabilityQueue(max_size=100)
        worker = QueueDrainWorker(queue=queue)
        worker.start()
        worker.stop()


# ---------------------------------------------------------------------------
# Default (lightweight) mode
# ---------------------------------------------------------------------------

def run_default_mode(args: argparse.Namespace) -> None:
    start = snapshot_start()
    run_workload(simulate_leak=args.simulate_leak, leak_count=args.leak_count)
    report = snapshot_end(start, top_n=args.top_n)

    _print_report(report, args.simulate_leak)

    if args.output:
        _write_json(report, args.output)
        print(f"\nJSON report written to: {args.output}")


def _print_report(report: MemoryReport, simulate_leak: bool) -> None:
    print("=" * 60)
    print("Memory & Resource Probe Report")
    print("=" * 60)
    rss_kb = report.rss_delta_bytes / 1024
    print(f"RSS delta:               {rss_kb:+.1f} KB ({report.rss_delta_bytes:+d} bytes)")
    print(f"Worker thread delta:     {report.worker_count_delta:+d}")
    print(f"EventRecorder delta:     {report.event_recorder_delta:+d}")
    if simulate_leak and report.worker_count_delta > 0:
        print(f"  *** LEAK DEMONSTRATED: {report.worker_count_delta} worker thread(s) not cleaned up ***")
    print()
    print(f"Top allocation sites (up to {len(report.top_allocations)}):")
    for line in report.top_allocations:
        print(f"  {line}")
    print("=" * 60)


def _write_json(report: MemoryReport, path: str) -> None:
    data = {
        "rss_delta_bytes": report.rss_delta_bytes,
        "worker_count_delta": report.worker_count_delta,
        "event_recorder_delta": report.event_recorder_delta,
        "top_allocations": report.top_allocations,
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Flamegraph mode
# ---------------------------------------------------------------------------

def run_flamegraph_mode(args: argparse.Namespace) -> None:
    if sys.platform == "win32":
        print(
            "ERROR: --flamegraph is not supported on Windows. "
            "memray requires Linux or macOS."
        )
        sys.exit(1)

    try:
        import memray  # noqa: F401
    except ImportError:
        print(
            "ERROR: memray is not installed. "
            "Install it with: pip install 'rpg-based-simulation[dev]' or pip install memray>=1.0.0"
        )
        sys.exit(1)

    # Determine output paths
    if args.output and args.output.endswith(".html"):
        html_path = args.output
        bin_path = args.output.replace(".html", ".bin")
    elif args.output:
        bin_path = args.output
        html_path = args.output.replace(".bin", ".html") if args.output.endswith(".bin") else args.output + ".html"
    else:
        Path("reports").mkdir(parents=True, exist_ok=True)
        bin_path = "reports/memory_probe.bin"
        html_path = "reports/memory_flamegraph.html"

    print(f"Recording allocations to: {bin_path}")
    print(f"Flamegraph output:        {html_path}")

    with memray.Tracker(bin_path):
        run_workload(simulate_leak=args.simulate_leak, leak_count=args.leak_count)

    print("Generating flamegraph HTML...")
    subprocess.run(
        ["python", "-m", "memray", "flamegraph", bin_path, "-o", html_path],
        check=True,
    )
    print(f"Flamegraph ready: {html_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Memory and resource debugging tool for the RPG simulation engine.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--flamegraph",
        action="store_true",
        help="Wrap workload in memray.Tracker and produce an HTML flamegraph. Requires memray (pip install memray).",
    )
    parser.add_argument(
        "--simulate-leak",
        action="store_true",
        help="Create N QueueDrainWorker instances without shutting them down to demonstrate a real leak.",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        default=None,
        help="Output path: JSON report (default mode) or flamegraph HTML path (--flamegraph mode).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        metavar="N",
        help="Number of top allocation sites to display (default: 20).",
    )
    parser.add_argument(
        "--leak-count",
        type=int,
        default=3,
        metavar="N",
        help="Number of workers to create when --simulate-leak is used (default: 3).",
    )

    args = parser.parse_args()

    if args.flamegraph:
        run_flamegraph_mode(args)
    else:
        run_default_mode(args)


if __name__ == "__main__":
    main()
