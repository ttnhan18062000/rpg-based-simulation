# Test Plan: Phase 5 Combat Legality Hardening

## 1. Combat Legality Matrix Expansion
File: `tests/rpg/test_combat_legality_matrix.py`

### New Scenarios:
- **AoE Splash Obstruction**: 
    - Attacker targets an enemy. 
    - Another enemy is within splash radius but behind a "WALL".
    - Result: Only the primary target (and any non-obstructed splash targets) take damage.
- **Skill Pipeline Integration**:
    - Propose a `SKILL` action through the pipeline.
    - Verify it resolves, drains stamina, and triggers cooldown.
- **Multi-Kill AoE Rewards**:
    - Target a group of 3 weak monsters with an AoE.
    - Verify the attacker receives XP/Gold for all 3.
- **Skill Legality Rejection**:
    - Propose a `SKILL` that is on cooldown.
    - Result: Rejected by pipeline with `INSUFFICIENT_READINESS` or `SKILL_ON_COOLDOWN`.

## 2. Regression Testing
- Run existing `test_rpg_advancement.py` to ensure Phase 8 progression logic still works.
- Run existing `test_combat_legality_matrix.py` to ensure baseline melee/ranged rules are preserved.

## 3. Verification Commands
```bash
pytest tests/rpg/test_combat_legality_matrix.py -v
pytest tests/progression/test_rpg_advancement.py -v
```
