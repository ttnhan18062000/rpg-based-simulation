"""LongRunStabilityHarness reports an outcome, not passed_certification, and maps into a capacity_run record (TCK-20261010-PERF-M2-T04-CAPACITY-RUN)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.perf.benchmark_record import BenchmarkRecord, GateTier, HashScheme, OutcomeState, PercentileMethod, nearest_rank
from src.perf.long_run_harness import LongRunStabilityHarness, LongRunStabilityReport, RunMode, _stability_outcome, _window_percentiles

PROFILE = RuntimeProfile(
    name="long_run_unit",
    hardware_class=HardwareClass.CLASS_B,
    max_ram_mb=512,
    max_cpu_percent=80.0,
    max_worker_count=0,
    max_queue_depth=500,
    max_replay_buffer_kb=4096,
    max_observability_budget_percent=10.0,
    max_tick_budget_ms=50.0,
)


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    samples = tmp_path_factory.mktemp("samples")
    harness = LongRunStabilityHarness(PROFILE)
    report = harness.execute_run("movement", total_ticks=40, entity_count=20, warmup_ticks=5, sample_interval=10, mode=RunMode.PURE, seed=7)
    return harness, report, harness.to_record(report, samples_dir=samples), samples


def test_the_report_has_an_outcome_and_no_passed_certification(run) -> None:
    _, report, _, _ = run
    assert not hasattr(report, "passed_certification")
    assert report.outcome.state in (OutcomeState.PASS, OutcomeState.REGRESSION)
    assert "passed_certification" not in report.to_dict()["certifications"]
    assert report.to_dict()["certifications"]["outcome"]["state"] == report.outcome.state.value


def test_the_report_keeps_warmup_ticks_samples_and_the_active_mode_per_sample(run) -> None:
    _, report, _, _ = run
    data = report.to_dict()
    assert data["warmup_ticks"] == 5 and data["sample_interval_ticks"] == 10
    assert len(data["samples"]) == len(report.samples) == 4
    assert all("active_mode" in sample for sample in data["samples"])
    assert len(report.tick_wall_ms) == len(report.mode_per_tick) == 40


def test_the_record_is_a_capacity_run_on_an_uncontrolled_runner(run) -> None:
    _, report, record, _ = run
    assert record.identity.gate.tier is GateTier.CAPACITY_RUN and record.identity.gate.projection == "long_run_stability"
    assert record.identity.runner.controlled is False
    assert record.result.protocol.percentile_method is PercentileMethod.NEAREST_RANK
    assert record.result.protocol.warmup_ticks == 5 and record.result.protocol.measured_ticks == 40
    assert record.identity.rng.seed == 7 and record.identity.workload.entity_count == 20
    assert record.result.outcome == report.outcome
    assert record.result.validity.final_state_hash == report.final_state_hash
    assert record.result.validity.hash_scheme is HashScheme.FLAT_SHA256_V2
    assert record.result.memory_mb["rss_high_water"] >= 0 and record.result.memory_mb["sample_every_ticks"] == 10
    assert BenchmarkRecord.from_dict(json.loads(json.dumps(record.to_dict()))) == record


def test_the_samples_are_a_pointer_whose_sha256_matches_its_file(run) -> None:
    _, report, record, samples_dir = run
    pointer = record.result.samples
    assert pointer.tick_wall_ms is None and Path(pointer.uri).parent == samples_dir
    payload = Path(pointer.uri).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == pointer.sha256
    assert json.loads(payload)["tick_wall_ms"] == list(report.tick_wall_ms)


def test_percentiles_are_nearest_rank_over_the_window() -> None:
    window = [float(i) for i in range(1, 21)]
    assert _window_percentiles(window) == (10.0, 19.0, 20.0)  # int(n * q) would give 11, 20, 20
    assert _window_percentiles([]) == (0.0, 0.0, 0.0)
    assert nearest_rank(sorted(window), 0.95) == 19.0


def test_the_stability_outcome_names_every_violated_invariant() -> None:
    held = {"rss_bounded": True, "latency_stable": True, "caches_bounded": True, "gc_stable": True}
    assert _stability_outcome(held).state is OutcomeState.PASS
    bad = _stability_outcome({**held, "rss_bounded": False, "gc_stable": False})
    assert bad.state is OutcomeState.REGRESSION and "rss_bounded" in bad.reason and "gc_stable" in bad.reason


def test_two_records_written_in_the_same_second_point_to_different_files(run) -> None:
    harness, report, first, samples_dir = run
    second = harness.to_record(report, samples_dir=samples_dir)
    assert first.result.samples.uri != second.result.samples.uri
    for record in (first, second):
        assert hashlib.sha256(Path(record.result.samples.uri).read_bytes()).hexdigest() == record.result.samples.sha256


def test_the_report_type_still_carries_the_certification_flags() -> None:
    assert {"rss_bounded", "latency_stable", "caches_bounded", "gc_stable"} <= set(LongRunStabilityReport.__dataclass_fields__)
