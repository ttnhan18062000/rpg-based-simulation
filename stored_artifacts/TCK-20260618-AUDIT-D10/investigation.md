---
ticket_id: TCK-20260618-AUDIT-D10-TESTS
type: investigation
date: 2026-06-18
---

# D10 Investigation — Test Coverage & Regression Risk

## Test Suite Scope

Run: `pytest tests/unit tests/integration` (excludes `tests/scenarios`)

| Metric | Value |
|---|---|
| Test files | 782 |
| Tests collected | 3,292 |
| Passed | 3,150 |
| Failed | 121 |
| Errors | 34 |
| Skipped | 3 |

## Domain File Distribution

| Domain | Test Files |
|---|---|
| unit/observability | 81 |
| unit/domains | 78 |
| unit/core | 44 |
| unit/strategic | 41 |
| integration/observability | 39 |
| unit/world | 33 |
| integration/kernel | 26 |
| unit/social | 20 |
| unit/lab | 18 |
| unit/resource | 17 |
| unit/kernel | 17 |
| unit/combat | 17 |
| unit/optimization | 16 |
| integration/scenarios | 16 |
| integration/pipeline | 16 |
| unit/progression | 12 |
| unit/content | 12 |
| unit/worldbuilding | 10 |
| unit/movement | 10 |
| integration/lab_agent | 9 |
| integration/domains | 9 |
| unit/quest | 8 |
| unit/worldassembly | 7 |
| unit/engine | 7 |
| unit/campaigns | 7 |
| unit/perf | 6 |
| unit/lab_agent | 6 |
| unit/entity | 6 |
| integration/worldassembly | 6 |
| integration/optimization | 6 |
| unit/cognition | 5 |
| integration/world | 5 |
| integration/lab | 5 |
| integration/content | 5 |

## Failure Distribution

| Domain | Failed Tests |
|---|---|
| integration/kernel | 29 |
| integration/observability | 24 |
| unit/core | 18 (errors) |
| unit/resource | 11 |
| unit/content | 5 |
| unit/combat | 5 |
| integration/optimization | 4 |
| unit/engine | 3 |
| integration/pipeline | 2 |
| integration/worldbuilding | 2 |
| integration/standalone | 6 |
| unit/worldgeneration | 1 |
| unit/worldassembly | 1 |
| unit/social | 1 |
| unit/progression | 1 |
| integration/world | 1 |
| integration/lab | 1 |

## Root Cause Clusters

### Cluster 1 — Teardown contamination (FallbackRestrictedError)
34 errors. Tests in `test_registry_bridge.py` and `test_catalog_*.py` put global registry into
`catalog_with_compatibility` mode and do not reset it in teardown. Subsequent tests that rely on
hardcoded content fallback see `FallbackRestrictedError` at setup time.
Files: `tests/unit/core/test_registry_bridge.py`, `test_catalog_fallback.py`,
`test_catalog_smoke_simulation.py`, `test_registry_cross_reference.py`, `test_registry_parity.py`
→ cascades into `tests/unit/cognition/test_phase2_knowledge_model_service.py` (15 setup errors)

### Cluster 2 — ItemStack missing position attribute
`src/engine/world_index.py:151` — `ItemStack.position` does not exist on `ItemStack`.
Causes `AttributeError` during spatial indexing. 21+ integration/kernel tests fail or
time out as a result (including `test_1000_tick_determinism`).

### Cluster 3 — Bare random usage (determinism breach)
`test_phase2_determinism.py` boundary enforcement tests find raw `random.` calls outside
`rng.py`. Two tests fail; the actual offending files are listed in the assertion output.
This is a P0 engine contract violation — breaks deterministic replay.

### Cluster 4 — Kernel phase contract broken (milestones A/B)
- Milestone A: `Kernel.tick_once` does not orchestrate `_phase_init`.
- Milestone B: runtime mode is `SURVIVAL` where `DEGRADED` is expected.
Both are milestone closure contract tests introduced as governance gates.

### Cluster 5 — Inventory capacity defaults diverged
Slot/weight defaults changed without updating tests.
- `test_inventory_limits`: expects 5 slots, gets 10
- `test_inventory_hardening`: expects 2 items, gets 3
- `test_crafting_succeeds_with_freed_space`: INVENTORY_FULL unexpectedly raised
- Economy tests: `shop_stock_depletion`, `arbitrage_prevention` → functions return None

### Cluster 6 — Content registry drift (new pack YAMLs)
3 new YAML files added to `data/content/` without registering in `ContentUsageMatrix`:
`compatibility/migration_map.yaml`, `packs/swamp_border_pack.yaml`,
`packs/frontier_extended_pack.yaml`.
`src/content/repository.py:353` raises `ValueError` on strict load.

### Cluster 7 — Combat reward trace label mismatch
Reward source label constants have been renamed; tests still expect old names:
- `relation_projection` expected to be `hostile_relation`
- `hero_kill` category missing or renamed

### Cluster 8 — NormalizedWorldModule constructor drift
`schema_version` kwarg passed by test not accepted by current `NormalizedWorldModule.__init__`.
3 reference graph tests affected.

### Cluster 9 — ReplayManager pressure report budget values
`test_resource_budget_gate.py` expects specific budget values (5.0, 3.0, None) but
`ReplayManager` returns 2.0 across all cases. Likely interface change.

### Cluster 10 — Test isolation: mutation lab folder
`test_mutation_lab_orchestrator.py` fails with `FileExistsError` if a prior run left
`data/mutation_labs/test_mutlab_run/`. Environment-dependent flaky failure.

### Cluster 11 — CI gate returning WARNING not PASS
`test_scenario_level_report_flow.py` expects `CI Gate Evaluation Result: PASS` but
gets `WARNING`. Gate thresholds or scoring logic changed.

## Well-Covered Domains (0 failures)
- unit/strategic (41 files) — AI/goal hierarchy appears stable
- unit/observability (81 files) — unit-level observability stable
- unit/world (33 files) — world state reads stable
- unit/movement (10 files) — movement logic stable
- unit/worldbuilding (10 files) — worldbuilding unit stable
- unit/domains (78 files) — domain logic largely stable (1 integration/domains failure)

## Coverage Gaps (Structural)
- No test files for `src/api/routes/` HTTP layer (D15 noted no BehaviorTimeline endpoint)
- `tests/scenarios` directory not included in this run (separate run required)
- Coverage% not measured — no instrumentation run executed
