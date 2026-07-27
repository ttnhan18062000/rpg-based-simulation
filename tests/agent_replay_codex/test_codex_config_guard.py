"""Tests for tools/agent_replay_codex/codex_config_guard.py (TCK-20260721-CODEX-REPLAY-PARITY, Step 5)."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_replay_codex.codex_config_guard import assert_committed_config_hook_free
from tools.agent_replay_codex.errors import ContainmentViolationError

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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
