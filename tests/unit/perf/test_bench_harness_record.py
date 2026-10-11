"""BenchHarness emits a BenchmarkRecord next to its unchanged dict, with nearest-rank percentiles (TCK-20261010-PERF-M2-T02B-RECORD)."""
from __future__ import annotations

import json

import pytest

from src.perf.bench_harness import BenchHarness
from src.perf.benchmark_record import (
    BenchmarkRecord,
    GateTier,
    OutcomeState,
    PercentileMethod,
    RecordOptions,
)
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_movement_state

#: Keys the committed baselines and the gate readers rely on; the record must not add to or remove from them.
LEGACY_KEYS = {
    "scenario_id", "profile", "sample_ticks", "wall_clock_s", "wall_clock_tps", "compute_tps", "avg_tps", "tick_ms", "mem_rss_mb",
    "phase_breakdown", "metrics", "cpu_time_user_delta_s", "cpu_time_system_delta_s", "cpu_time_total_delta_s", "replay_enabled",
    "frame_pacing_enabled", "timestamp", "mode_sequence", "avg_tick_compute_ms", "p50_tick_compute_ms", "p95_tick_compute_ms",
    "p99_tick_compute_ms", "max_tick_compute_ms", "peak_rss_mb", "memory_delta_mb",
}


@pytest.fixture(scope="module")
def run():
    harness = BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"])
    result = harness.run_benchmark("RECORD_UNIT", build_movement_state(entity_count=20), warmup_ticks=3, sample_ticks=20)
    return harness, result


def test_the_result_dict_keeps_its_keys(run) -> None:
    _, result = run
    assert set(result) == LEGACY_KEYS


def test_the_harness_emits_a_record(run) -> None:
    harness, result = run
    record = harness.last_record
    assert isinstance(record, BenchmarkRecord)
    assert record.identity.scenario.id == "RECORD_UNIT" and record.identity.config.profile_name == "PERF_512MB_LOCAL"
    assert record.identity.workload.entity_count == 20
    assert record.result.protocol.percentile_method is PercentileMethod.NEAREST_RANK
    assert record.result.protocol.measured_ticks == 20 and record.result.protocol.warmup_ticks == 3
    assert record.result.latency_ms == result["tick_ms"]
    assert record.result.outcome.state is OutcomeState.NOT_APPLICABLE
    assert sum(run_.ticks for run_ in record.result.runtime_mode_sequence) == 20
    assert BenchmarkRecord.from_dict(json.loads(json.dumps(record.to_dict()))) == record


def test_the_tripwire_record_embeds_raw_samples_matching_the_latency(run) -> None:
    harness, result = run
    samples = harness.last_record.result.samples
    assert samples is not None and samples.tick_compute_ms is not None and samples.tick_wall_ms is not None
    assert len(samples.tick_compute_ms) == len(samples.tick_wall_ms) == 20
    assert max(samples.tick_compute_ms) == pytest.approx(result["tick_ms"]["max"], abs=1e-3)
    assert all(w >= 0 for w in samples.tick_wall_ms)


def test_the_capacity_record_carries_a_pointer(tmp_path) -> None:
    harness = BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"])
    harness.run_benchmark(
        "RECORD_CAP",
        build_movement_state(entity_count=20),
        warmup_ticks=1,
        sample_ticks=5,
        record_options=RecordOptions(gate_tier=GateTier.CAPACITY_RUN, samples_dir=tmp_path),
    )
    samples = harness.last_record.result.samples
    assert samples.uri and samples.sha256 and samples.tick_wall_ms is None
    assert json.loads(open(samples.uri).read())["tick_wall_ms"].__len__() == 5
    assert harness.last_record.identity.gate.tier is GateTier.CAPACITY_RUN


def test_nearest_rank_replaces_int_n_q() -> None:
    stats = BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"])._calculate_stats([float(i) for i in range(1, 21)])
    assert stats["p95"] == 19.0 and stats["p99"] == 20.0 and stats["p50"] == 10.0 and stats["max"] == 20.0 and stats["min"] == 1.0


def test_empty_samples_still_return_zeroes() -> None:
    assert BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"])._calculate_stats([])["p95"] == 0.0


def test_a_record_failure_never_fails_the_benchmark(monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise RuntimeError("no git")

    monkeypatch.setattr("src.perf.bench_harness.collect_identity", boom)
    harness = BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"])
    result = harness.run_benchmark("RECORD_BOOM", build_movement_state(entity_count=20), warmup_ticks=1, sample_ticks=3)
    assert set(result) == LEGACY_KEYS and harness.last_record is None


def test_stats_cover_every_sampled_tick_not_just_the_last_hundred() -> None:
    """RuntimeStatus keeps only 100 tick signals; a 150-tick run must still report 150 ticks (DEV-021)."""
    harness = BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"])
    result = harness.run_benchmark("WINDOW_UNIT", build_movement_state(entity_count=10), warmup_ticks=1, sample_ticks=150)
    samples = harness.last_record.result.samples
    assert len(samples.tick_wall_ms) == len(samples.tick_compute_ms) == 150
    assert result["tick_ms"]["max"] == pytest.approx(max(samples.tick_compute_ms), abs=1e-3)
    total_ms = sum(samples.tick_compute_ms)
    assert result["compute_tps"] == pytest.approx(150 * 1000.0 / total_ms, rel=0.02)  # was 150 * 1000 / (sum of only the last 100)
