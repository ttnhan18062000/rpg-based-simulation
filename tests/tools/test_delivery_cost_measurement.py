"""Tests for tools/delivery/delivery_cost_measurement.py (TCK-20260924-DELIVERY-COST-MEASUREMENT).

One section per Acceptance Criterion, per staging_artifacts/TCK-20260924-DELIVERY-COST-
MEASUREMENT/test_plan.md.
"""
import inspect
import json
import subprocess
import sys
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
        [sys.executable, "-m", "pytest",
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


# ---------------------------------------------------------------------------
# TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT — rework rate, failure class, pushes after green
# ---------------------------------------------------------------------------

WF = ".github/workflows/test.yml"


def _run(rid, sha, pr, conclusion, created, attempt=1, path=WF):
    # `pull_requests` is empty on purpose: GitHub clears it once the PR branch is deleted
    return {"id": rid, "head_sha": sha, "conclusion": conclusion, "created_at": created, "run_attempt": attempt,
            "path": path, "head_branch": f"branch-{pr}", "pull_requests": []}


def _rework_runner(runs, subjects, jobs_by_run=None, runs_error=None):
    """Fake gh/git: merged-PR log, run list, per-run job lists, merge-commit file lists."""
    jobs_by_run = jobs_by_run or {}

    def rule_log(cmd):
        return cmd[:2] == ["git", "log"]

    def rule_rev(cmd):
        return cmd[:2] == ["git", "rev-parse"]

    def rule_show(cmd):
        return cmd[:2] == ["git", "show"]

    def rule_pulls(cmd):
        return cmd[0] == "gh" and "/pulls?state=closed" in " ".join(cmd)

    def rule_runs(cmd):
        return cmd[0] == "gh" and "actions/runs?per_page=100" in " ".join(cmd)

    def rule_jobs(cmd):
        return cmd[0] == "gh" and "/jobs" in " ".join(cmd) and "actions/jobs/" not in " ".join(cmd)

    def rule_job(cmd):
        return cmd[0] == "gh" and "actions/jobs/" in " ".join(cmd)

    class R(FakeRunner):
        def __call__(self, cmd, timeout=30):
            self.calls.append(cmd)
            joined = " ".join(cmd)
            if rule_rev(cmd):
                return CommandResult(0, "abc123def\n", "")
            if rule_log(cmd):
                return CommandResult(0, "".join(f"{sha}\t{subj}\n" for sha, subj in subjects), "")
            if rule_show(cmd):
                return CommandResult(0, "tests/tools/test_x.py\n", "")
            if rule_pulls(cmd):
                nums = sorted({int(subj.rsplit("(#", 1)[1].rstrip(")")) for _, subj in subjects if "(#" in subj} | {99})
                return CommandResult(0, json.dumps([{"number": n, "head": {"ref": f"branch-{n}"},
                                                     "merged_at": None if n == 99 else "2026-09-24T00:00:00Z"} for n in nums]), "")
            if rule_runs(cmd):
                if runs_error:
                    return CommandResult(1, "", runs_error)
                return CommandResult(0, json.dumps({"workflow_runs": runs}), "")
            if rule_jobs(cmd):
                rid = int(joined.split("actions/runs/")[1].split("/")[0])
                return CommandResult(0, json.dumps({"jobs": jobs_by_run.get(rid, [])}), "")
            if rule_job(cmd):
                return CommandResult(0, json.dumps({"steps": [{"name": "Run tests", "conclusion": "failure"}]}), "")
            raise AssertionError(f"no rule matched {cmd!r}")

    return R([])


def test_rework_fixture_with_one_first_pass_failure_reports_rate_and_class():
    runs = [
        # PR 10: first push fails, second passes (failed then fixed, 0 pushes after first green)
        _run(1, "a1", 10, "failure", "2026-09-22T10:00:00Z"),
        _run(2, "a2", 10, "success", "2026-09-22T11:00:00Z"),
        # PR 11: first push passes, then one more push after green
        _run(3, "b1", 11, "success", "2026-09-23T10:00:00Z"),
        _run(4, "b2", 11, "success", "2026-09-23T11:00:00Z"),
        # another workflow's run and an unmerged PR are ignored
        _run(5, "c1", 12, "failure", "2026-09-23T12:00:00Z", path=".github/workflows/other.yml"),
        _run(6, "d1", 99, "failure", "2026-09-23T12:00:00Z"),
    ]
    jobs = {1: [{"id": 501, "name": "Slow regression", "conclusion": "failure"}]}
    runner = _rework_runner(runs, [("m10", "feat: x (#10)"), ("m11", "feat: y (#11)"), ("m0", "no pr number")], jobs)
    rw = dcm.build_rework_report("origin/main", run_command=runner)
    assert rw["prs_merged_in_range"] == 2 and rw["prs_with_ci_history"] == 2
    assert rw["first_pass_ci_rate"] == 0.5
    assert rw["prs_failed_then_fixed"] == 1
    assert rw["pushes_after_first_green_total"] == 1
    assert rw["per_pr"]["10"]["first_outcome"] == "failure" and rw["per_pr"]["11"]["first_pass_ci"] is True
    # the failed run's job is classified by the existing classifier ('Slow regression' is a known parked job)
    assert sum(rw["failure_classes"].values()) == 1
    assert rw["classification_note"]


def test_rework_rerun_of_a_failed_run_counts_as_rework_not_first_pass():
    runs = [_run(1, "a1", 20, "success", "2026-09-22T10:00:00Z", attempt=2)]
    rw = dcm.build_rework_report("origin/main", run_command=_rework_runner(runs, [("m20", "x (#20)")]))
    assert rw["first_pass_ci_rate"] == 0.0 and rw["reran_attempts_total"] == 1
    assert rw["per_pr"]["20"]["first_outcome"] == "success_after_rerun"


def test_rework_output_is_labelled_a_baseline_snapshot_of_the_ref_and_sha():
    rw = dcm.build_rework_report("origin/main", run_command=_rework_runner([], []))
    assert rw["measured_ref"] == "origin/main" and rw["measured_sha"] == "abc123def"
    assert rw["snapshot_caveat"] == dcm.SNAPSHOT_CAVEAT and "never an 'after' claim" in rw["baseline_only"]
    assert rw["first_pass_ci_rate"] is None  # no PRs: undefined, not zero


def test_rework_unreachable_gh_says_so_instead_of_reporting_zeros():
    runner = _rework_runner([], [("m1", "x (#1)")], runs_error="x509: certificate signed by unknown authority")
    rw = dcm.build_rework_report("origin/main", run_command=runner)
    assert rw["ci_history_available"] is False and "certificate" in rw["reason"]
    assert "first_pass_ci_rate" not in rw


def test_rework_is_opt_in_and_the_default_report_is_unchanged(monkeypatch, capsys):
    monkeypatch.setattr(dcm.bcm, "load_tools_rows", lambda *a, **k: SAMPLE_ROWS)
    monkeypatch.setattr(dcm, "measure_subject_traceability", lambda *a, **k: {"total_subjects": 0, "ticket_id_subjects": 0, "share": 0.0})
    called = []
    monkeypatch.setattr(dcm, "build_rework_report", lambda *a, **k: called.append(1) or {})
    assert dcm.main(["--json"]) == 0
    assert "rework" not in json.loads(capsys.readouterr().out) and not called


def test_rework_makes_only_two_gh_api_list_calls_when_nothing_failed():
    runner = _rework_runner([_run(1, "a1", 10, "success", "2026-09-22T10:00:00Z")], [("m10", "x (#10)")])
    dcm.build_rework_report("origin/main", run_command=runner)
    gh_calls = [" ".join(c) for c in runner.calls if c[0] == "gh"]
    assert len(gh_calls) == 2 and all(c.startswith("gh api repos/") for c in gh_calls)
    assert any("actions/runs?per_page=100&event=pull_request&page=1" in c for c in gh_calls)
    assert any("/pulls?state=closed" in c and "page=1" in c for c in gh_calls)
