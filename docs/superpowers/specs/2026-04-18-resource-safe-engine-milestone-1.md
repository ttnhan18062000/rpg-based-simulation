# Design Spec: Resource-Safe Simulation Engine – Milestone 1 Kickoff

## 1. Goal & Context
Rebuild the simulation engine as a fresh project focusing on deterministic semantics and bounded resource envelopes. This milestone ("Lawmaking") establishes the foundational simulation kernel contract and the resource-envelope rulebook.

## 2. Structural Integrity & New Root
To prevent structural contamination from the legacy codebase:
- **Source Root**: `src_v2/`
- **Test Root**: `tests_v2/`
- **Documentation Root**: `docs/engine/`
- **Rule**: NO runtime imports from legacy `src/` or `tests/`.
- **Directory Layout**:
  ```text
  src_v2/
    config/      # Runtime Profiles and Resource Envelope schemas
    core/        # Authoritative state models and contract interfaces
    engine/      # Kernel phases and orchestration logic
    platform/    # Deterministic RNG and platform-specific abstractions
  tests_v2/      # Fresh test suite (no legacy imports)
  docs/engine/   # Law documents
  ```

## 3. Implementation Sequence (Four-Step Strategy)

### Step 1: Contract Documentation (Design Authority)
Before any code, the following "Laws" must be drafted in `docs/engine/`:
- `simulation_kernel_contract_m1.md`: Defines tick semantics, phase order, and authoritative state (state required to determine future simulation outcomes).
- `runtime_profiles_m1.md`: Defines hard resource ceilings (RAM, CPU, queue depth, etc.) and hardware-class certification language.
- `m1_test_matrix.md`: Maps law requirements to specific deterministic test groups.

### Step 2: Code-Facing Contract Types
Implement immutable contract types in `src_v2/`:
- `src_v2/config/profiles.py`: Pydantic models for rigid resource envelopes.
- `src_v2/core/state.py`: Lean dataclasses for authoritative state required for future outcomes.
- `src_v2/core/contracts.py`: Explicit kernel-facing contract markers.
- `src_v2/engine/phases.py`: Enum-defined phase progression.
- `src_v2/platform/rng.py`: Deterministic RNG interfaces.

### Step 3: Enforcement (Contract Tests)
Write these tests before any runnable logic to pin the contract:
- `tests_v2/platform/test_rng_contract.py`: Seed-to-result sequence pinning.
- `tests_v2/config/test_runtime_profile_contract.py`: Schema validation & envelope field coverage.
- `tests_v2/engine/test_simulation_kernel_contract.py`: Deterministic checkpointing & tick semantics.
- `tests_v2/engine/test_phase_order_contract.py`: Freezing the declared phase sequence contract first, then verify the skeletal kernel executes phases in exactly that order.
- `tests_v2/core/test_authoritative_state_contract.py`: Ensuring derived fields are structurally excluded.

### Step 4: The Skeletal Shell
Build the minimum executable contract shell in `src_v2/engine/kernel.py` that orchestrates the phases in Step 2 to pass the tests in Step 3.
- **Constraints**: No scheduler, replay, concurrency, or AI logic.

## 4. Definition of Done for Milestone 1
Milestone 1 is complete when:
- The contract documents (`.md`), code-facing contract types (`.py`), skeletal kernel shell, and deterministic contract tests all exist and agree.
- Zero imports from legacy `src/` or `tests/` exist in `src_v2/` or `tests_v2/`.
- The enforcement suite passes 100%.
