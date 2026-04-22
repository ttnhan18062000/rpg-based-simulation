# Walkthrough: Fix Test Regressions

Restored 100% test stability for the V2 engine.

## Changes Made

### Engine Logic
- **Legality Service**: Added missing `blocked_tiles` check to `verify_occupancy`. This ensures that terrain blocked via spatial sets is correctly enforced by the `MovementSystem`.
- **Movement System**: Fixed an `ImportError` where `CombatReactionSystem` was referenced instead of `CombatResolutionSystem`.
- **Apply Path**: Fixed a critical **double-damage bug**. The logic was subtracting both `hp_delta` and `damage_taken` from the HP, effectively doubling any damage received (e.g., OAs). It now correctly uses only `hp_delta`.

### Test Alignment
- **Tactical Parity**: Aligned `test_tactical_parity.py` with the updated `TacticalDecisionSystem` API (`evaluate_entity_intent`). Updated argument order and added hostiles to the test state to ensure valid intent generation.

## Verification Results

### Automated Tests
- `pytest tests_v2/`
- **Result**: 375 passed, 0 failed.

```bash
============================= 375 passed in 7.56s ==============================
```

## Proof of Work
- Verified OA damage parity: Damage calculation (12.9 -> 12) is now correctly applied once, resulting in 88 HP (100 - 12).
- Verified blocked terrain: V2 now correctly blocks movement on coordinates specified in `blocked_tiles`.
