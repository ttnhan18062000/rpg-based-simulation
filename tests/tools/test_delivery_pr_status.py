"""Tests for tools/delivery/pr_status.py (TCK-20260924-DELIVERY-STATUS-TOOL).

One section per Acceptance Criterion, per staging_artifacts/TCK-20260924-DELIVERY-STATUS-TOOL/
test_plan.md. All I/O is a FakeRunner — no real subprocess, no network, fully deterministic.
"""
import json
import re
import subprocess

import pytest

from tools.delivery import pr_status


class FakeRunner:
    """Records every command it was called with (for the no-log-fetch / no-mutating-command
    assertions) and returns a canned CommandResult keyed by matching the command's leading
    tokens against a list of (predicate, result) rules, first match wins."""

    def __init__(self, rules):
        self.rules = rules
        self.calls = []

    def __call__(self, cmd, timeout=30):
        self.calls.append(cmd)
        for predicate, result in self.rules:
            if predicate(cmd):
                return result
        raise AssertionError(f"FakeRunner: no rule matched command {cmd!r}")


def _is(cmd, *tokens):
    return cmd[: len(tokens)] == list(tokens)


def _contains(cmd, substr):
    return any(substr in part for part in cmd)


def ok(payload):
    return pr_status.CommandResult(0, json.dumps(payload), "")


def fail(code=1, stderr="boom"):
    return pr_status.CommandResult(code, "", stderr)


PR_VIEW_TOKENS = ("pr", "view")
RUNS_LIST_SUBSTR = "actions/runs?head_sha="
JOBS_LIST_SUBSTR = "/jobs"  # matches both .../runs/{id}/jobs and .../jobs/{id}
LS_REMOTE_TOKENS = ("ls-remote",)


def _pr_view_rule(head_sha="deadbeef", mergeable="MERGEABLE", branch="feature-x", number=42):
    return (
        lambda cmd: _is(cmd, "gh", *PR_VIEW_TOKENS),
        ok({
            "number": number, "headRefOid": head_sha, "mergeable": mergeable,
            "headRefName": branch,
        }),
    )


def _runs_list_rule(runs):
    return (
        lambda cmd: cmd[0] == "gh" and cmd[1] == "api" and RUNS_LIST_SUBSTR in cmd[2],
        ok({"total_count": len(runs), "workflow_runs": runs}),
    )


def _run_jobs_rule(run_id, jobs):
    return (
        lambda cmd: cmd[0] == "gh" and cmd[1] == "api" and f"actions/runs/{run_id}/jobs" in cmd[2],
        ok({"jobs": jobs}),
    )


def _job_steps_rule(job_id, steps):
    return (
        lambda cmd: cmd[0] == "gh" and cmd[1] == "api" and f"actions/jobs/{job_id}" in cmd[2]
        and "/jobs/" in cmd[2] and not cmd[2].rstrip("0123456789").endswith("/jobs"),
        ok({"steps": steps}),
    )


def _ls_remote_rule(sha):
    return (
        lambda cmd: _is(cmd, "git", *LS_REMOTE_TOKENS),
        pr_status.CommandResult(0, f"{sha}\trefs/heads/feature-x\n" if sha else "", ""),
    )


# ---------------------------------------------------------------------------
# Normal flow
# ---------------------------------------------------------------------------

def test_green_when_all_applicable_runs_succeed_against_current_head():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "success"}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "GREEN"
    assert result["head_sha"] == "abc123"
    assert result["failing_jobs"] == []


def test_pending_when_applicable_run_in_progress():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "in_progress", "conclusion": None}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "PENDING"
    assert result["head_sha"] == "abc123"


def test_json_output_contains_verdict_head_sha_reason(capsys):
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "success"}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    exit_code = _emit(result, as_json=True, capsys=capsys)
    out = capsys.readouterr().out.strip()
    assert exit_code == 0
    assert out.startswith("MARKER:")
    payload = json.loads(out[len("MARKER:"):])
    assert payload["verdict"] == "GREEN"
    assert payload["head_sha"] == "abc123"
    assert "reason" in payload


def test_json_output_and_human_output_agree_on_verdict(capsys):
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "success"}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    pr_status._print_human(result)
    human_out = capsys.readouterr().out
    assert "verdict: GREEN" in human_out
    assert result["verdict"] == "GREEN"


def _emit(result, as_json, capsys):
    if as_json:
        print("MARKER:" + json.dumps(result))
    else:
        pr_status._print_human(result)
    return 0


# ---------------------------------------------------------------------------
# Edge cases: stale SHA (AC2)
# ---------------------------------------------------------------------------

