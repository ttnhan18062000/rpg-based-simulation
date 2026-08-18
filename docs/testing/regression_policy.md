---
status: active
layer: testing
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Regression Policy

**Related docs:**
- `docs/testing/test_taxonomy.md` — marker definitions (`regression`, `v2_contract`, `differential`, etc.)
- `docs/testing/requirement_traceability.md` — which tests protect which requirements
- `docs/testing/how_to_add_requirement_tests.md` — how to add a test after fixing a regression
- `docs/performance/perf_baseline_policy.md` — numeric performance regression thresholds
- `docs/parity_ledger/` — P0 law parity evidence; must be updated when a P0 test changes

---

## 1. What Is a Regression?

A **regression** is a test failure caused by a code change that broke behavior that was previously correct and protected. It is not:
- A test failure caused by an intentional behavior change that was planned and documented.
- A test failure caused by a flawed test that never correctly described the system.
- A pre-existing failure that existed before the current change was made.

**Key distinction:** if a test correctly described system law and it now fails, that is a regression until proven otherwise. The burden of proof is on the developer claiming "this is an intentional change," not on the reviewer.

---

## 2. Hard Gates — Block Merge on Failure

These test groups must pass on every commit. A failure in any of them blocks merge.

| Test Group | Location | Requirement Groups Protected | Rationale |
|---|---|---|---|
| Certification suite | `tests/certification/` | World determinism, kernel stability, long-run stability | Final smoke gate; covers full engine runs |
| Kernel determinism | `tests/integration/kernel/test_determinism_suite.py`, `test_long_run_determinism.py`, `test_seed_stability.py`, `test_overflow_determinism.py` | World determinism (P0) | Determinism is non-negotiable; any non-determinism corrupts replay and debugging |
| World compile determinism | `tests/certification/test_world_compile_determinism.py` | World determinism (P0) | World assembly must be reproducible |
| Authoritative pipeline | `tests/integration/pipeline/test_mutation_boundary.py`, `test_no_hidden_mutation.py`, `test_rejection_audit.py`, `test_transaction_completion.py` | Resource conservation, authoritative mutation boundary (P0) | Core engine contract; mutation outside the apply path corrupts world state |
| Resource conservation | `tests/integration/kernel/test_resource_conservation.py`, `test_resource_conservation_v2.py` | Resource conservation (P0) | Atomic conservation law must not regress |
| Combat legality | `tests/integration/pipeline/test_combat_legality_matrix.py`, `test_combat_trust.py` | Combat legality (P0) | Illegal combat outcomes corrupt game state and replay |
| API security | `tests/api/test_cognition_history_api.py` (path-traversal test), `tests/api/test_historical_event_search_api.py` (security sanitization test) | API security (P0) | Path traversal is a security gate, not just a correctness gate |
| Architecture guards | `tests/architecture/` | Import boundaries, enum migration, hot-path safety | Boundary violations create hidden coupling that degrades future changes |

**Performance gates** (from `docs/performance/perf_baseline_policy.md`):
- p50 latency must not exceed baseline by more than **5%**
- p95 latency must not exceed baseline by more than **10%**
- p99 latency must not exceed baseline by more than **15%**
- RSS delta between tick 100 and tick 1000 must not exceed **15%** of starting baseline

A performance gate failure raises `UnacceptableRegressionError` and blocks CI. See `docs/performance/perf_baseline_policy.md` §3 for full details.

---

## 3. Soft Monitors — Alert Only

These test groups are important but do not block merge on failure. Failures are tracked as P1 or P2 issues.

| Test Group | Location | Reason for Soft Status |
|---|---|---|
| Live observability tests | `tests/api/test_live_health_api.py`, `tests/api/test_live_observability_status.py` | Require a running server; environment-dependent; failures indicate deployment issues, not code regressions |
| Integration observability flows | `tests/integration/observability/` (phase20–28, warehouse, streams) | Exercising telemetry pipelines that are infrastructure-dependent |
| Scenario tests | `tests/scenarios/`, `tests/certification/test_cert_long_run_stability.py` | Long-running; infrastructure-sensitive; failures are investigated but don't block fast iteration |
| Performance perf suite (non-gate scenarios) | `tests/perf/test_perf_metropolis.py`, `test_perf_idle.py`, `test_perf_stress.py` | Benchmarks that measure but do not enforce thresholds (advisory only) |
| World-assembly integration | `tests/integration/content/`, `tests/unit/worldassembly/` | Content pipeline; failures are tracked per `docs/testing/test_taxonomy.md` `worldassembly` ownership |
| Performance-threshold assertions | `tests/perf/`, `tests/arena/`, performance-only assertions in `tests/certification/` (e.g. `test_cert_long_run_stability.py`'s resource/latency-drift flags) | **TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING** (temporary stopgap): right-sizing a hard-coded performance threshold against real, variable CI hardware is an ongoing engine-performance-engineering problem, not a one-time test-fixing pass — see `docs/engine/performance_contract.md` Hardware Classes A/B/C. A threshold miss emits `tests/tools/perf_assertions.PerformanceThresholdWarning` (visible in pytest's `-rw` warnings summary, with actual value/limit/test id) instead of failing the test. Correctness checks (hash/state equality, invariants, gate-logic unit tests) that happen to live in these directories stay hard failures — see `tests/tools/perf_assertions.py`'s module docstring and the ticket's Assumptions/Open Questions for the revisit condition. This is explicitly temporary, not a permanent downgrade. |

