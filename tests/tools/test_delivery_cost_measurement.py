"""Tests for tools/delivery/delivery_cost_measurement.py (TCK-20260924-DELIVERY-COST-MEASUREMENT).

One section per Acceptance Criterion, per staging_artifacts/TCK-20260924-DELIVERY-COST-
MEASUREMENT/test_plan.md.
"""
import inspect
import json
import subprocess
from pathlib import Path

import pytest

from tools.delivery import delivery_cost_measurement as dcm
from tools.delivery.pr_status import CommandResult


def _row(tool, input_summary=None):
    row = {"tool": tool}
    if input_summary is not None:
        row["input_summary"] = input_summary
    return row


SAMPLE_ROWS = [
    _row("Bash", "gh pr view 123"),
    _row("Bash", "gh pr view 124"),
    _row("Bash", "gh pr checks 123"),
    _row("Bash", "gh pr create --title x"),
    _row("Bash", "gh api repos/o/r/actions/runs"),
    _row("Bash", "gh run rerun 555"),
    _row("Bash", "git status"),
    _row("Bash", "git diff"),
    _row("Bash", "git commit -m x"),
    _row("Bash", "ls -la"),
    _row("mcp__knowledge-search__search_docs", None),
]


class FakeRunner:
    def __init__(self, rules):
        self.rules = rules
        self.calls = []

    def __call__(self, cmd, timeout=30):
        self.calls.append(cmd)
        for predicate, result in self.rules:
            if predicate(cmd):
                return result
        raise AssertionError(f"no rule matched {cmd!r}")


def _log_rule(subjects):
    return (lambda cmd: cmd[:2] == ["git", "log"], CommandResult(0, "\n".join(subjects) + "\n", ""))


# ---------------------------------------------------------------------------
# AC1 — one command, all figures
# ---------------------------------------------------------------------------

def test_gh_call_report_computes_calls_per_pr_and_observation_split():
    report = dcm.build_gh_call_report(SAMPLE_ROWS)
    assert report["gh_calls_total"] == 6
    assert report["gh_pr_create_count"] == 1
    assert report["gh_calls_per_pr"] == 6.0
    assert report["gh_observation_calls"] == 4  # pr view x2, pr checks, api
    assert report["gh_action_calls"] == 2  # pr create, run rerun


def test_subject_traceability_computed_over_week_range():
    runner = FakeRunner([_log_rule(["TCK-20260924-X: fix", "no ticket here", "TCK-20260924-Y: fix"])])
    result = dcm.measure_subject_traceability(run_command=runner, since_week="2026-W30", through_week="2026-W39")
    assert result["total_subjects"] == 3
    assert result["ticket_id_subjects"] == 2
    assert result["share"] == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# AC2 — ref and resolved SHA named
# ---------------------------------------------------------------------------

def test_report_names_ref_and_sha(tmp_path, monkeypatch):
    monkeypatch.setattr(dcm.bcm, "load_tools_rows_from_ref", lambda ref, source, sw, tw: (SAMPLE_ROWS, "deadbeef123"))
    runner = FakeRunner([_log_rule(["TCK-20260924-X: fix"])])
    report = dcm.build_report(ref="origin/main", run_command=runner)
    assert report["measured_ref"] == "origin/main"
    assert report["measured_sha"] == "deadbeef123"


# ---------------------------------------------------------------------------
# AC3 — no silent working-tree fallback
# ---------------------------------------------------------------------------

def test_no_ref_labels_working_tree_snapshot_unmistakably(tmp_path, monkeypatch):
    monkeypatch.setattr(dcm.bcm, "load_tools_rows", lambda data_dir, sw, tw: SAMPLE_ROWS)
    runner = FakeRunner([_log_rule(["TCK-20260924-X: fix"])])
    report = dcm.build_report(ref=None, run_command=runner)
    assert report["measured_sha"] is None
    assert "working tree" in report["measured_ref"]
    assert "may be behind origin/main" in report["measured_ref"]


# ---------------------------------------------------------------------------
# AC4 — snapshot caveat always present
# ---------------------------------------------------------------------------

def test_snapshot_caveat_present_with_and_without_ref(monkeypatch):
    monkeypatch.setattr(dcm.bcm, "load_tools_rows_from_ref", lambda ref, source, sw, tw: (SAMPLE_ROWS, "sha1"))
    monkeypatch.setattr(dcm.bcm, "load_tools_rows", lambda data_dir, sw, tw: SAMPLE_ROWS)
    runner = FakeRunner([_log_rule([])])
    with_ref = dcm.build_report(ref="origin/main", run_command=runner)
    without_ref = dcm.build_report(ref=None, run_command=runner)
    assert "closed" in with_ref["snapshot_caveat"] and "closed" in without_ref["snapshot_caveat"]


# ---------------------------------------------------------------------------
# AC5 — shared, not duplicated, classification
# ---------------------------------------------------------------------------

def test_imports_shared_classification_from_bash_command_mix():
    source = inspect.getsource(dcm)
    assert "bash_command_mix" in source
    assert dcm.bcm.bash_head is not None
    assert dcm.bcm.gh_subcommand_key is not None


def test_no_duplicate_command_classification_ladder_in_new_module():
    source = Path(dcm.__file__).read_text(encoding="utf-8")
    # A duplicate classifier would look like a second `if head ==`/`parts[0] ==` command-name
    # comparison ladder; this module should only ever call into bcm's functions for that.
    assert "parts[0] ==" not in source
    assert 'input_summary.strip().split()' not in source


# ---------------------------------------------------------------------------
# AC6 — determinism
# ---------------------------------------------------------------------------

def test_same_rows_produce_identical_output(monkeypatch):
    monkeypatch.setattr(dcm.bcm, "load_tools_rows_from_ref", lambda ref, source, sw, tw: (SAMPLE_ROWS, "sha1"))
    runner = FakeRunner([_log_rule(["TCK-20260924-X: fix"])])
    r1 = dcm.build_report(ref="origin/main", run_command=runner)
    r2 = dcm.build_report(ref="origin/main", run_command=runner)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


# ---------------------------------------------------------------------------
# Regression-prone paths
# ---------------------------------------------------------------------------

def test_gh_row_with_single_token_counted_as_unparseable():
    rows = [_row("Bash", "gh")]
    report = dcm.build_gh_call_report(rows)
    assert report["gh_unparseable_count"] == 1
    assert report["gh_calls_total"] == 1


def test_bash_command_mix_own_tests_unaffected():
    result = subprocess.run(
        ["/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3", "-m", "pytest",
         "tests/tools/test_bash_command_mix.py", "-q"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_write_side_effect(monkeypatch):
    monkeypatch.setattr(dcm.bcm, "load_tools_rows_from_ref", lambda ref, source, sw, tw: (SAMPLE_ROWS, "sha1"))
    runner = FakeRunner([_log_rule([])])
    before = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    dcm.build_report(ref="origin/main", run_command=runner)
    after = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    assert before == after
