"""Tests for the SARIF PR feedback filter (TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK).

Unit tests use small hand-built SARIF; the end-to-end tests run the real ruff and complexipy in a temporary
project so they prove the whole path: changed files -> tool SARIF -> registry filter -> upload-ready SARIF.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import pytest

from tools.code_health import registry, sarif_feedback
from tools.code_health.registry import Row
from tools.code_health.sarif_feedback import (
    SarifError,
    cap_results,
    changed_python_files,
    filter_complexipy,
    filter_ruff,
    parse_sarif,
    relative_uri,
    run,
)

_ROOT = Path("/repo")


def _row(file, symbol, tool, rule, ceiling):
    return Row(file, symbol, tool, rule, ceiling, ceiling, "2026-10-03", False, None)


def _rows(*rows):
    return {r.key: r for r in rows}


def _ruff_result(file, rule="bare-except", line=1):
    uri = f"file://{_ROOT}/{file}"
    region = {"startLine": line}
    return {"ruleId": rule, "level": "error", "message": {"text": "x"},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}, "region": region}}]}


def _cx_result(file, name, complexity, limit=15):
    return {"ruleId": "CC001", "level": "warning",
            "message": {"text": f"Function '{name}' has a cognitive complexity of {complexity}, which exceeds the maximum allowed complexity of {limit}."},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": file, "uriBaseId": "%SRCROOT%"}},
                           "logicalLocations": [{"kind": "function", "name": name}]}]}


_CODES = {"bare-except": "E722", "blind-except": "BLE001"}


# ── ruff filter ──────────────────────────────────────────────────────────────


def test_a_ruff_group_within_its_row_ceiling_is_filtered_out():
    run_ = {"results": [_ruff_result("src/a.py"), _ruff_result("src/a.py", line=5)]}
    kept, stats = filter_ruff(run_, _rows(_row("src/a.py", None, "ruff", "E722", 2)), _CODES, _ROOT)
    assert kept == [] and stats == {"kept": 0, "dropped": 2, "groups": 0}


def test_a_ruff_finding_with_no_row_is_kept_with_a_repository_relative_uri():
    kept, stats = filter_ruff({"results": [_ruff_result("src/b.py")]}, _rows(_row("src/a.py", None, "ruff", "E722", 1)), _CODES, _ROOT)
    assert [r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] for r in kept] == ["src/b.py"]
    assert stats["kept"] == 1 and stats["groups"] == 1


def test_a_ruff_group_above_its_ceiling_is_kept_whole():
    run_ = {"results": [_ruff_result("src/a.py", line=1), _ruff_result("src/a.py", line=9), _ruff_result("src/a.py", line=20)]}
    kept, stats = filter_ruff(run_, _rows(_row("src/a.py", None, "ruff", "E722", 2)), _CODES, _ROOT)
    assert len(kept) == 3 and stats == {"kept": 3, "dropped": 0, "groups": 1}


def test_a_different_rule_in_the_same_file_is_not_covered_by_the_row():
    kept, _ = filter_ruff({"results": [_ruff_result("src/a.py", rule="blind-except")]}, _rows(_row("src/a.py", None, "ruff", "E722", 5)), _CODES, _ROOT)
    assert len(kept) == 1


def test_an_unknown_rule_name_falls_back_to_the_name_as_the_code():
    kept, _ = filter_ruff({"results": [_ruff_result("src/a.py", rule="invalid-syntax")]},
                          _rows(_row("src/a.py", None, "ruff", "invalid-syntax", 1)), _CODES, _ROOT)
    assert kept == []


# ── complexipy filter ────────────────────────────────────────────────────────


def test_a_complexipy_function_at_or_below_its_ceiling_is_filtered_out_and_one_above_is_kept():
    rows = _rows(_row("src/k.py", "Kernel.run", "complexipy", "cognitive-complexity", 20))
    kept, stats = filter_complexipy({"results": [_cx_result("src/k.py", "Kernel::run", 20)]}, rows, _ROOT)
    assert kept == [] and stats["dropped"] == 1
    kept, stats = filter_complexipy({"results": [_cx_result("src/k.py", "Kernel::run", 21)]}, rows, _ROOT)
    assert len(kept) == 1 and kept[0]["locations"][0]["physicalLocation"]["artifactLocation"] == {"uri": "src/k.py"}


def test_a_new_complexipy_function_is_kept():
    kept, _ = filter_complexipy({"results": [_cx_result("src/k.py", "new_function", 30)]}, {}, _ROOT)
    assert len(kept) == 1


def test_a_complexipy_result_without_a_complexity_or_name_is_an_error_not_swallowed():
    bad = _cx_result("src/k.py", "f", 20)
    bad["message"]["text"] = "something else"
    with pytest.raises(SarifError, match="no complexity"):
        filter_complexipy({"results": [bad]}, {}, _ROOT)
    nameless = _cx_result("src/k.py", "f", 20)
    del nameless["locations"][0]["logicalLocations"]
    with pytest.raises(SarifError, match="no function name"):
        filter_complexipy({"results": [nameless]}, {}, _ROOT)


# ── parsing, paths, cap ──────────────────────────────────────────────────────


@pytest.mark.parametrize("text", ["{not json", "[]", '{"version": "2.0.0", "runs": []}', '{"version": "2.1.0"}',
                                  '{"version": "2.1.0", "runs": [{"results": [{"message": {}}]}]}'])
def test_malformed_sarif_raises_instead_of_being_swallowed(text):
    with pytest.raises(SarifError):
        parse_sarif(text, "ruff")


def test_a_valid_sarif_with_no_results_parses():
    assert parse_sarif('{"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "x"}}, "results": []}]}', "x")["runs"]


def test_uris_outside_the_repository_or_escaping_it_are_rejected():
    assert relative_uri("file:///repo/src/a.py", _ROOT) == "src/a.py"
    assert relative_uri("src/a.py", _ROOT) == "src/a.py"
    with pytest.raises(SarifError):
        relative_uri("file:///etc/passwd", _ROOT)
    with pytest.raises(SarifError):
        relative_uri("src/../../etc/passwd", _ROOT)


def test_the_result_cap_trims_across_runs_and_counts_what_it_left_out():
    runs = [{"results": list(range(700))}, {"results": list(range(700))}]
    assert cap_results(runs, 1000) == 400
    assert [len(r["results"]) for r in runs] == [700, 300]


def test_changed_paths_are_validated_before_use(tmp_path):
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    for name in ("src/a.py", "src/pkg/b.py", "src/-x.py"):
        (tmp_path / name).write_text("x = 1\n")
    paths = ["src/a.py", "src/pkg/b.py", "src/a.py", "src/missing.py", "tests/t.py", "src/readme.md", "src/../a.py",
             "src/a.py; rm -rf /", "-rf", "src/-x.py", "src/$(id).py", "/etc/passwd"]
    assert changed_python_files(paths, tmp_path) == ["src/a.py", "src/pkg/b.py"]


def test_a_symlinked_source_file_is_never_linted(tmp_path):
    (tmp_path / "src").mkdir()
    outside = tmp_path.parent / "outside_secret.py"
    outside.write_text("x = 1\n")
    (tmp_path / "src" / "link.py").symlink_to(outside)
    (tmp_path / "src" / "real.py").write_text("x = 1\n")
    assert changed_python_files(["src/link.py", "src/real.py"], tmp_path) == ["src/real.py"]


def test_a_tool_result_with_a_string_message_is_a_sarif_error_not_a_crash():
    text = json.dumps({"version": "2.1.0", "runs": [{"results": [{"ruleId": "x", "message": "plain string"}]}]})
    with pytest.raises(SarifError, match="malformed"):
        parse_sarif(text, "ruff")


# ── end to end with the real ruff and complexipy ─────────────────────────────

_PYPROJECT = """\
[tool.ruff.lint]
select = ["E722"]

