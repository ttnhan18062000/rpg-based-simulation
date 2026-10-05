#!/usr/bin/env python3
"""What is in flight, per worktree and per seat (plan sections 8 and 11). Strictly read-only.

Reports: each worktree's branch, dirty state, git operation left in progress, open PR, size, last commit and
last activity; each seat's worktree, staffing and instance state (from the role-state directory written by
`tools/sessions/state.py`); a disk-budget warning past 85% of the volume that names the largest worktrees; and
worktrees that look removable, each with the exact `git worktree remove` command for the owner to run.

Nothing here prunes, fetches, writes a file or changes a ref: git is invoked with `--no-optional-locks` so even
`git status` leaves the index alone. A failing `gh` degrades to `pr: unknown`; the view never fails because of it.
Exit code is 0 unless the manifest cannot load.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from tools.sessions import state as st
from tools.sessions.launch import _worktree_entries as worktree_entries
from tools.sessions.launch import default_worktree_path, git_operation_in_progress, main_checkout
from tools.sessions.roster import REPO_ROOT, Role, Roster, RosterError, load_roster

DISK_WARN_FRACTION = 0.85
RETIRE_IDLE_DAYS = 14
GH_TIMEOUT_SECONDS = 20

PR_UNKNOWN = "unknown"
PR_NONE = "none"
INSTANCE_UNKNOWN = "unknown (M2 not present)"
INSTANCE_NONE = "none"

VolumeReader = Callable[[Path], tuple[int, int]]  # path -> (used bytes, total bytes)
SizeReader = Callable[[Path], int]


@dataclass(frozen=True)
class WorktreeInfo:
    path: Path
    branch: str | None
    head: str
    dirty: int | None  # number of changed paths; None when the directory is missing
    operations: tuple[str, ...]
    pr: str  # "#<n>", PR_NONE or PR_UNKNOWN
    size_bytes: int
    last_commit: str  # ISO timestamp, "" when unknown
    last_subject: str
    last_activity: float  # epoch seconds; 0.0 when unknown
    unique_commits: int | None  # commits not in main; None when main cannot be resolved
    prunable: bool
    is_main: bool


@dataclass(frozen=True)
class SeatInfo:
    role: str
    worktree: str
    seat_status: str
    instance: str  # live | orphaned | released | none | INSTANCE_UNKNOWN
    session_id: str | None


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "--no-optional-locks", *args], cwd=str(cwd), capture_output=True, text=True, check=False)


def disk_usage_of(path: Path) -> tuple[int, int]:
    usage = shutil.disk_usage(path)
    return usage.used, usage.total


def tree_size(path: Path) -> int:
    """Bytes on disk, via `du -sk`; 0 when the tree cannot be measured."""
    try:
        out = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, check=False)
        return int(out.stdout.split()[0]) * 1024 if out.returncode == 0 and out.stdout.strip() else 0
    except (OSError, ValueError, IndexError):
        return 0


def open_pr(branch: str | None, cwd: Path) -> str:
    """`#<n>` for an open PR on the branch, PR_NONE, or PR_UNKNOWN when gh is missing, blocked or answers badly."""
    if not branch:
        return PR_NONE
    try:
        res = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--state", "open", "--json", "number"],
            cwd=str(cwd), capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS, check=False,
        )
        if res.returncode != 0:
            return PR_UNKNOWN
        numbers = [p["number"] for p in json.loads(res.stdout or "[]")]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        return PR_UNKNOWN
    return ", ".join(f"#{n}" for n in numbers) if numbers else PR_NONE


def _main_ref(cwd: Path) -> str | None:
    for ref in ("origin/main", "main"):
        if _git(["rev-parse", "--verify", "--quiet", ref], cwd).returncode == 0:
            return ref
    return None


def _activity(path: Path, commit_epoch: float) -> float:
    git_dir = _git(["rev-parse", "--absolute-git-dir"], path)
    index = Path(git_dir.stdout.strip()) / "index" if git_dir.returncode == 0 else None
    try:
        return max(commit_epoch, index.stat().st_mtime) if index else commit_epoch
    except OSError:
        return commit_epoch


def inspect_worktree(entry: dict, main: Path, pr_reader: Callable[[str | None, Path], str] = open_pr,
                     size_reader: SizeReader = tree_size) -> WorktreeInfo:
    path = Path(entry["worktree"])
    branch = str(entry["branch"]).removeprefix("refs/heads/") if entry.get("branch") else None
    prunable = "prunable" in entry or not path.is_dir()
    is_main = path.resolve() == main.resolve()
    if prunable:
        return WorktreeInfo(path, branch, str(entry.get("HEAD", ""))[:9], None, (), PR_UNKNOWN, 0, "", "", 0.0, None, True, is_main)
    status = _git(["status", "--porcelain"], path)
    dirty = len(status.stdout.splitlines()) if status.returncode == 0 else None
    log = _git(["log", "-1", "--format=%ct%x09%cI%x09%h%x09%s"], path).stdout.strip().split("\t", 3)
    commit_epoch = float(log[0]) if len(log) == 4 and log[0].isdigit() else 0.0
    main_ref = _main_ref(path)
    ahead = _git(["rev-list", "--count", f"{main_ref}..HEAD"], path) if main_ref else None
    unique = int(ahead.stdout.strip()) if ahead is not None and ahead.returncode == 0 and ahead.stdout.strip().isdigit() else None
    return WorktreeInfo(
        path=path, branch=branch, head=log[2] if len(log) == 4 else "", dirty=dirty,
        operations=tuple(git_operation_in_progress(path)), pr=pr_reader(branch, path), size_bytes=size_reader(path),
        last_commit=log[1] if len(log) == 4 else "", last_subject=log[3] if len(log) == 4 else "",
        last_activity=_activity(path, commit_epoch), unique_commits=unique, prunable=False, is_main=is_main,
    )


def seat_infos(roster: Roster, state_root: Path) -> list[SeatInfo]:
    """Instance state per seat; a missing role-state directory reads as unknown, never as none."""
    have_state = state_root.is_dir()
    seats = []
    for role in roster.roles:
        instance, session = INSTANCE_UNKNOWN, None
        if have_state:
            try:
                recorded = st.read_instance(state_root, role.role)
            except st.StateError:
                recorded = None
                instance = INSTANCE_UNKNOWN
            else:
                instance = INSTANCE_NONE if recorded is None else st.liveness(recorded)
                session = recorded.holder.session_id if recorded else None
        seats.append(SeatInfo(role.role, role.worktree, role.seat_status, instance, session))
    return seats


def _worktree_for(role: Role, infos: list[WorktreeInfo], main: Path, state_root: Path) -> WorktreeInfo | None:
    """The physical worktree of a manifest worktree: the default path, else where the seat's instance last ran."""
    default = default_worktree_path(role, main).resolve()
    by_path = {i.path.resolve(): i for i in infos}
    if default in by_path:
        return by_path[default]
    if state_root.is_dir():
        try:
            recorded = st.read_instance(state_root, role.role)
        except st.StateError:
            return None
        if recorded and recorded.holder.worktree:
            return by_path.get(Path(recorded.holder.worktree).resolve())
    return None


