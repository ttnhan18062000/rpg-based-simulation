---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION
phase: done
date: 2026-08-11
tags: [economy, testing]
---

# TCK-20260811-HARVEST-CRAFT-EVENT-EXTRACTION-REGRESSION

## Title
Two `tests/integration/domains/adventure/test_harvest_to_event.py` tests fail on a clean tree,
unrelated to any known in-flight ticket

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
While running the scoped Test phase for `TCK-20260811-ADVENTURE-GOAL-SCORER` (part of the
`adventure-cognition-merge` epic), 2 tests failed:
- `tests/integration/domains/adventure/test_harvest_to_event.py::test_crafting_project_produces_item_crafted_event_through_full_pipeline`
- `tests/integration/domains/adventure/test_harvest_to_event.py::test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`

Both assert a specific event type (`item_crafted`, `resource_harvested`) appears in
`EventExtractor.extract()`'s output after running a project through the full pipeline. Both
currently fail with an empty/mismatched event-type set.

**Confirmed pre-existing, not caused by the adventure-cognition-merge epic's own work**: verified
independently twice this session — once by the epic's own implementer via `git stash` comparison
against the base branch, and once again independently by the epic's test-scoper agent (which
re-ran both tests on a freshly clean-stashed tree and got the identical failure). Neither
`ADVENTURE-GOAL-SCORER`'s changes (`src/core/strategic.py`, `src/ai/goals/adventure_scorer.py`,
`src/ai/goals/__init__.py`, `src/systems/strategic_systems/intelligence.py`) nor any other epic
ticket touches `event_extractor.py`, `tactical.py`'s harvest/craft dispatch, or
`service.py`/`generator.py`'s opportunity-to-event path.

## Scope
- Investigate why `EventExtractor.extract()` no longer surfaces `item_crafted`/`resource_harvested`
  events for these two full-pipeline scenarios
- Fix the root cause (likely in `src/observability/event_extractor.py` or the tactical
  craft/harvest dispatch path, but not yet confirmed — Investigate must determine this)
- Confirm both named tests pass again, and that no other event-extraction test regressed as a
  side effect

## Out of Scope
- Any change to the adventure-cognition-merge epic's own tickets (`ADVENTURE-GOAL-SCORER`,
  `THREAT-RESOLVED-ARBITER-RELOCATION`, etc.) — this regression is confirmed unrelated to that work
- Broader event-extraction test coverage beyond these 2 named failures, unless Investigate finds
  they share a root cause with other currently-passing tests that are only accidentally passing

## Acceptance Criteria
- [ ] Root cause of the `item_crafted`/`resource_harvested` extraction failure is identified with
      real evidence (not guessed)
- [ ] `test_crafting_project_produces_item_crafted_event_through_full_pipeline` passes
- [ ] `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline` passes
- [ ] No other test in `tests/integration/domains/adventure/` or
      `tests/unit/observability/test_event_extractor_narrative.py` regresses

## Related Tickets
- TCK-20260811-ADVENTURE-GOAL-SCORER (the ticket whose Test phase discovered this, unrelated to
  its own changes)
- TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION (canonical duplicate — see Completion
  Summary)

## Related Docs
None yet — Investigate should identify the relevant Mechanics Bible chapter or engine contract
once the root cause is known (likely `docs/mechanics/03_economic_laws.md` or an observability
contract).

## Related Stored Artifacts
None.

## Related Code Areas
- tests/integration/domains/adventure/test_harvest_to_event.py
- src/observability/event_extractor.py (suspected, unconfirmed)
- src/engine/tactical.py (suspected, unconfirmed — craft/harvest dispatch path)

## Assumptions / Open Questions
- Root cause is not yet known — this ticket only confirms the regression is real and unrelated to
  the epic that discovered it. Investigate must determine the actual mechanism.
- Given the failure mode (empty/mismatched event-type set, not a crash), this may be a recent,
  unrelated behavior change in event extraction or in how the full pipeline dispatches
  craft/harvest completion — Investigate should check recent commits touching
  `event_extractor.py`/`tactical.py` for a candidate cause before assuming it's a long-standing
  gap.

## Implementation Notes
None — this ticket was not separately implemented.

## Test Summary
None — see the canonical duplicate's own Test Summary once it closes.

## Files Changed
None.

## Completion Summary
Identified at Scope time (2026-08-12) as a duplicate of an independently-filed ticket,
`TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`, describing the exact same 2 failing
tests (`tests/integration/domains/adventure/test_harvest_to_event.py`) and the same root symptom
(empty event-type set from `EventExtractor.extract()`). That ticket's own investigation was
already further along (a real `git worktree` bisection scope against the test's creation commit
`90794a76`), so it was kept as canonical and this ticket's own findings (unrelated to
`ADVENTURE-GOAL-SCORER`'s changes, confirmed via `git stash` twice) were folded into it. No
separate implementation performed under this ticket ID -- the underlying regression is tracked
and will be fixed under `TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION`.
