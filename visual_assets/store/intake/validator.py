"""Independent intake validator. Pure: staged bytes in, findings out. Never trusts the producer.

One policy for every producer class: there is no branch on `producer_class`. A package that cannot be parsed still
gets every claim-free check on the source and preview bytes. Finding details are built only from numbers, hash
prefixes and fixed tokens, never from producer-supplied text, so a hostile package cannot inject text into a record.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from visual_assets.store import config
from visual_assets.store.contracts.base import LicenceState, parse_record
from visual_assets.store.contracts.handoff import (
    HANDOFF_ASSERTION,
    CandidateHandoffPackage,
    ProducerState,
    ProducerValidation,
)
from visual_assets.store.contracts.intake import MAX_FINDINGS, IntakeFinding
from visual_assets.store.contracts.intake import IntakeFindingCode as Code
from visual_assets.store.errors import ContractError
from visual_assets.store.intake import aseprite, png

VALIDATOR_VERSION = "intake-validator-1"

# A producer signals a feature the store cannot hold by declaring one of these exact tokens as a limitation.
# Provisional until the format/feature decision (U-05); anything else in `declared_limitations` is informational.
UNSUPPORTED_LIMITATIONS = frozenset(
    {
        "unsupported:tilemap",
        "unsupported:indexed_color",
        "unsupported:grayscale",
        "unsupported:linked_cels",
        "unsupported:external_reference",
    }
)

_PARSE_CODES = {
    "oversize": Code.PACKAGE_UNREADABLE,
    "invalid_utf8": Code.PACKAGE_UNREADABLE,
    "invalid_json": Code.PACKAGE_UNREADABLE,
    "non_finite_number": Code.PACKAGE_UNREADABLE,
    "duplicate_key": Code.PACKAGE_DUPLICATE_KEY,
    "unknown_field": Code.PACKAGE_UNKNOWN_FIELD,
    "missing_field": Code.PACKAGE_MISSING_FIELD,
    "wrong_record_type": Code.PACKAGE_WRONG_RECORD_TYPE,
    "unsupported_schema_version": Code.PACKAGE_UNSUPPORTED_VERSION,
}
_SAFE_FIELD = re.compile(r"[a-z][a-z0-9_]{0,40}(\.[a-z0-9_]{1,40}){0,3}")


@dataclass(frozen=True)
class Validation:
    package: CandidateHandoffPackage | None
    findings: tuple[IntakeFinding, ...]


def file_hash(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _finding(code: Code, detail: str) -> IntakeFinding:
    return IntakeFinding(code=code, detail=detail)


def _parse_package(data: bytes) -> tuple[CandidateHandoffPackage | None, list[IntakeFinding]]:
    try:
        return parse_record(CandidateHandoffPackage, data), []
    except ContractError as exc:
        field = exc.field if exc.field and _SAFE_FIELD.fullmatch(exc.field) else None
        if exc.field == "assertion":
            return None, [_finding(Code.ASSERTION_MISSING, "package.json lacks the exact handoff assertion")]
        code = _PARSE_CODES.get(exc.code, Code.PACKAGE_INVALID)
        detail = f"package.json rejected ({exc.code})" + (f" at field {field}" if field else "")
        return None, [_finding(code, detail)]


def _check_source(
    package: CandidateHandoffPackage | None, source: bytes
) -> list[IntakeFinding]:
    facts, problems = aseprite.read_facts(source)
    out = [_finding(code, detail) for code, detail in problems]
    if facts is None:
        return out
    if not (1 <= facts.width <= config.MAX_DIM and 1 <= facts.height <= config.MAX_DIM):
        out.append(_finding(Code.DIMENSION_OUT_OF_BOUNDS, f"source is {facts.width}x{facts.height}; limit is {config.MAX_DIM}"))
    if facts.color_depth != aseprite.DEPTH_RGBA:
        out.append(_finding(Code.SOURCE_UNSUPPORTED_COLOR_DEPTH, f"colour depth is {facts.color_depth} bpp; only 32 (RGBA) is supported"))
    if package is None:
        return out
    claims = (
        (Code.WIDTH_MISMATCH, "width", package.width, facts.width),
        (Code.HEIGHT_MISMATCH, "height", package.height, facts.height),
        (Code.FRAME_COUNT_MISMATCH, "frame count", package.frame_count, facts.frames),
        (Code.LAYER_COUNT_MISMATCH, "layer count", package.layer_count, facts.layers),
        (Code.CEL_COUNT_MISMATCH, "cel count", package.cel_count, facts.cels),
        (Code.TAG_COUNT_MISMATCH, "tag count", package.tag_count, facts.tags),
        (Code.PALETTE_SIZE_MISMATCH, "palette size", package.palette_size, facts.palette_size),
    )
    for code, label, claimed, actual in claims:
        if actual is None:
            continue  # unverifiable; the PALETTE_UNVERIFIABLE finding from the reader already quarantines it
        if claimed != actual:
            out.append(_finding(code, f"claimed {label} {claimed}, source has {actual}"))
    return out


def _check_preview(
    package: CandidateHandoffPackage | None, source: bytes, preview: bytes
) -> list[IntakeFinding]:
    try:
        header = png.read_header(preview)
    except png.PngError as exc:
        code = Code.PNG_SIGNATURE_INVALID if exc.signature else Code.PNG_MALFORMED
        return [_finding(code, str(exc))]
    out: list[IntakeFinding] = []
    if header.width > config.MAX_PREVIEW_DIM or header.height > config.MAX_PREVIEW_DIM:
        out.append(_finding(Code.PREVIEW_OUT_OF_BOUNDS, f"preview is {header.width}x{header.height}; limit is {config.MAX_PREVIEW_DIM}"))
    facts, _ = aseprite.read_facts(source)
    if facts is not None and facts.width >= 1 and facts.height >= 1:
        scale = header.width // facts.width
        if scale < 1 or header.width != facts.width * scale or header.height != facts.height * scale:
            out.append(
                _finding(
                    Code.PREVIEW_DIMENSION_MISMATCH,
                    f"preview {header.width}x{header.height} is not a whole-number scale of source {facts.width}x{facts.height}",
                )
            )
    return out


def _check_policy(package: CandidateHandoffPackage) -> list[IntakeFinding]:
    out: list[IntakeFinding] = []
    if package.licence_state is LicenceState.WITHDRAWN:
        out.append(_finding(Code.LICENCE_WITHDRAWN, "licence state is WITHDRAWN"))
    if package.producer_state is not ProducerState.ACTIVE:
        out.append(_finding(Code.PRODUCER_NOT_ACTIVE, f"producer state is {package.producer_state.value}"))
    if package.producer_validation is ProducerValidation.FAILED:
        out.append(_finding(Code.PRODUCER_VALIDATION_FAILED, "producer-side validation reported FAILED"))
    for token in sorted(UNSUPPORTED_LIMITATIONS.intersection(package.declared_limitations)):
        out.append(_finding(Code.UNSUPPORTED_LIMITATION, f"declared limitation {token}"))
    return out


def validate(package_bytes: bytes, source_bytes: bytes, preview_bytes: bytes) -> Validation:
    """Judge the three staged files. The same checks run for every producer class."""
    package, findings = _parse_package(package_bytes)
    if package is not None:
        if package.source_hash != file_hash(source_bytes):
            findings.append(_finding(Code.SOURCE_HASH_MISMATCH, f"source bytes hash to {file_hash(source_bytes)[:23]}..."))
        if package.preview_hash != file_hash(preview_bytes):
            findings.append(_finding(Code.PREVIEW_HASH_MISMATCH, f"preview bytes hash to {file_hash(preview_bytes)[:23]}..."))
    findings += _check_source(package, source_bytes)
    findings += _check_preview(package, source_bytes, preview_bytes)
    if package is not None:
        findings += _check_policy(package)
    return Validation(package, tuple(findings[:MAX_FINDINGS]))


__all__ = ["HANDOFF_ASSERTION", "UNSUPPORTED_LIMITATIONS", "VALIDATOR_VERSION", "Validation", "file_hash", "validate"]
