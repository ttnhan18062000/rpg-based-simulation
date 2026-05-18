from __future__ import annotations

import pytest

from src.perf.regression_gate import (
    PerfBaseline,
    PerfResult,
    PerfGateResult,
    PerfRegressionGate,
    MissingBaselineError,
)


def test_perf_gate_passes_within_threshold() -> None:
    """Verify that current metrics within tolerance of the baseline pass successfully."""
    baseline = PerfBaseline(
        scenario_id="idle",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0,
        phase_p95_ms={"movement": 2.0}
    )
    current = PerfResult(
        scenario_id="idle",
        p95_tick_compute_ms=10.5, # +5% (within 10% tolerance)
        p99_tick_compute_ms=15.5,
        peak_rss_mb=52.0,
        memory_delta_mb=2.5,
        compute_tps=98.0, # -2% (within 10% tolerance)
        wall_clock_tps=95.0,
        phase_p95_ms={"movement": 2.1}
    )

    gate = PerfRegressionGate(tolerance_percent=10.0)
    result = gate.compare(baseline, current)

    assert result.passed is True
    assert len(result.reasons) == 0


def test_perf_gate_fails_when_p95_regresses_too_much() -> None:
    """Verify failure when p95_tick_compute_ms regresses beyond tolerance."""
    baseline = PerfBaseline(
        scenario_id="idle",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0,
        phase_p95_ms={}
    )
    current = PerfResult(
        scenario_id="idle",
        p95_tick_compute_ms=15.0, # +50% regression (> 10% tolerance)
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0,
        wall_clock_tps=100.0,
        phase_p95_ms={}
    )

    gate = PerfRegressionGate(tolerance_percent=10.0)
    result = gate.compare(baseline, current)

    assert result.passed is False
    assert len(result.reasons) == 1
    assert "p95_tick_compute_ms regressed" in result.reasons[0]


def test_perf_gate_fails_when_phase_regresses_too_much() -> None:
    """Verify failure when a specific phase's p95 cost regresses beyond tolerance."""
    baseline = PerfBaseline(
        scenario_id="idle",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0,
        phase_p95_ms={"movement": 5.0}
    )
    current = PerfResult(
        scenario_id="idle",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0,
        wall_clock_tps=100.0,
        phase_p95_ms={"movement": 8.0} # +60% regression in movement phase
    )

    gate = PerfRegressionGate(tolerance_percent=10.0)
    result = gate.compare(baseline, current)

    assert result.passed is False
    assert len(result.reasons) == 1
    assert "Phase 'movement' p95 regressed" in result.reasons[0]


def test_perf_gate_fails_when_memory_regresses_too_much() -> None:
    """Verify failure when peak RSS or memory delta regresses beyond memory tolerance."""
    baseline = PerfBaseline(
        scenario_id="idle",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=100.0,
        memory_delta_mb=10.0,
        compute_tps=100.0,
        phase_p95_ms={}
    )
    current = PerfResult(
        scenario_id="idle",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=130.0, # +30% peak RSS regression (> 15% mem tolerance)
        memory_delta_mb=30.0, # +200% memory delta regression
        compute_tps=100.0,
        wall_clock_tps=100.0,
        phase_p95_ms={}
    )

    gate = PerfRegressionGate(tolerance_percent=10.0, mem_tolerance_percent=15.0)
    result = gate.compare(baseline, current)

    assert result.passed is False
    assert len(result.reasons) == 2
    assert any("peak_rss_mb regressed" in r for r in result.reasons)
    assert any("memory_delta_mb regressed" in r for r in result.reasons)


def test_perf_gate_ignores_wall_clock_tps_for_compute_regression() -> None:
    """Verify that severe drop in wall-clock TPS due to OS noise does not cause regression failure."""
    baseline = PerfBaseline(
        scenario_id="idle",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0,
        phase_p95_ms={}
    )
    current = PerfResult(
        scenario_id="idle",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0, # Pure compute TPS is perfectly stable
        wall_clock_tps=10.0, # Noisy wall-clock TPS dropped 90%
        phase_p95_ms={}
    )

    gate = PerfRegressionGate(tolerance_percent=10.0)
    result = gate.compare(baseline, current)

    assert result.passed is True
    assert len(result.reasons) == 0


def test_missing_baseline_fails_in_ci_mode() -> None:
    """Verify that missing baseline raises MissingBaselineError in CI mode."""
    current = PerfResult(
        scenario_id="combat",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0,
        phase_p95_ms={}
    )

    gate = PerfRegressionGate(ci_mode=True)
    with pytest.raises(MissingBaselineError, match="CI cannot silently skip missing baseline"):
        gate.compare(None, current)


def test_missing_baseline_warns_or_skips_in_local_mode() -> None:
    """Verify that missing baseline returns passing result with warning in local mode."""
    current = PerfResult(
        scenario_id="combat",
        p95_tick_compute_ms=10.0,
        p99_tick_compute_ms=15.0,
        peak_rss_mb=50.0,
        memory_delta_mb=2.0,
        compute_tps=100.0,
        phase_p95_ms={}
    )

    gate = PerfRegressionGate(ci_mode=False)
    result = gate.compare(None, current)

    assert result.passed is True
    assert len(result.warnings) == 1
    assert "Missing baseline for scenario 'combat' in local mode" in result.warnings[0]


def test_perf_result_from_bench_dict() -> None:
    """Verify that PerfResult.from_bench_dict correctly parses BenchHarness output dictionary."""
    bench_data = {
        "scenario_id": "town",
        "p95_tick_compute_ms": 12.5,
        "p99_tick_compute_ms": 18.0,
        "peak_rss_mb": 64.0,
        "memory_delta_mb": 4.5,
        "compute_tps": 80.0,
        "wall_clock_tps": 78.5,
        "raw_entity_updates": 500,
        "compacted_entity_updates": 120,
        "phase_breakdown": {
            "movement": {"p95": 3.2},
            "combat": {"p95": 4.1}
        }
    }

    result = PerfResult.from_bench_dict(bench_data)

    assert result.scenario_id == "town"
    assert result.p95_tick_compute_ms == 12.5
    assert result.p99_tick_compute_ms == 18.0
    assert result.peak_rss_mb == 64.0
    assert result.memory_delta_mb == 4.5
    assert result.compute_tps == 80.0
    assert result.wall_clock_tps == 78.5
    assert result.raw_entity_updates == 500
    assert result.compacted_entity_updates == 120
    assert result.phase_p95_ms == {"movement": 3.2, "combat": 4.1}
