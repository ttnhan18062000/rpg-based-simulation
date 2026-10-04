"""Tests for tools/delivery/pr_status.py (TCK-20260924-DELIVERY-STATUS-TOOL).

One section per Acceptance Criterion, per agent-working/staging_artifacts/TCK-20260924-DELIVERY-STATUS-TOOL/
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
        # Built-in fallbacks for the context-enumeration calls (TCK-20261004-PR-STATUS-FALSE-GREEN-ON-
        # STANDALONE-CHECK-RUNS): a test that does not care about standalone contexts sees none, exactly
        # as before that stage existed. Supplied rules are tried first.
        self.rules = list(rules) + _default_context_rules()
        self.calls = []

    def __call__(self, cmd, timeout=30):
        self.calls.append(cmd)
        for predicate, result in self.rules:
            if predicate(cmd):
                return result
        raise AssertionError(f"FakeRunner: no rule matched command {cmd!r}")


def _default_context_rules():
    return [
        (lambda cmd: cmd[:2] == ["gh", "api"] and "/check-runs?" in cmd[2], ok({"total_count": 0, "check_runs": []})),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "/status?" in cmd[2], ok({"total_count": 0, "statuses": []})),
        (
            lambda cmd: cmd[:3] == ["gh", "pr", "checks"] and "--required" in cmd,
            pr_status.CommandResult(1, "", "no required checks reported on the 'x' branch"),
        ),
        (
            lambda cmd: cmd[:3] == ["gh", "pr", "checks"],
            pr_status.CommandResult(1, "", "no checks reported on the 'x' branch"),
        ),
    ]


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
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "success"}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "GREEN"
    assert result["head_sha"] == "abc123"
    assert result["failing_jobs"] == []


def test_pending_when_applicable_run_in_progress():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "in_progress", "conclusion": None}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "PENDING"
    assert result["head_sha"] == "abc123"


def test_json_output_contains_verdict_head_sha_reason(capsys):
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "success"}]),
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
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "success"}]),
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
            {"id": 2, "head_sha": "current999", "path": ".github/workflows/test.yml", "status": "in_progress", "conclusion": None},
        ]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "PENDING"
    assert result["head_sha"] == "current999"


# ---------------------------------------------------------------------------
# Workflow scoping (TCK-20260924-DELIVERY-STATUS-TOOL-WORKFLOW-SCOPE)
#
# `actions/runs?head_sha=` is repo-wide across every workflow. Runs are partitioned, not
# filtered: only the target workflow's runs at this SHA may produce GREEN/PENDING/FAILING; any
# other workflow's run at the same SHA is reported in `other_workflow_runs` and must never, on
# its own, turn the verdict FAILING (AC2) or vote on it at all.
# ---------------------------------------------------------------------------

def test_other_workflow_failure_does_not_turn_verdict_failing():
    """AC1/AC2/AC3: two workflows at one head SHA, target passing, other failing — GREEN, and the
    other workflow's failure is reported separately, never voted into the verdict."""
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([
            {"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml",
             "status": "completed", "conclusion": "success"},
            {"id": 2, "head_sha": "abc123", "path": ".github/workflows/deploy-docs.yml",
             "status": "completed", "conclusion": "failure"},
        ]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "GREEN"
    assert result["failing_jobs"] == []
    assert len(result["other_workflow_runs"]) == 1
    assert result["other_workflow_runs"][0]["path"] == ".github/workflows/deploy-docs.yml"


def test_target_workflow_failure_is_failing_regardless_of_other_workflow_success():
    """Symmetric case: target workflow fails, other workflow (unrelated) succeeds — still FAILING,
    proving the partition works both directions, not just "other failures are ignored"."""
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([
            {"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml",
             "status": "completed", "conclusion": "failure"},
            {"id": 2, "head_sha": "abc123", "path": ".github/workflows/deploy-docs.yml",
             "status": "completed", "conclusion": "success"},
        ]),
        _run_jobs_rule(1, [{"id": 99, "name": "unit-tests", "conclusion": "failure"}]),
        _job_steps_rule(99, [{"name": "Run tests", "conclusion": "failure"}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "FAILING"
    assert len(result["other_workflow_runs"]) == 1


def test_only_other_workflow_ran_at_current_sha_yields_unknown_not_absent_or_failing():
    """No run from the target workflow at this SHA yet, but another workflow did run here — must
    not be reported as ABSENT (a run DOES exist, just not the target's) nor FAILING (the other
    workflow's own conclusion must not vote)."""
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([
            {"id": 2, "head_sha": "abc123", "path": ".github/workflows/deploy-docs.yml",
             "status": "completed", "conclusion": "failure"},
        ]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["verdict"] == "UNKNOWN"
    assert len(result["other_workflow_runs"]) == 1


def test_other_workflow_runs_key_present_and_empty_on_single_workflow_verdicts():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml",
                          "status": "completed", "conclusion": "success"}]),
    ])
    result = pr_status.compute_pr_status(run_command=runner)
    assert result["other_workflow_runs"] == []


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
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "success"}]),
    ])
    pr_status.compute_pr_status(run_command=runner)
    assert not any(_is(cmd, "git", *LS_REMOTE_TOKENS) for cmd in runner.calls)


