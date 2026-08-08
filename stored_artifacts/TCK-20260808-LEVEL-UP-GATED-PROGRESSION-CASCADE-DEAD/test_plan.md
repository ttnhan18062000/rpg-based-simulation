---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD
artifact_type: test_plan
tags: [progression, combat, simulation-quality]
---

# Test Plan — TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD

## Final outcome
The chosen `xp_multiplier` fix was implemented and re-tested against real corpus data, found
insufficient, and reverted (no net `src/` change). This test_plan's own final verification claims
are all real, instrumented probes against the live `urban_political` world/kernel — not synthetic
or assumed — documented below alongside the earlier Investigate-phase claims.

## Normal flow (Investigate-phase claims, already verified)
- `LevelingService.get_xp_required(1) == 100` — direct read, confirmed.
- Real per-kill XP (10) and real corpus-wide kill rate (3-5 per 2000 ticks) — cited from
  `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`'s own real probes, not re-derived.
- `AllocateAttributeAction`/`execute_allocate_ap` both gated by `unspent_ap` — direct read,
  confirmed.
- `compute_elder_attribute_update` gated by `age_ticks >= 7000` and has zero real callers — direct
  read + grep, confirmed.
- `dungeon_crawl` 200-tick run produces 0 real PROGRESSION events today — real, live
  `calibrate_simq.py` run, confirmed.

## Final verification claims (real, instrumented probes, this ticket's own closing work)
- **4x/6x multiplier re-test**: real 2000-tick `urban_political` (seed 42) kernel run, tracking
  only `original_ids` captured before ticking (excludes mid-run-spawned bosses/elites). Result: max
  real XP among original entities was 60 at 6x — insufficient to cross the 100 XP level-2
  threshold. Zero original entities leveled up. Confirmed via direct `kernel.state.entities`
  inspection, not log-derived.
- **Hostile-density probe**: real per-tick check of `SimulationDomainLogic.get_neighbor_view(state,
  entity, radius=10.0)` for original-population entities — hostiles present in 50/50 (100%) sampled
  ticks. Rules out hostile scarcity.
- **Goal-competition probe**: real `GoalRegistry.get_all_scores(entity, state)` calls —
  `GoalKind.COMBAT_ENGAGE` wins the competition in 325/330 (98.5%) samples when available. Rules
  out goal-competition loss.
- **`is_attack_legal` probe (decisive)**: direct instrumentation of `tactical.py`'s own
  `LegalityServiceV2.verify_attack_legality(entity, h, state)` call — FALSE in 330/330 (100%) real
  samples, splitting into `ReasonCode.FRIENDLY_FIRE_ILLEGAL` (150, 45%) and
  `ReasonCode.INSUFFICIENT_READINESS` (180, 55%). This is the real, decisive root cause — documented
  in full in `investigation.md` and handed to the dedicated follow-up
  `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`.
- **Revert confirmed clean**: `git status --porcelain -- src/ | grep -v __pycache__` → empty.

## Edge cases / Failure modes / Regression-prone paths
- Not applicable to this ticket's own final scope — no `src/` change lands here. Edge
  cases/failure modes for the real fix belong to the follow-up tickets that inherit this
  investigation's findings.

## Scoped test commands
- None required for this ticket's own close (no code change). The reverted multiplier change
  needed no test re-run since it was never merged into a committed state.
