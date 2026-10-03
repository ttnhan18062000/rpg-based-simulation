"""`gc`: list (and, only on request, delete) local and generated files nothing needs. Dry run by default.

Garbage means: quarantine directories with no adoption and no pending review (a QUARANTINED or revoked intake, or a leftover `.tmp-*`), review exports whose
intake is adopted, revoked or gone, and generated PNGs no artifact record refers to. An un-adopted PASSED, unrevoked intake is "pending review" and is kept.
Deleting a locally revoked intake also deletes its local revocation record (it lives inside that directory). Deletion removes ONLY listed items, each
verified to sit under the quarantine root, the review root or `generated/`; it never touches `sources/`, `provenance/` or `manifests/`.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from visual_assets.store import config, records
from visual_assets.store.contracts import IntakeResult, parse_record
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.errors import ContractError, StageError
from visual_assets.store.intake import quarantine

_INTAKE = re.compile(r"in-[0-9a-f]{16}")
_PNG = re.compile(r"([0-9a-f]{64})\.png")


@dataclass(frozen=True)
class GcItem:
    kind: str  # quarantine | review | generated
    path: Path
    reason: str


def _adopted(intake_id: str) -> bool:
    return (records.intake_dir() / f"{intake_id}.json").exists()


def collect() -> list[GcItem]:
    items: list[GcItem] = []
    q = config.QUARANTINE_ROOT
    if q.is_dir() and not q.is_symlink():
        for entry in sorted(q.iterdir()):
            if entry.name.startswith(quarantine.TEMP_PREFIX):
                items.append(GcItem("quarantine", entry, "a leftover temporary directory"))
            elif _INTAKE.fullmatch(entry.name) and entry.is_dir() and not entry.is_symlink() and not _adopted(entry.name):
                revoked = records.intake_revoked_locally(entry.name)
                try:
                    result = parse_record(IntakeResult, quarantine.read_one(entry, quarantine.RESULT_FILE))
                except (StageError, ContractError):
                    continue  # an unreadable intake is not ours to judge; `list` reports it
                if revoked or result.verdict is IntakeVerdict.QUARANTINED:
                    items.append(GcItem("quarantine", entry, "revoked, not adopted" if revoked else "QUARANTINED, not adopted"))
    r = config.REVIEW_ROOT
    if r.is_dir() and not r.is_symlink():
        for entry in sorted(r.iterdir()):
            if not _INTAKE.fullmatch(entry.name) or entry.is_symlink() or not entry.is_dir():
                continue
            gone = not (q / entry.name).is_dir()
            if gone or _adopted(entry.name) or records.intake_revoked_locally(entry.name):
                items.append(GcItem("review", entry, "its intake is gone, adopted or revoked"))
    g = records.generated_dir()
    if g.is_dir() and not g.is_symlink():
        for directory in sorted(g.iterdir()):
            if not directory.is_dir() or directory.is_symlink():
                continue
            referenced = {m.group(1) for p in directory.glob("*.artifact.json") if (m := re.match(r"([0-9a-f]{64})\.", p.name))}
            for png in sorted(directory.iterdir()):
                if (m := _PNG.fullmatch(png.name)) and m.group(1) not in referenced and png.is_file() and not png.is_symlink():
                    items.append(GcItem("generated", png, "no artifact record refers to it"))
    return items


def _inside(path: Path, root: Path) -> bool:
    """`path` is under `root` and neither it nor any directory between is a symlink."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return False
    return True


def gc(*, delete: bool = False) -> list[GcItem]:
    """The garbage list. With `delete=True` each listed item is removed (after re-checking it is where it should be); otherwise nothing changes."""
    items = collect()
    if delete:
        roots = {"quarantine": config.QUARANTINE_ROOT, "review": config.REVIEW_ROOT, "generated": records.generated_dir()}
        for item in items:
            if not _inside(item.path, roots[item.kind]):
                continue
            if item.path.is_dir():
                shutil.rmtree(item.path)
            else:
                item.path.unlink(missing_ok=True)
    return items
