"""Tests for tools/test_architecture/junit_cost_report.py (report-only JUnit cost view, roadmap §9)."""

import json
from pathlib import Path

import pytest

from tools.test_architecture import junit_cost_report as jcr


def _xml(cases):
    """cases: (classname, name, time|None, kind) tuples."""
    rows = []
    for cls, name, t, kind in cases:
        attr = f' time="{t}"' if t is not None else ""
        child = {"failed": "<failure/>", "errors": "<error/>", "skipped": "<skipped/>"}.get(kind, "")
        rows.append(f'<testcase classname="{cls}" name="{name}"{attr}>{child}</testcase>')
    return f'<testsuites><testsuite name="pytest">{"".join(rows)}</testsuite></testsuites>'


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    for rel in ("tests/unit/a/test_one.py", "tests/unit/b/test_two.py", "tests/integration/c/test_three.py"):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("", encoding="utf-8")
    return root


def _write(tmp_path, name, cases):
    d = tmp_path / "junit"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text(_xml(cases), encoding="utf-8")
    return p


def _report(paths, repo, **kw):
    return jcr.build_report(jcr.collect_xml(paths), [str(p) for p in paths], repo_root=repo, **kw)


def test_empty_input_is_no_junit_artifact_never_zero_seconds(repo):
    r = _report([], repo)
    assert r["state"] == jcr.NO_ARTIFACT and r["runs"] == []
    text = jcr.render_markdown(r)
    assert jcr.NO_ARTIFACT in text and "no cost evidence" in text and " 0 s" not in text


def test_single_run_counts_durations_and_slowest(tmp_path, repo):
    p = _write(tmp_path, "r.xml", [("tests.unit.a.test_one", "t1", 1.5, "passed"), ("tests.unit.a.test_one", "t2", 0.5, "failed"),
                                   ("tests.unit.b.test_two", "t3", 3.0, "skipped")])
    run = _report([p], repo)["runs"][0]
    assert run["testcases"] == 3 and run["unique_nodes"] == 3
    assert run["observed_test_duration_s"] == 5.0 and run["duration_label"] == "observed test duration"
    assert run["outcomes"] == {"passed": 1, "failed": 1, "errors": 0, "skipped": 1}
    assert run["slowest_files"][0] == {"name": "tests/unit/b/test_two.py", "observed_test_duration_s": 3.0}
    assert run["slowest_nodes"][0]["name"] == "tests.unit.b.test_two::t3"
    assert run["per_directory"]["tests/unit/a"]["duration"] == 2.0


def test_directory_absent_from_a_run_is_not_in_supplied_runs_not_zero(tmp_path, repo):
    a = _write(tmp_path, "a.xml", [("tests.unit.a.test_one", "t", 1.0, "passed")])
    b = _write(tmp_path, "b.xml", [("tests.integration.c.test_three", "t", 2.0, "passed")])
    runs = {r["artifact"]: r for r in _report([a, b], repo)["runs"]}
    assert runs["a.xml"]["per_directory"]["tests/integration/c"] == {"state": jcr.NOT_IN_RUNS}
    assert runs["b.xml"]["per_directory"]["tests/unit/a"] == {"state": jcr.NOT_IN_RUNS}
    assert "duration" not in runs["a.xml"]["per_directory"]["tests/integration/c"]


def test_missing_duration_is_stated_not_treated_as_zero(tmp_path, repo):
    p = _write(tmp_path, "m.xml", [("tests.unit.a.test_one", "t1", 2.0, "passed"), ("tests.unit.a.test_one", "t2", None, "passed")])
    run = _report([p], repo)["runs"][0]
    assert run["duration_state"] == jcr.MISSING_DURATION and run["testcases_missing_duration"] == 1
    assert run["per_directory"]["tests/unit/a"]["missing"] == 1
    assert "partial: missing time" in jcr.render_markdown(_report([p], repo))


def test_multiple_runs_stay_separate_and_directories_expand(tmp_path, repo):
    _write(tmp_path, "one.xml", [("tests.unit.a.test_one", "t", 1.0, "passed")])
    _write(tmp_path, "two.xml", [("tests.unit.b.test_two", "t", 4.0, "passed")])
    rep = jcr.build_report(jcr.collect_xml([tmp_path / "junit"]), ["junit"], repo_root=repo)
    assert [r["artifact"] for r in rep["runs"]] == ["one.xml", "two.xml"]
    assert [r["observed_test_duration_s"] for r in rep["runs"]] == [1.0, 4.0]
    assert rep["overlapping_node_sets"] == []


def test_duplicate_artifacts_are_detected_by_sha256(tmp_path, repo):
    cases = [("tests.unit.a.test_one", "t", 1.0, "passed")]
    a = _write(tmp_path, "a.xml", cases)
    b = _write(tmp_path, "b.xml", cases)
    rep = _report([a, b], repo)
    assert len(rep["duplicate_artifacts"]) == 1 and len(rep["duplicate_artifacts"][0]["runs"]) == 2
    assert "Duplicate artifacts" in jcr.render_markdown(rep)


def test_overlapping_node_sets_across_different_artifacts_are_reported(tmp_path, repo):
    a = _write(tmp_path, "a.xml", [("tests.unit.a.test_one", "shared", 1.0, "passed"), ("tests.unit.a.test_one", "x", 1.0, "passed")])
    b = _write(tmp_path, "b.xml", [("tests.unit.a.test_one", "shared", 2.0, "passed")])
    rep = _report([a, b], repo)
    assert rep["overlapping_node_sets"][0]["shared_nodes"] == 1 and rep["duplicate_artifacts"] == []


def test_unmapped_classnames_are_labelled_not_guessed(tmp_path, repo):
    p = _write(tmp_path, "u.xml", [("nowhere.test_x", "t", 1.0, "passed")])
    run = _report([p], repo)["runs"][0]
    assert "unmapped" in run["per_directory"] and run["slowest_files"][0]["name"] == "unmapped:nowhere.test_x"


def test_failure_history_is_unavailable_and_nothing_is_authorized(tmp_path, repo):
    rep = _report([_write(tmp_path, "r.xml", [("tests.unit.a.test_one", "t", 1.0, "passed")])], repo)
    assert rep["failure_history"] == "unavailable" and rep["report_only"] is True and "nothing" in rep["authorizes"]


def test_output_is_deterministic(tmp_path, repo, capsys):
    p1 = _write(tmp_path, "a.xml", [("tests.unit.a.test_one", "t2", 1.0, "passed"), ("tests.unit.b.test_two", "t1", 1.0, "passed")])
    p2 = _write(tmp_path, "b.xml", [("tests.integration.c.test_three", "t", 1.0, "failed")])
    outs = []
    for order in ([p1, p2], [p2, p1]):
        assert jcr.main([*map(str, order), "--repo-root", str(repo), "--format", "json", "--sha", "abc"]) == 0
        data = json.loads(capsys.readouterr().out)
        data["identity"]["input_scope"].sort()
        outs.append(json.dumps(data, sort_keys=True))
    assert outs[0] == outs[1]
