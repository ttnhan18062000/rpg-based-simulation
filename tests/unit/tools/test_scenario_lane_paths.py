"""Tests for tools/test_architecture/scenario_lane_paths.py (CI scenario-lane routing, roadmap D-R2)."""

import io
from pathlib import Path

import pytest
import yaml

from tools.test_architecture import scenario_lane_paths as slp

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("path", [
    "src/systems/economy.py",
    "tests/mechanic_scenarios/test_x.py",   # a scenario-test-only PR must run the lane (old PERF_RE omitted it)
    "tests/helpers/scenario.py",
    "tests/conftest.py",
    "data/content/entities/goblin.yaml",
    "data/worlds/unit_selfmodel_pilot/world.yaml",
    "config/simulation_quality/scoring_weights.yaml",
    "requirements.txt",
])
def test_trigger_paths_run_the_lane(path):
    r = slp.classify([path])
    assert r["run"] is True and r["matched"] == [path] and r["unknown"] == []


@pytest.mark.parametrize("path", ["docs/testing/x.md", "agent-working/tickets/done/T.md", "agent-working/agent-monitoring/data/a.jsonl",
                                  "frontend/src/App.tsx", "README.md", "tools/test_architecture/core_rpg_report.py"])
def test_known_irrelevant_paths_alone_skip_the_lane(path):
    r = slp.classify([path])
    assert r == {"run": False, "matched": [], "unknown": [], "irrelevant": [path]}


def test_unknown_path_fails_open_and_is_named():
    r = slp.classify(["docs/a.md", "brand_new_dir/x.bin"])
    assert r["run"] is True and r["unknown"] == ["brand_new_dir/x.bin"]
    assert "brand_new_dir/x.bin" in slp.render_summary(r, perf_covers=False)


def test_summary_states_when_perf_covers_and_when_skipped():
    covered = slp.render_summary(slp.classify(["src/a.py"]), perf_covers=True)
    assert "perf-cert-arena" in covered and "`src/a.py`" in covered
    skipped = slp.render_summary(slp.classify(["docs/a.md"]), perf_covers=False)
    assert "skipped" in skipped and "`docs/a.md`" in skipped


def _run_main(monkeypatch, capsys, stdin, argv=()):
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    assert slp.main(list(argv)) == 0
    return capsys.readouterr().out.splitlines()


def test_main_first_line_is_the_output_flag(monkeypatch, capsys):
    assert _run_main(monkeypatch, capsys, "docs/a.md\n")[0] == "run_scenario_lane=false"
    assert _run_main(monkeypatch, capsys, "docs/a.md\nsrc/x.py\n")[0] == "run_scenario_lane=true"


def test_main_empty_diff_fails_open(monkeypatch, capsys):
    assert _run_main(monkeypatch, capsys, "")[0] == "run_scenario_lane=true"


def test_main_classifier_error_fails_open(monkeypatch, capsys):
    monkeypatch.setattr(slp, "classify", lambda paths: (_ for _ in ()).throw(RuntimeError("boom")))
    out = _run_main(monkeypatch, capsys, "docs/a.md\n")
    assert out[0] == "run_scenario_lane=true" and "boom" in out[1]


