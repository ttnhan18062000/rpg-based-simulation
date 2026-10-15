"""`tools/delivery/ci_lanes.py` and check D of the pre-push advisory hook (TCK-20261014-PRE-PUSH-CI-LANE-PARITY).

The resolver reads the real `.github/workflows/test.yml`; the guard tests below fail when a new CI lane or a
changed-files regex becomes something it cannot map, so a lane is never silently missed.
"""
from __future__ import annotations

import re
import subprocess

import pytest

from tools.delivery import ci_lanes as lanes
from tools.delivery import pre_push_advisory_hook as hook


@pytest.fixture(scope="module")
def workflow():
    return lanes.load_workflow()


def _verdicts(workflow, changed, **kw):
    return {v.lane: v for v in lanes.resolve(workflow, changed, **kw)}


# A representative slice of PR #536's changed files (453 in all; the list is trimmed to one path per area). The
# checks that PR missed in CI: perf inventories (tests/perf), API metadata (tests/api), the visual_assets
# census (tests/visual_assets). The fourth, a thread-leak test, was not traced to a changed file.
PR_536 = [
    "src/engine/pipeline.py",
    "src/core/models/entity.py",
    "src/api/presenters/world.py",
    "tests/unit/engine/test_pipeline.py",
    "tests/perf/test_simq_isolation_overhead.py",
    "tests/api/test_metadata_api.py",
    "tests/visual_assets/test_icon_item_families.py",
    "tests/mechanic_scenarios/test_scenario.py",
    "data/content/living/species.yaml",
    "tools/test_architecture/scenario_lane_paths.py",
    "docs/engine/kernel.md",
]


# --- guards on the real test.yml -------------------------------------------------------------------------------

def test_real_test_yml_maps_completely(workflow):
    assert workflow.problems == []
    assert set(workflow.regexes) == {"PERF_RE", "MIG_RE", "FRONTEND_RE", "DOCKER_RE"}


