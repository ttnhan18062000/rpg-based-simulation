"""Diagnostics for the RSS contradiction of TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE (a reproduction script, not a measurement).

Question: the harness's after-collect RSS on simq_corpus_frontier_extended stayed at 1702 MB with only 1355 unreachable objects (tick_cost_growth.md section 5 said
it was uncollected garbage). This runs the SAME kernel call shape as ``BenchHarness.run_benchmark`` (warm-up, ``gc.collect()``, optional ``gc.disable()``,
sampled ticks, history of ``kernel.status.get_recent_history(1)``, end ``gc.collect()``) with diagnostics around it:

  --census        gc.get_objects() counts by type and lengths of the kernel's/state's container attributes, at the end of warm-up and after the end collect
                  (top 15 types by growth, count and shallow size)
  --gc on|off     leave the collector enabled during the window (on) or disable it as the harness does (off)
  --contract      canonical (canonical_variant of PERF_512MB_LOCAL) or pinned (PinnedNormalGovernor)
  --no-harness    run the ticks with no history list and no gc.collect() calls, to see whether growth belongs to the harness or the engine
  --trim          after the end collect call glibc malloc_trim(0) and report RSS again (does freed memory go back to the OS?)
  --tracemalloc   trace from the start of the window; after the end collect print the top 20 line numbers by growth and tracemalloc's total against RSS

Run from the repo root with the venv python, one at a time, under systemd-run MemoryMax. Python 3.13, psutil. Prints one JSON report on stdout (logs go to stderr).
"""
from __future__ import annotations

import argparse
import collections
import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def rss_mb() -> float:
    import psutil

    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def type_census(limit_size_types: int = 40) -> Dict[str, Any]:
    counts: collections.Counter = collections.Counter()
    sizes: collections.Counter = collections.Counter()
    for obj in gc.get_objects():
        name = type(obj).__name__
        counts[name] += 1
        try:
            sizes[name] += sys.getsizeof(obj)
        except TypeError:
            pass
    return {"counts": counts, "sizes": sizes, "total_objects": sum(counts.values())}


def container_lengths(root: Any, label: str, depth: int = 1) -> Dict[str, int]:
    """len() of every list/dict/set/deque attribute of ``root`` (and of ``root.status`` etc. one level down)."""
    out: Dict[str, int] = {}
    if hasattr(root, "__dict__"):
        items = list(vars(root).items())
    else:  # a __slots__ class
        names = [n for klass in type(root).__mro__ for n in getattr(klass, "__slots__", ())]
        items = [(n, getattr(root, n)) for n in names if hasattr(root, n)]
    for name, value in items:
        if isinstance(value, (list, dict, set, tuple, collections.deque)):
            out[f"{label}.{name}"] = len(value)
        elif depth > 0 and (hasattr(value, "__dict__") or hasattr(type(value), "__slots__")) and not isinstance(value, type):
            out.update(container_lengths(value, f"{label}.{name}", depth - 1))
    return out


