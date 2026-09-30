"""Canonical closed enums for ticket-body fields (`## Tier`, `## Priority`, `## Status`) plus a
re-export of `## Status`'s frontmatter sibling `layer:`, and a hard-validation check for the two
fields (Tier, Priority) that had no enforcement at all before this module existed.

Built for TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM. `## Tier`/`## Priority`/`## Status` are
**body-section** fields, parsed via `tools/generate_registry.py::parse_body_section` — a
completely different code path from `tools/validate_frontmatter.py`'s frontmatter-only
`extract_frontmatter`/`_check_enum`, which is why `layer:` (a frontmatter field) has always had a
real hard-validation gate at ticket-close time (`validate_frontmatter.py::validate_file`, invoked
by `tools/gate_checks/done_checker_static.py::check_frontmatter_valid`) while Tier/Priority never
did. `## Status` gained a canonical set earlier today (TCK-20260718-STATUS-FACET-CANONICAL,
originally `WORKFLOW_STATUS_VALUES` defined locally in
`src/api/agent_ops_dashboard/ingest.py`) but only as a dashboard-facet source, not a ticket-closing
gate — this module is the single shared home for all four, so `ingest.py`, `done_checker_static.py`,
and `tools/gate_checks/status_drift_check.py` each import from exactly one place instead of
defining or re-deriving their own slice of "what values can this field hold."

`LAYER_VALUES` is imported (never copied) from `validate_frontmatter.py` — a copy would itself
become a second source of truth for the exact class of drift this whole effort exists to prevent
(see `status_drift_check.py`'s own docstring for the concrete precedent: a duplicated,
first-token-only regex went stale twice before being replaced with a direct call to the real
extraction function).

`check_ticket_field_values` is intentionally narrow: it only validates `## Tier` and `## Priority`
against `TIER_VALUES`/`PRIORITY_VALUES` (plus the optional `## Disposition` pair when present). It does NOT re-validate `## Status` — that remains
`status_drift_check.py`'s job (a detection-only tool today, unwired, per that module's own
documented precedent), and does NOT touch `layer:` — already enforced by
`validate_frontmatter.py`/`check_frontmatter_valid`. Wired into
`done_checker_static.py::run_static_precheck` as a new blocking Part A condition, so a ticket
cannot reach `READY_TO_CLOSE` with a non-canonical `## Tier` or `## Priority` going forward.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import FrozenSet, List, Tuple

_TOOLS_DIR = Path(__file__).parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from validate_frontmatter import LAYER_VALUES  # noqa: E402,F401
from generate_registry import parse_body_section, _strip_frontmatter  # noqa: E402

TIER_VALUES: FrozenSet[str] = frozenset({"hotfix", "standard", "epic"})
PRIORITY_VALUES: FrozenSet[str] = frozenset({"P0", "P1", "P2", "P3"})
WORKFLOW_STATUS_VALUES: FrozenSet[str] = frozenset(
    {"OPEN", "INPROGRESS", "BLOCKED", "DONE", "EPIC_SCOPED"}
)

# TCK-20260930-DONE-CHECKER-DISPOSITION-CLOSURES: a ticket closed with no implementation records
# why in two body sections -- `## Disposition` (this bare value, validated like Tier/Priority) and
# `## Disposition Rationale` (prose that must cite evidence). Absent `## Disposition` means a
# normal implementation closure. Two sections rather than one so every body field keeps the same
# single parsing convention (`parse_body_section` returns a whole section, never a first line).
DISPOSITION_VALUES: FrozenSet[str] = frozenset(
    {"STALE-PREMISE", "NO-MECHANISM", "DUPLICATE", "SUPERSEDED", "WONT-DO"}
)

_COMMIT_SHA_RE = re.compile(r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b")
_FILE_LINE_RE = re.compile(r"[\w./-]+\.\w+:\d+")
_FENCED_OUTPUT_RE = re.compile(r"```[^\n]*\n\s*\S.*?```", re.DOTALL)


def has_body_section(body: str, section: str) -> bool:
    """True if a `## <section>` heading line exists (even with an empty body)."""
    return re.search(r"^## " + re.escape(section) + r"\s*$", body, re.MULTILINE) is not None


def check_disposition_rationale(body: str) -> Tuple[str, str]:
    """`## Disposition Rationale` must be present, non-empty and cite at least one piece of
    evidence: a commit SHA (7-40 hex chars with a digit and a letter), a `file:line` reference, or
    a fenced block of pasted compile/run output. Callers only invoke this once `## Disposition`
    is present."""
    if not has_body_section(body, "Disposition Rationale"):
        return ("FAIL", "## Disposition Rationale section is missing (required with ## Disposition)")
    rationale = parse_body_section(body, "Disposition Rationale")
    if not rationale:
        return ("FAIL", "## Disposition Rationale is empty")
    if (
        _COMMIT_SHA_RE.search(rationale)
        or _FILE_LINE_RE.search(rationale)
        or _FENCED_OUTPUT_RE.search(rationale)
    ):
        return ("PASS", "## Disposition Rationale cites evidence")
    return (
        "FAIL",
        "## Disposition Rationale cites no evidence "
        "(need a commit SHA, a file:line reference, or a fenced block of run output)",
    )


def check_disposition_fields(body: str) -> Tuple[str, str]:
    """Validate `## Disposition` (enum, via `check_body_field_enum` unchanged) and, when it is
    present, `## Disposition Rationale`. Returns ("NA", ...) when the ticket has no Disposition."""
    if not has_body_section(body, "Disposition"):
        return ("NA", "no ## Disposition — normal implementation closure")
    value = parse_body_section(body, "Disposition")
    if not value:
        return ("FAIL", "## Disposition is present but empty")
    enum_status, enum_evidence = check_body_field_enum(body, "Disposition", DISPOSITION_VALUES)
    rationale_status, rationale_evidence = check_disposition_rationale(body)
    status = "PASS" if enum_status == "PASS" and rationale_status == "PASS" else "FAIL"
    return (status, f"{enum_evidence}; {rationale_evidence}")


def check_body_field_enum(body: str, field: str, valid: FrozenSet[str]) -> Tuple[str, str]:
    """Extract `## <field>` from `body` via `parse_body_section` and check it against `valid`.

    Returns ("PASS", evidence) if the field is absent (nothing to validate — a missing section is
    a different failure mode, caught elsewhere) or matches exactly. Returns ("FAIL", evidence)
    on a non-empty, non-canonical value. Exact-match comparison, consistent with
    `validate_frontmatter.py::_check_enum` and `status_drift_check.py`'s own comparison.
    """
    value = parse_body_section(body, field)
    if not value:
        return ("PASS", f"## {field} not present — nothing to validate here")
    if value in valid:
        return ("PASS", f"## {field} = {value!r} (canonical)")
    return ("FAIL", f"## {field} = {value!r} is not canonical (valid: {sorted(valid)})")


def check_ticket_field_values(ticket_path: Path) -> List[dict]:
    """Validate a ticket file's `## Tier` and `## Priority` body sections against the canonical
    enums. Returns a list of `{"status": "PASS"|"FAIL", "evidence": "..."}` dicts, one per field,
    matching `run_static_precheck`'s other Part A checks' per-check shape.
    """
    text = ticket_path.read_text(encoding="utf-8")
    body = _strip_frontmatter(text)

    tier_status, tier_evidence = check_body_field_enum(body, "Tier", TIER_VALUES)
    priority_status, priority_evidence = check_body_field_enum(body, "Priority", PRIORITY_VALUES)

    disposition_status, disposition_evidence = check_disposition_fields(body)

    if "FAIL" in (tier_status, priority_status, disposition_status):
        combined_status = "FAIL"
    else:
        combined_status = "PASS"

    evidence = f"{tier_evidence}; {priority_evidence}"
    if disposition_status != "NA":
        evidence += f"; {disposition_evidence}"
    return [{
        "status": combined_status,
        "evidence": evidence,
    }]


def main(argv=None) -> int:
    """CLI entry point (TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT). Before this existed,
    `python3 tools/ticket_field_values.py <path>` imported the module, did nothing, and exited 0 —
    indistinguishable from a real pass. This module is named by CLAUDE.md as the authority for
    `## Tier`/`## Priority`; a silent no-op here is the sharpest instance of that defect class.
    Mirrors `tools/gate_checks/done_checker_static.py`'s own CLI shape."""
    parser = argparse.ArgumentParser(
        description="Validate a ticket file's '## Tier' and '## Priority' body fields against "
        "the canonical enums. Prints one readable PASS/FAIL line and exits non-zero on FAIL."
    )
    parser.add_argument("ticket_path", type=Path, help="Path to the ticket markdown file.")
    args = parser.parse_args(argv)

    results = check_ticket_field_values(args.ticket_path)
    any_fail = False
    for r in results:
        if r["status"] == "FAIL":
            any_fail = True
        print(f"[{args.ticket_path}] {r['status']} — {r['evidence']}")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
