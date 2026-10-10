"""BenchmarkRecord (schema 1.0) and compare() (TCK-20261010-PERF-M2-T02B-RECORD)."""
from __future__ import annotations

import dataclasses
import json
from typing import Any, Dict

import pytest

from src.config.profiles import SignalContract
from src.perf.benchmark_record import (
    COST_ACCOUNTING_VERSION,
    MAX_EMBEDDED_SAMPLES,
    SCHEMA_VERSION,
    UNKNOWN,
    BenchmarkRecord,
    BenchmarkRecordError,
    Contract,
    GateTier,
    HashScheme,
    ModeRun,
    Outcome,
    OutcomeState,
    PercentileMethod,
    Protocol,
    Result,
    RunSubject,
    Samples,
    Thresholds,
    Validity,
    collect_identity,
    collect_runtime,
    compare,
    compress_modes,
    nearest_rank,
    write_samples_file,
)
from src.perf.profiles import PERF_PROFILES

NORMAL = (ModeRun("NORMAL", 20),)


def make_record(*, avg: float = 10.0, signal: SignalContract = SignalContract.LIVE, modes=NORMAL, seed: int = 42, **result_overrides: Any) -> BenchmarkRecord:
    profile = PERF_PROFILES["PERF_512MB_LOCAL"].model_copy(update={"signal_contract": signal})
    identity = collect_identity(
        profile,
        RunSubject(scenario_id="unit", entity_count=20, seed=seed, flags={"no_replay": True, "no_frame_pacing": True}, warmup_ticks=5),
    )
    result = Result(
        protocol=Protocol(warmup_ticks=5, measured_ticks=20, percentile_method=PercentileMethod.NEAREST_RANK),
        latency_ms={"avg": avg, "p50": avg, "p95": avg * 1.5, "p99": avg * 2, "max": avg * 2, "min": avg / 2},
        throughput={"compute_tps": 100.0, "wall_tps": 90.0},
        time_s={"wall": 1.0, "cpu_user": 0.9, "cpu_system": 0.1},
        memory_mb={"rss_high_water": 100.0, "rss_delta": 1.0, "sample_every_ticks": 10},
        runtime_mode_sequence=modes,
        outcome=Outcome(OutcomeState.NOT_APPLICABLE, "unit"),
        recorded_at="2026-10-10T00:00:00+00:00",
        samples=Samples(tick_wall_ms=(1.0, 2.0), tick_compute_ms=(1.0, 2.0)),
    )
    return BenchmarkRecord(identity=identity, result=dataclasses.replace(result, **result_overrides))


def replace_identity(record: BenchmarkRecord, section: str, **changes: Any) -> BenchmarkRecord:
    """A copy of ``record`` with one identity section's fields changed."""
    new_section = dataclasses.replace(getattr(record.identity, section), **changes)
    return dataclasses.replace(record, identity=dataclasses.replace(record.identity, **{section: new_section}))


# ── record shape ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_record_is_frozen_and_versioned() -> None:
    record = make_record()
    assert record.schema_version == SCHEMA_VERSION == "1.1"
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.schema_version = "2.0"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.identity.rng.seed = 1  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.result.outcome.state = OutcomeState.PASS  # type: ignore[misc]


def test_round_trip_through_json_gives_an_equal_record() -> None:
    record = make_record(validity=Validity(replay_ok=True, final_state_hash="ab", hash_scheme=HashScheme.FLAT_SHA256_V2))
    wire = json.loads(json.dumps(record.to_dict()))
    assert BenchmarkRecord.from_dict(wire) == record


def test_blocking_contract_fields_are_present() -> None:
    wire = make_record().to_dict()
    assert wire["identity"]["contract"]["signal_contract"] == "live"
    assert wire["identity"]["contract"]["work_model_version"].startswith("WORK_MODEL_V")
    assert wire["result"]["cost_accounting_version"] == COST_ACCOUNTING_VERSION == "DEV-017"


@pytest.mark.parametrize("bad", ["flat-sha256-v3", "sha256", "", "FLAT-SHA256-V2"])
def test_hash_scheme_rejects_anything_but_the_two_schemes(bad: str) -> None:
    with pytest.raises(BenchmarkRecordError):
        Validity(final_state_hash="ab", hash_scheme=bad)  # type: ignore[arg-type]


