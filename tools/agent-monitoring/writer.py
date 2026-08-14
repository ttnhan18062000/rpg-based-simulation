#!/usr/bin/env python3
"""Shared Linux-only append-only writer for agent-monitoring/*.jsonl.

Single production implementation of the O_CREAT|O_EXCL lock-file protocol
(bounded retry, stale-lock recovery) that post_tool_hook.py, record_run.py,
and record_events.py all route their append step through, replacing 3
previously separate ad hoc implementations (fcntl.flock, unlocked single
write, unlocked batch write).

`write_line`/`write_lines` never raise to their caller: any lock-acquire or
write failure is caught internally, recorded to the out-of-band diagnostic
sidecar (`.writer_health.jsonl`, written via a lock-free best-effort
O_APPEND — never through this module's own locked append path, which would
recurse or silently lose the diagnostic), and reported back as a plain
`bool`.

Batch-write tradeoff (record_events.py): `write_lines` holds one lock
acquisition for the whole batch, preserving the "one batch write = one
contiguous block of lines" property. This means a very large batch widens
the window in which a concurrent single-line writer (post_tool_hook.py) can
hit `_acquire_lock`'s TimeoutError ceiling (MAX_RETRIES * RETRY_SLEEP_S ~= 1s)
and fall through to the diagnostic-only path instead of writing. This is an
accepted tradeoff for realistic (small) batch sizes, not a bug — no
artificial batch-size cap is added here.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

STALE_AFTER_S = 5.0
MAX_RETRIES = 200
RETRY_SLEEP_S = 0.005


def _lock_path_for(target_path: Path) -> Path:
    return target_path.with_name(target_path.name + ".lock")


def _diagnostic_path_for(target_path: Path) -> Path:
    return target_path.parent / ".writer_health.jsonl"


def _acquire_lock(
    lock_path: Path,
    stale_after_s: float = STALE_AFTER_S,
    max_retries: int = MAX_RETRIES,
    retry_sleep_s: float = RETRY_SLEEP_S,
) -> None:
    for _ in range(max_retries):
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            try:
                age_s = time.time() - os.path.getmtime(lock_path)
            except FileNotFoundError:
                continue
            if age_s > stale_after_s:
                try:
                    os.remove(lock_path)
                except FileNotFoundError:
                    pass
                continue
            time.sleep(retry_sleep_s)
    raise TimeoutError(f"could not acquire lock at {lock_path} after {max_retries} retries")


def _release_lock(lock_path: Path) -> None:
    try:
        os.remove(lock_path)
    except FileNotFoundError:
        pass


def _write_diagnostic(target_path: Path, stage: str, error: BaseException) -> None:
    """Best-effort, lock-free diagnostic append — must never raise.

    Uses a single os.write() call on an O_APPEND-opened fd (not Python's
    buffered open(..., "a")) so that one diagnostic line is atomic against
    concurrent unlocked writers on Linux local filesystems — the specific
    atomicity commitment this sidecar relies on, not merely best-effort.
    """
    try:
        diagnostic_path = _diagnostic_path_for(target_path)
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        record = {
            "ts": ts,
            "target": target_path.name,
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error)[:500],
        }
        line = json.dumps(record, separators=(",", ":")) + "\n"
        fd = os.open(str(diagnostic_path), os.O_APPEND | os.O_CREAT | os.O_WRONLY)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    except Exception:
        pass


def write_line(target_path: Path, line: str) -> bool:
    """Append one pre-serialized JSON line (no trailing newline) to target_path.

    Never raises. Returns True on success, False on any failure (a
    diagnostic line is written to the sidecar in that case).
    """
    lock_path = _lock_path_for(target_path)
    try:
        _acquire_lock(lock_path)
    except Exception as e:
        _write_diagnostic(target_path, "lock_acquire", e)
        return False
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        _write_diagnostic(target_path, "write", e)
        return False
    finally:
        try:
            _release_lock(lock_path)
        except Exception as e:
            _write_diagnostic(target_path, "lock_release", e)
            # A lock-release failure after a successful write is
            # diagnostic-worthy, not a reason to report the whole
            # operation as failed.
    return True


def write_lines(target_path: Path, lines: list[str]) -> bool:
    """Append a batch of pre-serialized JSON lines under one lock acquisition.

    Preserves "one batch write = contiguous lines in the file" for callers
    like record_events.py. Never raises; returns True/False like write_line.
    """
    lock_path = _lock_path_for(target_path)
    try:
        _acquire_lock(lock_path)
    except Exception as e:
        _write_diagnostic(target_path, "lock_acquire", e)
        return False
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "a") as f:
            for line in lines:
                f.write(line + "\n")
    except Exception as e:
        _write_diagnostic(target_path, "write", e)
        return False
    finally:
        try:
            _release_lock(lock_path)
        except Exception as e:
            _write_diagnostic(target_path, "lock_release", e)
    return True
