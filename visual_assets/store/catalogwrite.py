"""All-or-nothing publication of several files into the TRACKED catalog. Used only by the human-gated commands.

The files are written and fsynced into a temporary directory under the gitignored quarantine root (same filesystem), then
published one by one with exclusive hard links (`os.link` fails if the target exists, so nothing is ever overwritten),
creating missing parent directories as needed. On any failure every file and every directory created so far is removed,
so the catalog tree is byte-identical to before. A hard kill part-way can leave orphan files; `audit_chain` reports them.
"""

from __future__ import annotations

import os
import secrets
import shutil
from collections.abc import Callable, Sequence
from pathlib import Path

from visual_assets.store import config
from visual_assets.store.errors import GateError
from visual_assets.store.intake import quarantine

# Confirm(expected_id, notices) -> True when the operator has typed `expected_id` after reading `notices`.
Confirm = Callable[[str, Sequence[str]], bool]

_link = os.link  # a module attribute so tests can inject a failure at any position


def _inside(catalog: Path, final: Path) -> None:
    try:
        relative = final.relative_to(catalog)
    except ValueError:
        raise GateError("outside_catalog", f"{final.name} is not inside the catalog") from None
    current = catalog
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise GateError("catalog_symlink", f"{part} inside the catalog is a symlink; refusing to write through it")


def _make_parents(catalog: Path, directory: Path, created: list[Path]) -> None:
    missing: list[Path] = []
    current = directory
    while current != catalog and not current.exists():
        missing.append(current)
        current = current.parent
    for path in reversed(missing):
        os.mkdir(path, 0o755)
        created.append(path)


def publish(files: list[tuple[Path, bytes]]) -> None:
    """Publish `files` (final path, bytes) all together or not at all. An existing target is refused, never replaced."""
    catalog = config.CATALOG_ROOT
    for final, _ in files:
        _inside(catalog, final)
        if final.exists() or final.is_symlink():
            raise GateError("already_exists", f"{final.name} already exists; nothing was written")
    root = quarantine.ensure_root(config.QUARANTINE_ROOT)
    temp = root / f"{quarantine.TEMP_PREFIX}publish-{secrets.token_hex(4)}"
    os.mkdir(temp, 0o700)
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        for index, (_, data) in enumerate(files):
            staged = temp / str(index)
            quarantine.write_new(staged, data)
            os.chmod(staged, 0o644)
        for index, (final, _) in enumerate(files):
            _make_parents(catalog, final.parent, created_dirs)
            try:
                _link(temp / str(index), final)
            except FileExistsError:
                raise GateError("already_exists", f"{final.name} appeared while publishing; nothing was written") from None
            created_files.append(final)
    except BaseException:
        for path in reversed(created_files):
            path.unlink(missing_ok=True)
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(temp, ignore_errors=True)
