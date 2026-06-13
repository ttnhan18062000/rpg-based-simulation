---
ticket_id: TCK-20260613-DOC-TESTING-TRACEABILITY
artifact: investigation
date: 2026-06-13
---

# Investigation: TCK-20260613-DOC-TESTING-TRACEABILITY

## 1. Test Suite Inventory

| Directory | Notable subdirectories / files | Rough count |
|---|---|---|
| `tests/api/` | 11 files: cognition_history, historical_event_search, live_entity_inspection, live_health, live_observability_status, observability_websocket, paged_logic, phase27_behavior_query, rest_parity, ws_protocol | 11 files |
| `tests/architecture/` | 9 files: enum_migration_report, fallback_retirement_gate, legacy_enum_usage_boundaries, no_new_hardcoded_gameplay_truth, no_old_structural_content_paths, phase18_* (3), phase19_* (2) | 9 files |
| `tests/integration/` | Subdirs: campaigns, certification, combat, content, content_packs, domains, entities, kernel, lab, lab_agent, observability, optimization, perf, pipeline, scenarios | ~80 files |
| `tests/integration/pipeline/` | 18 files: authoritative_apply, combat_legality_matrix, combat_trust, governance_isolation, movement_*, mutation_boundary, no_hidden_mutation, phase5_idempotency, phase_order*, recovery_gaps, rejection_audit, state_isolation, strategic_cadence, transaction_completion | 18 files |
| `tests/integration/kernel/` | 24 files: authoritative_outcome_truth, certification_scenarios, checkpoint_reproducibility, determinism_suite, event_replay, executor_determinism, kernel_boundaries, long_run_determinism, milestone_a/b/c/d_closure, minimal_kernel, overflow_determinism, p1_replay_fidelity, phase10_replay, phase2_determinism, race_conditions_v2, replay_fidelity, resource_conservation, resource_conservation_v2, seed_stability, simulation_kernel_contract, snapshot_integrity, substrate_freeze_m1, worker_determinism | 24 files |
| `tests/integration/observability/` | ~35 files: phase20-28 observability tests, warehouse ingestion, event recorder, metric windows, multi-run index, stream backpressure, etc. | ~35 files |
| `tests/perf/` | 20+ files: bench_apply_path, bench_capacity, bench_worker_throughput, test_api_projection_perf, test_apply_compaction_perf, test_concurrency_parity, test_dirty_parity, test_dirty_set_integrity, test_hard_law_monitor_overhead, test_lod, test_observability_scale_validation, test_perf_{resource,combat,idle,metropolis}, etc. | 20+ files |
| `tests/certification/` | 11 files: allowed_failure_truth, cert_long_run_stability, envelope_violations, event_observability_parity, final_gate, harness_contract, phase10_enhanced_determinism_parity, phase10_enhanced_rollout_gate, phase28_behavior_observability_rollout_gate, resilience_recovery, world_compile_determinism | 11 files |
| `tests/scenarios/` | `phase1/` subdirectory | ~5 files |
| `tests/unit/` | Subdirs: api, campaigns, certification, cognition, combat, config, content, content_semantics, core, diagnostics, domains, engine, entities, entity, kernel, lab, lab_agent, movement, progression | ~100+ files |
| `tests/docs/` | 2 files: test_contributor_guardrails.py, test_doc_integrity.py | 2 files |

## 2. Annotation Conventions

### Existing requirement-style annotations (found via grep)

- **`test_combat_legality_matrix.py`** uses block comments citing compliance IDs and RPG-law IDs at file top:
  ```
  # Compliance IDs: COMB-283, COMB-284, ...
  # RPG-0012: melee_adjacency_parity
  # [RPG-AUTH-002] Every gameplay side effect is represented as a typed update bucket.
  # Logic ID: COMB-283 (...)
  ```
- **`test_transaction_completion.py`** uses docstring at class level:
  ```python
  class TestSourceMutationConservation:
      """Law: Node charges must not decrease if item cannot be added to inventory."""
  ```
  And inline comments `# Law:` on individual asserts.
- **`test_resource_conservation.py` / `test_resource_conservation_v2.py`** — no inline REQ: annotations; coverage is implicit in test names and docstrings.
- **`tests/api/test_cognition_history_api.py`** — no requirement annotations; tests are behaviour-focused (`@pytest.mark.anyio` only).
- **`tests/api/test_historical_event_search_api.py`** — security test `test_api_security_sanitization` exists with inline comment `# Path traversal patterns should raise HTTPException with 400 status code`.

### Verdict on annotation convention
No uniform `# REQ:` / `# Law:` annotation convention exists across the suite. A few files (combat legality matrix) use compliance-ID block comments; most tests use docstrings or plain inline comments. **The traceability map must be built from file inspection, not from annotations.** The `how_to_add_requirement_tests.md` document must establish the recommended convention going forward.

