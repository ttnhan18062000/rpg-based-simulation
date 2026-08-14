---
status: active
layer: guidelines
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
date: 2026-07-18
tags: [frontmatter, data-quality]
---

# Implementation Plan — TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM

## Summary

Create `tools/ticket_field_values.py` as the single canonical source for
all four ticket-field enums (`TIER_VALUES`, `PRIORITY_VALUES`,
`WORKFLOW_STATUS_VALUES` moved from `ingest.py`, `LAYER_VALUES` re-exported
from `validate_frontmatter.py`), plus a body-section enum-check function
using `parse_body_section`. Wire that function into
`done_checker_static.py::run_static_precheck` as a 6th blocking condition.
Fix `CLAUDE.md`'s Priority line.

## Steps

### Step 1 — Create `tools/ticket_field_values.py`

New file. Contents:
- Module docstring explaining purpose, mirroring `status_drift_check.py`'s
  own docstring shape (why this exists, what it fixes, what it deliberately
  doesn't do).
- `from validate_frontmatter import LAYER_VALUES  # noqa: E402` (after a
  `sys.path` setup identical to `status_drift_check.py`'s own
  `_TOOLS_DIR = Path(__file__).parent` — this file lives directly in
  `tools/`, not `tools/gate_checks/`, so `sys.path` insertion may not even
  be needed if run from repo root with `tools/` importable — verify during
  implementation whether the insertion is actually necessary here or only
  for `gate_checks/*.py`'s one-level-deeper case).
- `TIER_VALUES = frozenset({"hotfix", "standard", "epic"})`
- `PRIORITY_VALUES = frozenset({"P0", "P1", "P2", "P3"})`
- `WORKFLOW_STATUS_VALUES = frozenset({"OPEN", "INPROGRESS", "BLOCKED",
  "DONE", "EPIC_SCOPED"})` (moved from `ingest.py`, frozenset instead of the
  original `sorted(...)` list — check downstream usage in `ingest.py`: if
  `facets["statuses"] = list(WORKFLOW_STATUS_VALUES)` needs a stable sorted
  order, sort at the call site instead of baking list-vs-set into the
  canonical value itself; canonical enums should be sets/frozensets, not
  ordered lists — `LAYER_VALUES` itself is already a plain `set`, matching
  this).
- A function, e.g. `check_body_field_enum(body: str, field: str, valid:
  frozenset) -> tuple[str, str]` returning `("PASS"|"FAIL", evidence)`,
  extracting via `parse_body_section(body, field)` and comparing against
  `valid` (case-sensitive exact match, consistent with how `_check_enum`
  and `status_drift_check.py` both already compare).
- A convenience aggregate, e.g. `check_ticket_field_values(ticket_path:
  Path) -> list[dict]` that reads the file, strips frontmatter, and checks
  both `## Tier` against `TIER_VALUES` and `## Priority` against
  `PRIORITY_VALUES`, returning results in the same `{"status":...,
  "evidence":...}` shape `run_static_precheck`'s other checks use — this is
  the function `done_checker_static.py` will call.

### Step 2 — Update `src/api/agent_ops_dashboard/ingest.py`

Remove the local `WORKFLOW_STATUS_VALUES` definition (currently line 375).
Add `from ticket_field_values import WORKFLOW_STATUS_VALUES  # noqa: E402`
alongside the existing `from validate_frontmatter import ...` /
`from generate_registry import ...` lines. Confirm
`facets["statuses"] = list(WORKFLOW_STATUS_VALUES)` still produces the same
sorted 5-value list as before (sort explicitly at this call site if
`WORKFLOW_STATUS_VALUES` is now an unordered `frozenset`, since the existing
test `test_statuses_facet_is_canonical_full_set_regardless_of_corpus_content`
asserts an exact sorted list — `["BLOCKED", "DONE", "EPIC_SCOPED",
"INPROGRESS", "OPEN"]`).

### Step 3 — Wire into `done_checker_static.py`

Import `check_ticket_field_values` from `ticket_field_values`. Add a 6th
tuple to `run_static_precheck`'s `checks` tuple, e.g.
`("ticket_field_values_valid", check_ticket_field_values(ticket_path))` —
match the existing tuple-of-tuples shape exactly (each entry is
`(name, (status, evidence))`), so the list-comprehension below it needs no
change. Determine `ticket_path` the same way `check_frontmatter_valid`
already does (default `tickets/inprogress/{ticket_id}.md`).

### Step 4 — Fix `CLAUDE.md`

Change `## Priority       (P0 | P1 | P2)` to `## Priority       (P0 | P1 |
P2 | P3)` in the Ticket Format section.

### Step 5 — Tests

Write `tests/tools/test_ticket_field_values.py` per test_plan.md. Extend
`tests/tools/test_done_checker_static.py` with the `run_static_precheck`
integration test. Run the full regression surface.

## Scope Guards

- Do not touch `status_drift_check.py`'s own `EPIC_TIER_VALUES` — it is a
  distinct, narrower drift-detection concept (see investigation.md's risk
  note), not the same thing as this ticket's canonical source of truth.
- Do not touch `Tag`/`tag_registry.py` at all.
- Do not touch the frontmatter enums (`STATUS_VALUES`/`AUTHORITY_VALUES`/
  `AUDIENCE_VALUES`/`PHASE_VALUES`) — already correct and out of scope.
- Do not fix the 2 known `"P1: High"` corpus tickets in this ticket — that
  is the dependent sibling ticket's job (needs this ticket's check function
  to exist first, and should re-scan fresh rather than trust this ticket's
  preliminary count).

## Dependency Map

Step 1 → Step 2 and Step 3 (both need the new module to exist) → Step 5
(needs Steps 1-3 complete to test against). Step 4 is independent, can run
any time.

## Acceptance Criteria Map

- AC "module exists, single source" → Step 1.
- AC "P1: High rejected" / "valid combo passes" → Step 1 (function) + Step 5
  (tests).
- AC "run_static_precheck genuinely blocks" → Step 3 + Step 5 (integration
  test + genuine-catch proof).
- AC "CLAUDE.md P3" → Step 4.
- AC "existing suites still pass" → Step 5 (full regression run).

## Anti-Drift Notes

`LAYER_VALUES` must be imported, never copied — a copy would itself become
a second source of truth subject to exactly the drift this whole epic
exists to prevent. Verify via the anti-drift identity test in test_plan.md.

## Deviations

None material. Step 1's open question ("verify during implementation
whether the `sys.path` insertion is actually necessary") was resolved by
including it, matching `status_drift_check.py`'s exact pattern — needed
because the module is imported from `src/api/agent_ops_dashboard/ingest.py`
and `tools/gate_checks/done_checker_static.py`, neither of which is
guaranteed to already have plain `tools/` (as opposed to `tools/gate_checks/`)
on `sys.path` at import time.
