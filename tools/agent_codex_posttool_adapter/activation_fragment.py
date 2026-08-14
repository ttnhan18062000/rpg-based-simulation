"""Proposed PostToolUse hook activation fragment — reviewable, never invoked (Step 8).

PROPOSED_HOOK_BLOCK is a deliberate inert no-op placeholder (`command = "true"`), the same
discipline tools/agent_codex_pilot_guardrails/config_toggle.py::_HOOK_BLOCK already uses. The real
invocation command is deferred to a future activation ticket because
agent-orchestration/hook-surface-policy.yaml's `human_approval`, `project_trust_review`, and
`hook_trust_review` activation_prerequisites remain unmet by this ticket.

`render_proposed_fragment` is pure append and is never called against a real path anywhere in
this package's own source. This module does not modify or import from
`agent_codex_pilot_guardrails.config_toggle` (scope guard) — `assert_scratch_target` below is an
independently-implemented guard mirroring `config_toggle.py::_assert_scratch_target`'s discipline
without importing it.
"""
from __future__ import annotations

from pathlib import Path

from .errors import ActivationFragmentGuardError

PROPOSED_HOOK_BLOCK: bytes = b"""
[[hooks.PostToolUse]]
matcher = "*"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "true"
"""


def render_proposed_fragment(base_toml_bytes: bytes) -> bytes:
    """Pure append. Never called against a real path anywhere in this package."""
    return base_toml_bytes + PROPOSED_HOOK_BLOCK


def assert_scratch_target(path: Path, repo_root: Path) -> None:
    """Raise ActivationFragmentGuardError if path resolves to repo_root/.codex/config.toml."""
    real_config_path = (repo_root / ".codex" / "config.toml").resolve()
    if path.resolve() == real_config_path:
        raise ActivationFragmentGuardError(
            f"refusing to target the real committed config: {real_config_path}"
        )
