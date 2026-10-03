---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260327-WINDBIGMOD
artifact_type: plan
tags: [windbigmod]
---

# WINDBIGMOD Implementation Plan

## Step 1: BIGMOD (StatsShim Extraction)
1. **[NEW] `src/core/stats_proxy.py`**
    - Define `StatModifier` protocol (or base class).
    - Extract `StatsShim` from `models.py`.
    - Implement delegation to `active_effects` and `equipment`.
2. **[MODIFY] `src/core/models.py`**
    - Replace local `StatsShim` with imported version.
    - Clean up `Entity` base class to remove shim-specific implementation details.
    - Confirm no breaking changes to `Hero` and `Mob` subclasses.

## Step 2: Wind Pillar (Flow Field Smoothing)
1. **[MODIFY] `src/ai/flow_fields.py`**
    - Implement `get_vector_bilinear(self, pos: FloatVector2) -> FloatVector2`.
    - Interpolate directions of the 4 surrounding nodes for sub-tile precision.
    - Normalize the resulting vector.
2. **[MODIFY] `src/ai/flow_fields.py` (FlowFieldManager)**
    - Add `is_static_target(self, target: Vector2, grid: SnapshotGrid) -> bool`.
    - Ensure Towns and Camps use infinite cache (no TTL).
    - Ensure World Bosses (Calamities) use 5-tick TTL.

## Step 3: Wind Pillar (Navigation Integration)
1. **[MODIFY] `src/ai/states/navigation.py`**
    - In `MoveTowardHandler`, check `FlowFieldManager` for a global field.
    - Switch to Flow Field if distance > 10.
2. **[MODIFY] `src/ai/states/town.py`**
    - Update `ReturnToTownHandler` to explicitly request Flow Fields for efficiency.

## Step 4: Verification
1. Run `pytest tests/unit/ai/test_flow_fields.py`.
2. Run `pytest tests/unit/core/test_models.py`.
3. Run `make profile` and compare "AI Tick Phase" timings.
