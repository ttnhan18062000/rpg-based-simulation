---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260501-STRAT-HARDENING
artifact_type: plan
tags: [strat, hardening]
---

# Strategic Cognition Hardening Plan

Implement the full strategic loop from environmental sensing to historical learning.

## Proposed Changes

### [Component] Routine & Concerns

#### [MODIFY] [routine.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/routine.py)
- Add `evaluate_environmental_concerns` to check for `INVENTORY_FULL` and `REWARD_PENDING`.
- Add `evaluate_safety_concerns` for `LOW_HP` and `THREAT_SALIENCE`.

### [Component] Strategic Inference

#### [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/strategic.py)
- Update `infer_blockers` to detect `INVENTORY_FULL` from transaction rejections.
- Implement `process_project_outcome` to record `TurningPointState` (Victories/Losses).
- Update `evaluate_strategic_intent` to handle `INVENTORY_FULL` detour triggers.

### [Component] Detour & Learning

#### [MODIFY] [detour.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/detour.py)
- Add detour logic for `material` (harvesting) -> `location` (known nodes).
- Add detour logic for `inventory` (full) -> `location` (town center/shop).
- Add detour logic for `safety` (low hp) -> `location` (safe zone/healer).

### [Component] Tactical Bias

#### [MODIFY] [tactical.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/tactical.py)
- Ensure tactical decisions respect the `SUSPENDED` state of projects correctly.
- Add bias for "regroup" or "town return" when concerns are high.

## Verification Plan

### Automated Tests
- `tests/engine/test_strategic_lifecycle.py`: New test suite.
    - `test_inventory_full_to_town_detour`: Verify full inv triggers town return.
    - `test_low_hp_to_safe_detour`: Verify low hp triggers retreat to safe zone.
    - `test_failed_path_blocker_learning`: Verify repeated path failure suppresses lead.
    - `test_project_abandonment_boredom`: Verify failure count leads to abandonment and boredom bias.

### Manual Verification
- None required (Engine-level logic).
