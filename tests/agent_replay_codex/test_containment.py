"""Tests for tools/agent_replay_codex/containment.py (TCK-20260721-CODEX-REPLAY-PARITY, Step 4).

Exercises the real detection logic end-to-end against a real (but disposable, tmp_path-scoped)
git repository — never the actual project repo — satisfying the requirement that "a containment
test with no negative control is not a valid guard."
"""
from __future__ import annotations

import subprocess

import pytest

from tools.agent_replay_codex.containment import assert_no_diff, capture_snapshot
from tools.agent_replay_codex.errors import ContainmentViolationError


def _init_synthetic_repo(tmp_path):
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    week_dir = tmp_path / "agent-monitoring" / "data" / "2026-W01"
    week_dir.mkdir(parents=True)

    (tmp_path / "tickets" / "inprogress" / "FAKE.md").write_text("line one\n", encoding="utf-8")
    # TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP: the real corpus shape is now
    # agent-monitoring/data/<week>/<id>.<kind>.jsonl (per-PR/branch), not the flat
    # agent-monitoring/{runs,events,tools}.jsonl this fixture previously built directly --
    # those flat files have not existed since TCK-20260902-MONITORING-SHARD-WRITE-PATH.
    for filename in ("some-branch.runs.jsonl", "some-branch.events.jsonl", "some-branch.tools.jsonl"):
        (week_dir / filename).write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")

    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=test", "add", "-A"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-m", "init"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )


def test_assert_no_diff_raises_when_a_watched_file_is_mutated(tmp_path):
    _init_synthetic_repo(tmp_path)

    pre = capture_snapshot(tmp_path)
    (tmp_path / "tickets" / "inprogress" / "FAKE.md").write_text("mutated content\n", encoding="utf-8")
    post = capture_snapshot(tmp_path)

    with pytest.raises(ContainmentViolationError):
        assert_no_diff(pre, post)


def test_assert_no_diff_does_not_raise_when_nothing_changed(tmp_path):
    _init_synthetic_repo(tmp_path)

    pre = capture_snapshot(tmp_path)
    post = capture_snapshot(tmp_path)

    assert_no_diff(pre, post)


def test_assert_no_diff_raises_when_a_real_sharded_monitoring_file_is_mutated(tmp_path):
    """TCK-20260925-MONITORING-STALE-READ-PATH-SWEEP: this containment mechanism's own
    `_WATCHED_GIT_PATHSPECS`/`_watched_files()` previously named the retired flat
    `agent-monitoring/{runs,events,tools}.jsonl` paths, which have not existed since
    TCK-20260902-MONITORING-SHARD-WRITE-PATH -- meaning this exact mutation was silently
    undetected before this fix (git status on a nonexistent pathspec is empty, not an error).
    Proves detection now actually fires on the real sharded per-branch path, not just asserts
    the mechanism runs without error."""
    _init_synthetic_repo(tmp_path)

    pre = capture_snapshot(tmp_path)
    mutated = tmp_path / "agent-monitoring" / "data" / "2026-W01" / "some-branch.runs.jsonl"
    mutated.write_text('{"a": 1}\n{"a": 2}\n{"a": 3}\n', encoding="utf-8")
    post = capture_snapshot(tmp_path)

    with pytest.raises(ContainmentViolationError):
        assert_no_diff(pre, post)
