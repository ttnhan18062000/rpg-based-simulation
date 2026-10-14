#!/usr/bin/env python3
"""Read-only disk headroom report for the repo's filesystem (TCK-20261008-SESSION-DISK-HEADROOM-GUARD).

On 2026-10-08 the disk reached 100% in the middle of a working day and no session saw it coming. This
reports free space, the `data/runs` + `reports/release_proof` size per worktree, and the total worktree
size, so a session can look before a measurement batch. It never deletes, moves or refuses anything.

Two costs, kept apart on purpose: `free_bytes()` is one `statvfs` and is what the launcher and the
SessionStart hook call on every start; `measure()` walks every worktree (tens of seconds on a full disk
with ~50 of them) and runs only when free space is already below the threshold, or when asked for by hand.
Sizes are allocated blocks (`st_blocks * 512`, what `du` reports), without following symlinks.

    python3 tools/sessions/disk_headroom.py [--json] [--threshold-gb N]

By hand (not in the launcher, which must not wait on `gh`) the report also lists the worktrees `prune_branches
--worktrees` classifies as removable, plus detached clean ones to check (TCK-20261014-DISK-HEADROOM-MIDSESSION-
WARNING-AND-MERGED-WORKTREES). Report only: removing them still needs the user. The mid-session low-disk line
lives in `disk_warning.py`.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_THRESHOLD_GB = 10.0
THRESHOLD_ENV = "SESSION_DISK_THRESHOLD_GB"
RUN_DATA_DIRS = ("data/runs", "reports/release_proof")
GB = 1024**3
TOP_HOLDERS = 3


@dataclass(frozen=True)
class WorktreeUsage:
    path: str
    branch: str
    run_data_bytes: int
    total_bytes: int


@dataclass(frozen=True)
class Headroom:
    free_bytes: int
    total_bytes: int
    worktrees: tuple[WorktreeUsage, ...]

    @property
    def total_worktree_bytes(self) -> int:
        return sum(w.total_bytes for w in self.worktrees)

    @property
    def total_run_data_bytes(self) -> int:
        return sum(w.run_data_bytes for w in self.worktrees)


def threshold_bytes(override_gb: float | None = None, environ=os.environ) -> int:
    """The warning threshold: an explicit value, else `SESSION_DISK_THRESHOLD_GB`, else the default."""
    if override_gb is None:
        try:
            override_gb = float(environ.get(THRESHOLD_ENV, ""))
        except ValueError:
            override_gb = DEFAULT_THRESHOLD_GB
    return int(override_gb * GB)


def free_bytes(root: Path | str = _REPO_ROOT) -> int:
    """Free bytes on the filesystem holding `root`: one syscall, safe to call on every start."""
    return shutil.disk_usage(str(root)).free


def dir_bytes(path: Path) -> int:
    """Allocated bytes under `path` (symlinks not followed); 0 for a missing path."""
    total = 0
    stack = [str(path)]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    total += st.st_blocks * 512
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
        except OSError:
            continue
    return total


def _own_size(path: Path) -> int:
    try:
        return os.lstat(path).st_blocks * 512
    except OSError:
        return 0


def worktree_entries(root: Path) -> list[tuple[str, str]]:
    """(path, branch) of every worktree, main checkout first; [] when git cannot say."""
    out = subprocess.run(["git", "--no-optional-locks", "worktree", "list", "--porcelain"], cwd=str(root),
                         capture_output=True, text=True, check=False)
    if out.returncode != 0:
        return []
    entries, path, branch = [], None, ""
    for line in out.stdout.splitlines() + [""]:
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch "):
            branch = line[len("branch "):].removeprefix("refs/heads/")
        elif not line and path is not None:
            entries.append((path, branch or "(detached)"))
            path, branch = None, ""
    return entries


def measure(root: Path | str = _REPO_ROOT) -> Headroom:
    """The full report. Walks every worktree: call only when free space is low or asked for by hand."""
    root = Path(root)
    usage = shutil.disk_usage(str(root))
    rows = []
    for path, branch in worktree_entries(root):
        wt = Path(path)
        run_data = sum(dir_bytes(wt / d) + (_own_size(wt / d) if (wt / d).is_dir() else 0) for d in RUN_DATA_DIRS)
        rows.append(WorktreeUsage(path, branch, run_data, dir_bytes(wt) + _own_size(wt)))
    rows.sort(key=lambda w: (-w.run_data_bytes, w.path))
    return Headroom(usage.free, usage.total, tuple(rows))


@dataclass(frozen=True)
class RemovableWorktrees:
    """What `prune_branches --worktrees` would remove (merged, clean, no seat, no process inside), and detached clean ones."""

    gh_ok: bool
    removable: tuple[tuple[str, str, int], ...] = ()  # (path, branch, bytes)
    detached: tuple[tuple[str, int], ...] = ()  # (path, bytes): detached HEAD, no uncommitted changes
    error: str = ""

    @property
    def removable_bytes(self) -> int:
        return sum(r[2] for r in self.removable)


PRUNE_COMMAND = "python3 -m tools.sessions.prune_branches --worktrees --execute --backup <path>"


def removable_worktrees(root: Path | str = _REPO_ROOT, classify=None, dirty=None, size=None) -> RemovableWorktrees:
    """The classification is `prune_branches.classify_worktrees`, never a second copy. `classify`, `dirty` and `size`
    are seams for tests; any failure is reported as `error` and lists nothing as removable."""
    root = Path(root)
    try:
        if str(_REPO_ROOT) not in sys.path:  # run as a script, sys.path[0] is tools/sessions
            sys.path.append(str(_REPO_ROOT))
        from tools.sessions import prune_branches as pb

        if classify is None:
            from tools.sessions import state as st
            from tools.sessions.roster import load_roster

            def classify():
                return pb.classify_worktrees(root, pb.fetch_prs(root), load_roster(root), st.state_root(root))
        dirty = dirty or pb._dirty_paths
        size = size or pb._tree_bytes
        report = classify()
        if not report.gh_ok:
            return RemovableWorktrees(False)
        removable = tuple((r.path, r.branch, r.size_bytes) for r in report.removable())
        detached = tuple((r.path, size(Path(r.path))) for r in report.rows
                         if r.reason == pb.DETACHED_REASON and Path(r.path).is_dir() and not dirty(Path(r.path)))
        return RemovableWorktrees(True, removable, detached)
    except Exception as exc:  # noqa: BLE001 - a report never fails the caller
        return RemovableWorktrees(False, error=f"{type(exc).__name__}: {exc}")


def render_removable(r: RemovableWorktrees) -> str:
    lines = ["Removable worktrees (report only; nothing is removed):"]
    if r.error:
        lines.append(f"  unavailable ({r.error}); nothing listed as removable")
        return "\n".join(lines)
    if not r.gh_ok:
        lines.append("  gh unavailable: nothing could be proven merged, so none is listed as removable")
        return "\n".join(lines)
    lines.append(f"  merged, clean, no seat, no process inside: {len(r.removable)} ({_gb(r.removable_bytes)})")
    lines += [f"    {_gb(b):>9}  {p} [{br}]" for p, br, b in sorted(r.removable, key=lambda x: -x[2])]
    if r.detached:
        lines.append(f"  detached, check (no uncommitted changes, merged state unknown): {len(r.detached)}")
        lines += [f"    {_gb(b):>9}  {p}" for p, b in sorted(r.detached, key=lambda x: -x[1])]
    if r.removable:
        lines.append(f"  remove with the user's yes (delete_worktree_or_data): {PRUNE_COMMAND}")
    return "\n".join(lines)


def _gb(n: int) -> str:
    return f"{n / GB:.1f} GB"


def low_space_line(free: int, limit: int) -> str | None:
    """The cheap one-liner (launcher and SessionStart hook); None at or above the threshold."""
    if free >= limit:
        return None
    return (f"disk-headroom: only {_gb(free)} free on the repo filesystem (warning below {_gb(limit)}). Check "
            f"before a measurement batch with `python3 tools/sessions/disk_headroom.py`; clean your own run "
            f"data by run id with `done_checker_static.py --clean-data-runs --path <run_id>`.")


def warning_line(h: Headroom, limit: int) -> str | None:
    """`low_space_line` plus the largest run-data holders, from a full measurement."""
    base = low_space_line(h.free_bytes, limit)
    if base is None:
        return None
    holders = [w for w in h.worktrees if w.run_data_bytes > 0][:TOP_HOLDERS]
    if not holders:
        return base
    named = ", ".join(f"{Path(w.path).name} {_gb(w.run_data_bytes)}" for w in holders)
    return f"{base} Largest run-data holders: {named}."


def render_text(h: Headroom) -> str:
    lines = [f"free: {_gb(h.free_bytes)} of {_gb(h.total_bytes)}",
             f"worktrees: {len(h.worktrees)}, total {_gb(h.total_worktree_bytes)}, run data {_gb(h.total_run_data_bytes)}",
             "run data per worktree (largest first):"]
    lines += [f"  {_gb(w.run_data_bytes):>9}  of {_gb(w.total_bytes):>9}  {w.path} [{w.branch}]" for w in h.worktrees]
    return "\n".join(lines)


def to_json(h: Headroom, r: RemovableWorktrees | None = None) -> str:
    return json.dumps({
        **({"removable_worktrees": {"gh_ok": r.gh_ok, "error": r.error, "removable_bytes": r.removable_bytes,
                                    "removable": [{"path": p, "branch": b, "bytes": n} for p, b, n in r.removable],
                                    "detached": [{"path": p, "bytes": n} for p, n in r.detached]}} if r else {}),
        "free_bytes": h.free_bytes,
        "total_bytes": h.total_bytes,
        "total_worktree_bytes": h.total_worktree_bytes,
        "total_run_data_bytes": h.total_run_data_bytes,
        "worktrees": [{"path": w.path, "branch": w.branch, "run_data_bytes": w.run_data_bytes,
                       "total_bytes": w.total_bytes} for w in h.worktrees],
    }, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only disk headroom and run-data report.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--threshold-gb", type=float, default=None)
    ap.add_argument("--root", type=Path, default=_REPO_ROOT)
    a = ap.parse_args(argv)
    h = measure(a.root)
    removable = removable_worktrees(a.root)
    print(to_json(h, removable) if a.json else render_text(h) + "\n\n" + render_removable(removable))
    if not a.json:
        line = warning_line(h, threshold_bytes(a.threshold_gb))
        if line:
            print("\n" + line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
