"""Sprite directories, immutable revision files, hash sidecars and publication.

`log` uses the logger name "aseprite_mcp" so existing log filters keep working.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path

from visual_assets.drawing import config
from visual_assets.drawing.errors import AdapterError

log = logging.getLogger("aseprite_mcp")

REV_RE = re.compile(r"^r(\d{4})$")


def sprite_dir(name: str) -> Path:
    d = config.WORKSPACE / "sprites" / name
    if d.is_symlink():
        raise AdapterError(f"sprite directory for {name} is a symlink; refusing to use it")
    return d


def rev_files(name: str) -> list[tuple[int, Path]]:
    d = sprite_dir(name)
    if not d.is_dir():
        return []
    out = []
    for p in d.glob("r????.aseprite"):
        m = REV_RE.fullmatch(p.stem)
        if m and not p.is_symlink() and p.is_file():
            out.append((int(m.group(1)), p))
    return sorted(out)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_revision(name: str, revision: str | None) -> tuple[str, Path, str]:
    revs = rev_files(name)
    if not revs:
        raise AdapterError(f"no such sprite: {name}")
    if revision is None:
        num, path = revs[-1]
    else:
        m = REV_RE.fullmatch(revision) if isinstance(revision, str) else None
        if not m:
            raise AdapterError("revision must look like r0001")
        found = dict(revs).get(int(m.group(1)))
        if found is None:
            raise AdapterError(f"no such revision: {revision}")
        num, path = int(m.group(1)), found
    expected = path.with_suffix(".sha256").read_text().strip()
    if sha256_file(path) != expected:
        raise AdapterError(f"{name}/r{num:04d} failed its content-hash check; refusing to use it")
    return f"r{num:04d}", path, expected


def publish(name: str, job: Path) -> tuple[str, str]:
    """Hard-link the job output as the next revision. Never overwrites."""
    out = job / "out.aseprite"
    if not out.is_file() or out.stat().st_size == 0 or out.stat().st_size > config.MAX_FILE_BYTES:
        raise AdapterError("aseprite did not produce a valid output file")
    revs = rev_files(name)
    num = (revs[-1][0] if revs else 0) + 1
    if num > config.MAX_REVISIONS:
        raise AdapterError("revision limit reached")
    d = sprite_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    target = d / f"r{num:04d}.aseprite"
    sidecar = target.with_suffix(".sha256")
    digest = sha256_file(out)
    if target.exists() or target.is_symlink():
        raise AdapterError("revision collision; retry")
    # Sidecar first, created exclusively: a visible revision file must never lack its hash (that
    # would brick the sprite), and a sidecar that already exists is never overwritten (it may belong
    # to a competing writer's revision). A sidecar with no revision file next to it is an orphan from
    # an interrupted publish: remove it once and retry. Writers that hold the sprite flock cannot
    # race here; this guards the case where one does not.
    created = False
    try:
        for attempt in (1, 2):
            try:
                fh = open(sidecar, "x")
            except FileExistsError:
                if attempt == 2 or target.exists() or target.is_symlink():
                    raise
                sidecar.unlink(missing_ok=True)
                continue
            created = True
            with fh:
                fh.write(digest + "\n")
            break
        os.link(out, target)  # same filesystem as the job dir; fails if target exists
    except FileExistsError as exc:
        if created:
            sidecar.unlink(missing_ok=True)  # only ever our own sidecar; theirs was never touched
        raise AdapterError("revision collision; retry") from exc
    except OSError as exc:
        if created:
            sidecar.unlink(missing_ok=True)
        log.warning("publish of %s/r%04d failed: %s", name, num, exc)
        raise AdapterError("could not publish revision (storage error); nothing was saved") from exc
    return f"r{num:04d}", digest
