---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-DECISION-TRACE-SELECTED-MOCK-SCORE
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-HOTFIX-DECISION-TRACE-SELECTED-MOCK-SCORE

## Title
`test_adventure_goal_scorer_wires_writer`'s `selected_mock` is missing a `.score` float,
crashing `min(float, MagicMock)` in real production code

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Part of a batch of 7 tickets fixing genuinely pre-existing CI failures. This one:
`tests/unit/observability/test_decision_trace.py::test_adventure_goal_scorer_wires_writer` fails
with `TypeError: '<' not supported between instances of 'MagicMock' and 'float'`.

Root cause (confirmed via investigation): `src/ai/goals/adventure_scorer.py:220-223` computes
`utility = min(_GOAL_UTILITY_SCORE_MAX, (raw_score / _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX) *
_GOAL_UTILITY_SCORE_MAX)` where `raw_score = selected.score`. The test's `selected_mock =
MagicMock()` (line 332-333) only sets `.family`, never `.score` — so `selected.score` auto-generates
an unconfigured child `MagicMock`. `MagicMock` supports `__truediv__`/`__mul__` (the division and
multiplication silently succeed, both producing another `MagicMock`), so the crash only surfaces one
step later at `min(float, MagicMock)`, which has no `<` support. Both the test and the production
`min(...)` line were added together in the same commit (`29d78798`, "Simulation quality (#20)",
2026-08-14) — this is a genuine test-authoring gap (the mock was never given the float production
code correctly assumes it always has for a real route object), not a production bug requiring
defensive handling for non-numeric input.

## Scope
- Add `selected_mock.score = 0.8` (matching `scored_route`'s own score, set immediately above at
  line 329) alongside the existing `selected_mock.family = RouteFamily.GATHER_RESOURCE` at
  `tests/unit/observability/test_decision_trace.py:333`.

## Out of Scope
- Any other of the 7 CI failures in this batch (each has its own ticket).
- Any change to `src/ai/goals/adventure_scorer.py`'s own `min(...)` utility computation — confirmed
  correct; production code legitimately assumes `selected.score` is always a real float, an
  invariant true for every real `AdventureRouteOption`.

## Acceptance Criteria
- [x] `selected_mock` has a real, numeric `.score` matching this test's own scenario.
- [x] `test_adventure_goal_scorer_wires_writer` passes.
- [x] No other test in the same file regresses.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/unit/observability/test_decision_trace.py`

## Implementation Notes
Added `selected_mock.score = 0.8`, matching `scored_route`'s own score set immediately above,
alongside the existing `selected_mock.family = RouteFamily.GATHER_RESOURCE`.

## Test Summary
- `pytest tests/unit/observability/test_decision_trace.py -q`: 28 passed (all tests in the file, no
  regressions).

## Files Changed
- `tests/unit/observability/test_decision_trace.py` — added `selected_mock.score = 0.8`.

## Completion Summary
Fixed the genuine test-authoring gap: `selected_mock` now has a real, numeric `.score`, matching
what every real `AdventureRouteOption` provides. Confirmed production code
(`src/ai/goals/adventure_scorer.py`'s `min(...)` utility computation) correctly assumes this
invariant and needed no defensive-handling change.
