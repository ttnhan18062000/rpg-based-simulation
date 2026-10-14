"""Strict local run of the real-Aseprite tests, with an evidence file (ADR D10, `make visual-assets-aseprite-local`).

Real Aseprite runs only on the licence holder's own machine. This runs `tests/visual_assets -m needs_aseprite` with
`VISUAL_ASSETS_REQUIRE_ASEPRITE=1` (a missing binary, a wrong version or any skip is a failure), under a 2 GB memory
cap when `systemd-run` is available, and writes `reports/visual_assets/aseprite_local_run.json` (gitignored run
output): git commit, UTC time, `aseprite --version`, and the passed/failed/errors/skipped/total counts. Exit code is
non-zero on any failure, any skip, or an empty run.

After a clean, strict, COMPLETE run it also writes the committed proof record `docs/assets/aseprite_local_proof.json`
(`tools/visual_assets_aseprite_proof.py`; CI recomputes its guarded hash). The record is written ONLY for the full make target:
any extra pytest argument or a `PYTEST_ADDOPTS` that could select a subset means no record, and the runner says why. It is also
refused when a guarded file is modified or untracked, because the record names the commit the tests ran on.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tools import visual_assets_aseprite_proof as proof
from tools.ci_junit_summary import JUnitSummary, parse_junit_xml

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "reports" / "visual_assets"
EVIDENCE = OUT_DIR / "aseprite_local_run.json"
JUNIT = OUT_DIR / "aseprite_local_run.xml"
REBUILD_VERDICT = OUT_DIR / "aseprite_local_rebuild.json"  # written by the release rebuild test when VISUAL_ASSETS_REBUILD_VERDICT_OUT names it
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


def pytest_command(python: str, junit: Path, *, have_systemd_run: bool, extra_args: list[str] | None = None) -> list[str]:
    cmd = [python, "-m", "pytest", "tests/visual_assets", "-m", "needs_aseprite", "-q", "--tb=short", f"--junit-xml={junit}", *(extra_args or [])]
    if have_systemd_run:
        return ["systemd-run", "--user", "--scope", "-p", MEMORY_CAP, "--quiet", *cmd]
    return cmd


def _git_commit() -> str:
    done = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=False)
    return done.stdout.strip() or "unknown"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=False).stdout


def dirty_guarded_files() -> list[str]:
    """Guarded files that are modified, staged-but-different or untracked: the record would name a commit the tests did not run on."""
    tracked = proof.tracked_files(REPO)
    untracked = [p for p in _git("ls-files", "--others", "--exclude-standard", "-z").split("\0") if p]
    guarded = set(proof.guarded_paths(tracked + untracked, proof.marked_test_files(tracked + untracked, REPO)))
    modified = {line[3:] for line in _git("status", "--porcelain", "--untracked-files=no").splitlines() if len(line) > 3}
    return sorted(guarded & (modified | set(untracked)))


def read_rebuild_verdict() -> dict | None:
    try:
        data = json.loads(REBUILD_VERDICT.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_proof_record(evidence: dict, *, extra_args: list[str], env: dict[str, str]) -> str:
    """Write the committed record when this run qualifies; the returned sentence says what happened and why."""
    if not evidence["ok"]:
        return "no proof record written: the run was not clean and strict"
    reason = proof.selection_problem(extra_args, env)
    if reason:
        return f"no proof record written: this is not the full make target ({reason})"
    dirty = dirty_guarded_files()
    if dirty:
        return f"no proof record written: guarded files are not committed ({dirty[:5]}); commit them first, the record names the commit the tests ran on"
    rebuild = read_rebuild_verdict()
    if rebuild is None:
        return "no proof record written: the release rebuild verdict is missing (the rebuild test did not run or did not write it)"
    record = proof.build_record(
        run_commit=evidence["commit"], run_at_utc=evidence["utc_time"], aseprite_version=evidence["aseprite_version"],
        counts={k: evidence[k] for k in ("passed", "failed", "errors", "skipped", "total")}, rebuild=rebuild, files=proof.current_files(REPO),
    )
    problems = proof.record_problems(record)
    if problems:
        return f"no proof record written: the record would be invalid ({problems})"
    proof.RECORD_PATH.write_text(proof.dumps(record))
    shown = proof.RECORD_PATH.relative_to(REPO) if proof.RECORD_PATH.is_relative_to(REPO) else proof.RECORD_PATH
    return f"proof record written: {shown} (commit it; never edit it by hand)"


def main(argv: list[str] | None = None) -> int:
    from tests.visual_assets import strict_aseprite
    from visual_assets.drawing import config

    extra_args = list(sys.argv[1:] if argv is None else argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JUNIT.unlink(missing_ok=True)
    REBUILD_VERDICT.unlink(missing_ok=True)
    env = {**os.environ, strict_aseprite.ENV_VAR: "1", "VISUAL_ASSETS_REBUILD_VERDICT_OUT": str(REBUILD_VERDICT)}
    cmd = pytest_command(sys.executable, JUNIT, have_systemd_run=shutil.which("systemd-run") is not None, extra_args=extra_args)
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
    print(write_proof_record(evidence, extra_args=extra_args, env=dict(os.environ)))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
