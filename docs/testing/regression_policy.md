---
status: active
layer: testing
authority: P1
audience: agent
last_verified: 2026-08-30
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
| Live observability tests | `tests/api/test_live_health_api.py`, `tests/api/test_live_observability_status.py` | Require a running server; environment-dependent; failures indicate deployment issues, not code regressions — **except** a 401/403 response, which means the test's own `subprocess.Popen` server env is missing a valid `RPG_API_KEY_HASHES` entry (see `docs/architecture/http_api_key_authentication.md`), a test-config gap, not a deployment issue. `TCK-20260823-LIVE-TEST-API-KEY-AUTH` fixed this file set once already after two prior tickets misdiagnosed the same 401/403 failures as this row's generic "environment-dependent" case. |
| Integration observability flows | `tests/integration/observability/` (phase20–28, warehouse, streams) | Exercising telemetry pipelines that are infrastructure-dependent |
| Scenario tests | `tests/scenarios/`, `tests/certification/test_cert_long_run_stability.py` | Long-running; infrastructure-sensitive; failures are investigated but don't block fast iteration |
| Performance perf suite (non-gate scenarios) | `tests/perf/test_perf_metropolis.py`, `test_perf_idle.py`, `test_perf_stress.py` | Benchmarks that measure but do not enforce thresholds (advisory only) |
| World-assembly integration | `tests/integration/content/`, `tests/unit/worldassembly/` | Content pipeline; failures are tracked per `docs/testing/test_taxonomy.md` `worldassembly` ownership |
| Performance-threshold assertions | `tests/perf/`, `tests/arena/`, performance-only assertions in `tests/certification/` (e.g. `test_cert_long_run_stability.py`'s resource/latency-drift flags) | **TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING** (temporary stopgap): right-sizing a hard-coded performance threshold against real, variable CI hardware is an ongoing engine-performance-engineering problem, not a one-time test-fixing pass — see `docs/engine/performance_contract.md` Hardware Classes A/B/C. A threshold miss emits `tests/tools/perf_assertions.PerformanceThresholdWarning` (visible in pytest's `-rw` warnings summary, with actual value/limit/test id) instead of failing the test. Correctness checks (hash/state equality, invariants, gate-logic unit tests) that happen to live in these directories stay hard failures — see `tests/tools/perf_assertions.py`'s module docstring and the ticket's Assumptions/Open Questions for the revisit condition. This is explicitly temporary, not a permanent downgrade. |
| Zero-invocation skill-staleness assertions | `tests/tools/test_generate_retro.py::test_backend_testing_post_fix_state_not_currently_flagged`, `::test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` | **TCK-20260819-SKILL-STALENESS-SOFT-WARNING**: these 2 tests cross-reference the real `.claude/skills/*/SKILL.md` catalog against real `agent-monitoring/data/YYYY-Www/tools.jsonl` invocation history via `compute_zero_invocation_skill_flags()` (`tools/agent-monitoring/generate_retro.py`) — whether a domain-specific skill accrues a real invocation depends on which PRs happen to land, not something a test author or CI can force, and a skill's grace-period expiry is purely calendar-driven. A flag miss emits `tests/tools/skill_staleness_assertions.SkillStalenessWarning` (visible in pytest's `-rw` warnings summary, with the flagged skill name(s), grace period, and test id) instead of failing the test. The other 9 tests in the same "zero invocation" test group (synthetic `tmp_path` fixtures and source-inspection guards on `compute_zero_invocation_skill_flags()` itself) stay hard failures — see `tests/tools/skill_staleness_assertions.py`'s module docstring. Unlike the Performance-threshold row above, this is a durable, open-ended soft monitor, not a temporary stopgap: there is no single future engineering event that converts it back to hard — a skill's real-invocation signal is corpus- and calendar-driven, and some tracked skills may legitimately never accrue a real invocation by design. It self-clears per skill once that skill records a real invocation or stays within grace period. |

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

---

## 9. TCK-20260824/TCK-20260828 Re-Baseline (Worked Example)

Concrete worked example of §6's "hardcoded test baseline that this session's own legitimate change caused to drift" row: `TCK-20260824-TOWN-CENTER-POINTER-FIX` made entities correctly navigate to the real compiled town location (previously they never reached a real town — they navigated to `(0,0)` or two hardcoded fake waypoints). This genuinely, correctly increases combat/hazard exposure for several corpus worlds, tripping `tests/unit/worldassembly/test_corpus_diversity.py`'s hardcoded population-stability and grade-stability floors — the pre-fix "passing" state of those floors was itself an artifact of the pointer bug, not evidence of genuine balance.

`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH` re-verified all 13 tests the fix's own Test-gate disclosed as failing, using real Kernel-driven runs (not guessed values), and found the "all 13 are floor drift" assumption held for only 3 of them:

