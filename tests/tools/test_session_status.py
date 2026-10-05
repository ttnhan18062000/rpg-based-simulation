"""Session status view (session-layer M4a): worktrees, seats, disk budget, retirement report. Read-only."""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from pathlib import Path

import pytest

from tools.sessions import status as status_mod
from tools.sessions.roster import Domain, Role, Roster, Worktree
from tools.sessions.launch import _worktree_entries
from tools.sessions.status import (
    INSTANCE_UNKNOWN,
    PR_NONE,
    PR_UNKNOWN,
    RETIRE_IDLE_DAYS,
    disk_warning,
    inspect_worktree,
    open_pr,
    removable,
    render,
    seat_infos,
)

ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
}


def git(cwd: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(cwd), env=ENV, capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return res.stdout


def commit(cwd: Path, name: str, body: str, msg: str) -> None:
    (cwd / name).write_text(body)
    git(cwd, "add", name)
    git(cwd, "commit", "-q", "-m", msg)


def _role(role: str, domain: str, function: str, worktree: str, seat: str = "staffed") -> Role:
    return Role(role, domain, function, role, None, seat, None, (), (), (), ("user",), (), None, worktree, 1, f".claude/handover/{role}.md", ())


@pytest.fixture
def repo(tmp_path: Path) -> dict[str, Path]:
    """A main checkout (with origin/main) and worktrees: clean-merged, dirty, unique commit, mid-rebase, owned."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    main = tmp_path / "main"
    git(tmp_path, "clone", "-q", str(origin), str(main))
    git(main, "checkout", "-q", "-b", "main")
    commit(main, "a.txt", "a\n", "base")
    git(main, "push", "-q", "origin", "main")
    wt = main / ".claude" / "worktrees"
    out = {"main": main}
    for name in ("clean", "dirty", "unique", "rebase", "owned"):
        git(main, "worktree", "add", "-q", "-b", f"b-{name}", str(wt / name), "main")
        out[name] = wt / name
    (out["dirty"] / "scratch.txt").write_text("x")
    commit(out["unique"], "u.txt", "u\n", "only on the branch")
    # mid-rebase: conflicting change on main and on the branch, then start the rebase
    commit(out["rebase"], "a.txt", "branch\n", "branch edit")
    commit(main, "a.txt", "main\n", "main edit")
    git(main, "push", "-q", "origin", "main")
    subprocess.run(["git", "rebase", "main"], cwd=str(out["rebase"]), env=ENV, capture_output=True, text=True, check=False)
    return out


def _entries_by_path(main: Path) -> dict[Path, dict]:
    return {Path(e["worktree"]): e for e in _worktree_entries(main)}


def _infos(main: Path, pr_reader=lambda b, p: PR_NONE):
    return [inspect_worktree(e, main, pr_reader, lambda p: 1024**2) for e in _worktree_entries(main)]


def _roster() -> Roster:
    roles = (
        _role("owned-designer", "d", "designer", "owned"),
        _role("owned-planner", "d", "planner", "owned", seat="unstaffed"),
    )
    return Roster(domains=(Domain("d", (), (), ()),), splits=(), roles=roles, worktrees=(Worktree("owned", None),))


def _snapshot(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def test_report_shows_every_field_for_each_worktree(repo: dict[str, Path]) -> None:
    infos = {i.path.name: i for i in _infos(repo["main"])}
    assert infos["main"].is_main and infos["clean"].dirty == 0
    assert infos["dirty"].dirty == 1
    assert infos["unique"].unique_commits == 1 and infos["clean"].unique_commits == 0
    assert infos["clean"].branch == "b-clean" and infos["clean"].last_subject == "base" and infos["clean"].size_bytes == 1024**2
    assert infos["clean"].last_activity > 0 and infos["clean"].pr == PR_NONE
    text = render(list(infos.values()), seat_infos(_roster(), repo["main"] / "nope"), [], [], [], time.time())
    for needle in ("b-dirty", "dirty (1 paths)", "pr: none", "commits not in main: 1", "owned-designer"):
        assert needle in text


def test_status_changes_no_file_ref_or_worktree(repo: dict[str, Path]) -> None:
    before = _snapshot(repo["main"])
    infos = _infos(repo["main"])
    render(infos, seat_infos(_roster(), repo["main"] / "nope"), disk_warning(infos, repo["main"], lambda p: (99, 100)), [], [], time.time())
    assert _snapshot(repo["main"]) == before


def test_mid_rebase_is_flagged(repo: dict[str, Path]) -> None:
    infos = {i.path.name: i for i in _infos(repo["main"])}
    assert any("rebase" in op for op in infos["rebase"].operations)
    assert not infos["clean"].operations
    assert "git operation in progress" in render([infos["rebase"]], [], [], [], [], time.time())


def test_disk_warning_fires_at_threshold_and_orders_by_size(repo: dict[str, Path]) -> None:
    sizes = {"clean": 5, "dirty": 50, "unique": 20}
    infos = [inspect_worktree(e, repo["main"], lambda b, p: PR_NONE, lambda p: sizes.get(p.name, 1) * 1024**2) for e in _worktree_entries(repo["main"])]
    assert disk_warning(infos, repo["main"], lambda p: (84, 100)) == []
    lines = disk_warning(infos, repo["main"], lambda p: (85, 100))
    assert "85%" in lines[0]
    named = [ln.split()[-1] for ln in lines[1:]]
    assert named[:3] == [str(repo["dirty"]), str(repo["unique"]), str(repo["clean"])]


def test_retirement_report_lists_only_safe_idle_worktrees(repo: dict[str, Path]) -> None:
    infos = _infos(repo["main"])
    roster = _roster()
    seats = seat_infos(roster, repo["main"] / "nope")
    later = time.time() + (RETIRE_IDLE_DAYS + 1) * 86400
    listed = {i.path.name for i in removable(infos, roster, seats, repo["main"], repo["main"] / "nope", later)}
    assert "clean" in listed and "owned" in listed  # owned: idle past the threshold, not live
    assert listed.isdisjoint({"dirty", "unique", "rebase", "main"})
    assert removable(infos, roster, seats, repo["main"], repo["main"] / "nope", time.time()) == [
        i for i in infos if i.path.name == "clean"
    ]  # an unowned clean worktree is retired at once; the owned one is not idle yet
    with_pr = _infos(repo["main"], lambda b, p: "#7" if b == "b-clean" else PR_NONE)
    assert "clean" not in {i.path.name for i in removable(with_pr, roster, seats, repo["main"], repo["main"] / "nope", later)}
    unknown_pr = _infos(repo["main"], lambda b, p: PR_UNKNOWN)
    assert removable(unknown_pr, roster, seats, repo["main"], repo["main"] / "nope", later) == []


def test_current_directory_is_never_reported_removable(repo: dict[str, Path]) -> None:
    infos = _infos(repo["main"])
    roster = _roster()
    seats = seat_infos(roster, repo["main"] / "nope")
    later = time.time() + 30 * 86400
    listed = removable(infos, roster, seats, repo["main"], repo["main"] / "nope", later, current=repo["clean"])
    assert "clean" not in {i.path.name for i in listed}


def test_gh_failure_degrades_to_pr_unknown(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def boom(*a, **k):
        raise FileNotFoundError("gh")

    monkeypatch.setattr(status_mod.subprocess, "run", boom)
    assert open_pr("some-branch", tmp_path) == PR_UNKNOWN


def test_gh_nonzero_exit_and_garbage_are_unknown(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for rc, out in ((1, ""), (0, "not json")):
        monkeypatch.setattr(
            status_mod.subprocess, "run",
            lambda *a, rc=rc, out=out, **k: subprocess.CompletedProcess(a, rc, stdout=out, stderr=""),
        )
        assert open_pr("b", tmp_path) == PR_UNKNOWN


def test_missing_state_directory_reads_unknown_not_none(tmp_path: Path) -> None:
    seats = seat_infos(_roster(), tmp_path / "does-not-exist")
    assert {s.instance for s in seats} == {INSTANCE_UNKNOWN}
    (tmp_path / "state").mkdir()
    assert {s.instance for s in seat_infos(_roster(), tmp_path / "state")} == {"none"}


def test_prunable_worktree_is_reported_not_crashed(repo: dict[str, Path]) -> None:
    import shutil

    shutil.rmtree(repo["clean"])
    infos = {i.path.name: i for i in _infos(repo["main"])}
    assert infos["clean"].prunable
    assert "missing or prunable" in render([infos["clean"]], [], [], [], [], time.time())


def test_collect_runs_against_the_real_repository_without_failing() -> None:
    root = Path(__file__).resolve().parents[2]
    text = status_mod.collect(root, volume=lambda p: (1, 100), pr_reader=lambda b, p: PR_UNKNOWN, size_reader=lambda p: 0)
    assert "seats:" in text and "worktree " in text