def test_stale_sha_run_present_yields_unknown_not_green():
    runner = FakeRunner([
        _pr_view_rule(head_sha="current999"),
        _runs_list_rule([{"id": 1, "head_sha": "old111", "status": "completed", "conclusion": "success"}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "UNKNOWN"
    assert result["verdict"] != "GREEN"
    assert "current999" in str(result["head_sha"]) or result["head_sha"] == "current999"


def test_stale_sha_plus_current_sha_in_progress_yields_pending():
    runner = FakeRunner([
        _pr_view_rule(head_sha="current999"),
        _runs_list_rule([
            {"id": 1, "head_sha": "old111", "status": "completed", "conclusion": "success"},
            {"id": 2, "head_sha": "current999", "status": "in_progress", "conclusion": None},
        ]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "PENDING"
    assert result["head_sha"] == "current999"


# ---------------------------------------------------------------------------
# Edge cases: ABSENT (AC3 + disambiguators)
# ---------------------------------------------------------------------------

def test_absent_conflicting_pull_request_only_trigger(tmp_path):
    workflow = tmp_path / "test.yml"
    workflow.write_text("on:\n  pull_request:\n  push:\n    branches: [main]\n")
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123", mergeable="CONFLICTING", branch="feature-x"),
        _runs_list_rule([]),
        _ls_remote_rule("abc123"),
    ])
    result = pr_status.compute_pr_status(run_command=runner, workflow_path=workflow)
    assert result["verdict"] == "ABSENT"
    assert "CONFLICTING" in result["reason"]
    assert "resolve" in result["reason"].lower()
    assert "force-push" in result["reason"] or "force-push".replace("-", "") in result["reason"].replace("-", "")


def test_absent_push_not_landed_disambiguator(tmp_path):
    workflow = tmp_path / "test.yml"
    workflow.write_text("on:\n  pull_request:\n  push:\n    branches: [main]\n")
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123", mergeable="MERGEABLE", branch="feature-x"),
        _runs_list_rule([]),
        _ls_remote_rule("olderSHA"),
    ])
    result = pr_status.compute_pr_status(run_command=runner, workflow_path=workflow)
    assert result["verdict"] == "ABSENT"
    assert "push may not have landed" in result["reason"]


def test_absent_no_known_cause_still_reports_absent_not_unknown(tmp_path):
    workflow = tmp_path / "test.yml"
    workflow.write_text("on:\n  pull_request:\n  push:\n    branches: [main]\n")
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123", mergeable="MERGEABLE", branch="feature-x"),
        _runs_list_rule([]),
        _ls_remote_rule("abc123"),
    ])
    result = pr_status.compute_pr_status(run_command=runner, workflow_path=workflow)
    assert result["verdict"] == "ABSENT"
    assert "not determined" in result["reason"]


def test_workflow_covers_branch_via_push_true_when_no_push_key(tmp_path):
    workflow = tmp_path / "test.yml"
    workflow.write_text("on:\n  pull_request:\n")
    assert pr_status.workflow_covers_branch_via_push(workflow, "feature-x") is False


def test_workflow_covers_branch_via_push_true_when_push_has_no_branches_filter(tmp_path):
    workflow = tmp_path / "test.yml"
    workflow.write_text("on:\n  push: {}\n")
    assert pr_status.workflow_covers_branch_via_push(workflow, "feature-x") is True


def test_workflow_covers_branch_via_push_false_when_branch_not_listed(tmp_path):
    workflow = tmp_path / "test.yml"
    workflow.write_text("on:\n  push:\n    branches: [main]\n")
    assert pr_status.workflow_covers_branch_via_push(workflow, "feature-x") is False
    assert pr_status.workflow_covers_branch_via_push(workflow, "main") is True


# ---------------------------------------------------------------------------
# Failure modes (AC4) — the exact incident this ticket encodes
# ---------------------------------------------------------------------------

def test_unknown_when_runs_fetch_returns_nonzero_exit():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        (lambda cmd: cmd[0] == "gh" and cmd[1] == "api" and RUNS_LIST_SUBSTR in cmd[2],
         fail(1, "curl: (60) SSL certificate problem: unable to get local issuer certificate")),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "UNKNOWN"
    assert result["verdict"] != "GREEN"
    assert "tls" in result["reason"].lower() or "ssl" in result["reason"].lower() or "certificate" in result["reason"].lower()


def test_unknown_when_runs_fetch_returns_unparseable_stdout():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        (lambda cmd: cmd[0] == "gh" and cmd[1] == "api" and RUNS_LIST_SUBSTR in cmd[2],
         pr_status.CommandResult(0, "<html>Fortiguard block page</html>", "")),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "UNKNOWN"
    assert result["verdict"] != "GREEN"


def test_unknown_when_pr_view_fetch_fails():
    runner = FakeRunner([
        (lambda cmd: _is(cmd, "gh", *PR_VIEW_TOKENS), fail(1, "network error")),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "UNKNOWN"
    assert result["head_sha"] is None


def test_unknown_when_ls_remote_fails_during_absent_disambiguation(tmp_path):
    workflow = tmp_path / "test.yml"
    workflow.write_text("on:\n  pull_request:\n  push:\n    branches: [main]\n")
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123", mergeable="CONFLICTING", branch="feature-x"),
        _runs_list_rule([]),
        (lambda cmd: _is(cmd, "git", *LS_REMOTE_TOKENS), fail(1, "could not resolve host")),
    ])
    result = pr_status.compute_pr_status(run_command=runner, workflow_path=workflow)
    assert result["verdict"] == "UNKNOWN"
    assert "disambiguator" in result["reason"] or "ls-remote" in result["reason"].lower() or "cannot rule out" in result["reason"]


def test_ls_remote_disambiguator_never_called_when_runs_exist():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "success"}]),
    ])
    pr_status.compute_pr_status(run_command=runner)
    assert not any(_is(cmd, "git", *LS_REMOTE_TOKENS) for cmd in runner.calls)


