# Compliance IDs: PERF-001, PERF-002, PERF-004, PERF-018
from __future__ import annotations

import gc
import os
import time
import logging
import statistics
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

import psutil

from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.perf.scenarios import SCENARIO_BUILDERS
from src.api.read_model_cache import ReadModelCache
from src.engine.checkpoint import CanonicalStateHasher

logger = logging.getLogger(__name__)


class RunMode(str, Enum):
    """Execution modes for long-run stability testing."""
    PURE = "pure"        # Unthrottled raw compute (no governor degradation, no replay, no pacing)
    RUNTIME = "runtime"  # Governed adaptive execution (active phase budgets and governors)


@dataclass(frozen=True, slots=True)
class LongRunSample:
    """Telemetry sample captured at specified tick intervals during long runs."""
    tick: int
    rss_mb: float
    gc_collections: Tuple[int, int, int]  # (gen0, gen1, gen2)
    p50_tick_ms: float
    p95_tick_ms: float
    p99_tick_ms: float
    movement_cache_size: int
    read_model_cache_size: int
    spatial_index_entries: int
    candidate_count: int
    work_debt: int
    active_mode: str
    timestamp: float = field(default_factory=time.perf_counter)


@dataclass
class LongRunStabilityReport:
    """Authoritative certification report proving engine stability over extended horizons."""
    scenario_id: str
    run_mode: RunMode
    total_ticks: int
    entity_count: int
    warmup_ticks: int
    sample_interval_ticks: int
    seed: int
    
    # Baseline vs Final Metrics
    warmup_rss_mb: float
    peak_rss_mb: float
    rss_growth_ratio: float
    
    initial_p95_ms: float
    final_p95_ms: float
    latency_drift_ratio: float
    
    peak_movement_cache_size: int
    peak_read_model_cache_size: int
    
    total_gc_collections: Tuple[int, int, int]
    
    # Invariant Certifications
    rss_bounded: bool
    latency_stable: bool
    caches_bounded: bool
    gc_stable: bool
    passed_certification: bool
    
    final_state_hash: str
    samples: List[LongRunSample] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "run_mode": self.run_mode.value,
            "total_ticks": self.total_ticks,
            "entity_count": self.entity_count,
            "seed": self.seed,
            "metrics": {
                "warmup_rss_mb": round(self.warmup_rss_mb, 2),
                "peak_rss_mb": round(self.peak_rss_mb, 2),
                "rss_growth_ratio": round(self.rss_growth_ratio, 3),
                "initial_p95_ms": round(self.initial_p95_ms, 3),
                "final_p95_ms": round(self.final_p95_ms, 3),
                "latency_drift_ratio": round(self.latency_drift_ratio, 3),
                "peak_movement_cache_size": self.peak_movement_cache_size,
                "peak_read_model_cache_size": self.peak_read_model_cache_size,
                "total_gc_collections": list(self.total_gc_collections)
            },
            "certifications": {
                "rss_bounded": self.rss_bounded,
                "latency_stable": self.latency_stable,
                "caches_bounded": self.caches_bounded,
                "gc_stable": self.gc_stable,
                "passed_certification": self.passed_certification
            },
            "final_state_hash": self.final_state_hash
        }


