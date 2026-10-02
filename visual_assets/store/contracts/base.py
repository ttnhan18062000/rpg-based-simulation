"""Shared record machinery: strict frozen base, canonical JSON, strict parsing, enums and text types.

Pure: no file, clock or path access. Records are parsed only from JSON bytes so strict validation never has to
coerce (a list is not silently accepted for a tuple field, a string never becomes an enum).
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Annotated, Any, TypeVar, get_args

from pydantic import AfterValidator, BaseModel, ConfigDict, StringConstraints, ValidationError

from visual_assets.store import config
from visual_assets.store.errors import ContractError

SCHEMA_VERSION = 1

_TEXT_PATTERN = r"^\S(?:[^\x00-\x1f\x7f]*\S)?$"  # non-empty, no control characters, no edge whitespace


class Evidence(str, Enum):
    """A provenance field a producer class cannot supply. `None` never means "unknown"."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNAVAILABLE = "UNAVAILABLE"


class ProducerClass(str, Enum):
    MANUAL = "MANUAL"
    CAP_A = "CAP_A"


class LicenceState(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    CLEARED = "CLEARED"
    RESTRICTED = "RESTRICTED"
    WITHDRAWN = "WITHDRAWN"


class IntakeVerdict(str, Enum):
    PASSED = "PASSED"
    QUARANTINED = "QUARANTINED"


def _not_evidence_marker(value: str) -> str:
    if value in {m.value for m in Evidence}:
        raise ValueError("an evidence marker is not a value")
    return value


BoundedText = Annotated[str, StringConstraints(max_length=256, pattern=_TEXT_PATTERN)]
PersonText = Annotated[str, StringConstraints(max_length=128, pattern=_TEXT_PATTERN)]
# a provenance value or an explicit marker; a real value can never spell a marker
ProvenanceText = Annotated[BoundedText, AfterValidator(_not_evidence_marker)] | Evidence

def _check_dim(value: int) -> int:
    if not 1 <= value <= config.MAX_DIM:
        raise ValueError(f"dimension must be 1..{config.MAX_DIM}")
    return value


def _check_count(value: int) -> int:
    if not 0 <= value <= 65535:
        raise ValueError("count must be 0..65535")
    return value


Dimension = Annotated[int, AfterValidator(_check_dim)]
Count = Annotated[int, AfterValidator(_check_count)]


class StoreRecord(BaseModel):
    """Base of every record: unknown fields forbidden, immutable, no coercion."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


RecordT = TypeVar("RecordT", bound=StoreRecord)


def canonical_json(record: StoreRecord) -> bytes:
    """UTF-8, sorted keys, no insignificant whitespace, one trailing newline."""
    try:
        text = json.dumps(
            record.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        data = text.encode("utf-8") + b"\n"
    except (ValueError, UnicodeError) as exc:
        raise ContractError("invalid_record", f"not serialisable: {exc}") from None
    if len(data) > config.MAX_RECORD_BYTES:
        raise ContractError("oversize", f"record exceeds {config.MAX_RECORD_BYTES} bytes")
    return data


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ContractError("duplicate_key", f"duplicate object key {key!r}")
        out[key] = value
    return out


def _reject_constant(name: str) -> Any:
    raise ContractError("non_finite_number", f"{name} is not allowed")


def _expected_literal(cls: type[StoreRecord], field: str) -> Any:
    return get_args(cls.model_fields[field].annotation)[0]


def parse_record(cls: type[RecordT], data: bytes) -> RecordT:
    """Strictly parse `data` as a `cls`; every failure is a `ContractError` with a stable `code`."""
    if len(data) > config.MAX_RECORD_BYTES:
        raise ContractError("oversize", f"input exceeds {config.MAX_RECORD_BYTES} bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise ContractError("invalid_utf8", "input is not valid UTF-8") from None
    try:
        raw = json.loads(text, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
    except ContractError:
        raise
    except (ValueError, RecursionError) as exc:
        raise ContractError("invalid_json", str(exc)) from None
    if not isinstance(raw, dict):
        raise ContractError("invalid_record", "top level must be a JSON object")
    expected = _expected_literal(cls, "record_type")
    if raw.get("record_type") != expected:
        raise ContractError("wrong_record_type", f"expected record_type {expected!r}")
    version = raw.get("schema_version")
    if "schema_version" in raw and not (type(version) is int and version == SCHEMA_VERSION):
        raise ContractError("unsupported_schema_version", f"unsupported schema_version {version!r}")
    try:
        return cls.model_validate_json(text)
    except ValidationError as exc:
        first = exc.errors()[0]
        code = {"extra_forbidden": "unknown_field", "missing": "missing_field"}.get(first["type"], "invalid_record")
        where = ".".join(str(p) for p in first["loc"])
        raise ContractError(code, f"{where}: {first['msg']}") from None
    except (ValueError, UnicodeError) as exc:
        raise ContractError("invalid_record", str(exc)) from None