def test_hash_scheme_accepts_both_schemes_and_a_hash_needs_one() -> None:
    assert Validity(final_state_hash="ab", hash_scheme="flat-sha256-v1").hash_scheme is HashScheme.FLAT_SHA256_V1
    assert Validity(final_state_hash="ab", hash_scheme="flat-sha256-v2").hash_scheme is HashScheme.FLAT_SHA256_V2
    with pytest.raises(BenchmarkRecordError):
        Validity(final_state_hash="ab")


def test_from_dict_names_the_missing_required_field() -> None:
    wire = make_record().to_dict()
    del wire["identity"]["rng"]["seed"]
    with pytest.raises(BenchmarkRecordError, match="seed"):
        BenchmarkRecord.from_dict(wire)


def test_samples_are_embedded_or_a_pointer_never_both() -> None:
    with pytest.raises(BenchmarkRecordError):
        Samples()
    with pytest.raises(BenchmarkRecordError):
        Samples(tick_wall_ms=(1.0,), tick_compute_ms=(1.0,), uri="x", sha256="y")
    with pytest.raises(BenchmarkRecordError):
        Samples(tick_wall_ms=(1.0,))


def test_samples_pointer_hashes_the_written_file(tmp_path) -> None:
    samples = write_samples_file(tmp_path, "run", [1.0, 2.0], [0.5, 1.5])
    assert samples.uri and samples.sha256 and samples.tick_wall_ms is None
    import hashlib
    from pathlib import Path

    assert hashlib.sha256(Path(samples.uri).read_bytes()).hexdigest() == samples.sha256


def test_tripwire_record_embeds_raw_samples_within_the_cap() -> None:
    assert MAX_EMBEDDED_SAMPLES >= 100
    record = make_record()
    assert record.result.samples is not None and record.result.samples.tick_wall_ms == (1.0, 2.0)


# ── identity collector ────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_collector_uses_the_documented_unknown_sentinel_for_unavailable_fields() -> None:
    identity = make_record().identity
    assert UNKNOWN == "unknown"
    assert identity.content.content_hash == UNKNOWN
    assert identity.scenario.builder_version == UNKNOWN
    assert identity.runtime.det_port_tier == UNKNOWN
    assert identity.contract.verification_level == UNKNOWN
    assert identity.observer.level == "bare"
    assert identity.runtime.build_flavor in {"gil", "free-threaded"}
    assert identity.executor.backend == "sequential" and identity.executor.worker_count == 0


def test_collector_detects_the_hardware_class(monkeypatch) -> None:
    from src.certification.models import HardwareClass

    monkeypatch.setattr("src.perf.benchmark_record.HardwareClassifier.detect_class", staticmethod(lambda: HardwareClass.CLASS_C))
    assert collect_runtime().hardware_class == "class_c"


# ── percentiles (OD-1) ────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_nearest_rank_of_one_to_twenty() -> None:
    values = [float(i) for i in range(1, 21)]
    assert nearest_rank(values, 0.95) == 19.0  # not 20: the old int(n * q) made p95 the maximum
    assert nearest_rank(values, 0.99) == 20.0
    assert nearest_rank(values, 0.5) == 10.0


@pytest.mark.parametrize("n", [1, 2, 3, 7, 50, 100, 1000])
def test_nearest_rank_is_bounded_and_monotone(n: int) -> None:
    values = [float(i) for i in range(n)]
    p50, p95, p99 = (nearest_rank(values, q) for q in (0.5, 0.95, 0.99))
    assert values[0] <= p50 <= p95 <= p99 <= values[-1]


def test_nearest_rank_is_immune_to_float_noise() -> None:
    values = [float(i) for i in range(1, 101)]
    assert nearest_rank(values, 0.07) == 7.0  # 0.07 * 100 == 7.000000000000001


def test_compress_modes_is_run_length() -> None:
    assert compress_modes(["NORMAL", "NORMAL", "DEGRADED", "NORMAL"]) == (ModeRun("NORMAL", 2), ModeRun("DEGRADED", 1), ModeRun("NORMAL", 1))


# ── compare() ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_identical_identity_within_threshold_passes() -> None:
    outcome = compare(make_record(avg=10.0), make_record(avg=11.0))
    assert outcome.state is OutcomeState.PASS


def test_pass_lists_the_unverified_identity_fields() -> None:
    outcome = compare(make_record(), make_record())
    assert outcome.state is OutcomeState.PASS and "identity.content.content_hash" in outcome.reason


