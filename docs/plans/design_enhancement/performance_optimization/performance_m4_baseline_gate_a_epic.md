---
status: active
layer: performance
authority: P2
audience: developer
tags: [performance, benchmarking, certification, testing, simulation-quality]
---

# Epic Plan — Performance M4: Continuous Assurance, Baselines, and Decision Gate A

## Outcome

Establish a change-aware performance-assurance loop that detects future regressions quickly without
confusing noisy smoke measurements with capacity certification. Use the same controlled evidence to
produce the scenario baseline matrix and decide which exact optimizations deserve implementation
tickets. M4 builds gates, measures, and decides; it does not implement selected accelerators.

## Entry conditions

- M1 corrections and invalidation ledger are complete.
- M2 contract, result states, identity schema, gate tiers, and baseline/debt lifecycle are active.
- M3 stable phase/metric identities and bounded observer modes are available.
- Any hash change affecting identity is complete and versioned.
- Testing, Arena, Simulation Quality, Performance, Release/Certification, and CI owners are named.

## Candidate child tickets

| Candidate ID | Ticket scope | Depends on | Deliverable |
|---|---|---|---|
| PERF-M4-T01 | Verification matrix and change-impact contract | M2-T06 | Conservative source/domain/change-kind mapping to mandatory unit, E2E, Arena, SimQ, behavioral, and performance lanes |
| PERF-M4-T02 | PR-fast performance tripwire | T01 + M2-T03 | Blocking deterministic smoke comparison with bounded runtime, explicit result states, and no capacity claim |
| PERF-M4-T03 | Deterministic checkpoint/replay E2E lane | T01 | Representative full-pipeline runs proving final hash, ordered outcomes, checkpoint/restore continuation, and reference-path parity |
| PERF-M4-T04 | Arena performance and conformance lane | T01 | Fast representative Arena slice plus scheduled stress matrix recording conformance, tick cost, tails, memory, and final hash |
| PERF-M4-T05 | Simulation Quality regression lane | T01 + M2-T05 | Targeted fast corpus selection plus scheduled full/slow audit, anchor-drift classification, and regression/DA ticket handoff |
| PERF-M4-T06 | Long-horizon behavioral regression lane | T01 | Scheduled 5k or approved successor coverage with deterministic identity and behavioral threshold evidence |
| PERF-M4-T07 | Evidence-bundle and audit-document contract | T02–T06 | Machine-readable run bundle, durable audit summary template, optimization-ledger link, retention, and redaction rules |
| PERF-M4-T08 | CI routing, bypass, and escalation controls | T01–T07 | Changed-file selector tests, conservative core fallback, required-check wiring, alert/owner routing, and manual full-run path |
| PERF-M4-T09 | Scenario disposition and fixture mapping | M2-T06 | All nine performance identities mapped to committed builder/checkpoint or predeclared NOT_APPLICABLE/BLOCKED reason |
| PERF-M4-T10 | Benchmark manifest and preflight validation | T07, T09 | Machine-checked identity, required fields, supported backend, observer cleanliness, and no-silent-skip rules |
| PERF-M4-T11 | Controlled baseline matrix execution | T03–T06, T08, T10 | Core, pressure, subsystem, serving, Arena, behavioral, and SimQ evidence with valid dispositions |
| PERF-M4-T12 | Gate A bottleneck and candidate disposition report | T11 | Contributor ranking, materiality decisions, candidate selection/rejection/defer/transfer/escalation, and assurance evidence |

T03–T06 may proceed in parallel after T01 assigns coverage. T09 can proceed alongside assurance
harness construction. T11 waits for the required harnesses, routing controls, and identity preflight;
its artifacts are incomparable unless T10 says their identities are compatible.

## Verified current-state gaps and migration

M4 must migrate real mechanisms rather than describe them as already complete:

| Existing mechanism | Current limitation | Safe migration |
|---|---|---|
| `tests/tools/perf_assertions.py` | Threshold checks default to `PerformanceThresholdWarning`; a breach can leave pytest green | Calibrate stable PR tripwires, make selected checks hard, and retain controlled confirmation for noisy capacity claims |
| `tests/perf/test_perf_regression_baseline.py` | Missing baselines skip; RuntimeMode hard-scenario set is empty; samples are short compared with the P1 contract | Reconcile under M2, prohibit missing evidence from PASS, calibrate hard scenarios, and distinguish tripwire from capacity evidence |
| `.github/workflows/test.yml` SimQ drift job | Full recalibration is informational and uses `|| true`/`continue-on-error` because historical anchors already drift | Inventory/quarantine old drift, detect new base/candidate drift separately, then promote the lane to blocking when exit criteria hold |
| `tests/simulation_quality/test_grade_regression.py` | Comparisons skip when gitignored calibration reports are absent | Materialize the required corpus before comparison and treat missing required reports as an evidence failure |
| `tests/arena/` | Small Arena coverage is fast; stress Arena is `extra_slow` | Keep a stable representative PR slice and reserve the stress matrix for controlled scheduled/promotion gates |
| `tests/regression/test_behavioral_5k.py` | Valuable long-horizon coverage is `extra_slow` and its missing baseline skips | Keep it scheduled/promotion-bound, validate baseline presence, and create a faster substitute only with demonstrated detection equivalence |

