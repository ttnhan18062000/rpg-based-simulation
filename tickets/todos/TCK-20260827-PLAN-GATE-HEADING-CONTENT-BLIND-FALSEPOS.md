---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS
phase: open
date: 2026-08-27
tags: [ai, workflows, bug]
---

# TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS

## Title
`plan_gate_static.py`'s Unresolved-Questions check is heading-presence-only, not
content-aware — a recurrence of TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS's exact bug class

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found live during `TCK-20260824-OCCUPATION-CHANGE-TRIGGER` (`m1-quick-wins` batch): the planner
wrote a `## Unresolved Questions` heading in `plan.md` with real content underneath reading
`"None. The one question investigation.md flagged... was checked directly during planning and
resolved..."` — a genuinely resolved, non-blocking plan. `tools/gate_checks/plan_gate_static.py::
plan_has_unresolved_questions_heading()` only regex-matches the heading's *presence*
(`^##\s+Unresolved Questions\s*$`), never inspects the text beneath it, so it returned `True` and
`implement-ticket.js` unconditionally routed this to `NEEDS_HUMAN_INPUT`, stalling the pipeline for
a plan that had no real open question. This is the exact same substring/pattern-blindness bug class
`TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS` was built to fix (that ticket replaced a
`planText.includes('unresolved question')` free-text substring match with this heading-presence
regex specifically because the free-text version false-triggered on "No unresolved questions:
..." — the fix moved the false-positive one layer down instead of eliminating it, since the
planner's own prompt tells it to *always* write the heading, filling it with "None." when nothing
applies rather than omitting it).

## Scope
- Change `plan_has_unresolved_questions_heading()` (or add a sibling function used in its place at
  the `implement-ticket.js` Plan-gate call site) to distinguish a heading followed by a genuine
  "None."/empty body from a heading followed by real content — mirroring how a human reader would
  judge it, not just presence-of-heading
- Decide and document the exact content rule: e.g. heading present + body's first non-blank line
  starts with "None" (case-insensitive) → treated as no unresolved questions; heading present +
  any other body content → still gates to `NEEDS_HUMAN_INPUT`, same as today
- Add unit tests in `tests/tools/` covering: heading absent, heading + real content, heading +
  "None." variants (with/without trailing punctuation/explanation), heading + only whitespace
- Since this bug directly affects the M1 batch this ticket was found in: after the fix lands,
  confirm `TCK-20260824-OCCUPATION-CHANGE-TRIGGER`'s own already-written (and human-verified)
  `plan.md` now correctly evaluates to `False` (no re-block) — a real regression check, not just a
  new unit test

## Out of Scope
- Any other Plan-phase gate logic beyond this one check
- Retroactively re-auditing every prior ticket that may have hit this same false-positive and been
  worked around by direct human review (as this one was) — no evidence any ticket besides this one
  hit it during the M1 batch; not worth a blind audit without a concrete lead

## Acceptance Criteria
- [ ] `plan_has_unresolved_questions_heading()` (or its replacement call site) distinguishes a
      genuine "None." body from real unresolved-question content
- [ ] New unit tests cover the cases listed in Scope
- [ ] `TCK-20260824-OCCUPATION-CHANGE-TRIGGER`'s existing `plan.md` (or `stored_artifacts/` copy
      once that ticket closes) is confirmed to no longer false-trigger the gate

## Related Tickets
- TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS (prior fix for the same bug class, one layer up)
- TCK-20260824-OCCUPATION-CHANGE-TRIGGER (where this was found live)
- TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP (same "file a ticket for a real
  hand-orchestration/tooling gap found live" convention this session has been following)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/gate_checks/plan_gate_static.py
- .claude/workflows/implement-ticket.js (Plan-phase gate call site, ~line 654-680)

## Assumptions / Open Questions
None yet — self-evident intent, minimal targeted fix to one function's classification logic plus
tests.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
