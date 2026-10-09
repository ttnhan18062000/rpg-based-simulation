"""Static guards for the slow-regression workflow.

Shape pins for TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (Reporting-Path Design, P1/P2): the
slow suite lives in `.github/workflows/slow-regression.yml`, not in `test.yml` (whose cancel-in-progress group
evicted it); schedule + manual dispatch only, a non-cancelling concurrency group, a job timeout, explicit
least-privilege permissions, no `needs:`, and a closing report step. The step-gating pins below moved here
from `test_ci_slow_job_step_gating.py` with their assertions unchanged.

Step gating, from TCK-20261005-SLOW-REGRESSION-GATE-SKIPS-ITS-ONLY-TEST-STEP-ON-MAIN: in the `slow` job, the corpus-diversity step (5) failed or was
cancelled on most `main` runs, and the two later test steps (6 slow tests, 7 legacy regression)
had no `if:`, so they inherited the default `success()` and were skipped. Owner decision
2026-10-05: steps 6 and 7 run whether step 5 passes or fails, but a cancelled run stays
cancelled. This pins that shape: `!cancelled()` on 6 and 7, no `always()` or `continue-on-error`
on 5-7, and a closing summary step that reports each step's outcome.

Same `yaml.safe_load` pattern as `tests/static/test_corpus_diversity_ci_isolation.py`; no live
GitHub Actions execution is possible from pytest.
"""

from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_WORKFLOW_PATH = _ROOT / ".github" / "workflows" / "slow-regression.yml"
_TEST_WORKFLOW_PATH = _ROOT / ".github" / "workflows" / "test.yml"
_MAKEFILE_PATH = _ROOT / "Makefile"

_CORPUS_RUN = "make simq-corpus-diversity-slow-isolated"
_SLOW_TESTS_RUN = '-m "slow or extra_slow"'
_LEGACY_RUN = "make lane-legacy-regression"
_NOT_CANCELLED = "${{ !cancelled() }}"


def _workflow() -> dict:
    return yaml.safe_load(_WORKFLOW_PATH.read_text(encoding="utf-8"))


def _triggers() -> dict:
    workflow = _workflow()
    # PyYAML (YAML 1.1) parses the bare key `on` as the boolean True.
    return workflow.get("on", workflow.get(True))


def _slow_job() -> dict:
    return _workflow()["jobs"]["slow"]


def _slow_job_steps() -> list[dict]:
    return _slow_job()["steps"]


def _step_running(needle: str) -> dict:
    matches = [s for s in _slow_job_steps() if needle in s.get("run", "")]
    assert len(matches) == 1, f"expected exactly one slow-job step running {needle!r}, found {len(matches)}"
    return matches[0]


def _summary_step() -> dict:
    matches = [s for s in _slow_job_steps() if "GITHUB_STEP_SUMMARY" in s.get("run", "")]
    assert len(matches) == 1, "expected exactly one slow-job step writing GITHUB_STEP_SUMMARY"
    return matches[0]


def _report_step() -> dict:
    matches = [s for s in _slow_job_steps() if "slow_regression_report.py" in s.get("run", "")]
    assert len(matches) == 1, "expected exactly one report step"
    return matches[0]


def test_slow_tests_step_runs_even_when_corpus_diversity_fails() -> None:
    assert _step_running(_SLOW_TESTS_RUN).get("if") == _NOT_CANCELLED


def test_legacy_regression_step_runs_even_when_corpus_diversity_fails() -> None:
    assert _step_running(_LEGACY_RUN).get("if") == _NOT_CANCELLED


def test_steps_five_to_seven_continue_on_error_and_never_use_always() -> None:
    """Reporting-path hardening (2026-10-07) REVERSES the earlier pin (#360, #377) that forbade
    `continue-on-error` on steps 5-7. Reason (research report "CI known failure tracking patterns", rank 4,
    Trunk's exit-0-when-all-quarantined): a workflow that is red forever gets ignored, so the job's verdict
    belongs to the report step, which exits 1 only for an UNOWNED or EXPIRED red, a missing step or a GitHub
    error. `always()` stays forbidden: it would turn an evicted (cancelled) run into a reported result."""
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        step = _step_running(needle)
        assert step.get("continue-on-error") is True, step["name"]
        assert "always()" not in str(step.get("if", "")), step["name"]


def test_report_step_is_not_continue_on_error_so_it_alone_decides_the_job_conclusion() -> None:
    """Outcome vs conclusion: a failing step with continue-on-error has outcome 'failure' but conclusion
    'success'; the summary reads `.outcome` (truthful), the job turns red only if the report step fails."""
    report = _report_step()
    assert "continue-on-error" not in report
    assert report.get("if") == _NOT_CANCELLED


def test_each_test_step_has_an_id_for_the_summary_to_read() -> None:
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        assert _step_running(needle).get("id"), needle


def test_summary_step_reports_every_test_step_outcome() -> None:
    summary = _summary_step()
    assert summary.get("if") == _NOT_CANCELLED
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        step_id = _step_running(needle)["id"]
        assert f"steps.{step_id}.outcome" in summary["run"], step_id


