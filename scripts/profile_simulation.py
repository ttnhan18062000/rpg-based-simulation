#!/usr/bin/env python3
"""Automated simulation profiler.

Usage:
    python scripts/profile_simulation.py --ticks 500 --seed 42
    python scripts/profile_simulation.py --ticks 2000 --seed 42 --cprofile profile.prof
    python scripts/profile_simulation.py --ticks 500 --seed 42 --memory

Reports:
    - Per-tick timing statistics (min, max, mean, p50, p95, p99)
    - Per-phase breakdown (schedule, collect, resolve, cleanup)
    - Entity count over time
    - Throughput (ticks/sec)
    - Optional: cProfile dump for flame graph generation
    - Optional: tracemalloc memory snapshot
"""

from __future__ import annotations

import argparse
import cProfile
import io
import os
import pstats
import statistics
import sys
import time
import tracemalloc

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.api.engine_manager import EngineManager
from src.config import SimulationConfig
from src.core.snapshot import Snapshot


def _run_simulation(cfg: SimulationConfig, num_ticks: int) -> dict:
    """Run simulation and collect per-tick timing data."""
    mgr = EngineManager(cfg)
    loop = mgr._loop
    assert loop is not None

    tick_times: list[float] = []
    phase_times: list[tuple[float, float, float, float]] = []
    entity_counts: list[int] = []

    for i in range(num_ticks):
        t_start = time.perf_counter()

        # --- Phase 1: Scheduling ---
        loop._phase_generators()
        ready = loop._phase_scheduling()
        t1 = time.perf_counter()

        if not ready:
            tick_times.append(t1 - t_start)
            phase_times.append((t1 - t_start, 0.0, 0.0, 0.0))
            entity_counts.append(sum(1 for e in loop.world.entities.values() if e.alive and e.kind != "generator"))
            loop.world.tick += 1
            continue

        # --- Phase 2: Collect ---
        snapshot = Snapshot.from_world(loop.world)
        loop._worker_pool.dispatch(ready, snapshot, loop._action_queue)
        proposals = loop._action_queue.drain()
        t2 = time.perf_counter()

        # --- Phase 3: Resolve ---
        applied = loop._conflict_resolver.resolve(proposals, loop.world)
        loop._last_applied = applied
        loop._update_ai_states(applied)
        loop._process_item_actions(applied)
        loop._heal_home_entities()
        t3 = time.perf_counter()

        # --- Phase 4: Cleanup ---
        loop._phase_cleanup()
        loop._process_territory_effects()
        loop._tick_effects()
        loop._tick_resource_nodes()
        loop._tick_treasure_chests()
        loop._tick_engagement()
        loop._check_level_ups()
        loop._tick_stamina_and_skills()
        loop._update_entity_memory()
        loop._tick_quests()
        loop._update_entity_goals()
        t4 = time.perf_counter()

        total = t4 - t_start
        tick_times.append(total)
        phase_times.append((t1 - t_start, t2 - t1, t3 - t2, t4 - t3))

        alive = sum(1 for e in loop.world.entities.values() if e.alive and e.kind != "generator")
        entity_counts.append(alive)

        loop.world.tick += 1

        if alive == 0:
            break

    # Shutdown worker pool
    if mgr._worker_pool:
        mgr._worker_pool.shutdown()

    return {
        "tick_times": tick_times,
        "phase_times": phase_times,
        "entity_counts": entity_counts,
        "final_tick": loop.world.tick,
    }


