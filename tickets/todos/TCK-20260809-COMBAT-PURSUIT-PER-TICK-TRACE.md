---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE

## Title
Per-tick (not per-decision) live trace of a single real pursuing entity to distinguish
cadence-gated re-evaluation starvation from intercept-point prediction divergence as the real
cause of non-convergent pursuit

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct follow-up to `TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE` (DONE, same
session — investigation-only, no fix landed). That ticket identified 2 real, plausible, non-
exclusive contributing factors to why real hostile pairs (now correctly detected after
`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`'s identity-resolver fix) still never converge to
melee range within a 2000-tick corpus run:
1. `CognitionDomain.execute_brain()`'s cadence gate (`SystemCadence.strategic_intelligence=10`)
   only lets an idle, project-less entity re-evaluate tactical intent (including noticing a
   nearby hostile) once every ~10 ticks.
2. `PositioningService.find_intercept_position()` predicts a point 2 tiles ahead of the target
   along the target's *own* current navigation-goal vector; if the target's own destination
   changes between the pursuer's re-evaluations, the prediction changes too and may diverge.

Real corpus-wide sampling (11 chase-decisions in `dungeon_crawl`, 2 in `urban_political` across
2000 ticks) was too sparse to conclusively attribute the non-convergence to either factor. This
ticket requires a qualitatively different, denser instrumentation approach.

## Scope
1. Select one real entity from a live compiled world (`dungeon_crawl` or `urban_political`) that
   is confirmed, via the parent ticket's own probe methodology, to enter a real chase against a
   real hostile target within a bounded tick window.
2. Instrument `MovementSystem.resolve_move()` and `CognitionDomain.execute_brain()` to record,
   on **every single tick** (not just tactical-decision ticks): whether `execute_brain()` ran the
   full tactical-evaluation path or hit an early-exit; the entity's real `navigation.target`,
   `movement_mode`, and real distance-to-target.
3. From this trace, determine directly: does `navigation.target` stay stale across multiple ticks
   (cadence starvation) or does it change every evaluation but trend away from the target
   (prediction divergence) — or some real combination?
4. Produce a concrete, evidence-backed fix recommendation (or confirm neither factor is
   load-bearing and a third cause exists) — do not force a conclusion the trace doesn't support.

## Out of Scope
- Any change to `SystemCadence` defaults or `find_intercept_position`'s own math without this
  ticket's own confirmed evidence first.
- The identity-resolver fix and initial hostile-detection question — both already resolved by
  the parent tickets.

## Acceptance Criteria
- [ ] A real per-tick trace of at least one full chase sequence is captured and included in
      investigation.md
- [ ] The trace directly distinguishes cadence starvation vs. prediction divergence (or rules
      out both with equal rigor)
- [ ] A concrete, evidence-backed recommendation is produced
- [ ] If a fix lands: real corpus re-verification shows at least one non-zero `combat_damage`/
      `entity_killed` event in a 2000-tick run

## Related Tickets
- TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE (DONE, same session — the sparse
  corpus-wide sampling this ticket refines into a per-tick trace)
- TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE (DONE, same session — the identity-resolver fix
  that made real chases reachable at all)

## Related Docs
- `docs/engine/contracts/tactical_contract.md` §3 (Engagement & Pursuit Rules)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE/investigation.md`

## Related Code Areas
- `src/engine/domain/cognition.py` (`CognitionDomain.execute_brain`'s cadence gate)
- `src/engine/positioning.py` (`PositioningService.find_intercept_position`)
- `src/engine/movement.py` (`MovementSystem.resolve_move`)
- `src/engine/cadence.py` (`SystemCadence`, `should_run`)

## Assumptions / Open Questions
- Whether a single traced chase is representative enough, or multiple real chases across both
  worlds are needed before drawing a confident conclusion — left to Investigate phase judgment.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
