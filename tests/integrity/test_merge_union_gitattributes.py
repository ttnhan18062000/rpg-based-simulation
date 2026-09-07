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


def test_squash_style_single_parent_commit_is_not_a_merge_and_bypasses_drivers(tmp_path):
    """Root-cause regression guard (TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP):
    proves, at the git level, that merge=union provides zero protection for a landing path
    that never invokes git's own merge machinery -- exactly what a GitHub squash-merge does
    (confirmed for PR #90 / commit 5993cac3: single parent, GitHub-recorded merge SHA,
    concatenated per-commit message body -- the shape GitHub produces for a squash-merge).

    Reproduces the *effect* of a squash-merge without ever calling `git merge`, `git
    rebase`, or `git cherry-pick -m`: branch-b's append lands as a normal commit on main,
    then branch-a's diff (computed against the shared original base, exactly like GitHub
    diffs a stale PR branch tip against current main) is applied as a second plain,
    single-parent commit directly on top -- reproducing content already on main as a
    synthetic "addition," the same mechanism that produced the real ~1586-row duplication.
    """
    repo = _init_repo_with_union_attribute(tmp_path, "tickets/working_log.csv")
    target = repo / "tickets/working_log.csv"
    base_content = target.read_text()

    _run_git(["checkout", "-q", "-b", "branch-a"], cwd=repo)
    branch_a_addition = '{"seq": 2, "branch": "a"}\n'
    target.write_text(base_content + branch_a_addition)
    _run_git(["commit", "-q", "-am", "branch-a append"], cwd=repo)
    branch_a_full_content = target.read_text()

    _run_git(["checkout", "-q", "main"], cwd=repo)
    target.write_text(base_content + '{"seq": 2, "branch": "b"}\n')
    _run_git(["commit", "-q", "-am", "branch-b append"], cwd=repo)

    # Reproduce a squash-merge's mechanics: apply branch-a's full content directly as a
    # plain commit on current main, without ever calling git merge/rebase/cherry-pick -m.
    target.write_text(branch_a_full_content)
    result = _run_git(["commit", "-q", "-am", "squash-style landing of branch-a"], cwd=repo)
    assert result.returncode == 0

    parents = _run_git(["log", "-1", "--format=%P", "HEAD"], cwd=repo).stdout.strip().split()
    assert len(parents) == 1, (
        "a squash-style landing must be an ordinary single-parent commit, not a real merge"
    )

    final_content = target.read_text()
    assert final_content == branch_a_full_content, (
        "no merge driver ran (none was invoked) -- the squash-style commit's content is "
        "exactly branch-a's diff applied wholesale, silently discarding branch-b's own "
        "concurrent append that main already had. merge=union never got a chance to union "
        "the two sides because git's merge machinery never ran."
    )
    assert '"branch": "b"' not in final_content


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