---

## 4. Regression vs Expected Behavior Change

Use this decision tree when a test fails:

```
Test fails after a code change
        │
        ├─ Was the behavior change intentional and planned?
        │       ├─ YES → Is it documented in docs/guidelines/intentional_divergences.md?
        │       │           ├─ YES → Update the test to match new behavior. Update parity ledger if P0.
        │       │           └─ NO  → Stop. Document the divergence first, then update the test.
        │       │
        │       └─ NO  → This is a regression. Fix the code, not the test.
        │
        └─ Was the test correct before the change?
                ├─ YES → Regression. Revert or fix the change.
                └─ NO  → The test was flawed. Fix the test AND add a correct replacement.
                          Never delete a requirement test without a replacement.
```

**Signs a failing test is a real regression:**
- The test name includes a law ID (e.g., `COMB-283`, `RPG-0012`, `TOWN-001`)
- The test is in `tests/certification/` or `tests/integration/kernel/`
- The assertion checks an invariant (e.g., "source not mutated", "hash identical")
- The test has been passing for multiple releases

**Signs a failing test may need updating (not a regression):**
- The test was added for a specific implementation detail that was intentionally refactored
- The test is marked `@pytest.mark.intentional_divergence`
- There is a corresponding parity ledger entry with `status: divergent` already filed

---

## 5. Triage Checklist for a Failing Gate Test

When a hard gate test fails, follow these steps in order:

1. **Identify the requirement group.** Look up the failing test file in `docs/testing/requirement_traceability.md`. What law or requirement does it protect?

2. **Check the compliance checklist.** Find the relevant item in `docs/compliance/checklist.md`. Is it marked `[x]` with a `TEST:` path? Does the failing test match the cited proof?

3. **Check the parity ledger.** Find the relevant entry in `docs/parity_ledger/` for the subsystem. Is `status: verified` or `status: divergent`? If `divergent`, was this expected?

4. **Read the Mechanics Bible chapter.** For resource conservation: `docs/mechanics/03_economic_laws.md`. For combat: `docs/mechanics/02_combat_laws.md`. For world: `docs/mechanics/05_world_evolution.md`. Confirm whether the test is asserting the correct law.

5. **Bisect the change.** Run `git log --oneline -20` and identify which commit introduced the failure. Does the commit message reference an intentional divergence?

6. **Check for a filed divergence.** If the change was intentional, it must appear in `docs/guidelines/intentional_divergences.md`. If it does not appear there, the change is unauthorized.

7. **Decision:**
   - Code broke the law → revert or fix the code.
   - Intentional change, divergence filed → update test to match new behavior. Update parity ledger in the same session.
   - Test was always wrong → fix the test, add a correct replacement, and file a note in the ticket.

---

## 6. When a Test Can Be Updated vs When It Signals a Real Regression

| Situation | Action |
|---|---|
| Test checks an implementation detail that was legitimately refactored with no behavior change | Update the test. The assertion should check the same invariant through the new interface. |
| Test checks a behavior that was intentionally changed and the change is filed in `intentional_divergences.md` | Update the test to assert the new behavior. Update parity ledger entry in the same session. |
| Test checks a simulation law (P0) and the law was not intentionally changed | **Do not update the test.** Fix the code. |
| Test has been flaky (non-deterministic failures) for more than one session | File a P1 issue, mark the test `@pytest.mark.xfail(strict=False, reason="flaky: <ticket>")`, and investigate root cause before removing the xfail. |
| Test was written for a feature that has been removed | Move the test to `tests/scratch/` or delete with a comment in the commit message. Never silently delete a P0 test. |

---

## 7. Authority to Update a P0 Test

A **P0 test** is any test that protects a P0 requirement (see `docs/testing/requirement_traceability.md` — authority column).

**Rules:**
- A P0 test can only be updated when there is a filed intentional divergence in `docs/guidelines/intentional_divergences.md` that explicitly covers the behavior being changed.
- The parity ledger entry for the affected subsystem (`docs/parity_ledger/`) must be updated in the same session — `status`, `v2_evidence`, and `divergence_note`.
- The `docs/compliance/checklist.md` entry for the affected law must be updated if the proof path changes.
- The ticket closing the change must list all three: divergence doc, parity ledger entry, and checklist item.

**Who has authority:** Any contributor may propose a P0 test change. It requires explicit acknowledgment from a reviewer who has read the three supporting documents above. An automated agent implementing a ticket must record the parity ledger update as a verified step before closing the ticket.

---

## 8. Performance Regression Thresholds

Performance regression thresholds are defined in `docs/performance/perf_baseline_policy.md` §3. Summary:

| Metric | Gate threshold |
|---|---|
| p50 tick latency | Must not exceed baseline by > 5% |
| p95 tick latency | Must not exceed baseline by > 10% |
| p99 tick latency | Must not exceed baseline by > 15% |
| RSS delta (tick 100 → 1000) | Must not exceed 15% of starting baseline |

If a performance gate fires due to a legitimate architectural change, follow the baseline re-calibration procedure in `docs/performance/perf_baseline_policy.md` §4 before merging.
