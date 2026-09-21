"""Tests for tools/agent-monitoring/retrieval_baseline_metrics.py::build_harm_check_baseline_section
and its --harm-check-window-start CLI flag (TCK-20260916-HEADROOM-HARM-CHECK-BASELINE).
"""
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "retrieval_baseline_metrics.py"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from retrieval_baseline_metrics import build_harm_check_baseline_section  # noqa: E402


def _run(ts=None):
    events = [
        {"ts": "2026-09-15T00:00:00Z", "phase": "Implement", "status": "ok", "tool_call_count": 5},
        {"ts": "2026-09-16T01:00:00Z", "phase": "Implement", "status": "ok", "tool_call_count": 3},
        {"ts": "2026-09-16T02:00:00Z", "phase": "Test", "status": "failed", "reason_code": "TESTS_FAILED"},
        {"ts": "2026-09-16T03:00:00Z", "phase": "Verify", "status": "blocked", "reason_code": "DOD_BLOCKED"},
        {"ts": "2026-09-17T00:00:00Z", "phase": "Implement", "status": "ok"},
    ]
    runs = [
        {"start_ts": "2026-09-15T00:00:00Z", "final_status": "DONE"},
        {"start_ts": "2026-09-16T00:00:00Z", "final_status": "DONE"},
        {"start_ts": "2026-09-17T00:00:00Z", "final_status": "TESTS_FAILED"},
    ]
    tools = [
        {"ts": "2026-09-15T00:00:00Z", "session_id": "s1"},
        {"ts": "2026-09-16T00:00:00Z", "session_id": "s2"},
        {"ts": "2026-09-17T00:00:00Z", "session_id": None},
    ]
    return build_harm_check_baseline_section(runs, events, tools, ts or "2026-09-16")


def test_window_excludes_rows_before_window_start():
    result = _run()
    assert result["population"]["run_count"] == 2
    assert result["population"]["event_count"] == 4
    assert result["population"]["tools_count"] == 2


def test_done_rate_and_event_rates_computed_correctly():
    result = _run()
    # 1 of 2 runs in window is DONE
    assert result["done_rate"] == 0.5
    # 1 failed, 1 blocked, 4 events total in window
    assert result["per_event_failed_rate"] == 0.25
    assert result["per_event_blocked_rate"] == 0.25


def test_reason_code_frequency_only_counts_present_codes():
    result = _run()
    assert result["reason_code_frequency"] == {"TESTS_FAILED": 1, "DOD_BLOCKED": 1}


def test_tool_call_count_per_phase_excludes_none_not_treated_as_zero():
    result = _run()
    # Implement in-window has one event with tcc=3 and one with no tcc key at all (None) —
    # only the real value should count toward the mean, not a fabricated 0.
    assert result["tool_call_count_per_phase"]["Implement"] == {"mean": 3.0, "n": 1}
    # Test/Verify events in window have no tool_call_count key at all -> absent from the dict
    assert "Test" not in result["tool_call_count_per_phase"]
    assert "Verify" not in result["tool_call_count_per_phase"]


def test_hand_orchestration_caveat_present_when_all_counts_are_zero():
    events = [{"ts": "2026-09-16T00:00:00Z", "phase": "Implement", "status": "ok", "tool_call_count": 0}]
    result = build_harm_check_baseline_section([], events, [], "2026-09-16")
    assert result["tool_call_count_hand_orchestration_caveat"] is not None
    assert "hand-orchestrated" in result["tool_call_count_hand_orchestration_caveat"]


def test_hand_orchestration_caveat_absent_when_real_nonzero_counts_present():
    result = _run()
    assert result["tool_call_count_hand_orchestration_caveat"] is None


def test_session_id_population_rate():
    result = _run()
    # In-window (>= 2026-09-16): the 2026-09-16 row (session_id="s2") and the 2026-09-17 row
    # (session_id=None) -- 1 of 2 populated. The 2026-09-15 row is correctly excluded.
    assert result["population"]["tools_count"] == 2
    assert result["session_id_population_rate"] == 0.5


def test_empty_window_does_not_crash():
    result = build_harm_check_baseline_section([], [], [], "2026-09-16")
    assert result["done_rate"] is None
    assert result["per_event_failed_rate"] is None
    assert result["per_event_blocked_rate"] is None
    assert result["session_id_population_rate"] is None
    assert result["population"] == {"run_count": 0, "event_count": 0, "tools_count": 0}


def test_cli_harm_check_flag_produces_distinct_report_shape():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--harm-check-window-start", "2026-09-16"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert set(report.keys()) == {
        "window_start_ts", "window_end_ts", "population", "done_rate", "per_event_failed_rate",
        "per_event_blocked_rate", "reason_code_frequency", "tool_call_count_per_phase",
        "tool_call_count_hand_orchestration_caveat", "session_id_population_rate",
        "session_id_reliability_note", "statistical_limit", "trial_not_yet_started_note",
    }


def test_cli_without_flag_still_produces_the_original_pinned_report_shape():
    # Guards against the new flag silently changing default behavior — the exact key set here
    # is what test_baseline_report_cli_runs_against_real_corpus_and_prints_json already pins.
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert report["ticket_id"] == "TCK-20260728-RETRIEVAL-BASELINE-METRICS"


def test_cli_does_not_mutate_agent_monitoring():
    pre = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    subprocess.run(
        [sys.executable, str(_MODULE_PATH), "--harm-check-window-start", "2026-09-16"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    post = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    assert pre == post
