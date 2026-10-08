#!/usr/bin/env python3
"""Branch hygiene: dry-run classification, a name-to-SHA backup, and guarded deletion (plan section 8).

Codifies the cleanup done by hand on 2026-10-02. The default is a dry run that changes no ref. Classes:

  merged-PR       a merged PR's head SHA equals the branch tip. The only deletable class.
  hint-only       every commit subject on the branch is already a subject in main. Informational: under
                  squash merges, rebases and edited messages this does not prove the work is integrated,
                  so it is never deletion safety.
  unique-commits  everything else (including a branch whose tip moved after its PR merged). Listed with
                  the tip author, never deleted.
  skipped         checked out in a worktree, has an open PR, is newer than 7 days, or is main. When `gh`
                  is unavailable nothing can be proven merged, so every branch is skipped.

`--execute` deletes the merged-PR local branches (`git update-ref -d` with the expected SHA, so a branch that
moved since classification is left alone). Remote branches are deleted only with the additional `--remote`
flag, only when the PR merged and the remote-tracking tip equals the PR head, one
`--force-with-lease=<ref>:<sha>` push per branch. A backup file (name and SHA per line) is written and
read back before the first deletion. A remote delete is visible to everyone: the owner's call.

`--worktrees` (TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE) classifies WORKTREES instead, the case branch mode
skips ("checked out in a worktree"). A worktree is removable only when its branch tip equals a merged PR head,
the tree is completely clean (a dirty monitoring shard is named, never ignored), it is not a session seat
(roster path, writer lease or live instance), has no open PR and no process has its cwd inside. `--execute` runs
`git worktree remove` WITHOUT `--force`, keeps the branches, and writes a separate name-to-SHA backup.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from tools.sessions import state as st
from tools.sessions.launch import _worktree_entries as worktree_entries
from tools.sessions.resolve import instance_ids
from tools.sessions.roster import REPO_ROOT

STALE_DAYS = 7
GH_TIMEOUT_SECONDS = 60
PR_LIMIT = 2000
PROTECTED = ("main", "master")
REMOTE = "origin"

MERGED = "merged-PR"
HINT_ONLY = "hint-only"
UNIQUE = "unique-commits"
SKIPPED = "skipped"
CLASSES = (MERGED, HINT_ONLY, UNIQUE, SKIPPED)


@dataclass(frozen=True)
class PrData:
    """What `gh` says: merged head SHAs by branch name, and the branch names with an open PR."""

    merged: dict[str, tuple[str, ...]]
    open_heads: frozenset[str]


@dataclass(frozen=True)
class BranchRow:
    name: str
    sha: str
    cls: str
    reason: str
    owner: str
    age_days: float


@dataclass(frozen=True)
class RemoteRow:
    name: str
    sha: str
    deletable: bool
    reason: str


@dataclass(frozen=True)
class Report:
    local: tuple[BranchRow, ...]
    remote: tuple[RemoteRow, ...]
    gh_ok: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def deletable_local(self) -> list[BranchRow]:
        return [r for r in self.local if r.cls == MERGED]

    def deletable_remote(self) -> list[RemoteRow]:
        return [r for r in self.remote if r.deletable]


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "--no-optional-locks", *args], cwd=str(cwd), capture_output=True, text=True, check=False)


def fetch_prs(cwd: Path) -> PrData | None:
    """Merged and open PR data from `gh`; None when gh is missing, blocked or answers badly."""
    try:
        merged = subprocess.run(
            ["gh", "pr", "list", "--state", "merged", "--limit", str(PR_LIMIT), "--json", "headRefName,headRefOid"],
            cwd=str(cwd), capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS, check=False,
        )
        opened = subprocess.run(
            ["gh", "pr", "list", "--state", "open", "--limit", str(PR_LIMIT), "--json", "headRefName"],
            cwd=str(cwd), capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS, check=False,
        )
        if merged.returncode != 0 or opened.returncode != 0:
            return None
        by_name: dict[str, list[str]] = {}
        for pr in json.loads(merged.stdout or "[]"):
            by_name.setdefault(pr["headRefName"], []).append(pr["headRefOid"])
        return PrData({k: tuple(v) for k, v in by_name.items()}, frozenset(p["headRefName"] for p in json.loads(opened.stdout or "[]")))
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return None


def _main_ref(cwd: Path) -> str | None:
    for ref in ("origin/main", "main"):
        if _git(["rev-parse", "--verify", "--quiet", ref], cwd).returncode == 0:
            return ref
    return None


def _checked_out(cwd: Path) -> set[str]:
    return {str(e["branch"]).removeprefix("refs/heads/") for e in worktree_entries(cwd) if e.get("branch")}


def _subjects(cwd: Path, revspec: str) -> list[str]:
    return _git(["log", "--format=%s", revspec], cwd).stdout.splitlines()


def _hint(cwd: Path, main_ref: str | None, main_subjects: set[str], name: str) -> str | None:
    """Why the branch looks integrated (a hint, not proof), or None."""
    if main_ref is None:
        return None
    own = _subjects(cwd, f"{main_ref}..refs/heads/{name}")
    if not own:
        return "no commits beyond main (tip is reachable from main)"
    if all(s in main_subjects for s in own):
        return "all commit subjects already in main (hint, not proof)"
    return None


def classify(cwd: Path, prs: PrData | None, now: float | None = None) -> Report:
    now = time.time() if now is None else now
    main_ref = _main_ref(cwd)
    main_subjects = set(_subjects(cwd, main_ref)) if main_ref else set()
    checked_out = _checked_out(cwd)
    fmt = "%(refname:short)%09%(objectname)%09%(committerdate:unix)%09%(authorname)"
    rows: list[BranchRow] = []
    for line in _git(["for-each-ref", f"--format={fmt}", "refs/heads"], cwd).stdout.splitlines():
        name, sha, ts, owner = line.split("\t", 3)
        age = (now - float(ts)) / 86400

        def row(cls: str, reason: str, name: str = name, sha: str = sha, owner: str = owner, age: float = age) -> BranchRow:
            return BranchRow(name, sha, cls, reason, owner, age)

        if name in PROTECTED:
            rows.append(row(SKIPPED, "protected branch"))
        elif name in checked_out:
            rows.append(row(SKIPPED, "checked out in a worktree"))
        elif prs is None:
            rows.append(row(SKIPPED, "gh unavailable: nothing can be proven merged"))
        elif name in prs.open_heads:
            rows.append(row(SKIPPED, "open PR"))
        elif age < STALE_DAYS:
            rows.append(row(SKIPPED, f"newer than {STALE_DAYS} days"))
        elif sha in prs.merged.get(name, ()):
            rows.append(row(MERGED, "tip equals the merged PR head"))
        elif name in prs.merged:
            rows.append(row(UNIQUE, "a PR merged from this name but the tip moved after it (later work)"))
        elif hint := _hint(cwd, main_ref, main_subjects, name):
            rows.append(row(HINT_ONLY, hint))
        else:
            rows.append(row(UNIQUE, "commits not proven integrated"))
    return Report(tuple(rows), tuple(_remote_rows(cwd, prs, checked_out)), gh_ok=prs is not None)


def _remote_rows(cwd: Path, prs: PrData | None, checked_out: set[str]) -> list[RemoteRow]:
    out = []
    prefix = f"refs/remotes/{REMOTE}/"
    for line in _git(["for-each-ref", "--format=%(refname)%09%(objectname)", prefix], cwd).stdout.splitlines():
        ref, sha = line.split("\t", 1)
        name = ref.removeprefix(prefix)
        if name in PROTECTED or name == "HEAD":
            continue
        if prs is None:
            out.append(RemoteRow(name, sha, False, "gh unavailable"))
        elif name in prs.open_heads:
            out.append(RemoteRow(name, sha, False, "open PR"))
        elif name in checked_out:
            out.append(RemoteRow(name, sha, False, "checked out in a worktree"))
        elif sha in prs.merged.get(name, ()):
            out.append(RemoteRow(name, sha, True, "remote tip equals the merged PR head"))
        elif name in prs.merged:
            out.append(RemoteRow(name, sha, False, "remote tip moved after the PR merged"))
    return out


def write_backup(report: Report, path: Path, include_remote: bool) -> Path:
    """Write `<name> <sha>` lines for everything about to be deleted, then read the file back to verify it."""
    lines = [f"{r.name} {r.sha}" for r in report.deletable_local()]
    if include_remote:
        lines += [f"{REMOTE}/{r.name} {r.sha}" for r in report.deletable_remote()]
    target = path
    n = 2
    while target.exists():
        target = path.with_name(f"{path.stem}-{n}{path.suffix}")
        n += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if target.read_text(encoding="utf-8").splitlines() != lines:
        raise OSError(f"backup {target} did not read back as written; nothing was deleted")
    return target


def restore_commands(report: Report, include_remote: bool) -> list[str]:
    cmds = [f"git branch {r.name} {r.sha}" for r in report.deletable_local()]
    if include_remote:
        cmds += [f"git push {REMOTE} {r.sha}:refs/heads/{r.name}" for r in report.deletable_remote()]
    return cmds


def execute(cwd: Path, report: Report, remote: bool) -> list[str]:
    """Delete what the report marks deletable; each deletion is guarded by the expected SHA."""
    done = []
    for r in report.deletable_local():
        res = _git(["update-ref", "-d", f"refs/heads/{r.name}", r.sha], cwd)
        done.append(f"deleted local {r.name}" if res.returncode == 0 else f"left local {r.name}: {res.stderr.strip()}")
    if remote:
        for r in report.deletable_remote():
            ref = f"refs/heads/{r.name}"
            res = subprocess.run(
                ["git", "push", f"--force-with-lease={ref}:{r.sha}", REMOTE, f":{ref}"],
                cwd=str(cwd), capture_output=True, text=True, check=False,
            )
            done.append(f"deleted remote {r.name}" if res.returncode == 0 else f"left remote {r.name}: {res.stderr.strip()}")
    return done


def render(report: Report, remote: bool) -> str:
    lines = []
    if not report.gh_ok:
        lines.append("gh unavailable: every branch is skipped, nothing is deletable")
    for cls in CLASSES:
        rows = [r for r in report.local if r.cls == cls]
        lines.append(f"{cls}: {len(rows)}")
        for r in rows:
            owner = f" [{r.owner}]" if cls in (UNIQUE, HINT_ONLY) else ""
            lines.append(f"  {r.name} {r.sha[:9]} {r.age_days:.0f}d{owner}  {r.reason}")
    if remote:
        lines.append(f"remote deletable: {len(report.deletable_remote())} (remote-tracking refs; fetch first for current tips)")
        for r in report.deletable_remote():
            lines.append(f"  {REMOTE}/{r.name} {r.sha[:9]}")
        skipped = [r for r in report.remote if not r.deletable]
        lines.append(f"remote not deletable: {len(skipped)}")
        lines += [f"  {REMOTE}/{r.name}  {r.reason}" for r in skipped]
    return "\n".join(lines)


# ---- worktree mode (TCK-20261008-SESSION-MERGED-WORKTREE-PRUNE) --------------------------------
DIRTY_LISTED = 10


@dataclass(frozen=True)
class WorktreeRow:
    path: str
    branch: str
    sha: str
    removable: bool
    reason: str
    size_bytes: int


@dataclass(frozen=True)
class WorktreeReport:
    rows: tuple[WorktreeRow, ...]
    gh_ok: bool = True

    def removable(self) -> list[WorktreeRow]:
        return [r for r in self.rows if r.removable]


def _seat_paths(main: Path, roster) -> dict[str, str]:
    """Resolved worktree path -> why it is a seat, from the roster."""
    names = {r.worktree: r.role for r in roster.roles}
    names.update({w.name: w.writer or "shared worktree" for w in roster.worktrees})
    return {str((main / ".claude" / "worktrees" / n).resolve()): who for n, who in names.items()}


def _live_instance_paths(sroot: Path, roster) -> dict[str, str]:
    """Resolved worktree path -> instance id, for every live session instance."""
    found: dict[str, str] = {}
    for role in roster.roles:
        for iid in instance_ids(role.role, role.max_sessions):
            instance = st.read_instance(sroot, iid)
            if instance is not None and st.liveness(instance) == st.LIVE:
                found[str(Path(instance.holder.worktree).resolve())] = iid
    return found


def _processes_inside(path: Path, proc_root: Path = Path("/proc")) -> list[int]:
    prefix = str(path.resolve())
    pids = []
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return pids
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            cwd = os.readlink(entry / "cwd")
        except OSError:
            continue
        if cwd == prefix or cwd.startswith(prefix + os.sep):
            pids.append(int(entry.name))
    return sorted(pids)


def _dirty_paths(path: Path) -> list[str]:
    out = _git(["status", "--porcelain", "--untracked-files=all"], path)
    return [line[3:] for line in out.stdout.splitlines()] if out.returncode == 0 else ["(git status failed)"]


def _tree_bytes(path: Path) -> int:
    out = subprocess.run(["du", "-s", "--block-size=1", str(path)], capture_output=True, text=True, check=False)
    try:
        return int(out.stdout.split()[0])
    except (IndexError, ValueError):
        return 0


def classify_worktrees(cwd: Path, prs: PrData | None, roster, sroot: Path, proc_root: Path = Path("/proc")) -> WorktreeReport:
    main = Path(st.common_dir(cwd)).parent.resolve()
    seats = _seat_paths(main, roster)
    live = _live_instance_paths(sroot, roster)
    rows: list[WorktreeRow] = []
    for entry in worktree_entries(cwd):
        path = Path(str(entry["worktree"]))
        resolved = str(path.resolve())
        branch = str(entry.get("branch", "")).removeprefix("refs/heads/")
        sha = str(entry.get("HEAD", ""))

        def row(removable: bool, reason: str, path: Path = path, branch: str = branch, sha: str = sha) -> WorktreeRow:
            return WorktreeRow(str(path), branch or "(detached)", sha, removable, reason,
                               _tree_bytes(path) if removable and path.is_dir() else 0)

        lease = None
        lease_error = ""
        try:
            lease = st.read_lease(sroot, resolved)
        except st.StateError as exc:
            lease_error = str(exc)
        if resolved == str(main):
            rows.append(row(False, "main checkout"))
        elif entry.get("bare") or entry.get("prunable") or not path.is_dir():
            rows.append(row(False, "bare, prunable or missing directory"))
        elif not branch:
            rows.append(row(False, "detached HEAD"))
        elif resolved in seats:
            rows.append(row(False, f"seat worktree: {seats[resolved]}"))
        elif resolved in live:
            rows.append(row(False, f"live session instance: {live[resolved]}"))
        elif lease is not None:
            rows.append(row(False, f"writer lease held by {lease.role}"))
        elif lease_error:
            rows.append(row(False, f"lease unreadable: {lease_error}"))
        elif prs is None:
            rows.append(row(False, "gh unavailable: nothing can be proven merged"))
        elif branch in prs.open_heads:
            rows.append(row(False, "open PR"))
        elif sha not in prs.merged.get(branch, ()):
            why = "a PR merged from this name but the tip moved after it" if branch in prs.merged else "no merged PR with this tip"
            rows.append(row(False, f"unmerged: {why}"))
        elif pids := _processes_inside(path, proc_root):
            rows.append(row(False, f"process inside: pid {', '.join(map(str, pids[:5]))}"))
        elif dirty := _dirty_paths(path):
            shown = ", ".join(dirty[:DIRTY_LISTED]) + (f" (+{len(dirty) - DIRTY_LISTED} more)" if len(dirty) > DIRTY_LISTED else "")
            rows.append(row(False, f"dirty ({len(dirty)}): {shown}"))
        else:
            rows.append(row(True, "tip equals the merged PR head, clean, no seat, no process inside"))
    return WorktreeReport(tuple(rows), gh_ok=prs is not None)


def render_worktrees(report: WorktreeReport) -> str:
    lines = []
    if not report.gh_ok:
        lines.append("gh unavailable: nothing could be proven merged, so every worktree is kept")
    removable = report.removable()
    lines.append(f"removable: {len(removable)} ({sum(r.size_bytes for r in removable) / 1024**3:.1f} GB)")
    lines += [f"  {r.path} [{r.branch}] {r.size_bytes / 1024**3:.2f} GB" for r in removable]
    kept = [r for r in report.rows if not r.removable]
    lines.append(f"kept: {len(kept)}")
    if report.gh_ok:
        lines += [f"  {r.path} [{r.branch}]  {r.reason}" for r in kept]
    return "\n".join(lines)


def write_worktree_backup(report: WorktreeReport, path: Path) -> Path:
    """Write `<path> <branch> <sha>` for each worktree about to be removed, then read it back."""
    lines = [f"{r.path} {r.branch} {r.sha}" for r in report.removable()]
    target, n = path, 2
    while target.exists():
        target = path.with_name(f"{path.stem}-{n}{path.suffix}")
        n += 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if target.read_text(encoding="utf-8").splitlines() != lines:
        raise OSError(f"backup {target} did not read back as written; nothing was removed")
    return target


def worktree_restore_commands(report: WorktreeReport) -> list[str]:
    return [f"git worktree add {r.path} {r.branch}" for r in report.removable()]


def execute_worktrees(cwd: Path, report: WorktreeReport) -> list[str]:
    """`git worktree remove` (never --force) for each removable row; git's own refusal is reported, not overridden."""
    done, freed = [], 0
    for r in report.removable():
        res = _git(["worktree", "remove", r.path], cwd)
        if res.returncode == 0:
            done.append(f"removed {r.path}")
            freed += r.size_bytes
        else:
            done.append(f"left {r.path}: {res.stderr.strip()}")
    done.append(f"freed about {freed / 1024**3:.1f} GB")
    return done