def test_latency_over_the_threshold_is_a_regression() -> None:
    outcome = compare(make_record(avg=100.0), make_record(avg=140.0))  # limit = max(5, 125)
    assert outcome.state is OutcomeState.REGRESSION


def test_absolute_floor_protects_tiny_benchmarks() -> None:
    assert compare(make_record(avg=1.0), make_record(avg=4.0)).state is OutcomeState.PASS  # limit = max(5, 1.25)
    assert compare(make_record(avg=1.0), make_record(avg=5.5)).state is OutcomeState.REGRESSION


def test_thresholds_are_configurable() -> None:
    strict = Thresholds(relative=0.05, absolute_ms=0.0)
    assert compare(make_record(avg=10.0), make_record(avg=11.0), strict).state is OutcomeState.REGRESSION


def test_missing_base_is_inconclusive_never_pass() -> None:
    outcome = compare(None, make_record())
    assert outcome.state is OutcomeState.INCONCLUSIVE and "baseline" in outcome.reason


def test_major_schema_mismatch_is_inconclusive() -> None:
    old = dataclasses.replace(make_record(), schema_version="0.9")
    outcome = compare(old, make_record())
    assert outcome.state is OutcomeState.INCONCLUSIVE and "MAJOR" in outcome.reason


def test_minor_schema_difference_is_still_comparable() -> None:
    newer = dataclasses.replace(make_record(), schema_version="1.7")
    assert compare(make_record(), newer).state is OutcomeState.PASS


@pytest.mark.parametrize("side", ["base", "head"])
def test_missing_cost_accounting_version_is_inconclusive(side: str) -> None:
    bare = make_record(cost_accounting_version=None)
    base, head = (bare, make_record()) if side == "base" else (make_record(), bare)
    outcome = compare(base, head)
    assert outcome.state is OutcomeState.INCONCLUSIVE and "cost_accounting_version" in outcome.reason and side in outcome.reason


def test_a_different_cost_accounting_version_is_inconclusive() -> None:
    outcome = compare(make_record(cost_accounting_version="DEV-016"), make_record())
    assert outcome.state is OutcomeState.INCONCLUSIVE and "cost_accounting_version" in outcome.reason


@pytest.mark.parametrize(
    "section, change, field",
    [
        ("rng", {"seed": 7}, "identity.rng.seed"),
        ("config", {"profile_hash": "0" * 64}, "identity.config.profile_hash"),
        ("runtime", {"hardware_class": "class_c", "declared_hardware_class": "class_c"}, "identity.runtime.hardware_class"),
        ("contract", {"work_model_version": "WORK_MODEL_V2"}, "identity.contract.work_model_version"),
        ("contract", {"signal_contract": SignalContract.CANONICAL}, "identity.contract.signal_contract"),
        ("workload", {"entity_count": 21}, "identity.workload.entity_count"),
        ("runtime", {"cpu_model": "other cpu"}, "identity.runtime.cpu_model"),
        ("executor", {"worker_count": 4}, "identity.executor.worker_count"),
        ("gate", {"tier": GateTier.CAPACITY_RUN}, "identity.gate.tier"),
        ("observer", {"level": "replay"}, "identity.observer.level"),
    ],
)
def test_a_blocking_identity_difference_is_inconclusive_and_names_the_field(section: str, change: Dict[str, Any], field: str) -> None:
    head = replace_identity(make_record(), section, **change)
    outcome = compare(make_record(), head)
    assert outcome.state is OutcomeState.INCONCLUSIVE and field in outcome.reason


def test_a_different_percentile_method_is_inconclusive() -> None:
    linear = make_record()
    linear = dataclasses.replace(
        linear, result=dataclasses.replace(linear.result, protocol=dataclasses.replace(linear.result.protocol, percentile_method=PercentileMethod.LINEAR))
    )
    outcome = compare(make_record(), linear)
    assert outcome.state is OutcomeState.INCONCLUSIVE and "percentile_method" in outcome.reason


def test_unknown_against_a_known_value_is_a_mismatch() -> None:
    head = replace_identity(make_record(), "content", content_hash="deadbeef")
    outcome = compare(make_record(), head)
    assert outcome.state is OutcomeState.INCONCLUSIVE and "identity.content.content_hash" in outcome.reason


def test_python_patch_version_is_recorded_only() -> None:
    base = replace_identity(make_record(), "runtime", python_version="3.12.1")
    head = replace_identity(make_record(), "runtime", python_version="3.12.9")
    assert compare(base, head).state is OutcomeState.PASS
    other_minor = replace_identity(make_record(), "runtime", python_version="3.13.0")
    assert compare(base, other_minor).state is OutcomeState.INCONCLUSIVE