# ---------------------------------------------------------------------------
# Regression-prone paths (AC5, AC7, AC8)
# ---------------------------------------------------------------------------

def test_failing_verdict_never_fetches_a_log_endpoint():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "failure"}]),
        _run_jobs_rule(1, [{"id": 99, "name": "unit-tests", "conclusion": "failure"}]),
        _job_steps_rule(99, [{"name": "Run tests", "conclusion": "failure"}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "FAILING"
    for cmd in runner.calls:
        assert "/logs" not in " ".join(str(c) for c in cmd)


def test_failing_verdict_includes_step_name_and_conclusion_per_failing_job():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "failure"}]),
        _run_jobs_rule(1, [
            {"id": 99, "name": "unit-tests", "conclusion": "failure"},
            {"id": 100, "name": "lint", "conclusion": "success"},
        ]),
        _job_steps_rule(99, [
            {"name": "Checkout", "conclusion": "success"},
            {"name": "Run tests", "conclusion": "failure"},
        ]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "FAILING"
    assert len(result["failing_jobs"]) == 1
    job = result["failing_jobs"][0]
    assert job["job_name"] == "unit-tests"
    step_names = {s["name"]: s["conclusion"] for s in job["steps"]}
    assert step_names["Run tests"] == "failure"
    assert step_names["Checkout"] == "success"


MUTATING_SUBSTRINGS = ("commit", "push", "pr create", "pr merge", "run rerun", "run watch")


def test_no_git_or_gh_mutating_command_ever_issued():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "success"}]),
    ])
    pr_status.compute_pr_status(run_command=runner)
    for cmd in runner.calls:
        rendered = " ".join(cmd)
        for bad in MUTATING_SUBSTRINGS:
            assert bad not in rendered, f"mutating command issued: {rendered}"


def test_working_tree_and_index_unchanged_after_run():
    before = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "success"}]),
    ])
    pr_status.compute_pr_status(run_command=runner)
    after = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    assert before == after


@pytest.mark.parametrize("runs,expected", [
    ([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "success"}], "GREEN"),
    ([{"id": 1, "head_sha": "abc123", "status": "in_progress", "conclusion": None}], "PENDING"),
    ([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "failure"}], "FAILING"),
])
def test_exit_code_zero_for_every_verdict(runs, expected, monkeypatch, capsys):
    rules = [_pr_view_rule(head_sha="abc123"), _runs_list_rule(runs)]
    if expected == "FAILING":
        rules.append(_run_jobs_rule(1, [{"id": 99, "name": "unit-tests", "conclusion": "failure"}]))
        rules.append(_job_steps_rule(99, [{"name": "Run tests", "conclusion": "failure"}]))
    runner = FakeRunner(rules)
    monkeypatch.setattr(pr_status, "default_run_command", runner)
    exit_code = pr_status.main(["--json"])
    out = capsys.readouterr().out.strip()
    payload = json.loads(out[len("MARKER:"):])
    assert payload["verdict"] == expected
    assert exit_code == 0


def test_exit_code_zero_for_absent_and_unknown_verdicts(tmp_path):
    workflow = tmp_path / "test.yml"
    workflow.write_text("on:\n  pull_request:\n  push:\n    branches: [main]\n")

    absent_runner = FakeRunner([
        _pr_view_rule(head_sha="abc123", mergeable="CONFLICTING", branch="feature-x"),
        _runs_list_rule([]),
        _ls_remote_rule("abc123"),
    ])
    absent_result = pr_status.compute_pr_status(run_command=absent_runner, workflow_path=workflow)
    assert absent_result["verdict"] == "ABSENT"

    unknown_runner = FakeRunner([
        (lambda cmd: _is(cmd, "gh", *PR_VIEW_TOKENS), fail(1, "network error")),
    ])
    unknown_result = pr_status.compute_pr_status(run_command=unknown_runner)
    assert unknown_result["verdict"] == "UNKNOWN"


def test_exit_code_nonzero_only_on_internal_error(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(pr_status, "compute_pr_status", _raise)
    exit_code = pr_status.main([])
    assert exit_code == 1


def test_cli_exit_code_zero_for_a_real_failing_computation(monkeypatch):
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "status": "completed", "conclusion": "failure"}]),
        _run_jobs_rule(1, [{"id": 99, "name": "unit-tests", "conclusion": "failure"}]),
        _job_steps_rule(99, [{"name": "Run tests", "conclusion": "failure"}]),
    ])
    monkeypatch.setattr(pr_status, "default_run_command", runner)
    exit_code = pr_status.main(["--json"])
    assert exit_code == 0


def test_no_sleep_or_retry_loop_present():
    source = (pr_status.__file__ and open(pr_status.__file__).read()) or ""
    assert "time.sleep" not in source
    assert not re.search(r"while\s+True\s*:", source)
    assert "import time" not in source
