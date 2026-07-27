"""Process-level containment proof around the real Codex invocation (TCK-20260721-CODEX-REPLAY-PARITY,
Step 7). Uses the session-scoped `real_codex_replay` fixture — skips cleanly without consent.
"""
from __future__ import annotations

from tools.agent_replay_codex.containment import assert_no_diff


def test_real_invocation_produces_zero_tickets_or_monitoring_diff(real_codex_replay):
    assert_no_diff(real_codex_replay["pre_tickets"], real_codex_replay["post_tickets"])
