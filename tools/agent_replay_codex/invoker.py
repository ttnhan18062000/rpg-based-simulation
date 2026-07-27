"""Invoker: wires the consent gate, entry criterion, containment, and real `codex exec`
invocation together (TCK-20260721-CODEX-REPLAY-PARITY, Step 6).

Never uses `--dangerously-bypass-approvals-and-sandbox` or `--dangerously-bypass-hook-trust`
(both confirmed present in `codex exec --help`) — these would defeat the sandbox/trust posture
this module relies on; they must never appear in this module under any code path.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .codex_config_guard import assert_config_bytes_unchanged, snapshot_config_bytes
from .consent_gate import require_live_consent
from .containment import (
    assert_monitoring_prefix_preserved,
    assert_no_diff,
    capture_snapshot,
    snapshot_monitoring_lines,
)
from .entry_criterion import assert_monitoring_writer_landed
from .errors import CodexInvocationError


@dataclass(frozen=True)
class CodexReplayOutcome:
    final_status: str
    phases_completed: list[str]
    scratch_dir: Path  # left on disk, not auto-deleted — auditable per this ticket's own AC wording


def run_codex_replay(
    fixture_path: Path,
    *,
    repo_root: Path,
    env: Mapping[str, str] | None = None,
    timeout_s: float = 300.0,
) -> CodexReplayOutcome:
    require_live_consent(env)  # consent — literal first check, strictly before any subprocess object exists
    assert_monitoring_writer_landed(repo_root / "tools")  # entry criterion, checked next

    scratch_dir = Path(tempfile.mkdtemp(prefix="codex-replay-parity-"))
    out_path = scratch_dir / "codex_result.json"

    pre_tickets = capture_snapshot(repo_root)
    pre_monitoring = snapshot_monitoring_lines(repo_root / "agent-monitoring")
    pre_config = snapshot_config_bytes(repo_root)

    wrapper_path = Path(__file__).resolve().parent / "wrapper_script.py"
    command = [
        "codex", "exec",
        "-C", str(scratch_dir),
        "-s", "workspace-write",
        "--skip-git-repo-check",
        f"Run: {sys.executable} {wrapper_path} --fixture {fixture_path.resolve()} --out {out_path}",
    ]
    result = subprocess.run(
        command, cwd=str(scratch_dir), capture_output=True, text=True, timeout=timeout_s
    )

    post_tickets = capture_snapshot(repo_root)
    post_monitoring = snapshot_monitoring_lines(repo_root / "agent-monitoring")
    post_config = snapshot_config_bytes(repo_root)

    assert_no_diff(pre_tickets, post_tickets)  # raises ContainmentViolationError, never swallowed
    assert_monitoring_prefix_preserved(pre_monitoring, post_monitoring)
    assert_config_bytes_unchanged(pre_config, post_config)

    if result.returncode != 0 or not out_path.exists():
        raise CodexInvocationError(f"codex exec failed (rc={result.returncode}): {result.stderr[-2000:]}")

    parsed = json.loads(out_path.read_text(encoding="utf-8"))
    return CodexReplayOutcome(
        final_status=parsed["final_status"],
        phases_completed=parsed["phases_completed"],
        scratch_dir=scratch_dir,
    )
