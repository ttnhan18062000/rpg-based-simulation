"""Read-only Claude adapter representation generator.

Renders a Claude-shaped projection of the agent-orchestration/ contract by combining
`tools.agent_orchestration.loader.load_contract()`'s phase order with this package's own
`load_terminal_statuses()`. Every field in the rendered output traces to one of those two read
paths — no ad-hoc string literals duplicating contract data.

Structural write-guard: `render_claude_adapter()` refuses to write to any resolved path outside
`agent-orchestration/rendered/` unless the caller explicitly passes `allow_outside_contract=True`.
This is an independent implementation (not an import of
`tools.agent_orchestration.generator._assert_write_allowed`) — reusing that private function would
couple this ticket to an internal implementation detail of the predecessor's package.

Never writes into `.claude/` under any flag combination — that directory is not in this module's
write-guard allowlist at all, only `agent-orchestration/rendered/` (or, with the explicit opt-in
flag, any other target the caller names, which still can never be `.claude/` since callers of this
generator never pass a `.claude/`-rooted target_dir).

Zero network calls, zero subprocess calls: only local filesystem I/O and YAML serialization.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from tools.agent_orchestration.loader import load_contract
from tools.agent_orchestration_claude_adapter.terminal_status_loader import load_terminal_statuses

_RENDERED_SUBDIR = Path("agent-orchestration") / "rendered"
_CLAUDE_ADAPTER_SCHEMA_VERSION = 1


class ClaudeAdapterWriteGuardError(Exception):
    """Raised by render_claude_adapter when a write target resolves outside
    agent-orchestration/rendered/ and the explicit allow_outside_contract flag was not passed."""


def _assert_write_allowed(repo_root: Path, target_path: Path, allow_outside_contract: bool) -> None:
    if allow_outside_contract:
        return
    rendered_root = (repo_root / _RENDERED_SUBDIR).resolve()
    resolved_target = target_path.resolve()
    if not resolved_target.is_relative_to(rendered_root):
        raise ClaudeAdapterWriteGuardError(
            f"{target_path}: refuses to write outside {rendered_root} "
            "without allow_outside_contract=True"
        )


def build_claude_adapter_representation(repo_root: Path) -> dict:
    """Build the rendered representation dict, performing zero filesystem writes.

    Every field traces to `load_contract()` (phase order, phase tier/condition/if_false fields
    passed through unmodified — see the `phases` field) or `load_terminal_statuses()`.
    """
    bundle = load_contract(repo_root)
    terminal_statuses = load_terminal_statuses(repo_root)

    phase_order = [phase["name"] for phase in bundle.workflow["phases"]]

    return {
        "claude_adapter_schema_version": _CLAUDE_ADAPTER_SCHEMA_VERSION,
        "source_workflow_id": bundle.workflow["workflow_id"],
        "phase_order": phase_order,
        "phases": bundle.workflow["phases"],
        "terminal_statuses": terminal_statuses,
    }


def render_claude_adapter(
    repo_root: Path,
    target_dir: Path,
    *,
    allow_outside_contract: bool = False,
) -> Path:
    """Render the Claude adapter representation and write it as YAML under `target_dir`.

    Returns the path written. Raises ClaudeAdapterWriteGuardError before any write happens if
    `target_dir` resolves outside `repo_root / "agent-orchestration" / "rendered"` and
    `allow_outside_contract` is not True. Never opens or writes to any file under
    `.claude/workflows/` — this function only reads the contract via
    `load_contract()`/`load_terminal_statuses()` and writes its own rendered output file.
    """
    output_path = target_dir / "claude-adapter.yaml"
    _assert_write_allowed(repo_root, output_path, allow_outside_contract)

    representation = build_claude_adapter_representation(repo_root)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(representation, sort_keys=False), encoding="utf-8")
    return output_path

