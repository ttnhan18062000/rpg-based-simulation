"""Find the processes that belong to one test's sandbox jobs, without looking at the rest of the machine.

A sandbox started by another session, worktree or test can neither fail nor hide a leak here: a process counts only when its command
line or its mount table names `marker` (a path unique to the test, such as its workspace). The inner bwrap and the Aseprite it runs
share the job directory's bind mount, so the mount table finds them even when the command line does not.
"""

from __future__ import annotations

import time
from pathlib import Path


def holders(marker: str) -> list[int]:
    found = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            text = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace") + (entry / "mountinfo").read_text(errors="replace")
        except OSError:
            continue  # exited meanwhile, or not ours to read
        if marker in text:
            found.append(int(entry.name))
    return found


def wait_gone(marker: str, seconds: float = 10.0) -> list[int]:
    """Bounded poll for the holders of `marker` to be reaped; returns whatever is still there at the deadline."""
    deadline = time.monotonic() + seconds
    while holders(marker) and time.monotonic() < deadline:
        time.sleep(0.05)
    return holders(marker)


def describe(pid: int) -> str:
    """One line for a failure message: pid, NSpid, state, parent and the command line tail, read from /proc (the process may be gone)."""
    try:
        status = dict(line.split(":", 1) for line in (Path("/proc") / str(pid) / "status").read_text().splitlines() if ":" in line)
        cmd = (Path("/proc") / str(pid) / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
    except OSError:
        return f"pid {pid}: gone"
    return f"pid {pid} NSpid={status.get('NSpid', '?').strip()} State={status.get('State', '?').strip()} PPid={status.get('PPid', '?').strip()} cmd=...{cmd[-110:]}"