def default_worktree_backup_path(today: date | None = None) -> Path:
    return Path.home() / "Working" / f"worktree-backup-{(today or date.today()).isoformat()}.txt"


def _main_worktrees(args) -> int:
    from tools.sessions.roster import load_roster

    roster = load_roster(args.root)
    sroot = st.state_root(args.root)
    report = classify_worktrees(args.root, fetch_prs(args.root), roster, sroot)
    print(render_worktrees(report))
    if not args.execute:
        print("\ndry run: nothing removed. Re-run with --worktrees --execute to remove the worktrees listed as removable.")
        return 0
    if not report.removable():
        print("\nnothing removable.")
        return 0
    backup = write_worktree_backup(report, args.backup or default_worktree_backup_path())
    print(f"\nbackup written and verified: {backup}")
    print("restore with:")
    print("\n".join(f"  {c}" for c in worktree_restore_commands(report)))
    print("\n".join(execute_worktrees(args.root, report)))
    return 0


def default_backup_path(today: date | None = None) -> Path:
    return Path.home() / "Working" / f"branch-backup-{(today or date.today()).isoformat()}.txt"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify branches; delete merged-PR ones only with --execute.")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--execute", action="store_true", help="delete the merged-PR local branches after writing the backup")
    parser.add_argument("--remote", action="store_true", help="also list (and with --execute, delete) merged-PR remote branches")
    parser.add_argument("--backup", type=Path, default=None, help="backup file (default ~/Working/branch-backup-<date>.txt)")
    parser.add_argument("--worktrees", action="store_true", help="classify worktrees instead of branches; with --execute remove "
                        "the merged, clean, non-seat ones (git worktree remove, never --force; branches are kept)")
    args = parser.parse_args(argv)
    if args.worktrees:
        if args.remote:
            parser.error("--worktrees cannot be combined with --remote")
        return _main_worktrees(args)
    if args.remote and not args.execute:
        print("note: --remote without --execute only lists remote candidates")
    report = classify(args.root, fetch_prs(args.root))
    print(render(report, args.remote))
    if not args.execute:
        print("\ndry run: no ref changed. Re-run with --execute to delete the merged-PR branches listed above.")
        return 0
    if not report.deletable_local() and not (args.remote and report.deletable_remote()):
        print("\nnothing deletable.")
        return 0
    backup = write_backup(report, args.backup or default_backup_path(), args.remote)
    print(f"\nbackup written and verified: {backup}")
    print("restore with:")
    print("\n".join(f"  {c}" for c in restore_commands(report, args.remote)))
    print("\n".join(execute(args.root, report, args.remote)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
