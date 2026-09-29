#!/usr/bin/env python3
"""
Profiling sweep tool for the V2 simulation engine.

Wraps the same Kernel/SCENARIO_BUILDERS construction pattern scripts/profile_engine.py
uses for a single run, but sweeps across every scenario and multiple entity-count tiers
in one invocation, then exports structured, cross-comparable hotspot data instead of one
scenario's human-readable pstats text.

Two things this adds that a single profile_engine.py run cannot:
  1. Cross-scenario hotspot classification: a function that shows up in the top-N of
     multiple scenarios is a high-leverage, fix-once-benefits-everywhere target (the
     "high-level" optimization category). A function that only shows up under one
     scenario is scoped/algorithm-specific to that domain.
  2. Structured JSON export (per-run and aggregated), so hotspot data can be compared
     across entity-count tiers and scenarios programmatically, not just eyeballed from
     separate text reports.

Covers two distinct workload sources, not just one:
  - Synthetic scenarios (src/perf/scenarios.py's SCENARIO_BUILDERS) — procedurally generated,
    cheap to scale up/down via entity-count tiers, good for isolating a specific domain
    (movement-only, combat-only, etc.) but not representative of real authored content mix.
  - The real SimQ world corpus (data/worlds/*/resolved/world.resolved.yaml, loaded the same
    way tools/bench_corpus_world.py does via tools/calibrate_simq.py::_load_world_state ->
    WorldCompiler.compile) — real, authored worlds with real quest/building/region/faction
    density, not a synthetic approximation of it. Included by default; skip with --no-corpus.

Usage:
    python3 scripts/profile_sweep.py
    python3 scripts/profile_sweep.py --scenarios movement combat --tiers light heavy
    python3 scripts/profile_sweep.py --ticks 200 --top-n 50
    python3 scripts/profile_sweep.py --no-synthetic --corpus-worlds frontier_extended dungeon_crawl
    python3 scripts/profile_sweep.py --no-corpus                      # synthetic scenarios only
"""

from __future__ import annotations

import argparse
import cProfile
import json
import os
import pstats
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))  # for calibrate_simq._load_world_state

from src.config.profiles import PROD_LARGE, RuntimeProfile
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.perf.scenarios import SCENARIO_BUILDERS

OUT_DIR = Path("reports/profile")
CORPUS_ROOT = Path("data/worlds")


def discover_corpus_worlds() -> List[str]:
    """
    Real, loadable corpus worlds: any data/worlds/<name>/ with a resolved spec.
    Uses the filesystem, not data/worlds/world_index.json, since the index was found to be
    stale (missing at least 4 real world dirs with a resolved spec) during this tool's own
    construction — the resolved-spec file is what _load_world_state actually checks.
    """
    if not CORPUS_ROOT.is_dir():
        return []
    names = []
    for child in sorted(CORPUS_ROOT.iterdir()):
        if child.is_dir() and (child / "resolved" / "world.resolved.yaml").exists():
            names.append(child.name)
    return names

# Entity-count tiers. "light" mirrors the existing stored baselines (tests/perf/baselines/,
# ~100-200 entities); "heavy" is deliberately well above those so hotspots that only emerge
# under real density (e.g. a cache whose hit rate collapses as concurrent movement rises)
# have a chance to show up. Both are far below true production scale (10,000+) — this is a
# development diagnostic sweep, not a certification-grade production benchmark.
ENTITY_TIERS: Dict[str, int] = {
    "light": 200,
    "heavy": 1500,
}


@dataclass
class ContentionReading:
    """
    OS-level load-average snapshot, normalized by CPU count. cProfile's own cumtime/tottime and
    this tool's own compute_tick_timing() both use wall-clock timers (time.perf_counter()), not
    CPU-time accounting -- scheduler preemption from unrelated processes inflates every absolute
    millisecond figure this tool produces, on top of cProfile's own well-known 2-5x instrumentation
    overhead. TCK-20260818-HOTFIX-PROFILE-SWEEP-EXPORT-TOOL's own first real sweep runs were
    confirmed contaminated exactly this way (another session's pytest run at 100% CPU plus a
    concurrent `graphify update .`, on a 4-core box) -- discovered only by hand, after the fact.
    This reading is what check_contention() below judges against, and what gets recorded into the
    JSON summary so a reader can judge past runs the same way.
    """
    load_avg_1min: float
    load_avg_5min: float
    load_avg_15min: float
    cpu_count: int
    load_per_core_1min: float


