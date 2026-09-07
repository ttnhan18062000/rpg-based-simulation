"""Isolation mechanism for the filtered replay eval pilot's 2 replay runs
(TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, Step 5).

Does NOT create a literal `git worktree add` — investigation.md Risks #2 option (b), adopted
during Plan/Review: `replay_slice()` (tools/agent_replay/runner.py) is already proven zero-write
by `tests/agent_replay/test_no_mutation_snapshot.py` via its `_fake_write_monitoring`/
`_fake_hook_boundary` no-ops, regardless of which directory it runs from. This module reuses that
proven property plus a widened snapshot-diff check instead of standing up a real worktree.

Locally reimplements the porcelain-if-clean/content-hash-if-dirty zero-diff technique — mirroring
`tools/agent_replay_codex/containment.py`'s own pattern — parameterized by a watch set sourced
from `tools/agent_replay_codex/monitoring_shards.py::source_paths()` (sharding-aware) plus
`tickets/`, rather than calling `containment.py`'s own `capture_snapshot`/`assert_no_diff`
directly: those two functions accept no path-list parameter and hardcode the retired 3-file
`agent-monitoring/{runs,events,tools}.jsonl` pathspec internally (investigation.md Risks #3,
corrected during plan Review Round 1 — see plan.md).

`snapshot_monitoring_lines`/`assert_monitoring_prefix_preserved` ARE imported and reused as-is
from `containment.py` for the append-only-specific check, since the manifest module they wrap is
already sharding-aware and needs no widening.

Separately asserts the unscoped `.claude/current_run` sidecar's mtime/content is unchanged across
the pilot's execution window — static proof this pilot's code never calls
`implement-ticket.js`'s real `writeSidecar()`, satisfying AC #4's session-scoped-sidecar-
exclusivity requirement.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay_codex.containment import (  # noqa: E402
    assert_monitoring_prefix_preserved,
    snapshot_monitoring_lines,
)
from agent_replay_codex.errors import ContainmentViolationError  # noqa: E402
from agent_replay_codex.monitoring_shards import source_paths  # noqa: E402

from .fixture_envelope import FixtureEnvelope
from .runner import ReplayOutcome, replay_slice

_WATCHED_GIT_PATHSPECS = ["tickets/", "agent-monitoring/data/"]
_UNSCOPED_SIDECAR_RELPATH = ".claude/current_run"

PILOT_RUN_ID = "TCK-20260907-FILTERED-REPLAY-EVAL-PILOT"


@dataclass(frozen=True)
class IsolationSnapshot:
    porcelain: str
    content_hash: str | None
    monitoring_lines: dict
    sidecar_mtime: float | None
    sidecar_content: str | None


@dataclass(frozen=True)
class IsolationEvidence:
    held: bool
    pre_porcelain: str
    post_porcelain: str
    violation: str | None


def _porcelain_snapshot(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *_WATCHED_GIT_PATHSPECS],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _watched_files(repo_root: Path) -> list:
    files = [f for f in sorted((repo_root / "tickets").rglob("*")) if f.is_file()]
    monitoring_data_dir = repo_root / "agent-monitoring" / "data"
    if monitoring_data_dir.is_dir():
        files += [f for f in sorted(monitoring_data_dir.rglob("*")) if f.is_file()]
    return files


def _content_hash_snapshot(repo_root: Path) -> str:
    hasher = hashlib.sha256()
    for f in _watched_files(repo_root):
        hasher.update(str(f.relative_to(repo_root)).encode("utf-8"))
        hasher.update(f.read_bytes())
    return hasher.hexdigest()


def _sidecar_snapshot(repo_root: Path) -> tuple:
    path = repo_root / _UNSCOPED_SIDECAR_RELPATH
    if not path.exists():
        return (None, None)
    return (path.stat().st_mtime, path.read_text(encoding="utf-8"))


def capture(repo_root: Path) -> IsolationSnapshot:
    porcelain = _porcelain_snapshot(repo_root)
    content_hash = _content_hash_snapshot(repo_root) if porcelain != "" else None
    monitoring_lines = snapshot_monitoring_lines(repo_root / "agent-monitoring")
    sidecar_mtime, sidecar_content = _sidecar_snapshot(repo_root)
    return IsolationSnapshot(porcelain, content_hash, monitoring_lines, sidecar_mtime, sidecar_content)


def _assert_sidecar_unchanged(pre: IsolationSnapshot, post: IsolationSnapshot) -> None:
    if pre.sidecar_mtime != post.sidecar_mtime or pre.sidecar_content != post.sidecar_content:
        raise ContainmentViolationError(
            f"unscoped {_UNSCOPED_SIDECAR_RELPATH} sidecar changed across the pilot's isolated "
            "execution window — this pilot must never call the live orchestrator's writeSidecar()"
        )


def _assert_no_pilot_attributed_new_lines(pre_lines: dict, post_lines: dict, pilot_run_id: str) -> None:
    for filename, pre_file_lines in pre_lines.items():
        post_file_lines = post_lines.get(filename, [])
        new_lines = post_file_lines[len(pre_file_lines):]
        for line in new_lines:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("run_id") == pilot_run_id:
                raise ContainmentViolationError(
                    f"{filename}: a new line attributed to the pilot's own run_id "
                    f"{pilot_run_id!r} appeared during the isolated replay window — "
                    "replay_slice() must never write to agent-monitoring"
                )


def assert_isolation_held(
    pre: IsolationSnapshot, post: IsolationSnapshot, pilot_run_id: str = PILOT_RUN_ID
) -> None:
    """Raises `ContainmentViolationError` on any detected contamination.

    Fast path: if the watched pathspecs are byte-identical pre/post (porcelain and content-hash
    both unchanged), nothing happened during the window — pass. Otherwise ambient concurrent-
    session activity is the expected common case in this routinely-dirty repo (per
    investigation.md Current Behavior §7): fall back to asserting append-only prefix-preservation
    on every `agent-monitoring/*.jsonl` shard (no pre-existing line was rewritten/reordered/
    deleted) AND that none of the newly-appended lines carry the pilot's own `run_id` — the
    concrete distinguishing check between "grew because another concurrent session wrote its own
    attributed lines" (tolerated) and "grew because the pilot's own execution wrote something"
    (a hard failure).
    """
    _assert_sidecar_unchanged(pre, post)

    if pre.porcelain == post.porcelain and pre.content_hash == post.content_hash:
        return

    assert_monitoring_prefix_preserved(pre.monitoring_lines, post.monitoring_lines)
    _assert_no_pilot_attributed_new_lines(pre.monitoring_lines, post.monitoring_lines, pilot_run_id)


def run_pilot_isolated(
    fixtures: list, repo_root: Path, pilot_run_id: str = PILOT_RUN_ID
) -> tuple:
    """Runs `replay_slice()` over every fixture in `fixtures`, TWICE, inside one isolation
    snapshot window (Method step 3/AC #4 — "run twice... capture evidence no write touched
    agent-monitoring"). Returns `(run1_outcomes, run2_outcomes, timing, IsolationEvidence)`.
    """
    pre = capture(repo_root)

    run1_start = time.perf_counter()
    run1_outcomes: list = [replay_slice(fixture) for fixture in fixtures]
    run1_elapsed = time.perf_counter() - run1_start

    run2_start = time.perf_counter()
    run2_outcomes: list = [replay_slice(fixture) for fixture in fixtures]
    run2_elapsed = time.perf_counter() - run2_start

    post = capture(repo_root)

    timing = {"run1_wall_clock_s": run1_elapsed, "run2_wall_clock_s": run2_elapsed}

    try:
        assert_isolation_held(pre, post, pilot_run_id)
        evidence = IsolationEvidence(
            held=True, pre_porcelain=pre.porcelain, post_porcelain=post.porcelain, violation=None
        )
    except ContainmentViolationError as exc:
        evidence = IsolationEvidence(
            held=False, pre_porcelain=pre.porcelain, post_porcelain=post.porcelain, violation=str(exc)
        )

    return run1_outcomes, run2_outcomes, timing, evidence
