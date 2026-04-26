# Implementation Plan: Resource-Safe Engine Milestone 1

## Goal Description
Build the foundational "Lawmaking" layer for the new simulation engine. This milestone focuses on freezing semantics, defining resource envelopes, and creating a skeletal, isolated kernel structure.

## Proposed Changes
Follow the four-step strategy: Docs -> Types -> Tests -> Shell.

### Documentation & Laws
- `docs/engine/simulation_kernel_contract_m1.md`: Define tick semantics and authoritative state.
- `docs/engine/runtime_profiles_m1.md`: Define resource ceilings.
- `docs/engine/m1_test_matrix.md`: Map requirements to test groups.

### Code-Facing Contract Types (src/)
- `src/config/profiles.py`
- `src/core/state.py`
- `src/core/contracts.py`
- `src/engine/phases.py`
- `src/platform/rng.py`

### Enforcement Layer (tests/)
- `tests/platform/test_rng_contract.py`
- `tests/config/test_runtime_profile_contract.py`
- `tests/engine/test_simulation_kernel_contract.py`
- `tests/engine/test_phase_order_contract.py`
- `tests/core/test_authoritative_state_contract.py`

### Skeletal Shell (src/engine/)
- `src/engine/kernel.py`
- `src/engine/readiness.py`
- `src/engine/tick.py`

## Verification Plan

### Automated Tests
- Run `pytest tests/`.
- Verify zero imports from `src/` or `tests/`.

### Manual Verification
- Inspect doc/code alignment.