def test_engine_commit_and_dirty_flag_are_recorded_only() -> None:
    head = replace_identity(make_record(), "engine", commit="f" * 40, dirty_src=True)
    assert compare(make_record(), head).state is OutcomeState.PASS


def test_a_declared_hardware_class_that_is_not_the_detected_one_is_inconclusive() -> None:
    declared = replace_identity(make_record(), "runtime", declared_hardware_class="class_a", hardware_class="class_b")
    outcome = compare(make_record(), declared)
    assert outcome.state is OutcomeState.INCONCLUSIVE and "declared_hardware_class" in outcome.reason


def test_digests_of_different_schemes_are_not_comparable_but_only_when_both_carry_one() -> None:
    v1 = make_record(validity=Validity(final_state_hash="aa", hash_scheme=HashScheme.FLAT_SHA256_V1))
    v2 = make_record(validity=Validity(final_state_hash="bb", hash_scheme=HashScheme.FLAT_SHA256_V2))
    assert compare(v1, v2).state is OutcomeState.INCONCLUSIVE
    assert "hash_scheme" in compare(v1, v2).reason
    assert compare(v1, make_record()).state is OutcomeState.PASS  # head carries no hash: nothing to compare


def test_head_excursion_is_a_regression_under_the_canonical_contract() -> None:
    excursion = (ModeRun("NORMAL", 10), ModeRun("DEGRADED", 10))
    base = make_record(signal=SignalContract.CANONICAL)
    head = make_record(signal=SignalContract.CANONICAL, modes=excursion)
    outcome = compare(base, head)
    assert outcome.state is OutcomeState.REGRESSION and "DEGRADED" in outcome.reason


def test_head_excursion_is_inconclusive_under_the_live_contract() -> None:
    excursion = (ModeRun("NORMAL", 10), ModeRun("CONSTRAINED", 10))
    outcome = compare(make_record(), make_record(modes=excursion))
    assert outcome.state is OutcomeState.INCONCLUSIVE and "CONSTRAINED" in outcome.reason


@pytest.mark.parametrize("signal", [SignalContract.LIVE, SignalContract.CANONICAL])
def test_a_base_that_left_normal_or_has_no_sequence_is_inconclusive(signal: SignalContract) -> None:
    left = make_record(signal=signal, modes=(ModeRun("SURVIVAL", 20),))
    assert compare(left, make_record(signal=signal)).state is OutcomeState.INCONCLUSIVE
    assert compare(make_record(signal=signal, modes=()), make_record(signal=signal)).state is OutcomeState.INCONCLUSIVE
    assert compare(make_record(signal=signal), make_record(signal=signal, modes=())).state is OutcomeState.INCONCLUSIVE


def test_a_missing_latency_metric_is_inconclusive() -> None:
    outcome = compare(make_record(), make_record(), Thresholds(metric="p42"))
    assert outcome.state is OutcomeState.INCONCLUSIVE and "p42" in outcome.reason


def test_compare_ignores_perf_only_result_fields() -> None:
    """compare() may be reused by the RPG gate report: throughput, memory, phases, samples, work and outcome cannot change its answer."""
    plain = make_record(avg=10.0)
    noisy = make_record(
        avg=10.0,
        throughput={"compute_tps": 1.0},
        memory_mb={},
        time_s={},
        phases={"x": {"p95": 1e9}},
        work={"anything": 1e9},
        samples=Samples(uri="u", sha256="s"),
        scaling_slope={"k": 1.0},
        outcome=Outcome(OutcomeState.REGRESSION, "stale"),
        recorded_at="1999-01-01T00:00:00+00:00",
    )
    stripped = make_record(avg=10.0, samples=None, phases=None, work={})
    assert compare(plain, noisy) == compare(plain, stripped) == compare(plain, plain)
    assert compare(plain, noisy).state is OutcomeState.PASS
    regressed = make_record(avg=100.0, throughput={}, phases={"x": {"p95": 0.0}})
    assert compare(plain, regressed) == compare(plain, make_record(avg=100.0))


def test_compare_does_not_mutate_its_inputs() -> None:
    base, head = make_record(), make_record(avg=11.0)
    before = (base.to_dict(), head.to_dict())
    compare(base, head)
    assert (base.to_dict(), head.to_dict()) == before