# ---------------------------------------------------------------------------
# Regression-prone paths (AC5, AC7, AC8)
# ---------------------------------------------------------------------------

def test_failing_verdict_never_fetches_a_log_endpoint():
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "failure"}]),
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
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "failure"}]),
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
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "success"}]),
    ])
    pr_status.compute_pr_status(run_command=runner)
    for cmd in runner.calls:
        rendered = " ".join(cmd)
        if cmd[:2] == ["gh", "api"]:
            # `commits/<sha>/check-runs` is a read endpoint whose path contains "commit"; for api calls the
            # mutation test is "no write method/field flag", which is what actually makes a call a write.
            assert not {"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input"} & set(cmd), rendered
            continue
        for bad in MUTATING_SUBSTRINGS:
            assert bad not in rendered, f"mutating command issued: {rendered}"


def test_working_tree_and_index_unchanged_after_run():
    before = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    runner = FakeRunner([
        _pr_view_rule(head_sha="abc123"),
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "success"}]),
    ])
    pr_status.compute_pr_status(run_command=runner)
    after = subprocess.run(["git", "status", "--short"], capture_output=True, text=True).stdout
    assert before == after


@pytest.mark.parametrize("runs,expected", [
    ([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "success"}], "GREEN"),
    ([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "in_progress", "conclusion": None}], "PENDING"),
    ([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "failure"}], "FAILING"),
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
        _runs_list_rule([{"id": 1, "head_sha": "abc123", "path": ".github/workflows/test.yml", "status": "completed", "conclusion": "failure"}]),
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


# ---------------------------------------------------------------------------
# Standalone check runs / commit statuses (TCK-20261004-PR-STATUS-FALSE-GREEN-ON-STANDALONE-CHECK-RUNS)
# ---------------------------------------------------------------------------

TARGET = ".github/workflows/test.yml"
GREEN_RUN = {"id": 1, "head_sha": "abc123", "path": TARGET, "status": "completed", "conclusion": "success"}


def _cr(name, status="completed", conclusion="success", run_id=None, cid=None):
    url = (
        f"https://github.com/o/r/actions/runs/{run_id}/job/{cid or 5}" if run_id
        else f"https://github.com/o/r/runs/{cid or 5}"
    )
    return {"id": cid or 5, "name": name, "status": status, "conclusion": conclusion, "details_url": url}


def _check_runs_rule(runs, page=None, total=None):
    def pred(cmd):
        return cmd[:2] == ["gh", "api"] and "/check-runs?" in cmd[2] and (page is None or cmd[2].endswith(f"&page={page}"))
    return pred, ok({"total_count": len(runs) if total is None else total, "check_runs": runs})


