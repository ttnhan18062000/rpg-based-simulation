---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM
phase: done
date: 2026-07-18
tags: [frontmatter, data-quality]
---

# TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM

## Title
Define canonical TIER_VALUES/PRIORITY_VALUES and hard-validate ticket body Tier/Priority at close time

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`Layer` (ticket frontmatter) already has a closed, hardcoded enum
(`LAYER_VALUES` in `tools/validate_frontmatter.py`) hard-validated at
ticket-close time via `done_checker_static.py::check_frontmatter_valid` —
confirmed by reading that function directly: it calls
`validate_file(ticket_path)`, which only checks frontmatter fields
(layer/status/authority/audience/phase/tags). `Tier` and `Priority` are
ticket **body** sections (`## Tier`, `## Priority`), parsed via a completely
different code path (`tools/generate_registry.py::parse_body_section`, the
same function `tools/gate_checks/status_drift_check.py` already uses for
`## Status`) — and have no canonical enum or enforcement at all today.
`Priority` already shows real corpus drift (`"P1: High"` on 2 tickets,
confirmed via direct corpus scan), the same class of bug as the `## Status`
fragmentation fixed earlier today (TCK-20260718-STATUS-DRIFT-REPAIR /
-SUFFIX-TRIM / -MULTILINE-FIX). This ticket defines the canonical Tier/
Priority enums and makes them a real closing gate, not just documentation.

## Scope
- Create `tools/ticket_field_values.py` — a new shared module, not nested
  inside `tools/gate_checks/` since it will be imported by
  `src/api/agent_ops_dashboard/ingest.py` too (outside the gate_checks
  package), parallel to existing top-level `tools/` modules
  (`generate_registry.py`, `validate_frontmatter.py`, `tag_registry.py`).
  Define: `TIER_VALUES = frozenset({"hotfix", "standard", "epic"})`,
  `PRIORITY_VALUES = frozenset({"P0", "P1", "P2", "P3"})`,
  `WORKFLOW_STATUS_VALUES` (move here from
  `src/api/agent_ops_dashboard/ingest.py`, where it was added earlier today
  by TCK-20260718-STATUS-FACET-CANONICAL — re-export from `ingest.py` for
  any existing importers, or update `ingest.py`'s own import instead,
  whichever the investigation finds is the single actual import site),
  and `LAYER_VALUES` re-exported (imported, not duplicated) from
  `tools/validate_frontmatter.py`, so one module is the single place to get
  any of the four canonical ticket-field enums.
- Add a body-section enum check function to this new module (or to
  `tools/gate_checks/`, whichever keeps the dependency direction cleanest —
  investigate `status_drift_check.py`'s existing shape first, it already
  does almost exactly this for `## Status`), using `parse_body_section` to
  extract `## Tier`/`## Priority` and compare against the canonical sets.
- Wire this check into `tools/gate_checks/done_checker_static.py`'s
  `run_static_precheck` as a new Part A condition (currently 5:
  `staging_artifacts_complete`, `data_runs_clean`, `ticket_location`,
  `working_log_no_row_yet`, `frontmatter_valid` — add a 6th, e.g.
  `ticket_field_values_valid`), so a ticket cannot reach `READY_TO_CLOSE`
  with a non-canonical `## Tier` or `## Priority`.
- Fix `CLAUDE.md`'s Ticket Format section — its `## Priority` line
  currently reads `(P0 | P1 | P2)`, missing `P3` (used 24 times in the real
  corpus, confirmed via direct scan).

## Out of Scope
- Re-scanning/fixing the existing ticket corpus's drift — that is
  TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP, which depends on this ticket.
- Any change to the Agent Ops Dashboard's facets computation — that is
  TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL, which depends on this one.
- Any change to `Tag`'s open-vocabulary registry system.
- Any change to the already-working frontmatter enums
  (`STATUS_VALUES`/`AUTHORITY_VALUES`/`AUDIENCE_VALUES`/`PHASE_VALUES`).

## Acceptance Criteria
- [ ] `tools/ticket_field_values.py` exists and defines/re-exports
      `TIER_VALUES`, `PRIORITY_VALUES`, `WORKFLOW_STATUS_VALUES`,
      `LAYER_VALUES` — each importable from exactly one canonical location.
