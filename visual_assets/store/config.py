"""Store constants and roots only. A leaf module: imports nothing from the project.

Other modules read these as `config.NAME` at call time (never `from ...config import NAME`), so tests can patch
a module attribute. Every bound below is a proposed budget recorded in `docs/assets/budgets.md` (U-05), pinned to it by a test.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

STORE_FORMAT_VERSION = 1

ENV_CHECKOUT = "VISUAL_ASSETS_CHECKOUT"


class StoreRootError(Exception):
    """`VISUAL_ASSETS_CHECKOUT` names something that is not a store checkout (the server refuses to start rather than write somewhere else)."""


def resolve_visual_assets_dir(environ: Mapping[str, str] | None = None) -> tuple[Path, str]:
    """The `visual_assets` directory the store reads and writes, and where that choice came from (`module` or `env`).

    By default it is the directory this module lives in, so a server launched from a checkout serves that checkout. `VISUAL_ASSETS_CHECKOUT` (an absolute path to a git checkout
    or linked worktree, empty counts as unset) names another one explicitly: the drawing server of a Claude session started in the main checkout can then serve the worktree being
    worked on instead of silently writing intakes into the main checkout's quarantine. A value that is relative, missing, not a git checkout, without a store catalog
    (`visual_assets/catalog/STORE_FORMAT`) or with a store format version other than this code's `STORE_FORMAT_VERSION` is refused, never "corrected" (`TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT`)."""
    value = (os.environ if environ is None else environ).get(ENV_CHECKOUT, "")
    if not value.strip():
        return Path(__file__).resolve().parents[1], "module"
    raw = Path(value).expanduser()
    if not raw.is_absolute():
        raise StoreRootError(f"{ENV_CHECKOUT} must be an absolute path to a git checkout, got a relative one")
    root = raw.resolve()
    if not root.is_dir():
        raise StoreRootError(f"{ENV_CHECKOUT} does not name an existing directory")
    if not (root / ".git").exists():
        raise StoreRootError(f"{ENV_CHECKOUT} is not a git checkout or worktree (no .git)")
    if not (root / "visual_assets" / "catalog" / "STORE_FORMAT").is_file():
        raise StoreRootError(f"{ENV_CHECKOUT} is not a store checkout (no visual_assets/catalog/STORE_FORMAT)")
    stored = _store_format_version(root / "visual_assets" / "catalog" / "STORE_FORMAT")
    if stored != STORE_FORMAT_VERSION:
        raise StoreRootError(f"{ENV_CHECKOUT} names a store of format version {stored if stored is not None else 'unreadable'}, this code writes version {STORE_FORMAT_VERSION}: old code must never write into a newer store or the reverse")
    return root / "visual_assets", "env"


def _store_format_version(path: Path) -> int | None:
    """The `store_format_version: N` line of a catalog's STORE_FORMAT file, or None when it is missing or not an integer."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("store_format_version:"):
                return int(line.split(":", 1)[1].strip())
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    return None


def describe_root(visual_assets_dir: Path | None = None, source: str | None = None) -> dict[str, object]:
    """A path-free label for the root in use (tool results never carry absolute paths): the checkout's directory name, its branch and where the choice came from."""
    directory = _VISUAL_ASSETS if visual_assets_dir is None else visual_assets_dir
    checkout = directory.parent
    branch = "unknown"
    try:
        git = checkout / ".git"
        gitdir = Path(git.read_text().split("gitdir:", 1)[1].strip()) if git.is_file() else git
        head = (gitdir / "HEAD").read_text().strip()
        branch = head.removeprefix("ref: refs/heads/") if head.startswith("ref:") else "detached"
    except (OSError, IndexError):
        pass
    return {"checkout": checkout.name, "branch": branch, "source": source if source is not None else _SOURCE, "linked_worktree": (checkout / ".git").is_file()}


_VISUAL_ASSETS, _SOURCE = resolve_visual_assets_dir()
CATALOG_ROOT = _VISUAL_ASSETS / "catalog"
QUARANTINE_ROOT = CATALOG_ROOT / ".quarantine"
REVIEW_ROOT = CATALOG_ROOT / ".review"
DRAFTS_ROOT = _VISUAL_ASSETS / "drafts"  # tracked draft sets, OUTSIDE the catalog: `build`, `release`, `runtime_export` and catalog `verify` never read it

MAX_RECORD_BYTES = 128 * 1024  # budget: docs/assets/budgets.md
MAX_REGISTRY_BYTES = 7 * 64 * 1024  # budget: docs/assets/budgets.md
MAX_MANIFEST_BYTES = 8 * 64 * 1024  # budget: docs/assets/budgets.md; the widest candidate or runtime manifest (MAX_VISUAL_KEYS entries, each with a detail value, plus the details block), rounded up to 64 KiB
MAX_VISUAL_KEYS = 1024  # budget: docs/assets/budgets.md
MAX_DETAIL_KEYS = 64  # budget: docs/assets/budgets.md; keys declaring a detail axis per registry (the runtime manifest repeats each one's declared values)
MAX_DRAFT_SET_ENTRIES = 256  # budget: docs/assets/budgets.md; entries (slots) in one draft set and in one set adoption record; there is no limit on the number of sets
MAX_DROPPED_DRAFTS = 8  # budget: docs/assets/budgets.md; `draft drop` records per set (ADR D22), sized so a set at MAX_DRAFT_SET_ENTRIES revisions plus all of them stays under MAX_RECORD_BYTES
MAX_ALIASES = 1024  # budget: docs/assets/budgets.md
MAX_SOURCE_BYTES = 100 * 1024  # budget: docs/assets/budgets.md; the D2 (no Git LFS) reversal trigger
MAX_DIM = 128  # budget: docs/assets/budgets.md
MAX_PREVIEW_BYTES = 512 * 1024  # budget: docs/assets/budgets.md
MAX_PREVIEW_DIM = 1024  # budget: docs/assets/budgets.md; 128 px at scale 8, the only scale `export_handoff` produces. Kept low because PNG unfiltering is a pure-Python per-byte loop (a 2048 px preview cost ~16 M steps per decode, and adopt decodes more than once)
MAX_ATLAS_DIM = 1024  # budget: docs/assets/budgets.md; the width and height of one opt-in runtime atlas (`export-runtime --atlas`); a family that does not fit refuses instead of splitting
MAX_DELETION_LOG_BYTES = 1024 * 1024  # budget: docs/assets/budgets.md; the local `gc --delete` log (ADR D24); a full log refuses `gc --delete` until `deletions --archive` moves it aside
MAX_UNADOPTED_INTAKE_AGE_DAYS = 30  # budget: docs/assets/budgets.md (R0, a judgment not a measurement); `gc` may list a PASSED, never-adopted intake and its review export once the intake is older than this many days. Younger ones and everything tracked are never touched
MAX_DECODED_BYTES = 1024 * (1024 * 4 + 1)  # budget: docs/assets/budgets.md; decompressed PNG data above this (a 1024 px RGBA square) is refused before it is inflated
MAX_PNG_FILE_BYTES = 65 * 64 * 1024  # budget: docs/assets/budgets.md; the worst legal PNG (1024 px RGBA noise, written incompressibly) rounded up to 64 KiB
