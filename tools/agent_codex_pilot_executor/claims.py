"""Claim transitions guarded by a per-ticket Linux advisory lock.

The lock is only mutual exclusion for read/replace transitions.  It does not
confer ownership and is never reclaimed by age: closing a holder's descriptor
on process exit is the only crash recovery.  An active marker is deliberately
never auto-reclaimed.
"""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .errors import ClaimRefusedError
from .models import ClaimMarker
from .paths import resolve_scratch_paths

_TERMINAL_STATES = frozenset({"completed", "failed"})
_ALL_STATES = _TERMINAL_STATES | {"active"}


@contextmanager
def _transition_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _read_marker(path: Path) -> ClaimMarker | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        marker = ClaimMarker(
            ticket_id=raw["ticket_id"], execution_id=raw["execution_id"], state=raw["state"]
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ClaimRefusedError(f"malformed claim marker: {path}") from exc
    if marker.state not in _ALL_STATES:
        raise ClaimRefusedError(f"unrecognized claim state: {marker.state!r}")
    return marker


def _replace_marker(path: Path, marker: ClaimMarker) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temporary:
            json.dump(marker.__dict__, temporary, separators=(",", ":"))
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def acquire_claim(scratch_root: Path, ticket_id: str, execution_id: str) -> ClaimMarker:
    paths = resolve_scratch_paths(
        scratch_root=scratch_root, ticket_id=ticket_id, execution_id=execution_id
    )
    with _transition_lock(paths.lock_path):
        existing = _read_marker(paths.claim_path)
        if existing is not None and existing.state == "active":
            raise ClaimRefusedError(f"unfinished claim exists for {ticket_id}")
        marker = ClaimMarker(ticket_id=ticket_id, execution_id=execution_id, state="active")
        _replace_marker(paths.claim_path, marker)
        return marker


def terminalize_claim(
    scratch_root: Path, ticket_id: str, execution_id: str, state: str
) -> ClaimMarker:
    if state not in _TERMINAL_STATES:
        raise ValueError(f"terminal state must be one of {sorted(_TERMINAL_STATES)}")
    paths = resolve_scratch_paths(
        scratch_root=scratch_root, ticket_id=ticket_id, execution_id=execution_id
    )
    with _transition_lock(paths.lock_path):
        existing = _read_marker(paths.claim_path)
        if existing is None or existing.state != "active":
            raise ClaimRefusedError("no active claim to terminalize")
        if existing.ticket_id != ticket_id or existing.execution_id != execution_id:
            raise ClaimRefusedError("claim ownership does not match terminalization request")
        marker = ClaimMarker(ticket_id=ticket_id, execution_id=execution_id, state=state)
        _replace_marker(paths.claim_path, marker)
        return marker
