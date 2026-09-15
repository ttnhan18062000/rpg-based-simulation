"""Tests for tools/gate_checks/monitoring_anomaly_validator.py
(TCK-20260915-MONITORING-ANOMALY-VALIDATOR, child of TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC).
"""
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_GATE_CHECKS_DIR = _TOOLS_DIR / "gate_checks"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from monitoring_anomaly_validator import (  # noqa: E402
    AGENT_DRIFT_CEILING,
    TIER_DRIFT_CEILING,
    check_monitoring_anomalies,
    check_ts_shape_and_unknown_week,
    check_vocabulary_drift,
)


# ---------------------------------------------------------------------------
# check_vocabulary_drift
# ---------------------------------------------------------------------------

def _event(run_id, agent=None, phase="Scope", ts=None):
    return {"run_id": run_id, "agent": agent, "phase": phase, "ts": ts}


def test_vocabulary_drift_passes_when_no_non_canonical_literals():
    runs = [{"run_id": "TCK-A", "tier": "hotfix"}]
    events = [_event("TCK-A", agent="ticket-scoper", phase="Scope")]
    results = check_vocabulary_drift(runs, events)
    assert all(r["status"] == "PASS" for r in results)


def test_vocabulary_drift_registered_orchestrator_literal_not_flagged():
    # "orchestrator" was registered in vocabulary.py by this ticket -- must never count as drift.
    runs = [{"run_id": "TCK-A", "tier": "hotfix"}]
    events = [_event("TCK-A", agent="orchestrator", phase="Scope")]
    results = check_vocabulary_drift(runs, events)
    assert all(r["status"] == "PASS" for r in results)


def test_vocabulary_drift_agent_condition_fails_when_exceeded():
    # 3 unknown literals will only exceed the real ceiling if it's below 3 -- exercise via a
    # synthetic ceiling override by monkeypatching the module constant, for determinism.
    runs = [{"run_id": "TCK-A", "tier": "hotfix"}]
    events = [_event("TCK-A", agent=f"totally-unknown-agent-{i}", phase="Scope") for i in range(3)]
    import monitoring_anomaly_validator as mod
    old_ceiling = mod.AGENT_DRIFT_CEILING
    try:
        mod.AGENT_DRIFT_CEILING = 1
        results = mod.check_vocabulary_drift(runs, events)
    finally:
        mod.AGENT_DRIFT_CEILING = old_ceiling
    assert results[0]["status"] == "FAIL"
    assert "non-canonical agent literals" in results[0]["evidence"]


def test_vocabulary_drift_tier_condition_fails_when_exceeded():
    import monitoring_anomaly_validator as mod
    runs = [{"run_id": "TCK-A", "tier": "weird-tier"}]
    events = []
    old_ceiling = mod.TIER_DRIFT_CEILING
    try:
        mod.TIER_DRIFT_CEILING = 0
        results = mod.check_vocabulary_drift(runs, events)
    finally:
        mod.TIER_DRIFT_CEILING = old_ceiling
    assert results[1]["status"] == "FAIL"
    assert "non-canonical tier literals" in results[1]["evidence"]


def test_ceilings_may_only_decrease_never_used_to_paper_over_a_regression():
    assert AGENT_DRIFT_CEILING == 162, (
        "AGENT_DRIFT_CEILING changed -- if this is because legitimate patterns were registered in "
        "vocabulary.py, lower this value to match (never raise it to paper over new real drift)"
    )
    assert TIER_DRIFT_CEILING == 2


# ---------------------------------------------------------------------------
# check_ts_shape_and_unknown_week
# ---------------------------------------------------------------------------

def test_ts_shape_check_passes_on_clean_data(tmp_path):
    runs = [{"run_id": "TCK-A", "start_ts": "2026-07-01T00:00:00Z"}]
    events = [_event("TCK-A", agent="ticket-scoper", ts="2026-07-01T00:00:00Z")]
    results = check_ts_shape_and_unknown_week(runs, events, data_dir=tmp_path)
    assert all(r["status"] == "PASS" for r in results)


def test_ts_shape_check_detects_planted_bad_record(tmp_path):
    # Deliberately-planted bad record (AC #4): a run with start_ts=None must make this check fail
    # once the ceiling is monkeypatched to 0, proving detection works, not just clean reporting.
    import monitoring_anomaly_validator as mod
    runs = [{"run_id": "TCK-BAD", "start_ts": None}]
    events = []
    old_ceiling = mod.UNUSABLE_TS_RUN_CEILING
    try:
        mod.UNUSABLE_TS_RUN_CEILING = 0
        results = mod.check_ts_shape_and_unknown_week(runs, events, data_dir=tmp_path)
    finally:
        mod.UNUSABLE_TS_RUN_CEILING = old_ceiling
    assert results[0]["status"] == "FAIL"
    assert "unusable ts" in results[0]["evidence"]


# ---------------------------------------------------------------------------
# check_monitoring_anomalies (aggregate)
# ---------------------------------------------------------------------------

def test_aggregate_tags_each_result_with_its_source_check():
    results = check_monitoring_anomalies(
        runs=[{"run_id": "TCK-A", "start_ts": "2026-07-01T00:00:00Z", "tier": "hotfix"}],
        events=[_event("TCK-A", agent="ticket-scoper", ts="2026-07-01T00:00:00Z")],
        tools=[],
    )
    check_names = {r["check"] for r in results}
    assert check_names == {
        "duplicate_run_records", "event_seq_integrity", "tool_call_count_mismatch",
        "ts_shape_and_unknown_week", "vocabulary_drift",
    }


def test_aggregate_all_pass_on_clean_synthetic_corpus():
    results = check_monitoring_anomalies(
        runs=[{"run_id": "TCK-A", "start_ts": "2026-07-01T00:00:00Z", "tier": "hotfix"}],
        events=[_event("TCK-A", agent="ticket-scoper", ts="2026-07-01T00:00:00Z")],
        tools=[],
    )
    assert all(r["status"] == "PASS" for r in results)


def test_real_corpus_is_at_or_below_every_ratchet_ceiling():
    results = check_monitoring_anomalies()
    for r in results:
        assert r["status"] == "PASS", f"real corpus exceeded a ratchet ceiling: {r}"


# ---------------------------------------------------------------------------
# Wiring: Makefile target, and CLI presence-of-output (not merely a return code)
# ---------------------------------------------------------------------------

def test_makefile_wires_monitoring_anomaly_validate():
    makefile_text = (_REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "monitoring-anomaly-validate:" in makefile_text
    assert "monitoring_anomaly_validator.py" in makefile_text
    assert "monitoring-anomaly-validate" in makefile_text.splitlines()[0], (
        ".PHONY line must declare the new target"
    )


def test_cli_prints_marker_output_not_merely_a_return_code():
    # AC #3: the failure mode this whole arc keeps hitting is silence -- assert real stdout
    # content, not just a subprocess return code.
    result = subprocess.run(
        [sys.executable, str(_GATE_CHECKS_DIR / "monitoring_anomaly_validator.py")],
        cwd=str(_REPO_ROOT), capture_output=True, text=True,
    )
    assert "MARKER:" in result.stdout
    assert '"check":' in result.stdout
    assert '"status":' in result.stdout
    assert result.returncode == 0, (
        f"real corpus should pass every ratchet; got exit {result.returncode}:\n{result.stdout}"
    )
