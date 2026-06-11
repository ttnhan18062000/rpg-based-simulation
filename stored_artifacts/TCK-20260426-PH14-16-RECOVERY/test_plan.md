---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260426-PH14-16-RECOVERY
artifact_type: test_plan
tags: [ph14, recovery]
---

# Test Plan: RPG-Core Parity (Phases 14-16)

## Parity Tests (New)

### 1. `test_multi_attacker_opportunity_attacks`
- **Setup**: Hero surrounded by 3 hostiles.
- **Action**: Hero moves out of the center.
- **Verification**: `CombatUpdate` contains 3 intents; total `hp_delta` equals sum of all 3 OAs.

### 2. `test_social_bond_learning`
- **Setup**: Hero interacts with an entity.
- **Action**: Perform positive and then negative interactions.
- **Verification**: `SocialBond` records track `familiarity` and `sentiment` changes correctly. CHA modifier scaling verified.

### 3. `test_aoe_splash_damage`
- **Setup**: Attacker and 4 targets at various distances from impact.
- **Action**: Resolve AoE attack at `target1`.
- **Verification**: `target1` takes primary damage; neighbors within radius take splash damage; far targets take zero damage.

## Regression Tests
- Run `pytest tests/social`
- Run `pytest tests/combat`
- Run `pytest tests/parity`

## Acceptance Criteria
- 120/120 tests must pass.
- Bit-identical parity for all OA and AoE scenarios.
