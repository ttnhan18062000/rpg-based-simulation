---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED
phase: done
date: 2026-10-07
tags: [combat, bug]
---

# TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED

## Title
A walk to a building never arrives: the sidestep ladder oscillates beside its unenterable tile, so the tactical pass rarely sees the entity within reach and REST and EAT are almost never dispatched

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found tracing why `REST` was decided only twice in 700 ticks beside the inn (`TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`, break 3). A walk to a building targets the building's own tile, which cannot be entered (a blocked tile gives `path_not_found`, a building footprint gives `building_obstruction`). Beside it, `MovementSystem.resolve_move` ran its orthogonal sidestep rung, moving the entity perpendicular (to distance 2); the planner's next step moved it back; so it alternated between distance 1 and 2 every tick, never settling. The tactical pass dispatches the building's service only at `dist <= 1.0` on a brain tick (every 10 ticks), and the brain ticks in the observed window all landed at distance 2. Not the yield push and not occupancy contention (the verdict is a static reject, not an occupancy one). Planner ruling 2026-10-07: implement "settle at adjacency and decide on arrival", consistent with #385's completion guard.

## Scope
- In `MovementSystem.resolve_move` (`src/engine/movement.py`): an orthogonally adjacent entity whose step onto the walk's own destination tile is rejected as `path_not_found` or `building_obstruction` has arrived: no sidestep, no wait or replan counters, the walk ends (`navigation.target_clear`).
- Regression tests that fail on the old ladder; a constructed walker that reaches an inn and has `REST` dispatched; a before and after measurement on one tree; the other unenterable-target walks the change touches, with corpus counts.

## Out of Scope
- The scheduler (contested) and the yield push; neither is touched.
- The REST and SLEEP action semantics and the town path (`core_actions.py`, `town_resolution.py`): Lane B's biology ticket.
- Refreshing the current project's stored score, and whether a biological need may outrank a flat-80 goal.

## Acceptance Criteria
- [x] Arrival only when the rejected step is the destination tile itself and the entity is orthogonally adjacent; an obstacle on the way, a diagonal neighbour or another entity on the destination is not an arrival
- [x] A regression test fails on the old ladder (it reproduces the `(39,31),(39,32)` jitter), and a constructed walker reaches an inn and `REST` is dispatched
- [x] The other unenterable-target walks touched are reported with corpus counts (24 worlds, 500 ticks: 438 inn and 406 town_hall arrivals, 0 resource nodes, 0 other blocked tiles)
- [x] Before and after on one tree: movement stats, REST and EAT dispatches, deaths by cause (divergence 2.78)

## Related Tickets
- TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100 (umbrella, open)
- TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START (the capacity gate this builds on)

## Related Docs
- `docs/guidelines/intentional_divergences.md` 2.78; `docs/combat/combat_movement_overhaul_spec.md` (Congestion Responses)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-WALK-TO-A-BUILDING-NEVER-ARRIVES-SO-REST-AND-EAT-ARE-NEVER-DISPATCHED/`

## Related Code Areas
- `src/engine/movement.py`, `src/engine/tactical.py` (the building dispatch, unchanged), `src/engine/legality.py` (`verify_occupancy`)

## Assumptions / Open Questions
- Arrival ends the walk (`target_clear`); the brain decides at its next tick (at most 10 ticks later). The scheduler was not changed, so a decision on the arrival tick itself is not guaranteed.
- Open for Lane B: in compiled worlds `state.building_tiles` is empty and the building footprints sit in `blocked_tiles`, so `town_resolution.py`'s REST and EAT (which look the building up through `building_tiles` and need the entity ON the tile) can never fire there.

## Implementation Notes
- `src/engine/movement.py`: `_UNENTERABLE_TILE_REASONS` and `MovementSystem._has_arrived_beside_unenterable_target`, checked right after the first legality verdict in `resolve_move`; on arrival it returns `NavigationUpdate(target_clear=True)` and nothing else.

## Test Summary
- New `tests/unit/movement/test_arrival_beside_unenterable_target.py` (7 tests). With the arrival check neutralised three fail, and the walker test shows the old jitter `[(39,31),(39,32),(39,31),(39,32),...]`. The 64 existing `tests/unit/movement` tests pass.
- Corpus before and after: see divergence 2.78. REST decisions in frontier_living_world 0 to 34; eat and sleep events 0 to 0 (unchanged); STARVATION 30 / 34 to 30 / 32.
- CI directory lists, run locally with `-m "not slow and not extra_slow"` on the final branch: unit-core 1839 passed, 1 skipped; unit-domain 1474 passed, 1 skipped; integration plus `tests/integrity` plus `tests/architecture` 1225 passed, 7 skipped, 1 xfailed (the known strict deliberate-attack xfail); unit-infra including `tests/unit/tools` 3330 passed, 1 skipped; `tests/integration/campaigns` (slow, outside those lists) 28 passed, 1 xfailed. Not run locally: the full Tools job's remaining files and the slow suites.
- Gates (scratch venv): code-health ratchet 0 new, 0 worse (the arrival check first raised `resolve_move`'s complexity from 106 to 108 and its length from 289 to 292, so the existing sidestep rung was extracted unchanged into `_find_sidestep`; a 1500-tick crowded_frontier run after the extraction is identical to the one before it on every metric); parity-ledger schema 0 rose, 0 new; mypy baseline nothing in `movement.py`. CI is the first real run.

## Files Changed
`src/engine/movement.py`; the new test; `docs/guidelines/intentional_divergences.md`, `docs/combat/combat_movement_overhaul_spec.md`, `docs/parity_ledger/combat_movement.yaml`; this ticket, its artifacts and `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`.

## Completion Summary
A walker beside an unenterable building tile now arrives and stops instead of oscillating, so the tactical pass sees it within reach (`REST` decisions 0 to 34 in frontier_living_world). Eating and sleeping are still 0: the rest and sleep action semantics and the town path are Lane B's, and the stored-score and priority questions are separate (`TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100`).
