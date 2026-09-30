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


@pytest.mark.parametrize("path", ["docs/testing/x.md", "tickets/done/T.md", "agent-monitoring/data/a.jsonl",
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