def test_workflow_wires_the_lane_without_double_running_scenarios():
    wf = yaml.safe_load((REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8"))
    jobs = wf["jobs"]
    assert "run_scenario_lane" in jobs["changed-files"]["outputs"]
    cond = jobs["scenario-lane"]["if"]
    assert "run_scenario_lane == 'true'" in cond and "run_perf_cert_arena != 'true'" in cond
    assert "needs.changed-files.result != 'success'" in cond  # fail open when the gate itself failed
    runs = [s.get("run", "") for s in jobs["scenario-lane"]["steps"]]
    assert any("tests/mechanic_scenarios" in r for r in runs)


# Routing fixtures: real path shapes, no manufactured feature changes. Mirrors the workflow's PERF_RE gate.
import re as _re

def _workflow_perf_re():
    """PERF_RE read from the workflow itself so the fixtures cannot drift from the real gate."""
    text = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
    return _re.compile(_re.search(r"PERF_RE='([^']+)'", text).group(1))


_PERF_RE = _workflow_perf_re()


def _route(paths):
    """(run flag, perf covers) the workflow would compute for these changed paths."""
    return slp.classify(paths)["run"], any(_PERF_RE.match(p) for p in paths)


def _jobs(paths):
    """(perf-cert-arena runs, dedicated scenario-lane job runs) the workflow would compute.

    The dedicated job's `if` is `run_scenario_lane == 'true' && run_perf_cert_arena != 'true'`
    (asserted by test_workflow_wires_the_lane_without_double_running_scenarios), and
    perf-cert-arena itself runs tests/mechanic_scenarios.
    """
    run, perf = _route(paths)
    return perf, run and not perf


def test_src_progression_only_runs_the_scenario_tests_in_perf_cert_arena():
    """Epic B criterion 4 ("a PR touching only src/progression/** runs the scenario tests") stand-in.

    TCK-20261008-PERF-LANE-PATH-GATE-MISSES-SIMULATION-SRC-DIRS widened PERF_RE to any src/ path outside
    an evidence-derived exclusion list, so src/progression is now covered by perf-cert-arena (which runs
    tests/mechanic_scenarios) instead of the dedicated scenario-lane job. The criterion's property is
    unchanged: the scenario tests run, in exactly one job. Cleared with testing-planner 2026-10-08.
    """
    perf_job, lane_job = _jobs(["src/progression/xp.py"])
    assert perf_job is True and lane_job is False
    assert "routed to perf-cert-arena" in slp.render_summary(slp.classify(["src/progression/xp.py"]), perf_covers=True)


def test_src_systems_social_only_runs_the_scenario_tests_in_perf_cert_arena():
    """Same move as the progression test above: src/systems was outside the old PERF_RE, now it is inside."""
    paths = ["src/systems/social_systems/appraisal.py"]
    perf_job, lane_job = _jobs(paths)
    assert perf_job is True and lane_job is False
    assert "routed to perf-cert-arena" in slp.render_summary(slp.classify(paths), perf_covers=True)


@pytest.mark.parametrize("path", [
    "data/content/entities/goblin.yaml",   # non-src scenario trigger: only the dedicated job covers it
    "src/testing/scenario_runner.py",      # excluded src folder: still a scenario trigger, not a perf trigger
])
def test_dedicated_scenario_job_stand_ins_still_route_to_the_dedicated_job(path):
    perf_job, lane_job = _jobs([path])
    assert perf_job is False and lane_job is True
    assert "scenario-lane job" in slp.render_summary(slp.classify([path]), perf_covers=False)


@pytest.mark.parametrize("paths, scenario_tests_should_run", [
    (["src/progression/xp.py"], True),
    (["src/systems/economy.py"], True),
    (["src/domains/combat_engagement/x.py"], True),
    (["src/brand_new_folder/x.py"], True),
    (["src/testing/scenario_runner.py"], True),
    (["src/views/readiness.py"], True),
    (["data/content/entities/goblin.yaml"], True),
    (["data/worlds/unit_selfmodel_pilot/world.yaml"], True),
    (["tests/mechanic_scenarios/test_x.py"], True),
    (["tests/helpers/scenario.py"], True),
    (["config/simulation_quality/scoring_weights.yaml"], True),
    (["requirements.txt"], True),
    ([".github/workflows/test.yml"], True),
    (["brand_new_dir/x.bin"], True),                      # unknown path: fail open
    (["src/progression/xp.py", "data/content/a.yaml"], True),
    (["src/testing/a.py", "src/views/b.py"], True),
    (["docs/testing/x.md"], False),
    (["agent-working/tickets/done/T.md", "README.md"], False),
])
def test_scenario_tests_run_in_exactly_one_job(paths, scenario_tests_should_run):
    perf_job, lane_job = _jobs(paths)
    assert perf_job + lane_job == (1 if scenario_tests_should_run else 0), (paths, perf_job, lane_job)


def test_src_domains_progression_only_routes_to_perf_cert_arena():
    run, perf = _route(["src/domains/progression/service.py"])
    assert run is True and perf is True
    assert "routed to perf-cert-arena" in slp.render_summary(slp.classify(["src/domains/progression/service.py"]), True)


def test_mixed_change_is_routed_once_via_perf():
    paths = ["src/progression/xp.py", "src/domains/combat_engagement/x.py"]
    run, perf = _route(paths)
    assert run is True and perf is True  # perf covers, so the dedicated job (needs !perf) does not also run


def test_docs_only_change_is_skipped_and_says_so():
    run, perf = _route(["docs/testing/x.md", "agent-working/tickets/done/T.md"])
    assert run is False and perf is False
    assert "skipped" in slp.render_summary(slp.classify(["docs/testing/x.md"]), perf_covers=False)


def test_unknown_path_fails_open_to_the_lane():
    assert _route(["brand_new_dir/x.bin"]) == (True, False)


def test_summary_is_a_routing_statement_not_an_execution_record():
    for perf in (True, False):
        text = slp.render_summary(slp.classify(["src/a.py"]), perf_covers=perf)
        assert "scenario execution is that job's result" in text
        assert "no separate job" not in text


# TCK-20261008-PERF-LANE-PATH-GATE-MISSES-SIMULATION-SRC-DIRS: PERF_RE is "any src/ path except the
# evidence-derived exclusion list" (see the comment next to PERF_RE in test.yml).
@pytest.mark.parametrize("path", [
    "src/systems/economy.py", "src/strategy/planner.py", "src/progression/xp.py", "src/entities/entity.py",
    "src/economy/market.py", "src/quests/q.py", "src/town/t.py", "src/content/repository.py",
    "src/scenarios/s.py", "src/cli/main.py", "src/__main__.py", "src/brand_new_folder/x.py",
])
def test_formerly_missed_src_folders_trigger_the_perf_lane(path):
    assert _PERF_RE.match(path), path


@pytest.mark.parametrize("path", [
    "src/actions/harvest.py", "src/lab/orchestrator.py", "src/rendering/r.py", "src/runtime/bootstrap.py",
    "src/testing/scenario_runner.py", "src/views/readiness.py", "src/worldgeneration/generator.py",
])
def test_excluded_src_folders_alone_do_not_trigger_the_perf_lane(path):
    assert not _PERF_RE.match(path), path
    # An excluded folder is still a scenario trigger, so the dedicated job covers it.
    run, perf = _route([path])
    assert run is True and perf is False


def test_workflow_matches_perf_re_with_pcre_and_fails_open_on_grep_error():
    """The exclusion is a negative lookahead; grep -E would silently misread it, so the workflow must use grep -P.

    grep exits >= 2 on an error (e.g. a broken pattern); `grep ... && echo true || echo false` would turn that
    into "false" and skip the lane silently, so the match goes through perf_match(), which fails open.
    """
    text = (REPO_ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
    assert "(?!" in _PERF_RE.pattern
    assert 'grep -qE "$PERF_RE"' not in text
    assert text.count('grep -qP "$PERF_RE"') == 1
    assert 'PERF_COVERS=$(perf_match)' in text and 'run_perf_cert_arena=$PERF_COVERS' in text
    assert '[ "$rc" -ge 2 ]' in text and "failing open" in text
