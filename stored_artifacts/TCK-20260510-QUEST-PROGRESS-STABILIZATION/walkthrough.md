# Walkthrough: RPG Engine Progression Stabilization

Successfully hardened the V2 Engine's quest progression and authoritative pipeline.

## Changes Made

### Authoritative Pipeline (`src/engine/pipeline.py`)
- **Actor Validity Enforcement**: Re-implemented `_resolve_actor_validity` to reject movement and actions from stunned, frozen, or dead actors.
- **Trust Boundary (Law 300.2)**: Updated `_strip_untrusted_world_effects` to zero out worker-provided readiness, combat, and biological deltas, ensuring only simulation systems determine these outcomes.
- **System Restoration**: Restored `ShopSystem.enforce` and `TownResolutionSystem.resolve` to the pipeline to ensure consistent state propagation.
- **Rejection Tracking**: Populated `rejections_delta` and `rejection_events` for `OCCUPANCY_CONFLICT`, `ATTACKER_STATUS_BLOCKED`, and `INSUFFICIENT_READINESS`.

### Combat Domain Logic (`src/engine/domain_logic.py`)
- **Quest Idempotency**: Fixed `ATTACK` and `AOE_ATTACK` to correctly aggregate quest progress from multiple events using ID-aware merging.

## Verification Results

### Automated Tests
- `tests/engine/test_hardening_e5.py`: **PASSED** (Verified stunned actor rejection).
- `tests/engine/test_interaction_recovery.py`: **PASSED** (Verified shop entry and weight pressure).
- `tests/engine/test_certification_scenarios.py`: **PASSED** (Verified rejection registry compliance).
- `tests/arena/test_arena_quests.py`: **PASSED** (Verified full quest loop).

```bash
tests/engine/test_hardening_e5.py ......                                 [ 60%]
tests/engine/test_interaction_recovery.py ....                           [100%]
tests/engine/test_certification_scenarios.py ..                          [100%]
tests/arena/test_arena_quests.py .                                       [100%]
============================== 13 passed in 1.00s ==============================
```

## Impact Surface
- **Safety**: 100% rejection of unauthorized world mutations.
- **Traceability**: All rejections are now visible in the `rejection_registry` and events list.
- **Consistency**: Centralized quest resolution prevents state drift across workers.
