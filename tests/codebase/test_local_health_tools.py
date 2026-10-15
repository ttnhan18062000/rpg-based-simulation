"""A code-health tool that cannot run is loud, never clean (TCK-20261014-LOCAL-CODE-HEALTH-TOOLS).

`python -m ruff` exits 1 when ruff is not installed, which is also ruff's "findings" code, so the scan must
tell the two apart: real ruff always prints JSON (`[]` when clean), so empty stdout means it did not run.
"""
from __future__ import annotations

import stat
import subprocess
from pathlib import Path

import pytest

from codebase.gates import sarif_feedback
from codebase.health import scan
from codebase.structure import import_contracts as ic


def _fake_python(tmp_path: Path, stderr: str, code: int) -> str:
    script = tmp_path / "python-without-ruff"
    script.write_text(f"#!/bin/sh\necho '{stderr}' >&2\nexit {code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


def test_a_python_without_ruff_is_tool_unavailable_not_an_empty_ruff_json(tmp_path, monkeypatch):
    monkeypatch.setattr(scan.sys, "executable", _fake_python(tmp_path, "No module named ruff", 1))
    with pytest.raises(scan.ToolUnavailableError, match="No module named ruff"):
        scan._scan_ruff(tmp_path, tmp_path)
    assert not (tmp_path / scan.RUFF_JSON).exists()


@pytest.mark.parametrize("code", [0, 1])
def test_empty_ruff_output_is_tool_unavailable_whatever_the_stderr_and_exit_code(tmp_path, monkeypatch, code):
    monkeypatch.setattr(scan.sys, "executable", _fake_python(tmp_path, "segfault in a different way", code))
    with pytest.raises(scan.ToolUnavailableError, match="segfault"):
        scan._scan_ruff(tmp_path, tmp_path)
    assert not (tmp_path / scan.RUFF_JSON).exists()


def test_a_clean_ruff_run_still_writes_its_empty_json_array(tmp_path, monkeypatch):
    done = subprocess.CompletedProcess([], 0, stdout="[]\n", stderr="")
    monkeypatch.setattr(scan, "_run", lambda *args, **kwargs: done)
    scan._scan_ruff(tmp_path, tmp_path)
    assert (tmp_path / scan.RUFF_JSON).read_text() == "[]\n"


def test_empty_sarif_output_from_a_tool_is_a_sarif_error_not_a_clean_pass():
    with pytest.raises(sarif_feedback.SarifError):
        sarif_feedback.parse_sarif("", "ruff")


def test_report_runs_lint_imports_on_the_repo_config_and_returns_its_exit_code(tmp_path, monkeypatch):
    seen: list[list[str]] = []

    def fake_run(command, **kwargs):
        seen.append(list(command))
        assert "capture_output" not in kwargs, "report must pass lint-imports' output straight through"
        return subprocess.CompletedProcess(command, 7)

    monkeypatch.setattr(ic.subprocess, "run", fake_run)
    assert ic.main(["--root", str(tmp_path), "report", "--lint-imports", "LI"]) == 7
    assert seen == [["LI", "--config", str(tmp_path / ic.CONFIG_REL_PATH)]]


def test_report_that_cannot_start_lint_imports_exits_2(tmp_path, monkeypatch, capsys):
    def missing(command, **kwargs):
        raise FileNotFoundError(command[0])

    monkeypatch.setattr(ic.subprocess, "run", missing)
    assert ic.main(["--root", str(tmp_path), "report", "--lint-imports", "nope"]) == 2
    assert "could not run" in capsys.readouterr().out


def test_default_lint_imports_prefers_the_tool_beside_this_python_else_the_bare_name(monkeypatch):
    monkeypatch.setattr(ic, "find_tool", lambda name: f"/venv/bin/{name}")
    assert ic.default_lint_imports() == "/venv/bin/lint-imports"

    def unavailable(name):
        raise scan.ToolUnavailableError(name)

    monkeypatch.setattr(ic, "find_tool", unavailable)
    assert ic.default_lint_imports() == "lint-imports"