- [ ] A new test creates a ticket fixture with `## Priority\nP1: High` and
      confirms the new check function returns a FAIL/non-canonical result
      for it (not just that the function exists — that it actually rejects
      the known-bad value).
- [ ] A new test creates a ticket fixture with a valid `## Tier`/
      `## Priority` combination and confirms the check passes.
- [ ] `run_static_precheck`'s returned checklist includes the new condition,
      and a full pipeline test proves a ticket with an invalid body
      `## Priority` cannot reach `READY_TO_CLOSE` — genuinely blocked, not
      just theoretically checkable. Verify this the same way
      TCK-20260718-FILTER-SELECT-DROPOUT's regression test was verified:
      confirm the new test actually fails against the pre-fix code path
      (e.g. via `git stash` on the new check-function file alone) before
      trusting that it catches anything.
- [ ] `CLAUDE.md`'s `## Priority` line reads `(P0 | P1 | P2 | P3)`.
- [ ] Existing test suites (`test_validate_frontmatter.py`,
      `test_status_drift_check.py`, `test_done_checker_static.py`,
      `test_agent_ops_dashboard_ingest.py`) all still pass unmodified in
      behavior (only import-source changes, no behavior change to `Layer`/
      `Status` validation).

## Related Tickets
- Parent epic: TCK-20260718-CANONICAL-FIELD-ENUMS-EPIC
- TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP (depends on this ticket)
- TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL (depends on this ticket)
- TCK-20260718-STATUS-FACET-CANONICAL (prior art — the `WORKFLOW_STATUS_VALUES`
  pattern this ticket generalizes)
- TCK-20260718-STATUS-DRIFT-REPAIR / -SUFFIX-TRIM / -MULTILINE-FIX (prior
  art — the drift-detection pattern this ticket's corpus-cleanup sibling
  will follow)

## Related Docs
- CLAUDE.md (Ticket Format section)
- docs/plans/agent_ops_dashboard/proposal_canonical_ticket_field_enums.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/validate_frontmatter.py
- tools/generate_registry.py
- tools/gate_checks/done_checker_static.py
- tools/gate_checks/status_drift_check.py
- src/api/agent_ops_dashboard/ingest.py
- tests/tools/test_done_checker_static.py
- tests/tools/test_status_drift_check.py
- CLAUDE.md

## Assumptions / Open Questions
- Whether the new body-section enum check function lives in
  `tools/ticket_field_values.py` itself or a sibling in
  `tools/gate_checks/` — left for implementation to decide based on which
  keeps `tools/gate_checks/status_drift_check.py`'s existing import
  direction (`gate_checks/` importing from top-level `tools/`, never the
  reverse) intact.

## Implementation Notes

**Execution note (self-flagged deviation):** this ticket, and the whole
parent epic, was implemented by a forked execution context with no Agent
tool access (a hard rule of that context, not a transient outage) — every
phase (Scope/Investigate/Plan/Review/Implement/Architecture-Verify/Test/
Parity/Verify/Finalize) was executed directly via Read/Edit/Bash/Write
rather than via role-specific sub-agent spawns, mirroring the exact fallback
pattern several tickets earlier today (TCK-20260718-STATUS-MULTILINE-FIX,
TCK-20260718-STATUS-FACET-CANONICAL, TCK-20260718-FILTER-SELECT-DROPOUT)
already established and self-flagged the same way.

Created `tools/ticket_field_values.py` (new module) defining `TIER_VALUES`,
`PRIORITY_VALUES`, `WORKFLOW_STATUS_VALUES` (relocated from
`src/api/agent_ops_dashboard/ingest.py`, where TCK-20260718-STATUS-FACET-CANONICAL
originally added it as a dashboard-local definition), and re-exporting
`LAYER_VALUES` (imported, never copied, from `validate_frontmatter.py`).
Added `check_body_field_enum`/`check_ticket_field_values`, using
`parse_body_section` — never a bespoke regex, per this session's established
lesson from `status_drift_check.py`'s own docstring.

Updated `ingest.py`'s import to pull `WORKFLOW_STATUS_VALUES` from the new
module; changed `facets["statuses"]` from `list(WORKFLOW_STATUS_VALUES)` to
`sorted(WORKFLOW_STATUS_VALUES)` since the canonical set is now an unordered
`frozenset` rather than a pre-sorted list — confirmed the existing pinned
test still asserts and passes the identical sorted 5-value output, i.e. this
is a pure relocation with zero externally-observable behavior change.