def flags(roster: Roster, seats: list[SeatInfo], infos: list[WorktreeInfo], main: Path, state_root: Path) -> list[str]:
    """Worktree writers that are not the manifest's writer, and one session holding two seats."""
    out: list[str] = []
    writers = {w.name: w.writer for w in roster.worktrees}
    if state_root.is_dir():
        for role in roster.roles:
            info = _worktree_for(role, infos, main, state_root)
            if info is None:
                continue
            try:
                lease = st.read_lease(state_root, info.path)
            except st.StateError:
                continue
            expected = writers.get(role.worktree)
            if lease is not None and expected and lease.role != expected:
                out.append(f"worktree {info.path}: recorded writer {lease.role} is not the manifest writer {expected}")
    by_session: dict[str, list[str]] = {}
    for s in seats:
        if s.session_id and s.instance == st.LIVE:
            by_session.setdefault(s.session_id, []).append(s.role)
    out += [f"session {sid} holds {len(roles)} seats: {', '.join(roles)}" for sid, roles in by_session.items() if len(roles) > 1]
    return out


def disk_warning(infos: list[WorktreeInfo], main: Path, volume: VolumeReader = disk_usage_of) -> list[str]:
    used, total = volume(main)
    if total <= 0 or used / total < DISK_WARN_FRACTION:
        return []
    lines = [f"WARNING: disk {used / total:.0%} full (threshold {DISK_WARN_FRACTION:.0%}); largest worktrees:"]
    lines += [f"  {_size(i.size_bytes):>9}  {i.path}" for i in sorted(infos, key=lambda i: -i.size_bytes)[:5]]
    return lines


