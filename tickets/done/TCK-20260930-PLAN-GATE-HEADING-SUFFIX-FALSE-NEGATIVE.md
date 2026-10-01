---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-PLAN-GATE-HEADING-SUFFIX-FALSE-NEGATIVE
phase: done
date: 2026-09-30
tags: [ai]
---

# TCK-20260930-PLAN-GATE-HEADING-SUFFIX-FALSE-NEGATIVE

## Title
Plan gate misses an `## Unresolved Questions (...)` heading with a suffix and lets open owner decisions through

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tools/gate_checks/plan_gate_static.py` defines `_HEADING_RE = ^##\s+Unresolved Questions\s*$`, so it
matches only the bare heading. A real planner run wrote
`## Unresolved Questions (decide before the implementer runs; do not decide in-plan)` above 3
genuine owner decisions. `plan_has_unresolved_questions_heading()` returned `False`, so
`implement-ticket.js` (~L716-742) would have continued to Review and Implement. The run was only
stopped because the user read the plan's text. Reported by test-architecture-implementer
(2026-10-01) from a real run of `TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP`.

This is the opposite error class from the two earlier fixes in the same module
(`TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS`, `TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS`,
both false positives). The module is fail-open, so a missed heading is silent.

## Scope
1. Match the heading with an optional suffix, e.g. `^##\s+Unresolved Questions\b.*$`, keeping the
   existing content-aware body check (a body starting with the word "None" still counts as
   resolved).
2. Regression tests: suffixed heading with real questions returns `True`; suffixed heading with a
   "None." body returns `False`; bare heading behaviour is unchanged; a heading such as
   `## Unresolved Questions Resolved Later` is decided deliberately and pinned either way.
3. Check whether the planner prompt (`.claude/agents/planner.md` L82, `implement-ticket.js` L702)
   should also say to use the bare heading. State the call and why. Do not change it only to make
   the gate pass.

## Out of Scope
- Making the gate blocking or fail-closed on a missing plan file.
- Any other gate in `tools/gate_checks/`.

## Acceptance Criteria
1. The suffixed heading from the reported plan returns `True` in a test using its exact text.
2. All pre-existing `plan_gate_static` tests pass unchanged.
3. The decision on the planner prompt is recorded in Implementation Notes.

## Related Tickets
- TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS (done)
- TCK-20260827-PLAN-GATE-HEADING-CONTENT-BLIND-FALSEPOS (done)
- TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP (the run that exposed it)

## Related Docs
- `.claude/agents/planner.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/gate_checks/plan_gate_static.py`
- `.claude/workflows/implement-ticket.js` (~L702, ~L716-742)
- `tests/tools/test_plan_gate_static*.py`

## Assumptions / Open Questions
- Evidence plan.md lives in another worktree and is replaced on re-plan; the exact heading text is
  quoted above, which is enough for the test.

## Implementation Notes
`_HEADING_RE` in `tools/gate_checks/plan_gate_static.py` now accepts an optional qualifier introduced by punctuation after the title: `(`, `:`, `[`, `-`, en dash, em dash. The content-aware body check is unchanged (a body starting with "None" still counts as resolved). **Pinned decision:** a plain word after the title (`## Unresolved Questions Resolved Later`) is deliberately NOT matched; it reads as a different section, and the ticket's suggested `\b.*` would have swallowed it. **Planner prompt call (scope 3): not changed.** `.claude/agents/planner.md` and implement-ticket.js tell the planner to flag questions "under 'Unresolved Questions'" and do not prescribe the exact heading syntax, so the defect was the gate being stricter than the prompt; editing the prompt only to make the gate pass would be the wrong direction. No plan.md was edited.

## Test Summary
`tests/tools/test_plan_gate_static.py` (+9 cases, 23 total, all pass): the reported heading with real questions returns True; the same heading with a `None.` body returns False; five punctuation-qualified headings match; the plain-word suffix is pinned as not matched; the bare heading is unchanged. All 14 pre-existing tests pass unchanged.

## Files Changed
- `tools/gate_checks/plan_gate_static.py`, `tests/tools/test_plan_gate_static.py`; this ticket

## Completion Summary
Done. AC1: the suffixed heading from the reported plan returns True in a test using its exact text. AC2: all pre-existing plan_gate_static tests pass unchanged. AC3: the planner-prompt decision is recorded above.
