---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261010-DEFEAT-CORPUS-TEST-WINDOW-DEPENDS-ON-PURSUIT-GEOMETRY
phase: done
date: 2026-10-10
tags: []
---

# TCK-20261010-DEFEAT-CORPUS-TEST-WINDOW-DEPENDS-ON-PURSUIT-GEOMETRY

## Title
The defeat corpus test's fixed 120-tick window depends on pursuit geometry; it runs until the first DEFEAT, bounded at 400 ticks.

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
`test_defeat_deaths_are_recorded_in_unscripted_corpus_play` (slow) went red on main when #474 merged. Bisected: the intercept change (a chaser aims at where a pursuing target is) moved scout 17's death in `frontier_marches` seed 42 from DEFEAT at tick 93 to COMBAT at tick 104; the first DEFEAT now lands at tick 120, one tick outside the 120-tick window. The DEFEAT path is intact (0 DEFEAT deaths at tick 120, 2 at 200, 8 at 400).

## Scope
The test runs until the first DEFEAT, bounded at 400 ticks; it still fails a run with none and still asserts every DEFEAT is a recorded death. Docstring and a measured note on divergence 2.104.

## Out of Scope
The intercept change itself; any other corpus test.

## Acceptance Criteria
The test passes on main, fails with a window too short to see a DEFEAT (checked at 100 ticks), and says why the window is no longer 120 ticks.

## Related Tickets
TCK-20261009-PURSUING-GUARDS-RUN-HUNDREDS-OF-TILES-OFF-THE-MAP-AND-STARVE; TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE.

## Related Docs
docs/guidelines/intentional_divergences.md Section 2.104.

## Related Stored Artifacts
None.

## Related Code Areas
tests/mechanic_scenarios/test_entity_death_authority_boundary.py

## Assumptions / Open Questions
None; approved by rpg-planner on condition that a run with zero defeats still fails.

## Implementation Notes
Bisected by reverting `src/engine/positioning.py` alone on 39f353b95.

## Test Summary
The test passes in 11.5 s (slow marker); with `CORPUS_DEFEAT_WINDOW = 100` it fails.

## Files Changed
tests/mechanic_scenarios/test_entity_death_authority_boundary.py, docs/guidelines/intentional_divergences.md.

## Completion Summary
Re-scoped with the reason recorded; no number loosened.