These limitations are not permission to flip every warning or informational job to blocking at
once. A noisy permanently-red gate trains maintainers to ignore it. Migration requires debt
classification, stable thresholds, measured false-positive/false-negative behavior, named owners,
and an expiry for every temporary exception.

### Confirmed field evidence, 2026-09-14 (TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER)

Enabling `ENABLE_COMBAT_ENGAGEMENT` for the first time (a previously-dormant, default-OFF domain
going live) produced a concrete, real-world confirmation of the `assert_perf_threshold` gap above,
plus raw Gate-A-shaped evidence worth preserving here rather than only in that ticket:

- **Soft-gate confirmed live, not just theoretical**: `tests/perf/test_perf_metropolis.py::
  test_perf_metropolis_stress` (1000 entities) already breached both its own thresholds
  (avg TPS 1.8 vs limit 3.0; p99 tick time 1147ms vs limit 500ms) with the flag OFF and still
  reported green, because both checks default to `hard=False`. The only reason enabling the flag
  turned this test red was a wall-clock `TimeoutError` from the test harness's own resource budget
  (conftest.py), not the perf gate itself — the perf gate never fired in either state. This is the
  concrete instance the gap-table row above was describing in the abstract. Filed as its own
  diagnosed defect: `TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT`.
- **Re-tier, not a fix**: with user sign-off, that test was re-tiered `extra_slow` +
  `resource_budget_large` (it already ran 23s under a 60s "medium" budget with the flag OFF — a
  slow test mistakenly carrying a medium marker, independent of this ticket). Assertions/thresholds
  were left untouched per this epic's own gate-integrity stance above.
- **A/B attribution (raw Gate-A contributor evidence)**, same scenario, 1000 entities, 20 ticks
  post-warmup, flag OFF vs ON — real combat volume rose 4.1x (72->297 combat-related events per 20
  ticks) once entities could actually engage/avoid **(superseded 2026-09-15, see note below — does
  not reproduce on current code; retained here as the measurement that was real when taken, not as
  a current fact)**. Per-phase cost delta (ms/tick, ON minus OFF):
  `advancement` +543 (~50% of the total delta — `ApplyPath.apply_generation()` + hard-law checks +
  observability/decision-trace writing, all scaling with real activity volume), `resolution_overhead`
  +366 (~33%), `cooperation` +167 (~15%), the new `combat_engagement` phase itself +198 (~18%),
  `final_integrity` +98, `locomotion` +42, `persistence` +37 (new). Total delta ~1096ms/tick.
  **The new phase was not the dominant cost** — 82% of the increase was the rest of the engine
  correctly doing more work because the world now behaves differently, not a regression in the new
  code. This is exactly the contributor-ranking shape PERF-M4-T12 needs and a worked example of
  what M3's own instrumentation (PERF-M3-T04) should make routine instead of manual.
- **Three specific system costs surfaced as already-material at this scale**, candidates for M5
  Gate-A evidence once ranked: `src/domains/cooperation/services.py::find_pending_incoming_offer`
  (~1.15s tottime / 2.03s cumulative over 5 ticks at 1000 entities, 4500 calls — a real per-call
  cost that scales with entity count), `src/core/state.py::fingerprint()` (~2.83s cumulative over
  3 calls at 1000 entities), and `src/observability/cognition/decision_trace_writer.py::
  _write_entry_to_file` (~1.30s cumulative over 200 calls — file I/O in the hot path). None of these
  are `combat_engagement`'s own code; they are pre-existing systems this ticket's own profiling
  happened to expose as already near the tick budget ceiling at metropolis scale. Each filed as its
  own report-only ticket (observed, not investigated — no root cause, no proposed fix):
  `TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED` (also carries the full A/B table
  above, verbatim), `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`,
  `TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED`.

