"""Project-config guard reuse (Step 7): no new tools/ source. Imports and calls
assert_committed_config_hook_free, snapshot_config_bytes, assert_config_bytes_unchanged from
tools.agent_replay_codex.codex_config_guard — exactly as
tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py already does — never
reimplemented."""
from __future__ import annotations

from pathlib import Path

from tools.agent_replay_codex.codex_config_guard import (
    assert_committed_config_hook_free,
    assert_config_bytes_unchanged,
    snapshot_config_bytes,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_CONFIG_BYTES_AT_COLLECTION = snapshot_config_bytes(_REPO_ROOT)


def test_committed_config_hook_free_reused_not_reimplemented():
    assert_committed_config_hook_free(_REPO_ROOT)


def test_config_bytes_unchanged_across_full_adapter_suite():
    assert_config_bytes_unchanged(
        _REAL_CONFIG_BYTES_AT_COLLECTION, snapshot_config_bytes(_REPO_ROOT)
    )