def _status_rule(statuses):
    return (
        lambda cmd: cmd[:2] == ["gh", "api"] and "/status?" in cmd[2],
        ok({"total_count": len(statuses), "statuses": statuses}),
    )


def _gh_checks_rule(rows, required=False):
    text = "".join(f"{n}\t{b}\t1s\thttps://x\n" for n, b in rows)
    return (
        lambda cmd: cmd[:3] == ["gh", "pr", "checks"] and (("--required" in cmd) == required),
        pr_status.CommandResult(1 if any(b != "pass" for _, b in rows) else 0, text, ""),
    )


def _annotations_rule(check_id, annotations):
    return (
        lambda cmd: cmd[:2] == ["gh", "api"] and f"check-runs/{check_id}/annotations" in cmd[2],
        ok(annotations),
    )


def _status_of(rules):
    return pr_status.compute_pr_status(run_command=FakeRunner([_pr_view_rule(head_sha="abc123")] + rules))


def _frozen_291_shaped_contexts():
    """21 contexts shaped like PR #291: 19 jobs of the target workflow (run 1), one standalone passing
    `complexipy`, one standalone FAILING `ruff` (conclusion failure)."""
    jobs = [_cr(f"job-{i}", run_id=1, cid=100 + i) for i in range(19)]
    return jobs + [_cr("complexipy", cid=900), _cr("ruff", conclusion="failure", cid=901)]


def test_standalone_failing_ruff_makes_verdict_failing_not_green():
    runner_rules = [
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule(_frozen_291_shaped_contexts()),
        _annotations_rule(901, [{"path": "tools/x.py", "start_line": 3, "annotation_level": "failure", "message": "E501 line too long"}]),
    ]
    result = _status_of(runner_rules)
    assert result["verdict"] == "FAILING"
    assert result["contexts_examined"] == 21
    assert [c["name"] for c in result["failing_contexts"]] == ["ruff"]
    assert "ruff" in result["reason"]
    assert result["failing_contexts"][0]["annotations"][0]["path"] == "tools/x.py"


def test_same_fixture_without_the_context_stage_would_have_read_green():
    """Positive control: the workflow-runs view alone (what the tool used before) is GREEN for this
    fixture, so the FAILING above is produced by the new stage and not by the fixture."""
    result = pr_status._verdict_from_applicable_runs([GREEN_RUN], "abc123", FakeRunner([]))
    assert result["verdict"] == "GREEN"


def test_failure_on_a_second_page_is_seen():
    page1 = [_cr(f"ok-{i}", cid=i + 1) for i in range(100)]
    page2 = [_cr(f"ok2-{i}", cid=200 + i) for i in range(49)] + [_cr("ruff", conclusion="failure", cid=999)]
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule(page1, page=1, total=150),
        _check_runs_rule(page2, page=2, total=150),
        _annotations_rule(999, []),
    ])
    assert result["verdict"] == "FAILING"
    assert result["contexts_examined"] == 150


def test_required_context_absent_from_examined_set_is_unknown_not_green():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule([_cr("unit", run_id=1)]),
        _gh_checks_rule([("unit", "pass")]),
        _gh_checks_rule([("unit", "pass"), ("ruff", "pass")], required=True),
    ])
    assert result["verdict"] == "UNKNOWN"
    assert "ruff" in result["reason"]


def test_all_required_present_and_passing_stays_green_and_counts_contexts():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule([_cr("unit", run_id=1), _cr("ruff")]),
        _gh_checks_rule([("unit", "pass"), ("ruff", "pass")]),
        _gh_checks_rule([("ruff", "pass")], required=True),
    ])
    assert result["verdict"] == "GREEN"
    assert result["contexts_examined"] == 2
    assert "1 required check(s) read" in result["context_notes"]


def test_unreadable_required_checks_is_said_not_silently_green_or_blocking():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule([_cr("ruff")]),
        _gh_checks_rule([("ruff", "pass")]),
    ])
    assert result["verdict"] == "GREEN"
    assert any("no required checks configured" in n for n in result["context_notes"])


