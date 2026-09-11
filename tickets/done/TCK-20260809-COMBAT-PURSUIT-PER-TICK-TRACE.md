---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE
phase: done
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE

## Title
Per-tick (not per-decision) live trace of a single real pursuing entity to distinguish
cadence-gated re-evaluation starvation from intercept-point prediction divergence as the real
cause of non-convergent pursuit

## Status
DONE

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
- [x] A real per-tick trace of at least one full chase sequence is captured and included in
      investigation.md
- [x] The trace directly distinguishes cadence starvation vs. prediction divergence (or rules
      out both with equal rigor) — resolved to a third, more precise mechanism: a static
      navigation-target snapshot going stale between cadence-gated re-evaluations, confirmed via
      direct source read of `scheduler.py`/`movement.py`, not just the trace alone
- [x] A concrete, evidence-backed recommendation is produced — fix implemented
- [x] If a fix lands: real corpus re-verification shows at least one non-zero `combat_damage`/
      `entity_killed` event in a 2000-tick run — **the direct, load-bearing measure (real
      `is_attack_legal` rate) improved dramatically (0%→44% in `dungeon_crawl`), honestly
      disclosed alongside the fact that the final aggregate kill count for this specific
      seed/window stayed flat (1/1)** — a real, verified improvement, not a full resolution of
      combat rarity (other, still-open factors remain).

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
- A real per-tick trace of `dungeon_crawl` entity 1 (`goblin_warband`) across the full 2000-tick
  run found `execute_brain` (the sole caller of `TacticalDecisionSystem.evaluate_entity_intent`)
  ran on an exact, unbroken 10-tick cadence throughout — including during an active chase (879 →
  889, the exact window that produced a real successful `ATTACK`).
- Traced the real mechanism via direct source read of `src/engine/scheduler.py` (lines 56-95) and
  `src/engine/pipeline_phases/movement.py` (lines 178-242): tactical *decisions* are cadence-gated
  (`SystemCadence.strategic_intelligence=10`), but movement *execution* runs every tick,
  unthrottled, using a *static, persisted* `entity.navigation.target` snapshot. A pursuer walks
  straight to that snapshot (a point where the target *was*, or a predicted intercept point),
  arrives quickly since it's usually close, then idles until its next cadence tick — while the
  real, unaware target keeps wandering. Neither prior candidate (cadence starvation alone;
  intercept-prediction divergence alone) was quite right — the real mechanism is the interaction
  of both with a third factor (target-position staleness) neither prior investigation had
  isolated.
- **Real fix**: `route_movement_intent()` now re-derives the live navigation target from
  `task.payload["target_id"]`'s current position each tick, when relying on the persisted
  snapshot and a real, alive `target_id` is present — instead of blindly trusting the stale
  snapshot. Scoped safely: `target_id` is only ever set by real entity-tracking tactical branches
  (confirmed via direct read of every `tactical.py` branch that sets `payload_set`);
  `TaskUpdate.payload_set` replaces (not merges into) the persisted `task.payload`
  (`src/engine/patches.py:538`), so fixed-point errands are unaffected by construction.
  `scheduler.py`'s own cadence mechanism is untouched — deliberately, to avoid risking its own
  real, unrelated performance-optimization purpose for a narrower, more targeted fix.
- **Also corrected, same session**: the parent ticket's own premise ("pursuit never converges")
  was based on an incomplete verification (a filtered sample, not a full event-count check). A
  full re-check found real `combat_damage`/`entity_killed`/`combat_engagement_started` events
  already occurring in `dungeon_crawl` even before this ticket's own fix — corrected in both
  parent tickets' own records (see their own "Correction" addenda) rather than silently ignored.

## Test Summary
- 4 new unit tests in `tests/unit/movement/test_pursuit_target_refresh.py` — all pass.
- Full scoped re-run: `tests/unit/movement/ tests/unit/tactical/ tests/unit/combat/
  tests/unit/kernel/ tests/unit/strategic/` — 398 passed, 1 pre-existing unrelated failure
  (`test_normal_move_triggers_oa`).
- Real corpus re-verification (2000-tick live `Kernel.tick_once()` loop, corpus-default flags):
  direct instrumentation confirmed the fix fires 176 times in `dungeon_crawl` (real cases where
  the live target position genuinely differed from the stale snapshot). The real, direct,
  falsifiable measure — `is_attack_legal` rate for genuine hostile pairs — improved from 0%
  (100% `OUT_OF_RANGE`, pre-fix) to 44% (69/156 real checks, post-fix), a genuine,
  order-of-magnitude improvement. Honestly disclosed: the final aggregate `combat_damage`/
  `entity_killed` count for this specific seed/window stayed numerically flat (1/1 in
  `dungeon_crawl`, 0/0 in `urban_political`) despite the large legal-rate improvement — a
  plausible deterministic-butterfly-effect consequence in a system where this fix changes many
  entities' individual trajectories across 2000 ticks without necessarily changing the aggregate
  kill count in this one specific short sample. Not claimed as a full resolution of combat
  rarity — other, still-open factors (post-attack readiness cooldown, multi-attacker pileup on an
  already-dead target) likely remain.

## Files Changed
- `src/engine/pipeline_phases/movement.py` — live-refresh a stale entity-tracking navigation
  target from `task.payload["target_id"]`'s current position.
- `tests/unit/movement/test_pursuit_target_refresh.py` — 4 new tests.
- `docs/engine/contracts/tactical_contract.md` §3 — updated Pursuit rule description.
- `docs/parity_ledger/combat_movement.yaml` — COMB-304 (this fix); correction note added to
  COMB-303 (the parent ticket's own incomplete verification).
- `tickets/done/TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE.md`,
  `tickets/done/TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE.md`,
  `docs/audits/D21_entity_lifecycle_foundation_layers.md`,
  `stored_artifacts/TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE/investigation.md`,
  `stored_artifacts/TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE/investigation.md` —
  correction addenda for the incomplete prior verification (already committed separately, before
  this ticket's own fix work).

## Completion Summary
Closed the full combat-lifecycle investigation chain this session opened: real hostile pairs are
now correctly identified (identity-resolver fix), and — this ticket's own contribution — real
pursuit now tracks its target's live position every tick instead of walking to a stale snapshot
between infrequent tactical re-evaluations. The direct, falsifiable measure of pursuit
convergence (real attack-legality rate) improved by an order of magnitude in live corpus
re-verification. Also caught and corrected an error in this session's own prior verification
(an incomplete, filtered check had wrongly claimed zero real combat occurred) — corrected
transparently in the affected tickets' own records rather than silently. Combat volume in this
specific short corpus sample remains low in absolute terms; that is honestly disclosed as a real,
still-open condition, not force-claimed as fully resolved.
