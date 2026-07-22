"""Zero-diff-under-`.claude/` containment test (TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER, AC #1).

Mirrors tests/agent_replay/test_no_mutation_snapshot.py's clean-vs-dirty porcelain/content-hash
fallback pattern exactly, watched pathspec swapped to `[".claude/"]`. This is the one test in the
ticket that legitimately runs the generator against the real repo root (Review-phase Fix B moved
the schema-shape check off the real tree onto `tmp_path` in test_generator_containment.py — only
this containment proof still touches the committed `agent-orchestration/rendered/` output).

Also asserts docs/guidelines/intentional_divergences.md's content is unchanged after running every
tool built in this ticket — proves no accidental path collision between the new
agent-orchestration/intentional-divergences.md and the pre-existing mechanics-bible log.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from tools.agent_orchestration_claude_adapter.generator import render_claude_adapter

_REPO_ROOT = Path(__file__).parent.parent.parent
_WATCHED_GIT_PATHSPECS = [".claude/"]
_MECHANICS_BIBLE_DIVERGENCE_LOG = _REPO_ROOT / "docs" / "guidelines" / "intentional_divergences.md"


def _porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *_WATCHED_GIT_PATHSPECS],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _watched_files() -> list[Path]:
    return [f for f in sorted((_REPO_ROOT / ".claude").rglob("*")) if f.is_file()]


def _content_hash_snapshot() -> str:
    hasher = hashlib.sha256()
    for f in _watched_files():
        hasher.update(str(f.relative_to(_REPO_ROOT)).encode("utf-8"))
        hasher.update(f.read_bytes())
    return hasher.hexdigest()


def test_snapshot_target_is_the_real_dot_claude_directory_not_a_tmp_copy():
    dot_claude_dir = _REPO_ROOT / ".claude"
    assert dot_claude_dir.is_dir()
    assert dot_claude_dir.parent == _REPO_ROOT
    assert "tmp" not in str(dot_claude_dir).lower()


def test_generator_produces_zero_git_diff_under_claude_before_and_after():
    pre_porcelain = _porcelain_snapshot()

    if pre_porcelain == "":
        render_claude_adapter(_REPO_ROOT, _REPO_ROOT / "agent-orchestration" / "rendered")
        post_porcelain = _porcelain_snapshot()
        assert post_porcelain == "", (
            "render_claude_adapter mutated .claude/ (tree was clean before, dirty after): "
            f"{post_porcelain!r}"
        )
        return

    pre_hash = _content_hash_snapshot()
    assert _watched_files(), "no watched files found under .claude/ — snapshot would be vacuous"

    render_claude_adapter(_REPO_ROOT, _REPO_ROOT / "agent-orchestration" / "rendered")

    post_hash = _content_hash_snapshot()
    assert pre_hash == post_hash, (
        "render_claude_adapter changed the content of one or more files under .claude/ (ambient "
        "dirty state existed before the run, but its content hash must be unchanged after)"
    )


def test_mechanics_bible_divergence_log_is_never_touched_by_this_tickets_tooling():
    pre_hash = hashlib.sha256(_MECHANICS_BIBLE_DIVERGENCE_LOG.read_bytes()).hexdigest()

    render_claude_adapter(_REPO_ROOT, _REPO_ROOT / "agent-orchestration" / "rendered")

    post_hash = hashlib.sha256(_MECHANICS_BIBLE_DIVERGENCE_LOG.read_bytes()).hexdigest()
    assert pre_hash == post_hash, (
        f"{_MECHANICS_BIBLE_DIVERGENCE_LOG} content changed after running this ticket's own "
        "generator — this file must never be written to by any tool built in this ticket"
    )
