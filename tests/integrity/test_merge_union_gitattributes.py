"""Regression test for the merge=union .gitattributes entries (TCK-20260826-REGISTRY-PARITY-
CONFLICT-GUARDS). Verifies existing, already-shipped behavior -- not new implementation.

agent-monitoring/{tools,runs,events}.jsonl and tickets/working_log.csv are append-only logs
carrying `merge=union` in this repo's .gitattributes, a stock git built-in merge driver (no
custom script/registration needed). This test proves that attribute actually resolves a real,
concurrent two-branch append to the same file without manual conflict markers -- git-level
behavior, not just a static check that the .gitattributes line is present -- by running real git
commands (init/commit/branch/merge) against a throwaway repo in tmp_path, never the real repo.
"""
import subprocess
from pathlib import Path

import pytest


def _run_git(args, cwd):
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return result


def _init_repo_with_union_attribute(tmp_path: Path, tracked_filename: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-q", "-b", "main"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)
    _run_git(["config", "user.name", "Test"], cwd=repo)
    (repo / ".gitattributes").write_text(f"{tracked_filename} merge=union\n")
    target = repo / tracked_filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{"seq": 1}\n')
    _run_git(["add", "."], cwd=repo)
    _run_git(["commit", "-q", "-m", "initial"], cwd=repo)
    return repo


@pytest.mark.parametrize(
    "tracked_filename",
    [
        "agent-monitoring/tools.jsonl",
        "agent-monitoring/runs.jsonl",
        "agent-monitoring/events.jsonl",
        "tickets/working_log.csv",
        "agent-monitoring/tools/tools-2026-W36.jsonl",
    ],
)
def test_concurrent_branch_appends_merge_without_conflict_markers(tmp_path, tracked_filename):
    repo = _init_repo_with_union_attribute(tmp_path, tracked_filename)
    target = repo / tracked_filename

    _run_git(["checkout", "-q", "-b", "branch-a"], cwd=repo)
    with target.open("a") as f:
        f.write('{"seq": 2, "branch": "a"}\n')
    _run_git(["commit", "-q", "-am", "branch-a append"], cwd=repo)

    _run_git(["checkout", "-q", "main"], cwd=repo)
    with target.open("a") as f:
        f.write('{"seq": 2, "branch": "b"}\n')
    _run_git(["commit", "-q", "-am", "branch-b append"], cwd=repo)

    # Real concurrent-branch merge -- must succeed with git's built-in union driver, no manual
    # conflict resolution, no conflict markers left in the file.
    merge_result = subprocess.run(
        ["git", "merge", "-q", "branch-a", "--no-edit"], cwd=str(repo),
        capture_output=True, text=True,
    )
    assert merge_result.returncode == 0, (
        f"merge should auto-resolve via merge=union, got conflict: {merge_result.stdout!r} "
        f"{merge_result.stderr!r}"
    )

    merged_content = target.read_text()
    assert "<<<<<<<" not in merged_content
    assert "=======" not in merged_content
    assert ">>>>>>>" not in merged_content
    assert '"branch": "a"' in merged_content
    assert '"branch": "b"' in merged_content


def test_gitattributes_lines_present_for_all_four_union_merge_paths():
    """Sanity guard: the real repo's own .gitattributes must still carry all four entries this
    test's git-level behavior proves -- catches an accidental removal even though the git-level
    test above uses a throwaway repo, not the real .gitattributes file."""
    repo_root = Path(__file__).parent.parent.parent
    content = (repo_root / ".gitattributes").read_text()
    for path in (
        "agent-monitoring/runs.jsonl",
        "agent-monitoring/events.jsonl",
        "agent-monitoring/tools.jsonl",
        "tickets/working_log.csv",
    ):
        assert f"{path} merge=union" in content


def test_gitattributes_line_present_for_shard_glob():
    """TCK-20260902-MONITORING-SHARD-WRITE-PATH: post_tool_hook.py now writes new tool-call
    records to per-ISO-week shard files under agent-monitoring/tools/ instead of the single
    legacy agent-monitoring/tools.jsonl. Both the new shard glob and the old legacy line must be
    present -- the old line stays until a later ticket migrates/retires the legacy file."""
    repo_root = Path(__file__).parent.parent.parent
    content = (repo_root / ".gitattributes").read_text()
    assert "agent-monitoring/tools/*.jsonl merge=union" in content
    assert "agent-monitoring/tools.jsonl merge=union" in content
