"""Containment snapshot module for real Codex CLI invocations (TCK-20260721-CODEX-REPLAY-PARITY,
Step 4).

Reimplements (does not import — the source lives in a test file, not an importable module) the
exact porcelain-if-clean/content-hash-if-dirty technique from
tests/agent_replay/test_no_mutation_snapshot.py, parameterized by `repo_root` so tests can point
it at a disposable tmp_path git repo instead of the real one.

`snapshot_monitoring_lines`/`assert_monitoring_prefix_preserved` are thin wrappers around
tools/agent-monitoring/manifest.py's existing `capture_lines`/`assert_prefix_preserved` — imported
and reused unmodified, not reimplemented, for the narrower agent-monitoring/*.jsonl-only
append-only check.
"""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import ContainmentViolationError

_WATCHED_GIT_PATHSPECS = [
    "tickets/",
    "agent-monitoring/runs.jsonl",
    "agent-monitoring/events.jsonl",
    "agent-monitoring/tools.jsonl",
]


@dataclass(frozen=True)
class ContainmentSnapshot:
    porcelain: str
    content_hash: str | None  # populated only when porcelain was non-empty at capture time


def _porcelain_snapshot(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *_WATCHED_GIT_PATHSPECS],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _watched_files(repo_root: Path) -> list[Path]:
    files = [f for f in sorted((repo_root / "tickets").rglob("*")) if f.is_file()]
    files += sorted((repo_root / "agent-monitoring").glob("*.jsonl"))
    return files


def _content_hash_snapshot(repo_root: Path) -> str:
    hasher = hashlib.sha256()
    for f in _watched_files(repo_root):
        hasher.update(str(f.relative_to(repo_root)).encode("utf-8"))
        hasher.update(f.read_bytes())
    return hasher.hexdigest()


def capture_snapshot(repo_root: Path) -> ContainmentSnapshot:
    porcelain = _porcelain_snapshot(repo_root)
    content_hash = _content_hash_snapshot(repo_root) if porcelain != "" else None
    return ContainmentSnapshot(porcelain=porcelain, content_hash=content_hash)


def assert_no_diff(pre: ContainmentSnapshot, post: ContainmentSnapshot) -> None:
    """Raises ContainmentViolationError (not AssertionError, so callers outside pytest get a
    typed exception) on any detected diff, using the same porcelain-clean-else-content-hash logic
    as tests/agent_replay/test_no_mutation_snapshot.py."""
    if pre.porcelain == "":
        if post.porcelain != "":
            raise ContainmentViolationError(
                "containment violation: tickets/ or agent-monitoring/*.jsonl was clean before "
                f"and dirty after: {post.porcelain!r}"
            )
        return

    if pre.content_hash != post.content_hash:
        raise ContainmentViolationError(
            "containment violation: content of one or more watched files under tickets/ or "
            "agent-monitoring/*.jsonl changed (pre-existing dirty state's content hash differs "
            "before vs. after)"
        )


_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "agent-monitoring" / "manifest.py"
_MANIFEST_SPEC = importlib.util.spec_from_file_location("agent_monitoring_manifest", _MANIFEST_PATH)
_manifest = importlib.util.module_from_spec(_MANIFEST_SPEC)
_MANIFEST_SPEC.loader.exec_module(_manifest)


def snapshot_monitoring_lines(agent_monitoring_dir: Path) -> dict[str, list[str]]:
    return _manifest.capture_lines(agent_monitoring_dir)


def assert_monitoring_prefix_preserved(
    pre: dict[str, list[str]], post: dict[str, list[str]]
) -> None:
    try:
        _manifest.assert_prefix_preserved(pre, post)
    except AssertionError as exc:
        raise ContainmentViolationError(str(exc)) from exc
