"""Tests for the advisory edit hook (TCK-20261004-EDIT-RATCHET-HOOK): `codebase.hooks.edit_ratchet_hook`.

Real ruff runs in a temporary project (as in test_code_health_staged_ratchet.py). The hook must exit 0 and print
either one JSON object or nothing.
"""
from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from codebase.gates import staged_ratchet
from codebase.health import registry
from codebase.health.registry import Row
from codebase.hooks import edit_ratchet_hook as hook

_BARE = "def f():\n    try:\n        pass\n    except:\n        pass\n"
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _row(file: str, rule: str, ceiling: int) -> Row:
    return Row(file, None, "ruff", rule, ceiling, ceiling, "2026-10-03", False, None)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A scratch repo with one grandfathered file (`src/a.py`) and one clean file (`src/b.py`)."""
    (tmp_path / "src").mkdir()
    (tmp_path / "codebase" / "baselines").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[tool.ruff.lint]\nselect = ["E722"]\n')
    (tmp_path / "src" / "a.py").write_text(_BARE)
    (tmp_path / "src" / "b.py").write_text("x = 1\n")
    registry.write_rows(tmp_path / "codebase" / "baselines" / "code_health_exceptions.jsonl", [_row("src/a.py", "E722", 1)])
    return tmp_path


def _payload(path: Path | str, tool: str = "Edit") -> dict:
    return {"tool_name": tool, "tool_input": {"file_path": str(path)}}


def test_new_violation_gives_additional_context(project: Path) -> None:
    """A new violation in the edited file yields one hook JSON object."""
    (project / "src" / "b.py").write_text(_BARE)
    out = hook.advice(_payload(project / "src" / "b.py"), project)
    data = json.loads(out)
    assert data["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    context = data["hookSpecificOutput"]["additionalContext"]
    assert "NEW violations" in context and "src/b.py" in context and "python_code_standard.md" in context


def test_worse_violation_gives_additional_context(project: Path) -> None:
    """A violation above its row ceiling is reported as WORSE."""
    (project / "src" / "a.py").write_text(_BARE + "\n" + _BARE.replace("def f", "def g"))
    assert "WORSE" in json.loads(hook.advice(_payload(project / "src" / "a.py"), project))["hookSpecificOutput"]["additionalContext"]


def test_grandfathered_and_clean_files_are_silent(project: Path) -> None:
    """Debt at its ceiling and a clean file produce no output."""
    assert hook.advice(_payload(project / "src" / "a.py"), project) is None
    assert hook.advice(_payload(project / "src" / "b.py", "Write"), project) is None


def test_relative_path_resolves_against_cwd(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A relative file_path is resolved from the working directory, then must sit inside the checkout."""
    (project / "src" / "b.py").write_text(_BARE)
    monkeypatch.chdir(project)
    assert hook.advice(_payload("src/b.py"), project) is not None


def test_output_is_capped(project: Path) -> None:
    """A long report is cut to 20 lines plus a count and the pointer line."""
    text = hook._context("\n".join(f"line {i}" for i in range(45)))
    lines = text.splitlines()
    assert lines[19] == "line 19" and lines[20] == "... and 25 more line(s)" and lines[-1] == hook.POINTER
    assert len(lines) == 22


@pytest.mark.parametrize(
    "make",
    [
        lambda p: _payload(p / "tests" / "t.py"),
        lambda p: _payload(p / "src" / "notes.txt"),
        lambda p: _payload(p / "src" / "missing.py"),
        lambda p: _payload(p / "src" / ".." / "tests" / "t.py"),
        lambda p: _payload(p.parent / "elsewhere.py"),
        lambda p: _payload(p / "src" / "b.py", "Read"),
        lambda p: {"tool_name": "Edit", "tool_input": {}},
        lambda p: {"tool_name": "Edit", "tool_input": {"file_path": 3}},
        lambda p: ["not", "a", "dict"],
        lambda p: None,
    ],
)
def test_other_edits_are_silent(project: Path, make: Callable[[Path], object]) -> None:
    """Non-src, non-py, missing, outside-the-repo and non-edit payloads give nothing, even if the file is bad."""
    (project / "tests").mkdir()
    (project / "tests" / "t.py").write_text(_BARE)
    (project.parent / "elsewhere.py").write_text(_BARE)
    (project / "src" / "b.py").write_text(_BARE)
    assert hook.advice(make(project), project) is None


