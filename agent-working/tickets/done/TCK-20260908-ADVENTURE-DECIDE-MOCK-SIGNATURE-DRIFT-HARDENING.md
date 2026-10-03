---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260908-ADVENTURE-DECIDE-MOCK-SIGNATURE-DRIFT-HARDENING
phase: done
date: 2026-09-08
tags: [testing]
---

# TCK-20260908-ADVENTURE-DECIDE-MOCK-SIGNATURE-DRIFT-HARDENING

## Title
Harden hand-rolled AdventureDecisionService.decide() test mocks against future signature drift

## Status
DONE

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
- **Reviewer note (`rpg-feature-planning`, 2026-09-08)**: before assuming zero behavior change, confirm
  `create_autospec` doesn't fight any of the 5 tests' own intentional edge cases — i.e. check none of
  them relies on a mock accepting an argument shape the real `decide()` signature wouldn't allow.
  Unlikely given these are all `decide()`-output stubs, but a quick check, not an assumption.

## Out of Scope
- **Repo-wide audit of the other ~18 files using a similar `_fake_`/`_spy_`/`_stub_` naming pattern**
  (confirmed via `grep -rl "def _fake_\|def _spy_\|def _stub_" tests/` — 23 total hits, only 5 of which
  are the `AdventureDecisionService.decide()` mocks this ticket targets). Whether to extend this
  hardening repo-wide is a real, separate scope decision — not resolved or actioned here (see
  Assumptions/Open Questions).
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [x] All 5 `AdventureDecisionService.decide()` hand-rolled mock stubs replaced with a structurally-
      checked mock (`create_autospec` or equivalent).
- [x] A real test demonstrates the hardening catches signature drift at construction time.
- [x] No regression in the 5 touched test files' own existing assertions/behavior.

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
- **Decided 2026-09-08 (real user decision)**: **narrow scope** — fix only the 5
  `AdventureDecisionService.decide()` mock files this specific regression touched. The broader
  ~23-file repo-wide audit is explicitly out of scope, not a future phase of this same ticket.

## Implementation Notes
Confirmed the real, current `AdventureDecisionService.decide()` signature
(`src/domains/adventure/service.py`) directly before starting: `(entity, candidates, tick=0,
resource_nodes=None, faction_directives=None, factions=None, culture_state=None, legend_fact=None,
belief_institutions=None, event_fidelity=None)`, a `@staticmethod`.

Replaced every hand-rolled `_fake_decide`/`_spy_decide` definition across the 5 known files with
`unittest.mock.create_autospec(AdventureDecisionService.decide, side_effect=<behavior>)`. Also
narrowed each `<behavior>` function's own signature from a full hand-typed positional/keyword list
to `(entity, candidates, **kwargs)` — this is the part that actually delivers forward-compatibility
(not just re-validating today's signature): a *future* new optional kwarg is now silently absorbed
by `**kwargs` and needs zero further test-file changes, while `create_autospec` still enforces the
real, current call shape (rejecting unknown kwargs, missing required args) at every mock invocation.
Spy-style tests that captured a specific kwarg's value (`culture_state`, `legend_fact`) switched
from a named parameter to `kwargs.get(...)`, preserving identical assertions.

`test_adventure_goal_scorer.py`'s single `_fake_decide_factory`/inline stubs were consolidated
through one new shared `_autospec_decide(behavior)` helper (that file had 6 separate call sites);
the other 4 files kept their existing one-factory-or-inline-per-file shape, each independently
wrapped, since consolidating a shared helper *across* files was not asked for and would have grown
scope beyond a mechanical hardening pass.

**Reviewer's note addressed**: checked all 5 files' own real assertions before and after — none of
them relied on a mock accepting an argument shape the real `decide()` signature wouldn't allow (all
were straightforward `entity, candidates` positional + a subset of the real keyword params); no
edge case fought `create_autospec`.

Added `test_autospec_decide_mock_rejects_unknown_kwarg_structurally()` to
`test_adventure_goal_scorer.py` as the required regression proof: constructs a bare
`create_autospec(AdventureDecisionService.decide)` and confirms it raises `TypeError` immediately
when called with an unknown kwarg, while the real, current kwargs are still accepted — directly
demonstrating the hardening property without needing an actual future signature change to occur.

## Test Summary
`pytest tests/unit/strategic/test_adventure_route_materialization.py
tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py
tests/unit/strategic/test_fused_strategic_pass_routing_family.py
tests/unit/observability/test_event_shapers_strategy.py
tests/unit/ai/goals/test_adventure_goal_scorer.py -q` → 60 passed (was 59 before this ticket's own
new test). Broader regression sweep:
`pytest tests/unit/ai/goals/ tests/unit/domains/adventure/ tests/unit/strategic/
tests/unit/observability/ -m "not slow"` → 1505 passed, 1 skipped, 0 failed.

## Files Changed
- `tests/unit/ai/goals/test_adventure_goal_scorer.py` (new `_autospec_decide` helper, 6 stub
  call sites converted, 1 new regression test)
- `tests/unit/strategic/test_adventure_route_materialization.py`
- `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`
- `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`
- `tests/unit/observability/test_event_shapers_strategy.py`

## Completion Summary
Replaced all 5 known hand-rolled `AdventureDecisionService.decide()` test mock stubs with
`create_autospec`-wrapped equivalents, narrowing each fake's own signature to `(entity, candidates,
**kwargs)` so a *future* new optional kwarg needs no further test-file changes while `create_autospec`
still structurally enforces the real, current call shape. Added a direct regression test proving the
hardening property. No behavior change to any of the 5 files' own existing assertions — confirmed via
a clean 60/60 pass plus a 1505-test broader regression sweep. Repo-wide audit of the other ~18
similarly-patterned mock files stayed explicitly out of scope, per the real user decision.
