"""Safe reading of a candidate package and exclusive writing of its quarantine directory.

The producer controls the package directory, so nothing in it is trusted: the directory is opened without following
a symlink, every entry is examined with `lstat` before it is opened, files are opened with `O_NOFOLLOW` relative to
the directory descriptor (no path is ever rebuilt from package content), and a file must be a regular, single-link
file within its size bound. All three files are read into memory and verified BEFORE the quarantine directory is
created, so a refused package leaves nothing behind. The quarantine directory and its files are created exclusively.
"""

from __future__ import annotations

import os
import secrets
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path

from visual_assets.store import config
from visual_assets.store.errors import StageError

PACKAGE_FILE = "package.json"
SOURCE_FILE = "source.aseprite"
PREVIEW_FILE = "preview.png"
RESULT_FILE = "intake_result.json"
REVOCATION_FILE = "revocation.json"  # local revocation of an un-adopted intake (written by `revoke`)
STAGED_NAMES = (PACKAGE_FILE, SOURCE_FILE, PREVIEW_FILE)

_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
_WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC


@dataclass(frozen=True)
class PackageFiles:
    package: bytes
    source: bytes
    preview: bytes


def _limit(name: str) -> int:
    return {
        PACKAGE_FILE: config.MAX_RECORD_BYTES,
        SOURCE_FILE: config.MAX_SOURCE_BYTES,
        PREVIEW_FILE: config.MAX_PREVIEW_BYTES,
        RESULT_FILE: config.MAX_RECORD_BYTES,
        REVOCATION_FILE: config.MAX_RECORD_BYTES,
    }[name]


def _open_dir(path: Path) -> int:
    try:
        return os.open(os.fspath(path), _DIR_FLAGS)
    except FileNotFoundError:
        raise StageError("not_found", "package directory does not exist") from None
    except OSError as exc:
        # ELOOP from O_NOFOLLOW (a symlink) or ENOTDIR (not a directory)
        kind = "symlink" if os.path.islink(path) else "not_a_directory"
        raise StageError(kind, f"package directory is not a plain directory ({exc.strerror})") from None


def _read_regular(dfd: int, name: str, limit: int | None = None) -> bytes:
    """Read one entry of an open directory, refusing anything but a bounded regular single-link file."""
    limit = _limit(name) if limit is None else limit
    try:
        before = os.stat(name, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        raise StageError("missing_file", f"{name} is missing") from None
    if stat.S_ISLNK(before.st_mode):
        raise StageError("symlink", f"{name} is a symlink")
    if not stat.S_ISREG(before.st_mode):
        raise StageError("not_regular_file", f"{name} is not a regular file")
    try:
        fd = os.open(name, _READ_FLAGS, dir_fd=dfd)
    except OSError as exc:
        raise StageError("unreadable", f"{name} cannot be opened safely ({exc.strerror})") from None
    try:
        after = os.fstat(fd)  # re-check on the descriptor: the entry may have been swapped since lstat
        if not stat.S_ISREG(after.st_mode):
            raise StageError("not_regular_file", f"{name} is not a regular file")
        if after.st_nlink != 1:
            raise StageError("hard_link", f"{name} has {after.st_nlink} hard links")
        if after.st_size > limit:
            raise StageError("oversize_file", f"{name} is {after.st_size} bytes; limit is {limit}")
        chunks: list[bytes] = []
        total = 0
        while True:
            block = os.read(fd, min(65536, limit + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
            if total > limit:
                raise StageError("oversize_file", f"{name} grew past {limit} bytes while being read")
        return b"".join(chunks)
    finally:
        os.close(fd)


def read_directory(path: Path, *, extra_allowed: tuple[str, ...] = ()) -> PackageFiles:
    """Read exactly the three allowlisted files of `path`; refuse symlinks, extras, sub-directories, specials, oversize."""
    dfd = _open_dir(path)
    try:
        with os.scandir(dfd) as it:
            entries = list(it)
        allowed = set(STAGED_NAMES) | set(extra_allowed)
        for entry in entries:
            if entry.name not in allowed:
                if entry.is_dir(follow_symlinks=False):
                    raise StageError("sub_directory", "package directory contains a sub-directory")
                raise StageError("extra_entry", "package directory contains an entry outside the allowlist")
        present = {entry.name for entry in entries}
        for name in STAGED_NAMES:
            if name not in present:
                raise StageError("missing_file", f"{name} is missing")
        return PackageFiles(*(_read_regular(dfd, name) for name in STAGED_NAMES))
    finally:
        os.close(dfd)


def read_one(directory: Path, name: str) -> bytes:
    """Read a single allowlisted file (used for `intake_result.json`) with the same safety rules."""
    return read_one_any(directory, name, _limit(name))


def read_one_any(directory: Path, name: str, limit: int) -> bytes:
    """Like `read_one` for a name outside the staged set (review-area files) with an explicit size bound."""
    dfd = _open_dir(directory)
    try:
        return _read_regular(dfd, name, limit)
    except StageError:
        raise
    finally:
        os.close(dfd)


def write_new(path: Path, data: bytes) -> None:
    """Create `path` exclusively (never overwrites, never follows a symlink) and write `data`."""
    fd = os.open(os.fspath(path), _WRITE_FLAGS, 0o600)
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(fd, view) :]
        os.fsync(fd)
    finally:
        os.close(fd)


def ensure_root(root: Path) -> Path:
    if root.is_symlink():
        raise StageError("root_symlink", f"{root.name} is a symlink")
    root.mkdir(parents=True, exist_ok=True)
    return root


TEMP_PREFIX = ".tmp-"  # can never match an intake id (`in-` + 16 hex) or the IntakeId pattern, so it is ignored everywhere


def _fsync_directory(path: Path) -> None:
    fd = os.open(os.fspath(path), _DIR_FLAGS)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def stage_atomically(intake_id: str, files: dict[str, bytes]) -> Path:
    """Write `files` into a temporary sibling directory, fsync, then rename it to `<intake_id>`.

    A process killed part-way leaves only a `.tmp-*` directory (ignored by list/show/review and safe to delete), never a
    half-filled `<intake_id>` that would block every later intake of the same package. The rename fails rather than
    replacing an existing intake directory.
    """
    root = ensure_root(config.QUARANTINE_ROOT)
    final = root / intake_id
    temp = root / f"{TEMP_PREFIX}{intake_id}-{secrets.token_hex(4)}"
    try:
        os.mkdir(temp, 0o700)
    except FileExistsError:
        raise StageError("exists", "a temporary stage directory with this name already exists") from None
    try:
        for name, data in files.items():
            write_new(temp / name, data)
        _fsync_directory(temp)
        try:
            os.rename(temp, final)  # atomic; refuses a non-empty existing directory
        except OSError:
            raise StageError("exists", "a quarantine directory for this intake already exists") from None
        _fsync_directory(root)
    except BaseException:
        remove_partial(temp)
        raise
    return final


def remove_partial(directory: Path) -> None:
    """Remove a stage directory this process created and did not finish."""
    shutil.rmtree(directory, ignore_errors=True)
