---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION
artifact_type: investigation
tags: [engine, combat]
---

# Investigation: do BRACKETING moves go sticky, and what about the other entity-tracking modes?

Tree: branch `lane-a-sticky-family-2`, cut from `lane-a-sticky-attack-and-hostile-list` (`origin/main` `7a9f302db` + #347 + the router fix of
`TCK-20261005-SILENT-NO-OP-RETURNS-...`). Settings: real `Kernel.tick_once()`, seed 42, 2000 ticks, `audit_mode=True`,
`max_tick_budget_ms=1e9`, one simulation at a time. "value" = the identical run repeated and matched; "sample" = one run.
Probes: `probes/bracketing_lifetimes.py`, `probes/target_move_lifetimes.py`, `probes/measure.sh`; `forced_brain.py` from the attack-path ticket.

## 1. The 55% BRACKETING share was a forced-probe property, not real issuance
`forced_brain.py` (read-only `evaluate_entity_intent` on entities with a live hostile adjacent, sample, one run each): `crowded_frontier` 353
calls: BRACKETING 194, PANIC_RETREAT 141, ATTACK 15, plain move 3 (identical to the pre-router-fix split); `frontier_living_world` 438: ATTACK 397,
PANIC_RETREAT 31, plain move 10, BRACKETING 0; `urban_political` 144: PANIC_RETREAT 141, ATTACK 1, plain move 2; `dungeon_crawl` 12: ATTACK 12.
The split is world-specific, not stable. And the **real** `BRACKETING` `ENTITY_MOVE` issuance (value, 4 worlds x 2 runs): 0 in
`crowded_frontier`, `frontier_living_world`, `urban_political`; **1 in `dungeon_crawl`**. "Entities choose BRACKETING often" holds for a
forced decision on crowded_frontier only; the simulation almost never issues one.

## 2. The one real BRACKETING move is sticky (value)
`dungeon_crawl`, entity 12, target 3: issued t318, held to the end of the run (**1682 ticks**), `REPOSITION` mode, never stood on the
bracket tile, `evaluate_entity_intent` not re-entered once (0 calls while held), target dead at the last sighting. Per-tick trace
(`one_entity.py`): the navigation target is `bracket_pos` (0, 4) only on the issuing tick; from t319 it is the **hostile's current
position** (it moves every tick), so the entity circles the target at distance ~1-2 and never attacks.
Mechanism (read, then confirmed by the trace): `MovementCandidateSelector.resolve_live_tracking_target` (`candidate_selector.py:34`) returns
the live position of `payload["target_id"]` for **any** movement mode, and `bracket_pos` is a one-tick snapshot. So a BRACKETING move is
de facto an uncompleted pursuit of the target, not a move to the bracket tile. **Open-question answer: `bracket_pos` is a snapshot and is
overridden by live tracking toward the target after the first tick.**

