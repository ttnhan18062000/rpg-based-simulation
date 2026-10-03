"""Strict mode for the real-Aseprite tests (ADR D10): a missing or wrong-version binary fails instead of skipping.

The unit tests cover the rules as pure functions. The subprocess tests run real pytest on one `needs_aseprite`
file (`test_summary_facts.py`) so the conftest wiring itself is proven, not only the helper. No Aseprite needed.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.visual_assets import strict_aseprite as strict
from tools import visual_assets_aseprite_local as local
from tools.ci_junit_summary import JUnitSummary

REPO = Path(__file__).resolve().parents[2]
TARGET = "tests/visual_assets/drawing/integration/test_summary_facts.py"
PINNED = "1.3.18.6"


def test_strict_requested_only_for_exactly_one():
    assert strict.strict_requested({strict.ENV_VAR: "1"})
    assert not strict.strict_requested({})
    assert not strict.strict_requested({strict.ENV_VAR: "0"})
    assert not strict.strict_requested({strict.ENV_VAR: "true"})


def test_parse_version():
    assert strict.parse_version("Aseprite 1.3.18.6-x64") == PINNED
    assert strict.parse_version("garbage") is None


@pytest.mark.parametrize(
    ("kwargs", "needle"),
    [
        ({"binary_present": False}, "binary is missing"),
        ({"bwrap_present": False}, "bwrap is missing"),
        ({"version_output": "Aseprite 9.9.9-x64"}, "9.9.9"),
        ({"version_output": ""}, "pinned"),
    ],
)
def test_strict_problem_names_the_cause(kwargs, needle):
    facts = {"binary_present": True, "bwrap_present": True, "version_output": f"Aseprite {PINNED}-x64"}
    assert needle in strict.strict_problem(**{**facts, **kwargs}, pinned=PINNED)


def test_strict_problem_none_when_all_present_and_pinned():
    assert strict.strict_problem(
        binary_present=True, bwrap_present=True, version_output=f"Aseprite {PINNED}-x64", pinned=PINNED
    ) is None


def _run_pytest(tmp_path: Path, binary: str, *, strict_on: bool) -> tuple[dict[str, int], str]:
    junit = tmp_path / "out.xml"
    env = {k: v for k, v in os.environ.items() if k != strict.ENV_VAR}
    env["ASEPRITE_MCP_BINARY"] = binary
    if strict_on:
        env[strict.ENV_VAR] = "1"
    subprocess.run(
        [sys.executable, "-m", "pytest", TARGET, "-m", "needs_aseprite", "-q", "-p", "no:cacheprovider", f"--junit-xml={junit}"],
        cwd=REPO, env=env, capture_output=True, text=True, check=False, timeout=300,
    )
    suite = ET.parse(junit).getroot().find("testsuite")
    counts = {k: int(suite.get(k)) for k in ("tests", "failures", "errors", "skipped")}
    assert counts["tests"] > 0
    return counts, junit.read_text()


def _failing_with(report: str, needle: str) -> int:
    """How many testcases carry a failure or error whose message contains `needle`."""
    cases = ET.fromstring(report).iter("testcase")
    return sum(
        1
        for case in cases
        if any(needle in (child.get("message") or "") for child in case if child.tag in ("failure", "error"))
    )


def test_strict_missing_binary_fails_every_test_and_skips_none(tmp_path):
    counts, report = _run_pytest(tmp_path, "/nonexistent/aseprite", strict_on=True)
    assert _failing_with(report, "strict mode: the Aseprite binary is missing") == counts["tests"]  # right reason
    assert counts["skipped"] == 0
    assert counts["failures"] + counts["errors"] == counts["tests"]


def test_default_missing_binary_skips_every_test(tmp_path):
    counts, _ = _run_pytest(tmp_path, "/nonexistent/aseprite", strict_on=False)
    assert counts["skipped"] == counts["tests"]
    assert counts["failures"] + counts["errors"] == 0


def test_strict_wrong_reported_version_fails_the_session(tmp_path):
    fake = tmp_path / "aseprite"
    fake.write_text("#!/bin/sh\necho 'Aseprite 9.9.9-x64'\n")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    counts, report = _run_pytest(tmp_path, str(fake), strict_on=True)
    assert _failing_with(report, "reports version '9.9.9', pinned '1.3.18.6'") == counts["tests"]
    assert counts["skipped"] == 0
    assert counts["failures"] + counts["errors"] == counts["tests"]


def _summary(**kw) -> JUnitSummary:
    base = {"total": 10, "passed": 10, "failed": 0, "errors": 0, "skipped": 0, "duration_seconds": 1.0, "parse_ok": True}
    return JUnitSummary(**{**base, **kw})


def _evidence(summary: JUnitSummary, rc: int = 0) -> dict:
    return local.build_evidence(
        summary, commit="abc", now=datetime(2026, 10, 3, tzinfo=timezone.utc), version_output="Aseprite 1.3.18.6-x64", pytest_rc=rc
    )


def test_evidence_fields_and_ok():
    ev = _evidence(_summary())
    assert ev["ok"] is True
    assert {"commit", "utc_time", "aseprite_version", "passed", "failed", "skipped", "total"} <= set(ev)
    assert ev["utc_time"] == "2026-10-03T00:00:00Z"


@pytest.mark.parametrize(
    "summary",
    [_summary(skipped=1, passed=9), _summary(failed=1, passed=9), _summary(errors=1, passed=9), _summary(total=0, passed=0), _summary(parse_ok=False)],
)
def test_evidence_not_ok_on_skip_failure_or_empty(summary):
    assert _evidence(summary)["ok"] is False


def test_evidence_not_ok_on_nonzero_pytest_exit():
    assert _evidence(_summary(), rc=1)["ok"] is False


def test_pytest_command_adds_memory_cap_only_with_systemd_run():
    junit = Path("j.xml")
    capped = local.pytest_command("py", junit, have_systemd_run=True)
    assert capped[:5] == ["systemd-run", "--user", "--scope", "-p", "MemoryMax=2G"]
    assert local.pytest_command("py", junit, have_systemd_run=False)[0] == "py"
    assert "needs_aseprite" in capped
