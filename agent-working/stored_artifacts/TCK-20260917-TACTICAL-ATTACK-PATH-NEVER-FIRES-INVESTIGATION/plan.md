---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION
artifact_type: plan
tags: [strategy, combat, investigation]
---

# Plan — TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION

## Steps
1. Read the real code for all three call sites relevant to the four candidates before writing any
   instrumentation, per this ticket's own Acceptance Criteria #1 (measure, don't reason about the
   code alone — but reading first is what tells you *what* to measure).
2. Write one instrumented probe script that wraps, without modifying any `src/` file:
   - `TacticalDecisionSystem.evaluate_entity_intent` — call count per entity (candidate 1) and
     return-value inspection for an `ATTACK`/`SKILL` `TaskUpdate` (candidate 3, reframed).
   - `FactionSemanticsService.is_hostile_compat` (the singleton instance, via
     `get_faction_semantics_service()`) — whether any neighbor was found hostile per
     `evaluate_entity_intent` call (candidate 2).
   - `CombatActions.execute_attack` — real dispatch count (the other half of candidate 3's gap
     measurement).
   - Direct sampling of `entity.strategic.projects[...].objectives[...].kind` at two points per run
     (candidate 4) — no wrapping needed, this is plain state inspection.
3. **Force `LocalSequentialExecutor` explicitly on the `Kernel`**, not left to the profile's own
   `max_worker_count` (which defaults to concurrent execution for `PROD_SMALL`/`PROD_DEFAULT`).
   `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own 2026-09-17 addendum already found
   that `_phase_collection()`'s concurrent entity evaluation makes a shared-mutable-state probe
   (exactly what this investigation's own counters are) unreliable — avoiding that failure mode by
   construction rather than repeating it and finding out the hard way a second time.
4. Run all four worlds (`crowded_frontier`, `quest_dense_frontier`, `hero_guild_routing`,
   `metropolis`), each reported separately, never aggregated, per this ticket's own Acceptance
   Criteria #2. Corpus worlds at 2000 ticks (matching the rarity investigation's own convention);
   `metropolis` at a shorter tick count (matching the established "5 warmup + N sample" convention
   for its own 1000-entity cost) since it is the control, not a candidate-measurement target in
   itself.
5. Report per-candidate findings per world, stating exactly which call site was instrumented for
   each claim, per Acceptance Criteria #3 — the `heir_entity_id`/`heir_entity_id_set` miss (cited in
   this ticket's own Related history) is the standing example of why this matters.
6. If a positive control is needed to validate the probe's own correctness (e.g., confirming the
   wrapped `evaluate_entity_intent` genuinely intercepts the real call, not a stale reference),
   run it through the real `Kernel.tick_once()` loop, never a direct service call bypassing the
   pipeline — per Acceptance Criteria #4 and the standing lesson from
   `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS`'s own first, wrong-layer
   control.
7. Record the verdict against `tactical_decision` in `registries/mechanisms.yaml`'s own `verified`
   block, per Acceptance Criteria #5 — whatever the verdict turns out to be.

## Scope guards
- **Investigate and report only.** No `src/` file is modified by this ticket, per its own explicit
  Scope.
- Do not re-litigate the posture-veto gate's own correctness (confirmed working where it applies).
- Do not tune the XP threshold (`TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME`) —
  that ticket stays filed and stays after this one.

## Acceptance-criteria map
| AC | Satisfied by |
|---|---|
| 1. Each candidate confirmed/ruled out by measurement | Steps 2-4 |
| 2. Results reported per world | Step 4 |
| 3. Every "never happens" claim states which call site was instrumented | Step 5 |
| 4. Positive controls run through a real Kernel tick | Step 6 |
| 5. Verdict recorded against `tactical_decision` in the registry | Step 7 |
