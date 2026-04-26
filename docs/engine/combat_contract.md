# Authoritative Combat Contract (Phase 8)

This document defines the explicit legality and outcome rules for combat interactions in the `src` engine.

## 1. Combat Legality Rules

A combat interaction is considered **LEGAL** if and only if all following conditions are met:

| Rule | Condition | Failure Reason |
| :--- | :--- | :--- |
| **State Validity** | Attacker and Target must be `active` and `alive`. | `ATTACKER_INCAPACITATED` / `TARGET_INCAPACITATED` |
| **Identity** | Attacker ID must not equal Target ID. | `SELF_ATTACK_ILLEGAL` |
| **Faction** | Attacker and Target must belong to different factions. | `FRIENDLY_FIRE_ILLEGAL` |
| **Range** | Manhattan distance must be <= `attacker.combat.range`. | `OUT_OF_RANGE` |

## 2. Combat Resolution Formula

The engine uses the **Pillar 3: Fractional Armor Mitigation** model for all direct combat.

- **Formula**: `damage = atk * (atk / (atk + def * 2.0 + 1.0))`
- **Minimum Damage**: 1 (Unless special immunity applies).
- **Determinism**: All calculations use `float` precision and are truncated to `int` at the final step.

## 3. Outcome Classification

Combat results are emitted as `CombatUpdate` objects with specific semantic kinds:

| Kind | Trigger Condition | Side Effects |
| :--- | :--- | :--- |
| **SURVIVE** | Target HP > 0 after damage. | HP reduction applied. |
| **DEFEAT** | Target HP <= 0 AND `is_lethal=False`. | `active=False`, `alive=False`. Non-permanent. |
| **KILL** | Target HP <= 0 AND `is_lethal=True`. | `active=False`, `alive=False`. Permanent removal. |

## 4. Opportunity Attacks (OA)

- **Legality**: Triggered by adjacent movement in an engaged state (See `LegalityServiceV2.get_engaged_hostiles`).
- **Semantics**: OAs are by default **Non-Lethal** (`DEFEAT` outcome).
- **Formula**: Same as standard attack.

## 5. Known Divergences / Exclusions
- **Evasion**: Currently assume 100% hit rate in the contract baseline (RNG integration pending Milestone 3/4).
- **LoS**: Line-of-sight obstructions are not yet enforced in the legality service.
- **Critical Hits**: Not yet implemented.
