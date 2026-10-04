"""Tests for the pre-commit ratchet check (TCK-20261003-PREK-GIT-HOOKS-OPT-IN): `codebase.gates.staged_ratchet`.

Real ruff runs in a temporary project; the registry is hand-written so each case is explicit.
"""
from __future__ import annotations

import importlib.util

import pytest

from codebase.gates import staged_ratchet
from codebase.health import registry
from codebase.health.registry import Row
from codebase.gates.staged_ratchet import run

_PYPROJECT = '[tool.ruff.lint]\nselect = ["E722"]\n'
_BARE = "def f():\n    try:\n        pass\n    except:\n        pass\n"


def _row(file, rule, ceiling):
    return Row(file, None, "ruff", rule, ceiling, ceiling, "2026-10-03", False, None)


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "codebase" / "baselines").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT)
    (tmp_path / "src" / "a.py").write_text(_BARE)
    (tmp_path / "src" / "b.py").write_text("x = 1\n")
    registry.write_rows(tmp_path / "codebase" / "baselines" / "code_health_exceptions.jsonl", [_row("src/a.py", "E722", 1)])
    return tmp_path


def test_a_file_whose_violations_are_all_grandfathered_passes(project, capsys):
    assert run(project, ["src/a.py"]) == 0
    assert capsys.readouterr().out == ""


def test_a_new_violation_in_a_file_without_a_row_is_rejected_with_the_ratchet_message(project, capsys):
    (project / "src" / "b.py").write_text(_BARE)
    assert run(project, ["src/b.py"]) == 1
    out = capsys.readouterr().out
    assert "NEW violations (no baseline row) (1):" in out and "src/b.py" in out and "[ruff E722]" in out
    assert "FAIL: 1 new, 0 worse" in out and "git commit --no-verify" in out


def test_a_violation_above_the_row_ceiling_is_rejected_as_worse(project, capsys):
    (project / "src" / "a.py").write_text(_BARE + "\n" + _BARE.replace("def f", "def g"))
    assert run(project, ["src/a.py"]) == 1
    assert "WORSE than baseline (1):" in capsys.readouterr().out


def test_a_violation_at_its_ceiling_and_a_fixed_one_both_pass(project):
    assert run(project, ["src/a.py"]) == 0
    (project / "src" / "a.py").write_text("x = 1\n")
    assert run(project, ["src/a.py"]) == 0, "paid-off debt is never a failure"


def test_only_the_staged_files_are_checked(project):
    (project / "src" / "b.py").write_text(_BARE)
    assert run(project, ["src/a.py"]) == 0, "b.py is not staged, so its new violation is not this commit's business"


def test_files_outside_src_and_unsafe_paths_are_ignored(project):
    (project / "tests").mkdir()
    (project / "tests" / "t.py").write_text(_BARE)
    assert run(project, ["tests/t.py", "README.md", "-rf", "src/../tests/t.py", "src/missing.py"]) == 0
    assert run(project, []) == 0


def test_a_missing_registry_skips_with_a_visible_line_instead_of_blocking(project, capsys):
    (project / "codebase" / "baselines" / "code_health_exceptions.jsonl").unlink()
    (project / "src" / "b.py").write_text(_BARE)
    assert run(project, ["src/b.py"]) == 0
    assert capsys.readouterr().out.startswith("code-health hook skipped: no code-health registry")


def test_an_unusable_registry_skips_with_a_visible_line(project, capsys):
    (project / "codebase" / "baselines" / "code_health_exceptions.jsonl").write_text("{not json\n")
    assert run(project, ["src/a.py"]) == 0
    assert capsys.readouterr().out.startswith("code-health hook skipped: the code-health registry is unusable")


def test_a_python_without_ruff_skips_with_a_visible_line(project, monkeypatch, capsys):
    real = importlib.util.find_spec
    monkeypatch.setattr(staged_ratchet.importlib.util, "find_spec", lambda name, *a: None if name == "ruff" else real(name, *a))
    (project / "src" / "b.py").write_text(_BARE)
    assert run(project, ["src/b.py"]) == 0
    assert "code-health hook skipped: ruff is not installed for this Python (environment not synced: uv sync)" in capsys.readouterr().out
