"""Parser and approval-check for agent-orchestration/intentional-divergences.md.

Distinct from docs/guidelines/intentional_divergences.md (the mechanics-bible log, out of scope
for this ticket) — this module only ever reads
`agent-orchestration/intentional-divergences.md`, never that other file. This module is read-only
(`Path.read_text()` only).

Entry format — one `##`-level markdown section per divergence, plain `Key: value` lines (no
per-entry YAML frontmatter):

    ## <axis>:<value-or-id>
    Axis: terminal_status | phase_order | gate_policy | artifact_requirements
    Contract-value: <what the contract says>
    Live-value: <what the live workflow source actually does>
    Rationale: <free text explaining why this is intentional>
    Approved-by: <reviewer name>
    Approved-date: YYYY-MM-DD
    Status: RATIFIED

A divergence only suppresses a conformance failure when its `Axis` + heading identifier matches
the mismatch, `Approved-by` and `Approved-date` (valid `YYYY-MM-DD`) are both present and
non-empty, and `Status: RATIFIED` — a `DEFERRED` or missing-field entry does NOT suppress. Mirrors
docs/guidelines/intentional_divergences.md's own RATIFIED/DEFERRED status vocabulary for
terminology consistency, without sharing the file.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SECTION_HEADING_RE = re.compile(r"^##\s+(\S+):(\S+)\s*$", re.MULTILINE)
_APPROVED_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_FENCED_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)

_FIELD_PATTERNS = {
    "axis": re.compile(r"^Axis:\s*(.+)$", re.MULTILINE),
    "contract_value": re.compile(r"^Contract-value:\s*(.+)$", re.MULTILINE),
    "live_value": re.compile(r"^Live-value:\s*(.+)$", re.MULTILINE),
    "rationale": re.compile(r"^Rationale:\s*(.+)$", re.MULTILINE),
    "approved_by": re.compile(r"^Approved-by:\s*(.+)$", re.MULTILINE),
    "approved_date": re.compile(r"^Approved-date:\s*(.+)$", re.MULTILINE),
    "status": re.compile(r"^Status:\s*(.+)$", re.MULTILINE),
}


@dataclass(frozen=True)
class Divergence:
    axis: str
    identifier: str
    contract_value: str | None
    live_value: str | None
    rationale: str | None
    approved_by: str | None
    approved_date: str | None
    status: str | None


def _extract_field(section_body: str, field: str) -> str | None:
    match = _FIELD_PATTERNS[field].search(section_body)
    return match.group(1).strip() if match else None


def _mask_fenced_code_blocks(text: str) -> str:
    """Blank out ``` fenced code block content (preserving length/line positions) so a literal
    `## <axis>:<value-or-id>` format example inside a fence (e.g. this file's own header docs)
    is never mistaken for a real divergence entry heading."""
    return _FENCED_CODE_BLOCK_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def load_divergences(path: Path) -> list[Divergence]:
    """Parse every `##`-level divergence section in `path`. Returns `[]` if the file has none."""
    text = path.read_text(encoding="utf-8")
    masked_text = _mask_fenced_code_blocks(text)

    headings = list(_SECTION_HEADING_RE.finditer(masked_text))
    divergences: list[Divergence] = []
    for idx, heading_match in enumerate(headings):
        section_end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        section_body = text[heading_match.end():section_end]

        heading_axis, identifier = heading_match.group(1), heading_match.group(2)
        body_axis = _extract_field(section_body, "axis") or heading_axis

        divergences.append(
            Divergence(
                axis=body_axis,
                identifier=identifier,
                contract_value=_extract_field(section_body, "contract_value"),
                live_value=_extract_field(section_body, "live_value"),
                rationale=_extract_field(section_body, "rationale"),
                approved_by=_extract_field(section_body, "approved_by"),
                approved_date=_extract_field(section_body, "approved_date"),
                status=_extract_field(section_body, "status"),
            )
        )
    return divergences


def _is_fully_approved(divergence: Divergence) -> bool:
    if not divergence.approved_by or not divergence.approved_by.strip():
        return False
    if not divergence.approved_date or not _APPROVED_DATE_RE.match(divergence.approved_date.strip()):
        return False
    if divergence.status != "RATIFIED":
        return False
    return True


def is_approved(divergences: list[Divergence], axis: str, value: str) -> bool:
    """True if a matching, fully-approved (RATIFIED, Approved-by + valid Approved-date) entry
    exists for `axis`/`value` (the heading's `<value-or-id>` identifier). A `DEFERRED` entry, or
    one missing `Approved-by`/`Approved-date`, does NOT suppress a conformance failure."""
    return any(
        d.axis == axis and d.identifier == value and _is_fully_approved(d)
        for d in divergences
    )
