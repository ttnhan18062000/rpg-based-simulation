---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE

## Context
Direct follow-up to `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION` (same
session), whose own §2.36 divergence entry explicitly disclosed and deferred this exact gap:
"movement and attack draw from the same readiness pool... closing that gap further is a broader
combat-pacing question." The user's own follow-up request ("focus into a complete combat
component") made this the natural next real target.

## Root cause: movement double-costs readiness AND stamina for the same fatigue concern
`search_docs` for "stamina cost movement attack readiness resource separation" surfaced
`docs/combat/combat_movement_overhaul_spec.md` §5 "Fatigue and Consequences" (real, documents
Stamina Pressure/Exhaustion as the intended movement-fatigue mechanic) and
`docs/core/attributes_and_classes.md` §4 "Stamina System" (a per-action stamina cost table).
Direct source read of `src/engine/movement.py`'s real `MovementSystem.resolve_move()` (line
243-245, `VERIFIED v2: stamina_drain_movement`) confirmed movement **already** applies a real,
separate stamina cost (`StaminaComponent.MOVE_COST`), with its own separate regen
(`StaminaService.tick_regen()`). The SAME function, moments later (line 267-276,
`VERIFIED v2: environmental_move_cost` / `authoritative_move_cost`), ALSO applies a real
`readiness_delta = -(move_cost * terrain_cost)` for the identical move. The position-swap path
(`src/engine/pipeline_phases/movement.py:428`) has the identical double-cost pattern.

`docs/engine/contracts/minimal_kernel.md` §5 (already-verified real, active contract this whole
session's investigation chain has relied on) describes `readiness` purely as: "Entities are only
eligible to submit updates if `readiness >= 100.0`" — an attack-eligibility/cooldown gate, with no
mention of movement cost. `stamina` already, independently fills the "movement fatigue" role. This
is a genuine architectural double-cost, not two intentionally-separate mechanics.

## Real, direct verification
Removed the `readiness_delta` cost from both real application sites (kept the stamina cost
unchanged). Re-ran this session's own `is_attack_legal` probe methodology against the same live
compiled worlds used in the sibling ticket:

| World | Before (this ticket) | After |
|---|---|---|
| `dungeon_crawl` (600 ticks) | 1.3% legal (2/159) | **28.5% legal** (53/186) |
| `urban_political` (600 ticks) | not separately measured, same-order-of-magnitude baseline | **36.6% legal** (90/246) |

`INSUFFICIENT_READINESS` no longer appears at all in either world's real reason-code breakdown
(previously the dominant reason at every tested `readiness_speed` value in the sibling ticket's
own parameter sweep). The remaining illegal reasons are `OUT_OF_RANGE` (now dominant — expected,
since random per-20-tick sampling naturally catches entities still mid-approach) and
`FRIENDLY_FIRE_ILLEGAL`.

## What was deliberately left untouched
`LegalityServiceV2.verify_movement_legality()`'s own separate readiness pre-check
(`readiness >= move_cost`, a much smaller bar than the attack path's 100.0) was left as-is. It
still provides a real, brief, correct movement lockout immediately after an attack resets
readiness to 0 (until passive regen restores enough to cover a single move's cost, typically 1-2
ticks) — a real, minor, sensible consequence of attacking, not disruptive, and out of this
ticket's own narrow scope (removing the double-cost, not redesigning the legality pre-check
layer).

## Docs Requiring Update
- `docs/mechanics/02_combat_laws.md` §7 (this session's own earlier addition) — corrected the
  now-false "Movement consumes a variable amount" claim.
- `docs/parity_ledger/combat_movement.yaml` — added COMB-300; updated COMB-298's own note to
  point to this ticket's resolution of its previously-deferred gap.
- `docs/guidelines/intentional_divergences.md` — added §2.38.
