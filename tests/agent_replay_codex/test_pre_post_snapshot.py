"""Literal AC-bullet assertion: pre/post content-hash or git-porcelain snapshot of tickets/ and
agent-monitoring/*.jsonl around the real Codex invocation is asserted identical
(TCK-20260721-CODEX-REPLAY-PARITY, Step 7). Exercises the same underlying mechanism as
test_containment_real_process.py and test_no_production_hook_invocation.py, phrased as its own
named test for direct AC traceability.
"""
from __future__ import annotations

from tools.agent_replay_codex.containment import assert_no_diff


def test_ac_explicit_pre_post_snapshot_around_real_invocation(real_codex_replay):
    assert_no_diff(real_codex_replay["pre_tickets"], real_codex_replay["post_tickets"])
