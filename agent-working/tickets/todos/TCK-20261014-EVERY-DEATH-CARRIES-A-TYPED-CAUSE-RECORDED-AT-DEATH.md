---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-EVERY-DEATH-CARRIES-A-TYPED-CAUSE-RECORDED-AT-DEATH

## Title
Every death carries a typed cause, recorded at death in a durable field: a `DeathCause` enum, the last attacker, and the region hazard kind when the cause is a hazard. Hash-neutral.

## Status
OPEN

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
TBD

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
