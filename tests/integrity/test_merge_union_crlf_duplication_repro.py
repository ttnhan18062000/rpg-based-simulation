"""Proves, with real `git` commands in a throwaway repo, both halves of TCK-20260911-WORKING-
LOG-LINE-ENDING-UNION-DUPLICATION's root cause: (1) `merge=union` alone duplicates a block of
rows when two branches append the *same* rows with *different* line endings, because the CRLF
vs. LF bytes make git see two different additions rather than one shared one; (2) adding `text
eol=lf` to that same `.gitattributes` line removes the duplication, since both branches' content
is normalized to LF before either side's diff is computed, so the two additions become byte-
identical and merge cleanly.

Without step (1) actually reproducing the duplicate, a test that only exercises the fixed state
proves nothing about whether the fix addresses the real defect -- see investigation.md's Batch A/
PR #160/Batch C findings, all three explained by exactly this mechanism.

Git identity and `core.autocrlf` are configured inside each scratch repo only, never inherited
from the host, so the host's own git config cannot affect the result either way.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

_CSV_HEADER = "timestamp,ticket_id,title,status,summary,artifacts_path\n"
_BASE_ROW = "2026-09-01T00:00:00Z,TCK-BASE,Base row,DONE,Seed row already on both sides.,none\n"

# The rows both branches append -- identical content, deliberately written with different line
# endings per branch to reproduce the real writer-mismatch (record_hand_orchestrated_closure.py's
# CRLF vs. every other writer's LF).
_SHARED_ROWS = [
    "2026-09-11T10:00:00.000001Z,TCK-SHARED-1,Shared row one,DONE,Appended identically by both branches.,none\n",
    "2026-09-11T10:00:01.000002Z,TCK-SHARED-2,Shared row two,DONE,Appended identically by both branches.,none\n",
]
_BRANCH_B_ONLY_ROW = "2026-09-11T10:00:02.000003Z,TCK-BRANCH-B-ONLY,Branch B's own new row,DONE,Only branch B adds this one.,none\n"


def _run_git(args, cwd):
    result = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    assert result.returncode == 0, (
        f"git {' '.join(args)} failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return result


def _init_repo(tmp_path: Path, gitattributes_content: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-q", "-b", "main"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)
    _run_git(["config", "user.name", "Test"], cwd=repo)
    _run_git(["config", "core.autocrlf", "false"], cwd=repo)
    (repo / ".gitattributes").write_text(gitattributes_content)
    (repo / "tickets").mkdir()
    (repo / "tickets" / "working_log.csv").write_text(_CSV_HEADER + _BASE_ROW)
    _run_git(["add", "."], cwd=repo)
    _run_git(["commit", "-q", "-m", "base"], cwd=repo)
    return repo


def _append_crlf(path: Path, lines: list[str]) -> None:
    with path.open("ab") as f:
        for line in lines:
            f.write(line.replace("\n", "\r\n").encode("utf-8"))


def _append_lf(path: Path, lines: list[str]) -> None:
    with path.open("ab") as f:
        for line in lines:
            f.write(line.encode("utf-8"))


def _merge_branch_b_into_a(repo: Path) -> Path:
    target = repo / "tickets" / "working_log.csv"

    _run_git(["checkout", "-q", "-b", "branch-a"], cwd=repo)
    _append_crlf(target, _SHARED_ROWS)
    _run_git(["commit", "-q", "-am", "branch-a appends the shared rows as CRLF"], cwd=repo)

    _run_git(["checkout", "-q", "main"], cwd=repo)
    _run_git(["checkout", "-q", "-b", "branch-b"], cwd=repo)
    _append_lf(target, _SHARED_ROWS + [_BRANCH_B_ONLY_ROW])
    _run_git(["commit", "-q", "-am", "branch-b appends the same shared rows as LF, plus its own row"], cwd=repo)

    _run_git(["checkout", "-q", "branch-a"], cwd=repo)
    merge_result = subprocess.run(
        ["git", "merge", "-q", "branch-b", "--no-edit"], cwd=str(repo), capture_output=True, text=True,
    )
    assert merge_result.returncode == 0, (
        f"merge=union should auto-resolve without conflict markers, got: "
        f"{merge_result.stdout!r} {merge_result.stderr!r}"
    )
    assert "<<<<<<<" not in target.read_text(errors="replace")
    return target


def test_merge_union_alone_duplicates_rows_shared_across_branches_with_different_line_endings(tmp_path):
    """Proof step: without `eol=lf`, the same rows appended on both branches with different
    line endings land twice after the merge -- this is the real defect, reproduced at the git
    level, not assumed."""
    repo = _init_repo(tmp_path, "tickets/working_log.csv merge=union\n")
    target = _merge_branch_b_into_a(repo)

    merged_lines = target.read_text(errors="replace").splitlines()
    for shared_row in _SHARED_ROWS:
        stripped = shared_row.strip()
        occurrences = sum(1 for line in merged_lines if line.strip() == stripped)
        assert occurrences == 2, (
            f"expected the merge=union defect to duplicate {stripped!r} (found "
            f"{occurrences} occurrence(s)) -- if this no longer reproduces, this test no "
            "longer proves the fix addresses the real bug"
        )
    assert _BRANCH_B_ONLY_ROW.strip() in [line.strip() for line in merged_lines]


def test_text_eol_lf_prevents_the_duplication_and_leaves_no_cr(tmp_path):
    """Fix step: the same two-branch scenario, with `text eol=lf` added ahead of `merge=union`
    on the same .gitattributes line -- no duplicate, no CR byte anywhere in the merged file."""
    repo = _init_repo(tmp_path, "tickets/working_log.csv text eol=lf merge=union\n")
    target = _merge_branch_b_into_a(repo)

    merged_bytes = target.read_bytes()
    assert b"\r" not in merged_bytes

    merged_lines = target.read_text().splitlines()
    for shared_row in _SHARED_ROWS:
        stripped = shared_row.strip()
        occurrences = sum(1 for line in merged_lines if line.strip() == stripped)
        assert occurrences == 1, f"expected exactly one copy of {stripped!r}, found {occurrences}"
    assert _BRANCH_B_ONLY_ROW.strip() in [line.strip() for line in merged_lines]