def growth(before: Dict[str, Any], after: Dict[str, Any], top: int = 15) -> List[Dict[str, Any]]:
    names = set(before["counts"]) | set(after["counts"])
    rows = [{"type": n, "count_before": before["counts"].get(n, 0), "count_after": after["counts"].get(n, 0),
             "count_growth": after["counts"].get(n, 0) - before["counts"].get(n, 0),
             "shallow_mb_growth": round((after["sizes"].get(n, 0) - before["sizes"].get(n, 0)) / 1048576, 2)} for n in names]
    return sorted(rows, key=lambda r: r["shallow_mb_growth"], reverse=True)[:top]


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--world", default="frontier_extended")
    p.add_argument("--warmup", type=int, default=100)
    p.add_argument("--ticks", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--contract", choices=["canonical", "pinned"], default="canonical")
    p.add_argument("--gc", choices=["on", "off"], default="off")
    p.add_argument("--census", action="store_true")
    p.add_argument("--no-harness", action="store_true")
    p.add_argument("--tracemalloc", action="store_true")
    p.add_argument("--trim", action="store_true", help="after the end collect call glibc malloc_trim(0) and report RSS again")
    args = p.parse_args(argv)

    from src.engine.kernel import Kernel
    from src.perf.profiles import PERF_PROFILES, canonical_variant
    from src.platform.rng import DeterministicRNG
    from tools.perf.rerun_baselines import load_corpus_state

    state = load_corpus_state(args.world, args.seed)[0]
    base = PERF_PROFILES["PERF_512MB_LOCAL"]
    governor = None
    if args.contract == "canonical":
        profile = canonical_variant(base)
    else:
        from tests.helpers.kernel_pinning import PinnedNormalGovernor

        profile, governor = base, PinnedNormalGovernor()
    kernel = Kernel(profile, state, DeterministicRNG(args.seed), governor=governor, flags={"no_replay": True, "no_frame_pacing": True})
    report: Dict[str, Any] = {"args": vars(args), "python": sys.version.split()[0], "loadavg_1min": os.getloadavg()[0]}
    history: List[Any] = []
    modes: collections.Counter = collections.Counter()
    try:
        for _ in range(args.warmup):
            kernel.tick_once()
        if not args.no_harness:
            gc.collect()
        report["rss_after_warmup_mb"] = round(rss_mb(), 1)
        before = type_census() if args.census else None
        lens_before = {**container_lengths(kernel, "kernel"), **container_lengths(kernel._state, "state", 0)} if args.census else None
        snap_before = None
        if args.tracemalloc:
            import tracemalloc

            tracemalloc.start(1)
            snap_before = tracemalloc.take_snapshot()
        was_enabled = gc.isenabled()
        if args.gc == "off":
            gc.disable()
        rss_samples: List[float] = []
        tick_ms: List[float] = []
        try:
            for i in range(args.ticks):
                t0 = time.perf_counter()
                kernel.tick_once()
                tick_ms.append((time.perf_counter() - t0) * 1000.0)
                modes[kernel.status.current_mode.name] += 1
                if not args.no_harness:
                    history.extend(kernel.status.get_recent_history(1))
                if i % 10 == 0:
                    rss_samples.append(rss_mb())
        finally:
            if was_enabled:
                gc.enable()
        report["rss_end_of_window_mb"] = round(rss_mb(), 1)
        report["rss_high_water_mb"] = round(max(rss_samples), 1)
        report["rss_growth_in_window_mb"] = round(rss_samples[-1] - rss_samples[0], 1)
        report["mean_tick_ms"] = round(sum(tick_ms) / len(tick_ms), 1)
        report["modes"] = dict(modes)
        report["history_len"] = len(history)
        if not args.no_harness:
            report["end_collect_unreachable"] = gc.collect()
        report["rss_after_end_collect_mb"] = round(rss_mb(), 1)
        if args.trim:
            import ctypes

            report["malloc_trim_returned"] = ctypes.CDLL("libc.so.6").malloc_trim(0)
            report["rss_after_malloc_trim_mb"] = round(rss_mb(), 1)
        if args.census and before is not None:
            after = type_census()
            report["census_top15_by_shallow_growth"] = growth(before, after)
            report["objects_before"], report["objects_after"] = before["total_objects"], after["total_objects"]
            lens_after = {**container_lengths(kernel, "kernel"), **container_lengths(kernel._state, "state", 0)}
            report["container_len_growth"] = {k: [lens_before.get(k, 0), v] for k, v in sorted(lens_after.items(), key=lambda kv: kv[1] - lens_before.get(kv[0], 0), reverse=True)[:15]}
        if args.tracemalloc and snap_before is not None:
            import tracemalloc

            snap = tracemalloc.take_snapshot()
            top = snap.compare_to(snap_before, "lineno")[:20]
            report["tracemalloc_top20_growth"] = [{"where": str(s.traceback[0]), "size_diff_mb": round(s.size_diff / 1048576, 2), "count_diff": s.count_diff} for s in top]
            current, peak = tracemalloc.get_traced_memory()
            report["tracemalloc_current_mb"], report["tracemalloc_peak_mb"] = round(current / 1048576, 1), round(peak / 1048576, 1)
            report["rss_minus_tracemalloc_mb"] = round(rss_mb() - current / 1048576, 1)
            tracemalloc.stop()
    finally:
        kernel.shutdown()
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
