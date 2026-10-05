"""Shared scratch-repository fixtures and helpers for the code-health ratchet tests.

`repo` is a scratch repository with the sample source, a config and a staged scan; `seeded` is the same
repository after `seed`. `test_code_health_ratchet_registry.py`, `test_code_health_ci_summary.py` and
`test_code_health_blocking_policy.py` use them (testing review of PR #329: share fixtures through a conftest).
The helpers are plain functions the test modules import by name.
"""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from codebase.health import registry
from codebase.health.__main__ import main
from codebase.health.findings import Finding
from codebase.health.registry import Row

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "code_health"
_TODAY = date(2026, 10, 2)


def _f(file: str, rule: str, value: int, symbol: str | None = None, tool: str = "ruff", line: int | None = None) -> Finding:
    return Finding(file, symbol, tool, rule, value, line)


def _rows(findings: list[Finding]) -> list[Row]:
    return registry.seed_rows(findings, _TODAY)


@pytest.fixture
def repo(tmp_path):
    """A scratch repository with the sample source, a config, and a staged scan of it."""
    shutil.copytree(_FIXTURES / "sample_src", tmp_path / "sample_src")
    (tmp_path / "pyproject.toml").write_text("[tool.complexipy]\nmax-complexity-allowed = 15\n")
    scan_dir = tmp_path / "scan"
    (scan_dir / "jscpd").mkdir(parents=True)
    ruff = (_FIXTURES / "ruff.json").read_text().replace("/FIXTURE_ROOT", str(tmp_path))
    (scan_dir / "ruff.json").write_text(ruff)
    shutil.copy(_FIXTURES / "complexipy.json", scan_dir / "complexipy.json")
    shutil.copy(_FIXTURES / "line_count.json", scan_dir / "line_count.json")
    shutil.copy(_FIXTURES / "ast_grep.json", scan_dir / "ast_grep.json")
    shutil.copy(_FIXTURES / "jscpd-report.json", scan_dir / "jscpd" / "jscpd-report.json")
    return tmp_path


def _run(repo: Path, *args: str) -> int:
    # The sample's jscpd names are relative to sample_src, so that is the scanned directory here.
    return main(["--root", str(repo), "--registry", str(repo / "reg.jsonl"), "--scan-root", "sample_src", *args])


def _scan_arg(repo: Path) -> list[str]:
    return ["--from", str(repo / "scan")]


def _edit_ruff(repo: Path, edit) -> None:
    path = repo / "scan" / "ruff.json"
    data = json.loads(path.read_text())
    edit(data)
    path.write_text(json.dumps(data))


@pytest.fixture
def seeded(repo):
    assert _run(repo, "seed", *_scan_arg(repo)) == 0
    return repo
