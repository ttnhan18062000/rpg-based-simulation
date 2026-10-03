---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-MONITORING-SCHEMA-GATE-SYNC
phase: done
date: 2026-07-05
tags: [agent-monitoring, schema, documentation]
---

# TCK-20260705-MONITORING-SCHEMA-GATE-SYNC

## Title
Sync docs/agent-monitoring/schema.md's phase/status enumerations with the new Security-Review gate

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`TCK-20260705-WORKFLOW-SECURITY-GATE` (done) added a new `Security-Review` phase and `SECURITY_BLOCKED`
final_status value to `implement-ticket.js`, and correctly updated `docs/ai/workflows.md`,
`docs/ai/system_overview.md`, and `docs/ai/ticket-lifecycle.md` — but that ticket's own Related Docs
never named `docs/agent-monitoring/schema.md`, the authoritative reference for exactly these two
enumerations. Checked directly: both are genuinely stale.
- `docs/agent-monitoring/schema.md`'s "`phase` values (implement-ticket workflow)" list (line 109)
  reads `Scope, Investigate, Plan, Review, Implement, Test, Parity, Verify, Finalize` — missing
  `Security-Review`.
- Its "`final_status` values" table (lines 51-64) has no row for `SECURITY_BLOCKED`.

## Scope
- Add `Security-Review` to the phase-values list (line 109), in pipeline order (after `Parity`, before
  `Verify`), matching the actual `pushEvent` call order in `implement-ticket.js`.
- Add a `SECURITY_BLOCKED` row to the `final_status` values table, in pipeline order (after
  `DOD_BLOCKED` would be wrong — Security-Review runs before Verify/DOD_BLOCKED; insert it between
  `TESTS_FAILED` and `DOD_BLOCKED` to match actual gate order), with the same one-line style as the
  existing rows (e.g. `| SECURITY_BLOCKED | Security review rejected the change. |`).

## Out of Scope
- Any other section of `schema.md` (the JSON examples, join example, Known Limitations section).
- Re-litigating or expanding the `TCK-20260705-WORKFLOW-PARITY-SKIP` ticket's own doc updates — that
  ticket's changes (the Parity `skipped` status is already covered generically by the existing
  `skipped` status row's "e.g. Investigate/Plan/Review for hotfix tier" example) are not touched here.
- Any code change — this is a pure documentation sync.

## Acceptance Criteria
- [ ] `docs/agent-monitoring/schema.md`'s phase-values list includes `Security-Review` in correct
      pipeline order.
- [ ] Its `final_status` values table includes a `SECURITY_BLOCKED` row in correct pipeline order.
- [ ] No other line in the file is modified.

## Related Tickets
- TCK-20260705-WORKFLOW-SECURITY-GATE (added the phase/status this ticket documents)

## Related Docs
- docs/agent-monitoring/schema.md (edit target)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
None.

## Implementation Notes
- Added `SECURITY_BLOCKED` to the `final_status` values table, positioned between `TESTS_FAILED` and
  `DOD_BLOCKED` to match actual gate order in `implement-ticket.js` (Security-Review runs after Test/Parity,
  before Verify).
- Added `Security-Review` to the phase-values list, same position, plus a one-sentence note that it's
  conditional (absent entirely, not even a `skipped` event, for non-triggering tickets) — this
  distinguishes it from the unconditional phases in the same list.
- Did not touch the Parity `skipped` status — already covered generically by the existing `skipped`
  row's "e.g. Investigate/Plan/Review for hotfix tier" illustrative example, not an exhaustive list.

## Test Summary
- `git diff docs/agent-monitoring/schema.md` — exactly 2 additive changes (1 table row, 1 list entry +
  clarifying sentence), no other line touched.
- `python3 -m pytest tests/tools/test_validate_frontmatter.py -q` → 64 passed (frontmatter untouched).

## Files Changed
- `docs/agent-monitoring/schema.md`

## Completion Summary
Synced `docs/agent-monitoring/schema.md`'s `phase` and `final_status` enumerations with the
`Security-Review`/`SECURITY_BLOCKED` gate added by `TCK-20260705-WORKFLOW-SECURITY-GATE`, which had
correctly updated 3 other docs but not this one (its own Related Docs list never named it). Two-line
fix, no code changes, regression suite unaffected.
