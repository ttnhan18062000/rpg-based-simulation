---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-APPLY-PATH-REDESIGN
artifact_type: plan
tags: [apply, path, redesign]
---

# Implementation Plan - Milestone 14 ApplyPath Structural Redesign

## Problem Statement
During state application in `ApplyPath.apply_generation`, the engine repeatedly loops through every entity and checks every possible component field on `EntityUpdate` (18+ checks per entity) and branches conditionally to construct a replacement dictionary. This creates CPU overhead and branch mispredictions during heavy ticks.

## Proposed Solution
Introduce `ApplyPlan` and `ApplyPlanBuilder` in `src/engine/apply_plan.py`. `ApplyPlanBuilder` will take the compacted `StateUpdate` and precompute exactly which entities have changes, grouping them by domain. It will precompute component replacements and determine which collections need copying and which caches/indexes must be invalidated. `ApplyPath.apply_generation` will then directly execute this prepared `ApplyPlan`.

## Architectural Changes
1. **`src/engine/apply_plan.py`**:
   - `ApplyPlan`: Dataclass holding precomputed dictionaries of entity component changes, world collection changes, resource transfers, lifecycle changes, transaction trace changes, and cache invalidation hints.
   - `ApplyPlanBuilder`: Class with `build_plan(state, update)` method.
2. **`src/engine/apply.py`**:
   - Refactor `ApplyPath.apply_generation` to utilize `ApplyPlanBuilder.build_plan(state, update)`.
   - Iterate only over entities that require passive updates or have intentional changes precomputed in `ApplyPlan`.

## Verification
- Unit test: `tests/unit/optimization/test_apply_plan_builder.py` verifying grouping and precomputation.
- Parity test: `tests/integration/optimization/test_apply_plan_parity.py` verifying exact 100% hash parity with old behavior.
- Perf test: `tests/perf/test_apply_plan_perf.py` verifying performance improvement in state application.
