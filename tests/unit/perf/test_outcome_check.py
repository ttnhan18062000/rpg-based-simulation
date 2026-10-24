"""``Outcome.check`` names the ``compare()`` check that decided an outcome, and known-debt matching uses it instead of the reason text.

TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE: a ledger entry's ``expected_signature`` is ``<STATE>:<check>``. Before this field, no code could
match a real outcome against it without parsing ``Outcome.reason``.
"""
from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from src.config.profiles import SignalContract
from src.perf.benchmark_record import (
    CHECK_NAMES,
    BenchmarkRecord,
    BenchmarkRecordError,
    HashScheme,
    ModeRun,
    Outcome,
    OutcomeState,
    Thresholds,
    Validity,
    compare,
)
from tests.unit.perf.test_benchmark_record import make_record, replace_identity
from tools.perf import known_debt as kd

REPO_ROOT = Path(__file__).resolve().parents[3]


def _outcome_for(check: str) -> Outcome:
    """A real ``compare()`` outcome decided by ``check``."""
    if check == "schema":
        return compare(dataclasses.replace(make_record(), schema_version="0.9"), make_record())
    if check == "each_side":
        return compare(make_record(cost_accounting_version=None), make_record())
    if check == "blocking_fields":
        return compare(make_record(), replace_identity(make_record(), "rng", seed=7))
    if check == "hash_scheme":
        v1 = make_record(validity=Validity(final_state_hash="aa", hash_scheme=HashScheme.FLAT_SHA256_V1))
        v2 = make_record(validity=Validity(final_state_hash="bb", hash_scheme=HashScheme.FLAT_SHA256_V2))
        return compare(v1, v2)
    if check == "mode_sequences":
        excursion = (ModeRun("NORMAL", 10), ModeRun("DEGRADED", 10))
        return compare(make_record(signal=SignalContract.CANONICAL), make_record(signal=SignalContract.CANONICAL, modes=excursion))
    if check == "latency":
        return compare(make_record(avg=10.0), make_record(avg=500.0))
    raise AssertionError(check)


@pytest.mark.parametrize("check", CHECK_NAMES)
def test_every_non_pass_compare_outcome_carries_the_check_that_decided_it(check: str) -> None:
    outcome = _outcome_for(check)
    assert outcome.state is not OutcomeState.PASS, f"the {check} scenario did not fail"
    assert outcome.check == check


def test_a_pass_has_no_check() -> None:
    outcome = compare(make_record(), make_record())
    assert outcome.state is OutcomeState.PASS and outcome.check is None


def test_a_missing_record_has_no_check() -> None:
    assert compare(None, make_record()).check is None
    assert compare(make_record(), None).check is None


def test_the_missing_latency_metric_is_the_latency_check() -> None:
    assert compare(make_record(), make_record(), Thresholds(metric="p42")).check == "latency"


def test_an_unknown_check_name_is_refused() -> None:
    with pytest.raises(BenchmarkRecordError, match="check"):
        Outcome(OutcomeState.REGRESSION, "r", "not_a_check")


def test_check_survives_a_serialization_round_trip_and_an_old_record_without_it_still_loads() -> None:
    record = make_record(outcome=Outcome(OutcomeState.REGRESSION, "slow", "latency"))
    restored = BenchmarkRecord.from_dict(record.to_dict())
    assert restored.result.outcome.check == "latency"
    old = record.to_dict()
    del old["result"]["outcome"]["check"]
    assert BenchmarkRecord.from_dict(old).result.outcome.check is None


# ── known-debt matching on state + check ──────────────────────────────────────────────────────────────────────────────────────────


def _entry(**fields: str) -> dict:
    return {"match": "mixed_*", "ticket": "TCK-X", "owner": "o", "added_on": "2026-10-01", "expires_on": "2026-12-01", "kind": "broken", **fields}


def test_an_entry_matches_the_state_and_check_of_a_real_outcome() -> None:
    outcome = _outcome_for("latency")
    assert kd.signature_for(outcome) == "REGRESSION:latency"
    assert kd.entry_matches_outcome(_entry(expected_signature="REGRESSION:latency"), "mixed_200_local", outcome)


def test_a_different_check_or_state_in_the_same_lane_is_new_drift() -> None:
    entry = _entry(expected_signature="REGRESSION:latency")
    assert not kd.entry_matches_outcome(entry, "mixed_200_local", _outcome_for("mode_sequences"))
    assert not kd.entry_matches_outcome(entry, "mixed_200_local", _outcome_for("each_side"))


def test_the_scenario_must_match_the_entry_pattern() -> None:
    assert not kd.entry_matches_outcome(_entry(expected_signature="REGRESSION:latency"), "idle_100_local", _outcome_for("latency"))


def test_an_entry_without_a_signature_covers_any_non_pass_outcome_of_the_lane() -> None:
    assert kd.entry_matches_outcome(_entry(), "mixed_200_local", _outcome_for("each_side"))


def test_a_pass_is_never_covered_by_known_debt() -> None:
    passing = compare(make_record(), make_record())
    assert kd.signature_for(passing) is None
    assert not kd.entry_matches_outcome(_entry(), "mixed_200_local", passing)
    assert not kd.entry_matches_outcome(_entry(expected_signature="REGRESSION:latency"), "mixed_200_local", passing)


def test_matching_ignores_the_reason_text() -> None:
    outcome = Outcome(OutcomeState.REGRESSION, "a completely different sentence", "latency")
    assert kd.entry_matches_outcome(_entry(expected_signature="REGRESSION:latency"), "mixed_200_local", outcome)


def test_no_code_in_known_debt_reads_the_reason_of_an_outcome() -> None:
    """The module may not read ``.reason`` at all: matching on it is the parse this ticket removes."""
    tree = ast.parse((REPO_ROOT / "tools" / "perf" / "known_debt.py").read_text(encoding="utf-8"))
    reads = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "reason"]
    assert reads == []