class LongRunStabilityHarness:
    """
    Milestone 18: Long-Run Stability Certification Harness.
    Executes extended multi-thousand tick simulations monitoring RSS memory trends,
    optimization cache boundaries, garbage collection frequency, and latency degradation.
    """

    def __init__(self, profile: RuntimeProfile):
        self._profile = profile
        self._process = psutil.Process(os.getpid())

    def execute_run(
        self,
        scenario_id: str,
        total_ticks: int = 5000,
        entity_count: int = 1000,
        warmup_ticks: int = 200,
        sample_interval: int = 50,
        mode: RunMode = RunMode.PURE,
        seed: int = 42,
        flags: Optional[Dict[str, bool]] = None
    ) -> LongRunStabilityReport:
        """
        Execute a full long-run certification benchmarking simulation.
        """
        logger.info(f"Starting Long-Run Stability Certification: {scenario_id} ({mode.value.upper()} mode, {total_ticks} ticks)")
        
        # 1. Bootstrapping State
        if scenario_id not in SCENARIO_BUILDERS:
            raise ValueError(f"Unknown scenario ID: {scenario_id}. Available: {list(SCENARIO_BUILDERS.keys())}")
            
        builder = SCENARIO_BUILDERS[scenario_id]
        initial_state = builder(entity_count=entity_count, seed=seed)
            
        # 2. Configure Runtime Flags
        effective_flags = {
            "no_frame_pacing": True,
            "no_replay": mode == RunMode.PURE,
            "force_full_scan": False
        }
        if flags:
            effective_flags.update(flags)
            
        rng = DeterministicRNG(seed)
        kernel = Kernel(self._profile, initial_state, rng, flags=effective_flags)
        read_cache = ReadModelCache()
        
        # Initial GC Baseline
        gc.collect()
        initial_gc = self._get_gc_collections()
        
        # 3. WARMUP STAGE
        logger.info(f"Executing {warmup_ticks} warmup ticks...")
        for _ in range(warmup_ticks):
            kernel.tick_once()
            read_cache.update(kernel.state)
            
        warmup_rss = self._process.memory_info().rss / (1024 * 1024)
        logger.info(f"Warmup complete. Warmup RSS: {warmup_rss:.2f} MB")
        
        # 4. SAMPLING STAGE
        samples: List[LongRunSample] = []
        recent_tick_ms: List[float] = []
        
        start_ts = time.perf_counter()
        tick_times = []
        
        for t in range(1, total_ticks + 1):
            t_start = time.perf_counter_ns()
            kernel.tick_once()
            read_cache.update(kernel.state)
            t_ms = (time.perf_counter_ns() - t_start) / 1e6
            recent_tick_ms.append(t_ms)
            tick_times.append(t_ms)
            
            if len(recent_tick_ms) > sample_interval:
                recent_tick_ms.pop(0)
                
            if t % sample_interval == 0 or t == total_ticks:
                rss = self._process.memory_info().rss / (1024 * 1024)
                gc_counts = self._get_gc_collections()
                
                # Compute latency percentiles over the recent window
                sorted_ms = sorted(recent_tick_ms)
                cnt = len(sorted_ms)
                p50 = sorted_ms[int(cnt * 0.5)] if cnt else 0.0
                p95 = sorted_ms[int(cnt * 0.95)] if cnt else 0.0
                p99 = sorted_ms[int(cnt * 0.99)] if cnt else 0.0
                
                # Cache Sizes
                m_cache = getattr(kernel.state, "movement_cache", None)
                m_size = len(getattr(m_cache, "_cache", {})) if m_cache else 0
                r_size = len(getattr(read_cache, "_entity_dtos", {}))
                
                # Spatial index
                s_size = len(kernel.state.entities)
                work_debt = sum(kernel.state.work_debt.values())
                candidate_count = sum(len(q) for q in kernel.state.work_debt.values()) if kernel.state.work_debt else 0
                
                sample = LongRunSample(
                    tick=t,
                    rss_mb=rss,
                    gc_collections=gc_counts,
                    p50_tick_ms=p50,
                    p95_tick_ms=p95,
                    p99_tick_ms=p99,
                    movement_cache_size=m_size,
                    read_model_cache_size=r_size,
                    spatial_index_entries=s_size,
                    candidate_count=candidate_count,
                    work_debt=work_debt,
                    active_mode=kernel.status.current_mode.name
                )
                samples.append(sample)
                
        total_s = time.perf_counter() - start_ts
        logger.info(f"Simulation completed {total_ticks} ticks in {total_s:.2f}s (Avg: {sum(tick_times)/len(tick_times):.2f} ms/tick)")
        
        # Final shutdown and hash
        shutdown_res = kernel.shutdown()
        final_hash = shutdown_res.final_hash
        
        # 5. INVARIANT STABILITY CHECKS
        peak_rss = max(s.rss_mb for s in samples) if samples else warmup_rss
        rss_growth = peak_rss / warmup_rss if warmup_rss > 0 else 1.0
        
        # Latency Drift Check: Compare first 20% vs last 20% of samples
        window = max(1, len(samples) // 5)
        initial_p95 = statistics.mean([s.p95_tick_ms for s in samples[:window]]) if samples else 0.0
        final_p95 = statistics.mean([s.p95_tick_ms for s in samples[-window:]]) if samples else 0.0
        latency_drift = final_p95 / initial_p95 if initial_p95 > 0 else 1.0
        
        peak_m_cache = max(s.movement_cache_size for s in samples) if samples else 0
        peak_r_cache = max(s.read_model_cache_size for s in samples) if samples else 0
        
        final_gc = self._get_gc_collections()
        total_gc_delta = (
            final_gc[0] - initial_gc[0],
            final_gc[1] - initial_gc[1],
            final_gc[2] - initial_gc[2]
        )
        
        # Certification Invariants:
        # 1. RSS Bounded: Peak RSS growth <= 2.0x of warmup (or under 512MB hard envelope)
        rss_bounded = rss_growth <= 2.0 or peak_rss <= 512.0
        
        # 2. Latency Stable: Final p95 <= 1.5x of initial p95 (or absolute increase under 15ms)
        latency_stable = latency_drift <= 1.5 or (final_p95 - initial_p95) <= 15.0
        
        # 3. Caches Bounded: Optimization caches do not grow indefinitely beyond entity count multipliers
        caches_bounded = peak_m_cache <= (entity_count * 10) and peak_r_cache <= (entity_count * 2)
        
        # 4. GC Stable: GC collections remain healthy across long horizons
        gc_stable = total_gc_delta[2] <= max(10, total_ticks // 10) and total_gc_delta[1] <= max(100, total_ticks)
        
        passed = rss_bounded and latency_stable and caches_bounded and gc_stable
        
        report = LongRunStabilityReport(
            scenario_id=scenario_id,
            run_mode=mode,
            total_ticks=total_ticks,
            entity_count=entity_count,
            warmup_ticks=warmup_ticks,
            sample_interval_ticks=sample_interval,
            seed=seed,
            warmup_rss_mb=warmup_rss,
            peak_rss_mb=peak_rss,
            rss_growth_ratio=rss_growth,
            initial_p95_ms=initial_p95,
            final_p95_ms=final_p95,
            latency_drift_ratio=latency_drift,
            peak_movement_cache_size=peak_m_cache,
            peak_read_model_cache_size=peak_r_cache,
            total_gc_collections=total_gc_delta,
            rss_bounded=rss_bounded,
            latency_stable=latency_stable,
            caches_bounded=caches_bounded,
            gc_stable=gc_stable,
            passed_certification=passed,
            final_state_hash=final_hash,
            samples=samples
        )
        
        return report

    def verify_determinism_parity(
        self,
        scenario_id: str,
        total_ticks: int = 1000,
        entity_count: int = 500,
        seed: int = 42
    ) -> Tuple[bool, str, str]:
        """
        Verify that two independent multi-thousand tick simulation runs across identical seeds
        produce 100% exact bit-identical state hashes at termination.
        """
        logger.info(f"Verifying determinism parity across {total_ticks} ticks (Seed {seed})...")
        builder = SCENARIO_BUILDERS[scenario_id]
        
        effective_flags = {
            "no_replay": True,
            "no_frame_pacing": True,
            "audit_mode": True  # M8 Law: Guarantees 100% exact determinism by zeroing wall-clock time signals
        }
        
        # Run 1
        state1 = builder(entity_count=entity_count, seed=seed)
        kernel1 = Kernel(self._profile, state1, DeterministicRNG(seed), flags=effective_flags)
        for _ in range(total_ticks):
            kernel1.tick_once()
        hash1 = kernel1.shutdown().final_hash
        
        # Run 2
        state2 = builder(entity_count=entity_count, seed=seed)
        kernel2 = Kernel(self._profile, state2, DeterministicRNG(seed), flags=effective_flags)
        for _ in range(total_ticks):
            kernel2.tick_once()
        hash2 = kernel2.shutdown().final_hash
        
        passed = (hash1 == hash2)
        logger.info(f"Determinism Check: {'PASSED' if passed else 'FAILED'} (Hash1: {hash1}, Hash2: {hash2})")
        return passed, hash1, hash2

    def _get_gc_collections(self) -> Tuple[int, int, int]:
        """Extract generation collection counts safely across python versions."""
        try:
            stats = gc.get_stats()
            return (
                stats[0]["collections"],
                stats[1]["collections"],
                stats[2]["collections"]
            )
        except Exception:
            # Fallback if get_stats behaves differently
            cnt = gc.get_count()
            return (cnt[0], cnt[1], cnt[2])