def test_symlink_out_of_the_repo_is_silent(project: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    """A src file that is a symlink to a file outside the checkout is never linted."""
    outside = tmp_path_factory.mktemp("out") / "x.py"
    outside.write_text(_BARE)
    (project / "src" / "link.py").symlink_to(outside)
    assert hook.advice(_payload(project / "src" / "link.py"), project) is None


def test_missing_registry_and_missing_ruff_are_silent(project: Path) -> None:
    """The registry or ruff being unavailable is a skip, not output."""
    (project / "src" / "b.py").write_text(_BARE)
    (project / "codebase" / "baselines" / "code_health_exceptions.jsonl").unlink()
    assert hook.advice(_payload(project / "src" / "b.py"), project) is None


def _fake_python(path: Path, body: str) -> Path:
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def test_a_missing_ruff_is_a_skip_not_a_clean_pass(project: Path, tmp_path: Path) -> None:
    """Exit 1 with empty stdout and 'No module named ruff' must raise HookSkipped (shared with pre-commit)."""
    fake = _fake_python(tmp_path / "py", "echo 'No module named ruff' >&2; exit 1")
    with pytest.raises(staged_ratchet.HookSkipped, match="not installed"):
        staged_ratchet.check(project, ["src/a.py"], python=str(fake))


def test_the_time_budget_is_a_skip(project: Path, tmp_path: Path) -> None:
    """A ruff that outlives the budget raises HookSkipped, so the hook is silent."""
    fake = _fake_python(tmp_path / "py", "sleep 5")
    with pytest.raises(staged_ratchet.HookSkipped, match="could not run"):
        staged_ratchet.check(project, ["src/a.py"], python=str(fake), timeout=0.2)


def test_defaults_keep_the_precommit_behaviour(project: Path, capsys: pytest.CaptureFixture) -> None:
    """With no new arguments check() still rejects NEW and passes grandfathered code."""
    assert staged_ratchet.run(project, ["src/a.py"]) == 0
    (project / "src" / "b.py").write_text(_BARE)
    assert staged_ratchet.run(project, ["src/b.py"]) == 1
    assert "NEW violations" in capsys.readouterr().out


def test_unexpected_error_inside_the_hook_is_silent(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """main() swallows any exception and returns 0 with nothing printed."""
    monkeypatch.setattr(hook, "advice", lambda payload: 1 / 0)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(_payload("src/x.py"))))
    assert hook.main() == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("stdin", ["", "not json", "{", "[]", "null"])
def test_malformed_stdin_exits_zero_silently(stdin: str) -> None:
    """The real entry point, run as a subprocess, exits 0 and prints nothing for malformed input."""
    done = subprocess.run(
        [sys.executable, "-m", "codebase.hooks.edit_ratchet_hook"], input=stdin, capture_output=True, text=True,
        cwd=_REPO_ROOT, check=False,
    )
    assert (done.returncode, done.stdout) == (0, "")


def test_stdout_is_exactly_one_json_object(project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """For the NEW case main() prints one parseable JSON object and nothing else."""
    (project / "src" / "b.py").write_text(_BARE)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(_payload(project / "src" / "b.py"))))
    original = hook.advice
    monkeypatch.setattr(hook, "advice", lambda payload: original(payload, project))
    assert hook.main() == 0
    out = capsys.readouterr().out
    assert out.endswith("\n") and out.count("\n") == 1
    assert json.loads(out)["hookSpecificOutput"]["hookEventName"] == "PostToolUse"


def test_non_src_edit_does_not_import_the_health_modules() -> None:
    """The common path stays cheap: filtering happens before codebase.gates / codebase.health are imported."""
    code = (
        "import json,sys\nfrom codebase.hooks import edit_ratchet_hook as h\n"
        "assert h.advice({'tool_name':'Edit','tool_input':{'file_path':'/x/README.md'}}) is None\n"
        "assert not any(m.startswith(('codebase.gates','codebase.health')) for m in sys.modules)\n"
    )
    done = subprocess.run([sys.executable, "-c", code], cwd=_REPO_ROOT, capture_output=True, text=True, check=False,
                          env={**os.environ, "PYTHONPATH": str(_REPO_ROOT)})
    assert done.returncode == 0, done.stderr
