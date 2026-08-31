---
status: active
layer: testing
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Requirement Traceability Map

**Related docs:**
- `docs/testing/test_taxonomy.md` — marker definitions and enforcement rules
- `docs/testing/regression_policy.md` — which groups are hard gates
- `docs/testing/how_to_add_requirement_tests.md` — how to add a new requirement test
- `docs/parity_ledger/` — P0 law parity evidence (one YAML file per subsystem)
- `docs/compliance/checklist.md` — atomic RPG-core law inventory

---

## Purpose

This document is the authoritative map from simulation behavior requirements to the test files that protect them. It answers the question: *"What proves that requirement X is protected?"*

An agent investigating a regression, auditing coverage, or adding a new law test should consult this map first. All file paths are verified real files in `tests/`.

---

## Master Traceability Table

| Requirement Group | Example Behavior | Test File(s) | Markers | Authority |
|---|---|---|---|---|
| **Resource Conservation** | No source mutation (node depletion, ground item removal, corpse removal) occurs unless the destination successfully receives the transfer. Gold is not deducted if an item cannot be stored. | `tests/integration/pipeline/test_transaction_completion.py` `tests/integration/kernel/test_resource_conservation.py` `tests/integration/kernel/test_resource_conservation_v2.py` | `v2_contract`, `regression` | P0 |
| **Grouped Transfer Rollback** | A grouped bundle of resource transfers rolls back atomically if any required member fails. Independent transfers may partially succeed. | `tests/integration/pipeline/test_transaction_completion.py` (`TestGroupedTransferRollback`) | `v2_contract` | P0 |
| **API History** | The history API returns paginated entity snapshots, diffs, and features. Missing run returns 404. Malformed identifiers return 400. | `tests/api/test_cognition_history_api.py` | `anyio` | P1 |
| **Historical Search** | The search API supports querying runs, events, anomalies, and metric trends. Entity timeline combines events and anomalies in tick order. | `tests/api/test_historical_event_search_api.py` | `anyio` | P1 |
| **API Security** | Path-traversal patterns in `run_id` or `entity_id` raise HTTP 400 before any filesystem access. | `tests/api/test_cognition_history_api.py` (`test_get_entity_snapshots_path_traversal`) `tests/api/test_historical_event_search_api.py` (`test_api_security_sanitization`) | `anyio` | P0 |
| **Live Observability** | The live `/status` endpoint returns `RUNNING` or `PAUSED` with a health score. The live snapshot endpoint returns current entity states under a running server. | `tests/api/test_live_observability_status.py` `tests/api/test_live_health_api.py` | none (live server tests) | P1 |
| **WebSocket Protocol** | The observability WebSocket emits structured tick events. Backpressure does not corrupt the event stream. | `tests/api/test_ws_protocol.py` `tests/api/test_observability_websocket.py` `tests/integration/observability/test_stream_backpressure.py` | `anyio` | P1 |
| **Combat Legality** | Melee attacks require adjacency. Ranged attacks require line-of-sight. AoE resolves as atomic sub-intents. Dead targets are rejected. Actions against invalid targets are rejected before any side effect is calculated. | `tests/integration/pipeline/test_combat_legality_matrix.py` `tests/integration/pipeline/test_combat_trust.py` `tests/integration/combat/test_relation_combat_integration.py` | `v2_contract`, `differential` | P0 |
| **Performance Correctness** | Resource scenario p95 tick latency < 250ms at 1000 entities. Combat scenario within baseline thresholds. Hard law monitor adds < acceptable overhead. | `tests/perf/test_perf_resource.py` `tests/perf/test_perf_combat.py` `tests/perf/test_hard_law_monitor_overhead.py` `tests/perf/test_perf_regression_baseline.py` | `perf`, `slow` | P1 |
| **World Determinism** | The same seed produces bit-identical state hashes across 10 independent runs. Long-run determinism holds past tick 1000. World compile produces identical output. | `tests/integration/kernel/test_determinism_suite.py` `tests/integration/kernel/test_long_run_determinism.py` `tests/integration/kernel/test_seed_stability.py` `tests/integration/kernel/test_overflow_determinism.py` `tests/certification/test_world_compile_determinism.py` | `v2_contract`, `differential`, `certification` | P0 |
| **Progression Correctness** | XP-to-level formula matches Mechanics Bible §01. Attribute growth on level-up is correct. Evolution point conversion is bounded. Breakthrough events trigger at the right thresholds. | `tests/unit/progression/test_leveling.py` `tests/unit/quest/test_progression_regression.py` `tests/unit/progression/test_evolution.py` `tests/unit/progression/test_breakthroughs.py` `tests/integration/domains/progression/test_phase6_progression_conversion_phase.py` `tests/integration/progression/test_allocate_ap_dormancy.py` | `v2_contract`, `legacy_characterization` | P1 |
| **Authoritative Mutation Boundary** | World mutation happens after proposal generation, not inside worker thought code. Workers cannot directly set authoritative state (e.g., quest status). | `tests/integration/pipeline/test_mutation_boundary.py` `tests/integration/pipeline/test_no_hidden_mutation.py` `tests/integration/pipeline/test_rejection_audit.py` | `v2_contract` | P0 |
| **Kernel Contract** | The kernel executes the 6-phase deterministic loop. Conflict resolution produces one authoritative outcome per tick. Worker decision-making is decoupled from authoritative application. | `tests/integration/kernel/test_simulation_kernel_contract.py` `tests/integration/kernel/test_kernel_boundaries.py` `tests/integration/kernel/test_authoritative_outcome_truth.py` | `v2_contract`, `certification` | P0 |
| **Replay Fidelity** | Replay consumes authoritative results rather than recomputing them. Replay output is bit-identical to the original run. | `tests/integration/kernel/test_replay_fidelity.py` `tests/integration/kernel/test_p1_replay_fidelity.py` `tests/integration/kernel/test_event_replay.py` | `v2_contract`, `differential` | P1 |

