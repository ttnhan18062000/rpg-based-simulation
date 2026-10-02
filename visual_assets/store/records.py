"""Reading catalog records (sources, adoptions, intake copies, revocations) through the same safe reader as intake.

Every function takes an optional `root` (default `config.CATALOG_ROOT`, read at call time). Nothing here writes.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from visual_assets.store import config
from visual_assets.store.contracts import AdoptionRecord, RevocationRecord, SourceRecord, parse_record
from visual_assets.store.contracts.base import StoreRecord
from visual_assets.store.intake import quarantine

REVISION_FILE = re.compile(r"(r[0-9]{4})\.(aseprite|source\.json)")
_SOURCE_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")


def _root(root: Path | None) -> Path:
    return Path(root) if root is not None else config.CATALOG_ROOT


def adoption_id_for(intake_id: str, source_asset_id: str, revision: str) -> str:
    """`ad-` + 16 hex of sha256 over the three ids joined with newlines (so the id is reproducible from the records)."""
    return "ad-" + hashlib.sha256("\n".join((intake_id, source_asset_id, revision)).encode()).hexdigest()[:16]


def sources_dir(root: Path | None = None) -> Path:
    return _root(root) / "sources"


def adoptions_dir(root: Path | None = None) -> Path:
    return _root(root) / "provenance" / "adoptions"


def intake_dir(root: Path | None = None) -> Path:
    return _root(root) / "provenance" / "intake"


def revocations_dir(root: Path | None = None) -> Path:
    return _root(root) / "provenance" / "revocations"


def source_paths(source_asset_id: str, revision: str, root: Path | None = None) -> tuple[Path, Path]:
    directory = sources_dir(root) / source_asset_id
    return directory / f"{revision}.aseprite", directory / f"{revision}.source.json"


def read_file(path: Path, limit: int) -> bytes:
    """Bounded read refusing symlinks, specials and hard links (raises `StageError`)."""
    return quarantine.read_one_any(path.parent, path.name, limit)


def parse_file(cls: type[StoreRecord], path: Path) -> tuple[StoreRecord, bytes]:
    data = read_file(path, config.MAX_RECORD_BYTES)
    return parse_record(cls, data), data


def list_source_ids(root: Path | None = None) -> list[str]:
    base = sources_dir(root)
    if not base.is_dir() or base.is_symlink():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.is_symlink() and _SOURCE_ID.fullmatch(p.name))


def list_revisions(source_asset_id: str, root: Path | None = None) -> list[str]:
    """Revisions that have a SourceRecord file, sorted (the record is what makes a revision exist)."""
    directory = sources_dir(root) / source_asset_id
    if not directory.is_dir() or directory.is_symlink():
        return []
    found = set()
    for entry in directory.iterdir():
        match = REVISION_FILE.fullmatch(entry.name)
        if match and match.group(2) == "source.json":
            found.add(match.group(1))
    return sorted(found)


def load_source(source_asset_id: str, revision: str, root: Path | None = None) -> SourceRecord:
    record, _ = parse_file(SourceRecord, source_paths(source_asset_id, revision, root)[1])
    return record  # type: ignore[return-value]


def load_adoption(adoption_id: str, root: Path | None = None) -> AdoptionRecord:
    record, _ = parse_file(AdoptionRecord, adoptions_dir(root) / f"{adoption_id}.json")
    return record  # type: ignore[return-value]


def find_adoption_for_intake(intake_id: str, root: Path | None = None) -> AdoptionRecord | None:
    """The adoption that consumed `intake_id`, if any (the intake copy's presence marks it adopted)."""
    if not (intake_dir(root) / f"{intake_id}.json").exists():
        return None
    base = adoptions_dir(root)
    if base.is_dir():
        for path in sorted(base.glob("ad-*.json")):
            record = load_adoption(path.stem, root)
            if record.intake_id == intake_id:
                return record
    return None


def revisions_with_source_hash(source_hash: str, root: Path | None = None) -> list[tuple[str, str]]:
    """Every (source_asset_id, revision) whose SourceRecord holds exactly these source bytes' hash, across ALL assets."""
    found = []
    for sid in list_source_ids(root):
        for revision in list_revisions(sid, root):
            if load_source(sid, revision, root).source_hash == source_hash:
                found.append((sid, revision))
    return found


def locally_revoked_source_hashes() -> dict[str, str]:
    """source hash -> intake id, for every un-adopted intake whose quarantine directory carries a local revocation.

    Local means this machine's gitignored quarantine only: another checkout does not see it (stated limit).
    """
    from visual_assets.store.contracts import IntakeResult  # local import keeps the module header unchanged

    out: dict[str, str] = {}
    base = config.QUARANTINE_ROOT
    if not base.is_dir() or base.is_symlink():
        return out
    for entry in sorted(base.iterdir()):
        if re.fullmatch(r"in-[0-9a-f]{16}", entry.name) and intake_revoked_locally(entry.name):
            result, _ = parse_file(IntakeResult, entry / quarantine.RESULT_FILE)
            for staged in result.staged_files:  # type: ignore[union-attr]
                if staged.name == "source.aseprite":
                    out[staged.file_hash] = entry.name
    return out


def all_revocations(root: Path | None = None) -> list[RevocationRecord]:
    """Every revocation record. Raises on an unreadable one: callers decide whether to fail closed."""
    base = revocations_dir(root)
    out: list[RevocationRecord] = []
    if base.is_dir():
        for path in sorted(base.glob("*.json")):
            record, _ = parse_file(RevocationRecord, path)
            out.append(record)  # type: ignore[arg-type]
    return out


def revoked_revisions(source_asset_id: str, root: Path | None = None) -> set[str]:
    revoked = set()
    for record in all_revocations(root):
        target = record.target
        if getattr(target, "kind", "") == "source_revision" and target.source_asset_id == source_asset_id:  # type: ignore[union-attr]
            revoked.add(target.source_revision)  # type: ignore[union-attr]
    return revoked


def intake_revoked_locally(intake_id: str) -> bool:
    """True when `revoke` wrote a local revocation into this intake's quarantine directory."""
    return os.path.lexists(config.QUARANTINE_ROOT / intake_id / quarantine.REVOCATION_FILE)
