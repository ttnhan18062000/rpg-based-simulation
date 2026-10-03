"""Strict local run of the real-Aseprite tests, with an evidence file (ADR D10, `make visual-assets-aseprite-local`).

Real Aseprite runs only on the licence holder's own machine. This runs `tests/visual_assets -m needs_aseprite` with
`VISUAL_ASSETS_REQUIRE_ASEPRITE=1` (a missing binary, a wrong version or any skip is a failure), under a 2 GB memory
cap when `systemd-run` is available, and writes `reports/visual_assets/aseprite_local_run.json` (gitignored run
output): git commit, UTC time, `aseprite --version`, and the passed/failed/errors/skipped/total counts. Exit code is
non-zero on any failure, any skip, or an empty run.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tools.ci_junit_summary import JUnitSummary, parse_junit_xml

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "visual_assets"
EVIDENCE = OUT_DIR / "aseprite_local_run.json"
JUNIT = OUT_DIR / "aseprite_local_run.xml"
MEMORY_CAP = "MemoryMax=2G"


def build_evidence(summary: JUnitSummary, *, commit: str, now: datetime, version_output: str, pytest_rc: int) -> dict:
    ok = summary.parse_ok and pytest_rc == 0 and summary.total > 0 and not (
        summary.failed or summary.errors or summary.skipped
    )
    return {
        "commit": commit,
        "utc_time": now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aseprite_version": version_output,
        "passed": summary.passed,
        "failed": summary.failed,
        "errors": summary.errors,
        "skipped": summary.skipped,
        "total": summary.total,
        "duration_seconds": round(summary.duration_seconds, 2),
        "pytest_exit_code": pytest_rc,
        "ok": ok,
    }


def pytest_command(python: str, junit: Path, *, have_systemd_run: bool) -> list[str]:
    cmd = [python, "-m", "pytest", "tests/visual_assets", "-m", "needs_aseprite", "-q", "--tb=short", f"--junit-xml={junit}"]
    if have_systemd_run:
        return ["systemd-run", "--user", "--scope", "-p", MEMORY_CAP, "--quiet", *cmd]
    return cmd


def _git_commit() -> str:
    done = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=False)
    return done.stdout.strip() or "unknown"


def main() -> int:
    from tests.visual_assets import strict_aseprite
    from visual_assets.drawing import config

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JUNIT.unlink(missing_ok=True)
    env = {**os.environ, strict_aseprite.ENV_VAR: "1"}
    cmd = pytest_command(sys.executable, JUNIT, have_systemd_run=shutil.which("systemd-run") is not None)
    rc = subprocess.run(cmd, cwd=REPO, env=env, check=False).returncode
    evidence = build_evidence(
        parse_junit_xml(JUNIT),
        commit=_git_commit(),
        now=datetime.now(timezone.utc),
        version_output=strict_aseprite.read_version(str(config.ASEPRITE)),
        pytest_rc=rc,
    )
    EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
