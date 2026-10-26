"""Shape of the paired perf tripwire step in `perf-cert-arena` (TCK-20261011-PERF-M2-T03B-CI-PAIRED-STEP).

testing-planner's six conditions (issue 488) as assertions on `.github/workflows/test.yml`: the job has a timeout, the step is report-only, the base is
a second checkout at the PR's base SHA under its own path, a non-PR event skips the step with a stated reason, and both SHAs and the CPU model reach the
report. No live Actions run is possible from pytest, so this reads the YAML like the other `test_ci_*` shape tests.
"""
from pathlib import Path

import yaml

_WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "test.yml"
_JOB = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))["jobs"]["perf-cert-arena"]
_STEPS = {step.get("name", ""): step for step in _JOB["steps"]}
_TRIPWIRE = _STEPS["Perf tripwire (paired, report-only)"]


def test_the_job_has_a_timeout_sized_from_its_p95() -> None:
    assert _JOB["timeout-minutes"] == 10
    assert "p95" in _WORKFLOW.read_text(encoding="utf-8")


def test_the_job_keeps_its_path_filter() -> None:
    assert "run_perf_cert_arena" in _JOB["if"] and "changed-files" in _JOB["needs"]


def test_the_base_is_a_second_checkout_at_the_pr_base_sha_under_its_own_path() -> None:
    step = _STEPS["Perf tripwire base checkout"]
    assert step["uses"] == "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    assert step["with"] == {"ref": "${{ github.event.pull_request.base.sha }}", "path": "perf-base"}
    assert step["if"] == "github.event_name == 'pull_request'"
    assert "HEAD~1" not in _TRIPWIRE["run"].replace("never guesses HEAD~1", "")


def test_a_non_pull_request_event_skips_the_step_and_says_why() -> None:
    run = _TRIPWIRE["run"]
    assert _TRIPWIRE["env"] == {"EVENT_NAME": "${{ github.event_name }}"}  # context via env, never inline in the run block
    assert 'if [ "$EVENT_NAME" != "pull_request" ]' in run and "no base SHA" in run and "exit 0" in run


def test_the_step_is_report_only_it_neither_continues_on_error_nor_gates_on_the_outcome() -> None:
    assert "continue-on-error" not in _TRIPWIRE  # only infrastructure failures (tripwire.py exit 1) should fail the job
    assert "tools/perf/tripwire.py run --base perf-base --head ." in _TRIPWIRE["run"]
    assert "--summary" in _TRIPWIRE["run"]
    text = _WORKFLOW.read_text(encoding="utf-8")
    assert "REPORT-ONLY" in text


def test_the_artifact_is_uploaded_even_when_a_step_fails() -> None:
    step = _STEPS["Perf tripwire artifact"]
    assert step["uses"] == "actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9" and step["with"]["name"] == "perf-tripwire"
    assert "always()" in step["if"]


def test_the_calibration_step_runs_on_manual_dispatch_only() -> None:
    assert _STEPS["Perf tripwire A/A calibration (manual dispatch only)"]["if"] == "github.event_name == 'workflow_dispatch'"
