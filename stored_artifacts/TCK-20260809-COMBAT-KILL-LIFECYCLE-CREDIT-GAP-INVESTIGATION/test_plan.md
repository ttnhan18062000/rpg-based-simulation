---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan: TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION

## New Tests
`tests/unit/observability/test_event_extractor_world.py`:
- `test_combat_kill_not_emitted_for_hazard_caused_death` — a death with `death_reason=None` and
  a preceding `HAZARD`-outcome `CombatUpdate` must not fire `combat_kill`. Confirmed via
  `git stash` bisection to genuinely fail against pre-fix code.
- `test_combat_kill_emitted_for_genuine_combat_death` — regression guard: a death with
  `death_reason=="COMBAT"` must still fire `combat_kill`.

## Regression Scope
`tests/unit/observability/`, `tests/simulation_quality/`, `tests/observability/` — full sweep,
since the changed branch is shared infrastructure (`event_extractor.py`'s fallback path) touched
by multiple domains' own tests (narrative hero-death tests specifically caught a real regression
during this ticket's own Test phase, corrected before Finalize).

## Real Corpus Verification
`tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 2000` and
`--name urban_political --seed 42 --ticks 2000`, before and after the fix, comparing COMBAT
pillar norm score and real `combat_kill` event count in the replayed JSONL.
