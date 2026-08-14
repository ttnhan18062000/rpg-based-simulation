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
against `TIER_VALUES`/`PRIORITY_VALUES`. It does NOT re-validate `## Status` — that remains
`status_drift_check.py`'s job (a detection-only tool today, unwired, per that module's own
documented precedent), and does NOT touch `layer:` — already enforced by
`validate_frontmatter.py`/`check_frontmatter_valid`. Wired into
`done_checker_static.py::run_static_precheck` as a new blocking Part A condition, so a ticket
cannot reach `READY_TO_CLOSE` with a non-canonical `## Tier` or `## Priority` going forward.
"""

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

    if tier_status == "FAIL" or priority_status == "FAIL":
        combined_status = "FAIL"
    else:
        combined_status = "PASS"

    return [{
        "status": combined_status,
        "evidence": f"{tier_evidence}; {priority_evidence}",
    }]
