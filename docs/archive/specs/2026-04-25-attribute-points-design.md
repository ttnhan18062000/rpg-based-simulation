---
status: archive
authority: P2
audience: historical
layer: core
original_date: 2026-04-25
---

# Design Spec — PH8 M5: Attribute Points and Manual Growth

## Status
APPROVED

## Goal
Implement a system where leveling up grants "Attribute Points" (AP) that can be distributed into STR, AGI, VIT, etc., to boost base attributes. This follows the Hybrid Growth model where Heroes use manual growth and Monsters use auto-scaling.

## Requirements
- **AP Accumulation**: Grant 5 AP per level up for Heroes.
- **AP Distribution**: Implement `AllocateAttributeAction` to spend AP.
- **Component Update**: Add `AttributeComponent` to `EntityState` and `unspent_ap` to `IdentityComponent`.
- **Stat Recalculation**: Derived stats (CombatComponent) must update deterministically when attributes change.
- **Parity Alignment**: Follow `PROG-015` (Aptitudes), `PROG-046` (Caps), and `PROG-051` (Recalculation).

## Proposed Architecture

### 1. Data Model (`src/core/state.py`)
- **`AttributeComponent`**:
    - `strength`, `agility`, `vitality`, `endurance`, `intelligence`, `spirit`, `wisdom`, `perception`, `charisma` (all `int`, default 5).
- **`IdentityComponent`**:
    - `unspent_ap: int = 0`.
- **`EntityState`**:
    - Add `attributes: AttributeComponent`.

### 2. Stat Recalculation (`src/progression/leveling.py`)
Centralize formulas:
- `max_hp = base_hp + (vitality * 2) + (endurance * 0.5)`
- `atk = base_atk + (strength * 0.5)`
- `def_stat = base_def + (vitality * 0.3)`
- `evasion = base_evasion + (agility * 0.001)`

### 3. Leveling Logic
- Monsters: Maintain 1.1x multiplier scaling.
- Heroes: Skip multiplier, add +5 to `unspent_ap`.

### 4. Attribute Allocation Action (`src/actions/attributes.py`)
- **Action**: `AllocateAttributeAction(entity_id, attribute_name)`
- **Validation**: `unspent_ap > 0`.
- **Update**: 
    - `unspent_ap -= 1`
    - `attributes[name] += 1 * aptitude[name]` (PROG-015)
- **Side Effect**: Refresh `CombatComponent`.

## Verification Plan
- **Unit Test**: `tests/progression/test_attribute_growth.py`
    - Verify AP grant on level up.
    - Verify allocation consumes AP and increases attribute.
    - Verify combat stats recalculate correctly.
    - Verify hard cap of 100.
    - Verify aptitude multiplier (PROG-015).