Wired `check_ticket_field_values_valid` (a small adapter unwrapping the new
function's `list[dict]` return to the `(status, evidence)` tuple shape) into
`done_checker_static.py::run_static_precheck` as a 6th Part A condition
(`ticket_field_values_valid`) — `run_static_precheck` now returns 6
conditions, not 5. Updated the one existing test that asserted an exact
count of 5. Did not update `implement-ticket.js`'s Verify-phase prompt text
(which cites "conditions 3, 4, 7, 10, 12" by CLAUDE.md DoD-list number) — the
new condition is additive, not a renumbering of an existing DoD list item,
so that wording remains accurate as-is; left for a future ticket if a
dedicated DoD-list entry for this check is ever wanted.

Fixed `CLAUDE.md`'s `## Priority` line (`P0 | P1 | P2` → `P0 | P1 | P2 |
P3`).

## Test Summary

- `python3 -m pytest tests/tools/test_ticket_field_values.py -q` — 8/8
  passing (canonical-set values, `LAYER_VALUES` identity — not equality,
  proving no duplication — `check_body_field_enum`/`check_ticket_field_values`
  PASS/FAIL/absent-section cases).
- `python3 -m pytest tests/tools/test_ticket_field_values.py
  tests/tools/test_done_checker_static.py tests/tools/test_validate_frontmatter.py
  tests/tools/test_status_drift_check.py tests/tools/test_agent_ops_dashboard_ingest.py
  -q` — 190/190 passing.
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_api.py
  tests/tools/test_agent_ops_dashboard_serve.py
  tests/tools/test_agent_ops_dashboard_api_boundary.py
  tests/tools/test_agent_ops_dashboard_concurrency.py
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -q` — 22/22
  passing (full dashboard backend regression surface).
- Direct import sanity check: `src.api.agent_ops_dashboard.main.app` imports
  cleanly after the `ingest.py` change.
- **Genuine-catch proof**: `git stash push -- tools/gate_checks/done_checker_static.py`,
  re-ran the 3 new/updated `run_static_precheck` tests — all 3 failed with
  `KeyError: 'ticket_field_values_valid'`, confirming they would have caught
  the gap pre-fix, not just passed post-fix by coincidence. `git stash pop`
  restored the fix; full suite re-confirmed green afterward.
- Parity cross-reference static check
  (`tools/gate_checks/parity_updater_static.py::cross_reference_touched`)
  confirms `src/api/agent_ops_dashboard/ingest.py`'s expected subsystem
  (`infrastructure.yaml`) was genuinely touched by this ticket's diff — run
  directly and confirmed `PASS`.

## Files Changed
- tools/ticket_field_values.py (new)
- src/api/agent_ops_dashboard/ingest.py (import source change; facets["statuses"]
  now explicitly sorted)
- tools/gate_checks/done_checker_static.py (new `ticket_field_values_valid`
  Part A condition + adapter function)
- tests/tools/test_ticket_field_values.py (new, 8 tests)
- tests/tools/test_done_checker_static.py (updated count assertion; 2 new
  integration tests)
- CLAUDE.md (Priority line fix)
- docs/parity_ledger/infrastructure.yaml (new INFRA-278 entry)

## Completion Summary
All acceptance criteria met: `tools/ticket_field_values.py` is the single
importable source for `TIER_VALUES`/`PRIORITY_VALUES`/`WORKFLOW_STATUS_VALUES`/
`LAYER_VALUES`; a ticket with `## Priority\nP1: High` is genuinely rejected
by `run_static_precheck`'s new `ticket_field_values_valid` condition, proven
via a stash-based genuine-catch test rather than just asserted; `CLAUDE.md`'s
Priority line now correctly lists all 4 values; the full regression surface
(190 gate-check/validation tests + 22 dashboard-backend tests) is green with
zero behavior change to any existing facet output. This ticket intentionally
does not touch the existing ticket corpus (2 known `"P1: High"` cases plus
whatever a fresh full-corpus scan finds) — that is
TCK-20260718-TIER-PRIORITY-CORPUS-CLEANUP's job, which depends on this
ticket and must re-run the real check function fresh rather than trust any
number quoted here.
