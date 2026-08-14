---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY
artifact_type: test_plan
tags: [simulation-quality, faction]
---

# test_plan.md — TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY

## Regression Surface

- `tests/unit/observability/test_event_shapers_economy_faction.py` (existing `FactionShaper`
  suite — must still pass unmodified)
- `tests/simulation_quality/test_faction_scorer.py` (existing `FactionScorer` suite — must still
  pass unmodified)

## New Tests Required

- `FactionShaper`: `faction_trajectory_stagnant` fires after `_FACTION_STAGNANT_TICKS` ticks of
  diplomatic activity with zero territorial change for the same faction; does NOT fire if
  territory changed recently; does NOT fire for a faction with no diplomatic activity (stagnant
  but quiet, not the "active but fruitless" pattern this rule targets); does not fire twice for
  the same faction; a freshly-first-observed faction does not immediately appear stagnant.
- `FactionScorer`: `faction_trajectory_stagnant` scores its configured weight and tag, using an
  injected `ScoringWeights` fixture.
- `Kernel.__init__`: `FactionShaper.reset_run_state()` wired in alongside the other shapers.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/observability/test_event_shapers_economy_faction.py \
  tests/simulation_quality/test_faction_scorer.py -q
```

## Anti-Drift Test Guards

Same caution as the PROGRESSION sibling ticket: a passing unit-test suite alone would not catch a
wiring gap (e.g. `reset_run_state()` never called, leaking state across runs) — verify with a
real, non-mocked multi-hundred-tick kernel run showing the new event actually fires under
realistic conditions, not just isolated unit fixtures.
