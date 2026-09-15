---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-SIBLING-WORKFLOW-SUMMARY-TRUNCATION-MARKERS
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-SIBLING-WORKFLOW-SUMMARY-TRUNCATION-MARKERS

## Title
`create-tickets.js`, `simq-audit.js`, and `implement-epic.js` still truncate event summaries with a
silent `.slice(0, 200)` — the same defect `TCK-20260915-EVENT-SUMMARY-TRUNCATION` fixed only in
`implement-ticket.js`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`TCK-20260915-EVENT-SUMMARY-TRUNCATION` fixed `implement-ticket.js`'s `pushEvent()` (and 10
call-site-level pre-slices) by replacing a silent `.slice(0, 200)` with a `truncateSummary()`
helper that appends a visible `' […]'` marker only when a real cut occurs. That ticket's own scope
named `implement-ticket.js` only (`Related Code Areas` listed only that file's `pushEvent` call
sites).

Peer review of that closed ticket found the identical unmarked-truncation pattern still present in
3 sibling workflows, each with its own central `pushEvent` doing a raw `.slice(0, 200)`:

- `create-tickets.js`:110 (own `pushEvent`) and a second pre-slice at :885
- `simq-audit.js`:35 (own `pushEvent`) and pre-slices at :127, :291, :325
- `implement-epic.js`:356 (a single direct assignment, no `pushEvent` wrapper)

Measured real impact across the corpus (894 summaries sit at exactly 200 chars total, i.e. the
truncation boundary — 838 of those are from `implement-ticket.js`/`implement-epic.js`'s own
`TCK-*`-prefixed runs, already fixed for `implement-ticket.js`'s share):

| `run_id` prefix | Workflow | Truncated / Total events |
|---|---|---|
| `TCK-*` | implement-ticket / implement-epic | 838 / 9,592 |
| `FOLDER-*` | implement-epic | 16 / 218 |
| `CREATE-TICKETS-*` | create-tickets | 15 / 488 |
| `SIMQ-AUDIT-*` | simq-audit | 9 / 25 |

`implement-ticket.js`'s fix covers the large majority of the raw count, but `simq-audit.js`'s own
rate (9/25 = 36%) is the worst of any workflow measured, despite the small absolute count.

## Scope
- Add the same `truncateSummary()`-shaped helper (or import/share the one already defined in
  `implement-ticket.js`, if these files already share any common module — check before
  duplicating) to `create-tickets.js` and `simq-audit.js`'s own `pushEvent` functions, and to
  `implement-epic.js`'s single direct-assignment site.
- Fix each file's own pre-slicing call sites the same way `TCK-20260915-EVENT-SUMMARY-TRUNCATION`
  did: remove redundant pre-slices that feed into the file's own `pushEvent`, and apply the helper
  directly at any site that builds an event object without going through `pushEvent`.

## Out of Scope
- `implement-ticket.js` itself — already fixed.
- Rewriting historical truncated summaries in any of these 3 workflows' own past events.

## Acceptance Criteria
- [ ] `create-tickets.js`, `simq-audit.js`, and `implement-epic.js` each apply a visible-marker
      truncation helper at every summary-producing call site (central `pushEvent` and any
      direct-assignment site), mirroring `implement-ticket.js`'s fix.
- [ ] No raw `.slice(0, 200)` remains in any of the 3 files (regression-tested, mirroring
      `tests/tools/test_event_summary_truncation.py`'s own file-wide assertion).
- [ ] `docs/agent-monitoring/schema.md`'s `summary` field row is updated to note the same
      writer/marker behavior now applies uniformly across all 4 workflow files, not just
      `implement-ticket.js`.

## Related Tickets
- `TCK-20260915-EVENT-SUMMARY-TRUNCATION` (the fix this ticket extends to sibling workflows)
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (the epic during which the fixed ticket, and
  this follow-on gap, were found — this ticket is NOT a child of that epic; it was scoped after
  the epic's own 9-ticket child list was already fixed, and is tracked independently so it does
  not retroactively expand that epic's already-agreed scope)

## Related Docs
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.claude/workflows/create-tickets.js` (`pushEvent` at :110, second pre-slice at :885)
- `.claude/workflows/simq-audit.js` (`pushEvent` at :35, pre-slices at :127, :291, :325)
- `.claude/workflows/implement-epic.js` (:356, direct assignment)

## Assumptions / Open Questions
- Whether these 4 workflow files already share (or should share) one common summary-truncation
  helper module, versus each defining its own copy the way `implement-ticket.js` does today — worth
  a quick check before implementing, to avoid introducing 3 more independent copies of the same
  logic if a shared location already exists or is cheap to add.

## Implementation Notes
Line numbers above are from the peer review that found this gap (2026-09-15) — re-verify via grep
before editing, since they may have shifted.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
