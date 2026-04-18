# Test Plan: Resource-Safe Engine Milestone 1

## Purpose
Verify that the simulation kernel contract and resource-envelope rulebook are strictly enforced by the code-facing types and skeletal kernel shell.

## Test Areas

### 1. Deterministic RNG (src_v2/platform/rng.py)
- **Goal**: Ensure the RNG is truly deterministic and isolated from ambient state.
- **Tests**:
  - `test_rng_reproducibility`: Same seed must yield the same 1k number sequence.
  - `test_rng_isolation`: RNG instances must not share state.

### 2. Runtime Profiles (src_v2/config/profiles.py)
- **Goal**: Validate the resource-envelope contract.
- **Tests**:
  - `test_profile_validation`: Ensure required fields (RAM, CPU, etc.) are present and valid.
  - `test_invalid_profile_rejection`: Test negative values, missing fields, and type mismatches.
  - `test_profile_comparison`: Ensure profiles can be compared (e.g., "Developer" vs "Server Small").

### 3. Authoritative State (src_v2/core/state.py)
- **Goal**: Structural enforcement of authoritative-only data.
- **Tests**:
  - `test_state_immutability_intent`: Ensure state structs are designed for shallow-copying or generation-based mutation.
  - `test_derived_state_exclusion`: Verify that no diagnostic or replay fields are present in the core state dataclasses.

### 4. Phase Orchestration (src_v2/engine/phases.py & kernel.py)
- **Goal**: Freeze tick semantics and phase order.
- **Tests**:
  - `test_phase_order_immutability`: Assert the enum-defined sequence.
  - `test_kernel_execution_order`: Use mocks to verify the skeletal kernel calls phases in the exact contract order.

### 5. Deterministic Kernel (src_v2/engine/kernel.py)
- **Goal**: Seed-to-checkpoint consistency.
- **Tests**:
  - `test_seed_to_checkpoint`: Same seed + same inputs => same authoritative state hash.
  - `test_quiet_tick_determinism`: Ensure empty ticks still advance world-time deterministically.

## Verification Constraints
- **Zero Legacy Imports**: A scan of `src_v2/` must not reveal any imports from the legacy `src/` directory.
- **Isolated Tests**: `tests_v2/` must be runnable independently of the legacy test suite.