def test_summary_step_runs_after_the_three_test_steps() -> None:
    steps = _slow_job_steps()
    summary_index = steps.index(_summary_step())
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        assert steps.index(_step_running(needle)) < summary_index


# ── shape of the workflow itself ─────────────────────────────────────────────────────────────


def test_triggers_are_schedule_and_dispatch_only_with_no_push() -> None:
    triggers = _triggers()
    assert set(triggers) == {"schedule", "workflow_dispatch"}
    assert "push" not in triggers and "pull_request" not in triggers
    assert [entry["cron"] for entry in triggers["schedule"]] == ["41 2,8,14,20 * * *"]


def test_concurrency_group_never_cancels_a_running_slow_run() -> None:
    concurrency = _workflow()["concurrency"]
    assert concurrency["cancel-in-progress"] is False
    assert concurrency["group"].startswith("slow-regression-")


def test_job_has_a_timeout_no_needs_and_least_privilege_permissions() -> None:
    job = _slow_job()
    assert job["timeout-minutes"] == 240
    assert job["needs"] == "gate", "the slow suite waits on its own gate only, never on the fast jobs"
    assert job["permissions"] == {"contents": "read", "issues": "write"}
    assert "permissions" not in _workflow(), "permissions are set at job level only"


def test_report_step_runs_last_but_for_uploads_and_is_not_gated_on_success() -> None:
    steps = _slow_job_steps()
    report = _report_step()
    assert report.get("if") == _NOT_CANCELLED
    assert steps.index(report) > steps.index(_summary_step())
    for needle in (_CORPUS_RUN, _SLOW_TESTS_RUN, _LEGACY_RUN):
        assert steps.index(_step_running(needle)) < steps.index(report)


def test_each_test_step_writes_junit_into_the_report_directory() -> None:
    assert "--junitxml=reports/slow/slow_tests.xml" in _step_running(_SLOW_TESTS_RUN)["run"]
    legacy = _step_running(_LEGACY_RUN)
    assert "reports/slow/legacy_regression.xml" in legacy["env"]["PYTEST_ADDOPTS"]


def test_isolated_corpus_loop_still_runs_every_id_and_keeps_its_floor() -> None:
    """The per-invocation JUnit flag was added to the Makefile loop; the 32-test floor and the exit
    logic are unchanged, so the floor cannot be bypassed."""
    text = _MAKEFILE_PATH.read_text(encoding="utf-8")
    start = text.index("simq-corpus-diversity-slow-isolated: ##")
    recipe = text[start : text.index("\n\n", start)]
    assert 'echo "$$nodeids" > reports/slow/corpus_expected.txt' in recipe  # lets the reporter spot a dead subprocess
    assert '-lt 32' in recipe and "exit 1" in recipe
    assert "for nodeid in $$nodeids" in recipe
    assert '--junitxml="reports/slow/corpus_$$n.xml"' in recipe
    assert "|| status=1" in recipe and recipe.rstrip().endswith("exit $$status")


def test_the_pr_workflow_no_longer_has_a_slow_job() -> None:
    workflow = yaml.safe_load(_TEST_WORKFLOW_PATH.read_text(encoding="utf-8"))
    assert "slow" not in workflow["jobs"]
    # No job still waits on it.
    for name, job in workflow["jobs"].items():
        assert "slow" not in (job.get("needs") or []), name


# --- TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN: the gate job ---

def _gate_job() -> dict:
    return _workflow()["jobs"]["gate"]


def test_gate_job_is_short_least_privilege_and_exports_its_decision() -> None:
    job = _gate_job()
    assert job["runs-on"] == "ubuntu-latest"
    assert job["timeout-minutes"] <= 15
    assert job["permissions"] == {"actions": "read", "contents": "read"}
    assert "needs" not in job
    assert job["outputs"]["decision"] == "${{ steps.decide.outputs.decision }}"


def test_gate_decision_step_runs_for_schedule_events_only() -> None:
    steps = [s for s in _gate_job()["steps"] if s.get("id") == "decide"]
    assert len(steps) == 1
    assert steps[0]["if"] == "${{ github.event_name == 'schedule' }}"
    assert "slow_regression_gate decide" in steps[0]["run"]
    assert "--exclude-run-id" in steps[0]["run"], "the gate must not count its own run"


def test_slow_job_runs_on_dispatch_or_unless_the_gate_said_skip_and_fails_open() -> None:
    condition = _slow_job()["if"]
    assert "github.event_name == 'workflow_dispatch'" in condition, "a dispatched run always tests"
    assert "needs.gate.outputs.decision != 'skip'" in condition, "only an explicit skip stops the suite (fail open)"
    assert "!cancelled()" in condition, "a failed gate must not skip the suite"


def test_the_suite_job_keeps_the_name_the_gate_reads_a_skip_from() -> None:
    from tools.test_architecture.slow_regression_gate import SUITE_JOB_NAME

    assert _slow_job()["name"] == SUITE_JOB_NAME


def test_report_and_issue_writes_live_only_in_the_gated_slow_job() -> None:
    gate_text = "\n".join(str(step) for step in _gate_job()["steps"])
    assert "slow_regression_report" not in gate_text and "issues" not in str(_gate_job()["permissions"])
    assert "slow_regression_report" in _report_step()["run"]
