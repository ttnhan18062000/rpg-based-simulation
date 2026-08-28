---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED
phase: open
date: 2026-08-29
tags: [ai, workflows, bug]
---

# TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED

## Title
`done_checker_static.py`'s `docs_to_update_coverage` check can't recognize a conditional
investigation.md bullet resolved as "condition not met" — false `DOD_BLOCKED`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found live during `TCK-20260824-AFFECTION-CONTRACT-GATE` (`m1-quick-wins` batch):
`investigation.md`'s "Docs Requiring Update" section listed
`docs/mechanics/04_strategic_cognition.md` as conditional — "only if the implementer chooses to
route Team-Up through tier-5 `GoalRegistry` materialization." The implementer correctly scoped
Team-Up as appraisal-only (verified independently in the real diff: no `GoalRegistry`/tier-5
reference anywhere), so the condition was genuinely never met and the doc correctly did not need
touching. `tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage` does literal
path-diff matching against every backtick-wrapped path in investigation.md's bulleted list — it has
no concept of a conditional bullet being evaluated and resolved as "not applicable," so it returned
`DOD_BLOCKED` for a genuinely correct, fully-substantiated implementation. This is a sibling bug to
`TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS` (same class: a static gate doing
presence/pattern matching instead of understanding resolved-vs-unresolved content), found the very
next day in a different gate.

## Scope
- Decide and implement a way for `check_docs_to_update_coverage` (or the investigation.md format it
  parses) to distinguish an unconditional "this doc must be updated" bullet from a conditional one
  that was evaluated and resolved as not-applicable — e.g. a recognized marker phrase like "Resolved
  during implementation, condition not met" immediately following the path, or a structural change
  to how conditional bullets are written (a separate "Conditionally Required" subsection, machine-
  parsed the same way, with an explicit resolution line required before Verify)
- Add unit tests in `tests/tools/` covering: unconditional bullet + doc untouched (still FAILs, as
  today), unconditional bullet + doc touched (PASSes), conditional bullet resolved-not-applicable +
  doc untouched (should now PASS, currently FAILs), conditional bullet + doc touched anyway (PASSes)
- Confirm the fix doesn't weaken the check for genuine gaps — an unconditional bullet must still hard
  -fail if its doc is untouched; only a real, explicitly-resolved conditional should be exempted

## Out of Scope
- `TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS`'s own fix (a separate gate, separate
  function, tracked separately) -- though both may be worth landing together as a small
  gate-checks-hardening batch if convenient, that's an implementer's call, not this ticket's scope
- Retroactively auditing every prior ticket in this batch for the same false-positive -- no evidence
  any other ticket hit it; not worth a blind audit without a concrete lead

## Acceptance Criteria
- [ ] `check_docs_to_update_coverage` (or its investigation.md-parsing input) distinguishes a
      genuinely resolved-not-applicable conditional bullet from an unaddressed required doc
- [ ] New unit tests cover the cases listed in Scope
- [ ] `TCK-20260824-AFFECTION-CONTRACT-GATE`'s own investigation.md (already manually amended with a
      "Resolved during implementation, condition not met" marker as a stopgap) is confirmed to now
      pass the check for real, not just by the manual marker text happening to work by coincidence

## Related Tickets
- TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS (original ancestor bug class, one gate up)
- TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS (sibling instance, found the day before)
- TCK-20260824-AFFECTION-CONTRACT-GATE (where this was found live)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- .claude/workflows/implement-ticket.js (Verify-phase call site)

## Assumptions / Open Questions
None yet — self-evident intent, minimal targeted fix to one function's classification logic plus
tests, mirroring the sibling ticket's shape.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
