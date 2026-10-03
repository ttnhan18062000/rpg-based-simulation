---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260430-PH5-COMBAT-LEGALITY-HARDENING
phase: done
date: 2026-04-30
tags: [ph5, combat, legality, hardening]
---

# TCK-20260430-PH5-COMBAT-LEGALITY-HARDENING

## Title
Hardening Combat Legality Matrix and AoE Authoritative Substrate

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Complete the integration of the authoritative V2 combat loop by finalizing the Combat Legality Matrix. Ensure all melee, ranged, and AoE interactions adhere to deterministic engine laws, validate legality contracts (LOS, range, readiness, friendly fire), and update the exhaustive logic ledger.

## Scope
- Fix pipeline omission: Ensure `SKILL` and `AOE_ATTACK` actions are routed through `_route_combat_intent` in `AuthoritativeApplyPipeline`.
- Harden AoE Splash logic: Implement Line-of-Sight (LoS) checks for splash damage to prevent "explosion through walls".
- Expand `test_combat_legality_matrix.py` with complex AoE scenarios (multi-target, splash obstruction).
- Verify friendly-fire rules for both direct and splash damage.
- Ensure dead attacker/target rejection is consistent across all combat types.

## Acceptance Criteria
- [x] `SKILL` actions work in the pipeline and are rejected if illegal (cooldown, stamina, range).
- [x] `AOE_ATTACK` actions work in the pipeline and correctly apply splash damage.
- [x] Splash damage does not penetrate solid walls (LoS requirement from impact point).
- [x] Multi-kill rewards (XP/Gold) are correctly attributed to the attacker in a single tick.
- [x] Friendly fire is applied according to engine laws (currently: splash hits allies, direct FF rejected).
- [x] All tests in `tests/rpg/test_combat_legality_matrix.py` pass, including new cases.

## Files Changed
- `src/engine/pipeline.py`
- `src/engine/combat.py`
- `src/engine/legality.py`
- `src/engine/apply.py`
- `tests/engine/test_phase5_combat_legality.py`

## Completion Summary
Phase E4.2 is complete. The Combat Legality Matrix is now fully authoritative and hardened. Melee, ranged, and AoE attacks are routed through a unified legality service. AoE splash respects Line-of-Sight constraints, and multi-entity rewards are handled atomically. Verified with exhaustive legality tests.
