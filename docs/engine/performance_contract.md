---
status: active
layer: engine
authority: P1
audience: developer
---

# Engine Performance Contract

## 1. Purpose
This contract defines how performance (TPS, Tick Cost) must be measured, reported, and certified. It ensures that performance claims are honest, scoped, and reproducible.

**Authority (PERF-D4, approved 2026-10-03).** This document is the single clause-level authority for how performance is measured, compared, and claimed. Hardware classes are defined once, in `docs/engine/contracts/certification_contract.md` §3. `docs/performance/perf_baseline_policy.md` is the calibration procedure only. Every clause below says whether a check enforces it today; a clause with no enforcing check says so and names the work that adds one (`PERF-M2-T03` for the tripwire, `PERF-M2-T04` for the capacity run). The row-by-row evidence is `docs/performance/performance_clause_inventory.md`.

## 2. Primary Metrics

### 2.1 Tick Cost (ms)
- **Definition**: The total wall-clock time spent inside `Kernel.tick_once()`.
- **Measurement**: Derived from `time.perf_counter_ns()` with microsecond resolution.
- **Reporting**: Reported per-tick in `PressureSignals`.

### 2.2 TPS (Ticks Per Second)
- **Definition**: The sustainable number of ticks the engine can process per second.
- **Measurement**: `1000 / avg_tick_compute_ms`.

### 2.3 Phase Breakdown
The engine must report the cost of each authoritative phase separately. The kernel phases named here are:
- `INIT`: Context setup and policy.
- `SCHEDULING`: Work selection.
- `COLLECTION`: Execution (local or concurrent).
- `RESOLUTION`: Applying results to state.
- `CLEANUP`: Metrics and finalization.
- `ADVANCEMENT`: Signal recording.

In practice the harness records every phase key the kernel emits, which is more than these six (a committed baseline carries, for example, `apply`, `resource`, `combat`, `movement`, `strategic` and `persistence`, and the kernel also emits sub-phase keys). The reported set is whatever `phase_breakdown` contains; this list is the minimum.

## 3. Benchmarking Rules

### 3.1 Scoped Claims
Performance claims are ONLY valid when combined with:
- **Runtime Profile**: (e.g. `standard_gaming`)
- **Hardware Class**: (e.g. `Class_B`)
- **Scenario**: (e.g. `movement` parameterized by `entity_count=100` — see `src/perf/scenarios.py`'s
  `SCENARIO_BUILDERS`; the previously-cited `MOVEMENT_STRESS_100_ACTORS` name is not a real wired
  scenario anywhere in `src/perf/scenarios.py` or `tests/`, corrected 2026-08-22 per
  `TCK-20260822-SCAN-POLICY-DOC-FIX`)
- **Execution Mode**: (LOCAL vs CONCURRENT)
- **RuntimeMode**: (NORMAL — see §7 Adaptive Phase Budget Governor for the ladder; a claim
  measured while the Governor left NORMAL is not a valid baseline claim without stating so)

Every result record also carries (PERF-D4, approved; the record shape is pending `PERF-M2-T02`; provisional draft in `docs/performance/benchmark_identity_schema.md`): the PERF-D2 runtime identity (interpreter version and build flavor, OS, architecture, native-kernel versions) and its DET-PORT tier; the PERF-D1 contract it ran under (Canonical or Live bounded); the `RuntimeMode` sequence observed during sampling; and the processed-work count. A comparison between results with different identities is not valid and returns `INCONCLUSIVE` (§3.3).

### 3.2 measurement Protocol
These minimums apply to the **capacity run** (§3.3). The **tripwire** is a cheaper projection and uses smaller, stated sizes.
- **Warmup**: A capacity run must execute a minimum of 100 warmup ticks before recording starts.
- **Sampling**: A capacity run must sample a minimum of 1000 ticks for a baseline.
- **Environmental Stability**: Capacity runs must run on isolated cores if possible to minimize noise.

What runs today: the tripwire check (`tests/perf/test_perf_regression_baseline.py`) uses 10 warmup and 50 sampled ticks; the smoke benchmark tool (`tools/perf/run_benchmarks.py`) uses 10/20 or 50/200. `BenchHarness` defaults to 100/1000, so a harness caller that passes nothing runs the capacity sizes. No capacity run exists as a gate. Of the 15 committed files in `tests/perf/baselines/`, 12 record 20 sampled ticks and only the three `simq_corpus_*` files record 1000; they are **tripwire references only** and carry no capacity claim.