def removable(infos: list[WorktreeInfo], roster: Roster, seats: list[SeatInfo], main: Path, state_root: Path,
              now: float, current: Path | None = None) -> list[WorktreeInfo]:
    """Worktrees to *report* as removable: no open PR, nothing unique, clean, no live seat, and idle or unstaffed."""
    out = []
    by_role = {s.role: s for s in seats}
    for info in infos:
        if info.is_main or info.prunable or (current and info.path.resolve() == current.resolve()):
            continue
        if info.pr != PR_NONE or info.unique_commits != 0 or info.dirty != 0 or info.operations:
            continue
        owners = [(r, by_role[r.role]) for r in roster.roles if _worktree_for(r, infos, main, state_root) is info]
        if any(s.instance == st.LIVE for _, s in owners):
            continue
        idle_days = (now - info.last_activity) / 86400 if info.last_activity else None
        retired = not owners or all(r.seat_status == "unstaffed" for r, _ in owners)
        if retired or (idle_days is not None and idle_days >= RETIRE_IDLE_DAYS):
            out.append(info)
    return out


def _size(n: int) -> str:
    return f"{n / 1024**3:.1f} GB" if n >= 1024**3 else f"{n / 1024**2:.0f} MB"


def render(infos: list[WorktreeInfo], seats: list[SeatInfo], warn: list[str], notes: list[str],
           removal: list[WorktreeInfo], now: float) -> str:
    lines = list(warn)
    for i in infos:
        lines.append(f"worktree {i.path}" + ("  (main checkout)" if i.is_main else ""))
        if i.prunable:
            lines.append(f"  missing or prunable; branch {i.branch or '?'}")
            continue
        dirty = "unknown" if i.dirty is None else ("clean" if i.dirty == 0 else f"dirty ({i.dirty} paths)")
        lines.append(f"  branch {i.branch or '(detached)'} @ {i.head}; {dirty}; {_size(i.size_bytes)}; pr: {i.pr}")
        if i.operations:
            lines.append(f"  git operation in progress: {', '.join(i.operations)}")
        idle = f"{(now - i.last_activity) / 86400:.1f}d ago" if i.last_activity else "unknown"
        unique = "unknown" if i.unique_commits is None else str(i.unique_commits)
        lines.append(f"  last commit {i.last_commit or 'unknown'} {i.last_subject}; last activity {idle}; commits not in main: {unique}")
    lines.append("seats:")
    lines += [f"  {s.role}: worktree {s.worktree}, {s.seat_status}, instance {s.instance}" for s in seats]
    lines += [f"flag: {n}" for n in notes]
    if removal:
        lines.append(f"removable (report only; run yourself if you agree; idle threshold {RETIRE_IDLE_DAYS}d):")
        lines += [f"  git worktree remove {i.path}" for i in removal]
    return "\n".join(lines)


def collect(root: Path, volume: VolumeReader = disk_usage_of, pr_reader: Callable[[str | None, Path], str] = open_pr,
            size_reader: SizeReader = tree_size, now: float | None = None) -> str:
    roster = load_roster(root)
    main = main_checkout(root)
    now = time.time() if now is None else now
    try:
        state_root = st.state_root(root)
    except st.StateError:
        state_root = root / ".git" / "session-roles-unavailable"
    infos = [inspect_worktree(e, main, pr_reader, size_reader) for e in worktree_entries(root) if e.get("worktree")]
    seats = seat_infos(roster, state_root)
    return render(
        infos, seats, disk_warning(infos, main, volume), flags(roster, seats, infos, main, state_root),
        removable(infos, roster, seats, main, state_root, now, current=root), now,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="What is in flight, per worktree and seat (read-only).")
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        print(collect(args.root))
    except RosterError as exc:
        print(f"status: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