---

## Requirement Groups — Detail Notes

### Resource Conservation (P0)

**Mechanics Bible reference:** `docs/mechanics/03_economic_laws.md` — Atomic Conservation law.  
**Parity ledger:** `docs/parity_ledger/town_resource.yaml`

The core invariant: if a transfer's destination cannot accept the payload, the source must not be mutated. This applies to:
- Node harvesting (node charges preserved on full inventory)
- Ground item pickup (item remains on ground if inventory full)
- Corpse looting (corpse persists if inventory full)
- Shop purchase (gold not deducted if item cannot be stored)
- Crafting (materials not consumed if product cannot be added)

All of these are tested in `test_transaction_completion.py` under `TestSourceMutationConservation`.

### API Security (P0)

**Pattern:** Path-traversal strings (`../../etc/passwd`) in any identifier parameter must raise HTTP 400. The check is performed in the route handler before any service call resolves a filesystem path.

### Combat Legality (P0)

**Mechanics Bible reference:** `docs/mechanics/02_combat_laws.md`.  
**Compliance IDs in test file:** COMB-283 through COMB-289.  
**Parity ledger:** `docs/parity_ledger/combat_movement.yaml`

### World Determinism (P0)

**Engine Contract reference:** `docs/engine/kernel.md` — deterministic loop.  
**Parity ledger:** `docs/parity_ledger/substrate.yaml`

Standard: same seed, same scenario → `CanonicalStateHasher` produces identical hash at every tick across independent runs.

---

## How to Keep This Map Current

This map is maintained manually. The update obligation is triggered by any of:

1. **A new test file is added that protects a requirement** — add a row or extend the test file list in the relevant row. See `docs/testing/how_to_add_requirement_tests.md` for the full workflow.

2. **An existing test is renamed or moved** — update the file path in this table. A stale path will mislead agents during regression triage.

3. **A new requirement group is established** — add a new row. The group must map to at least one real test file before it appears here.

4. **A test is deleted** — if it was the sole test for a requirement, either add a replacement test or note the gap explicitly in the row under test file(s) as `[GAP — no current test]`.

5. **A P0 law changes** — update the parity ledger entry in `docs/parity_ledger/` in the same session. Then update this table's test file and marker columns.

**Who is responsible:** The agent or developer who performs the implementation that triggers any of the above. The traceability map must be updated in the same commit or session as the behavior change.

**How to verify the map is current:** For each row, run `ls <test_file_path>` to confirm the file exists. If a path is stale, treat it as a P1 defect.
