"""One `gc --delete` removal (ADR D24). Lines of the local, gitignored, append-only deletion log, hash-chained by `prev_hash`.

Not in `RECORD_TYPES`: it is local state (never committed, no committed fixture), parsed and bounded by the same strict machinery.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, StringConstraints

from visual_assets.store.contracts.base import BoundedText, StoreRecord
from visual_assets.store.identities import FileHash, UtcTimestamp

ZERO_HASH = "sha256:" + "0" * 64
KINDS = ("quarantine", "review", "generated")


def _relative_path(value: str) -> str:
    parts = value.split("/")
    if parts[0] not in KINDS or len(parts) < 2 or any(p in ("", ".", "..") for p in parts) or "\\" in value:
        raise ValueError("a deletion path is `<kind>/<relative path>` without `.` or `..` parts")
    return value


DeletionPath = Annotated[BoundedText, AfterValidator(_relative_path)]


class DeletionRecord(StoreRecord):
    record_type: Literal["deletion_record"]
    schema_version: Literal[1]
    kind: Literal["quarantine", "review", "generated"]
    path: DeletionPath
    content_hash: FileHash
    reason: BoundedText
    decided_at: UtcTimestamp
    prev_hash: FileHash
