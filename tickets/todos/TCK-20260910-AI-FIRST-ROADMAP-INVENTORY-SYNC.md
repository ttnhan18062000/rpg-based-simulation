---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260910-AI-FIRST-ROADMAP-INVENTORY-SYNC
phase: open
date: 2026-09-10
tags: [ai, documentation]
---

# TCK-20260910-AI-FIRST-ROADMAP-INVENTORY-SYNC

## Title
Sync `roadmap.md`'s 21-row inventory table with real shipped state

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`'s inventory table is the
intended authoritative "what's left" index for the AI-First Hardening track, but it has drifted:
several items shipped in PRs #141/#145/#149 without their rows being updated, so the table
reports work as outstanding that is actually done.

This is not cosmetic. Determining true status now requires cross-checking `tickets/done/`
against the table item by item — that has been done at least twice in the last few days to
answer "what's next," each time re-deriving what the table was supposed to record. The table
misreporting its own subject matter is the cost being fixed here.

Confirmed drifted as of 2026-09-10 (verify each rather than trusting this list — other sessions
may land changes in the interim):

| Item | Table says | Actually |
|---|---|---|
| 3 — Versioned capability-envelope baseline | outstanding | shipped, `TCK-20260904-CAPABILITY-ENVELOPE-BASELINE` |
| 9 — Model-diverse reviewer, shadow logging | outstanding | shipped, `TCK-20260904-SHADOW-REVIEWER-LOGGING` (PR #141) |
| 11 — `working_log.csv` parser | outstanding | shipped, `TCK-20260904-WORKING-LOG-CSV-PARSER` (PR #141) |
| 12 — Provider-portability conformance test | outstanding | shipped, `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST` (PR #141) |
| 14 — Ticket-claim detection logging | outstanding | shipped, `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING` (PR #145) |
| 15 — Phase-level resume design | outstanding | shipped, `TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN` (PR #145) |

## Scope
- Update each drifted row to the same `~~struck~~ **SHIPPED** — <ticket>` convention rows 4, 5, 7,
  8, and 10 already use, so the table stays internally consistent rather than gaining a second
  notation style.
- Re-verify every remaining row's status against `tickets/done/` while in there — the six above
  are the ones found on 2026-09-10, not necessarily the complete set by the time this runs.
- Update the running counts in the prose beneath the table (the "N remaining to implement" /
  "still Horizon-2-only" sentences), which are derived from the table and will be wrong once the
  rows change.
- Preserve the distinction rows 10 and 6 already draw between "code shipped" and "acceptance
  signal confirmed" — item 10's real-run confirmation is still genuinely outstanding, so it must
  not be flattened to plain SHIPPED.

## Out of Scope
- Implementing any of the still-outstanding roadmap items themselves (item 1's Waves 2/3, item
  10's real-run confirmation, Bucket B/C items).
- Restructuring the table, changing its columns, or re-bucketing items — status accuracy only.
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` / item 6's own row, which is being handled by the
  KGMCP completion work and will need its own final update when that lands.

## Acceptance Criteria
- [ ] Every inventory row's status reflects real `tickets/done/` state, verified item by item.
- [ ] The struck/**SHIPPED** notation matches the existing convention; no second style introduced.
- [ ] Derived counts in the surrounding prose are recomputed and consistent with the table.
- [ ] Item 10's "shipped code, unconfirmed acceptance signal" distinction is preserved, not
      flattened.

## Related Tickets
- `TCK-20260904-CAPABILITY-ENVELOPE-BASELINE`, `TCK-20260904-SHADOW-REVIEWER-LOGGING`,
  `TCK-20260904-WORKING-LOG-CSV-PARSER`, `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST`,
  `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING`,
  `TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN` — the shipped work the table misses.
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` — item 6's own arc, excluded per Out of Scope.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/`

## Assumptions / Open Questions
- The six drifted rows were identified by cross-checking `origin/main` on 2026-09-10; re-derive
  at implementation time rather than trusting the table above, since it is itself a snapshot of
  the thing being fixed.

## Implementation Notes
(filled in during implementation)

## Test Summary
(filled in during implementation)

## Files Changed
(filled in during implementation)

## Completion Summary
(filled in at close)
