---
artifact_type: test_plan
ticket_id: TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION
date: 2026-09-07
---

# Test Plan — TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION

## Regression Surface (existing tests that must pass)

- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` — full file, especially
  `test_pending_information_response_fires_exactly_once_not_carried_forward` (must still pass
  unchanged — asserts `pending_information_responses`, not `information_source_profiles`).
- `tests/unit/engine/test_apply_generation*.py` (or wherever `ApplyPath.apply_generation()`'s own
  carry-forward behavior is unit-tested — locate via grep at Test phase) — must still pass; new
  assertion added for `information_source_profiles` persistence.
- `tests/unit/domains/information/` — router/phase unit tests, must be unaffected.

## New Tests Required (per AC)

- A direct multi-tick test (mirrors `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD`'s own
  reproduction shape) proving `state.information_source_profiles` is non-empty from tick 1 through at
  least tick 3, given a `WorldCompiler.compile()`-produced state carrying a real
  `information_source_profiles` entry.
- Real recalibration runs (not unit tests, but required evidence per AC):
  1. `tools/calibrate_simq.py --name urban_political ...`, `--name unit_information_source ...`,
     `--name unit_information_density ...` — confirm no pillar-score regression vs. pre-fix baseline.
  2. `tools/calibrate_simq.py --name unit_information_routing_pilot --seed 42 --ticks 200` — confirm
     `route_new_query`/Branch 3 now fires and INFORMATION pillar moves off `grade=C events=0`.

## Scoped Pytest Commands

```
pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py tests/unit/engine/ tests/unit/domains/information/ -m "not slow"
```
(Exact directories confirmed/refined at Test phase via `test-scoper`'s own Test Directory Map
mapping for `src/engine/apply.py` and `src/core/state.py`.)

## Anti-Drift Test Guards

- The multi-tick reproduction test must NOT assert anything about `pending_information_responses` —
  that stays out of scope and continues to be verified by the existing INFRA-257-backed test.
- Recalibration commands must not modify `unit_information_routing_pilot`'s own world/profile
  content — read-only verification runs.
