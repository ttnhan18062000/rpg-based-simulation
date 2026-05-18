from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


class MissingBaselineError(Exception):
    """Raised when an automated performance regression check in CI mode lacks a baseline."""
    pass


@dataclass(frozen=True)
class PerfBaseline:
    """Committed performance baseline metrics for a specific simulation scenario."""
    scenario_id: str
    p95_tick_compute_ms: float
    p99_tick_compute_ms: float
    peak_rss_mb: float
    memory_delta_mb: float
    compute_tps: float
    raw_entity_updates: int = 0
    compacted_entity_updates: int = 0
    phase_p95_ms: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class PerfResult:
    """Benchmarked performance metrics from an active execution run."""
    scenario_id: str
    p95_tick_compute_ms: float
    p99_tick_compute_ms: float
    peak_rss_mb: float
    memory_delta_mb: float
    compute_tps: float
    wall_clock_tps: float = 0.0
    raw_entity_updates: int = 0
    compacted_entity_updates: int = 0
    phase_p95_ms: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_bench_dict(cls, data: Dict[str, Any]) -> PerfResult:
        """Construct a PerfResult from the dictionary returned by BenchHarness.run_benchmark."""
        phase_breakdown = data.get("phase_breakdown", {})
        phase_p95 = {}
        for phase, stats in phase_breakdown.items():
            if isinstance(stats, dict) and "p95" in stats:
                phase_p95[phase] = float(stats["p95"])

        return cls(
            scenario_id=str(data.get("scenario_id", "unknown")),
            p95_tick_compute_ms=float(data.get("p95_tick_compute_ms", 0.0)),
            p99_tick_compute_ms=float(data.get("p99_tick_compute_ms", 0.0)),
            peak_rss_mb=float(data.get("peak_rss_mb", 0.0)),
            memory_delta_mb=float(data.get("memory_delta_mb", 0.0)),
            compute_tps=float(data.get("compute_tps", 0.0)),
            wall_clock_tps=float(data.get("wall_clock_tps", 0.0)),
            raw_entity_updates=int(data.get("raw_entity_updates", 0)),
            compacted_entity_updates=int(data.get("compacted_entity_updates", 0)),
            phase_p95_ms=phase_p95
        )


@dataclass(frozen=True)
class PerfGateResult:
    """Outcome of a performance regression gate evaluation."""
    passed: bool
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PerfRegressionGate:
    """
    Compares active performance results against committed baselines.
    Enforces computational latency, throughput, and memory stability
    while isolating comparisons from wall-clock variance.
    """

    def __init__(
        self, 
        ci_mode: bool = True, 
        tolerance_percent: float = 10.0,
        mem_tolerance_percent: float = 15.0
    ):
        self.ci_mode = ci_mode
        self.tolerance_percent = tolerance_percent
        self.mem_tolerance_percent = mem_tolerance_percent

    def compare(
        self,
        baseline: Optional[PerfBaseline],
        current: PerfResult
    ) -> PerfGateResult:
        """
        Evaluate whether the current result regresses beyond allowable thresholds
        compared to the baseline.
        """
        if baseline is None:
            if self.ci_mode:
                raise MissingBaselineError(
                    f"CI cannot silently skip missing baseline for scenario '{current.scenario_id}'"
                )
            return PerfGateResult(
                passed=True,
                warnings=[f"Missing baseline for scenario '{current.scenario_id}' in local mode; skipping verification"]
            )

        if baseline.scenario_id != current.scenario_id:
            return PerfGateResult(
                passed=False,
                reasons=[f"Scenario mismatch: baseline is '{baseline.scenario_id}', current is '{current.scenario_id}'"]
            )

        reasons: List[str] = []
        warnings: List[str] = []

        # 1. Compute Latency (p95, p99)
        max_p95 = baseline.p95_tick_compute_ms * (1.0 + self.tolerance_percent / 100.0)
        if current.p95_tick_compute_ms > max_p95:
            reasons.append(
                f"p95_tick_compute_ms regressed: {current.p95_tick_compute_ms:.2f}ms vs baseline {baseline.p95_tick_compute_ms:.2f}ms "
                f"(max allowable: {max_p95:.2f}ms, +{self.tolerance_percent}%)"
            )

        max_p99 = baseline.p99_tick_compute_ms * (1.0 + self.tolerance_percent / 100.0)
        if current.p99_tick_compute_ms > max_p99:
            reasons.append(
                f"p99_tick_compute_ms regressed: {current.p99_tick_compute_ms:.2f}ms vs baseline {baseline.p99_tick_compute_ms:.2f}ms "
                f"(max allowable: {max_p99:.2f}ms, +{self.tolerance_percent}%)"
            )

        # 2. Compute Throughput (TPS)
        min_tps = baseline.compute_tps * (1.0 - self.tolerance_percent / 100.0)
        if current.compute_tps < min_tps and baseline.compute_tps > 0:
            reasons.append(
                f"compute_tps degraded: {current.compute_tps:.2f} TPS vs baseline {baseline.compute_tps:.2f} TPS "
                f"(min allowable: {min_tps:.2f} TPS, -{self.tolerance_percent}%)"
            )

        # Note: wall_clock_tps is explicitly ignored for pass/fail decisions to isolate compute from OS noise.

        # 3. Memory Consumption (Peak RSS & Delta)
        max_rss = baseline.peak_rss_mb * (1.0 + self.mem_tolerance_percent / 100.0)
        if current.peak_rss_mb > max_rss and baseline.peak_rss_mb > 0:
            reasons.append(
                f"peak_rss_mb regressed: {current.peak_rss_mb:.2f}MB vs baseline {baseline.peak_rss_mb:.2f}MB "
                f"(max allowable: {max_rss:.2f}MB, +{self.mem_tolerance_percent}%)"
            )

        # For memory delta, allow either a small flat variance (e.g., 5MB) or the percentage tolerance
        max_delta = baseline.memory_delta_mb + max(5.0, baseline.memory_delta_mb * (self.mem_tolerance_percent / 100.0))
        if current.memory_delta_mb > max_delta:
            reasons.append(
                f"memory_delta_mb regressed: {current.memory_delta_mb:.2f}MB vs baseline {baseline.memory_delta_mb:.2f}MB "
                f"(max allowable: {max_delta:.2f}MB)"
            )

        # 4. Phase-level p95 Latency
        for phase, base_p95 in baseline.phase_p95_ms.items():
            curr_p95 = current.phase_p95_ms.get(phase, 0.0)
            # Only check if base_p95 is non-trivial (> 0.1ms) to avoid false positives on microsecond noise
            if base_p95 > 0.1:
                max_phase_p95 = base_p95 * (1.0 + self.tolerance_percent / 100.0)
                if curr_p95 > max_phase_p95:
                    reasons.append(
                        f"Phase '{phase}' p95 regressed: {curr_p95:.2f}ms vs baseline {base_p95:.2f}ms "
                        f"(max allowable: {max_phase_p95:.2f}ms, +{self.tolerance_percent}%)"
                    )

        # 5. Compaction Efficiency Monitoring
        if current.raw_entity_updates > 0 and current.compacted_entity_updates > current.raw_entity_updates:
            warnings.append(
                f"Compaction anomaly: compacted updates ({current.compacted_entity_updates}) exceed raw updates ({current.raw_entity_updates})"
            )

        passed = len(reasons) == 0
        return PerfGateResult(passed=passed, reasons=reasons, warnings=warnings)
