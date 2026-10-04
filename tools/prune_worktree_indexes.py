"""Reclaim disk from derived indexes that idle git worktrees keep.

TCK-20261004-WORKTREE-INDEX-DUPLICATION: every worktree builds its own ``agent-working/.index/`` (the
knowledge index is ~100M, the monitoring index ~140M). Both are untracked and regenerable
(``make knowledge-index``, ``make agent-monitoring-index``), so the cheapest safe fix is to delete them in
worktrees nobody has touched for a while, not to share one index across branches with different docs.

Dry run by default. ``--apply`` deletes. Never touches the current worktree or the main checkout, and only the
two large index folders (the parity index is a few MB and stays).

    python3 tools/prune_worktree_indexes.py                # report
    python3 tools/prune_worktree_indexes.py --days 3 --apply
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.agent_working_paths import AGENT_MONITORING_INDEX, KNOWLEDGE_INDEX  # noqa: E402

PRUNABLE = (KNOWLEDGE_INDEX, AGENT_MONITORING_INDEX)
DEFAULT_IDLE_DAYS = 7


@dataclass(frozen=True)
class Candidate:
    worktree: Path
    index_dir: Path
    size_bytes: int
    idle_days: float


def list_worktrees(cwd: Path) -> list[Path]:
    """Worktree paths, main checkout first (``git worktree list --porcelain`` order)."""
    out = subprocess.run(
        ["git", "worktree", "list", "--porcelain"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout
    return [Path(line.split(" ", 1)[1]) for line in out.splitlines() if line.startswith("worktree ")]


def _tree_stats(path: Path) -> tuple[int, float]:
    """(total bytes, newest mtime) over every file under ``path``."""
    total, newest = 0, path.stat().st_mtime
    for f in path.rglob("*"):
        if f.is_file():
            st = f.stat()
            total += st.st_size
            newest = max(newest, st.st_mtime)
    return total, newest


def find_candidates(worktrees: list[Path], current: Path, idle_days: float, now: float | None = None) -> list[Candidate]:
    """Index folders in idle worktrees. The main checkout (first entry) and ``current`` are skipped."""
    now = time.time() if now is None else now
    current = current.resolve()
    found: list[Candidate] = []
    for wt in worktrees[1:]:
        if wt.resolve() == current:
            continue
        for rel in PRUNABLE:
            d = wt / rel
            if not d.is_dir():
                continue
            size, newest = _tree_stats(d)
            idle = (now - newest) / 86400
            if idle >= idle_days:
                found.append(Candidate(wt, d, size, idle))
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--days", type=float, default=DEFAULT_IDLE_DAYS, help="idle threshold (default %(default)s)")
    ap.add_argument("--apply", action="store_true", help="delete (default: report only)")
    args = ap.parse_args(argv)

    current = Path.cwd()
    cands = find_candidates(list_worktrees(current), current, args.days)
    total = sum(c.size_bytes for c in cands)
    for c in cands:
        print(f"{c.size_bytes / 1e6:7.1f}M idle {c.idle_days:5.1f}d  {c.index_dir}")
        if args.apply:
            shutil.rmtree(c.index_dir)
    verb = "removed" if args.apply else "would remove"
    print(f"{verb} {total / 1e6:.1f}M in {len(cands)} folder(s); rebuild with make knowledge-index / agent-monitoring-index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
