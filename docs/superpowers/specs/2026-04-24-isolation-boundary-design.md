# Design Specification — Phase 1 Task 1.4: V2 State Isolation Boundary

## 1. Goal
Enforce a total isolation boundary between the **Authoritative State** and the **Execution Environment** (Kernel, Systems, Workers). This ensures that the state remains bit-identical across simulation ticks except through the singular, validated `ApplyPath`.

## 2. Context
The V2 substrate has already implemented deterministic tick alignment (Task 1.2) and deep immutability (Task 1.3). However, the Kernel still performs manual state manipulation for clock advancement, and the `LocalSequentialExecutor` passes mutable state references to systems. These are "architecture leaks" (Principle 1.2) that must be closed before Phase 2.

## 3. Proposed Design

### 3.1 Singular Apply Authority
The `ApplyPath.apply_generation` method will become the exclusive owner of all state transitions.
- **Clock Advancement**: `apply_generation` will accept `next_tick` and `next_world_time` as optional parameters.
- **Kernel Refactor**: `Kernel._phase_advancement` will no longer call `replace(self._state, ...)`. Instead, it will call `ApplyPath.apply_generation` with an empty update and the incremented clock values.

### 3.2 Reference Isolation (Deep Freeze)
- **Sequential Parity**: The `LocalSequentialExecutor` will be refactored to use `deep_freeze` on the `AuthoritativeState` before passing it to systems.
- **Boundary Proof**: Systems will never receive a mutable dictionary or list belonging to the authoritative state.

### 3.3 Integrity Guard (Audit Mode)
A new `IntegrityGuard` component in the Kernel will:
- Capture the state fingerprint at the start of non-mutating phases.
- Assert equality at the end of the phase.
- This is enabled during `tests` and `certification` runs to catch mutation leaks.

## 4. Components

### 4.1 Kernel Phase Updates
- **Init**: Captures current clock.
- **Resolution**: Applies updates via `ApplyPath`.
- **Advancement**: Applies clock increment via `ApplyPath`.

### 4.2 Executor Hardening
- `LocalSequentialExecutor.execute`:
  ```python
  snapshot = deep_freeze(state)
  # ... execute systems using snapshot ...
  ```

## 5. Verification Plan

### 5.1 Contract Tests (`v2_contract`)
- `test_state_immutability_enforcement`: A test that tries to mutate the state inside a system call and verifies that a `TypeError` or `AttributeError` is raised.
- `test_clock_advancement_exclusivity`: Verifies that the tick only changes during the Advancement phase.

### 5.2 Parity Tests
- `test_sequential_concurrent_isolation_parity`: Ensures that the sequential and concurrent executors produce bit-identical fingerprints for complex interaction scenarios.