def read_contention() -> ContentionReading:
    """os.getloadavg() is POSIX-only -- this tool already assumes a POSIX dev environment
    (no Windows support claimed or tested anywhere else in this script)."""
    load1, load5, load15 = os.getloadavg()
    cpu_count = os.cpu_count() or 1
    return ContentionReading(
        load_avg_1min=load1,
        load_avg_5min=load5,
        load_avg_15min=load15,
        cpu_count=cpu_count,
        load_per_core_1min=load1 / cpu_count,
    )


def check_contention(reading: ContentionReading, max_load_per_core: float, force: bool) -> None:
    """
    Aborts (exit code 1) when the 1-minute load-average-per-core exceeds max_load_per_core,
    unless --force is passed -- so a sweep run under real external contention doesn't silently
    produce numbers that look like a trustworthy baseline. This is the pre-flight check
    TCK-20260818-HOTFIX-PROFILE-SWEEP-EXPORT-TOOL's own Assumptions section called for as future
    hardening item (a); it runs once, before the sweep starts, since that is the only point at
    which the reading reflects other processes and not the sweep's own CPU usage.
    """
    if reading.load_per_core_1min <= max_load_per_core:
        return
    message = (
        f"\n[CONTENTION WARNING] 1-min load average is {reading.load_avg_1min:.2f} across "
        f"{reading.cpu_count} cores ({reading.load_per_core_1min:.2f} per core), above the "
        f"{max_load_per_core:.2f}-per-core threshold. cProfile's wall-clock timers cannot "
        f"distinguish real engine cost from scheduler preemption by other processes -- absolute "
        f"timing figures from this run would not be a trustworthy baseline.\n"
    )
    if not force:
        message += (
            "Re-run once the machine is idle, or pass --force to proceed anyway (rank/presence-"
            "based findings -- which functions show up as hotspots at all -- are far more "
            "contention-robust than absolute millisecond values).\n"
        )
        print(message, file=sys.stderr)
        sys.exit(1)
    message += "Proceeding anyway because --force was passed -- treat absolute timing numbers from this run as untrustworthy.\n"
    print(message, file=sys.stderr)


@dataclass
class HotspotRecord:
    function: str
    file: str
    line: int
    ncalls: str
    tottime_ms: float
    cumtime_ms: float
    percall_cum_ms: float


@dataclass
class RunResult:
    scenario: str
    tier: str
    entity_count: int
    ticks_completed: int
    tick_ms_avg: float
    tick_ms_p50: float
    tick_ms_p95: float
    tick_ms_max: float
    metrics: Dict[str, float]
    hotspots: List[HotspotRecord]
    prof_path: str


def extract_top_hotspots(stats: pstats.Stats, n: int) -> List[HotspotRecord]:
    """
    Pull the top-N functions by cumulative time out of a pstats.Stats object.

    Kept as a pure function (stats in, records out) so it's independently testable
    against a hand-constructed Stats object, without running a real profiled tick loop.
    """
    records: List[HotspotRecord] = []
    for (filename, lineno, funcname), (cc, nc, tt, ct, _callers) in stats.stats.items():
        records.append(
            HotspotRecord(
                function=funcname,
                file=filename,
                line=lineno,
                ncalls=str(nc) if cc == nc else f"{nc}/{cc}",
                tottime_ms=round(tt * 1000.0, 4),
                cumtime_ms=round(ct * 1000.0, 4),
                percall_cum_ms=round((ct / nc) * 1000.0, 4) if nc else 0.0,
            )
        )
    records.sort(key=lambda r: r.cumtime_ms, reverse=True)
    return records[:n]


