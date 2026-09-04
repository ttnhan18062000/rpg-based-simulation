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


def test_gitattributes_line_present_for_working_log_csv():
    """Sanity guard: the real repo's own .gitattributes must still carry the
    tickets/working_log.csv append-only-file entry -- catches an accidental removal even
    though the git-level test above uses a throwaway repo, not the real .gitattributes
    file. All 3 monitoring-source legacy lines this function used to also assert
    (`agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`,
    `agent-monitoring/tools/*.jsonl`) were removed from .gitattributes by
    TCK-20260903-MONITORING-DATA-MIGRATION, which retired all 3 legacy physical shapes
    from the working tree in favor of the unified agent-monitoring/data/YYYY-Www/
    {runs,events,tools}.jsonl layout (see test_gitattributes_lines_absent_for_retired_
    monitoring_paths below)."""
    repo_root = Path(__file__).parent.parent.parent
    content = (repo_root / ".gitattributes").read_text()
    assert "tickets/working_log.csv merge=union" in content


def test_gitattributes_lines_absent_for_retired_monitoring_paths():
    """TCK-20260902-MONITORING-SHARD-MIGRATION retired the legacy agent-monitoring/
    tools.jsonl file. TCK-20260903-MONITORING-DATA-MIGRATION has since retired the other
    2 legacy monolithic files (agent-monitoring/runs.jsonl, agent-monitoring/
    events.jsonl) and the shard directory this ticket's own migration produced
    (agent-monitoring/tools/) -- none of the 3 monitoring-source legacy merge=union
    lines remain; only the unified glob added by TCK-20260903-MONITORING-DATA-WRITE-
    PATH-UNIFY does."""
    repo_root = Path(__file__).parent.parent.parent
    content = (repo_root / ".gitattributes").read_text()
    assert "agent-monitoring/tools.jsonl merge=union" not in content
    assert "agent-monitoring/runs.jsonl merge=union" not in content
    assert "agent-monitoring/events.jsonl merge=union" not in content
    assert "agent-monitoring/tools/*.jsonl merge=union" not in content
    assert "agent-monitoring/data/*/*.jsonl merge=union" in content
