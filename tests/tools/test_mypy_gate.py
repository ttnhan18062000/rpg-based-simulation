"""Tests for the advisory mypy gate (TCK-20261003-MYPY-BASELINE-ADVISORY).

The unit tests feed canned mypy output (`--mypy-output`). The end-to-end tests build a tiny project in tmp_path
with its own `[tool.mypy]` and `[tool.mypy_baseline]` and run the real mypy and mypy-baseline, so they prove the
behaviours the gate relies on: line numbers do not matter, a new error is reported alone, a repeated message is
new, a reworded note is not new, and a fixed-but-unsynced error does not fail.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tools.code_health import mypy_gate
from tools.code_health.mypy_gate import baseline_entries, format_summary, new_error_lines, run

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PYPROJECT = """\
[tool.mypy]
python_version = "3.11"
ignore_missing_imports = true

[tool.mypy_baseline]
baseline_path = "registries/mypy_baseline.txt"
allow_unsynced = true
hide_stats = true
ignore_categories = ["note", "annotation-unchecked"]
"""
_ERROR = 'src/a.py:{line}: error: Incompatible return value type (got "int", expected "str")  [return-value]'
_NOTE = "src/a.py:{line}: note: PEP 484 prohibits implicit Optional."


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "registries").mkdir()
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT)
    return tmp_path


def _sync(project: Path, output: str) -> None:
    done = subprocess.run(
        [sys.executable, "-m", "mypy_baseline", "sync"], cwd=project, input=output, text=True, capture_output=True
    )
    assert done.returncode == 0, done.stderr


def _gate(project: Path, output: str, *flags: str) -> int:
    saved = project / "mypy.out"
    saved.write_text(output)
    return run(project, project / "summary.md" if "summary" in flags else None, "annotate" in flags, saved)


def test_the_repository_declares_a_baseline_file_and_the_filter_config():
    assert baseline_entries(_REPO_ROOT) > 0
    assert mypy_gate.baseline_path(_REPO_ROOT).relative_to(_REPO_ROOT).as_posix() == "registries/mypy_baseline.txt"


def test_summary_is_one_line_with_the_baseline_size_when_nothing_is_new():
    text = format_summary([], 1569)
    assert text == "**mypy (advisory):** 0 new errors (baseline holds 1569 entries)."


def test_summary_lists_new_errors_with_a_cap():
    errors = [f"src/x.py:{i}: error: boom  [misc]" for i in range(30)]
    text = format_summary(errors, 10)
    assert "30 new errors (baseline holds 10 entries)" in text and "... and 5 more" in text
    assert text.count("src/x.py") == mypy_gate.LIST_LIMIT


def test_only_error_lines_count_as_new():
    assert new_error_lines("src/a.py:1: error: x  [misc]\nsrc/a.py:1: note: hint\n\n") == ["src/a.py:1: error: x  [misc]"]


def test_an_unrelated_edit_above_an_existing_error_does_not_resurface_it(project):
    _sync(project, _ERROR.format(line=3) + "\n")
    assert _gate(project, _ERROR.format(line=43) + "\n", "summary") == 0
    assert (project / "summary.md").read_text() == "**mypy (advisory):** 0 new errors (baseline holds 1 entries).\n"


def test_a_genuinely_new_error_is_reported_alone_with_a_warning(project, capsys):
    _sync(project, _ERROR.format(line=3) + "\n")
    new = 'src/b.py:9: error: Name "x" is not defined  [name-defined]'
    assert _gate(project, _ERROR.format(line=3) + "\n" + new + "\n", "summary", "annotate") == 1
    out = capsys.readouterr().out
    assert new in out and _ERROR.format(line=3) not in out
    assert "::warning::mypy-baseline: 1 new errors (advisory); see job summary" in out
    assert "1 new errors (baseline holds 1 entries)" in (project / "summary.md").read_text()


def test_a_repeated_identical_message_in_the_same_file_is_new(project):
    _sync(project, _ERROR.format(line=3) + "\n")
    assert _gate(project, _ERROR.format(line=3) + "\n" + _ERROR.format(line=8) + "\n") == 1


def test_a_changed_note_alone_is_not_a_new_error(project):
    _sync(project, _ERROR.format(line=3) + "\n" + _NOTE.format(line=3) + "\n")
    reworded = _NOTE.format(line=3).replace("prohibits", "now prohibits")
    assert _gate(project, _ERROR.format(line=3) + "\n" + reworded + "\n") == 0


def test_a_standalone_annotation_unchecked_note_is_not_baselined_or_reported(project):
    note = "src/a.py:5: note: By default the bodies of untyped functions are not checked  [annotation-unchecked]"
    _sync(project, _ERROR.format(line=3) + "\n" + note + "\n")
    assert baseline_entries(project) == 1
    assert _gate(project, _ERROR.format(line=3) + "\n" + note + "\n" + note.replace(":5:", ":9:") + "\n") == 0


def test_a_fixed_error_that_was_not_re_synced_does_not_fail_the_gate(project):
    _sync(project, _ERROR.format(line=3) + "\n")
    assert _gate(project, "") == 0


def test_a_missing_baseline_is_reported_as_could_not_run(project, capsys):
    assert _gate(project, "", "summary", "annotate") == 2
    out = capsys.readouterr().out
    assert "::warning::mypy-baseline could not run (advisory): baseline registries/mypy_baseline.txt does not exist" in out
    assert (project / "summary.md").read_text().startswith("**mypy (advisory):** could not run: baseline")


def test_mypy_crashing_is_reported_as_could_not_run_and_the_summary_is_appended(project, monkeypatch, capsys):
    _sync(project, _ERROR.format(line=3) + "\n")
    (project / "summary.md").write_text("earlier step\n")

    def boom(command, root, ok_codes, stdin=None):
        raise mypy_gate.GateCannotRun("-m mypy exited 2: INTERNAL ERROR\nsecond line")

    monkeypatch.setattr(mypy_gate, "_run", boom)
    assert run(project, project / "summary.md", True, None) == 2
    assert "::warning::mypy-baseline could not run (advisory): -m mypy exited 2: INTERNAL ERROR second line" in capsys.readouterr().out
    assert (project / "summary.md").read_text() == "earlier step\n**mypy (advisory):** could not run: -m mypy exited 2: INTERNAL ERROR second line\n"


def test_the_whole_gate_runs_real_mypy_on_a_tiny_project(project):
    (project / "src" / "a.py").write_text(textwrap.dedent("""\
        def f() -> str:
            return 1
    """))
    first = subprocess.run([sys.executable, "-m", "mypy", "src/", "--config-file", "pyproject.toml", "--no-error-summary"],
                           cwd=project, capture_output=True, text=True)
    assert first.returncode == 1 and "return-value" in first.stdout
    _sync(project, first.stdout)
    assert run(project) == 0
    (project / "src" / "a.py").write_text("\n\n# an unrelated edit above\n" + (project / "src" / "a.py").read_text())
    assert run(project) == 0, "an unrelated edit above an existing error must not resurface it"
    (project / "src" / "a.py").write_text((project / "src" / "a.py").read_text() + "\ndef g() -> str:\n    return 2\n")
    assert run(project) == 1, "a genuinely new error is reported"