## 3. Pytest Markers Registered (from `pyproject.toml`)

```
slow                  — deselect with -m "not slow"
extra_slow            — deselect with -m "not extra_slow"
world_long_run        — long-run living-world stability
legacy_characterization
v2_contract
differential
intentional_divergence
regression
certification
perf                  — found in tests/perf/ (test_perf_resource.py etc.)
anyio / asyncio       — async test runners
parametrize           — standard pytest
worldassembly         — from v2_test_taxonomy.md
```

Taxonomy markers (`legacy_characterization`, `v2_contract`, `differential`, `intentional_divergence`, `regression`, `certification`) are defined in `docs/testing/v2_test_taxonomy.md` and enforced on `tests/parity/` at collection time.

## 4. Tests Protecting Resource Conservation

Primary files:
- `tests/integration/pipeline/test_transaction_completion.py` — atomic transfer resolver, grouped rollback, rejection reasons, source mutation conservation
- `tests/integration/kernel/test_resource_conservation.py` — harvest system: node charges not depleted on full inventory
- `tests/integration/kernel/test_resource_conservation_v2.py` — harvest + pipeline path for resource conservation
- `tests/integration/pipeline/test_mutation_boundary.py` — authoritative mutation is post-proposal only
- `tests/integration/pipeline/test_rejection_audit.py` — intent result propagation through pipeline

## 5. Tests Protecting API Security

Primary files:
- `tests/api/test_cognition_history_api.py` — `test_get_entity_snapshots_path_traversal` → 400 on `../../etc/passwd` run_id
- `tests/api/test_historical_event_search_api.py` — `test_api_security_sanitization` → 400 on path-traversal run_id
- `tests/api/test_live_health_api.py` — live server HTTP endpoint validation
- `tests/api/test_live_observability_status.py` — live server status endpoint contracts
- `tests/api/test_ws_protocol.py` — WebSocket protocol contract

## 6. Tests Protecting Performance Correctness

Primary files:
- `tests/perf/test_perf_resource.py` — `@pytest.mark.perf`, p95 < 250ms at 1000 entities
- `tests/perf/test_perf_combat.py` — combat tick latency
- `tests/perf/test_perf_metropolis.py` — large-scale tick latency
- `tests/perf/test_perf_idle.py` — idle baseline
- `tests/perf/test_hard_law_monitor_overhead.py` — hard law monitor overhead
- `tests/perf/test_perf_regression_baseline.py` — regression baseline check

## 7. Tests Protecting World Determinism

Primary files:
- `tests/integration/kernel/test_determinism_suite.py` — seed reproducibility (10 runs, identical hashes)
- `tests/integration/kernel/test_long_run_determinism.py` — long-run hash stability
- `tests/integration/kernel/test_executor_determinism.py` — executor-level determinism
- `tests/integration/kernel/test_seed_stability.py` — seed stability across restarts
- `tests/integration/kernel/test_overflow_determinism.py` — determinism under overflow conditions
- `tests/certification/test_world_compile_determinism.py` — world compile produces identical output

## 8. Tests Protecting Combat Legality

Primary files:
- `tests/integration/pipeline/test_combat_legality_matrix.py` — melee adjacency, ranged LOS, AoE, dead-target rejection (Compliance IDs: COMB-283–289)
- `tests/integration/pipeline/test_combat_trust.py` — trust boundary for combat proposals
- `tests/integration/combat/test_relation_combat_integration.py` — relation-based combat

## 9. Tests Protecting Progression Correctness

Primary files:
- `tests/unit/progression/test_leveling.py` — XP-to-level formula
- `tests/unit/progression/test_attribute_growth.py` — attribute growth on level-up
- `tests/unit/progression/test_evolution.py` — evolution point conversion
- `tests/unit/progression/test_breakthroughs.py` — breakthrough events
- `tests/integration/domains/progression/test_phase6_progression_conversion_phase.py` — pipeline-level progression phase

## 10. What Constitutes a Hard Gate (from compliance/checklist.md)

The compliance checklist uses `[x]` / `[ ]` with proof types: `contract`, `regression`, `differential`, `characterization`, `certification`, `E2E`. Key gate-level behaviors (P0) include:
- TOWN-001 to TOWN-008: Authoritative action model (typed intents, update buckets, mutation separation)
- Combat/movement legality laws (COMB-283 to COMB-289, RPG-0012 to RPG-0019)
- Resource conservation (no source mutation without destination receipt)
- Deterministic world hash reproduction (same seed → same hash)

These translate to hard merge gates: any test in `tests/certification/` or `tests/integration/kernel/` covering the above must pass before merge. `tests/perf/` gates are checked against `perf_baseline_policy.md` thresholds (p50 +5%, p95 +10%, p99 +15%).
