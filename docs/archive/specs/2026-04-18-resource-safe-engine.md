---
status: archive
authority: P2
audience: historical
layer: economy
original_date: 2026-04-18
---

# Design Spec: Resource-Safe Simulation Engine – Milestone 1 Kickoff

## 1. Goal & Context
Rebuild the simulation engine as a fresh project focusing on deterministic semantics and bounded resource envelopes. This milestone ("Lawmaking") establishes the foundational simulation kernel contract and the resource-envelope rulebook.

## 2. Structural Integrity & New Root
To prevent structural contamination from the legacy codebase:
- **Source Root**: `src/`
- **Test Root**: `tests/`
- **Documentation Root**: `docs/engine/`
- **Rule**: NO runtime imports from legacy `src/` or `tests/`.
- **Directory Layout**:
  ```text
  src/
    config/      # Runtime Profiles and Resource Envelope schemas
    core/        # Authoritative state models and contract interfaces
    engine/      # Kernel phases and orchestration logic
    platform/    # Deterministic RNG and platform-specific abstractions
  tests/      # Fresh test suite (no legacy imports)
  docs/engine/   # Law documents
  ```

## 3. Implementation Sequence (Four-Step Strategy)

### Step 1: Contract Documentation (Design Authority)
Before any code, the following "Laws" must be drafted in `docs/engine/`:
- `simulation_kernel_contract.md`: Defines tick semantics, phase order, and authoritative state (state required to determine future simulation outcomes).
- `runtime_profiles.md`: Defines hard resource ceilings (RAM, CPU, queue depth, etc.) and hardware-class certification language.
- `simulation_kernel_test_matrix.md`: Maps law requirements to specific deterministic test groups.

### Step 2: Code-Facing Contract Types
Implement immutable contract types in `src/`:
- `src/config/profiles.py`: Pydantic models for rigid resource envelopes.
- `src/core/state.py`: Lean dataclasses for authoritative state required for future outcomes.
- `src/core/contracts.py`: Explicit kernel-facing contract markers.
- `src/engine/phases.py`: Enum-defined phase progression.
- `src/platform/rng.py`: Deterministic RNG interfaces.

### Step 3: Enforcement (Contract Tests)
Write these tests before any runnable logic to pin the contract:
- `tests/platform/test_rng_contract.py`: Seed-to-result sequence pinning.
- `tests/config/test_runtime_profile_contract.py`: Schema validation & envelope field coverage.
- `tests/engine/test_simulation_kernel_contract.py`: Deterministic checkpointing & tick semantics.
- `tests/engine/test_phase_order_contract.py`: Freezing the declared phase sequence contract first, then verify the skeletal kernel executes phases in exactly that order.
- `tests/core/test_authoritative_state_contract.py`: Ensuring derived fields are structurally excluded.

### Step 4: The Skeletal Shell
Build the minimum executable contract shell in `src/engine/kernel.py` that orchestrates the phases in Step 2 to pass the tests in Step 3.
- **Constraints**: No scheduler, replay, concurrency, or AI logic.

## 4. Definition of Done for Milestone 1
Milestone 1 is complete when:
- The contract documents (`.md`), code-facing contract types (`.py`), skeletal kernel shell, and deterministic contract tests all exist and agree.
- Zero imports from legacy `src/` or `tests/` exist in `src/` or `tests/`.
- The enforcement suite passes 100%.
