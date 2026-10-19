# Compliance IDs: PERF-001, PERF-002, PERF-004
from __future__ import annotations

import gc
import sys
import time
import logging
from dataclasses import dataclass
import statistics
import os
from typing import Dict, List, Any, Optional, Tuple

import psutil

from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG
from src.config.profiles import RuntimeProfile
from src.perf.benchmark_record import (
    MAX_EMBEDDED_SAMPLES,
    BenchmarkRecord,
    GateTier,
    MemoryPassReading,
    Outcome,
    OutcomeState,
    PercentileMethod,
    Protocol,
    RecordOptions,
    Result,
    RunSubject,
    Samples,
    collect_identity,
    compress_modes,
    default_samples_dir,
    latency_stats,
    utc_now,
    write_samples_file,
)

logger = logging.getLogger(__name__)


def _gc_collected_total() -> int:
    """Objects the collector has freed so far, over all generations (``gc.get_stats()``)."""
    return sum(int(generation["collected"]) for generation in gc.get_stats())


def _malloc_trim() -> bool:
    """Hand the allocator's freed pages back to the OS (glibc ``malloc_trim(0)``).

    True when the call was made, **whatever it returned** (glibc returns 1 when it released memory and 0 when there was nothing to release; neither
    means "unavailable"). False only when libc or the symbol is missing or the call raised. Never raises.
    """
    try:
        import ctypes

        ctypes.CDLL("libc.so.6").malloc_trim(0)
        return True
    except (OSError, AttributeError):
        return False


class PerformanceRegressionError(Exception):
    """Raised when an engine phase exceeds its allotted time budget."""
    pass


@dataclass(frozen=True)
class _Measured:
    """The per-tick series and aggregates of one run, as collated for both the result dict and the record."""

    tick_times: List[float]
    tick_wall_ms: List[float]
    mode_samples: List[str]
    phase_stats: Dict[str, Dict[str, float]]
    metric_stats: Dict[str, float]


def run_memory_pass(
    profile: RuntimeProfile,
    initial_state: AuthoritativeState,
    scenario_id: str,
    warmup_ticks: int,
    sample_ticks: int,
) -> MemoryPassReading:
    """An untimed pass over the same run shape as ``run_benchmark``, with the collector **enabled**, read at its end (TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS).

    ``run_benchmark`` disables the collector for its sampled ticks, so its RSS includes garbage the engine would have collected and the freed memory stays
    mapped; this pass leaves the collector on, so what it reads after ``gc.collect()`` and ``malloc_trim(0)`` is the engine's working set. It reads no clock
    and is meant to run in a fresh process, so it shares no arenas with the timed pass. The collector's state is restored on return.
    """
    process = psutil.Process(os.getpid())
    rng = DeterministicRNG(initial_state.seed)
    kernel = Kernel(profile, initial_state, rng, flags={"no_replay": True, "no_frame_pacing": True})  # the M1 defaults of ``run_benchmark``
    gc_was_enabled = gc.isenabled()
    try:
        for _ in range(warmup_ticks):
            kernel.tick_once()
        gc.collect()
        rss_before = process.memory_info().rss / (1024 * 1024)
        blocks_before = sys.getallocatedblocks()
        collected_before = _gc_collected_total()
        gc.enable()
        for _ in range(sample_ticks):
            kernel.tick_once()
        gc.collect()
        rss_after_collect = process.memory_info().rss / (1024 * 1024)
        trimmed = _malloc_trim()
        rss_after_trim = process.memory_info().rss / (1024 * 1024) if trimmed else None
        blocks_after = sys.getallocatedblocks()
        return MemoryPassReading(
            scenario_id=scenario_id,
            seed=initial_state.seed,
            profile_name=profile.name,
            warmup_ticks=warmup_ticks,
            sample_ticks=sample_ticks,
            rss_before_mb=rss_before,
            rss_after_collect_mb=rss_after_collect,
            rss_after_trim_mb=rss_after_trim,
            blocks_delta=blocks_after - blocks_before,
            gc_collected=_gc_collected_total() - collected_before,
        )
    finally:
        if not gc_was_enabled:
            gc.disable()
        kernel.shutdown()


