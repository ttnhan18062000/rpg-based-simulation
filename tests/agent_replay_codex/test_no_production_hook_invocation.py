"""Codex-config-untouched proof around the real Codex invocation (TCK-20260721-CODEX-REPLAY-PARITY,
Step 7). Uses the session-scoped `real_codex_replay` fixture — skips cleanly without consent.
"""
from __future__ import annotations

from pathlib import Path

from tools.agent_replay_codex.codex_config_guard import assert_committed_config_hook_free

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_committed_codex_config_byte_identical_across_real_invocation(real_codex_replay):
    assert real_codex_replay["pre_config"] == real_codex_replay["post_config"]
    assert_committed_config_hook_free(_REPO_ROOT)