## 3. The defect is wider than BRACKETING: entity-tracking moves outlive their dead target (value, 4 worlds x 2 runs matched)
`probes/target_move_lifetimes.py`, every `ENTITY_MOVE` carrying a `target_id`, by (mode / reason):
| mode / reason | moves | still running at end | outlived their target | held >20 ticks with a dead target |
|---|---|---|---|---|
| INTERCEPT / INTERCEPTING | 6 (crowded 3, frontier 1, urban 1, dungeon 1) | 6 | 6 | **6** (1688 to 1997 ticks) |
| PURSUE | 13 (4, 6, 2, 1) | 2 | 2 | **2** (1876 and 1998 ticks); the other 11 ended in median 3 ticks |
| REPOSITION / BRACKETING | 1 | 1 | 1 | **1** (1682 ticks) |
| GUARD / CONTRACT_OBLIGATION_GUARD | 1 | 1 | 1 | 1 (1010 ticks) |
10 of 21 target-carrying move RECORDS persisted to the end of the run (see 3b: in all 10 the mover itself was dead or inactive at its last sighting, so most were corpses carrying a stale task, not live entities held in place). The existing pursuit completion
(`pursuit_reached_attack_range`, #347) requires a **live** target in reach, so a dead or gone target returns False and nothing ends the
move. INTERCEPT has no completion at all in the corpus: every INTERCEPT move in every world was still running at the end.
KITING: no instance in the corpus (0 moves), so it is checked and unobserved, not shown safe.

## 4. What this means for the ticket
- Outcome is (b), not (a): BRACKETING (and INTERCEPT, and PURSUE with a dead target) persist.
- The ticket's candidate fix, widening the `PURSUE`-only mode gate, **would not end any of the observed moves**: the BRACKETING instance has a
  dead target, and the PURSUE instances also have a dead target. The missing condition is "target dead / inactive / gone ends the move",
  for the combat-positioning modes. Widening the gate for the in-reach condition alone fixes nothing measured.
- Guarding (`GUARD`) also shows a 1010-tick hold with a dead target (leader dead). Per the planner's scoping, guarding and cover-seeking are
  left alone; reported, not fixed.
- Not measured: whether SEEK_COVER (`REPOSITION` with a ranged-threat `target_id`) is live-tracked toward the threat by the same helper (0
  instances in the corpus; by the code it would be).

## Proposed (not done): scope for the planner
Combat-positioning modes = {PURSUE, INTERCEPT, KITING, REPOSITION/BRACKETING}. (1) A target that is dead, inactive or gone ends the move for all
of them (the existing idle-task encoding, `pursuit_completion_update`), in both dispatchers (`executor.py`, `worker_logic.py`). (2) The in-reach
condition extends to INTERCEPT and BRACKETING, not KITING (which intends to hold range). Guarding and cover-seeking untouched. A BRACKETING move
that actually walks to `bracket_pos` rather than to the target is a separate defect (the live-tracking helper's mode blindness).

## 3b. Correction (same session): count LIVE movers only (value, 4 worlds x 2 runs per arm, every pair matched)
My first probe counted any entity that still carried the move, including corpses (a dead or inactive entity keeps its stale task and is never
scheduled again: the dispatch check showed the completion check and the LOD gate stop being called for entity 8 after it died at ~t322).
`probes/target_move_lifetimes.py` now records the mover's own status and counts only ticks where the mover is alive and active while the
target is gone (`live_mover_dead_target_ticks`); `probes/before_after.sh` runs a `legacy` arm (the pre-fix logic swapped in by the probe) and the fix.
**Legacy arm:** all 10 persisted-to-end moves had a dead mover at the last sighting. The harm is the live-mover time:
- `frontier_living_world`, entity 18, PURSUE of target 51 which died at **t4**: held by a live mover for **986 ticks** (the worst case).
- `crowded_frontier`, INTERCEPT entities 33 and 12 (target 26 died t972): 30 and 20 live ticks. GUARD entity 10: 16.
- `dungeon_crawl`, BRACKETING entity 12: not a dead-target hold. The mover circled a LIVE target at distance ~1 for the move's life and was
  eventually killed (corpse): a live-target, in-reach case, ended only by the in-reach extension (fixed arm: 5 ticks).
**Fixed arm:** no live-mover dead-target hold above 20 ticks anywhere; the INTERCEPT moves end in 6-27 ticks and the BRACKETING move in 5. The only
remaining persisted records are corpses and the GUARD move, which is untouched by design (the guard mover had 16 live ticks before it died).
So the defect is real but much smaller than the first count suggested: one 986-tick live hold, two ~20-30-tick live holds, one BRACKETING circle.
**PURSUE "must stay unchanged" check:** by construction a PURSUE move whose target stays alive takes the unchanged branch (unit-pinned:
out-of-reach keeps pursuing, in-reach ends). At corpus level the per-move comparison is not available because freeing a held entity changes the
trajectory afterwards (`frontier_living_world` PURSUE 6 -> 19 moves, median 3 -> 1; `crowded_frontier` 4 -> 3, median 6 -> 3; `urban_political`
identical at 2 moves, median 3; `dungeon_crawl` 1 move). These are population comparisons, not per-move identity.