@dataclass(frozen=True)
class _CollectedMemory:
    """Memory read with every unreachable object collected, before the sampled window and after it (TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE).

    The collector is disabled for the sampled ticks, so ``mem_rss_mb`` / ``peak_rss_mb`` include the cyclic garbage the engine makes meanwhile, and a
    ``gc.collect()`` alone does not bring RSS back: the freed memory stays mapped in the allocator (measured: 402 MB after collect, 125.6 MB after
    ``malloc_trim(0)``, against 99.6 MB at the end of warm-up). So there are three RSS readings: ``rss_before_window_mb`` (after the ``gc.collect()`` that
    precedes the window, untrimmed: trimming before the window would hand pages back and make the sampled ticks fault them in again),
    ``rss_after_collect_mb`` (after a ``gc.collect()`` taken once the window's wall and CPU clocks have stopped) and ``rss_after_trim_mb`` (after
    ``malloc_trim(0)`` straight after it, ``None`` where glibc's is unavailable). ``blocks_*`` (live Python allocations) does not depend on the allocator.
    ``gc_collected`` is the change of ``gc.get_stats()``' collected total over the window plus the end collect.
    """

    rss_before_mb: float
    blocks_before: int
    rss_after_collect_mb: float
    rss_after_trim_mb: Optional[float]
    blocks_after: int
    gc_collected: int
    collect_s: float


