# Compliance IDs: PERF-001, PERF-002, PERF-004
from __future__ import annotations

import time
import logging
import statistics
import os
from typing import Dict, List, Any

import psutil

from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile

logger = logging.getLogger(__name__)


class PerformanceRegressionError(Exception):
    """Raised when an engine phase exceeds its allotted time budget."""
    pass


class BenchHarness:
    """
    Dedicated harness for high-frequency performance measurement.
    Adheres to the V2 Engine Performance Contract.
    
    Enhanced with:
    - RSS Memory monitoring via psutil
    - p50/p95/p99 latency percentiles
    - Phase-specific cost distribution
    """

    def __init__(self, profile: RuntimeProfile):
        self._profile = profile
        self._process = psutil.Process(os.getpid())

    def run_benchmark(
        self,
        scenario_id: str,
        initial_state: AuthoritativeState,
        warmup_ticks: int = 100,
        sample_ticks: int = 1000,
        phase_budgets: Optional[Dict[str, float]] = None,
        flags: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Execute a stable measurement run: Warmup -> Sample -> Collate.
        
        M1 Law: Benchmarks default to no_replay and no_frame_pacing to measure 
        raw engine compute throughput.
        """
        # Set M1 defaults
        effective_flags = {"no_replay": True, "no_frame_pacing": True}
        if flags:
            effective_flags.update(flags)
            
        logger.info(f"Starting Benchmark: {scenario_id} ({self._profile.name})")
        logger.info(f"Flags: {effective_flags}")
        
        # Initialize Kernel — always shut down to release EventRecorder thread
        rng = DeterministicRNG(initial_state.seed)
        kernel = Kernel(self._profile, initial_state, rng, flags=effective_flags)

        import gc

        try:
            # 1. WARMUP
            for _ in range(warmup_ticks):
                kernel.tick_once()

            gc.collect()
            gc_was_enabled = gc.isenabled()
            gc.disable()

            # 2. SAMPLING
            rss_samples: List[float] = []
            wall_start_ts = time.perf_counter()

            try:
                for i in range(sample_ticks):
                    kernel.tick_once()

                    # Sample memory every 10 ticks to reduce overhead
                    if i % 10 == 0:
                        rss_samples.append(self._process.memory_info().rss / (1024 * 1024))
            finally:
                if gc_was_enabled:
                    gc.enable()

            wall_end_ts = time.perf_counter()

            wall_clock_s = wall_end_ts - wall_start_ts
            wall_clock_tps = sample_ticks / wall_clock_s if wall_clock_s > 0 else 0

            # 3. COLLATION
            history = kernel.status.get_recent_history(sample_ticks)
            tick_times = [s.tick_compute_ms for s in history]

            # Compute TPS: Theoretical throughput if no wall-clock overhead
            total_compute_ms = sum(tick_times)
            compute_tps = (sample_ticks * 1000.0) / total_compute_ms if total_compute_ms > 0 else 0

            phase_aggregates: Dict[str, List[float]] = {}
            metric_aggregates: Dict[str, List[float]] = {}
            for signals in history:
                for phase, cost in signals.phase_costs_ms.items():
                    if phase not in phase_aggregates:
                        phase_aggregates[phase] = []
                    phase_aggregates[phase].append(cost)
                if hasattr(signals, "metrics") and signals.metrics:
                    for k, v in signals.metrics.items():
                        if k not in metric_aggregates:
                            metric_aggregates[k] = []
                        metric_aggregates[k].append(float(v))

            phase_stats = {}
            for phase, costs in phase_aggregates.items():
                phase_stats[phase] = self._calculate_stats(costs)

            metric_stats = {}
            for k, vals in metric_aggregates.items():
                metric_stats[k] = round(sum(vals) / len(vals), 2) if vals else 0.0

            result = {
                "scenario_id": scenario_id,
                "profile": self._profile.name,
                "sample_ticks": sample_ticks,
                "wall_clock_s": round(wall_clock_s, 4),
                "wall_clock_tps": round(wall_clock_tps, 2),
                "compute_tps": round(compute_tps, 2),
                "avg_tps": round(compute_tps, 2),  # Legacy compat
                "tick_ms": self._calculate_stats(tick_times),
                "mem_rss_mb": {
                    "avg": round(sum(rss_samples) / len(rss_samples), 2) if rss_samples else 0.0,
                    "max": round(max(rss_samples), 2) if rss_samples else 0.0,
                    "delta": round(max(rss_samples) - min(rss_samples), 2) if rss_samples else 0.0,
                },
                "phase_breakdown": phase_stats,
                "metrics": metric_stats,
                "replay_enabled": not effective_flags.get("no_replay", False),
                "frame_pacing_enabled": not effective_flags.get("no_frame_pacing", False),
                "timestamp": time.time()
            }

            # Add flat keys for schema compliance
            result["avg_tick_compute_ms"] = result["tick_ms"]["avg"]
            result["p50_tick_compute_ms"] = result["tick_ms"]["p50"]
            result["p95_tick_compute_ms"] = result["tick_ms"]["p95"]
            result["p99_tick_compute_ms"] = result["tick_ms"]["p99"]
            result["max_tick_compute_ms"] = result["tick_ms"]["max"]
            result["peak_rss_mb"] = result["mem_rss_mb"]["max"]
            result["memory_delta_mb"] = result["mem_rss_mb"]["delta"]

            # Law 125: Phase Budget Enforcement
            if phase_budgets and self._profile.max_tick_budget_ms > 0:
                for phase, budget_ratio in phase_budgets.items():
                    if phase in phase_stats:
                        p95_ms = phase_stats[phase]["p95"]
                        limit_ms = self._profile.max_tick_budget_ms * budget_ratio
                        if p95_ms > limit_ms:
                            raise PerformanceRegressionError(
                                f"Phase '{phase}' exceeded budget in scenario '{scenario_id}': "
                                f"p95={p95_ms:.2f}ms, limit={limit_ms:.2f}ms ({budget_ratio*100}% of {self._profile.max_tick_budget_ms}ms)"
                            )

            return result

        finally:
            kernel.shutdown()

    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate distribution statistics for a set of values."""
        if not values:
            return {"avg": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
            
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "avg": round(sum(values) / count, 3),
            "p50": round(sorted_values[int(count * 0.5)], 3),
            "p95": round(sorted_values[int(count * 0.95)], 3),
            "p99": round(sorted_values[int(count * 0.99)], 3),
            "max": round(sorted_values[-1], 3),
            "min": round(sorted_values[0], 3)
        }
