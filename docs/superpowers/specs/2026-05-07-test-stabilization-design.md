# Design Spec: RPG Simulation Test Stabilization (2026-05-07)

## 1. Goal Description
The objective is to stabilize the test suite by resolving widespread failures across API, Arena, and Engine modules. These failures appear to be linked to recent architectural shifts towards `AuthoritativeState` and `V2EntityBuilder`.

## 2. Exploration of Project Context
- **V2 Migration**: The project is in the middle of migrating to a V2 engine with stricter immutability and authoritative state management.
- **Fluent API**: `V2EntityBuilder` is the primary way to create entities.
- **Test Failures**: Initial scan shows failures in multiple domains:
    - **API**: Parity issues between REST and core logic.
    - **Arena**: Startup and regional control logic issues.
    - **Engine**: Combat matrix, migration proof, and worker equivalence failures.

## 3. Clarifying Questions (Self-Refinement)
- Are the `AttributeError`s caused by accessing deleted properties or using old builder methods?
- Is `AuthoritativeState` enforcement causing tests to fail because they attempt direct mutation?
- Are the Arena failures due to timing/asynchrony or fundamental logic drifts?

## 4. Proposed Approaches

### Approach A: Targeted Fixes (Recommended)
Investigate each module's failures sequentially. Identify common patterns (e.g., all `AttributeError`s in `tests/arena` are due to `entity.active` vs `entity.is_active`). Fix the underlying logic in the source or update tests to match the V2 contract.
- **Pros**: Minimal disruption, maintains architectural integrity.
- **Cons**: Can be slow if failures are highly varied.

### Approach B: Global Pattern Replacement
Use `grep`/`sed` or specialized scripts to replace known legacy patterns across the entire test suite (e.g., replacing `.gold(100)` with `.with_gold(100)`).
- **Pros**: Fast for widespread simple patterns.
- **Cons**: Risky; might miss nuanced cases or break valid logic.

### Approach C: Incremental Rollback and Hardening
Roll back the most recent "breaking" change, then re-apply it one module at a time with dedicated hardening tests.
- **Pros**: Safest way to ensure 100% pass rate at each step.
- **Cons**: High effort, might conflict with other developers' work.

## 5. Proposed Design (Targeted Fixes)

### 5.1 API Stabilization
- Audit `tests/api/test_rest_parity.py`.
- Ensure REST endpoints are correctly mapping to the `AuthoritativeState` and using the proper DTOs.

### 5.2 Arena Stabilization
- Fix `AttributeError` in `test_arena_quests.py` and others.
- Validate that the Arena harness correctly initializes the Kernel with the V2 builder.

### 5.3 Engine Stabilization
- **Combat Matrix**: Re-verify the legality matrix logic.
- **Worker Equivalence**: Ensure different worker implementations (e.g., sequential vs concurrent) produce identical state updates.
- **Read-Only Guard**: Verify that observational paths do not inadvertently trigger mutations.

## 6. Verification Plan
- Run the full test suite (excluding long-run tests).
- Run `graphify update .` to ensure the knowledge graph is current.
- Add regression tests for any non-trivial logic fixes.
