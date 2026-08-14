"""AC #6 direct verification: no production hook is enabled in the committed .codex/config.toml.

First-class assertion owned by this ticket's own test tree — not merely inherited via the
cross-ticket edit to tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONFIG_PATH = _REPO_ROOT / ".codex" / "config.toml"


def _walk_for_hooks_key(node) -> None:
    if isinstance(node, dict):
        assert "hooks" not in node, (
            f"{_CONFIG_PATH}: found a 'hooks' key — production hook wiring is forbidden "
            "in the committed project config"
        )
        for value in node.values():
            _walk_for_hooks_key(value)
    elif isinstance(node, list):
        for item in node:
            _walk_for_hooks_key(item)


def test_no_production_hook_registered_in_committed_codex_config():
    assert _CONFIG_PATH.is_file(), f"{_CONFIG_PATH} must exist (Step 13)"
    with open(_CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)
    _walk_for_hooks_key(data)


def test_committed_codex_config_parses_to_empty_dict():
    """Comment-only file, by construction — no TOML keys/tables of any kind."""
    with open(_CONFIG_PATH, "rb") as f:
        data = tomllib.load(f)
    assert data == {}
