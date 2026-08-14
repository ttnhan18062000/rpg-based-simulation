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
    (tmp_path / "agent-monitoring").mkdir(parents=True)

    (tmp_path / "tickets" / "inprogress" / "FAKE.md").write_text("line one\n", encoding="utf-8")
    for filename in ("runs.jsonl", "events.jsonl", "tools.jsonl"):
        (tmp_path / "agent-monitoring" / filename).write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")

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
