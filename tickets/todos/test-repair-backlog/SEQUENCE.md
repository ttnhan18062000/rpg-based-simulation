# Test Repair Backlog — Implementation Sequence

Investigation date: 2026-06-24  
Total tickets: 12  
Prerequisite: none (this is a standalone repair batch)

## Key decisions from investigation

| Question | Decision |
|---|---|
| Race condition locking bug? | **No — test setup bug.** `max_slots=10` vs `quantity=50`. Locking code is correct. |
| Economy drift: fix code or tests? | **Fix tests.** `TCK-20260619-E33D-REP-DISCOUNTS` correctly added 10% rep discount; tests predate it. |
| 5 thread-leak teardown ERRORs | **Cascade from FIX-MOCK-SERIAL.** Those 5 tests don't create Kernels — the 7 MagicMock tests do and never shut them down. Fix MOCK-SERIAL; teardown errors clear automatically. |
| Performance: fix code or tests? | **Mixed.** AdventureDecisionPhase is a real 3x regression → fix code. All others: ad-hoc thresholds, no sampling → update tests. |
| Spawn table schema | **Extend schema** (new `ClassTableDefinition`). Data is intentional and newer. |
| Duplicate tests? | **None requiring action.** Parallel unit/integration structures only. |

---

## Phase 1 — P1 (unblock green-suite guarantee)

These four are independent of each other and can be run in any order within the phase,
but all should land before Phase 2.

```
1. TCK-20260624-FIX-MOCK-SERIAL         (standard)
   Fix: add rng.get_state.return_value to 7 MagicMock Kernel tests + add shutdown()
   Clears: 7 failures + 5 cascading teardown ERRORs
   Depends on: nothing

2. TCK-20260624-FIX-ECONOMY-TESTS       (hotfix)
   Fix: update test assertions to post-rep-discount prices (or use rep=0.0 entities)
   Clears: 6 failures
   Depends on: nothing

3. TCK-20260624-FIX-SPAWN-SCHEMA        (standard)
   Fix: add ClassTableDefinition schema for class_id_by_role record type
   Clears: 1 failure (test_strict_load_on_real_content_dir) + possible cascade in worldbuilding
   Depends on: nothing

4. TCK-20260624-FIX-WORLDASSEMBLY-TESTS (hotfix)
   Fix: test data — use valid module IDs in CLI test; add type field to quest dicts
   Clears: 3–4 failures
   Depends on: TCK-20260624-FIX-SPAWN-SCHEMA (run after to confirm cascade is gone)
```

---

## Phase 2 — P2 infra + cert

```
5. TCK-20260624-FIX-SLOW-MARKERS        (hotfix)
   Fix: add @pytest.mark.slow to 3 cert long-run tests + CLI test
   Note: re-check test_pause_sets_flag AFTER FIX-MOCK-SERIAL lands — it may clear
   Depends on: TCK-20260624-FIX-MOCK-SERIAL (confirm pause test clears first)

6. TCK-20260624-FIX-CERT-GATE           (hotfix)
   Fix: register CERT domain in scripts/release_gate.py (or rename RPG-CERT-001/002)
   Depends on: nothing

7. TCK-20260624-FIX-WORKER-SHUTDOWN     (hotfix)
   Fix: add kernel.shutdown() teardown to test_worker_harden.py
   Depends on: nothing

8. TCK-20260624-FIX-TOOLS-SERVER        (standard)
   Fix: graceful-degradation exit codes in knowledge_search.py; .mcp.json absolute path;
        TestClient lifespan monkeypatch timing
   Depends on: nothing
```

---

## Phase 3 — P2 gameplay + perf

```
9. TCK-20260624-FIX-STRATEGIC-TESTS     (hotfix)
   Fix: ServiceRegistry fixture, target_node_id setup, ItemRegistry init
   Depends on: nothing

10. TCK-20260624-FIX-RACE-TESTS          (hotfix)
    Fix: increase max_slots (or reduce quantity) in create_mock_entity()
    Depends on: nothing

11. TCK-20260624-PERF-GUARD-INFRA        (standard)  ← NEW infrastructure
    Build: perf_baselines.json + perf_budget fixture + tools/perf_guard.py + make perf-measure
    Depends on: nothing (but Phase 1 should be green first for clean baseline measurements)

12. TCK-20260624-FIX-PERF-BUDGETS        (standard)
    Fix: AdventureDecisionPhase regression (code fix) + migrate all perf tests to perf_budget
         fixture + populate perf_baselines.json with measured values
    Depends on: TCK-20260624-PERF-GUARD-INFRA (HARD DEPENDENCY — must complete first)
```

---

## Dependency graph

```
FIX-MOCK-SERIAL ──────────────────────────────► FIX-SLOW-MARKERS (re-check pause test)
FIX-SPAWN-SCHEMA ────────────────────────────► FIX-WORLDASSEMBLY-TESTS (confirm cascade)
PERF-GUARD-INFRA ────────────────────────────► FIX-PERF-BUDGETS (hard prerequisite)

All others: no inter-ticket dependencies
```

---

## Expected outcome

After all 12 tickets:
- All P1 failures cleared (~18 tests + 5 teardown ERRORs)
- All remaining P2 failures cleared (~29 tests)
- `pytest tests/ -m "not slow"` approaches ~4,850 passing with no failures
- `make perf-measure` workflow established for all future perf-affecting tickets