def test_every_job_but_the_gates_is_a_lane(workflow):
    import yaml

    jobs = yaml.safe_load(lanes.TEST_WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    assert {l.name for l in workflow.lanes} == set(jobs) - {"changed-files"} - lanes.GATE_JOBS


def _mutated(tmp_path, old, new, count=1):
    text = lanes.TEST_WORKFLOW.read_text(encoding="utf-8")
    assert old in text
    path = tmp_path / "test.yml"
    path.write_text(text.replace(old, new, count), encoding="utf-8")
    return lanes.load_workflow(path)


def test_guard_fails_when_a_regex_variable_is_missing(tmp_path):
    problems = _mutated(tmp_path, "FRONTEND_RE='", "FRONTEND_PATTERN='").problems
    assert any("FRONTEND_RE" in p and "found 0" in p for p in problems)


def test_guard_fails_when_a_regex_variable_is_assigned_twice(tmp_path):
    text = lanes.TEST_WORKFLOW.read_text(encoding="utf-8")
    line = next(l for l in text.splitlines() if l.strip().startswith("DOCKER_RE='"))
    problems = _mutated(tmp_path, line, line + "\n" + line).problems
    assert any("DOCKER_RE" in p and "found 2" in p for p in problems)


def test_guard_fails_when_a_regex_does_not_compile(tmp_path):
    problems = _mutated(tmp_path, "FRONTEND_RE='^(frontend/", "FRONTEND_RE='^((frontend/").problems
    assert any("FRONTEND_RE" in p and "compile" in p for p in problems)


def test_guard_fails_on_an_unmapped_changed_files_output(tmp_path):
    problems = _mutated(
        tmp_path, "      run_frontend: ${{ steps.diff.outputs.run_frontend }}",
        "      run_frontend: ${{ steps.diff.outputs.run_frontend }}\n      run_new_lane: ${{ steps.diff.outputs.run_new_lane }}",
    ).problems
    assert any("run_new_lane" in p for p in problems)


def test_guard_fails_on_a_pytest_step_with_no_test_path(tmp_path):
    problems = _mutated(tmp_path, "pytest tests/simulation_quality", "pytest --co -q", 1).problems
    assert any("simulation-quality" in p and "no tests/ path" in p for p in problems)


# --- resolution --------------------------------------------------------------------------------------------------

def test_pr_536_names_the_lanes_that_held_the_missed_checks(workflow):
    v = _verdicts(workflow, PR_536)
    assert v["perf-cert-arena"].verdict == "runs"
    assert "tests/perf/test_simq_isolation_overhead.py" in v["perf-cert-arena"].hints
    assert "tests/api/test_metadata_api.py" in v["api-cli-engine"].hints
    assert "tests/visual_assets/test_icon_item_families.py" in v["api-cli-engine"].hints
    touched = {x.lane for x in lanes.touched(workflow, lanes.resolve(workflow, PR_536))}
    assert {"perf-cert-arena", "api-cli-engine", "migration-lanes"} <= touched
    assert v["frontend"].verdict == "skipped" and v["docker-build"].verdict == "skipped"


def test_scenario_lane_does_not_run_when_perf_covers_it(workflow):
    assert _verdicts(workflow, PR_536)["scenario-lane"].verdict == "skipped"
    # PERF_RE does not name tests/mechanic_scenarios, so a scenario-test-only diff runs the dedicated lane instead.
    only_scenarios = _verdicts(workflow, ["tests/mechanic_scenarios/test_x.py"])
    assert only_scenarios["perf-cert-arena"].verdict == "skipped"
    assert only_scenarios["scenario-lane"].verdict == "runs"


def test_a_docs_only_diff_touches_no_lane(workflow):
    verdicts = lanes.resolve(workflow, ["docs/engine/kernel.md"])
    assert lanes.touched(workflow, verdicts) == []
    assert {v.lane: v.verdict for v in verdicts}["perf-cert-arena"] == "skipped"


@pytest.mark.parametrize("changed", [[], ["docs/a.md"], ["src/x.py"], PR_536])
def test_an_always_on_lane_is_never_reported_skipped(workflow, changed):
    for lane in workflow.lanes:
        if lane.always_on:
            assert _verdicts(workflow, changed)[lane.name].verdict == "runs"


def test_a_src_only_change_has_no_hint_but_every_unfiltered_lane_runs(workflow):
    v = _verdicts(workflow, ["src/systems/economy.py"])
    assert all(x.hints == [] for x in v.values())
    assert v["unit-gameplay"].verdict == "runs" and v["integration"].verdict == "runs"


def test_ignore_glob_keeps_tools_tests_in_their_half(workflow):
    v = _verdicts(workflow, ["tests/tools/test_delivery_ci_lanes.py", "tests/tools/test_zeta.py"])
    assert v["tools-a-e"].hints == ["tests/tools/test_delivery_ci_lanes.py"]
    assert v["tools-f-z"].hints == ["tests/tools/test_zeta.py"]


def test_failed_diff_fails_open_never_skipped(workflow):
    for lane in workflow.lanes:
        v = _verdicts(workflow, [], diff_ok=False)[lane.name]
        assert v.verdict.startswith("runs")
        if not lane.always_on:
            assert v.verdict == "runs (fail-open)"


def test_regex_error_fails_open(workflow, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("classifier broke")

    monkeypatch.setattr(lanes, "compute_flags", boom)
    v = _verdicts(workflow, ["docs/a.md"])
    assert v["perf-cert-arena"].verdict == "runs (fail-open)"
    assert "classifier broke" in v["perf-cert-arena"].reason


def test_if_expression_with_an_unknown_atom_is_an_error_not_a_skip(workflow):
    with pytest.raises(ValueError):
        lanes.evaluate_if("${{ github.actor == 'someone' }}", {})


def test_regexes_match_grep_semantics_for_the_documented_cases(workflow):
    perf = workflow.regexes["PERF_RE"]
    assert perf.search("src/systems/economy.py")
    assert not perf.search("src/rendering/draw.py")  # excluded by the negative lookahead
    assert not perf.search("docs/a.md")


# --- listing, running -------------------------------------------------------------------------------------------

def test_render_list_names_slow_lanes_and_the_assumptions(workflow):
    text = lanes.render_list(workflow, lanes.resolve(workflow, PR_536), "origin/main", ["x.py"])
    assert "slow-regression.yml: not on PR" in text
    assert "resync-gate assumed not to skip" in text
    assert "1 uncommitted path(s)" in text
    assert "* perf-cert-arena" in text


def test_commands_drop_the_junit_artifact_flag(workflow):
    commands = lanes.lane_commands(next(l for l in workflow.lanes if l.name == "simulation-quality"))
    assert commands and all("--junit-xml" not in c for c in commands)


def test_run_lanes_reports_pass_and_fail_per_lane(workflow):
    calls = []

    def runner(cmd, cwd=None):
        calls.append(cmd[-1])
        return subprocess.CompletedProcess(cmd, 1 if "simulation_quality" in cmd[-1] else 0)

    results = lanes.run_lanes(workflow, ["integration", "simulation-quality"], runner=runner)
    assert results == {"integration": True, "simulation-quality": False}
    assert len(calls) == 2


def test_git_changed_uses_three_dots_and_none_on_failure():
    seen = []

    def runner(cmd, **kw):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="a.py\n\nb.py\n")

    assert lanes.git_changed("origin/main", run=runner) == ["a.py", "b.py"]
    assert seen[0] == ["git", "diff", "--name-only", "origin/main...HEAD"]
    assert lanes.git_changed("x", run=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 128, stdout="")) is None


# --- check D of the hook ----------------------------------------------------------------------------------------

def _diff_runner(stdout, returncode=0):
    def run(cmd, timeout=30):
        assert cmd == ["git", "diff", "--name-only", "origin/main...HEAD"]
        return hook.CommandResult(returncode, stdout, "")

    return run


def test_check_d_names_touched_lanes_and_the_command():
    findings = hook.check_ci_lanes(_diff_runner("\n".join(PR_536) + "\n"))
    assert len(findings) == 1
    assert "perf-cert-arena" in findings[0] and "api-cli-engine" in findings[0]
    assert "python3 -m tools.delivery.ci_lanes --run" in findings[0]


def test_check_d_says_nothing_when_no_lane_is_touched_or_the_diff_fails():
    assert hook.check_ci_lanes(_diff_runner("docs/engine/kernel.md\n")) == []
    assert hook.check_ci_lanes(_diff_runner("")) == []
    assert hook.check_ci_lanes(_diff_runner("", returncode=128)) == []


def test_check_d_degrades_to_no_finding_on_any_error(monkeypatch):
    monkeypatch.setattr(lanes, "load_workflow", lambda *a, **k: (_ for _ in ()).throw(OSError("no test.yml")))
    assert hook.check_ci_lanes(_diff_runner("tests/api/x.py\n")) == []


def test_check_d_is_part_of_run_all_checks(monkeypatch):
    monkeypatch.setattr(hook, "check_commit_subjects", lambda *a, **k: [])
    monkeypatch.setattr(hook, "check_monitoring_shard_staged", lambda *a, **k: [])
    monkeypatch.setattr(hook, "check_squash_merged_finished", lambda *a, **k: [])
    out = hook.run_all_checks(run_command=_diff_runner("tests/api/x.py\n"))
    assert len(out) == 1 and re.search(r"CI lane\(s\) .*api-cli-engine", out[0])
