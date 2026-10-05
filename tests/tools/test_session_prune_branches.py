"""Branch pruning (session-layer M4b): conservative classes, backup before deletion, guarded execution."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from tools.sessions import prune_branches as pb
from tools.sessions.prune_branches import HINT_ONLY, MERGED, SKIPPED, UNIQUE, PrData, classify

NOW = time.time()
DAY = 86400
BASE_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
}


def git(cwd: Path, *args: str, age_days: float = 30) -> str:
    stamp = f"{int(NOW - age_days * DAY)} +0000"
    env = {**BASE_ENV, "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
    res = subprocess.run(["git", *args], cwd=str(cwd), env=env, capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def commit(cwd: Path, name: str, msg: str, age_days: float = 30) -> str:
    (cwd / name).write_text(msg)
    git(cwd, "add", name)
    git(cwd, "commit", "-q", "-m", msg, age_days=age_days)
    return git(cwd, "rev-parse", "HEAD")


def branch(work: Path, name: str, *commits: tuple[str, str], age_days: float = 30) -> str:
    git(work, "checkout", "-q", "-b", name, "main")
    sha = ""
    for fname, msg in commits:
        sha = commit(work, fname, msg, age_days)
    git(work, "checkout", "-q", "main")
    return sha


@pytest.fixture
def work(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    path = tmp_path / "work"
    git(tmp_path, "clone", "-q", str(origin), str(path))
    git(path, "checkout", "-q", "-b", "main")
    commit(path, "base.txt", "base")
    git(path, "push", "-q", "origin", "main")
    return path


def refs(work: Path) -> str:
    return git(work, "for-each-ref", "--format=%(refname) %(objectname)")


def by_name(report: pb.Report) -> dict[str, pb.BranchRow]:
    return {r.name: r for r in report.local}


def test_merged_pr_branch_is_the_only_deletable_class(work: Path) -> None:
    sha = branch(work, "done", ("d.txt", "done work"))
    branch(work, "other", ("o.txt", "other work"))
    rows = by_name(classify(work, PrData({"done": (sha,)}, frozenset()), NOW))
    assert rows["done"].cls == MERGED
    assert rows["other"].cls == UNIQUE
    assert rows["main"].cls == SKIPPED


def test_squash_merged_branch_with_later_unmerged_commits_is_never_deletable(work: Path) -> None:
    old_head = branch(work, "feat", ("f1.txt", "feature one"))
    git(work, "checkout", "-q", "feat")
    commit(work, "f2.txt", "later unmerged work")
    git(work, "checkout", "-q", "main")
    # the PR squash-merged the first commit only: main carries its subject, the branch tip moved on
    commit(work, "f1.txt", "feature one")
    report = classify(work, PrData({"feat": (old_head,)}, frozenset()), NOW)
    row = by_name(report)["feat"]
    assert row.cls == UNIQUE and "tip moved" in row.reason
    assert report.deletable_local() == []


def test_hint_only_is_its_own_class_and_never_deletable(work: Path) -> None:
    branch(work, "hinted", ("h.txt", "same subject as main"))
    commit(work, "other.txt", "same subject as main")  # main now carries the subject under another SHA
    git(work, "push", "-q", "origin", "main")
    report = classify(work, PrData({}, frozenset()), NOW)
    assert by_name(report)["hinted"].cls == HINT_ONLY
    assert report.deletable_local() == []


def test_checked_out_open_pr_and_young_branches_are_skipped(work: Path, tmp_path: Path) -> None:
    sha_wt = branch(work, "in-worktree", ("w.txt", "w"))
    sha_open = branch(work, "has-pr", ("p.txt", "p"))
    sha_young = branch(work, "young", ("y.txt", "y"), age_days=1)
    git(work, "worktree", "add", "-q", str(tmp_path / "wt"), "in-worktree")
    prs = PrData({"in-worktree": (sha_wt,), "has-pr": (sha_open,), "young": (sha_young,)}, frozenset({"has-pr"}))
    rows = by_name(classify(work, prs, NOW))
    assert {rows[n].cls for n in ("in-worktree", "has-pr", "young")} == {SKIPPED}
    assert "worktree" in rows["in-worktree"].reason and "open PR" in rows["has-pr"].reason and "days" in rows["young"].reason


def test_gh_unavailable_skips_everything(work: Path) -> None:
    branch(work, "a", ("a.txt", "a"))
    report = classify(work, None, NOW)
    assert not report.gh_ok and {r.cls for r in report.local} == {SKIPPED}
    assert report.deletable_local() == [] and report.deletable_remote() == []
    assert "gh unavailable" in pb.render(report, remote=False)


def test_dry_run_changes_no_ref(work: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    sha = branch(work, "done", ("d.txt", "d"))
    git(work, "push", "-q", "origin", "done")
    before = refs(work)
    monkeypatch.setattr(pb, "fetch_prs", lambda cwd: PrData({"done": (sha,)}, frozenset()))
    assert pb.main(["--root", str(work), "--remote"]) == 0
    assert refs(work) == before
    out = capsys.readouterr().out
    assert "dry run" in out and "origin/done" in out


def test_execute_writes_backup_first_and_restore_works(work: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sha = branch(work, "done", ("d.txt", "d"))
    keep = branch(work, "keep", ("k.txt", "k"))
    backup = tmp_path / "backups" / "b.txt"
    seen: dict[str, bool] = {}
    real_execute = pb.execute

    def checking_execute(cwd, report, remote):
        seen["backup_exists_before_delete"] = backup.exists() and "done " in backup.read_text()
        return real_execute(cwd, report, remote)

    monkeypatch.setattr(pb, "fetch_prs", lambda cwd: PrData({"done": (sha,)}, frozenset()))
    monkeypatch.setattr(pb, "execute", checking_execute)
    assert pb.main(["--root", str(work), "--execute", "--backup", str(backup)]) == 0
    assert seen == {"backup_exists_before_delete": True}
    names = git(work, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    assert "done" not in names.split() and "keep" in names.split()
    name, recorded = backup.read_text().split()
    git(work, "branch", name, recorded)  # the restore command the tool prints
    assert git(work, "rev-parse", "done") == sha and git(work, "rev-parse", "keep") == keep


def test_branch_that_moved_since_classification_is_left_alone(work: Path) -> None:
    sha = branch(work, "done", ("d.txt", "d"))
    report = classify(work, PrData({"done": (sha,)}, frozenset()), NOW)
    git(work, "checkout", "-q", "done")
    commit(work, "late.txt", "late")
    git(work, "checkout", "-q", "main")
    result = pb.execute(work, report, remote=False)
    assert result[0].startswith("left local done")
    assert "done" in git(work, "for-each-ref", "--format=%(refname:short)", "refs/heads").split()


def test_remote_deleted_only_when_tip_equals_merged_head(work: Path, tmp_path: Path) -> None:
    sha = branch(work, "same", ("s.txt", "s"))
    branch(work, "moved", ("m.txt", "m1"))
    git(work, "push", "-q", "origin", "same", "moved")
    git(work, "checkout", "-q", "moved")
    commit(work, "m2.txt", "m2")
    git(work, "push", "-q", "origin", "moved")  # remote tip moved after the PR merged
    git(work, "checkout", "-q", "main")
    old_moved = git(work, "rev-parse", "moved~1")
    prs = PrData({"same": (sha,), "moved": (old_moved,)}, frozenset())
    report = classify(work, prs, NOW)
    remote = {r.name: r for r in report.remote}
    assert remote["same"].deletable and not remote["moved"].deletable and "moved" in remote["moved"].reason
    pb.execute(work, report, remote=True)
    heads = git(tmp_path, "--git-dir", str(tmp_path / "origin.git"), "for-each-ref", "--format=%(refname:short)", "refs/heads")
    assert "same" not in heads.split() and "moved" in heads.split()


def test_remote_not_touched_without_remote_flag(work: Path, tmp_path: Path) -> None:
    sha = branch(work, "same", ("s.txt", "s"))
    git(work, "push", "-q", "origin", "same")
    report = classify(work, PrData({"same": (sha,)}, frozenset()), NOW)
    pb.execute(work, report, remote=False)
    heads = git(tmp_path, "--git-dir", str(tmp_path / "origin.git"), "for-each-ref", "--format=%(refname:short)", "refs/heads")
    assert "same" in heads.split()


def test_backup_never_overwrites_an_existing_file(work: Path, tmp_path: Path) -> None:
    sha = branch(work, "done", ("d.txt", "d"))
    report = classify(work, PrData({"done": (sha,)}, frozenset()), NOW)
    first = pb.write_backup(report, tmp_path / "b.txt", include_remote=False)
    second = pb.write_backup(report, tmp_path / "b.txt", include_remote=False)
    assert first != second and first.read_text() == second.read_text()


def test_fetch_prs_failure_is_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def boom(*a, **k):
        raise FileNotFoundError("gh")

    monkeypatch.setattr(pb.subprocess, "run", boom)
    assert pb.fetch_prs(tmp_path) is None


def test_branch_already_contained_in_main_is_hint_only(work: Path) -> None:
    git(work, "branch", "contained", "main", age_days=30)
    row = by_name(classify(work, PrData({}, frozenset()), NOW))["contained"]
    assert row.cls == HINT_ONLY and "reachable from main" in row.reason
