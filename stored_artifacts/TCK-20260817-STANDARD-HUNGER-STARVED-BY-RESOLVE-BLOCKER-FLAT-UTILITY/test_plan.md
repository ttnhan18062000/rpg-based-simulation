---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY
tags: [cognition, bug]
---

# Test Plan — TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER-FLAT-UTILITY

## Normal flow
- `tests/integration/scenarios/test_hunger_satiation.py::test_hunger_satiation_resolves_in_food_world`
  — the original failing regression scenario — passes.

## New unit tests (edge cases, added this ticket)
- `tests/unit/strategic/test_strategic_detour_ph6.py::test_resolve_blocker_project_timeout_abandons_and_suppresses_blocker`:
  a `resolve_blocker` project 60 ticks past its `created_tick=0` (>= the 50-tick timeout) is
  abandoned via `evaluate_strategic_intent`, and the specific blocker its objective targeted gets
  `suppression_until_tick = current_tick + 100` — not just any blocker, not marked `resolved`
  (still a real, unaddressed blocker, just deprioritized).
- `tests/unit/strategic/test_strategic_detour_ph6.py::test_resolve_blocker_scorer_skips_suppressed_blocker`:
  `ResolveBlockerScorer.score()` returns `utility=0.0` while a blocker is suppressed, `utility=80.0`
  (regression-safety: confirms the existing, documented flat value is unchanged) both before
  suppression starts and after the suppression window elapses.

## Regression check
- Full strategic/goals/integration-scenario sweep
  (`tests/unit/strategic tests/unit/ai/goals tests/strategic tests/integration/scenarios
  tests/integration/pipeline/test_strategic_cadence.py -m "not slow and not extra_slow"`): no
  regressions — this touches shared strategic-update machinery
  (`evaluate_project_switch`/`StrategicUpdate.blockers_add_or_update`) exercised by many other
  goal kinds.

## Failure mode covered
- The "fix half the loop" failure mode this investigation specifically found and guards against: a
  bare timeout/abandon alone (without blocker suppression) would cause an infinite
  abandon-recreate cycle at the scorer's own flat utility, never actually letting hunger win. Both
  the timeout AND the suppression are covered by dedicated, separate assertions.

## Results
- `pytest tests/unit/strategic/test_strategic_detour_ph6.py -v`: 3 passed (1 existing + 2 new).
- `pytest tests/integration/scenarios/test_hunger_satiation.py -q`: 1 passed (was failing before).
- `pytest tests/unit/strategic tests/unit/ai/goals tests/strategic tests/integration/scenarios
  tests/integration/pipeline/test_strategic_cadence.py -m "not slow and not extra_slow" -q`: 440
  passed, 1 skipped, 24 deselected.
