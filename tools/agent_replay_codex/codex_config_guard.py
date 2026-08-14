"""Codex-config hook-free guard (TCK-20260721-CODEX-REPLAY-PARITY, Step 5).

Gives this ticket's own first-class, mechanical proof (not merely inherited from a different
ticket's test) that the real invocation never causes this repo's committed .codex/config.toml to
gain a hook registration or change at all — belt-and-suspenders on top of the scratch dir never
containing its own .codex/config.toml in the first place. Mirrors
tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py's walk logic (read,
not imported — that test module isn't an importable production module).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import ContainmentViolationError


def _walk_for_hooks_key(node, config_path: Path) -> None:
    if isinstance(node, dict):
        if "hooks" in node:
            raise ContainmentViolationError(
                f"{config_path}: found a 'hooks' key — production hook wiring is forbidden in "
                "the committed project config"
            )
        for value in node.values():
            _walk_for_hooks_key(value, config_path)
    elif isinstance(node, list):
        for item in node:
            _walk_for_hooks_key(item, config_path)


def assert_committed_config_hook_free(repo_root: Path) -> None:
    """Raises ContainmentViolationError if repo_root/.codex/config.toml exists and contains a
    'hooks' key anywhere at any nesting depth."""
    config_path = repo_root / ".codex" / "config.toml"
    if not config_path.exists():
        return
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    _walk_for_hooks_key(data, config_path)


def snapshot_config_bytes(repo_root: Path) -> bytes | None:
    """Returns raw bytes of repo_root/.codex/config.toml, or None if it doesn't exist."""
    config_path = repo_root / ".codex" / "config.toml"
    if not config_path.exists():
        return None
    return config_path.read_bytes()


def assert_config_bytes_unchanged(pre: bytes | None, post: bytes | None) -> None:
    """Raises ContainmentViolationError if pre != post."""
    if pre != post:
        raise ContainmentViolationError(
            "containment violation: .codex/config.toml bytes changed across the real Codex "
            "invocation"
        )
