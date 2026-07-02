---
status: active
layer: testing
authority: P1
audience: agent
tags: [audit, test-coverage, regression-risk, test-suite-health, determinism]
---

# D10 — Test Coverage & Regression Risk

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | B — Engine Health |
| **State** | `done` |
| **Impact** | 4 / 5 |
| **Interest** | 4 / 5 |
| **Priority** | 7 |
| **Method** | run + classify |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Is the test suite a reliable regression net? Which domains
are well-guarded and which carry hidden regression risk today?

**Related dimensions:** D09 (System Wiring) — several D09 wiring gaps (F2, F3) show up
here as test failures; D15 (Entity Decision Inspection) — cognition snapshot test coverage
of goal-score comparison gap is zero; D17 (Documentation Currency) — inventory slot/weight
default change (D17 uncertain finding) is confirmed here by 4 resource test failures.

---

## Classification Method

Test failures are grouped into root-cause clusters. Each cluster is scored on three dimensions
to produce a Regression Risk score. Higher score = higher priority to remediate.

### Regression Risk Scoring

3 dimensions, each 1–5. Maximum: 15.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Failure Breadth** | 1–3 tests affected | 4–15 tests affected | 16+ tests or cross-domain cascade |
| **Domain Criticality** | Peripheral tooling or lab | Active gameplay domain | Core engine, determinism, or contract |
| **Masking Risk** | Fails loudly in isolation | Requires run ordering or specific mode | Silent logic drift or mode contamination that passes in isolation |

---

## Suite Snapshot

Run: `pytest tests/unit tests/integration` (excludes `tests/scenarios`)

| Metric | Count |
|---|---|
| Test files | 782 |
| Tests collected | 3,292 |
| Passed | 3,150 (95.7%) |
| Failed | 121 |
| Errors | 34 |
| Skipped | 3 |

### Failure Distribution by Domain

| Domain | Failures |
|---|---|
| integration/kernel | 29 |
| integration/observability | 24 |
| unit/core | 18 (teardown errors) |
| unit/resource | 11 |
| integration/standalone | 6 |
| unit/content | 5 |
| unit/combat | 5 |
| integration/optimization | 4 |
| unit/engine | 3 |
| integration/pipeline | 2 |
| integration/worldbuilding | 2 |
| Other (1 each) | 6 |

---

## Key Findings

> **RESOLVED: TCK-20260624-FIX-MOCK-SERIAL, TCK-20260624-FIX-ECONOMY-TESTS, TCK-20260624-FIX-SPAWN-SCHEMA, TCK-20260624-FIX-WORLDASSEMBLY-TESTS, TCK-20260624-FIX-SLOW-MARKERS, TCK-20260624-FIX-CERT-GATE, TCK-20260624-FIX-WORKER-SHUTDOWN, TCK-20260624-FIX-TOOLS-SERVER, TCK-20260624-FIX-STRATEGIC-TESTS, TCK-20260624-FIX-RACE-TESTS, TCK-20260624-PERF-GUARD-INFRA, TCK-20260624-FIX-PERF-BUDGETS (2026-06-24):** All 12 Phase 1–3 repair tickets completed; test suite green.

### F1 — Teardown mode contamination (FallbackRestrictedError) — Risk: 14 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 5 | 34 errors; cascades from core/ into cognition/ across run ordering |
| Domain Criticality | 4 | Core registry/catalog system — foundational to content resolution |
| Masking Risk | 5 | Tests pass in isolation; fail only when run after `catalog_with_compatibility` tests — classic order-dependent contamination |
| **Total** | **14** | |

`tests/unit/core/test_registry_bridge.py` and related files set the global registry mode
to `catalog_with_compatibility` but do not restore the previous mode in teardown.
Subsequent tests that rely on hardcoded content fallback see `FallbackRestrictedError`
at setup time and are counted as errors (not failures).

**Cascade:** 15 setup errors in `tests/unit/cognition/test_phase2_knowledge_model_service.py`
are not caused by the cognition code — they are contamination victims.

**Fix:** Add a `@pytest.fixture(autouse=True)` in `conftest.py` at the `unit/core` level
that saves and restores the global content mode around each test.

---

### F2 — `ItemStack` missing `position` attribute (world_index.py) — Risk: 12 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 5 | 29 integration/kernel failures + 1000-tick determinism timeout |
| Domain Criticality | 5 | `world_index.py` — spatial indexing is core engine infrastructure |
| Masking Risk | 2 | Fails loudly with `AttributeError`; not silent |
| **Total** | **12** | |

