---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION
artifact_type: investigation
tags: [simulation-quality, testing, architecture]
---

# Investigation — TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION

## What the mechanism actually is

Read directly, not from the atlas's own citation alone:

- **The gate**: `src/engine/legality.py:143`, `LegalityServiceV2.verify_readiness(entity)` —
  `entity.combat.readiness < 100.0` → `(False, ReasonCode.INSUFFICIENT_READINESS)`, else `(True,
  ReasonCode.LEGAL)`. Dispatched from `src/engine/domain/action_router.py:20-44`,
  `ActionRouter.execute_action`'s "0. Readiness Check", which runs ahead of every action EXCEPT
  `SLEEP`/`EAT`/`REST` (survival actions bypass it explicitly, line 33-35 — a real, deliberate
  exception, not a gap).
- **Readiness accrual**: `src/engine/apply.py:127-128` — `readiness` increments by
  `readiness_speed` each tick, capped at 100.0.
- **The pacing-by-build claim** (the atlas's own cited `partial` reason): `readiness_speed` should
  scale with agility so faster characters act more often; the atlas's citation (`entity-action#4`,
  `beyond-city` mapping unrelated) says it's flat 10.0 for everyone.

## Whether `partial` is still accurate — checked, not assumed

`TCK-20260831-READINESS-SPEED-FORMULA` (closed 2026-08-31, before this session's own Foundation
seed on 2026-09-15) added `readiness_speed = max(1.0, 10.0 + (agility - 5) * 1.0)`
(`src/progression/leveling.py:104`) and fixed a wiring bug so it survives into the live
`CombatComponent`. This raised a real question worth checking directly: is the atlas's "flat for
everyone" claim now stale, a fourth stale-badge instance matching Foundation's own two and T4's
`camp` finding?

Checked, not assumed:
1. `grep -rn "readiness_speed\|get_effective_stats\|recalculate_combat_stats" src/worldbuilding/`
   → **zero matches**. `WorldCompiler` never invokes the agility-derived formula.
2. The formula only runs via `src/engine/apply.py:593-635`'s `stats_dirty` path, gated on an
   attribute/equipment/skill/trait/breakthrough/class/evolution/wound-changing `EntityUpdate` —
   i.e., a LIVE simulation event, never at world-compile/spawn time.
3. Directly compiled `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` and confirmed
   both entities spawn with `readiness_speed == 10.0` (both have `agility == 5`, the formula's own
   reference point, so this alone doesn't distinguish "formula ran and produced 10.0" from
   "formula never ran, dataclass default is 10.0"). Read the formula's own math directly instead of
   guessing: `max(1.0, 10.0 + (agility-5)*1.0)` is agility-linear and would differ for any
   non-5-agility entity — but per point 1/2, no entity gets this formula applied before its first
   stat-dirtying event regardless of its agility.

**Conclusion**: `state: partial` remains accurate, for a more precise reason than the atlas's own
text: not "flat forever," but "flat at spawn/until first stat-recalculation event, then
individually varying." Not a stale badge — no registry `state` edit warranted. Not a new defect —
the formula's own closing ticket already independently found a related corpus-visibility gap
(combat structurally ceasing before tick 1000 in every tested world) and recorded it honestly
rather than overclaiming; this investigation's own finding is consistent with, not contradicting,
that record. Not re-litigated as broken here, per this ticket's own explicit "verification, not
repair" scope.

## What would distinguish working from not working

The gate (the load-bearing half all 23 transitive dependents actually need) is falsifiable with a
clean differential: stage an otherwise-legal action with readiness below 100.0 (must be withheld)
versus at/above 100.0 (must proceed), on the same forced dispatch, through the real
`Kernel.tick_once()` path. This is exactly the shape `docs/plans/mechanic_verification_scenarios_
proposal.md` §3.3 requires and the combat-judgement scenario already demonstrated is buildable
against the real compile path.

## Reused, not reinvented

`data/worlds/mechanic_scenario_combat_judgement_withdrawal/` (real, compiled, catalog-driven
`goblin_scout` vs `orc_warchief`) and `tests/mechanic_scenarios/test_combat_judgement_withdrawal.py`'s
own staging shape (`_compile_world`, forced `ENTITY_ACT`/`ATTACK` task, one-tick `Kernel` run,
`CombatActions.execute_attack` call counting). Confirmed by direct compile: both entities spawn
with `combat.readiness == 100.0` and no `last_combat_posture` recorded for this pairing — the
already-verified posture gate cannot interfere, so reusing this world isolates the readiness gate
cleanly without staging or neutralizing anything extra.
