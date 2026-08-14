"""Tests for tools/agent_codex_pilot_guardrails/config_toggle.py
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS, Step 5)."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.agent_codex_pilot_guardrails.config_toggle import (
    assert_rollback_scope_unchanged,
    disable,
    enable,
    snapshot_rollback_scope,
)
from tools.agent_codex_pilot_guardrails.errors import (
    PilotConfigToggleGuardError,
    PilotRollbackVerificationError,
)
from tools.agent_replay_codex.codex_config_guard import (
    assert_committed_config_hook_free,
    assert_config_bytes_unchanged,
    snapshot_config_bytes,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_CONFIG_BYTES_AT_COLLECTION = snapshot_config_bytes(_REPO_ROOT)


def _build_scratch_area(tmp_path: Path) -> Path:
    # Deliberately NOT laid out as <scratch>/.codex/config.toml — _assert_scratch_target's job is
    # to forbid targeting the real repo_root's own .codex/config.toml specifically, so the scratch
    # config here lives at an unrelated path and repo_root is always the real project root.
    scratch_area = tmp_path / "scratch"
    scratch_area.mkdir()
    (scratch_area / "config.toml").write_text('# scratch config\nfoo = "bar"\n', encoding="utf-8")
    monitoring_dir = scratch_area / "agent-monitoring"
    monitoring_dir.mkdir()
    for filename in ("runs.jsonl", "events.jsonl", "tools.jsonl"):
        (monitoring_dir / filename).write_text('{"a": 1}\n', encoding="utf-8")
    (scratch_area / "TCK-SCRATCH-PILOT.md").write_text("# scratch pilot ticket\n", encoding="utf-8")
    return scratch_area


def test_enable_disable_round_trip_leaves_zero_byte_diff_in_rollback_scope(tmp_path):
    scratch_area = _build_scratch_area(tmp_path)
    scratch_config_path = scratch_area / "config.toml"
    agent_monitoring_dir = scratch_area / "agent-monitoring"
    ticket_path = scratch_area / "TCK-SCRATCH-PILOT.md"

    baseline_bytes = scratch_config_path.read_bytes()

    enable(scratch_config_path, _REPO_ROOT)
    assert b"hooks" in scratch_config_path.read_bytes()  # proves the toggle is real and capable

    pre_rollback_scope = snapshot_rollback_scope(agent_monitoring_dir, ticket_path)

    disable(scratch_config_path, _REPO_ROOT, baseline_bytes)

    post_rollback_scope = snapshot_rollback_scope(agent_monitoring_dir, ticket_path)

    assert_rollback_scope_unchanged(pre_rollback_scope, post_rollback_scope)
    assert scratch_config_path.read_bytes() == baseline_bytes
    assert_config_bytes_unchanged(baseline_bytes, scratch_config_path.read_bytes())


def test_enable_refuses_to_target_the_real_committed_config():
    real_config_path = _REPO_ROOT / ".codex" / "config.toml"
    with pytest.raises(PilotConfigToggleGuardError):
        enable(real_config_path, _REPO_ROOT)
    # Never even reached a read/write of the real file.
    assert_committed_config_hook_free(_REPO_ROOT)


def test_disable_refuses_to_target_the_real_committed_config():
    real_config_path = _REPO_ROOT / ".codex" / "config.toml"
    with pytest.raises(PilotConfigToggleGuardError):
        disable(real_config_path, _REPO_ROOT, b"")
    assert_committed_config_hook_free(_REPO_ROOT)


def test_rollback_scope_mismatch_raises():
    pre = {"runs.jsonl": "abc", "events.jsonl": "def", "tools.jsonl": "ghi", "pilot_ticket": "jkl"}
    post = {"runs.jsonl": "abc", "events.jsonl": "CHANGED", "tools.jsonl": "ghi", "pilot_ticket": "jkl"}
    with pytest.raises(PilotRollbackVerificationError):
        assert_rollback_scope_unchanged(pre, post)


def test_real_committed_config_never_touched_by_this_suite():
    # Session-level anti-drift guard, mirroring assert_config_bytes_unchanged applied at the
    # test-suite level rather than inside just one test: the real, committed .codex/config.toml
    # must still be hook-free AND byte-identical to its state at module-collection time after
    # this entire module's test run.
    assert_committed_config_hook_free(_REPO_ROOT)
    assert_config_bytes_unchanged(
        _REAL_CONFIG_BYTES_AT_COLLECTION, snapshot_config_bytes(_REPO_ROOT)
    )