`src/engine/world_index.py:151` calls `.position` on an `ItemStack` object.
`ItemStack` does not have a `position` attribute. This breaks spatial indexing
and causes the entire `integration/kernel` suite to fail or time out.

**Why not caught sooner:** `world_index` is used in full-run integration contexts; unit
tests mock the spatial layer. The `ItemStack` model likely changed without updating the
index query path.

---

### F3 — Bare random usage (determinism contract breach) — Risk: 11 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 2 | 2 tests in `test_phase2_determinism.py` |
| Domain Criticality | 5 | Determinism is a P0 engine contract — breaks replay |
| Masking Risk | 4 | Only caught by boundary enforcement tests; raw `random.` calls produce non-deterministic behavior silently during normal simulation runs |
| **Total** | **11** | |

`TestRNGBoundaryEnforcement` scans source for `import random` / `random.` calls
outside `rng.py`. Tests are finding bare random usage. Every such call breaks
deterministic replay for the current tick.

**Risk:** Replay divergence is silent — a run looks correct but produces different
outcomes on re-run. This undermines the core contract in `docs/engine/kernel.md`.

---

### F4 — Inventory capacity defaults diverged — Risk: 10 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 4 | 11 resource + 2 pipeline failures = 13 tests |
| Domain Criticality | 3 | Economy/resource domain — gameplay-critical but not engine core |
| Masking Risk | 3 | Some failures are INVENTORY_FULL masking INSUFFICIENT_GOLD — wrong ReasonCode means silent logic divergence in error handling |
| **Total** | **10** | |

Inventory slot or weight defaults changed. Tests still expect old values:
- `test_inventory_limits`: expects 5 slots, gets 10
- `test_inventory_hardening`: expects 2 items at limit, gets 3
- `test_crafting_succeeds_with_freed_space`: `INVENTORY_FULL` raised unexpectedly
- `test_insufficient_gold_records_reason` (integration/pipeline): returns `INVENTORY_FULL` where `INSUFFICIENT_GOLD` expected

The `ReasonCode` mismatch is particularly risky — upstream callers branch on reason code.

**Connected to D17:** D17 flagged inventory slot/weight defaults as an uncertain finding.
This confirms the defaults changed and tests were not updated.

---

### F5 — Kernel phase contract broken (milestones A/B) — Risk: 10 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 2 | 2 milestone closure tests |
| Domain Criticality | 5 | Kernel phase orchestration and runtime mode are P0 contracts |
| Masking Risk | 3 | Milestone closure tests are explicit; not silent |
| **Total** | **10** | |

Two governance gate tests fail:
- **Milestone A**: `Kernel.tick_once` does not orchestrate `_phase_init`. This phase
  is mandatory per `docs/engine/kernel.md` (6-phase loop: Init → Governance → Scheduling
  → Packetization → Resolution → Persistence).
- **Milestone B**: runtime mode is `SURVIVAL` where `DEGRADED` expected. The watchdog
  governance threshold changed or the mode transition logic regressed.

---

### F6 — Content registry drift (3 new pack YAMLs) — Risk: 7 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 2 | 2–3 test failures; 1 ValueError on strict load |
| Domain Criticality | 2 | Content registry tooling — does not affect runtime simulation |
| Masking Risk | 3 | `repository.py:353` raises on strict load; easy to miss when adding pack files |
| **Total** | **7** | |

3 YAML files exist in `data/content/` but are not registered in `ContentUsageMatrix`:
`compatibility/migration_map.yaml`, `packs/swamp_border_pack.yaml`,
`packs/frontier_extended_pack.yaml`. The strict-load path raises `ValueError`.

**Fix:** Register the 3 new families in `ContentUsageMatrix` or confirm they are
intentionally draft (and gate them behind a non-strict load flag).

---

### F7 — Combat reward trace label mismatch — Risk: 8 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 2 | 3 tests in `test_combat_reward_trace.py` |
| Domain Criticality | 3 | Combat reward sourcing — affects XP/reward attribution |
| Masking Risk | 3 | Tests catch the mismatch; but callers checking `source` string elsewhere may silently disagree |
| **Total** | **8** | |

Reward source label constants renamed. Tests expect:
- `hostile_relation` → actual: `relation_projection`
- `hero_kill` category missing

**Risk:** Any code path that branches on `reward.source == "hostile_relation"` will
silently skip the branch after this rename if not caught by a test.

---

### F8 — Test isolation: mutation lab folder — Risk: 7 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 1 | 1 test |
| Domain Criticality | 2 | Lab tooling — not production simulation |
| Masking Risk | 4 | `FileExistsError` only fires if prior test run left state; passes on a clean environment — environment-dependent flake |
| **Total** | **7** | |