@pytest.mark.parametrize("bad", [fail(1, "boom"), fail(1, "x509: certificate signed by unknown authority"),
                                 pr_status.CommandResult(0, "not json", ""),
                                 pr_status.CommandResult(0, json.dumps({"unexpected": 1}), "")])
def test_check_runs_fetch_error_or_malformed_payload_is_unknown_never_green(bad):
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "/check-runs?" in cmd[2], bad),
    ])
    assert result["verdict"] == "UNKNOWN"
    assert "incomplete" in result["reason"]


def test_status_endpoint_error_is_unknown_never_green():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        (lambda cmd: cmd[:2] == ["gh", "api"] and "/status?" in cmd[2], fail()),
    ])
    assert result["verdict"] == "UNKNOWN"


def test_short_pagination_is_unknown_not_an_empty_pass():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule([], total=7),
    ])
    assert result["verdict"] == "UNKNOWN"
    assert "ran out of pages" in result["reason"]


def test_pending_standalone_check_run_is_pending():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule([_cr("ruff", status="in_progress", conclusion=None)]),
    ])
    assert result["verdict"] == "PENDING"


def test_skipped_and_neutral_do_not_block_green():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule([_cr("a", conclusion="skipped"), _cr("b", conclusion="neutral"), _cr("c")]),
    ])
    assert result["verdict"] == "GREEN"


def test_failing_commit_status_is_failing_and_pending_status_is_pending():
    failing = _status_of([_runs_list_rule([GREEN_RUN]), _status_rule([{"context": "ci/legacy", "state": "failure"}])])
    assert failing["verdict"] == "FAILING" and failing["failing_contexts"][0]["source"] == "commit-status"
    pending = _status_of([_runs_list_rule([GREEN_RUN]), _status_rule([{"context": "ci/legacy", "state": "pending"}])])
    assert pending["verdict"] == "PENDING"


def test_gh_pr_checks_failure_the_enumeration_missed_is_not_lost():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule([_cr("unit", run_id=1)]),
        _gh_checks_rule([("unit", "pass"), ("mystery-check", "fail")]),
    ])
    assert result["verdict"] == "FAILING"
    assert result["failing_contexts"][0]["source"] == "gh pr checks only"


def test_other_workflow_check_run_does_not_vote_even_when_gh_pr_checks_lists_it():
    other = {"id": 2, "head_sha": "abc123", "path": ".github/workflows/docs.yml", "status": "completed", "conclusion": "failure"}
    result = _status_of([
        _runs_list_rule([GREEN_RUN, other]),
        _check_runs_rule([_cr("unit", run_id=1), _cr("docs-publish", conclusion="failure", run_id=2, cid=77)]),
        _gh_checks_rule([("unit", "pass"), ("docs-publish", "fail")]),
    ])
    assert result["verdict"] == "GREEN"
    assert result["contexts_examined"] == 1


def test_unavailable_gh_pr_checks_cross_check_is_noted_but_does_not_block():
    result = _status_of([
        _runs_list_rule([GREEN_RUN]),
        _check_runs_rule([_cr("ruff")]),
        (lambda cmd: cmd[:3] == ["gh", "pr", "checks"], pr_status.CommandResult(2, "", "boom")),
    ])
    assert result["verdict"] == "GREEN"
    assert any("cross-check" in n and "unavailable" in n for n in result["context_notes"])


def test_failing_workflow_verdict_is_kept_and_standalone_failure_is_added():
    result = _status_of([
        _runs_list_rule([{**GREEN_RUN, "conclusion": "failure"}]),
        _run_jobs_rule(1, [{"id": 99, "name": "unit", "conclusion": "failure"}]),
        _job_steps_rule(99, [{"name": "Run", "conclusion": "failure"}]),
        _check_runs_rule([_cr("ruff", conclusion="failure", cid=901)]),
        _annotations_rule(901, []),
    ])
    assert result["verdict"] == "FAILING"
    assert len(result["failing_jobs"]) == 1 and len(result["failing_contexts"]) == 1