def _percentile(data: list[float], p: float) -> float:
    """Simple percentile calculation."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def _print_report(data: dict, wall_time: float) -> None:
    """Print a formatted performance report."""
    tick_times = data["tick_times"]
    phase_times = data["phase_times"]
    entity_counts = data["entity_counts"]
    num_ticks = len(tick_times)

    if num_ticks == 0:
        print("No ticks executed.")
        return

    print("\n" + "=" * 70)
    print("  SIMULATION PERFORMANCE REPORT")
    print("=" * 70)

    # --- Overview ---
    print(f"\n  Ticks executed:    {num_ticks}")
    print(f"  Wall clock time:   {wall_time:.3f}s")
    print(f"  Throughput:        {num_ticks / wall_time:.1f} ticks/sec")
    print(f"  Avg tick time:     {statistics.mean(tick_times) * 1000:.2f}ms")

    # --- Entity counts ---
    print(f"\n  Entity count (start):  {entity_counts[0]}")
    print(f"  Entity count (end):    {entity_counts[-1]}")
    if entity_counts:
        print(f"  Entity count (peak):   {max(entity_counts)}")

    # --- Tick time distribution ---
    print(f"\n  {'Metric':<16} {'Time (ms)':>10}")
    print(f"  {'-' * 16} {'-' * 10}")
    print(f"  {'Min':<16} {min(tick_times) * 1000:>10.3f}")
    print(f"  {'P50 (median)':<16} {_percentile(tick_times, 50) * 1000:>10.3f}")
    print(f"  {'P95':<16} {_percentile(tick_times, 95) * 1000:>10.3f}")
    print(f"  {'P99':<16} {_percentile(tick_times, 99) * 1000:>10.3f}")
    print(f"  {'Max':<16} {max(tick_times) * 1000:>10.3f}")
    print(f"  {'StdDev':<16} {statistics.stdev(tick_times) * 1000:>10.3f}" if num_ticks > 1 else "")

    # --- Phase breakdown ---
    sched = [p[0] for p in phase_times]
    collect = [p[1] for p in phase_times]
    resolve = [p[2] for p in phase_times]
    cleanup = [p[3] for p in phase_times]
    total_sum = sum(tick_times)

    print(f"\n  {'Phase':<16} {'Avg (ms)':>10} {'P95 (ms)':>10} {'% Total':>10}")
    print(f"  {'-' * 16} {'-' * 10} {'-' * 10} {'-' * 10}")
    for name, times in [("Schedule", sched), ("Collect", collect), ("Resolve", resolve), ("Cleanup", cleanup)]:
        avg_ms = statistics.mean(times) * 1000 if times else 0
        p95_ms = _percentile(times, 95) * 1000 if times else 0
        pct = (sum(times) / total_sum * 100) if total_sum > 0 else 0
        print(f"  {name:<16} {avg_ms:>10.3f} {p95_ms:>10.3f} {pct:>9.1f}%")

    # --- Slowest ticks ---
    print(f"\n  Top 5 slowest ticks:")
    indexed = sorted(enumerate(tick_times), key=lambda x: x[1], reverse=True)[:5]
    for tick_idx, t in indexed:
        ent = entity_counts[tick_idx] if tick_idx < len(entity_counts) else "?"
        print(f"    Tick {tick_idx:>5}: {t * 1000:.3f}ms  ({ent} entities)")

    print("\n" + "=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile the simulation engine")
    parser.add_argument("--ticks", type=int, default=500, help="Number of ticks to run")
    parser.add_argument("--seed", type=int, default=42, help="World seed")
    parser.add_argument("--entities", type=int, default=25, help="Initial entity count")
    parser.add_argument("--grid", type=int, default=128, help="Grid size (NxN)")
    parser.add_argument("--workers", type=int, default=1, help="Worker threads (1 for consistent timing)")
    parser.add_argument("--cprofile", type=str, default=None, help="Save cProfile output to file")
    parser.add_argument("--memory", action="store_true", help="Enable tracemalloc memory profiling")
    args = parser.parse_args()

    cfg = SimulationConfig(
        world_seed=args.seed,
        max_ticks=args.ticks + 10,
        initial_entity_count=args.entities,
        num_workers=args.workers,
        grid_width=args.grid,
        grid_height=args.grid,
    )

    print(f"Profiling: {args.ticks} ticks, seed={args.seed}, "
          f"entities={args.entities}, grid={args.grid}x{args.grid}, workers={args.workers}")

    # --- Optional: memory tracking ---
    if args.memory:
        tracemalloc.start()

    # --- Optional: cProfile ---
    profiler = None
    if args.cprofile:
        profiler = cProfile.Profile()
        profiler.enable()

    wall_start = time.perf_counter()
    data = _run_simulation(cfg, args.ticks)
    wall_time = time.perf_counter() - wall_start

    if profiler:
        profiler.disable()

    _print_report(data, wall_time)

    # --- cProfile output ---
    if profiler and args.cprofile:
        profiler.dump_stats(args.cprofile)
        print(f"\n  cProfile data saved to: {args.cprofile}")
        print(f"  View with: python -m pstats {args.cprofile}")
        print(f"  Or: snakeviz {args.cprofile}")

        # Also print top 20 cumulative
        print(f"\n  Top 20 functions by cumulative time:")
        stream = io.StringIO()
        ps = pstats.Stats(profiler, stream=stream)
        ps.sort_stats("cumulative")
        ps.print_stats(20)
        print(stream.getvalue())

    # --- Memory output ---
    if args.memory:
        snapshot = tracemalloc.take_snapshot()
        print("\n  Top 15 memory allocations by size:")
        print(f"  {'File:Line':<60} {'Size':>10}")
        print(f"  {'-' * 60} {'-' * 10}")
        top_stats = snapshot.statistics("lineno")
        for stat in top_stats[:15]:
            size_kb = stat.size / 1024
            print(f"  {str(stat.traceback):<60} {size_kb:>8.1f} KB")

        current, peak = tracemalloc.get_traced_memory()
        print(f"\n  Current memory: {current / 1024:.1f} KB")
        print(f"  Peak memory:    {peak / 1024:.1f} KB")
        tracemalloc.stop()


if __name__ == "__main__":
    main()
