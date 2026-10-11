"""Static guards for the rpg gate report workflow (TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW).

Same `yaml.safe_load` pattern as `test_ci_slow_workflow_shape.py`; no live Actions execution is possible from pytest. Live evidence (a scheduled run and a
dispatch run) is recorded in the ticket.
"""
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_PATH = _ROOT / ".github" / "workflows" / "rpg-gate-report.yml"


def _workflow() -> dict:
    return yaml.safe_load(_PATH.read_text(encoding="utf-8"))


def _triggers() -> dict:
    wf = _workflow()
    return wf.get("on", wf.get(True))  # PyYAML parses the bare key `on` as True


def _jobs() -> dict:
    return _workflow()["jobs"]


def _steps(job: str) -> list:
    return _jobs()[job]["steps"]


def _run_text(job: str) -> str:
    return "\n".join(s.get("run", "") for s in _steps(job))


def test_triggers_are_a_daily_off_hour_schedule_and_a_dispatch_with_a_ref_input_only():
    triggers = _triggers()
    assert set(triggers) == {"schedule", "workflow_dispatch"}  # no push, no pull_request
    crons = [entry["cron"] for entry in triggers["schedule"]]
    assert len(crons) == 1
    minute, hour, dom, month, dow = crons[0].split()
    assert minute not in ("0", "00") and hour.isdigit() and (dom, month, dow) == ("*", "*", "*")  # once a day, off the hour
    assert "ref" in triggers["workflow_dispatch"]["inputs"]
    # clear of the slow suite's slots
    assert f"{minute}" != "41"


def test_concurrency_group_is_non_cancelling():
    concurrency = _workflow()["concurrency"]
    assert concurrency["cancel-in-progress"] is False and "rpg-gate-report" in concurrency["group"]


def test_gate_runs_the_shared_decision_module_for_this_workflow_on_schedule_only_with_pipefail():
    gate = _jobs()["gate"]
    assert gate["permissions"] == {"actions": "read", "contents": "read"} and gate["timeout-minutes"] <= 10
    decide = next(s for s in gate["steps"] if s.get("id") == "decide")
    assert decide["if"] == "${{ github.event_name == 'schedule' }}"
    run = decide["run"]
    assert run.lstrip().startswith("set -o pipefail")
    assert "tools.test_architecture.slow_regression_gate decide" in run
    assert "--workflow rpg-gate-report.yml" in run and '--suite-job "RPG gate report"' in run


def test_the_suite_job_the_gate_looks_for_has_that_exact_name():
    assert _jobs()["report"]["name"] == "RPG gate report"


def test_only_an_explicit_skip_decision_stops_a_run_and_a_dispatch_always_runs():
    plan_if = _jobs()["plan"]["if"]
    assert "!cancelled()" in plan_if and "workflow_dispatch" in plan_if and "decision != 'skip'" in plan_if
    assert _jobs()["plan"]["needs"] == "gate"


def test_missing_config_or_module_stops_the_run_green_before_any_shard_and_an_invalid_config_turns_plan_red():
    for job in ("shard", "report"):
        assert "needs.plan.outputs.ready == 'true'" in _jobs()[job]["if"]
    run = _run_text("plan")
    assert "rpg_gate_plan" in run and 'exit "$rc"' in run  # the plan's exit status (non-zero for an invalid config) is the job's, after the outputs are written
    assert "set -o pipefail" not in run or "| tee" not in run  # no pipe that would hide the plan's exit status


def test_shards_do_not_fail_fast_run_the_harness_per_world_and_have_a_timeout_with_headroom():
    shard = _jobs()["shard"]
    assert shard["strategy"]["fail-fast"] is False and 60 < shard["timeout-minutes"] <= 360
    run = _run_text("shard")
    assert "tools.test_architecture.rpg_gate_harness" in run and "--only-world" in run and "--workers 2" in run
    assert "needs.plan.outputs.matrix" in shard["strategy"]["matrix"]
    assert any(s.get("with", {}).get("name", "").startswith("rpg-gate-docs-") for s in shard["steps"])


def test_the_report_job_evaluates_uploads_updates_the_issue_on_schedule_only_and_ends_on_the_verdict():
    steps = _steps("report")
    run = _run_text("report")
    assert "tools.test_architecture.rpg_gate_report" in run and "GITHUB_STEP_SUMMARY" in run
    uploads = [s for s in steps if "upload-artifact" in s.get("uses", "")]
    assert uploads and uploads[0]["if"] == "always()"
    issue = next(s for s in steps if "rpg_gate_issue" in s.get("run", ""))
    assert "github.event_name == 'schedule'" in issue["if"]
    assert "rpg_gate_issue" not in "\n".join(s.get("run", "") for j in ("shard", "plan", "gate") for s in _steps(j))
    assert steps[-1]["name"] == "Verdict" and 'test "$verdict" = "green"' in steps[-1]["run"]
    assert steps.index(issue) < len(steps) - 1 and steps.index(uploads[0]) < steps.index(issue)


def test_permissions_are_least_privilege_and_issues_write_is_only_on_the_report_job():
    jobs = _jobs()
    assert "permissions" not in _workflow()  # job-level only
    for name, job in jobs.items():
        wants_issues = job["permissions"].get("issues") == "write"
        assert wants_issues == (name == "report"), name


def test_the_workflow_is_advisory_nothing_needs_it_and_no_other_workflow_triggers_on_it():
    assert not any("workflow_run" in str((yaml.safe_load(p.read_text(encoding="utf-8")) or {})) and "RPG gate report" in p.read_text(encoding="utf-8")
                   for p in (_ROOT / ".github" / "workflows").glob("*.yml") if p != _PATH)
    assert "RPG gate report" not in (_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")


def test_the_report_job_writes_a_baseline_candidate_best_effort_and_labels_a_non_main_one_evidence_only():
    step = next(s for s in _steps("report") if s.get("name", "").startswith("Baseline candidate"))
    assert step["continue-on-error"] is True and step["if"] == "${{ !cancelled() }}"  # a refusal never fails the job
    run = step["run"]
    assert "tools.test_architecture.rpg_gate_candidate" in run and "--known tools/test_architecture/rpg_gate_known.yaml" in run
    assert "report/rpg-gate-candidate.json" in run and "--evidence-only" in run and "Baseline candidate refused" in run
    names = [s.get("name", "") for s in _steps("report")]
    assert names.index(step["name"]) < names.index("Upload report")  # inside the uploaded `report/` directory
