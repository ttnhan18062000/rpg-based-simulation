"""prune_branches.py --worktrees (TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE): classification, dry run, guarded removal."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.agent_working_paths import AGENT_MONITORING, posix
from tools.sessions import prune_branches as pb
from tools.sessions import state as st
from tools.sessions.prune_branches import PrData, classify_worktrees

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(cwd: Path, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=str(cwd), env=ENV, capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    main = tmp_path / "main"
    main.mkdir()
    git(main, "init", "-q", "-b", "main")
    (main / "base.txt").write_text("base")
    git(main, "add", "-A")
    git(main, "commit", "-q", "-m", "base")
    return main


def add_worktree(main: Path, name: str, branch: str, parent: Path | None = None) -> tuple[Path, str]:
    path = (parent or main.parent / "wts") / name
    path.parent.mkdir(parents=True, exist_ok=True)
    git(main, "worktree", "add", "-q", "-b", branch, str(path))
    (path / f"{name}.txt").write_text(name)
    git(path, "add", f"{name}.txt")
    git(path, "commit", "-q", "-m", name)
    return path, git(path, "rev-parse", "HEAD")


ROSTER = SimpleNamespace(roles=[SimpleNamespace(role="seat-role", worktree="seat", max_sessions=1)], worktrees=[])


def classify(main: Path, prs, tmp_path: Path, proc_root: Path = Path("/proc")):
    report = classify_worktrees(main, prs, ROSTER, tmp_path / "state", proc_root)
    return {Path(r.path).name: r for r in report.rows}, report


def test_each_kind_of_worktree_is_classified_with_its_reason(repo, tmp_path):
    clean, clean_sha = add_worktree(repo, "clean", "b-clean")
    dirty, dirty_sha = add_worktree(repo, "dirty", "b-dirty")
    (dirty / "scratch.txt").write_text("uncommitted")
    _, unmerged_sha = add_worktree(repo, "unmerged", "b-unmerged")
    _, open_sha = add_worktree(repo, "openpr", "b-open")
    _, seat_sha = add_worktree(repo, "seat", "b-seat", parent=repo / ".claude" / "worktrees")
    prs = PrData({"b-clean": (clean_sha,), "b-dirty": (dirty_sha,), "b-open": (open_sha,), "b-seat": (seat_sha,)},
                 frozenset({"b-open"}))
    rows, report = classify(repo, prs, tmp_path)
    assert rows["clean"].removable and "merged PR head" in rows["clean"].reason
    assert not rows["dirty"].removable and "dirty (1): scratch.txt" in rows["dirty"].reason
    assert not rows["unmerged"].removable and rows["unmerged"].reason.startswith("unmerged")
    assert not rows["openpr"].removable and rows["openpr"].reason == "open PR"
    assert not rows["seat"].removable and "seat worktree: seat-role" in rows["seat"].reason
    assert not rows["main"].removable and rows["main"].reason == "main checkout"
    assert [Path(r.path).name for r in report.removable()] == ["clean"]


def test_a_dirty_monitoring_shard_is_named_not_ignored(repo, tmp_path):
    path, sha = add_worktree(repo, "shardy", "b-shard")
    rel = AGENT_MONITORING / "data" / "2026-W41" / "x.tools.jsonl"
    shard = path / rel
    shard.parent.mkdir(parents=True)
    shard.write_text("{}\n")
    rows, _ = classify(repo, PrData({"b-shard": (sha,)}, frozenset()), tmp_path)
    assert not rows["shardy"].removable
    assert posix(rel) in rows["shardy"].reason


def test_a_tip_that_moved_after_the_merged_pr_is_kept(repo, tmp_path):
    path, sha = add_worktree(repo, "moved", "b-moved")
    (path / "more.txt").write_text("later")
    git(path, "add", "more.txt")
    git(path, "commit", "-q", "-m", "later work")
    rows, _ = classify(repo, PrData({"b-moved": (sha,)}, frozenset()), tmp_path)
    assert not rows["moved"].removable and "tip moved after it" in rows["moved"].reason


def test_a_writer_lease_or_a_live_instance_makes_it_a_seat(repo, tmp_path):
    leased, leased_sha = add_worktree(repo, "leased", "b-leased")
    live, live_sha = add_worktree(repo, "livey", "b-live")
    sroot = tmp_path / "state"
    st.take_lease(sroot, leased, "seat-role", "s1", None)
    me = st.process_identity(os.getpid())
    binding = st.Binding("s2", "seat-role", "startup", str(live), "b-live", "", me, "d", "2026-10-08T00:00:00Z")
    st.record_start(sroot, binding)
    prs = PrData({"b-leased": (leased_sha,), "b-live": (live_sha,)}, frozenset())
    rows, _ = classify(repo, prs, tmp_path)
    assert "writer lease held by seat-role" in rows["leased"].reason
    assert "live session instance" in rows["livey"].reason and not rows["livey"].removable


def test_a_process_with_its_cwd_inside_keeps_the_worktree(repo, tmp_path):
    path, sha = add_worktree(repo, "busy", "b-busy")
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], cwd=str(path))
    try:
        rows, _ = classify(repo, PrData({"b-busy": (sha,)}, frozenset()), tmp_path)
        assert not rows["busy"].removable and f"pid {proc.pid}" in rows["busy"].reason
    finally:
        proc.kill()
        proc.wait()


def test_gh_unavailable_keeps_everything_with_one_summary_line(repo, tmp_path):
    add_worktree(repo, "a", "b-a")
    add_worktree(repo, "b", "b-b")
    rows, report = classify(repo, None, tmp_path)
    assert not report.removable() and not report.gh_ok
    text = pb.render_worktrees(report)
    assert text.count("gh unavailable") == 1 and "nothing could be proven merged" in text
    assert "[b-a]" not in text  # no per-row spam


def test_dry_run_changes_nothing(repo, tmp_path, monkeypatch, capsys):
    path, sha = add_worktree(repo, "clean", "b-clean")
    monkeypatch.setattr(pb, "fetch_prs", lambda cwd: PrData({"b-clean": (sha,)}, frozenset()))
    monkeypatch.setattr(st, "state_root", lambda *_: tmp_path / "state")
    monkeypatch.setattr("tools.sessions.roster.load_roster", lambda root: ROSTER)
    before = git(repo, "worktree", "list", "--porcelain")
    assert pb.main(["--root", str(repo), "--worktrees"]) == 0
    assert "dry run: nothing removed" in capsys.readouterr().out
    assert git(repo, "worktree", "list", "--porcelain") == before and path.is_dir()


def test_execute_removes_only_removable_never_forces_and_keeps_branches(repo, tmp_path, monkeypatch, capsys):
    clean, clean_sha = add_worktree(repo, "clean", "b-clean")
    dirty, dirty_sha = add_worktree(repo, "dirty", "b-dirty")
    (dirty / "scratch.txt").write_text("x")
    monkeypatch.setattr(pb, "fetch_prs", lambda cwd: PrData({"b-clean": (clean_sha,), "b-dirty": (dirty_sha,)}, frozenset()))
    monkeypatch.setattr(st, "state_root", lambda *_: tmp_path / "state")
    monkeypatch.setattr("tools.sessions.roster.load_roster", lambda root: ROSTER)
    calls = []
    real_git = pb._git
    monkeypatch.setattr(pb, "_git", lambda args, cwd: calls.append(list(args)) or real_git(args, cwd))
    backup = tmp_path / "worktree-backup.txt"
    assert pb.main(["--root", str(repo), "--worktrees", "--execute", "--backup", str(backup)]) == 0
    out = capsys.readouterr().out
    assert not clean.exists() and dirty.is_dir()
    assert f"removed {clean}" in out and "freed about" in out and "git worktree add" in out
    assert backup.read_text().splitlines() == [f"{clean} b-clean {clean_sha}"]
    assert "b-clean" in git(repo, "branch", "--list", "b-clean")  # the branch survives
    assert all("--force" not in c and "-f" not in c for c in calls if c[:2] == ["worktree", "remove"])
    assert any(c[:2] == ["worktree", "remove"] for c in calls)


def test_a_removal_git_refuses_is_reported_not_forced(repo, tmp_path):
    path, sha = add_worktree(repo, "clean", "b-clean")
    _, report = classify(repo, PrData({"b-clean": (sha,)}, frozenset()), tmp_path)
    (path / "late.txt").write_text("appeared after classification")  # git itself now refuses
    lines = pb.execute_worktrees(repo, report)
    assert any(line.startswith("left ") for line in lines) and path.is_dir()


def test_worktrees_with_remote_is_rejected(repo):
    with pytest.raises(SystemExit):
        pb.main(["--root", str(repo), "--worktrees", "--remote"])
