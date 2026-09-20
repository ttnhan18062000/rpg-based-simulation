"""Tests for tools/agent-monitoring/read_ranged_baseline.py
(TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS).
"""
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "read_ranged_baseline.py"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from read_ranged_baseline import compute_read_ranged_baseline  # noqa: E402


def test_counts_split_correctly_across_known_and_unknown():
    tools = [
        {"tool": "Read", "ts": "2026-01-01T00:00:00Z", "read_ranged": True},
        {"tool": "Read", "ts": "2026-01-02T00:00:00Z", "read_ranged": False},
        {"tool": "Read", "ts": "2026-01-03T00:00:00Z"},  # historical: field absent entirely
        {"tool": "Bash", "ts": "2026-01-04T00:00:00Z", "read_ranged": None},
        {"tool": "Edit", "ts": "2026-01-05T00:00:00Z"},
    ]
    report = compute_read_ranged_baseline(tools)
    assert report["total_tool_calls"] == 5
    assert report["total_read_calls"] == 3
    assert report["read_ranged_true_count"] == 1
    assert report["read_ranged_false_count"] == 1
    assert report["read_ranged_unknown_count"] == 1
    assert report["window_start_ts"] == "2026-01-01T00:00:00Z"
    assert report["window_end_ts"] == "2026-01-05T00:00:00Z"


def test_empty_corpus_reports_zero_counts_and_null_window():
    report = compute_read_ranged_baseline([])
    assert report["total_tool_calls"] == 0
    assert report["total_read_calls"] == 0
    assert report["window_start_ts"] is None
    assert report["window_end_ts"] is None


def test_rows_missing_ts_are_excluded_from_the_window_but_still_counted():
    tools = [
        {"tool": "Read", "read_ranged": True},  # no ts
        {"tool": "Read", "ts": "2026-02-01T00:00:00Z", "read_ranged": False},
    ]
    report = compute_read_ranged_baseline(tools)
    assert report["total_read_calls"] == 2
    assert report["window_start_ts"] == "2026-02-01T00:00:00Z"
    assert report["window_end_ts"] == "2026-02-01T00:00:00Z"


def test_cli_runs_against_real_corpus_and_prints_json():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert set(report.keys()) == {
        "window_start_ts", "window_end_ts", "total_tool_calls", "total_read_calls",
        "read_ranged_true_count", "read_ranged_false_count", "read_ranged_unknown_count", "note",
    }
    assert report["total_read_calls"] >= report["read_ranged_true_count"] + report["read_ranged_false_count"]
    assert (
        report["read_ranged_true_count"] + report["read_ranged_false_count"] + report["read_ranged_unknown_count"]
        == report["total_read_calls"]
    )


def test_cli_does_not_mutate_agent_monitoring():
    pre = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    subprocess.run(
        [sys.executable, str(_MODULE_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    post = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    assert pre == post
