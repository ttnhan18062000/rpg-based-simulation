# Implementation Plan: Resource-Safe Engine Milestone 1

## Goal Description
Build the foundational "Lawmaking" layer for the new simulation engine. This milestone focuses on freezing semantics, defining resource envelopes, and creating a skeletal, isolated kernel structure.

## Proposed Changes
Follow the four-step strategy: Docs -> Types -> Tests -> Shell.

### Documentation & Laws
- `docs/engine/simulation_kernel_contract_m1.md`: Define tick semantics and authoritative state.
- `docs/engine/runtime_profiles_m1.md`: Define resource ceilings.
- `docs/engine/m1_test_matrix.md`: Map requirements to test groups.

### Code-Facing Contract Types (src_v2/)
- `src_v2/config/profiles.py`
- `src_v2/core/state.py`
- `src_v2/core/contracts.py`
- `src_v2/engine/phases.py`
- `src_v2/platform/rng.py`

### Enforcement Layer (tests_v2/)
- `tests_v2/platform/test_rng_contract.py`
- `tests_v2/config/test_runtime_profile_contract.py`
- `tests_v2/engine/test_simulation_kernel_contract.py`
- `tests_v2/engine/test_phase_order_contract.py`
- `tests_v2/core/test_authoritative_state_contract.py`

### Skeletal Shell (src_v2/engine/)
- `src_v2/engine/kernel.py`
- `src_v2/engine/readiness.py`
- `src_v2/engine/tick.py`

## Verification Plan

### Automated Tests
- Run `pytest tests_v2/`.
- Verify zero imports from `src/` or `tests/`.

### Manual Verification
- Inspect doc/code alignment.
