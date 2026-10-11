"""The store write lock (ADR D24): one advisory `flock` per store data root, refused at once, never waited for.

Every command that writes the store, or exports from it, runs inside `store_write_lock`. The lock file is `catalog/.store.lock` under the resolved
`config.CATALOG_ROOT`, so a worktree (or a `VISUAL_ASSETS_CHECKOUT` data root) has its own lock. A second writer gets a `GateError("store_locked")` naming the last
holder's pid and command (agents must not hang). The kernel releases the lock when the holder exits or is killed, so a stale file is harmless: the holder text is the
last writer's claim, not the truth. The file is never deleted (no unlink race) and `gc` never lists it. Linux only: the platform check happens at acquire time so read-only
commands still import anywhere. Library code takes `started_at` as a parameter (only entry points read the clock).
"""

from __future__ import annotations

import errno
import json
import os
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager

from visual_assets.store import config
from visual_assets.store.errors import GateError
from visual_assets.store.identities import UtcTimestamp, check

LOCK_NAME = ".store.lock"
_HOLDER_READ = 512
_COMMAND = re.compile(r"[a-z][a-z0-9 -]{0,63}")


def lock_path():
    return config.CATALOG_ROOT / LOCK_NAME


def _holder_text(raw: bytes) -> str:
    """A path-free, control-character-free description of the last holder, from untrusted file content."""
    try:
        data = json.loads(raw.decode("utf-8"))
        pid, command = data["pid"], data["command"]
        if type(pid) is int and 0 < pid < 2**31 and isinstance(command, str) and _COMMAND.fullmatch(command):
            return f"the last holder was pid {pid} running `{command}`"
    except (ValueError, KeyError, TypeError, UnicodeError):
        pass
    return "the last holder is unknown"


@contextmanager
def store_write_lock(command: str, *, started_at: str) -> Iterator[None]:
    """Hold the store lock for the `with` body, or raise `GateError` at once. `command` is a short lowercase name (`gc`, `draft keep`)."""
    if not sys.platform.startswith("linux"):
        raise GateError("lock_unsupported", "the store lock needs Linux flock; run store commands that write on Linux")
    import fcntl  # not at import time: read-only commands must import anywhere

    check(UtcTimestamp, started_at)
    if not _COMMAND.fullmatch(command):
        raise GateError("lock_command", "a lock holder command is a short lowercase name")
    path = lock_path()
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise GateError("store_missing", "the store catalog directory does not exist")
    try:
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise GateError("lock_file", "the lock file is a symlink; refusing to use it") from None
        raise GateError("lock_file", f"the lock file cannot be opened ({exc.strerror})") from None
    try:
        import stat

        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise GateError("lock_file", "the lock file is not a regular file")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            holder = _holder_text(os.pread(fd, _HOLDER_READ, 0))
            raise GateError("store_locked", f"another store command is writing this store ({holder}); wait for it to finish, nothing was changed") from None
        record = json.dumps({"command": command, "pid": os.getpid(), "started_at": started_at}, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        os.ftruncate(fd, 0)
        os.pwrite(fd, record, 0)
        yield
    finally:
        os.close(fd)  # closing the descriptor releases the flock; the file stays