- **Genuinely re-baselined** (3 tests): real floor/tolerance drift, confirmed via multiple independent evidence batches per this file's own established tolerance-band methodology (see `test_corpus_diversity.py`'s own module docstring §5 for the full per-test evidence and derivation).
- **NOT touched, deferred to follow-up tickets** (10 tests): each failed for a reason a floor value cannot fix — a real, pre-existing, unrelated `src/` bug (`TCK-20260829-LIFECYCLE-HEIRLOOM-INVENTORY-TUPLE-TYPEERROR`, fixed) and a test-invocation resource-budget cap masking a real observability-backpressure issue (`TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION`, resolved: relocated `ReplayManager._rotate_chunk()`'s redundant synchronous budget-check pre-check into the already-async `_execute_persistence()`, batched `QualityPersistence.write()`/`EventRecorder._write_envelope_to_file()` from per-record `flush()` to a deterministic batch-of-50, and added a `resource_budget_large` pytest marker forcing `--resource-budget large` for the 6 affected tests regardless of CLI default. 5 of the 6 now pass; the 6th, `test_urban_political_seed42_1000t_social_grade_stability`, completes without `CalibrationIntegrityError`/`TimeoutError` — confirming the backpressure root cause is fixed — but surfaces a genuine, separately-scoped SOCIAL floor/tolerance drift (`mean_score=36.8373` vs. `anchor_score=15.45`, tolerance `abs_floor=6.5052`) needing its own re-baseline follow-up ticket, left unmodified here per Gate Integrity). Force-fitting a floor edit onto a crash or a timeout would have been a Gate Integrity violation — no threshold value makes a `TypeError` or a `TimeoutError` pass.

**Lesson for future re-baseline tickets**: before re-baselining any failing test after a legitimate upstream fix, verify with a fresh, isolated re-run *why* it is failing — a batch of assertion failures after a real code change is not guaranteed to be homogeneous. Some may be genuine floor drift (re-baseline-able); others may be unrelated bugs or environment/resource limits that a floor edit cannot fix and that deserve their own ticket instead.

---

## 10. TCK-20260824-ROLLOUT-FLAG-DECISIONS / TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE Re-Baseline (Worked Example)

A second, directly analogous worked example to §9, this time for `tests/simulation_quality/test_grade_regression.py`'s `FAST_ANCHOR_KEYS` corpus against `tests/simulation_quality/fixtures/grade_anchors.json`, triggered by the M1 batch's feature-flag rollout rather than a pointer-navigation fix.

**Trigger**: `TCK-20260824-ROLLOUT-FLAG-DECISIONS` flipped `ENABLE_BELIEF_ASSIMILATION` and `ENABLE_SOCIAL_COOPERATION` to `FeatureMode.ON` (`src/domains/optimization/feature_flags.py:37,52`). This is a legitimate, already-approved behavior change, not a bug — but it made previously-dormant cooperation and belief-assimilation content fire for real every tick, which correctly and predictably drifted `FAST_ANCHOR_KEYS`' hardcoded score anchors away from their pre-flip values. A fresh full fast-tier engine re-run found **61/61 `FAST_ANCHOR_KEYS` failing** `test_grade_within_anchor_band`, spanning 211 failing `(run_key, pillar)` combos across the 61 run_keys.

**Root cause, per §6's decision tree**: re-verifying each of the 211 failing combos individually (not blanket-assuming all 211 were flip-caused) found only **80 were genuinely new (uncovered) drift** — the other 131 were pre-existing, M1-unrelated structural noise already classified by `tools/simq_ceiling.py` (118 `tick_budget`, 9 `flag_gated`, 3 `watchdog_variance`, 1 `corrected`). Of the 80 real combos:

- **Dominant driver — SOCIAL (50/50 uncovered) and COGNITION (5/5 uncovered)**: both traced directly to the same flag flip. `CooperationPhase.execute()` (`src/domains/cooperation/phase.py:35-141`) now runs its cooperation pipeline live instead of no-op, moving all 50 SOCIAL combos upward (anchor mostly near-zero/moderate → actual materially higher), all within the ±1 letter band (score-tolerance-only failures, a magnitude shift not a qualitative regression). COGNITION's 5 combos show the identical "dormant → live" signature via `belief_updated` events now scoring in `src/simulation_quality/scorers/cognition.py:52-68` once `ENABLE_BELIEF_ASSIMILATION` allows updates through.
- **Secondary drivers**: AGENCY (12/12 uncovered, anchor=0.000 → small consistent nonzero actual, same cooperation-wiring downstream effect via `EntityUpdate` mutations, traced with high confidence but not line-level certainty) and PROGRESSION/ECONOMY (5 + 8 uncovered, 500t-scenario-only — ECONOMY moves positive from cooperation-adjacent trade activity, PROGRESSION moves mostly negative from wound-penalty accumulation, see next bullet).
- **PROGRESSION 200t/500t sign-flip nuance**: `urban_political` PROGRESSION moves in *opposite* directions by run length — the 200t variant flips sign because it lands exactly on the pre-existing, M1-unrelated `progression_frozen_by_tick=200` tick-budget ceiling artifact (a documented `simq_ceiling.py` classification, noisy at that exact boundary), while the 500t seeds show consistent genuine negative drift (~-0.185) from the wound/scar penalty formula (`TCK-20260824-WOUND-PENALTY-FORMULA-WIRING` and related tickets) compounding over more ticks. Both causes are documented distinctly, not folded into one blanket explanation.

**NOT re-baselined, disclosed instead** (1 of 211 combos): `highland_traverse_seed42_200t`/SOCIAL was investigated as part of the ticket's `loop_detected` due-diligence check and found to trace to a real, unfixed gap — `src/domains/cooperation/phase.py` has no cooldown/backoff after an offer expires, so the same entity re-attempts and re-fails every tick indefinitely (confirmed via the fresh calibration data's `worst_events`: entity 13 fired `contract_expired_offer` on 23 consecutive ticks, entity 8 on 20). This is a real tuning gap, not legitimate dense-cooperation behavior, and a floor edit cannot fix it — per the Gate Integrity rule, it was left failing and disclosed rather than silently re-baselined over.

