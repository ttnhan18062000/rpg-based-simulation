---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH
phase: implement
date: 2026-10-14
tags: []
---

# TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH

## Title
Every death carries a typed cause, recorded at death in a durable field: a `DeathCause` enum, the last attacker, and the region hazard kind when the cause is a hazard. Hash-neutral.

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Found in the D75 attribution (rpg-implementer-3, 2026-10-14; frontier_living_world, seeds 42-46, 5000 ticks, base cefce1664 against D75 6bb940b8f, audit_mode). Of 134 people deaths (D75 on), 46 are hazard-dominant (the victim stood in a region with `hazard_kind` NATURAL_TERRAIN or UNDEAD_CORRUPTION and hazard damage was at least half of the hp lost in the last 50 ticks), 2 are starvation, 85 are killed by a hit. Only the 2 starvation deaths carry a typed cause (`lifecycle.passive_death_cause`). A hazard death has only a transient `outcome_kind == "HAZARD"` on the tick's combat update (`src/engine/world_dynamics.py:104-110`, which also writes `hp_delta` and `hazard_damage`), not a durable record at death. Combat deaths are reconstructed from the last attacker. One guard on a cave tile lost 2 hp that no update's `hp_delta` accounts for (residual); its writer is not identified.

The designer ruled (D75/D76) that the physics is intended, that avoiding a hazard region is a known gap, and that hazard is not folded into route weights. This ticket does not change behaviour; it records why an entity died.

## Scope
- A `DeathCause` enum (at least COMBAT, HAZARD, STARVATION, plus a catch-all that must stay at zero) and a durable typed record at death: cause, last attacker id (or None), the region hazard kind when the cause is HAZARD, the tick.
- Recorded at death by the authoritative apply path; read by observability, the R2 gate and the D77 pillars.
- Hash-neutral: an observability record outside the state fingerprint, proven under audit_mode (state hash identical before and after).
- Trace every hp loss to a typed source.

## Out of Scope
- Any behaviour change, hazard avoidance, route weights.

## Acceptance Criteria
- Every death in a run (all seeds of the standard measurement command) carries a typed cause; the catch-all count is 0.
- Every hp loss in a run has a typed source: combat hit, hazard drain, starvation or need drain (healing is separate). A residual test names the source.
- NAMED test case: the 2 hp residual on the guard on a cave tile (frontier_living_world, D75 on, found at death). Trace which code writes that hp loss (it is not in the update's `hp_delta`; the passive branch in `apply.py` with `starvation.hp_loss` is one candidate) and assert it carries a typed source.
- State hash identical before and after under audit_mode; code-health 0 new; lint-imports unchanged.

## Related Tickets
TCK-20261014-TERRAIN-COST-BECOMES-TIME-A-STEP-COSTING-N-TAKES-N-TIMES-AS-LONG-D75.

## Related Docs
docs/guidelines/intentional_divergences.md 2.126.

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/world_dynamics.py (hazard drain, lines 104-110); src/engine/apply.py (passive branch, starvation hp loss, death record); src/core/state.py (`LifecycleComponent.passive_death_cause`); src/engine/starvation.py.

## Assumptions / Open Questions
- Where the durable record lives (a lifecycle field, or an observability ledger outside the fingerprint) is for the implementer; it must not enter the state hash.
- Owner rpg-implementer-2 (feeds the standard measurement command), per rpg-planner.

## Implementation Notes
Finding: `death_reason` was already durable but a string, and the hp the D75 attribution could not place (the 2 hp on a cave guard) is the starving passive drain, taken inside the apply path's passive branch; no update carries it. In a 5000-tick frontier_living_world seed 42 probe every residual loss was at or above the starving line.

Shape (rpg-planner approved A + B):
- (B) durable: `DeathRecord(cause, tick, last_attacker_id, hazard_kind)` on `LifecycleComponent.death_record`, written only by `LifecycleSystem._death_record` through `LifecycleUpdate.death_record_set`, applied in `LifecyclePatch.apply`. `CombatComponent.last_attacker_id`, written by `CombatPatch.apply` on a damaging hit only. Both are in the canonical state.
- (A) observability: `src/observability/death_ledger.py` splits every hp loss into HIT / HAZARD / STARVATION / UNATTRIBUTED (expected 0), tallies deaths by cause, writes one row per death with the hp lost by source. Wired through `event_recorder` and the kernel hands it the starving line.
- No `last_attacker_tick`: the combat patch has no tick and no reader needs one. The record therefore names the most recent hit at any time before death; recency is not recorded (stated in Bible ch01, PROG-137, and pinned by a test).
- The two new canonical fields move every state digest. Behaviour-neutral by projection: `tests/helpers/death_field_projection.py` drops exactly the two fields; projected digests, alive/dead/cause counts and movement_count are identical to base 7888c5457 on frontier_living_world, urban_political, crowded_frontier (seed 42, 5000 ticks, audit_mode, PYTHONHASHSEED=0). Every dead body carries a record (36/36, 11/11, 33/33).
- Pinned expectations changed (approved by rpg-planner): FIXTURE_DIGEST_V2 631feb2b...->41b03d22..., FIXTURE_DIGEST_V1_ON_MAIN ec75b106...->13ed76f7... (two null keys), and the combat-field sentinel gains last_attacker_id.
- Code-health refactors kept behaviour: LifecycleUpdate.merge loops over its scalar set fields; EntityState.to_readonly copies the combat component with `replace` (status_effects stays uncarried, as before).

## Test Summary
tests/unit/progression/test_death_record.py (9), tests/unit/progression/test_death_record_projection.py (3), tests/unit/observability/test_death_ledger.py (11); core, progression, observability, engine, kernel, combat, lab, resource, kernel integration and certification sweep: 3061 passed before the pins, the 3 pinned failures fixed. Health 0 new / 0 worse; lint-imports 17 kept / 0 broken; mechanism pin test updated (scope 340->341, unbound 252->253).

## Files Changed
src/core/death_cause.py (new), src/core/state.py, src/core/updates.py, src/engine/patches.py, src/engine/kernel.py, src/systems/lifecycle_systems/lifecycle.py, src/observability/death_ledger.py (new), src/observability/event_recorder.py; tests above plus tests/helpers/death_field_projection.py; docs/mechanics/01_entity_anatomy.md, docs/parity_ledger/progression.yaml (PROG-137).

## Completion Summary
TBD
