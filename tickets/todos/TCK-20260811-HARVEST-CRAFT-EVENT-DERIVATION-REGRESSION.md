---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION
phase: open
date: 2026-08-11
tags: [economy, adventure]
---

# TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION

## Title
`resource_harvested`/`item_crafted` event derivation regressed — the exact behavior
`TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` closed with a passing, non-mocked
integration test now fails

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while running the full combat/strategy/adventure test suite as part of a broader session
health check (not originally targeted). `tests/integration/domains/adventure/test_harvest_to_event.py`'s
2 tests both fail:

- `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`
- `test_crafting_project_produces_item_crafted_event_through_full_pipeline`

Both fail with `AssertionError: Expected a real resource_harvested event, got: set()` (and the
crafting equivalent for `item_crafted`) — the full pipeline (`ActionIntentAdapter.execute()` →
`InteractionSystem.enforce()` → `ResourceTransactionSystem.resolve_all()` →
`EventExtractor.extract()`) produces zero matching events where it should produce one.

**Confirmed a real regression, not a stale/flaky test**, via direct bisection this session:
checked out the exact commit that created this test file
(`90794a76`, `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION: source, test, parity ledger,
and monitoring changes`) in an isolated `git worktree` and ran the test there — **both tests pass
cleanly at that commit** (2 passed). The test file itself has never been touched since
(`git log --oneline -- tests/integration/domains/adventure/test_harvest_to_event.py` shows exactly
one commit, the creating one) — so the regression is in one of the source files the test exercises
(`ActionIntentAdapter`, `InteractionSystem.enforce()`, `ResourceTransactionSystem.resolve_all()`,
or `EventExtractor.extract()`), introduced by a later commit that never re-ran or updated this
specific test.

This test was originally written specifically to prove `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-
TRANSITION`'s own fix (a real, non-mocked, end-to-end observation of a `resource_harvested`
`SimulationEvent`) — its own working_log entry states this explicitly. The regression means that
fix's guarantee no longer holds, silently, with no CI signal beyond this specific test file, which
is not part of any tier's fast/PR-blocking suite path exclusion list (confirmed: no `slow`/
`extra_slow` marker on either test) but also evidently not run in whatever check would have caught
this at the time it broke.

## Scope
- Bisect the real regression-introducing commit (a real `git bisect` between `90794a76` and current
  HEAD, not a guess) — likely candidates given the pipeline stages: any commit touching
  `ActionIntentAdapter.execute()`, `InteractionSystem.enforce()`,
  `ResourceTransactionSystem.resolve_all()`, or `EventExtractor.extract()`'s event-type mapping/
  translation table for `HARVEST_RESOURCE`/`REQUEST_CRAFT` intent kinds
- Fix the real root cause (not just re-mock the test to pass)
- Confirm both `test_harvest_to_event.py` tests pass post-fix
- Check whether this regression has any real corpus/SimQ blast radius (per
  `docs/simulation_quality/event_type_coverage.md`'s own "is the event wired to reach a scorer"
  question — if `resource_harvested`/`item_crafted` events have been silently zero corpus-wide
  since the regression, that's a SimQ-relevant finding requiring its own cross-check against
  `grade_anchors.json`, not assumed out of scope by default)

## Out of Scope
- Any change to `test_harvest_to_event.py` itself beyond what's needed to keep it passing post-fix
  — it is confirmed correctly written (passed cleanly at its own creation commit)
- Combat/strategy work from the parent session context (`TCK-20260810-COMBAT-BRAVERY-QUARTILE-
  ENGAGEMENT-INVERSION` and its own batch) — unrelated subsystem (economy/harvest, not combat/
  strategic-cognition), found only incidentally while running an adjacent test suite

## Acceptance Criteria
- [ ] Real regression-introducing commit identified via `git bisect` between `90794a76` and current
      HEAD, not assumed
- [ ] Root cause fixed in the actual pipeline stage responsible, not routed around
- [ ] Both `test_harvest_to_event.py` tests pass
- [ ] SimQ/corpus blast-radius question (see Scope) answered with direct evidence, not assumed

## Related Tickets
- TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION (DONE — the ticket whose own proof-test now
  fails)
- TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP (DONE — related economy-intent-generation work,
  same subsystem area)

## Related Docs
- docs/simulation_quality/event_type_coverage.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION/ (the original fix this
  ticket's own test proved, now regressed)

## Related Code Areas
- src/domains/adventure/ (ActionIntentAdapter)
- src/engine/ (InteractionSystem.enforce(), pipeline.py's interaction_enforcement phase)
- src/systems/ (ResourceTransactionSystem.resolve_all())
- src/observability/ (EventExtractor.extract())
- tests/integration/domains/adventure/test_harvest_to_event.py

## Assumptions / Open Questions
- Exact regression-introducing commit not yet identified — a real `git bisect` is required, not
  assumed from the pipeline-stage candidate list above
- Whether this has a real corpus/SimQ blast radius or is confined to this specific non-mocked test's
  own narrow construction — not yet checked, must be confirmed with direct evidence

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