[tool.complexipy]
max-complexity-allowed = 3
"""
_BARE = "def f():\n    try:\n        pass\n    except:\n        pass\n"
_COMPLEX = textwrap.dedent("""\
    def tangled(a, b, c):
        if a:
            if b:
                if c:
                    for i in range(a):
                        if i:
                            return i
        return 0
""")


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "registries").mkdir()
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT)
    (tmp_path / "src" / "a.py").write_text(_BARE + "\n" + _COMPLEX)
    (tmp_path / "src" / "b.py").write_text("x = 1\n")
    rows = [_row("src/a.py", None, "ruff", "E722", 1), _row("src/a.py", "tangled", "complexipy", "cognitive-complexity", 15)]
    registry.write_rows(tmp_path / "registries" / "code_health_exceptions.jsonl", rows)
    return tmp_path


def _code(rule_id: str) -> str:
    return _CODES.get(rule_id, rule_id) if rule_id != "bare-except" else "E722"


def _changed(project: Path, *paths: str) -> Path:
    path = project / "changed.txt"
    path.write_text("\n".join(paths) + "\n")
    return path


def _results(out: Path) -> list[dict]:
    return [r for run_ in json.loads(out.read_text())["runs"] for r in run_["results"]]


def test_end_to_end_baselined_findings_produce_no_results(project):
    out = project / "out.sarif"
    assert run(project, _changed(project, "src/a.py"), out) == 0
    assert _results(out) == []
    assert json.loads(out.read_text())["version"] == "2.1.0"


def test_end_to_end_exactly_the_new_violation_is_reported(project, capsys):
    (project / "src" / "b.py").write_text(_BARE)
    summary = project / "summary.md"
    summary.write_text("earlier step\n")
    out = project / "out.sarif"
    assert run(project, _changed(project, "src/a.py", "src/b.py"), out, summary, annotate=True) == 0
    results = _results(out)
    # ruff names a rule by its code (E722) or by its name (bare-except) depending on the rule; the filter handles both.
    assert [(_code(r["ruleId"]), r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]) for r in results] == [("E722", "src/b.py")]
    text = summary.read_text()
    assert text.startswith("earlier step\n") and "1 findings not in the baseline" in text and "Groups are shown whole" in text
    assert "::warning::code-health: 1 findings not in the baseline" in capsys.readouterr().out


def test_end_to_end_a_worse_group_and_a_worse_function_are_kept_whole(project):
    (project / "src" / "a.py").write_text(_BARE + "\n" + _BARE.replace("def f", "def g") + "\n" + _COMPLEX.replace("if i:", "if i or a:"))
    out = project / "out.sarif"
    assert run(project, _changed(project, "src/a.py"), out) == 0
    ids = sorted(_code(r["ruleId"]) for r in _results(out))
    assert ids == ["CC001", "E722", "E722"], "both bare excepts (old one included) and the worse function"


def test_end_to_end_with_no_changed_src_python_an_empty_valid_sarif_is_still_written(project):
    summary = project / "summary.md"
    out = project / "out.sarif"
    assert run(project, _changed(project, "README.md", "tests/test_x.py", "src/gone.py"), out, summary) == 0
    data = json.loads(out.read_text())
    assert data["version"] == "2.1.0" and data["runs"][0]["results"] == []
    assert "no changed `src` Python files" in summary.read_text()


def test_end_to_end_an_unusable_registry_writes_no_sarif_and_reports_could_not_run(project, capsys):
    (project / "registries" / "code_health_exceptions.jsonl").write_text("{not json\n")
    summary = project / "summary.md"
    out = project / "out.sarif"
    assert run(project, _changed(project, "src/a.py"), out, summary, annotate=True) == 2
    assert not out.exists(), "an empty upload would wrongly clear existing alerts"
    assert "could not run:" in summary.read_text()
    assert "::warning::code-health SARIF could not run (advisory):" in capsys.readouterr().out


def test_end_to_end_a_missing_changed_list_is_could_not_run_not_an_empty_upload(project, capsys):
    out = project / "out.sarif"
    summary = project / "summary.md"
    assert run(project, project / "absent-changed.txt", out, summary, annotate=True) == 2
    assert not out.exists(), "no changed list means no SARIF: an empty upload would clear earlier alerts"
    assert "could not run:" in summary.read_text()
    assert "::warning::code-health SARIF could not run (advisory):" in capsys.readouterr().out


def test_end_to_end_malformed_tool_output_is_reported_not_swallowed(project, monkeypatch):
    def broken(command, root, label):
        class Done:
            returncode, stdout, stderr = 0, "not sarif at all", ""
        return Done()

    monkeypatch.setattr(sarif_feedback, "ruff_rule_codes", lambda root: _CODES)
    monkeypatch.setattr(sarif_feedback, "_run_tool", broken)
    out = project / "out.sarif"
    summary = project / "summary.md"
    assert run(project, _changed(project, "src/a.py"), out, summary) == 2
    assert not out.exists() and "could not run: ruff: not valid JSON" in summary.read_text()


def test_end_to_end_a_missing_tool_is_reported_as_could_not_run(project, monkeypatch):
    def missing(command, root, label):
        raise SarifError(f"{label}: tool not found")

    monkeypatch.setattr(sarif_feedback, "_run_tool", missing)
    summary = project / "summary.md"
    assert run(project, _changed(project, "src/a.py"), project / "out.sarif", summary) == 2
    assert "could not run: ruff rule: tool not found" in summary.read_text()


def test_an_unexpected_shape_from_a_tool_exits_2_with_a_summary_line_instead_of_a_traceback(project, monkeypatch):
    broken = {"version": "2.1.0", "runs": [{"results": [{"ruleId": "x", "locations": [{"physicalLocation": 5}]}]}]}
    monkeypatch.setattr(sarif_feedback, "ruff_rule_codes", lambda root: _CODES)
    monkeypatch.setattr(sarif_feedback, "_tool_sarif", lambda files, root: (broken, broken))
    summary = project / "summary.md"
    assert run(project, _changed(project, "src/a.py"), project / "out.sarif", summary) == 2
    assert "could not run:" in summary.read_text() and not (project / "out.sarif").exists()


def test_the_cli_entry_point_writes_the_same_file(project):
    out = project / "cli.sarif"
    assert sarif_feedback.main(["--root", str(project), "--changed", str(_changed(project, "src/a.py")), "--out", str(out)]) == 0
    assert out.exists() and sys.executable