**Correction, 2026-09-15 (superseding the 4.1x combat-volume figure above, method and date
attached rather than the figure silently removed):** re-investigating `combat_engagement`'s actual
downstream wiring (`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`) found that the
phase's own posture/intent decision has zero consumers anywhere in `src/` — a real
`ActionIntent` is built by `PostureIntentResolver.resolve()` and never staged for execution, and
the `last_combat_posture`/`last_combat_posture_target` properties it also writes have no readers.
To check whether the 4.1x combat-volume increase above could still hold despite that (e.g. via
some other gated site), the same 1000-entity metropolis scenario (seed 42, 5 warmup + 25 sample
ticks) was re-run under four conditions, counting real `CombatActions.execute_attack()` calls
directly:

| Condition | Real `execute_attack()` calls |
|---|---|
| A) flag OFF | 1960 |
| B) flag ON, unmodified | 1960 |
| C) flag ON, phase output discarded (phase runs fully, its `StateUpdate` is thrown away) | 1960 |
| D) flag ON, phase never runs at all (fully stubbed) | 1960 |

All four conditions are identical. **The 4.1x figure above does not reproduce on current code** —
retained above as the measurement that was genuinely taken and real at the time (2026-09-14), not
retracted, since deleting a superseded number erases the trail the next person would need. No root
cause for why it no longer reproduces has been confirmed; plausible, unconfirmed candidates are the
O(n²) spatial-index fix and the `cognition_bundle_set` whole-object-replace fix landed the same day
as the original measurement (both described above), or a broader "combat-related events" counting
methodology in the original measurement that this correction's narrower `execute_attack()` proxy
doesn't reproduce. Filed as its own investigation rather than assumed: see
`docs/brainstorm/rpg_feature_atlas.html`'s Combat Engagement card for the corrected
"entities assess a threat before fighting" claim, and the cross-faction rarity ticket above for the
full four-condition detail.

### Second confirmed instance, 2026-09-14 (TCK-20260914-HOTFIX-PERF-METROPOLIS-LONGEVITY-RETIER)

The same flag produced a second real CI failure, discovered when `main` failed `Perf / cert / arena`
on six consecutive merges. `test_perf_metropolis_stress` (1000 entities) was re-tiered when the flag
went live (above); its sibling `test_perf_metropolis_longevity` (500 entities, 105 real ticks) was
not, because it only produced a soft warning locally at the time — CI's weaker 2-core runner pushed
the same real cost past the test harness's own 60s wall-clock budget, tripping a hard `TimeoutError`.

**A/B, same box, back to back, 500-entity scenario, 60 ticks, flag ON vs OFF**:

| | ON (default) | OFF | Δ | % of total Δ |
|---|---|---|---|---|
| tick_ms mean | 469.84 | 164.60 | −305.24 | 100% |
| `advancement` | 237.80 | 59.94 | −177.86 | 58% |
| `resolution_overhead` | 128.64 | 43.96 | −84.68 | 28% |
| `combat_engagement` | 63.07 | 0.02 | −63.05 | **21%** |
| `cooperation` | 63.64 | 41.93 | −21.71 | 7% |
| `final_integrity` | 51.47 | 17.81 | −33.66 | 11% |
| `locomotion` | 23.77 | 15.63 | −8.15 | 3% |

**`combat_engagement`'s own phase is only ~21% of the total delta.** This independently reproduces
the ~82%/~18% downstream split found at 1000-entity scale above — two separate measurements, two
different scenarios, agreeing on where the cost actually lives. **If this cost is ever reduced
rather than accommodated, the savings have to come from `advancement`, `resolution_overhead`, and
`cooperation` — not from `combat_engagement` itself**, which was never the dominant contributor at
either scale tested so far. That is the single most useful fact for whoever picks up cost-reduction
work here: it says where the work isn't.

Re-tiered the same way as the stress test (`extra_slow` + `resource_budget_large`, no assertion or
threshold touched) with the same explicit caveat: a pass means the wall clock fits, not that
performance is acceptable. **This is the second test re-tiered for the identical underlying cause.**
A third instance of the same pattern should be read as a signal that the cost needs reducing, not
as another candidate for the same accommodation.

## Assurance coverage matrix

