# Milestone 1 Test Matrix — Contract Enforcement

## 1. Purpose
This matrix maps the high-level laws defined in the kernel and profile contracts to specific deterministic test groups in `tests_v2/`.

## 2. Test Groups

### Group A: Deterministic RNG (`tests_v2/platform/`)
| Requirement | Test Group | Input Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| Seed Reproducibility | `test_rng_reproducibility` | Seed `42`, 1000 draws | Exact byte-identical sequence |
| State Isolation | `test_rng_isolation` | Two RNG instances, same seed | Independent but identical sequences |
| No Time Leakage | `test_rng_no_time_leakage` | Mock `time.time()` | RNG output remains unchanged |

### Group B: Runtime Profiles (`tests_v2/config/`)
| Requirement | Test Group | Input Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| Required Fields | `test_profile_schema` | Valid Dict | Successful Pydantic instantiation |
| Hard Ceilings | `test_invalid_ceilings` | Negative `max_ram` | `ValidationError` at instantiation |
| Language Consistency | `test_hardware_class_logic` | Valid Profile | Verification of hardware-class cert concept |

### Group C: Kernel Contract (`tests_v2/engine/`)
| Requirement | Test Group | Input Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| Phase Ordering | `test_phase_order_contract` | Iterating `PhaseEnum` | Exact 1:1 match with Step 4 contract |
| Skeletal Integrity | `test_kernel_execution_order`| Mock Phase execute | Phases called in Enum order exactly once |
| Tick Advancement | `test_quiet_tick_semantics` | Empty collection | Tick increments and context persists |

### Group D: Authoritative State (`tests_v2/core/`)
| Requirement | Test Group | Input Condition | Expected Result |
| :--- | :--- | :--- | :--- |
| Structural Isolation | `test_state_shape` | `AuthoritativeState` | Zero diagnostic/replay fields |
| Determinism Anchor | `test_state_hashing` | Identical State | Stable and identical deterministic hash |

## 3. Regression Intent
These tests are designed to catch:
- **Phase Drifting**: Accidental reordering of tick phases.
- **Contract Dilution**: Adding non-authoritative data into core state.
- **Resource Vagueness**: Creating profiles with missing or advisory-only limits.
- **RNG Pollution**: Leaking system time or ambient state into the simulation.