def classify_cross_scenario(
    per_run_hotspots: Dict[str, List[HotspotRecord]],
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Split hotspot functions into cross-scenario (appear in >=2 runs' top-N) vs.
    scenario-specific (appear in exactly 1 run's top-N).

    Identity is (file, line, function) — the same function inlined/reported differently
    across Python versions would not merge, but within one interpreter run this is stable.
    Pure function: dict of run-name -> hotspot list in, two classified structures out.
    """
    location_to_runs: Dict[Tuple[str, int, str], List[str]] = {}
    location_to_record: Dict[Tuple[str, int, str], HotspotRecord] = {}

    for run_name, hotspots in per_run_hotspots.items():
        for h in hotspots:
            key = (h.file, h.line, h.function)
            location_to_runs.setdefault(key, []).append(run_name)
            # Keep the record with the largest cumtime seen for this location as representative.
            existing = location_to_record.get(key)
            if existing is None or h.cumtime_ms > existing.cumtime_ms:
                location_to_record[key] = h

    cross_scenario: List[Dict[str, Any]] = []
    scenario_specific: Dict[str, List[Dict[str, Any]]] = {run: [] for run in per_run_hotspots}

    for key, run_names in location_to_runs.items():
        record = asdict(location_to_record[key])
        record["seen_in"] = sorted(run_names)
        if len(run_names) >= 2:
            cross_scenario.append(record)
        else:
            scenario_specific[run_names[0]].append(record)

    cross_scenario.sort(key=lambda r: (len(r["seen_in"]), r["cumtime_ms"]), reverse=True)
    for run in scenario_specific:
        scenario_specific[run].sort(key=lambda r: r["cumtime_ms"], reverse=True)

    return cross_scenario, scenario_specific


def compute_tick_timing(tick_durations_ms: List[float]) -> Dict[str, float]:
    """Avg/p50/p95/max from a list of individual per-tick wall-clock durations."""
    if not tick_durations_ms:
        return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0}
    ordered = sorted(tick_durations_ms)
    n = len(ordered)

    def pct(p: float) -> float:
        idx = min(n - 1, int(round(p * (n - 1))))
        return ordered[idx]

    return {
        "avg": round(sum(ordered) / n, 4),
        "p50": round(pct(0.50), 4),
        "p95": round(pct(0.95), 4),
        "max": round(ordered[-1], 4),
    }


def make_state(scenario_name: str, entity_count: int) -> AuthoritativeState:
    builder_fn = SCENARIO_BUILDERS[scenario_name]
    if scenario_name == "resource":
        return builder_fn(entity_count=int(entity_count * 0.7), node_count=int(entity_count * 0.3))
    elif scenario_name == "combat":
        side_count = max(1, entity_count // 2)
        return builder_fn(team_a_count=side_count, team_b_count=side_count)
    else:
        return builder_fn(entity_count=entity_count)


def run_one(
    scenario_name: str,
    tier_name: str,
    entity_count: int,
    ticks: int,
    top_n: int,
    profile: RuntimeProfile,
) -> RunResult:
    run_label = f"{scenario_name}_{tier_name}"
    print(f"--- Sweeping: {run_label} ({entity_count} entities, {ticks} ticks) ---")

    state = make_state(scenario_name, entity_count)
    kernel = Kernel(
        profile,
        state,
        DeterministicRNG(42),
        flags={"no_replay": True, "no_frame_pacing": True, "audit_mode": False},
    )

    tick_durations_ms: List[float] = []
    profiler = cProfile.Profile()
    profiler.enable()
    ticks_completed = 0
    try:
        for _ in range(ticks):
            start = time.perf_counter()
            kernel.tick_once()
            tick_durations_ms.append((time.perf_counter() - start) * 1000.0)
            ticks_completed += 1
    finally:
        profiler.disable()
        final_metrics = dict(kernel._metrics)
        kernel.shutdown()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prof_path = OUT_DIR / f"{run_label}.prof"
    profiler.dump_stats(prof_path)

    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    hotspots = extract_top_hotspots(stats, top_n)

    timing = compute_tick_timing(tick_durations_ms)

    return RunResult(
        scenario=scenario_name,
        tier=tier_name,
        entity_count=entity_count,
        ticks_completed=ticks_completed,
        tick_ms_avg=timing["avg"],
        tick_ms_p50=timing["p50"],
        tick_ms_p95=timing["p95"],
        tick_ms_max=timing["max"],
        metrics=final_metrics,
        hotspots=hotspots,
        prof_path=str(prof_path),
    )


def run_corpus_world(
    world_name: str,
    ticks: int,
    top_n: int,
    profile: RuntimeProfile,
    seed: int = 42,
) -> RunResult:
    """
    Same profiling logic as run_one(), but the state comes from a real, authored corpus
    world (WorldCompiler-compiled) instead of a synthetic SCENARIO_BUILDERS state.
    """
    from calibrate_simq import _load_world_state  # local import: tools/ added to sys.path above

    run_label = f"corpus_{world_name}"
    print(f"--- Sweeping: {run_label} ({ticks} ticks) ---")

    state, compile_report = _load_world_state(world_name, seed)
    if state is None:
        raise ValueError(f"Corpus world {world_name!r} has no resolved spec.")
    entity_count = compile_report.get("entity_count", 0)

    kernel = Kernel(
        profile,
        state,
        DeterministicRNG(seed),
        flags={"no_replay": True, "no_frame_pacing": True, "audit_mode": False},
    )

    tick_durations_ms: List[float] = []
    profiler = cProfile.Profile()
    profiler.enable()
    ticks_completed = 0
    try:
        for _ in range(ticks):
            start = time.perf_counter()
            kernel.tick_once()
            tick_durations_ms.append((time.perf_counter() - start) * 1000.0)
            ticks_completed += 1
    finally:
        profiler.disable()
        final_metrics = dict(kernel._metrics)
        kernel.shutdown()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prof_path = OUT_DIR / f"{run_label}.prof"
    profiler.dump_stats(prof_path)

    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    hotspots = extract_top_hotspots(stats, top_n)
    timing = compute_tick_timing(tick_durations_ms)

    return RunResult(
        scenario=f"corpus_{world_name}",
        tier="corpus",
        entity_count=entity_count,
        ticks_completed=ticks_completed,
        tick_ms_avg=timing["avg"],
        tick_ms_p50=timing["p50"],
        tick_ms_p95=timing["p95"],
        tick_ms_max=timing["max"],
        metrics=final_metrics,
        hotspots=hotspots,
        prof_path=str(prof_path),
    )


def render_markdown_report(
    results: List[RunResult],
    cross_scenario: List[Dict[str, Any]],
    scenario_specific: Dict[str, List[Dict[str, Any]]],
    top_n: int,
) -> str:
    lines: List[str] = []
    lines.append("# Profiling Sweep Report")
    lines.append("")
    lines.append(
        f"Swept {len(results)} (scenario, tier) combinations. "
        f"Top {top_n} functions by cumulative time captured per run."
    )
    lines.append("")

    lines.append("## Tick timing per run")
    lines.append("")
    lines.append("| Run | Entities | Ticks | avg ms | p50 ms | p95 ms | max ms |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r.scenario}_{r.tier} | {r.entity_count} | {r.ticks_completed} | "
            f"{r.tick_ms_avg} | {r.tick_ms_p50} | {r.tick_ms_p95} | {r.tick_ms_max} |"
        )
    lines.append("")

    lines.append("## Cache / index metrics per run")
    lines.append("")
    lines.append("| Run | movement_cache hit% | spatial_index hit% | raw metrics |")
    lines.append("|---|---|---|---|")
    for r in results:
        m = r.metrics
        mv_h, mv_m = m.get("movement_cache_hits", 0), m.get("movement_cache_misses", 0)
        sp_h, sp_m = m.get("spatial_index_hits", 0), m.get("spatial_index_misses", 0)
        mv_rate = f"{(mv_h / (mv_h + mv_m) * 100):.1f}%" if (mv_h + mv_m) else "n/a"
        sp_rate = f"{(sp_h / (sp_h + sp_m) * 100):.1f}%" if (sp_h + sp_m) else "n/a"
        lines.append(f"| {r.scenario}_{r.tier} | {mv_rate} | {sp_rate} | `{m}` |")
    lines.append("")

    lines.append("## Cross-scenario hotspots (high-level / fix-once-benefits-everywhere candidates)")
    lines.append("")
    lines.append("Functions appearing in the top-N of 2 or more scenario runs.")
    lines.append("")
    lines.append("| Function | File:Line | Seen in | Max cumtime ms |")
    lines.append("|---|---|---|---|")
    for h in cross_scenario[:40]:
        lines.append(
            f"| `{h['function']}` | {h['file']}:{h['line']} | "
            f"{', '.join(h['seen_in'])} | {h['cumtime_ms']} |"
        )
    lines.append("")

    lines.append("## Scenario-specific hotspots (scoped / algorithmic candidates)")
    lines.append("")
    for run_name, hs in scenario_specific.items():
        if not hs:
            continue
        lines.append(f"### {run_name}")
        lines.append("")
        lines.append("| Function | File:Line | cumtime ms |")
        lines.append("|---|---|---|")
        for h in hs[:15]:
            lines.append(f"| `{h['function']}` | {h['file']}:{h['line']} | {h['cumtime_ms']} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="RPG Engine Profiling Sweep")
    parser.add_argument(
        "--scenarios",
        nargs="+",
        choices=list(SCENARIO_BUILDERS.keys()),
        default=list(SCENARIO_BUILDERS.keys()),
        help="Scenarios to sweep (default: all)",
    )
    parser.add_argument(
        "--tiers",
        nargs="+",
        choices=list(ENTITY_TIERS.keys()),
        default=list(ENTITY_TIERS.keys()),
        help="Entity-count tiers to sweep (default: all)",
    )
    parser.add_argument("--ticks", type=int, default=150, help="Ticks per run")
    parser.add_argument("--top-n", type=int, default=40, help="Top-N functions captured per run")
    parser.add_argument("--no-synthetic", action="store_true", help="Skip SCENARIO_BUILDERS sweep")
    parser.add_argument("--no-corpus", action="store_true", help="Skip real data/worlds/ corpus sweep")
    parser.add_argument(
        "--corpus-worlds",
        nargs="+",
        default=None,
        help="Specific corpus world names to sweep (default: all discovered under data/worlds/)",
    )
    parser.add_argument("--corpus-ticks", type=int, default=None, help="Ticks per corpus-world run (default: --ticks)")
    parser.add_argument(
        "--max-load-per-core", type=float, default=0.5,
        help="Abort if 1-min load-average-per-core exceeds this before the sweep starts (default: 0.5)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Proceed even if the pre-flight contention check fails (absolute timings will be untrustworthy)",
    )
    args = parser.parse_args()

    contention = read_contention()
    check_contention(contention, args.max_load_per_core, args.force)

    results: List[RunResult] = []

    if not args.no_synthetic:
        for scenario_name in args.scenarios:
            for tier_name in args.tiers:
                entity_count = ENTITY_TIERS[tier_name]
                result = run_one(
                    scenario_name, tier_name, entity_count, args.ticks, args.top_n, PROD_LARGE
                )
                results.append(result)

    if not args.no_corpus:
        world_names = args.corpus_worlds if args.corpus_worlds else discover_corpus_worlds()
        corpus_ticks = args.corpus_ticks if args.corpus_ticks is not None else args.ticks
        for world_name in world_names:
            try:
                result = run_corpus_world(world_name, corpus_ticks, args.top_n, PROD_LARGE)
                results.append(result)
            except Exception as e:
                print(f"  [SKIPPED] corpus world {world_name!r}: {e}")

    per_run_hotspots = {f"{r.scenario}_{r.tier}": r.hotspots for r in results}
    cross_scenario, scenario_specific = classify_cross_scenario(per_run_hotspots)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = OUT_DIR / "sweep_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "contention_at_start": asdict(contention),
                "runs": [
                    {**asdict(r), "hotspots": [asdict(h) for h in r.hotspots]} for r in results
                ],
                "cross_scenario_hotspots": cross_scenario,
                "scenario_specific_hotspots": scenario_specific,
            },
            f,
            indent=2,
        )

    report_path = OUT_DIR / "sweep_report.md"
    report_path.write_text(
        render_markdown_report(results, cross_scenario, scenario_specific, args.top_n),
        encoding="utf-8",
    )

    print(f"\nSweep complete. {len(results)} runs.")
    print(f"  JSON summary: {summary_path}")
    print(f"  Markdown report: {report_path}")


if __name__ == "__main__":
    main()