### 3.3 Projections, outcomes, and clause kinds
Approved decision: PERF-D4. A performance claim is made by one of three clause kinds, which have different claims and are never mixed.

- **Tripwire.** Fast, runs on every relevant change, detects change against a baseline of the same identity, and makes **no capacity claim**. The tripwire is `tools/perf/tripwire.py` (pull requests: base and head paired, each side in a fresh process) and the nightly baseline lane (`tests/perf/test_perf_regression_baseline.py`). Both go through `compare()` and report; neither blocks. The nightly lane is `INCONCLUSIVE` until baseline records are promoted (`PERF-M2-T08`).
- **Capacity run.** Warmup and sample sizes from §3.2, percentiles and memory, repeated, on a controlled runner, bound to a hardware class (`certification_contract.md` §3). It is the only kind that may support a statement of the form "this build sustains X on class Y". `tools/perf/capacity_run.py` implements the projection: 100 warmup and 1000 sampled ticks, N repetitions each in a fresh process, a declared variance limit (coefficient of variation of average tick latency, 0.10), and an optional paired base/head mode. It reports `INCONCLUSIVE` or `NOT_APPLICABLE`, never `PASS`, and runs on one named host with `runner.controlled = false`, so no result is a capacity claim until the owner names an approved runner (owner decision OD-5). It is not a gate.
- **Comparative.** Compares two configurations of one build (for example instrumentation off against on), or the start and the end of one run. It uses the same four outcomes and the same identity fields as the other kinds and makes **no capacity claim**. Its current instances, all soft: the instrumentation and subsystem overhead ratios (`tests/perf/test_hard_law_monitor_overhead.py`, `tests/perf/test_production_observatory_overhead.py`, the four bands of `tests/perf/test_simq_isolation_overhead.py`), and the within-run trend checks of the long-run harness (`src/perf/long_run_harness.py`: `rss_bounded`, `latency_stable`, `caches_bounded`, `gc_stable`, exercised by `tests/certification/test_cert_long_run_stability.py`; the report's verdict is its `outcome`, which replaced `passed_certification`, and `LongRunStabilityHarness.to_record` maps it to a `comparative` record).

Every projection returns one of `PASS`, `REGRESSION`, `INCONCLUSIVE`, or `NOT_APPLICABLE`. A missing baseline, or one whose identity is incompatible with the run, is `INCONCLUSIVE`, never a skip that reads as success. A missing or legacy baseline is `INCONCLUSIVE` with a named reason in both tripwire lanes (`PERF-M2-T03`). `PerfRegressionGate` still raises `MissingBaselineError` only in CI mode and has no production caller.

## 4. Optimization Laws

### 4.1 Parity Invariant
Optimization MUST NOT change the semantic outcome of an official RPG slice. Any optimization that causes a hash mismatch in the `AuthoritativeState` vs the baseline is a failure.

### 4.2 Bounded Overhead
Timing instrumentation itself must stay bounded (< 1% of total tick time). This is a **comparative** clause (§3.3). **Not met by one existing check:** the hard-law monitor's overhead test records, in its own comment, that the monitor cannot meet 1% and asserts a looser absolute limit, soft (`tests/perf/test_hard_law_monitor_overhead.py`). The 1% figure is a target; no check enforces it as written.

## 5. Regression Enforcement
These are **tripwire** clauses (§3.3).
- A commit that increases `avg_tick_compute_ms` on a stable scenario beyond the tripwire threshold, against a baseline of compatible identity, must be reported as `REGRESSION`. **The threshold (provisional, owner-approved 2026-10-10):** the tripwire (`tools/perf/tripwire.py`, `TRIPWIRE_THRESHOLDS`) reports `REGRESSION` when the head's average tick latency over 50 sampled ticks exceeds `max(5.0 ms, base x 1.40)`, base and head measured paired on one runner, each in a fresh process. The relative term sits above the noise budget, 0.35, the largest head/base deviation seen with identical code on both sides (44 A/A pairs, 6-vCPU VM, 2026-10-10); the margin is small, which is a further reason to recalibrate. A first non-PASS result is run once more, head first; a disagreeing retry is `INCONCLUSIVE`; the outcome is reported and never blocks. The values are **provisional**: they must be recalibrated with `python3 tools/perf/tripwire.py calibrate` on the CI runner once the CI step lands, and on this host they detect only changes above about 40%. The earlier tolerances (`max(5 ms, 1.25x)` in the old live check, `max(1.15x, +3 ms)` in the retired `tools/perf/check_perf_regression.py`, and 5% / 10% / 15% for p50 / p95 / p99 in `perf_baseline_policy.md` before it was moved here) are retired.
- Documented targets, not enforced by any check (no enforcing check yet; `PERF-M2-T03`): p50 latency not above baseline by more than 5.0%, p95 by more than 10.0%, p99 by more than 15.0% (moved from `perf_baseline_policy.md` §3.1). `PerfRegressionGate` (`src/perf/regression_gate.py`) implements p95, p99, throughput, memory and per-phase comparisons with a 10% default tolerance, and is exercised only against synthetic fixtures (`tests/unit/perf/test_perf_regression_gate.py`); no production caller runs it. No check enforces these targets: the paired tripwire cannot resolve a change below about 40% on the measured host.
- An intentional baseline increase is accepted by recording a rationale with the baseline update. A rationale does not turn a `REGRESSION` into a `PASS`; it is the record that explains why the baseline moved.

### 5.1 Capacity-run targets
Not enforced by any check today (`PERF-M2-T04`). Moved from `perf_baseline_policy.md` §2.2 and §3.2, and keyed to the hardware classes of `certification_contract.md` §3 (the policy's own class table is removed because it contradicted that definition):

| Class | Target |
|---|---|
| `CLASS_A` | 10,000+ entities at < 50 ms per tick |
| `CLASS_B` | 2,500 entities at < 40 ms per tick |
| `CLASS_C` | 500 entities at < 30 ms per tick |

- Resident memory growth between tick 100 and tick 1,000 must not exceed 15.0% of its value at tick 100.
- Garbage-collection sweep counts must remain stable over a capacity run (the high-frequency no-op singletons exist to prevent generation 1 and 2 heap fragmentation).

The nearest live checks are the long-run harness's trend checks (comparative, §3.3) and the passive-scaling memory check (`tests/perf/test_perf_passive_scaling.py`), both soft.

### 5.2 Known gaps (recorded debt, not clauses)
- **Absolute per-scenario and per-phase ceilings.** Many tests in `tests/perf/` and `tests/arena/` assert hard-coded millisecond, MB and TPS limits (for example `tests/perf/test_perf_idle.py`, `test_perf_stress.py`, `test_phase2_self_model_budget.py` through `test_phase9_campaign_semantic_budget.py`). No document sets these numbers and they are not contract clauses. **Disposition (owner-approved 2026-10-10): they stay as soft smoke bounds, not clauses.** 56 `assert_perf_threshold` / `perf_check` call sites in `tests/perf`, `tests/arena` and `tests/certification`, one with `hard=True`; no document owns the numbers; and an absolute millisecond ceiling depends on the host, which a paired same-host comparison does not. They are not absorbed into the tripwire. Each maps to "enforces none" in the gate-conformance map (`PERF-M2-T06`) and is removed when its test is next edited.
- **The `PerfBudget` store.** `perf_baselines.json` at the repository root and the `perf_budget` fixture (`tests/perf/conftest.py`, `make perf-measure`) form a second baseline store, per named test, with its own 20% tolerance. It is not described by any other document. **Disposition (owner-approved 2026-10-10): deleted, together with `tools/perf_guard.py`, in a follow-up (`TCK-20261010-PERF-M2-PERFBUDGET-RETIRE`).** `entries` is empty and the fixture has two users (`test_phase2_self_model_budget.py`, `test_phase3_adventure_decision_budget.py`).
- **`src/perf/regression_gate.py` (`PerfRegressionGate`).** **Disposition (owner-approved 2026-10-10): retired under its own later lift** (it is outside the `PERF-M2` lift). It has no production caller and `compare()` replaces it. `tools/perf/check_perf_regression.py` and `tools/perf/perf_ci.py` were removed by `PERF-M2-T03`.
- **Soft thresholds.** Every threshold in the test tree is soft (0 of 55 `assert_perf_threshold` / `perf_check` call sites pass `hard=True`, `docs/performance/performance_clause_inventory.md` §7), and 45 of the 55 are `slow`-marked and deselected on pull requests. `TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT` tracks this; changing a warning to a failure reaches RPG-core pull requests through the `perf-cert-arena` job and waits for the RPG-core entry gate.
- **The governor's trigger rule** (`PhaseBudgetGovernor`, §7) is a runtime control rule, not a measurement clause, and is not governed by this section.

## 6. Memory Management & Pooling
- **Differential Caching**: AuthoritativeState must utilize differential caching for read-only views. Reconstruction of views should be O(Dirty) rather than O(N).
- **Singleton Singletons**: High-frequency no-op updates (e.g. EMPTY_ENTITY_UPDATE) must be implemented as singletons to minimize object allocation spikes.
- **Deep-Freeze Caching**: Shared world components that are immutable for the duration of a simulation tick should be cached in their "frozen" state to avoid redundant recursive traversals.
- **Incremental GC**: The Kernel must utilize frame-pacing idle windows to perform shallow garbage collection (`gc.collect(0)`). This prevents the accumulation of short-lived objects into expensive generation 1/2 collections, smoothing the latency p95/p99 envelope.

## 7. Adaptive Phase Budget Governor

### 7.1 Granular Sub-Phase Budgets
Under system pressure, the engine must not rely solely on macro concurrency limits. The `PhaseBudgetGovernor` monitors real-time sub-phase compute costs (e.g., Locomotion vs. Strategic Intelligence) and dynamically emits granular `PhaseBudgets`.

### 7.2 Sub-Phase Budget Parameters
- `candidate_budget`: Caps the maximum number of entities evaluated per tick during movement and action routing.
- `movement_budget`: Caps the number of spatial pathfinding operations per tick.
- `strategic_budget`: Caps the number of high-cost cognition cycles per tick.
- `scan_policy`: Governs candidate evaluation rigor (`FULL`, `THROTTLED`, `EXACT_DIRTY`). Under heavy pressure, systems bypass O(N) full scans and evaluate ONLY entities marked in the authoritative `DirtySet`.
- `background_sweep_interval`: Modulates the cadence of background entity sweeps (e.g., from every tick up to every 10 ticks under `SURVIVAL` mode).
- `compaction_level`: Modulates state update compaction (`NORMAL` vs `AGGRESSIVE`) to aggressively prune redundant or no-op updates before authoritative application.

## 8. Derived Entity Indexes

### 8.1 Spatial Indexes (`WorldIndexService`)
`src/engine/world_index.py` maintains `WorldIndexes` -- spatial lookups (active resource nodes by
grid chunk, buildings/entities/ground items/corpses by tile) over `AuthoritativeState`. Lifecycle:
lazy, pull-based (called from `SpatialQueryService` query methods, not any Kernel phase),
tick-scoped cache hit, per-domain partial rebuild gated by `CacheInvalidationPolicy.should_invalidate()`
against the tick's `DirtySet`. Attached to `AuthoritativeState.world_indexes` via
`object.__setattr__` -- never `StateUpdate`/`replace()`.

**Note (`TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD` investigation):** `WorldIndexService.get_indexes()`
(`src/engine/world_index.py:105-138`) has the structurally identical eager-all-5-dimensions shape
that `SemanticEntityIndexService.get_indexes()` had before that ticket's `dimensions` parameter
(§8.2) -- every call resolves all 5 fields together, with no per-call selective-dimension request
path. It was not given the same `dimensions` parameter in that ticket, because its 3
`SpatialQueryService` call sites (`nearest_resource_node`, `nearest_building`, `nearby_entities`,
invoked per-entity across movement/pathfinding/routing logic) collectively exercise most of its 5
dimensions every tick regardless of which single dimension any one call wanted -- natural
cross-call amortization that `SemanticEntityQuery`, with zero production callers at the time, had no
equivalent of. This remains an intentionally deferred, not fixed, limitation.

### 8.2 Semantic Entity Indexes (`SemanticEntityIndexService`)
`src/engine/semantic_entity_index.py` maintains `SemanticEntityIndexes` -- five entity-attribute
lookups over live entity state: `by_role_class` (`(role, class_id)` -> entity IDs),
`by_region` (`NavigationComponent.region_id` -> entity IDs), `by_faction`
(`IdentityComponent.faction` -> entity IDs), `by_need` (`BiologicalComponent` threshold crossings
-- `hunger`/`sleep_debt`/`rest_pressure`, thresholds per §4 of `docs/mechanics/01_entity_anatomy.md`
where documented), and `by_knowledge_domain` (`AuthoritativeState.information_providers` keyed by
`InformationProviderState.knowledge_domains`). Introduced by `TCK-20260822-SEMANTIC-ENTITY-INDEX`
to give strategic/governance layers O(1)/O(k) entity lookups instead of O(N) scans. The live
`paid_information.py` seeker/provider hotspot was retrofitted by
`TCK-20260822-PAID-INFO-INDEX-RETROFIT`, but **not** by routing through `SemanticEntityQuery`:
`PaidInformationTransactionSystem.enforce()`'s shipped selection picks the smallest non-self
`entity_id` among *all* registered providers, unfiltered by domain, while `by_knowledge_domain` is
bucketed by knowledge-domain string and would drop any provider with an empty `knowledge_domains`
tuple -- no dimension in this section maps onto "all providers sorted by entity_id" without
changing that selection semantics. The retrofit instead hoists `sorted(providers.keys())` out of
the per-seeker loop into a single local variable computed once per `enforce()` call, eliminating
the O(seekers x M log M) resort without adding a new `SemanticEntityIndexes` dimension or touching
this service.

The live `MilitaryConflictPhase._find_guard_entities_in_region` per-WAR-pair `O(N)` scan
(`src/engine/military_conflict.py`) was retrofitted by `TCK-20260822-GUARD-SCAN-INDEX-RETROFIT`,
also **not** by routing through `SemanticEntityQuery.by_region`: unlike PAID-INFO, `by_region` is
the correct index dimension for this call site (it needs exactly "entities in one region," filtered
in-memory to `identity.role == EntityRole.GUARD`), but at the time `SemanticEntityIndexService.get_indexes()`
had no partial-dimension build path -- any query call rebuilt all five dimensions together, and this
call site would have been the index's first production caller, paying that full rebuild cost with
no same-tick amortization in any shipped scenario (every existing scenario has exactly one WAR pair
active per tick). This is no longer true of the index as of `TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD`
(see the "Cross-tick carry-forward and per-dimension selective building" note below) -- `by_region`
alone no longer forces a rebuild of the other four dimensions -- but GUARD-SCAN itself was not
retrofitted onto the index (per that ticket's Out of Scope), so its shipped local-hoist behavior
below is unaffected and remains the production implementation. The retrofit instead hoists a single
`region_id -> sorted [GUARD entity id]` dict
(`_build_guard_index_by_region`), built with one pass over `state.entities` at the top of
`execute()`, bounding the scan to `O(N)` once per tick regardless of `war_pair_count` without the
index's rebuild tax.

**Lifecycle** -- follows §8.1's `WorldIndexService` pattern exactly, not an eager Persistence-phase
write: `Kernel._phase_persistence` performs zero state mutation today (it only hashes and emits a
trace event), so there is no state-mutating phase boundary for an eager write to attach to without
restructuring Kernel phases, which was out of scope. `SemanticEntityIndexService.get_indexes()` is
lazy and pull-based, called from query sites via `SemanticEntityQuery`, tick-scoped cache hit,
per-dimension partial rebuild gated by three additive `CacheInvalidationPolicy` domains
(`"identity"`, `"region"`, `"needs"` -- `"knowledge"` conservatively always invalidates, since
`information_providers` mutations carry no dedicated `DirtySet` tag). Attached to
`AuthoritativeState.semantic_entity_indexes` via `object.__setattr__`, same non-authoritative
derived-cache pattern as `world_indexes`.

**`identity_entities` DirtySet tag**: `DirtySet` gained a dedicated `identity_entities: Set[int]`
field (populated whenever an entity's `EntityUpdate.identity` is a non-noop `IdentityUpdate`,
i.e. a role/faction/etc. change) to back the `identity` invalidation domain -- `DirtySet` previously
had no tag coverage for identity/role/faction changes at all. Kept separate from the existing
`attribute_entities` tag because `src/engine/phase_graph.py` gates unrelated phases on
`attribute_entities`'s narrower meaning. `DirtySet.all_dirty_entities` was extended to include
`identity_entities` so audit-mode leak detection (`AuthoritativeState.validate_dirty_set`),
`ReadModelCache`'s WS delta invalidation, `ApplyPlan.invalidate_read_model`, `HardLawMonitor`, and
`CandidateSelector`'s `"all"` domain all see identity-only changes correctly.

**Determinism**: excluded from `CanonicalStateHasher` by omission -- `to_canonical_data()` is a
hand-written allow-list that never references `semantic_entity_indexes`, mirroring how
`world_indexes` is excluded today (verified by
`tests/unit/domains/optimization/test_semantic_entity_index.py::test_semantic_index_excluded_from_canonical_state_hash`).
Query methods (`SemanticEntityQuery.by_*`) return only `Tuple[int, ...]` entity IDs, never
`EntityState`/component objects.

**Cross-tick carry-forward and per-dimension selective building** (`TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD`):
the "Known limitation" that used to be documented here -- `semantic_entity_indexes` not carried
forward across ticks -- is closed. `ApplyPath.apply_generation`'s new-state construction
(`src/engine/apply.py`) now carries `semantic_entity_indexes=getattr(prior_state,
"semantic_entity_indexes", None)`, mirroring `world_indexes`'s existing carry-forward line exactly.
Each tick's first query no longer forces a full five-dimension rebuild; the per-dimension
reuse-or-rebuild ternaries in `get_indexes()` now see the prior tick's resolved object as `existing`
and correctly reuse whichever dimensions `CacheInvalidationPolicy.should_invalidate()` says are
still clean.

`get_indexes()` also now accepts an optional `dimensions: Optional[Set[str]] = None` parameter
(`None` means "all 5", preserving every pre-existing call signature). A caller that only needs one
dimension -- e.g. `SemanticEntityQuery.by_region`, which now internally calls `get_indexes(state,
dirty, dimensions={"region"})` -- no longer pays the `_build_*` cost for an invalidated-but-unrequested
dimension it did not ask for. All 5 `SemanticEntityQuery` methods (`by_role_class`, `by_region`,
`by_faction`, `by_need`, `by_knowledge_domain`) were updated this way; their own public signatures
are unchanged.

To make this safe within a single tick, `SemanticEntityIndexes` gained a 6th field,
`resolved_dimensions: FrozenSet[str]` (default `frozenset()`), tracking which dimensions have
already had their invalidation question settled (built fresh, or confirmed clean) *this tick*. A
dimension already in `resolved_dimensions` is reused on any later same-tick call requesting it,
without re-consulting `should_invalidate()` -- so N same-tick calls requesting the same invalidated
dimension trigger at most one rebuild, not one per call. Deliberately, there is **no** same-tick
"return the cached object immediately" shortcut in `get_indexes()` at all -- an earlier version of
this mechanism had one and it was found, in review, to be able to return a stale value for a
dimension an earlier same-tick *partial* request had not yet resolved (e.g. a full request
following a same-tick partial request that only touched one of the 5 dimensions). Every call,
partial or full, always runs the full per-field resolution logic; this is what makes
`resolved_dimensions` correctness-bearing rather than merely a performance nicety.

The `knowledge` domain's unconditional always-invalidate-on-request behavior
(`CacheInvalidationPolicy.should_invalidate("knowledge", ...)` unconditionally returning `True`,
since `information_providers` mutations carry no dedicated `DirtySet` tag) is unchanged by this
ticket -- it remains a deliberate, still-documented limitation. Only *repeated* same-tick requests
for `knowledge_domain` now avoid redundant rebuilds via `resolved_dimensions`; a caller requesting it
for the first time in a given tick still always gets a fresh rebuild, and a caller that never
requests it never pays for it at all (via the "not requested" gate).

