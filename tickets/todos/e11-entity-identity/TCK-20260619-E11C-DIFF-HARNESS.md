---
status: open
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260619-E11C-DIFF-HARNESS
phase: open
date: 2026-06-19
tags: [entity-differentiation, test-harness, behavioral-quality, integration, phase-1]
---

# TCK-20260619-E11C-DIFF-HARNESS

## Title
E11-C · Build 400-tick differentiation test harness

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
No test currently verifies that entities with different personality vectors make observably different behavioral choices. After this ticket, a 400-tick integration test asserts that top-bravery-quartile entities take `combat_engage` routes at ≥2× the rate of bottom-bravery-quartile entities.

## Scope
- Build `tests/integration/scenarios/test_entity_differentiation.py`
- Test `test_bravery_quartile_combat_rate_2x()`:
  1. Compile sandbox_world (requires HERO entities from E11A)
  2. Run 400 ticks
  3. Collect per-entity route-kind histogram from transaction trace or observability
  4. Sort entities by bravery trait
  5. Assert: top quartile combat_engage rate ≥ 2× bottom quartile combat_engage rate
- Test `test_no_identical_personality_vectors_at_spawn()`:
  1. Compile sandbox_world
  2. Assert all entities have distinct personality tuples at tick 0
- The harness must be tagged so it runs in CI (use appropriate pytest mark)

## Out of Scope
- Implementing the calibration (that's E11D)
- Changing scoring weights (harness only measures, does not calibrate)

## Acceptance Criteria
- `test_no_identical_personality_vectors_at_spawn` passes with current seeding (E11A prerequisite)
- `test_bravery_quartile_combat_rate_2x` may initially fail if calibration (E11D) is not done; mark with `@pytest.mark.xfail(strict=False)` until E11D is complete
- Harness runs in `pytest tests/integration/scenarios/` without errors

## Related Tickets
- TCK-20260619-E11-ENTITY-IDENTITY (parent epic)
- TCK-20260619-E11A-HERO-AUTHORING (prerequisite — needs world with HERO entities)
- TCK-20260619-E11B-OBS-SNAPSHOT (prerequisite — needs personality in snapshot)
- TCK-20260619-E11D-SCORING-CAL (run after — calibration makes the 2× test pass)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` (personality→score relationship)
- `docs/engine/kernel.md` (tick loop for running N ticks)

## Related Code Areas
- `tests/integration/scenarios/`
- `src/core/state.py:PersonalityComponent`
- `src/domains/adventure/scoring.py` (route scoring with bravery)

## Assumptions / Open Questions
- How are per-entity route choices recorded? Check if transaction_trace or event records route-kind per entity per tick.
- How to run N ticks programmatically? Look at existing integration test patterns.

## Implementation Notes
Read existing integration tests in `tests/integration/` to understand how to run a world for N ticks. The route-kind histogram can be derived from the transaction_trace field on AuthoritativeState.

## Test Summary
`tests/integration/scenarios/test_entity_differentiation.py`:
- `test_no_identical_personality_vectors_at_spawn()` — strict pass
- `test_bravery_quartile_combat_rate_2x()` — xfail until E11D complete, then strict pass

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