`test_mutation_lab_orchestrator.py` fails with `FileExistsError` on
`data/mutation_labs/test_mutlab_run/` if a previous run was not cleaned up.

**Fix:** Add cleanup in test teardown (or `tmp_path` fixture).

---

### F9 — NormalizedWorldModule constructor drift — Risk: 5 / 15

| Dimension | Score | Reason |
|---|---|---|
| Failure Breadth | 1 | 3 tests in same file |
| Domain Criticality | 2 | World module tooling |
| Masking Risk | 2 | `TypeError` is loud and immediate |
| **Total** | **5** | |

`schema_version` kwarg passed in `test_reference_graph.py` is no longer accepted
by `NormalizedWorldModule.__init__`. Field was removed or renamed. Easy fix.

---

### Regression Risk Summary

| Finding | Description | Risk Score |
|---|---|---|
| F1 | Teardown mode contamination (FallbackRestrictedError) | **14 / 15** |
| F2 | ItemStack missing position attribute | **12 / 15** |
| F3 | Bare random usage (determinism breach) | **11 / 15** |
| F4 | Inventory capacity defaults diverged | **10 / 15** |
| F5 | Kernel phase contract broken (milestones A/B) | **10 / 15** |
| F7 | Combat reward trace label mismatch | **8 / 15** |
| F6 | Content registry drift (3 new pack YAMLs) | **7 / 15** |
| F8 | Test isolation: mutation lab folder | **7 / 15** |
| F9 | NormalizedWorldModule constructor drift | **5 / 15** |

---

## Coverage Strength Assessment

### Well-covered domains (0 failures)

| Domain | Files | Assessment |
|---|---|---|
| unit/strategic | 41 | AI/goal hierarchy — stable and broad |
| unit/observability | 81 | Unit-level observability — largest test domain, fully green |
| unit/world | 33 | World state reads — stable |
| unit/movement | 10 | Movement logic — stable |
| unit/domains | 78 | Domain logic — 1 integration failure, unit clean |
| unit/worldbuilding | 10 | Worldbuilding unit — stable |
| unit/social | 20 | Social events — 1 isolated failure |

### Coverage gaps (structural)

| Gap | Description |
|---|---|
| `src/api/routes/` | No test files for HTTP route layer (confirmed by D15 gap analysis) |
| `tests/scenarios/` | Excluded from this run; separate run required |
| Coverage percentage | Not measured — no instrumentation run executed |
| Cognition goal scoring | Zero tests verify goal-score comparison (D15 Gap 1) |
| BehaviorTimeline REST | No test for `/behavior-timeline` endpoint (doesn't exist yet — D15 Gap 5) |

---

## Recommended Follow-Up Tickets

| Priority | Action | Root Cause |
|---|---|---|
| **P0** | Fix `ItemStack.position` AttributeError in `world_index.py:151` | F2 — blocks 29+ kernel tests |
| **P0** | Eliminate bare random calls outside `rng.py` | F3 — determinism contract violation |
| **P0** | Fix kernel phase contract: restore `_phase_init` + runtime mode threshold | F5 — milestone governance gate |
| **P1** | Add teardown fixture to reset global content mode after catalog tests | F1 — blocks cognition test suite |
| **P1** | Reconcile inventory slot/weight defaults; update tests or revert defaults | F4 — INVENTORY_FULL/INSUFFICIENT_GOLD mismatch |
| **P1** | Register 3 new pack YAMLs in ContentUsageMatrix | F6 |
| **P1** | Update combat reward source label constants in tests | F7 |
| P2 | Add `tmp_path` teardown to mutation lab test | F8 |
| P2 | Remove `schema_version` kwarg from `test_reference_graph.py` | F9 |
| P2 | Add HTTP route layer test coverage for `src/api/routes/` | Coverage gap |

---

## Related Dimensions

- **D09 (System Wiring)** — F2 (`ItemStack.position`) and F4 (inventory defaults) are wiring gaps confirmed here as test failures.
- **D15 (Entity Decision Inspection)** — cognition snapshot test coverage of goal-score comparison gap is zero; no tests verify the missing WHY data.
- **D17 (Documentation Currency)** — inventory slot/weight default change (D17 uncertain) confirmed here by 4 resource failures and 2 pipeline failures.
- **D02 (Foundation Features)** — determinism (F3) and kernel phase contract (F5) are P0 foundation features; failures here indicate regression against that baseline.
