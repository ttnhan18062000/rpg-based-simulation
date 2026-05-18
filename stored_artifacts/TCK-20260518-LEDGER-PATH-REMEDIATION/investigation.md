# Investigation: Release Gate Ledger Discrepancies

## Root Cause Analysis
During automated testing, `pytest tests/` passes successfully up until `tests/certification/test_final_gate.py::test_real_release_proof_is_valid`.
The M10 certification release gate script (`scripts/release_gate.py`) invokes `scripts/ledger_validator.py` to verify that every item in `docs/logic_checklist_exhaustive.md` points to existing source and test paths in the repository.

The validator fails due to two distinct classes of errors:
1. **Critical Domain Error**: Section Z20 (Milestone 3 Performance Optimization Mechanisms) introduced 14 items with IDs `RPG-OPT-001` through `RPG-OPT-014`. The domain prefix `OPT` is not in the approved `DOMAINS` set in `scripts/ledger_validator.py`, causing 14 critical validation errors.
2. **Path Existence Warnings**: Across sections Z14–Z18 and Z20, 58 paths cited in metadata comments (`<!-- SOURCE: ... TEST: ... PROOF: ... -->`) do not match the actual file locations on disk.

## Path Mapping Matrix
Through exact filesystem mapping, we identified the true locations of all cited files:
- **Optimization Sources (Section Z20)**:
  - `RPG-OPT-001`: `src/core/dirty.py` (CandidateSelector)
  - `RPG-OPT-004`: `src/core/dirty.py` (DirtyDependencyGraph)
  - `RPG-OPT-005`: `src/engine/compactor.py` (StateUpdateCompactor)
  - `RPG-OPT-007`: `src/engine/candidate_selector.py` (MovementCandidateSelector)
  - `RPG-OPT-008`: `src/engine/occupancy_snapshot.py` (OccupancySnapshot)
  - `RPG-OPT-009`: `src/engine/movement_cache.py` (MovementPlanCache)
  - `RPG-OPT-010`: `src/engine/spatial_query.py` (SpatialQueryService)
  - `RPG-OPT-011`: `src/engine/world_index.py` (CacheInvalidationPolicy)
  - `RPG-OPT-012`: `src/systems/strategic_systems/work_queue.py` (StrategicWorkQueue)
  - `RPG-OPT-013`: `scripts/profile_engine.py` (ProfilingHarness)
  - `RPG-OPT-014`: `src/perf/regression_gate.py` (PerfRegressionGate)
- **Subsystem Tests (Sections Z14–Z18)**:
  - `test_movement_congestion.py` -> `tests/unit/movement/test_movement_congestion.py`
  - `test_combat_legality_matrix.py` -> `tests/integration/pipeline/test_combat_legality_matrix.py`
  - `test_phase6_strategic_cognition.py` -> `tests/unit/strategic/test_phase6_strategic_cognition.py`
  - `src/social/contracts.py` -> `src/systems/social_systems/contracts.py`
  - `test_contract_lifecycle_phase7.py` -> `tests/unit/social/test_contract_lifecycle_phase7.py`
  - `test_resource_conservation.py` -> `tests/integration/kernel/test_resource_conservation.py`
  - `test_rpg_depth.py` -> `tests/unit/core/test_rpg_depth.py`
  - `test_replay_determinism.py` -> `tests/unit/kernel/test_replay_determinism.py`
  - `test_long_run_determinism.py` -> `tests/integration/kernel/test_long_run_determinism.py`
  - `test_living_world_ph9.py` -> `tests/integration/world/test_living_world_ph9.py`
  - `test_authoritative_state_contract.py` -> `tests/unit/core/test_authoritative_state_contract.py`
  - `test_transaction_completion.py` -> `tests/integration/pipeline/test_transaction_completion.py`
  - `test_domain_8_economy.py` -> `tests/unit/resource/test_domain_8_economy.py`
  - `test_hardening_e5.py` -> `tests/unit/core/test_hardening_e5.py`
  - `test_phase_order_contract.py` -> `tests/integration/pipeline/test_phase_order_contract.py`
