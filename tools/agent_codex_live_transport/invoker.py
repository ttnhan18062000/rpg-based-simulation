"""Fixed-argv subprocess transport; actual use remains separately authorized."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

from tools.agent_codex_realrepo_pilot_harness.authority import _LivePilotAuthority, issue_live_authority
from tools.agent_codex_realrepo_pilot_harness.boundary import _invoke_live_after_authority
from tools.agent_codex_realrepo_pilot_harness.live_preflight import LivePreflightResult


@dataclass(frozen=True)
class LiveTransportOutcome:
    returncode: int
    stdout: str
    stderr: str
    started_at_iso: str
    ended_at_iso: str


def _hook_environment(preflight: LivePreflightResult) -> dict[str, str]:
    """Thread reviewed identity only; all consent grants stay ambient and human-set."""
    context = preflight.context
    env = dict(os.environ)
    env.update({
        "CODEX_HOOK_EXECUTION_ID": context.execution_id,
        "CODEX_HOOK_TICKET_ID": context.ticket_id,
        "CODEX_HOOK_RUN_ID": context.ticket_id,
        "CODEX_HOOK_SEQ_START": "1",
        "CODEX_HOOK_PHASE": "PostToolUse",
        "CODEX_HOOK_AGENT": "codex-posttool-hook",
    })
    return env


def _fixed_instruction(preflight: LivePreflightResult) -> str:
    """Build the sole fixed prompt from already-validated evidence fields."""
    return (
        "Execute only the reviewed controlled-pilot operation described by the "
        "validated evidence. Do not enable hooks or broaden scope.\n"
        f"ticket_id={json.dumps(preflight.context.ticket_id)}\n"
        f"candidate_path={json.dumps(preflight.context.candidate_path)}\n"
        f"policy_path={json.dumps(preflight.context.policy_path)}\n"
    )


def _fixed_argv(root: Path, preflight: LivePreflightResult) -> list[str]:
    return [
        "codex",
        "exec",
        "-C",
        str(root),
        "-s",
        "workspace-write",
        "--skip-git-repo-check",
        _fixed_instruction(preflight),
    ]


def invoke_live_transport(
    authority: _LivePilotAuthority | None,
    preflight: LivePreflightResult | None,
) -> LiveTransportOutcome:
    issue_live_authority(os.environ)
    if not isinstance(authority, _LivePilotAuthority):
        raise PermissionError("live pilot authority is required before transport construction")
    if not isinstance(preflight, LivePreflightResult):
        raise PermissionError("captured live preflight is required before transport construction")

    def _invoke(root: Path) -> LiveTransportOutcome:
        started_at_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        result = subprocess.run(
            _fixed_argv(root, preflight),
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300.0,
            shell=False,
            env=_hook_environment(preflight),
        )
        ended_at_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return LiveTransportOutcome(result.returncode, result.stdout, result.stderr, started_at_iso, ended_at_iso)

    return _invoke_live_after_authority(authority, preflight, _invoke)
