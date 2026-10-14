#!/usr/bin/env python3
"""Mid-session low-disk line for the PostToolUse hook (TCK-20261014-DISK-HEADROOM-MIDSESSION-WARNING-AND-MERGED-WORKTREES).

The SessionStart warning (`disk_headroom.low_space_line`) fires once; a session that runs all day never sees it again,
and on 2026-10-14 the disk reached 0 bytes free. `mid_session_line()` is called on every tool call, so it is built to
cost almost nothing:

- one small state file per session (`.claude/.disk_warn.<session_id>`, gitignored) holds the time of the last check;
- inside the check window (10 minutes) it reads that file and returns, with no `statvfs`;
- outside it, one `statvfs`; below the threshold (`SESSION_DISK_THRESHOLD_GB`, default 10) it returns a line, at most
  once per 30 minutes, and at once when free space first drops below 2 GB;
- it never raises: any error returns None.

Report only. It names the two commands that look and never deletes anything.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

CHECK_WINDOW_SECONDS = 600
REPEAT_WINDOW_SECONDS = 1800
CRITICAL_GB = 2.0
STATE_PREFIX = ".disk_warn."
STALE_SECONDS = 24 * 3600  # no session-end hook exists, so any later call sweeps files this old


def _state_path(state_dir: Path, session_id: str) -> Path:
    return state_dir / (STATE_PREFIX + (re.sub(r"[^A-Za-z0-9_-]", "", session_id or "")[:64] or "nosession"))


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _sweep(state_dir: Path, now: float) -> None:
    for old in state_dir.glob(STATE_PREFIX + "*"):
        try:
            if now - old.stat().st_mtime > STALE_SECONDS:
                old.unlink()
        except OSError:
            pass


def _line(free: int, limit: int) -> str:
    gb = 1024**3
    return (f"disk-headroom: only {free / gb:.1f} GB free on the repo filesystem (warning below {limit / gb:.1f} GB). "
            "Look: `python3 tools/sessions/disk_headroom.py` (run data per worktree, merged worktrees that could go). "
            "Removing worktrees needs the user: `python3 -m tools.sessions.prune_branches --worktrees`. "
            "Clean your own run data by run id: `done_checker_static.py --clean-data-runs --path <run_id>`.")


def mid_session_line(session_id: str, state_dir: Path = Path(".claude"), now: float | None = None,
                     free_fn=None, environ=os.environ) -> str | None:
    """The warning line for this tool call, or None. Never raises."""
    try:
        now = time.time() if now is None else now
        path = _state_path(Path(state_dir), session_id)
        state = _read(path)
        checked = state.get("checked")
        if isinstance(checked, (int, float)) and 0 <= now - checked < CHECK_WINDOW_SECONDS:
            return None
        from tools.sessions import disk_headroom as dh

        free = (free_fn or dh.free_bytes)()
        limit = dh.threshold_bytes(environ=environ)
        critical = free < CRITICAL_GB * dh.GB
        warned = state.get("warned")
        due = free < limit and (
            not isinstance(warned, (int, float)) or now - warned >= REPEAT_WINDOW_SECONDS
            or (critical and not state.get("critical")))
        new = {"checked": now, "warned": now if due else warned, "critical": bool(state.get("critical")) or (due and critical)}
        if free >= limit:
            new["critical"] = False
        try:
            Path(state_dir).mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(new))
            _sweep(Path(state_dir), now)
        except OSError:
            pass
        return _line(free, limit) if due else None
    except Exception:  # noqa: BLE001 - never fail or slow a tool call
        return None
