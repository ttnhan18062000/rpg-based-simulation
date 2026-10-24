"""The Pyrefly advisory report (TCK-20261021-PYREFLY-ADVISORY-REPORT, parity ledger INFRA-TYPE-002).

Pyrefly is a second type-checker opinion that never blocks: the report exits 0 with new errors and 2 only when it cannot
run. Deterministic, no network: Pyrefly is replaced by a recorded JSON fixture or a tiny stand-in script.
"""

from __future__ import annotations

import json
import re
import stat
import tomllib
from pathlib import Path

import pytest
import yaml

from codebase.gates import pyrefly_report

ROOT = Path(__file__).resolve().parents[2]


def _error(name: str, path: str, line: int, text: str) -> dict[str, object]:
    return {"line": line, "column": 5, "path": path, "name": name, "concise_description": text, "severity": "error"}


FIXTURE = [
    _error("bad-argument-type", "src/a.py", 10, "Argument `str` is not assignable to `int`"),
    _error("missing-attribute", "src/b.py", 20, "Object of class `NoneType` has no attribute `x`"),
    _error("bad-return", "src/c.py", 30, "Returned type `str` is not assignable to `int`"),
    _error("bad-index", "src/d.py", 40, "Cannot index into `int`"),
    _error("unsupported-operation", "src/e.py", 50, "`+` is not supported"),
]


def _write(path: Path, errors: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"errors": errors}), encoding="utf-8")
    return path


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """A repository root whose baseline holds the first three fixture errors."""
    _write(tmp_path / pyrefly_report.DEFAULT_BASELINE, FIXTURE[:3])
    return tmp_path


def _fake_pyrefly(tmp_path: Path, stdout: str, code: int) -> str:
    script = tmp_path / "fake-pyrefly"
    script.write_text(f"#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'pyrefly 9.9.9'; exit 0; fi\ncat <<'EOF'\n{stdout}\nEOF\nexit {code}\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return str(script)


def test_summary_counts_new_errors_and_names_file_line_and_kind(root: Path, tmp_path: Path) -> None:
    new = _write(tmp_path / "out.json", FIXTURE[3:])
    summary = tmp_path / "summary.md"
    assert pyrefly_report.run(root, summary_out=summary, pyrefly_output=new) == 0
    text = summary.read_text(encoding="utf-8")
    assert "2 new errors" in text and "baseline holds 3 errors" in text and "### Pyrefly (advisory, never blocks)" in text
    assert "src/d.py:40:5 [bad-index]" in text and "src/e.py:50:5 [unsupported-operation]" in text


def test_no_new_errors_is_one_line(root: Path, tmp_path: Path) -> None:
    summary = tmp_path / "summary.md"
    assert pyrefly_report.run(root, summary_out=summary, pyrefly_output=_write(tmp_path / "out.json", [])) == 0
    assert "0 new errors (baseline holds 3 errors)" in summary.read_text(encoding="utf-8")


def test_new_errors_never_fail_the_report(root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    binary = _fake_pyrefly(tmp_path, json.dumps({"errors": FIXTURE[3:]}), code=1)
    assert pyrefly_report.run(root, executable=binary) == 0
    assert "src/d.py:40:5 [bad-index]" in capsys.readouterr().out


def test_summary_lists_at_most_the_limit(root: Path, tmp_path: Path) -> None:
    many = [_error("bad-index", "src/x.py", n, "Cannot index") for n in range(1, pyrefly_report.LIST_LIMIT + 6)]
    text = pyrefly_report.format_summary(many, 3, "1.3.2")
    assert "... and 5 more" in text and text.count("[bad-index]") == pyrefly_report.LIST_LIMIT


def test_exit_2_when_the_binary_is_missing(root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pyrefly_report.sys, "executable", str(tmp_path / "bin" / "python"))
    monkeypatch.setattr(pyrefly_report.shutil, "which", lambda _name: None)
    summary = tmp_path / "summary.md"
    assert pyrefly_report.run(root, summary_out=summary) == 2
    assert "could not run" in summary.read_text(encoding="utf-8").lower()


def test_exit_2_when_the_output_is_not_json(root: Path, tmp_path: Path) -> None:
    (tmp_path / "out.txt").write_text("INFO something broke", encoding="utf-8")
    assert pyrefly_report.run(root, pyrefly_output=tmp_path / "out.txt") == 2
    assert pyrefly_report.run(root, executable=_fake_pyrefly(tmp_path, "not json", code=1)) == 2


def test_exit_2_when_pyrefly_crashes(root: Path, tmp_path: Path) -> None:
    assert pyrefly_report.run(root, executable=_fake_pyrefly(tmp_path, '{"errors": []}', code=3)) == 2


def test_exit_2_with_a_missing_or_empty_baseline_never_a_silent_zero(tmp_path: Path) -> None:
    out = _write(tmp_path / "out.json", [])
    assert pyrefly_report.run(tmp_path, pyrefly_output=out) == 2
    _write(tmp_path / pyrefly_report.DEFAULT_BASELINE, [])
    assert pyrefly_report.run(tmp_path, pyrefly_output=out) == 2


def test_pyrefly_excludes_equal_the_mypy_excludes() -> None:
    tool = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]
    mypy = {f"{entry.rstrip('/')}/**" for entry in tool["mypy"]["exclude"]}
    assert set(tool["pyrefly"]["project-excludes"]) == mypy
    assert tool["pyrefly"]["project-includes"] == ["src/**/*.py"]


def test_the_ci_step_is_last_advisory_and_in_the_existing_code_health_job() -> None:
    jobs = yaml.safe_load((ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8"))["jobs"]
    assert not [name for name, job in jobs.items() if "pyrefly" in name or "pyrefly" in str(job.get("name", "")).lower()], (
        "Pyrefly is a step of the Code health job, not a job of its own (test.yml is held to its job count)"
    )
    job = jobs["code-health"]
    assert job["name"] == "Code health" and "continue-on-error" not in job
    step = job["steps"][-1]
    assert step["name"] == pyrefly_report.SUMMARY_HEADING
    assert step["continue-on-error"] is True and step["timeout-minutes"] <= 3
    assert "pyrefly_report" in step["run"] and "annotate" not in step["run"] and "github." not in step["run"]
    assert {s["name"] for s in job["steps"] if s.get("continue-on-error")} == {"Paths this PR changed", step["name"]}
    assert "pyrefly" not in json.dumps(jobs["typecheck"]).lower(), "the Type check job is mypy's"


def test_makefile_targets_exist_and_say_advisory() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    phony = next(line for line in makefile.splitlines() if line.startswith(".PHONY:")).split()
    for target in ("typecheck-pyrefly", "typecheck-pyrefly-baseline-sync"):
        assert target in phony
        help_line = re.search(rf"^{target}:.*## (.*)$", makefile, re.MULTILINE)
        assert help_line and "advisory" in help_line.group(1)


def test_the_committed_baseline_is_nonempty_and_never_written_by_suppress() -> None:
    entries = pyrefly_report.baseline_entries(ROOT)
    assert entries > 0
    assert "pyrefly: ignore" not in "".join(p.read_text(encoding="utf-8", errors="ignore") for p in (ROOT / "src").rglob("*.py"))
