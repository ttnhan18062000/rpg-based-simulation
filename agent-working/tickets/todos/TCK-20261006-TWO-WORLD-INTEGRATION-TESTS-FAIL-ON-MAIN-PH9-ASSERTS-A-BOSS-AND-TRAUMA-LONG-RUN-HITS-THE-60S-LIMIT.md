---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261006-TWO-WORLD-INTEGRATION-TESTS-FAIL-ON-MAIN-PH9-ASSERTS-A-BOSS-AND-TRAUMA-LONG-RUN-HITS-THE-60S-LIMIT
phase: open
date: 2026-10-06
tags: [testing, world]
---

# TCK-20261006-TWO-WORLD-INTEGRATION-TESTS-FAIL-ON-MAIN-PH9-ASSERTS-A-BOSS-AND-TRAUMA-LONG-RUN-HITS-THE-60S-LIMIT

## Title
`test_long_run_simulation_ph9` and `test_long_run_stability` fail on `origin/main` (ph9 half stands; found by `rpg-implementer-2` while landing the spawn-faction batch)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`test_long_run_simulation_ph9` fails identically on an untouched control worktree (`hazard-impl2` at `8647b612a`, main plus #357 and no spawn change) and on the spawn-faction branch, so neither is caused by that batch.
- `tests/integration/world/test_living_world_ph9.py::test_long_run_simulation_ph9` fails at line 105, `assert boss_spawn_tick > 0` ("Boss should have spawned during 1000 ticks", `-1`). Hypothesis (planner, not yet verified): the test predates #356. World-boss branches are inert behind the default-OFF `ENABLE_WORLD_BOSS_SPAWN` flag, and line 106 (`trauma_score > 0`) is probably also false now that regional trauma counts only violent deaths (ENV-07). Either the test must turn the flag on and drive a violent-death trauma source, or its premise is retired by owner decisions 10, 14 and 15.
- **Withdrawn half (2026-10-06):** `test_long_run_stability` failed with `TimeoutError: ... resource time limit` (about 60 s) only because it was run with the default medium budget. Since #360 `extra_slow` gets the large budget; re-run on the spawn-faction branch with `--resource-budget large` it **passes** (1 passed in 434 s). Not a defect, dropped from this ticket. (The ticket's file name still says 60S for traceability.)

## Scope
1. Re-run each alone on `origin/main`; record the outcome and error.
2. ph9: decide, with the designer, whether the premise (a boss spawns within 1,000 ticks) is retired or the test should enable the flag and a violent trauma source. Do not weaken an assertion to pass.

## Out of Scope
Re-enabling bosses; changing ENV-07 or the flag default.

## Acceptance Criteria
- [ ] Each failure explained with a control run.
- [ ] ph9 fixed or retired with an owner/designer-backed reason.

## Related Tickets
- `TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING` (#356)
- `TCK-20261005-SPAWN-MONSTER-STRIPS-CATALOG-FACTION-FROM-EVERY-RUNTIME-SPAWNED-MONSTER` (where it was found)

## Related Code Areas
`tests/integration/world/test_living_world_ph9.py:105`, `tests/integration/world/test_long_run_stability.py`, `src/world/boss.py`.

## Assumptions / Open Questions
Lane B for ph9 (world); testing lane for the budget question. Hypotheses above are unverified.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
