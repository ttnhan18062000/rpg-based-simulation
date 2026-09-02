"""Config toggle mechanism (scratch-only) + rollback zero-byte-diff proof
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 5).

Builds the enable/disable *mechanism* as code — capable of producing a hook-registered config
when explicitly invoked — while the committed .codex/config.toml stays byte-identical to its
current hook-free state at this ticket's close, the same "capability built, live switch never
left flipped" discipline every sibling ticket in this batch already follows. Every function here
operates on an explicit scratch_config_path; _assert_scratch_target refuses to ever target the
real, committed config.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from tools.agent_replay_codex.monitoring_shards import hash_tools_source

from .errors import PilotConfigToggleGuardError, PilotRollbackVerificationError

# The empirically-discovered hook-registration TOML syntax, recorded in
# stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/ (tickets/done/
# TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md Implementation Notes, Step 11). `command = "true"`
# is a deliberate no-op placeholder: this mechanism is never wired to a real Codex invocation, so
# even if the rendered config were somehow used, the hook command is inert by construction.
_HOOK_BLOCK = b"""
[[hooks.PostToolUse]]
matcher = "*"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "true"
"""


def render_enabled_config(base_toml_bytes: bytes) -> bytes:
    """Append the hook-registration block to base_toml_bytes."""
    return base_toml_bytes + _HOOK_BLOCK


def _assert_scratch_target(path: Path, repo_root: Path) -> None:
    real_config_path = (repo_root / ".codex" / "config.toml").resolve()
    if path.resolve() == real_config_path:
        raise PilotConfigToggleGuardError(
            f"refusing to target the real committed config: {real_config_path}"
        )


def enable(scratch_config_path: Path, repo_root: Path) -> None:
    _assert_scratch_target(scratch_config_path, repo_root)
    scratch_config_path.write_bytes(render_enabled_config(scratch_config_path.read_bytes()))


def disable(scratch_config_path: Path, repo_root: Path, baseline_bytes: bytes) -> None:
    """Restore the exact pre-enable bytes — never a delete."""
    _assert_scratch_target(scratch_config_path, repo_root)
    scratch_config_path.write_bytes(baseline_bytes)


def snapshot_rollback_scope(agent_monitoring_dir: Path, pilot_ticket_path: Path) -> dict[str, str]:
    """sha256 of each of runs.jsonl/events.jsonl + the combined 'tools' source (a single legacy
    tools.jsonl, or the weekly agent-monitoring/tools/tools-*.jsonl shards) + pilot_ticket_path,
    whole-file.

    Strict hash-equality IS correct here, unlike the baseline-manifest gate's prefix-preservation
    check — the rollback drill must leave these files completely untouched, not merely
    append-safe.
    """
    watched = {
        "runs.jsonl": agent_monitoring_dir / "runs.jsonl",
        "events.jsonl": agent_monitoring_dir / "events.jsonl",
        "pilot_ticket": pilot_ticket_path,
    }
    scope = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in watched.items()}
    scope["tools.jsonl"] = hash_tools_source(agent_monitoring_dir)
    return scope


def assert_rollback_scope_unchanged(pre: dict[str, str], post: dict[str, str]) -> None:
    for name, pre_hash in pre.items():
        post_hash = post.get(name)
        if post_hash != pre_hash:
            raise PilotRollbackVerificationError(
                f"{name}: rollback scope changed (pre={pre_hash}, post={post_hash})"
            )
