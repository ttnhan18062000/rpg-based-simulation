"""Suite-level non-mutation guards for tests/agent_codex_posttool_adapter/ (Step 1).

One autouse, session-scoped fixture that snapshots (a) agent-monitoring/{runs,events,tools}.jsonl
via whole-file sha256 — the same technique
tools.agent_codex_pilot_guardrails.config_toggle.snapshot_rollback_scope uses, reimplemented here
for a 3-file-only subset since that function's signature also requires a pilot_ticket_path this
suite has no reason to supply; (b) .codex/config.toml bytes via
tools.agent_replay_codex.codex_config_guard.snapshot_config_bytes, reused directly; (c) a
tickets/-scoped git-porcelain-diff baseline via tools.agent_replay_codex.containment's existing
capture_snapshot/assert_no_diff helpers, reused directly. All three assert unchanged at teardown.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_replay_codex.codex_config_guard import (
    assert_config_bytes_unchanged,
    snapshot_config_bytes,
)
from tools.agent_replay_codex.containment import assert_no_diff, capture_snapshot
from tools.agent_replay_codex.monitoring_shards import hash_source

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"
_MONITORING_SOURCES = ("runs.jsonl", "events.jsonl", "tools.jsonl")


def _snapshot_monitoring_hashes() -> dict[str, str]:
    return {
        name: hash_source(_AGENT_MONITORING_DIR, name)
        for name in _MONITORING_SOURCES
    }


@pytest.fixture(scope="session", autouse=True)
def _no_real_side_effects_across_suite():
    pre_monitoring_hashes = _snapshot_monitoring_hashes()
    pre_config_bytes = snapshot_config_bytes(_REPO_ROOT)
    pre_tickets_snapshot = capture_snapshot(_REPO_ROOT)

    yield

    post_monitoring_hashes = _snapshot_monitoring_hashes()
    assert post_monitoring_hashes == pre_monitoring_hashes, (
        "agent-monitoring/{runs,events,tools}.jsonl changed during "
        "tests/agent_codex_posttool_adapter/ — every test must write to a tmp_path-based "
        "target_path, never the real corpus"
    )

    post_config_bytes = snapshot_config_bytes(_REPO_ROOT)
    assert_config_bytes_unchanged(pre_config_bytes, post_config_bytes)

    post_tickets_snapshot = capture_snapshot(_REPO_ROOT)
    assert_no_diff(pre_tickets_snapshot, post_tickets_snapshot)
