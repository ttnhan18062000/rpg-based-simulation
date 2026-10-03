---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-BELIEF-ASSIMILATED-TESTS-BYPASS-SHADOW-SHAPERS
phase: done
date: 2026-08-17
tags: [information, observability, bug]
---

# TCK-20260817-HOTFIX-BELIEF-ASSIMILATED-TESTS-BYPASS-SHADOW-SHAPERS

## Title
Fix 2 belief-assimilation integration tests calling `EventExtractor.extract()` directly, bypassing
the now-default push-shaper delivery path

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Real CI failures on the "Integration" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496):
`tests/integration/scenarios/test_phase5_information_belief_scenarios.py::test_compiled_urban_political_state_fires_belief_assimilated`
and `::test_pending_information_response_fires_exactly_once_not_carried_forward` both failed —
0 `belief_assimilated` events found where 1 was expected.

Root cause (confirmed via investigation): commit `29d78798` squashed in the "push-based
observability migration epic," which flipped `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` to default `ON`
(`src/domains/optimization/feature_flags.py`) and moved `belief_assimilated`/`belief_updated`
construction out of `EventExtractor.extract()`'s inline code (now an explicit, flag-gated rollback
path) into `StrategyShaper.shape()` (`src/observability/event_shapers.py`). Production delivery
requires both `EventExtractor.extract()` **and** `run_shadow_shapers()` (exactly what
`Kernel._phase_observability()` does). Both tests called `EventExtractor.extract()` directly,
bypassing `run_shadow_shapers()`/`StrategyShaper` entirely — a stale test harness, not a
production bug. `InformationBeliefPhase.apply()` itself was independently confirmed to produce the
correct `EntityUpdate`/`KnowledgeFact`.

## Scope
- Both tests in `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`: after
  calling `EventExtractor.extract()`, also call `run_shadow_shapers(prior_state, update, tick,
  mode)` and merge its events into the same list — mirroring exactly how
  `Kernel._phase_observability()` assembles the real event list.

## Out of Scope
- Any other ticket in this batch, including the 3rd Integration-job failure in the same
  investigation (`test_hunger_satiation_resolves_in_food_world` — a genuine, pre-existing strategic-
  cognition bug, own standard-tier ticket) and the stale world-profile fixture (own hotfix ticket).
- Any change to `EventExtractor`, `StrategyShaper`, or the push-shaper architecture itself — all
  confirmed correct and working as intended.

## Acceptance Criteria
- [ ] Both tests pass.
- [ ] `InformationBeliefPhase`/production event-shaping code is unchanged.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`

## Implementation Notes
Added `from src.observability.event_shapers import run_shadow_shapers` and, in both tests, extended
the `events` list with `run_shadow_shapers(state, refined, state.tick, ObservabilityMode.NORMAL)`
immediately after the existing `EventExtractor.extract()` call — exactly matching the two-source
merge `Kernel._phase_observability()` performs in production.

## Test Summary
- `pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py -q`: 8 passed.

## Files Changed
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` — both tests now merge
  `run_shadow_shapers()` output, matching real production event assembly.

## Completion Summary
Fixed a stale test harness: both tests called only half of the real production event-assembly path
after a later, unrelated commit moved belief-event construction into the push-shaper system by
default. No production code change — `InformationBeliefPhase` and the push-shaper architecture were
both already correct.
