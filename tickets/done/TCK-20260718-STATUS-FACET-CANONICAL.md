---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-STATUS-FACET-CANONICAL
phase: done
date: 2026-07-18
tags: []
---

# TCK-20260718-STATUS-FACET-CANONICAL

## Title
Make the Agent Ops Dashboard's Status filter always show all possible statuses, even ones with zero matching tickets

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The user asked that the Agent Ops Dashboard's Tickets view Status filter
dropdown display all possible status values a ticket could hold, even if no
ticket currently has that status — so a status like BLOCKED is still visible
and selectable (returning zero rows) rather than silently disappearing from
the dropdown whenever no ticket happens to be blocked at that moment.

## Scope
- Add a fixed canonical `WORKFLOW_STATUS_VALUES` constant to
  `src/api/agent_ops_dashboard/ingest.py` covering the 5 legitimate body
  `## Status` values: `OPEN`, `INPROGRESS`, `BLOCKED`, `DONE`, `EPIC_SCOPED`.
- Change `get_tickets()`'s `facets["statuses"]` computation to always return
  this fixed list, independent of the currently filtered corpus and any
  active `status` query param.
- Tighten `tools/gate_checks/status_drift_check.py`'s `EPIC_TIER_VALUES`
  from `{"EPIC_SCOPED", "SCOPED"}` to `{"EPIC_SCOPED"}` for consistency with
  the new canonical set, now that the corpus's one remaining bare `SCOPED`
  ticket has already been normalized away.
- Update tests, docs, and the relevant parity ledger entry in the same
  session.

## Out of Scope
- `tiers`/`layers`/`priorities`/`tags` facets — these remain corpus-derived
  exactly as before; only `statuses` changes.
- Any `dashboard-frontend/` code change — confirmed unnecessary via
  investigation.
- The 78 tickets with empty `workflow_status` and the 6 same-line
  colon-format tickets — both remain explicitly deferred, unchanged from the
  two predecessor tickets' own scope decisions.

## Acceptance Criteria
- [x] `facets.statuses` always contains all 5 canonical values
      (`BLOCKED`, `DONE`, `EPIC_SCOPED`, `INPROGRESS`, `OPEN`), independent
      of corpus content, active filters, and pagination.
- [x] `tiers`/`layers`/`priorities`/`tags` facets are unchanged — still
      corpus-derived.
- [x] `EPIC_TIER_VALUES` in `status_drift_check.py` is consistent with the
      dashboard's canonical set (`{"EPIC_SCOPED"}` only).
- [x] `docs/observability/agent_ops_dashboard_contract.md` and
      `docs/guides/agent_ops_dashboard.md` accurately describe the new
      behavior.
- [x] `docs/parity_ledger/infrastructure.yaml`'s `INFRA-275` entry updated
      in the same session — no stale claims left for a future session to
      discover.
- [x] No `dashboard-frontend/` file changed.