class BenchHarness:
    """
    Dedicated harness for high-frequency performance measurement.
    Adheres to the V2 Engine Performance Contract.
    
    Enhanced with:
    - RSS Memory monitoring via psutil
    - p50/p95/p99 latency percentiles (nearest-rank, PERF-M2 OD-1)
    - Phase-specific cost distribution
    - A typed ``BenchmarkRecord`` (schema 1.0) of the last run in ``last_record``; the returned dict is unchanged by it
    """

    def __init__(self, profile: RuntimeProfile):
        self._profile = profile
        self._process = psutil.Process(os.getpid())
        self.last_record: Optional[BenchmarkRecord] = None

    def run_benchmark(
        self,
        scenario_id: str,
        initial_state: AuthoritativeState,
        warmup_ticks: int = 100,
        sample_ticks: int = 1000,
        phase_budgets: Optional[Dict[str, float]] = None,
        flags: Optional[Dict[str, bool]] = None,
        record_options: Optional[RecordOptions] = None,
    ) -> Dict[str, Any]:
        """
        Execute a stable measurement run: Warmup -> Sample -> Collate.
        
        M1 Law: Benchmarks default to no_replay and no_frame_pacing to measure 
        raw engine compute throughput.

        The returned dict is unchanged by the typed record; the record of this run is left in ``last_record``.
        ``record_options`` picks the projection the record is for (default: tripwire).
        """
        # Set M1 defaults
        effective_flags = {"no_replay": True, "no_frame_pacing": True}
        if flags:
            effective_flags.update(flags)
            
        logger.info(f"Starting Benchmark: {scenario_id} ({self._profile.name})")
        logger.info(f"Flags: {effective_flags}")

        self.last_record = None
        subject = RunSubject(
            scenario_id=scenario_id,
            entity_count=len(initial_state.entities),
            seed=initial_state.seed,
            flags=effective_flags,
            warmup_ticks=warmup_ticks,
        )

        # Initialize Kernel — always shut down to release EventRecorder thread
        rng = DeterministicRNG(initial_state.seed)
        kernel = Kernel(self._profile, initial_state, rng, flags=effective_flags)

        try:
            cpu_start = self._process.cpu_times()

            # 1. WARMUP
            for _ in range(warmup_ticks):
                kernel.tick_once()

            gc.collect()
            before_window = (self._rss_mb(), sys.getallocatedblocks(), _gc_collected_total())
            gc_was_enabled = gc.isenabled()
            gc.disable()

            # 2. SAMPLING
            rss_samples: List[float] = []
            mode_samples: List[str] = []
            tick_wall_ms: List[float] = []
            history: List[Any] = []  # every sampled tick's signals: RuntimeStatus keeps only the last 100
            wall_start_ts = time.perf_counter()

            try:
                for i in range(sample_ticks):
                    tick_start_ts = time.perf_counter()
                    kernel.tick_once()
                    tick_wall_ms.append((time.perf_counter() - tick_start_ts) * 1000.0)
                    history.extend(kernel.status.get_recent_history(1))

                    # RuntimeMode is a trivial IntEnum read — sample every tick, unlike the
                    # throttled RSS collector below, so a transient CONSTRAINED/DEGRADED/SURVIVAL
                    # excursion inside an un-sampled gap can never be missed
                    # (TCK-20260817-RUNTIMEMODE-BENCH-SCOPING; see plan.md Design Decisions (a)).
                    mode_samples.append(kernel.status.current_mode.name)

                    # Sample memory every 10 ticks to reduce overhead
                    if i % 10 == 0:
                        rss_samples.append(self._rss_mb())
            finally:
                if gc_was_enabled:
                    gc.enable()

            wall_end_ts = time.perf_counter()
            cpu_end = self._process.cpu_times()

            # Outside both timed spans: ``gc.collect()`` runs whether or not the collector is enabled, so the ``finally`` above stays the only place
            # that changes its state.
            collected = self._collect_and_read(before_window)

            wall_clock_s = wall_end_ts - wall_start_ts
            wall_clock_tps = sample_ticks / wall_clock_s if wall_clock_s > 0 else 0

            # 3. COLLATION
            measured = self._collate(history, tick_wall_ms, mode_samples)
            tick_times = measured.tick_times

            # Compute TPS: Theoretical throughput if no wall-clock overhead
            total_compute_ms = sum(tick_times)
            compute_tps = (sample_ticks * 1000.0) / total_compute_ms if total_compute_ms > 0 else 0

            cpu_time_user_delta_s = cpu_end.user - cpu_start.user
            cpu_time_system_delta_s = cpu_end.system - cpu_start.system
            cpu_time_total_delta_s = cpu_time_user_delta_s + cpu_time_system_delta_s

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
                "phase_breakdown": measured.phase_stats,
                "metrics": measured.metric_stats,
                "cpu_time_user_delta_s": round(cpu_time_user_delta_s, 4),
                "cpu_time_system_delta_s": round(cpu_time_system_delta_s, 4),
                "cpu_time_total_delta_s": round(cpu_time_total_delta_s, 4),
                "replay_enabled": not effective_flags.get("no_replay", False),
                "frame_pacing_enabled": not effective_flags.get("no_frame_pacing", False),
                "timestamp": time.time(),
                "mode_sequence": mode_samples,
            }

            # Add flat keys for schema compliance
            result.update(
                {
                    "avg_tick_compute_ms": result["tick_ms"]["avg"],
                    "p50_tick_compute_ms": result["tick_ms"]["p50"],
                    "p95_tick_compute_ms": result["tick_ms"]["p95"],
                    "p99_tick_compute_ms": result["tick_ms"]["p99"],
                    "max_tick_compute_ms": result["tick_ms"]["max"],
                    "peak_rss_mb": result["mem_rss_mb"]["max"],
                    "memory_delta_mb": result["mem_rss_mb"]["delta"],
                }
            )

            self.last_record = self._build_record(result, measured, subject, record_options or RecordOptions(), collected)

            self._enforce_phase_budgets(phase_budgets, measured.phase_stats, scenario_id)

            return result

        finally:
            kernel.shutdown()

    def _collect_and_read(self, before_window: Tuple[float, int, int]) -> _CollectedMemory:
        """One full ``gc.collect()``, timed, then the RSS and live-block readings (and RSS again after ``malloc_trim``) that pair with those taken before the window."""
        start_ts = time.perf_counter()
        gc.collect()
        collect_s = time.perf_counter() - start_ts
        rss_after_collect = self._rss_mb()
        blocks_after = sys.getallocatedblocks()
        trimmed = _malloc_trim()
        rss_after_trim = self._rss_mb() if trimmed else None
        return _CollectedMemory(before_window[0], before_window[1], rss_after_collect, rss_after_trim, blocks_after, _gc_collected_total() - before_window[2], collect_s)

    def _rss_mb(self) -> float:
        return float(self._process.memory_info().rss) / (1024 * 1024)

    def _collate(self, history: List[Any], tick_wall_ms: List[float], mode_samples: List[str]) -> _Measured:
        """Fold the kernel's per-tick signals into the series and aggregates the result dict and the record are both built from."""
        phase_aggregates: Dict[str, List[float]] = {}
        metric_aggregates: Dict[str, List[float]] = {}
        for signals in history:
            for phase, cost in signals.phase_costs_ms.items():
                phase_aggregates.setdefault(phase, []).append(cost)
            if hasattr(signals, "metrics") and signals.metrics:
                for k, v in signals.metrics.items():
                    metric_aggregates.setdefault(k, []).append(float(v))

        return _Measured(
            tick_times=[s.tick_compute_ms for s in history],
            tick_wall_ms=tick_wall_ms,
            mode_samples=mode_samples,
            phase_stats={phase: self._calculate_stats(costs) for phase, costs in phase_aggregates.items()},
            metric_stats={k: round(sum(vals) / len(vals), 2) if vals else 0.0 for k, vals in metric_aggregates.items()},
        )

    def _enforce_phase_budgets(self, phase_budgets: Optional[Dict[str, float]], phase_stats: Dict[str, Dict[str, float]], scenario_id: str) -> None:
        """Law 125: Phase Budget Enforcement."""
        if not phase_budgets or self._profile.max_tick_budget_ms <= 0:
            return
        for phase, budget_ratio in phase_budgets.items():
            if phase in phase_stats:
                p95_ms = phase_stats[phase]["p95"]
                limit_ms = self._profile.max_tick_budget_ms * budget_ratio
                if p95_ms > limit_ms:
                    raise PerformanceRegressionError(
                        f"Phase '{phase}' exceeded budget in scenario '{scenario_id}': "
                        f"p95={p95_ms:.2f}ms, limit={limit_ms:.2f}ms ({budget_ratio*100}% of {self._profile.max_tick_budget_ms}ms)"
                    )

    def _build_record(
        self, result: Dict[str, Any], measured: _Measured, subject: RunSubject, options: RecordOptions, collected: Optional[_CollectedMemory] = None
    ) -> Optional[BenchmarkRecord]:
        """Assemble the typed record from the numbers already collated. A failure here is logged and never fails the benchmark.

        ``memory_mb.rss_high_water`` and ``rss_delta`` come from RSS samples taken with the collector disabled, so they **include the cyclic garbage the
        engine made during the window**; the after-collect keys (``collected``) do not. ``rss_over_declared`` is ``rss_after_trim_mb /
        RuntimeProfile.max_ram_mb`` (report only, never a gate), or ``rss_after_collect_mb / max_ram_mb`` where the trim is unavailable, and
        ``rss_over_declared_basis_trim`` says which (1.0 trim, 0.0 collect); the peak-based ratio is the separate key ``peak_rss_over_declared``.
        """
        try:
            wall_ms = [round(v, 4) for v in measured.tick_wall_ms]
            compute_ms = [round(v, 4) for v in measured.tick_times]
            if options.gate_tier is GateTier.TRIPWIRE and len(compute_ms) <= MAX_EMBEDDED_SAMPLES:
                samples = Samples(tick_wall_ms=tuple(wall_ms), tick_compute_ms=tuple(compute_ms))
            else:
                stem = f"{subject.scenario_id}_{self._profile.name}_{int(result['timestamp'])}"
                samples = write_samples_file(options.samples_dir or default_samples_dir(), stem, wall_ms, compute_ms)
            return BenchmarkRecord(
                identity=collect_identity(self._profile, subject, options),
                result=Result(
                    protocol=Protocol(
                        warmup_ticks=subject.warmup_ticks,
                        measured_ticks=result["sample_ticks"],
                        percentile_method=PercentileMethod.NEAREST_RANK,
                    ),
                    latency_ms=dict(result["tick_ms"]),
                    throughput={"compute_tps": result["compute_tps"], "wall_tps": result["wall_clock_tps"]},
                    time_s={
                        "wall": result["wall_clock_s"],
                        "cpu_user": result["cpu_time_user_delta_s"],
                        "cpu_system": result["cpu_time_system_delta_s"],
                    },
                    memory_mb=self._memory_mb(result, collected),
                    runtime_mode_sequence=compress_modes(measured.mode_samples),
                    outcome=Outcome(OutcomeState.NOT_APPLICABLE, "single measurement: no comparison was made"),
                    recorded_at=utc_now(),
                    samples=samples,
                    work=dict(measured.metric_stats),
                    phases={k: dict(v) for k, v in measured.phase_stats.items()},
                ),
            )
        except Exception:  # noqa: BLE001 - the record is additive; a failure to build it must never fail a benchmark (logged with traceback)
            logger.warning("BenchmarkRecord could not be built for %s; the result dict is unaffected", subject.scenario_id, exc_info=True)
            return None

    def _memory_mb(self, result: Dict[str, Any], collected: Optional[_CollectedMemory]) -> Dict[str, float]:
        """The record's ``memory_mb``: the old keys unchanged, plus the after-collect readings and the declared-memory ratios when ``collected`` exists."""
        memory: Dict[str, float] = {
            "rss_high_water": result["mem_rss_mb"]["max"],
            "rss_delta": result["mem_rss_mb"]["delta"],
            "sample_every_ticks": 10,
        }
        if collected is None:
            return memory
        declared = float(self._profile.max_ram_mb)
        rss_basis = collected.rss_after_trim_mb if collected.rss_after_trim_mb is not None else collected.rss_after_collect_mb
        memory.update(
            {
                "rss_before_window_mb": round(collected.rss_before_mb, 2),
                "rss_after_collect_mb": round(collected.rss_after_collect_mb, 2),
                "allocated_blocks_delta": float(collected.blocks_after - collected.blocks_before),
                "gc_collected_objects": float(collected.gc_collected),
                "gc_collect_s": round(collected.collect_s, 4),
                "declared_ram_mb": declared,
                "rss_over_declared": round(rss_basis / declared, 4),
                "rss_over_declared_basis_trim": 1.0 if collected.rss_after_trim_mb is not None else 0.0,
                "peak_rss_over_declared": round(result["mem_rss_mb"]["max"] / declared, 4),
            }
        )
        if collected.rss_after_trim_mb is not None:
            memory["rss_after_trim_mb"] = round(collected.rss_after_trim_mb, 2)
            memory["rss_trim_delta_mb"] = round(collected.rss_after_trim_mb - collected.rss_before_mb, 2)
        return memory

    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """Distribution statistics. Percentiles are nearest-rank, ceil(q * n) (PERF-M2 OD-1), not ``sorted[int(n * q)]``."""
        return latency_stats(values)