| Layer | Detects | Fast signal | Controlled confirmation |
|---|---|---|---|
| Unit/property/adversarial | Local invariants, invalidation, ordering, accounting, bounds | Relevant PRs | Full scoped suite before promotion |
| Checkpoint/replay E2E | Pipeline integration, deterministic continuation, reference-path parity | Short representative checkpoint | Longer/multi-backend and worker-delay matrix |
| Arena | Combat/movement conformance, scale, memory, tail cost | Stable small Arena slice | Stress Arena under approved resource budget |
| Simulation Quality | Emergent-behavior/pillar/grade drift | Impact-selected worlds and pillars when calibrated | `simq-audit` full/slow recalibration and drift classification |
| Long-horizon behavior | Survival, economy, quests, accumulation, lifecycle | Targeted substitute only when proven equivalent | 5k regression or approved successor on main/nightly |
| Capacity/performance | Tick/phase/serving latency, throughput, memory, scaling | PR tripwire | Repeated clean matrix on controlled runners |

No individual layer substitutes for another. Canonical-hash parity cannot prove acceptable emergent
quality, a SimQ grade cannot prove identical authoritative outcomes, and a microbenchmark cannot
prove end-to-end improvement.

## Feedback and control loop

1. Classify changed files, domains, semantics, phase/catalog impact, and optimization family.
2. Select mandatory lanes from the versioned impact map. Unknown core-engine changes select the
   conservative broad set; an empty selection is an error, not success.
3. Run unit/static checks and the PR-fast tripwire first for immediate feedback.
4. Run required targeted E2E, Arena, and SimQ checks. Behavior-changing and optimization tickets
   cannot waive them merely because the fast performance result is green.
5. When a result is noisy or expensive, emit `INCONCLUSIVE` and trigger the predeclared controlled
   confirmation path; do not rerun until green.
6. Classify failures as implementation regression, expected drift tied to an approved change,
   design acknowledgment needed, infrastructure failure, or evidence incompatibility.
7. Block promotion on unexplained regression, required-lane failure, missing evidence, or expired
   quarantine. Regression/DA outcomes receive an owned ticket or incident handoff.
8. Publish the audit bundle and update the durable summary/ledger before promotion or baseline
   acceptance.

The first useful result should arrive in the PR-fast lane. Heavy Arena, full SimQ, 5k, and capacity
runs may complete later, but their status remains visible and they are mandatory before the change's
declared promotion boundary. “Immediate” means immediate detection by the cheapest trustworthy
signal—not forcing every multi-hour scenario into every edit cycle.

## Merge, promotion, quarantine, and calibration semantics

“Promotion boundary” is not a synonym for merge. The impact contract assigns each required lane to
one or more concrete boundaries:

1. merge to the protected branch;
2. candidate activation or default ON;
3. performance-baseline or SimQ-anchor update;
4. reference-path retirement;
5. release or capacity claim.

A required PR-fast or calibrated PR-targeted check needs `PASS` before merge. `REGRESSION` and
`INCONCLUSIVE` block merge until a predeclared controlled confirmation returns `PASS`; an
infrastructure failure follows bounded retry/escalation policy and is never converted to PASS. A
default-OFF implementation may merge before assigned heavy checks complete only when the impact
contract explicitly places those checks at activation/release. It stays OFF and cannot update
baselines, retire the reference path, ship, or support a capacity claim until they pass. A default-ON
behavior change cannot use that deferral.

Lane readiness is separate from test result:

- `BLOCKING` — calibrated; a required `PASS` satisfies its assigned boundary;
- `CALIBRATING` — visible/informational; cannot satisfy a required boundary, so the impact contract
  must select an approved substitute oracle or the boundary remains blocked;
- `QUARANTINED_KNOWN_DEBT` — known failing signature with owner and expiry; never satisfies
  activation, baseline/anchor update, retirement, release, or capacity-claim boundaries.

An active quarantine may permit an unrelated merge only when the impact map excludes the debt or a
paired candidate/base run proves no new or worsened delta and the named exception owner approves it.
Expired quarantine blocks every assigned boundary. Before any lane becomes a required check, M4-T08
defines its CI status/check mapping for all three readiness states and tests that branch protection
cannot interpret `CALIBRATING` or `QUARANTINED_KNOWN_DEBT` as PASS.

## SimQ drift governance

M4 reuses the repository's `simq-audit` classification model:

- `EXPECTED_DRIFT` requires a specific approved ticket/change cause before anchors move;
- `REGRESSION` remains un-anchored and creates a repair ticket;
- `DA_NEEDED` remains un-anchored and creates a design-decision ticket;
- `NO_ACTION` requires evidence that no change is necessary.

Current known anchor drift must be inventoried separately from new candidate deltas. Until the
historical backlog is classified, the full SimQ lane may remain informational, but candidate/base
delta and newly uncovered anchor signals must still be visible. Making the lane blocking is an exit
target with named criteria, not an assumption. Anchor refresh, docs synchronization, parity-ledger
updates, and final verification follow `docs/simulation_quality/audit_workflow.md`.

