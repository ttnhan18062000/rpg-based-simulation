"""Tests for tools/agent_replay_codex/codex_config_guard.py (TCK-20260721-CODEX-REPLAY-PARITY, Step 5)."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools.agent_replay_codex.codex_config_guard import (
    assert_committed_config_hook_free,
    snapshot_config_bytes,
)
from tools.agent_replay_codex.errors import ContainmentViolationError

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Recorded before TCK-20260730-PROVIDER-HOOK-POLICY's implementation touched the repo — that
# ticket's own scope guard forbids registering any actual Codex hook or changing this file at
# all, and this sha256 is the byte-identity proof, stronger than the structural hooks-key walk
# alone (it also catches non-'hooks'-key edits).
_PRE_TICKET_CONFIG_SHA256 = "74074efc3b2be3a08803b658c6a086dce1548c3901071488c317da96e961c758"


def test_real_committed_config_passes_hook_free_guard():
    assert_committed_config_hook_free(_REPO_ROOT)


def test_hook_bearing_config_raises(tmp_path):
    codex_dir = tmp_path / ".codex"
    codex_dir.mkdir()
    (codex_dir / "config.toml").write_text(
        '[[hooks.PostToolUse]]\nmatcher = "*"\n',
        encoding="utf-8",
    )
    with pytest.raises(ContainmentViolationError):
        assert_committed_config_hook_free(tmp_path)


def test_committed_codex_config_still_hook_free():
    current_bytes = snapshot_config_bytes(_REPO_ROOT)
    assert current_bytes is not None, ".codex/config.toml must exist"
    current_sha256 = hashlib.sha256(current_bytes).hexdigest()
    assert current_sha256 == _PRE_TICKET_CONFIG_SHA256, (
        ".codex/config.toml bytes changed since TCK-20260730-PROVIDER-HOOK-POLICY's "
        "pre-implementation snapshot — this ticket's scope forbids any change to this file"
    )
