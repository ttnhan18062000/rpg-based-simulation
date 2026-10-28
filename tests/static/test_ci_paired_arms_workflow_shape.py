"""Static guard for TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (AC4): the paired-arms workflow is manual, advisory, pinned and non-cancelling.

No GitHub Actions execution is possible from pytest, so this reads the YAML. The pin guard (`test_workflow_actions_pinned_by_sha.py`) and the context guard
(`test_workflow_run_blocks_take_github_context_via_env.py`) glob / list workflows too; this file also pins that they cover this one.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.static import test_workflow_actions_pinned_by_sha as pins
from tests.static import test_workflow_run_blocks_take_github_context_via_env as ctx

_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "paired-arms.yml"
INPUTS = {"base_sha", "new_sha", "step", "worlds", "seeds", "ticks", "self_check"}


def _wf() -> dict:
    return yaml.safe_load(_PATH.read_text(encoding="utf-8"))


def _on() -> dict:
    wf = _wf()
    return wf.get("on", wf.get(True))  # YAML 1.1 reads a bare `on` key as True


def test_it_is_dispatch_only_with_no_pull_request_push_or_schedule_trigger():
    on = _on()
    assert set(on) == {"workflow_dispatch"}
    for trigger in ("pull_request", "pull_request_target", "push", "schedule", "workflow_run", "workflow_call", "release"):
        assert trigger not in on


def test_the_dispatch_inputs_are_the_ticket_ones():
    inputs = _on()["workflow_dispatch"]["inputs"]
    assert INPUTS <= set(inputs)
    assert {name for name, spec in inputs.items() if spec.get("required")} == {"base_sha", "new_sha", "step"}
    assert inputs["self_check"]["default"] == "seed42" and inputs["legacy_base"]["type"] == "boolean"


def test_concurrency_is_per_step_and_never_cancels_a_running_pair():
    concurrency = _wf()["concurrency"]
    assert concurrency["cancel-in-progress"] is False
    assert concurrency["group"] == "paired-arms-${{ inputs.step }}"


def test_every_action_is_pinned_by_sha_and_the_two_guards_cover_this_file():
    assert pins.unpinned(_PATH.read_text(encoding="utf-8")) == []
    assert "paired-arms.yml" in pins.WORKFLOWS
    assert ctx.offending_steps(_PATH.read_text(encoding="utf-8")) == []
    assert _PATH in ctx.FILES


def test_the_jobs_are_plan_arms_aggregate_with_least_privilege():
    jobs = _wf()["jobs"]
    assert list(jobs) == ["plan", "arms", "aggregate"]
    for name, job in jobs.items():
        assert job["permissions"] == {"contents": "read"}, name
        assert job["timeout-minutes"] <= 360, name


def test_the_matrix_is_per_world_and_seed_and_both_arms_run_in_the_same_job():
    arms = _wf()["jobs"]["arms"]
    assert arms["strategy"]["fail-fast"] is False
    assert "needs.plan.outputs.matrix" in arms["strategy"]["matrix"]
    steps = {s["name"]: s for s in arms["steps"] if "name" in s}
    base, new, repeat = steps["Base arm"], steps["New arm"], steps["Base-vs-base repeat arm"]
    assert "--arm base" in base["run"] and "${BASE_SHA}" in base["run"] and "if" not in base
    assert "--arm new" in new["run"] and "${NEW_SHA}" in new["run"] and new["if"] == "${{ matrix.kind == 'pair' }}"
    assert "--repeat" in repeat["run"] and "${BASE_SHA}" in repeat["run"] and repeat["if"] == "${{ matrix.kind == 'self' }}"
    for step in (base, new, repeat):
        assert "paired_arms run-arm" in step["run"] and "--cache arm-cache" in step["run"]  # paired's own functions, never a re-implementation in the workflow


def test_every_job_checks_out_the_same_ref_so_the_child_hash_agrees():
    for name, job in _wf()["jobs"].items():
        checkouts = [s for s in job["steps"] if str(s.get("uses", "")).startswith("actions/checkout@")]
        assert len(checkouts) == 1 and "ref" not in checkouts[0].get("with", {}), name  # the dispatched ref, the same commit in plan, arms and aggregate


def test_artifact_names_carry_step_world_and_seed_and_self_jobs_are_marked():
    upload = next(s for s in _wf()["jobs"]["arms"]["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact@"))
    name = upload["with"]["name"]
    assert name.startswith("paired-arms-${{ needs.plan.outputs.slug }}-${{ matrix.world }}-s${{ matrix.seed }}") and "-self" in name
    assert upload["with"]["path"] == "upload/"
    download = next(s for s in _wf()["jobs"]["aggregate"]["steps"] if str(s.get("uses", "")).startswith("actions/download-artifact@"))
    assert download["with"]["pattern"] == "paired-arms-${{ needs.plan.outputs.slug }}-*" and "merge-multiple" not in download["with"]


def test_the_aggregate_refuses_mixed_runners_before_calling_paired_collected_with_the_verdict_json():
    steps = [s for s in _wf()["jobs"]["aggregate"]["steps"] if "name" in s]
    names = [s["name"] for s in steps]
    assert names.index("Assemble one paired cache root") < names.index("Compare with paired.py --collected")
    assemble = next(s for s in steps if s["name"] == "Assemble one paired cache root")["run"]
    assert "paired_arms assemble" in assemble and '--base "${BASE_SHA}"' in assemble and '--new "${NEW_SHA}"' in assemble
    compare = next(s for s in steps if s["name"] == "Compare with paired.py --collected")["run"]
    assert "tools.rpg_measure.paired --collected collected" in compare and "--verdict-json verdict.json" in compare
    assert "--jobs" not in compare and "--clean-cache" not in compare  # both are rejected with --collected


def test_no_step_pipes_a_refusable_command_into_tee():
    for name, job in _wf()["jobs"].items():
        for step in job["steps"]:
            assert "| tee" not in str(step.get("run", "")), f"{name}/{step.get('name')}: the default shell has no pipefail, a pipe hides the exit status"
