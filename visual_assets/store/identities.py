"""Validated identity types for the store, usable as pydantic field types, plus pure helpers.

Nothing here normalises: a non-canonical value is rejected, never lowercased or trimmed. This module does no
I/O and reads no clock. The eight opaque ids share one syntax; they are distinct types for static checking
(`NewType`) but, being the same shape, cannot be told apart at runtime.
"""

from __future__ import annotations

from typing import Annotated, Any, NewType

from pydantic import AfterValidator, StringConstraints, TypeAdapter, ValidationError

from visual_assets.store.errors import IdentityError

VISUAL_KEY_PATTERN = r"^[a-z][a-z0-9_]{0,31}(\.[a-z][a-z0-9_]{0,31}){1,3}$"
ID_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"
SOURCE_REVISION_PATTERN = r"^r[0-9]{4}$"
RELEASE_ID_PATTERN = r"^rc-[0-9]{4}$"
FILE_HASH_PATTERN = r"^sha256:[0-9a-f]{64}$"
PIXEL_HASH_PATTERN = r"^pixels-v1:[0-9a-f]{64}$"
UTC_TIMESTAMP_PATTERN = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"

FIXTURE_NAMESPACE = "fixture"  # first VisualKey segment reserved for synthetic test data

_MAX_REVISION = 9999


def _check_revision(value: str) -> str:
    if value == "r0000":
        raise ValueError("r0000 is not a valid source revision")
    return value


def _check_timestamp(value: str) -> str:
    year, month, day = int(value[0:4]), int(value[5:7]), int(value[8:10])
    hour, minute, second = int(value[11:13]), int(value[14:16]), int(value[17:19])
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not (1 <= year and 1 <= month <= 12 and 1 <= day <= days[month - 1]):
        raise ValueError("not a real calendar date")
    if not (hour < 24 and minute < 60 and second < 60):
        raise ValueError("not a real time of day")
    return value


VisualKey = Annotated[str, StringConstraints(pattern=VISUAL_KEY_PATTERN, max_length=96)]

_OpaqueId = Annotated[str, StringConstraints(pattern=ID_PATTERN, max_length=64)]
SourceAssetId = NewType("SourceAssetId", _OpaqueId)
ArtifactId = NewType("ArtifactId", _OpaqueId)
CatalogId = NewType("CatalogId", _OpaqueId)
CandidateId = NewType("CandidateId", _OpaqueId)
IntakeId = NewType("IntakeId", _OpaqueId)
AdoptionId = NewType("AdoptionId", _OpaqueId)
RevocationId = NewType("RevocationId", _OpaqueId)

def _check_release(value: str) -> str:
    if value == "rc-0000":
        raise ValueError("rc-0000 is not a valid release id")
    return value


# Release ids are ORDERED (rc-0001, rc-0002, ...) so "greater than every existing one" compares numbers, not opaque strings.
ReleaseId = NewType(
    "ReleaseId", Annotated[str, StringConstraints(pattern=RELEASE_ID_PATTERN), AfterValidator(_check_release)]
)

SourceRevision = Annotated[
    str, StringConstraints(pattern=SOURCE_REVISION_PATTERN), AfterValidator(_check_revision)
]
FileHash = Annotated[str, StringConstraints(pattern=FILE_HASH_PATTERN)]
PixelHash = Annotated[str, StringConstraints(pattern=PIXEL_HASH_PATTERN)]
UtcTimestamp = Annotated[
    str, StringConstraints(pattern=UTC_TIMESTAMP_PATTERN), AfterValidator(_check_timestamp)
]


def check(tp: Any, value: Any) -> Any:
    """Return `value` if it is a canonical `tp` (strict, no coercion); raise `IdentityError` otherwise."""
    try:
        return TypeAdapter(tp).validate_python(value, strict=True)
    except ValidationError as exc:
        raise IdentityError(f"not a valid {getattr(tp, '__name__', tp)}: {exc.errors()[0]['msg']}") from None


def revision_number(revision: str) -> int:
    check(SourceRevision, revision)
    return int(revision[1:])


def next_revision(revision: str) -> str:
    number = revision_number(revision)
    if number >= _MAX_REVISION:
        raise IdentityError("source revision space exhausted (r9999)")
    return f"r{number + 1:04d}"


def release_number(release_id: str) -> int:
    check(ReleaseId, release_id)
    return int(release_id[3:])


def next_release_id(existing: list[str]) -> str:
    """The next ordered release id after every id in `existing` (rc-0001 when there is none)."""
    number = max((release_number(r) for r in existing), default=0) + 1
    if number > 9999:
        raise IdentityError("release id space exhausted (rc-9999)")
    return f"rc-{number:04d}"


def is_fixture_key(key: str) -> bool:
    return key.split(".", 1)[0] == FIXTURE_NAMESPACE
