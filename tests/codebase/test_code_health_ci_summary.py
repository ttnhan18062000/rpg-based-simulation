"""Tests for the advisory CI summary of the ratchet (TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB).

`format_summary` and the `check --summary-for/--summary-out/--annotate` flags turn the ratchet's result
into a GitHub job summary and a warning annotation; the exit code stays the ratchet's own. The CLI tests
reuse the scratch-repository fixtures of test_code_health_ratchet_registry.py.
"""
from __future__ import annotations

import json

from tests.codebase.test_code_health_ratchet_registry import (  # noqa: F401  (pytest fixtures)
    _edit_ruff,
    _f,
    _rows,
    _run,
    _scan_arg,
    repo,
    seeded,
)
from codebase.health.ratchet import DEFAULT_REPORT_LIMIT, compare, format_summary


def _result(baseline, current):
    return compare(current, _rows(baseline))


def test_a_pass_is_one_line():
    findings = [_f("a.py", "F401", 3)]
    text = format_summary(_result(findings, findings))
    assert text.count("\n") == 0 and "OK" in text and "advisory" in text


def test_violations_in_changed_files_are_listed_before_the_rest():
    baseline = [_f("a.py", "F401", 1)]
    current = [*baseline, _f("other.py", "E722", 1, line=4), _f("mine.py", "E722", 2, line=9)]
    text = format_summary(_result(baseline, current), ["mine.py"])
    assert text.index("In files this PR changed") < text.index("mine.py") < text.index("Elsewhere") < text.index("other.py")
    assert "2 new, 0 worse" in text and "does not fail the PR" in text


def test_a_worse_value_is_reported_with_its_ceiling():
    baseline = [_f("a.py", "F401", 1)]
    text = format_summary(_result(baseline, [_f("a.py", "F401", 4)]), ["a.py"])
    assert "WORSE 4 > ceiling 1" in text


def test_with_no_changed_files_everything_is_elsewhere():
    text = format_summary(_result([], [_f("x.py", "E722", 1)]), [])
    assert "In files this PR changed" not in text and "Elsewhere" in text


def test_each_list_is_capped():
    current = [_f(f"f{i}.py", "E722", 1) for i in range(DEFAULT_REPORT_LIMIT + 5)]
    text = format_summary(_result([], current), [])
    assert f"... and 5 more" in text and text.count("- `f") == DEFAULT_REPORT_LIMIT


def test_check_writes_the_summary_and_the_warning_but_keeps_the_exit_code(seeded, capsys):
    new = {"code": "E722", "filename": str(seeded / "sample_src" / "nested.py"), "location": {"row": 1, "column": 1}}
    _edit_ruff(seeded, lambda data: data.append(new))
    changed = seeded / "changed.txt"
    changed.write_text("sample_src/nested.py\n")
    out = seeded / "summary.md"
    out.write_text("earlier step output\n")
    code = _run(seeded, "check", *_scan_arg(seeded), "--summary-for", str(changed), "--summary-out", str(out), "--annotate")
    assert code == 1
    assert capsys.readouterr().out.count("::warning::code-health: 1 new/worse violations (advisory)") == 1
    text = out.read_text()
    assert text.startswith("earlier step output\n"), "the summary is appended, never overwritten"
    assert "In files this PR changed" in text and "nested.py" in text


def test_a_passing_check_writes_one_line_and_no_warning(seeded, capsys):
    out = seeded / "summary.md"
    assert _run(seeded, "check", *_scan_arg(seeded), "--summary-out", str(out), "--annotate") == 0
    assert "::warning::" not in capsys.readouterr().out
    assert len(out.read_text().strip().splitlines()) == 1


def test_without_the_new_flags_check_behaves_as_before(seeded, capsys):
    assert _run(seeded, "check", *_scan_arg(seeded)) == 0
    assert "::warning::" not in capsys.readouterr().out


def test_an_unusable_registry_still_writes_a_summary_line_and_a_warning_then_exits_2(seeded, capsys):
    (seeded / "reg.jsonl").write_text("{not json\n")
    out = seeded / "summary.md"
    out.write_text("earlier step output\n")
    assert _run(seeded, "check", *_scan_arg(seeded), "--summary-out", str(out), "--annotate") == 2
    captured = capsys.readouterr()
    assert "::warning::code-health could not run (advisory):" in captured.out
    assert "error:" in captured.err, "the original stderr error is still printed"
    text = out.read_text()
    assert text.startswith("earlier step output\n")
    assert "**Code health (advisory):** could not run:" in text and text.count("\n") == 2


def test_an_unusable_tool_still_writes_a_summary_line_and_a_warning_then_exits_2(repo, monkeypatch, capsys):
    from codebase.health import scan

    def broken(root, out_dir):
        raise scan.ToolUnavailableError("npx --yes jscpd@5.4.0 exited 1: registry unreachable\nsecond line")

    monkeypatch.setattr(scan, "run_scan", broken)
    out = repo / "summary.md"
    assert _run(repo, "check", "--summary-out", str(out), "--annotate") == 2
    warning = [l for l in capsys.readouterr().out.splitlines() if l.startswith("::warning::")]
    assert warning == ["::warning::code-health could not run (advisory): npx --yes jscpd@5.4.0 exited 1: registry unreachable second line"]
    assert out.read_text() == "**Code health (advisory):** could not run: npx --yes jscpd@5.4.0 exited 1: registry unreachable second line\n"


def test_without_the_flags_an_unusable_tool_prints_nothing_extra(repo, monkeypatch, capsys):
    from codebase.health import scan

    monkeypatch.setattr(scan, "run_scan", lambda root, out_dir: (_ for _ in ()).throw(scan.ToolUnavailableError("x not found")))
    assert _run(repo, "check") == 2
    assert "::warning::" not in capsys.readouterr().out
