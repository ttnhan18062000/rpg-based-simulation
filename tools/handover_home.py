"""Where handover notes live: the main checkout, not the tree a tool or session happens to run in.

`.claude/handover/` is gitignored, so notes and drafts exist only in the main checkout, while seats run in
worktrees under it. TCK-20261006-HANDOVER-NOTES-RESOLVE-FROM-MAIN-CHECKOUT. Stdlib only so every caller
(launcher, SessionStart hooks, transit) can import it without a package cycle.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

HANDOVER_REL = Path(".claude/handover")


def main_checkout_root(cwd: Path | str = ".") -> Path | None:
    """The main checkout (git common dir's parent), the same from every worktree; None when git cannot say."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=str(cwd), capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip()
    except Exception:
        return None
    return Path(out).parent if out else None


def handover_base(cwd: Path | str = ".") -> Path:
    """Directory that `.claude/handover/...` is relative to; `cwd` itself when git is unavailable."""
    return main_checkout_root(cwd) or Path(cwd)


def handover_dir(cwd: Path | str = ".") -> Path:
    """`<main checkout>/.claude/handover`; the cwd-relative path when git is unavailable."""
    root = main_checkout_root(cwd)
    return root / HANDOVER_REL if root else HANDOVER_REL
