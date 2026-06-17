---
status: active
layer: engine
authority: P1
audience: developer
---

# Simulation Kernel Verification Surface

Maps the core contract laws to specific deterministic test groups. Every law in the kernel and profile contracts must be pinned by at least one regression test.

## 1. Deterministic RNG (`tests/platform/`)

| Requirement | Test Group | Input Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| Seed Reproducibility | `test_rng_reproducibility` | Seed `42`, 1000 draws | Exact byte-identical sequence |
| State Isolation | `test_rng_isolation` | Two RNG instances, same seed | Independent but identical sequences |
| No Time Leakage | `test_rng_no_time_leakage` | Mock `time.time()` | RNG output remains unchanged |

## 2. Runtime Profiles (`tests/config/`)

| Requirement | Test Group | Input Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| Required Fields | `test_profile_schema` | Valid dict | Successful Pydantic instantiation |
| Hard Ceilings | `test_invalid_ceilings` | Negative `max_ram` | `ValidationError` at instantiation |
| Language Consistency | `test_hardware_class_logic` | Valid profile | Verification of hardware-class certification concept |

## 3. Kernel Contract (`tests/engine/`)

| Requirement | Test Group | Input Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| Phase Ordering | `test_phase_order_contract` | Iterating `PhaseEnum` | Exact 1:1 match with the 6-phase contract |
| Skeletal Integrity | `test_kernel_execution_order` | Mock phase execute | Phases called in enum order exactly once |
| Tick Advancement | `test_quiet_tick_semantics` | Empty collection | Tick increments and context persists |

## 4. Authoritative State (`tests/core/`)

| Requirement | Test Group | Input Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| Structural Isolation | `test_state_shape` | `AuthoritativeState` | Zero diagnostic/replay fields |
| Determinism Anchor | `test_state_hashing` | Identical state | Stable and identical deterministic hash |

## Regression Intent

- **Phase Drifting**: Accidental reordering of tick phases.
- **Contract Dilution**: Adding non-authoritative data into core state.
- **Resource Vagueness**: Creating profiles with missing or advisory-only limits.
- **RNG Pollution**: Leaking system time or ambient state into the simulation.