## Related Tickets
- TCK-20260718-STATUS-DRIFT-REPAIR (established `EPIC_SCOPED` as canonical)
- TCK-20260718-STATUS-SUFFIX-TRIM
- TCK-20260718-STATUS-MULTILINE-FIX (normalized the corpus's last bare
  `SCOPED` ticket to `EPIC_SCOPED`, and is the ticket whose own parity-entry
  gap this ticket's Step 5 was written to avoid repeating)
- TCK-20260717-TICKETS-TABLE-PAGINATION (introduced the `facets` field this
  ticket modifies)

## Related Docs
- CLAUDE.md's Ticket Format section (source of the 4-value `## Status` enum)
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md
- docs/parity_ledger/infrastructure.yaml (INFRA-275)

## Related Stored Artifacts
- stored_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/
- stored_artifacts/TCK-20260718-STATUS-MULTILINE-FIX/

## Related Code Areas
- src/api/agent_ops_dashboard/ingest.py
- tools/gate_checks/status_drift_check.py
- tests/tools/test_agent_ops_dashboard_ingest.py
- tests/tools/test_status_drift_check.py
- docs/observability/agent_ops_dashboard_contract.md
- docs/guides/agent_ops_dashboard.md
- docs/parity_ledger/infrastructure.yaml

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Executed directly (Read/Edit/Bash/Write tool calls) rather than via the
standard Scope→Investigate→Plan→Review→Implement→Architecture-Verify→
Test→Parity→Verify→Finalize multi-agent pipeline used by earlier tickets
today — this run's execution context (a forked worker) had its Agent tool
disabled by a hard runtime rule prohibiting further subagent spawns, so no
ticket-scoper/investigator/planner/architecture-reviewer/implementer/
test-scoper/parity-updater/done-checker agents were invoked. All the same
work products (investigation.md, plan.md, test_plan.md, this ticket file,
the code/data changes, and the verification steps below) were produced
directly instead. Flagging this deviation explicitly per this project's
traceability rule — no important decision should be undocumented, and per
the immediately-prior ticket's own precedent for the same constraint.

Canonical set derivation: confirmed via a full corpus scan
(`tickets/{done,inprogress,todos}/**/*.md`, using the real
`parse_body_section`/`_strip_frontmatter` extraction) that exactly 3 values
are currently present (`DONE`: 1046, `OPEN`: 12, `EPIC_SCOPED`: 6) and zero
non-canonical values exist outside the already-deferred exemptions.
`INPROGRESS` and `BLOCKED` currently have zero tickets anywhere in the live
corpus — precisely the scenario motivating this ticket, and now directly
covered by `test_statuses_facet_is_canonical_full_set_regardless_of_corpus_content`'s
fixture (which deliberately contains neither).

`EPIC_TIER_VALUES` tightening: found during investigation that
`status_drift_check.py`'s exemption set was looser than the new canonical
list would be. Rather than leave that asymmetry (dashboard treats bare
`SCOPED` as non-canonical/unselectable, checker treats it as legitimately
exempt), tightened it to match, updating and splitting the one existing
test that pinned the old two-value exemption.

Parity gap avoidance: the immediately-prior ticket
(`TCK-20260718-STATUS-MULTILINE-FIX`) also ran without Agent-tool access and
missed updating a stale parity ledger entry (`INFRA-277`) that referenced
code it had rewritten — caught only during the user's independent
post-close review. This ticket's Step 5 was written specifically to avoid
repeating that: `INFRA-275`'s `v2_evidence` and `test_path` were updated in
this same session, with both cited pytest commands re-run and confirmed
live immediately before closing (`66 passed in 1.21s` for the backend
suite, matching what's recorded in the parity entry).

## Test Summary
- `python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py
  tests/tools/test_agent_ops_dashboard_api.py
  tests/tools/test_agent_ops_dashboard_api_boundary.py
  tests/tools/test_agent_ops_dashboard_concurrency.py
  tests/tools/test_agent_ops_dashboard_frontend_api_surface.py
  tests/tools/test_agent_ops_dashboard_serve.py
  tests/tools/test_status_drift_check.py -q` — 66/66 passing (re-run
  immediately before closing, matching the parity ledger's recorded count).
- `cd dashboard-frontend && npm run test -- --run` — 58/58 passing (no
  frontend file changed; run as a regression guard).
- Live corpus scan re-confirmed: `{OPEN, INPROGRESS, BLOCKED, DONE,
  EPIC_SCOPED}` covers every non-deferred-exempt body `## Status` value
  across `tickets/{done,inprogress,todos}/`.

## Files Changed
- src/api/agent_ops_dashboard/ingest.py (new `WORKFLOW_STATUS_VALUES`
  constant; `facets["statuses"]` now returns it unconditionally)
- tools/gate_checks/status_drift_check.py (`EPIC_TIER_VALUES` tightened to
  `{"EPIC_SCOPED"}`; docstring updated)
- tests/tools/test_agent_ops_dashboard_ingest.py (updated one assertion,
  added 2 new tests)
- tests/tools/test_status_drift_check.py (split one test into two, one
  assertion narrowed, one new test added)
- docs/observability/agent_ops_dashboard_contract.md (facets description
  corrected)
- docs/guides/agent_ops_dashboard.md (Tickets-view Status filter behavior
  described)
- docs/parity_ledger/infrastructure.yaml (`INFRA-275` `v2_evidence`/
  `test_path` updated in the same session)

## Completion Summary
`facets.statuses` in `GET /api/tickets` now always returns the fixed
5-value canonical set (`BLOCKED`, `DONE`, `EPIC_SCOPED`, `INPROGRESS`,
`OPEN`) regardless of what's present in the currently filtered ticket
corpus, so the dashboard's Status filter dropdown always shows every valid
status a ticket could hold — including `BLOCKED`/`INPROGRESS`, which
currently have zero matching tickets anywhere in the live corpus. Every
other facet (tiers/layers/priorities/tags) is unchanged, still
corpus-derived. Tightened `status_drift_check.py`'s `EPIC_TIER_VALUES` to
match the new canonical set. Updated the relevant parity ledger entry
(`INFRA-275`) in the same session, avoiding the gap the immediately-prior
ticket left for the user to catch independently. 66/66 backend tests and
58/58 frontend tests passing; no frontend file changes were needed.
