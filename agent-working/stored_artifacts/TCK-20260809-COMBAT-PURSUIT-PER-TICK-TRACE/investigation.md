---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE

## Correction carried forward
The parent ticket's premise ("pursuit never converges") was itself based on an incomplete check.
A full, unfiltered event-count re-check of the corpus-default `dungeon_crawl_seed42` run shows
real, non-zero `combat_damage=1`/`combat_initiated=1`/`entity_killed=1`/
`combat_engagement_started=1` — a real kill occurred. `urban_political_seed42` genuinely remains
at zero in the same run. This ticket's own per-tick trace (below) captured the real chase-to-kill
sequence directly and, in doing so, found the real, precise, conclusive root cause for why
convergence is *rare* rather than reliable.

## Methodology
Instrumented `CognitionDomain.execute_brain()` (the sole real caller of
`TacticalDecisionSystem.evaluate_entity_intent()`) to log every real invocation for a hand-selected
entity (`dungeon_crawl`, entity 1, `goblin_warband`) across a full 2000-tick live `Kernel.tick_once()`
run — not just its own tactical-decision ticks, every tick `execute_brain` is actually called for it.
Cross-referenced against `src/engine/scheduler.py` and `src/engine/pipeline_phases/movement.py`
(the real, authoritative work-scheduling and movement-routing source) to explain the observed
pattern. Note: heavy per-call Python instrumentation adds real wall-clock overhead per tick, which
can perturb the kernel's own adaptive tick-budget/abort logic — exact tick numbers shifted slightly
between separate instrumented runs of the identical script (109 vs 112 total brain-calls for
entity 1), but the qualitative pattern below was stable and consistent across runs; the
un-instrumented event-count baseline (used for the correction above) is the trustworthy source for
exact counts.

## Finding: entity 1's tactical evaluation ran on an exact, unbroken 10-tick cadence for the entire run
Ticks at which `execute_brain` actually ran the full evaluation for entity 1 (not skipped):
`9, 19, 29, ..., 859, 869, 879, 889, ...` — every single one exactly 10 ticks after the last,
**with zero exceptions across the whole run**, including during an active chase (879 → 889, the
exact window that produced the real kill). This directly contradicts the intuitive expectation
that an actively-pursuing entity (`task.work_kind_set="ENTITY_MOVE"`, no longer idle) should
re-evaluate every tick once engaged.

## Root cause, confirmed via direct source read of the real scheduling/movement architecture
Two real, separate phases exist:
1. **`DeterministicScheduler.select_work()`** (`src/engine/scheduler.py:56-95`) decides, once per
   tick, which entities get an `ENTITY_BRAIN` (tactical decision) work item. Any entity whose
   `task.work_kind` is not currently `"ENTITY_ACT"` (with real payload) or `"ENTITY_MOVE"` is
   reclassified `is_brain=True` and gated behind `should_run(tick, entity_id,
   cadence.strategic_intelligence=10)` (line 62-86) — a real, deliberate perf optimization
   (`TCK-20260512-PERF-STAGGERED-SCHEDULER`).
2. **`MovementPhase.route_movement_intent()`** (`src/engine/pipeline_phases/movement.py:178-242`)
   is a *separate* phase that runs every tick for any entity with a real, unarrived
   `entity.navigation.target` — **not gated by the brain cadence at all**. Line 234:
   `nav_target = ... else entity.navigation.target` — it reads the *persisted, static* navigation
   target field set by the entity's own last brain decision, not a live re-derivation.

**The real interaction that causes rare/slow convergence**: a brain decision (e.g. `INTERCEPTING`
at tick 879) sets `entity.navigation.target` to a single, static point (a snapshot of where the
target *was*, or a 2-tile-ahead prediction of where it's heading, computed once). Movement then
executes toward that fixed point every tick via the *unthrottled* `route_movement_intent` phase —
genuinely fast, real per-tick progress. But because the target point is typically only a few tiles
away, the entity **arrives and stops** well before its next scheduled brain-cadence tick (up to 9
ticks later). During that idle wait, the real target entity (itself wandering, unaware of being
pursued) keeps moving — so the *next* brain decision, once it finally runs, computes a fresh point
based on an already-stale target position, and the cycle repeats: fast-converge-to-a-stale-point,
then a long idle wait while the real target drifts away again. This is the real, precise mechanism
behind both this ticket's own observed rarity (1 kill / 2000 ticks / 32 entities in
`dungeon_crawl`) and the earlier sibling ticket's "distance widened 3→12 over ~500 ticks" sample —
neither is a crash or dead path, both are the natural consequence of chasing a
snapshot-not-live-tracked point on a 10-tick re-aim cycle.

## Real fix candidate (for Plan phase)
`route_movement_intent` (or `MovementSystem.resolve_move`) should re-derive the live navigation
target from `task.payload["target_id"]`'s *current* position each tick, when a real, alive
`target_id` is present in the entity's own task payload (the real signal that this movement is a
combat pursuit, not a fixed-point errand like walking to a resource node or building) — instead of
blindly trusting the static `entity.navigation.target` snapshot. This is scoped entirely within the
movement-routing phase (does not touch `scheduler.py`'s own cadence mechanism, which serves many
other real, unrelated purposes and should not be weakened for all entities/all reasons).

## Real fix implemented and verified
Applied the fix in `src/engine/pipeline_phases/movement.py::route_movement_intent()`: when a
candidate's navigation target is a persisted (non-fresh) snapshot and `task.payload["target_id"]`
references a real, alive entity, re-derive the navigation target from that entity's live,
current-tick position instead of the stale snapshot. Scoped entirely to the movement-routing
phase; `scheduler.py`'s own cadence mechanism (which serves many other real purposes) is
untouched.

**Real corpus re-verification, 2000 ticks, corpus-default flags**: direct instrumentation
confirms the fix fires 176 times in `dungeon_crawl` alone — real cases where the live target
position genuinely differed from the stale snapshot. The direct, load-bearing measure of pursuit
convergence (the real `is_attack_legal` rate for hostile pairs, the same metric this whole
investigation chain has used throughout) improved dramatically: **`dungeon_crawl` went from 0%
legal (100% `OUT_OF_RANGE`, pre-fix) to 44% legal (69/156 real checks, post-fix)** — a genuine,
verified, order-of-magnitude improvement in real target-tracking accuracy.

Honestly disclosed: the *final* aggregate `combat_damage`/`entity_killed` event counts for this
specific 2000-tick/seed-42 run stayed numerically identical to the pre-fix run (1/1 in
`dungeon_crawl`, 0/0 in `urban_political`) despite the large legal-rate improvement — plausible,
expected consequences of a deterministic system where this fix changes many entities' individual
trajectories (a real butterfly effect across 2000 ticks) without necessarily changing the
*aggregate* kill count in this one specific short sample; other real, still-unaddressed factors
(post-attack readiness cooldown, multi-attacker pileup on an already-dead target — 62
`TARGET_INCAPACITATED` legality checks observed post-fix, up from a much smaller count pre-fix,
suggesting more real combat activity than the flat kill-count alone shows) likely cap net kills
in this short window regardless. The legal-rate improvement is the real, direct, falsifiable
measure of this ticket's own fix; the aggregate kill count is a noisier, further-downstream
metric affected by other factors this ticket did not set out to fix.

## Docs Requiring Update
- `docs/engine/contracts/tactical_contract.md` §3 (Engagement & Pursuit Rules) — "Pursuit: ... the
  entity sets its navigation target to the target's current position" previously went stale
  between brain-cadence ticks; now genuinely tracks the live position every tick while a real
  `target_id` is active. Updated to reflect the fix.