## Audit artifact contract

Each behavior-affecting performance ticket must produce:

- a machine-readable run manifest and raw comparison artifacts with build/config/content/checkpoint,
  runner, backend, worker count, RuntimeMode, observer level, work cardinality, samples, and hashes;
- a durable `docs/audits/performance/<ticket-or-change-id>.md` summary, subject to M4/P1 owner
  approval of the location and schema;
- links to unit, E2E, Arena, SimQ, behavioral, and performance results, with `NOT_APPLICABLE`
  justified per the predeclared impact contract;
- before/after metrics, uncertainty, regression classification, approved exceptions, rollout,
  fallback, and rollback result;
- an entry or update in `docs/optimization_audit_ledger.md`, unless its P1 owner approves a
  replacement index.

CI artifacts may expire under a bounded retention policy. The durable summary records artifact
digests, storage location, retention deadline, aggregate evidence required to reproduce the
decision, and explicit raw-evidence expiry; it must not promise a live link after retention ends.
Secrets, host-specific paths, and unbounded traces do not enter committed audit documents.

## Required performance scenario dispositions

1. certification-small;
2. gameplay-medium;
3. world-large-sparse;
4. world-large-dense;
5. dense-hotspot;
6. serving-high-client;
7. debt-pressure;
8. hash-intensive;
9. snapshot/IPC-intensive.

`NOT_APPLICABLE` is valid only under a rule approved before execution. `BLOCKED` is honest but
prevents Gate A. Unsupported backends and missing fixtures may not become silent skips.

## Gate A decision rules

Every candidate receives exactly one disposition:

- selected for M5 ticket creation;
- rejected because measured evidence is negative;
- deferred because evidence is insufficient;
- transferred to an existing owner/program;
- escalated to M6 because it changes semantics or authority.

A candidate is selected only when it:

- exceeds a predeclared materiality threshold in a target scenario;
- addresses an end-to-end contributor, not only a microbenchmark;
- has a reference path and correctness oracle;
- has an impact classification and required assurance lanes;
- has determinism/order, Simulation Quality, and memory-bound analysis;
- has adoption, rollback, retirement, and audit-document rules;
- is approved by Performance, Engine Architecture, and Simulation Correctness owners.

## Out of scope

- Implementing an accelerator.
- Treating load shedding or reduced processed work as a speedup.
- Comparing flat and hierarchical hashes as equal values.
- Promoting heavy-observer runs as clean baselines.
- Automatically accepting a new baseline or SimQ anchor because a test failed.
- Treating an informational, skipped, inconclusive, or quarantined result as PASS.
- Selecting concurrent RESOLUTION or semantic approximation as exact optimization.

## Exit criteria

- The impact mapper cannot silently under-select core-engine, phase, state, Arena, or SimQ changes.
- PR-fast produces a bounded-latency blocking signal for relevant changes.
- Required E2E and representative Arena lanes are blocking and stable.
- SimQ known drift has an owner/expiry disposition and the new-drift signal cannot be hidden by it;
  the criteria and owner for converting the full lane to blocking are recorded.
- Long-horizon and full-capacity checks run on the approved main/nightly/manual cadence with alert
  and ticket-handoff ownership.
- Every applicable scenario is reproducible and none remains BLOCKED.
- Baselines record full identity, mode sequence, cardinality, observer level, latency distribution,
  CPU/wall time, memory, variance, hash/replay validity, and relevant scaling slope.
- Audit bundles are schema-validated, retained according to policy, and indexed durably.
- Gate A report is approved and names owners for selected work.
- M5 candidate tickets are eligible for a later `create-tickets` pass; none are created here.

## Primary surfaces

- `.github/workflows/test.yml`
- `Makefile`
- `tests/perf/`
- `tests/arena/`
- `tests/integration/`
- `tests/regression/test_behavioral_5k.py`
- `tests/simulation_quality/`
- `tools/evaluate_simq.py`
- `tools/simq_audit_gaps.py`
- `docs/optimization_audit_ledger.md`
- `docs/simulation_quality/audit_workflow.md`

## References

- `performance_optimization_prerequisite_execution_plan.md` PA-07..08
- `../../../engine/contracts/regression_and_verification.md`
- `../../../engine/performance_contract.md`
- `../../../performance/perf_baseline_policy.md`
- `../../../simulation_quality/audit_workflow.md`
- `system_design_terms_and_concepts.md` §§11–14
