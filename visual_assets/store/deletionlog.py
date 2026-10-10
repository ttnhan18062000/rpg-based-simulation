"""The local, gitignored, append-only deletion log of `gc --delete` (ADR D24).

`catalog/.deletions.jsonl`: one canonical `DeletionRecord` per line, each carrying `prev_hash` = the file hash of the previous line's bytes (the first record of the
first log carries `ZERO_HASH`). `gc --delete` appends a record BEFORE it removes the item, so no deletion is ever unrecorded; a kill between the two leaves a record whose
item still exists (`audit_chain` notes it). A full log (`MAX_DELETION_LOG_BYTES`) refuses further deletions until `archive` moves it to `.deletions-NNNN.jsonl`; the next log's
first record is anchored on the archive's last line hash, so the whole history stays one chain (a wrong anchor is a BREAK). Writers hold the store lock; `audit_chain` verifies.
Nothing here ever deletes a log or archive, and `gc` cannot list them (they sit outside its three roots).
"""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from visual_assets.store import config
from visual_assets.store.contracts.base import canonical_json, parse_record
from visual_assets.store.contracts.deletion import ZERO_HASH, DeletionRecord
from visual_assets.store.errors import ContractError, GateError
from visual_assets.store.intake.validator import file_hash

LOG_NAME = ".deletions.jsonl"
ARCHIVE = re.compile(r"\.deletions-(\d{4})\.jsonl")


def log_path(root: Path | None = None) -> Path:
    return (config.CATALOG_ROOT if root is None else root) / LOG_NAME


def archives(root: Path | None = None) -> list[Path]:
    base = config.CATALOG_ROOT if root is None else root
    found = sorted(p for p in base.iterdir() if ARCHIVE.fullmatch(p.name)) if base.is_dir() else []
    return found


def content_hash(path: Path) -> str:
    """Hash of a file's bytes, or of a directory's sorted listing (relative path, kind, file hash or link target); symlinks are never followed."""
    if path.is_symlink():
        return file_hash(b"link\0" + os.readlink(path).encode())
    if path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return "sha256:" + digest.hexdigest()
    lines: list[bytes] = []
    for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
        dirnames.sort()
        base = Path(dirpath)
        for name in sorted(filenames) + [d for d in dirnames if (base / d).is_symlink()]:
            entry = base / name
            rel = str(entry.relative_to(path)).encode()
            lines.append(rel + b"\0" + content_hash(entry).encode() + b"\n")
        lines.append(str(base.relative_to(path)).encode() + b"\0dir\n")
    return file_hash(b"".join(lines))


def _read_lines(path: Path) -> list[bytes]:
    _open_ok(path)
    data = path.read_bytes()
    return [line + b"\n" for line in data.split(b"\n") if line]


def _open_ok(path: Path) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise GateError("deletion_log", "the deletion log is a symlink or not a regular file; refusing to use it")
    if path.is_file() and path.stat().st_size > config.MAX_DELETION_LOG_BYTES:
        raise GateError("deletion_log", f"the deletion log is larger than {config.MAX_DELETION_LOG_BYTES} bytes; refusing to read it")


def last_hash(root: Path | None = None) -> str:
    """The chain head: the hash of the newest line of the current log, else of the newest archive, else the zero anchor."""
    for candidate in (log_path(root), *reversed(archives(root))):
        if candidate.is_file() and not candidate.is_symlink():
            lines = _read_lines(candidate)
            if lines:
                return file_hash(lines[-1])
    return ZERO_HASH


def build_record(*, kind: str, relative: str, content: str, reason: str, decided_at: str, prev_hash: str) -> tuple[DeletionRecord, bytes]:
    record = DeletionRecord(record_type="deletion_record", schema_version=1, kind=kind, path=f"{kind}/{relative}", content_hash=content,
                            reason=reason, decided_at=decided_at, prev_hash=prev_hash)
    return record, canonical_json(record)


def current_size() -> int:
    path = log_path()
    _open_ok(path)
    return path.stat().st_size if path.is_file() else 0


def require_room(extra: int) -> None:
    if current_size() + extra > config.MAX_DELETION_LOG_BYTES:
        raise GateError("deletion_log_full", f"the deletion log would pass {config.MAX_DELETION_LOG_BYTES} bytes; nothing was deleted. "
                        "Run `python -m visual_assets.store deletions --archive` to move it aside, then `gc --delete` again")


def require_clean_tail() -> None:
    """Refuse (before anything is removed) when the log ends in a torn line, so no record is ever appended onto one."""
    path = log_path()
    _open_ok(path)
    if path.is_file() and path.stat().st_size and path.read_bytes()[-1:] != b"\n":
        raise GateError("deletion_log", "the deletion log ends in a torn line (an interrupted append); run `audit`, repair the log by hand, nothing was deleted")


def append(line: bytes) -> None:
    """Append one canonical record line (with O_APPEND, fsynced). The caller holds the store lock and has checked `require_room`."""
    path = log_path()
    _open_ok(path)
    if path.is_file() and path.stat().st_size and path.read_bytes()[-1:] != b"\n":
        raise GateError("deletion_log", "the deletion log ends in a torn line (an interrupted append); run `audit`, repair the log by hand, nothing was deleted")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        view = memoryview(line)
        while view:
            view = view[os.write(fd, view):]  # a short write continues; it never leaves half a line unnoticed
        os.fsync(fd)
    finally:
        os.close(fd)


def archive() -> Path:
    """Move the current log to the next `.deletions-NNNN.jsonl` (never overwriting). Refuses an empty or missing log. The chain continues from the archive's last hash."""
    path = log_path()
    _open_ok(path)
    if not path.is_file() or not _read_lines(path):
        raise GateError("deletion_log_empty", "there is no deletion log to archive")
    taken = [int(ARCHIVE.fullmatch(p.name).group(1)) for p in archives()]  # type: ignore[union-attr]
    target = path.parent / f".deletions-{(max(taken) + 1) if taken else 1:04d}.jsonl"
    if target.exists() or target.is_symlink():
        raise GateError("deletion_log", "the next archive name is taken")
    os.rename(path, target)
    return target


@dataclass(frozen=True)
class Entry:
    source: str  # file name inside the catalog root
    number: int  # 1-based line number
    record: DeletionRecord
    line: bytes


def entries(root: Path | None = None) -> Iterator[Entry]:
    """Every parsed record, archives first then the current log. Raises `ContractError` on the first bad line (audit does its own tolerant walk)."""
    for path in (*archives(root), log_path(root)):
        if path.is_file() and not path.is_symlink():
            for number, line in enumerate(_read_lines(path), 1):
                yield Entry(path.name, number, parse_record(DeletionRecord, line), line)


def listing() -> list[str]:
    return [f"{e.record.decided_at}  {e.record.kind}  {e.record.path}  {e.record.content_hash}  ({e.record.reason})  [{e.source}:{e.number}]" for e in entries()]


__all__ = ["LOG_NAME", "ContractError"]