**Lesson for future re-baseline tickets**: a batch of anchor failures following a flag-flip rollout is not automatically "all flip-caused" — re-derive each `(run_key, pillar)` combo's classification against `simq_ceiling.py` before re-baselining, since a majority (131/211 here) can be unrelated pre-existing structural noise. And a directional score movement that looks consistent with the new behavior (dense cooperation) is not proof of legitimacy on its own — the same entity failing identically on 20+ consecutive ticks, surfaced only by reading the actual `worst_events` trace, is what separated the one genuine tuning gap from the other 210 legitimate re-baselines.

---

## 11. TCK-20260830-URBAN-POLITICAL-SOCIAL-1000T-FLOOR-DRIFT-REBASELINE Re-Baseline (Worked Example)

A follow-up worked example to §9: `test_urban_political_seed42_1000t_social_grade_stability`, the one test §9's own `TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION` fix unblocked but left with a disclosed, unresolved `mean_score=36.8373` vs. `anchor_score=15.45` SOCIAL drift, has now been separately re-baselined. Two more tickets landed between that measurement and this one — `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` and `TCK-20260830-COOPERATION-OFFER-CONCURRENT-DUPLICATE-BURST` — both directly gating `contract_expired_offer`/`contract_offer_created` volume (SOCIAL's two highest-frequency scored event types here, `src/simulation_quality/scorers/social.py`). A fresh 9-trial (3-batch), evidence-backed re-measurement on top of both fixes found SOCIAL had moved further and — notably — tightened dramatically in trial-to-trial variance (~40%→~10% `event_count` spread), consistent with bounding a previously-unbounded re-offer loop and deduping a duplicate-creation burst. New anchor: `{"grade": "S", "score": 35.1038, "abs_floor": 2.5387}`, derived and verified per §9's own established 2-batch-combined-plus-verification-batch methodology (see `test_corpus_diversity.py`'s own updated docstring for the full derivation). This is a second concrete instance of §9's "Lesson": a disclosed, deferred drift measured before a related fix landed must be re-measured fresh, not assumed still accurate.

---

## 12. The `-m slow` Lane Is a CI Blind Spot — a Real Crash Sat Unnoticed on `main`

`TCK-20260912-ACTIONINTENT-WRONG-TYPE-IN-LATEST-INTENT-RESULTS-CRASHES-STRATEGIC-WORK-QUEUE` found
a real, reproducible crash in `StrategicWorkQueue.build()` (`AttributeError: 'ActionIntent' object
has no attribute 'accepted'`) that had been present on `main` for as long as
`InformationBeliefPhase` Branch B has existed and any real corpus world had enough population/content
for it to fire — confirmed via `git stash`, unrelated to the ticket that happened to surface it
(`TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`).

**Why nobody saw it**: `tests/unit/worldassembly/test_corpus_diversity.py` (the file whose tests
actually exercise real corpus worlds at real population density, where this crash reliably fires)
is entirely `@pytest.mark.slow`. This file is exactly the class of test this policy document's own
§9–§11 worked examples describe re-baselining and triaging repeatedly — meaning it *is* run and
watched periodically as a deliberate practice, just not as part of routine/default CI on every push.
A real crash can sit on `main` between those periodic passes with nothing red in the routine
pipeline to flag it. This is a structural gap, not a one-off miss: it is the general shape of "the
one test lane that would catch X only runs occasionally," not specific to this one bug.

**Not resolved by this entry alone.** This section exists to make the gap durable and findable, per
the same "write it down, don't let it evaporate into prose" discipline this whole document already
follows for re-baseline evidence. Whether the right structural fix is a scheduled/periodic CI run of
`-m slow`, a lighter always-on smoke subset of `test_corpus_diversity.py`, or something else is an
open question this entry deliberately does not resolve — flagged here so the next person considering
CI cadence changes has this concrete cost (a crash invisible for an unknown but likely multi-week
span) as real evidence, not a hypothetical.
