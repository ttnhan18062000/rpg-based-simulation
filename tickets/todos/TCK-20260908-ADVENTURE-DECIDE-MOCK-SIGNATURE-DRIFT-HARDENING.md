---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260908-ADVENTURE-DECIDE-MOCK-SIGNATURE-DRIFT-HARDENING
phase: open
date: 2026-09-08
tags: [testing]
---

# TCK-20260908-ADVENTURE-DECIDE-MOCK-SIGNATURE-DRIFT-HARDENING

## Title
Harden hand-rolled AdventureDecisionService.decide() test mocks against future signature drift

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Follow-up from an independent review (`rpg-feature-planning`) of the Dormant Mechanism Closure
epic's PR #144. `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` added a new `belief_institutions`
kwarg to `AdventureDecisionService.decide()`; 4 of 5 test files with their own hand-rolled
`_fake_decide`/`_spy_decide` stub functions did not get updated to accept it, causing 7 real CI test
failures (fixed as `TCK-20260907-DORMANT-CLOSURE-CI-REGRESSION-FIXUP`) — a regression-scope gap the
implementing ticket's own Test phase didn't catch because it only ran the tests it already knew were
directly relevant, not a full-repo grep for the mocked symbol.

The reviewer's own suggested structural fix: replace the hand-rolled stub functions with
`unittest.mock.create_autospec(AdventureDecisionService.decide)`, which would catch this exact class
of signature drift at test-collection time (a `TypeError` on the mock construction itself) rather than
relying on someone remembering to grep before every future signature change.

## Scope
- Confirm during Investigate which of the 5 known `_fake_decide`/`_spy_decide` files
  (`tests/unit/strategic/test_adventure_route_materialization.py`,
  `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`,
  `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`,
  `tests/unit/observability/test_event_shapers_strategy.py`,
  `tests/unit/ai/goals/test_adventure_goal_scorer.py`) still use the fragile hand-rolled pattern.
- Replace each with `unittest.mock.create_autospec(AdventureDecisionService.decide, ...)` (or an
  equivalent structurally-checked mock), preserving each test's own real assertions and behavior —
  this is a mechanical hardening pass, not a test-behavior change.
- Prove the hardening actually works: add (or confirm) a regression test showing that reverting one of
  these mocks to a stale hand-rolled signature would now fail at mock-construction time, not silently
  produce a `TypeError` deep in application code.

## Out of Scope
- **Repo-wide audit of the other ~18 files using a similar `_fake_`/`_spy_`/`_stub_` naming pattern**
  (confirmed via `grep -rl "def _fake_\|def _spy_\|def _stub_" tests/` — 23 total hits, only 5 of which
  are the `AdventureDecisionService.decide()` mocks this ticket targets). Whether to extend this
  hardening repo-wide is a real, separate scope decision — not resolved or actioned here (see
  Assumptions/Open Questions).
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] All 5 `AdventureDecisionService.decide()` hand-rolled mock stubs replaced with a structurally-
      checked mock (`create_autospec` or equivalent).
- [ ] A real test demonstrates the hardening catches signature drift at construction time.
- [ ] No regression in the 5 touched test files' own existing assertions/behavior.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (`tickets/done/` — parent epic)
- `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING`, `TCK-20260907-DORMANT-CLOSURE-CI-REGRESSION-FIXUP`
  (`tickets/done/` — the ticket that added the new kwarg, and the hotfix that fixed the resulting
  CI regression)

## Related Docs
None.

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `tests/unit/strategic/test_adventure_route_materialization.py`
- `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`
- `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`
- `tests/unit/observability/test_event_shapers_strategy.py`
- `tests/unit/ai/goals/test_adventure_goal_scorer.py`
- `src/domains/adventure/service.py` (`AdventureDecisionService.decide()`)

## Assumptions / Open Questions
- **Real scope decision, not resolved here**: fix only the 5 files this specific regression touched
  (narrow), or use this ticket as the pilot for a broader repo-wide audit of all ~23 files using the
  same fragile hand-rolled `_fake_`/`_spy_`/`_stub_` mock pattern (broad — genuinely bigger scope,
  most of those 23 files likely mock entirely different functions with different risk profiles, not
  evaluated here). Default assumption unless told otherwise: narrow, since a broad audit was never
  requested and most of the 23 hits are unrelated to this specific regression class.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
