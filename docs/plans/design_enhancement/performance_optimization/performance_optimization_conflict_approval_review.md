---
status: active
layer: architecture
authority: P2
audience: agent
tags: [performance, architecture, review, determinism, observability, testing]
---

# Performance Optimization Conflict and Approval Review Brief

Date: 2026-09-08
Review type: architecture reconciliation; no implementation authorization

## 1. Review request

Determine whether the project should approve the new evidence-gated performance approach described
by:

- `docs/brainstorm/codex/system-design/performance_optimization_architecture_proposal.md`;
- `docs/plans/design_enhancement/performance_optimization_prerequisite_execution_plan.md`.

The review must not assume those authority-P2 documents override active authority-P1 documents.
If the new approach is approved, identify which P1 documents must be amended or superseded, by
which owner, and with what transition wording.

Return one verdict:

1. **APPROVE** — accept the new approach and the listed P1 reconciliation.
2. **APPROVE WITH MODIFICATIONS** — list exact required changes and which work remains blocked.
3. **REJECT** — retain the existing P1 approach and explain which new evidence or design is
   unsound.

Do not implement engine changes, create implementation tickets, or edit higher-authority
documents as part of this review.

## 2. Proposed approach being reviewed

The new approach would:

1. Preserve the stable engine spine: immutable Collection, barrier, canonical `WorkerResult`
   order, serial authoritative refinement, and single-owner generation reference replacement.
2. Approve six performance architecture decisions before dependent implementation:
   PERF-D1 determinism contracts, PERF-D2 portability, PERF-D3 debt meaning, PERF-D4 performance
   contract, PERF-D5 hash policy, and PERF-D6 phase-catalog authority.
3. Correct measurement and contract foundations before optimizing.
4. Audit hash behavior before changing its schedule or algorithm.
5. Inventory executable phase structure before promoting a catalog.
6. Run a versioned nine-scenario baseline with RuntimeMode, processed-work cardinality, latency
   distributions, memory, and observer overhead.
7. Use Decision Gate A to select only measured material Stage 5 optimizations.
8. Require Decision Gate B and a separate architecture proposal for Resolution concurrency or
   semantic/fidelity changes.

Approval of this direction would authorize only the prerequisite ticket workflow after the
proposal and plan are committed/merged, every required P1 amendment or supersession is approved
and merged, and each package's decision is approved. A disposition written only in the review
report is not enough. Approval would not authorize Stage 5 or Stage 6 code.

For a self-contained decision handoff, the proposed defaults are:

| Decision | Proposed default |
|---|---|
| PERF-D1 | Maintain separate Canonical/certification and Live bounded determinism contracts; Live requires a sufficient versioned control trace |
| PERF-D2 | Guarantee same-approved-runtime/platform portability first, retain tested same-environment executor parity, and expand cross-platform guarantees only after a passing matrix |
| PERF-D3 | Keep aggregate counters as capacity debt; create separate authoritative semantic-deferred-work state only for a concrete feature contract |
| PERF-D4 | Select one performance-contract authority with explicit CI-fast and scheduled executable projections |
| PERF-D5 | Keep versioned flat SHA-256 for certification boundaries, require scheme/tick/freshness metadata, and evidence-gate scheduling or hierarchical hashing |
| PERF-D6 | Select one static phase catalog for identity/order/contracts/instrumentation; validate it against handwritten execution before it may drive execution |

Package naming used below follows the execution plan. `PA-05A` is evidence-only inventory before
PERF-D6; `PA-05B` is catalog authority/generation after PERF-D6. The source proposal used the
single name `PA-05`; references to `PA-05` mean the combined workstream, not a third package.

## 3. Authority conflict

The new proposal, execution plan, and this brief are authority P2. The following relevant
documents are authority P1:

- `docs/plans/design_enhancement/design_enhancement_roadmap.md`;
- `docs/plans/design_enhancement/determinism_envelope_epic.md`;
- `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`;
- `docs/plans/design_enhancement/performance_milestones_epic.md`;
- `docs/engine/authoritative_pipeline.md`;
- `docs/engine/deterministic_execution.md`;
- `docs/engine/performance_contract.md`;
- `docs/engine/contracts/certification_contract.md`;
- `docs/performance/perf_baseline_policy.md`;
- `docs/performance/optimization_architecture.md`;
- `docs/architecture/performance_optimization.md`.

Repository behavior and P1/P0 contracts remain controlling until an authorized owner changes
them. The reviewer must not treat the word “canonical” in the proposal as authority elevation.

## 4. Conflicts requiring disposition

Each entry distinguishes repository observation or controlling authority from the proposed
change and recommendation. Where no separate proposal exists, that field says so explicitly.

### C-01 — P1/P2 program authority

**Type:** authority-blocking.

**Existing position:** the active P1 design-enhancement and performance documents define current
policy and sequencing.

**New position:** the P2 plan introduces a different prerequisite order and Gate A/B boundaries.

**Recommended disposition:** approve the new approach only if P1 owners either make the existing
roadmap the parent authority and link the new plan beneath it, or promote the new plan through an
explicit authority change while marking overlapping epics superseded. Reject silent replacement.

### C-02 — 37, 39, and 43 are being treated as the same count

**Type:** documentation drift.

**Current controlling authority:** the 39-phase P1 authoritative-pipeline contract remains
controlling; the 37-phase epic wording and 43 static call-site count are unreconciled evidence.

**Evidence:**

- the phase-contract epic repeatedly says 37;
- `docs/engine/authoritative_pipeline.md` says 39;
- AST inspection of `AuthoritativeApplyPipeline.refine` in `src/engine/pipeline.py` finds 43 static
  calls to its local `run_phase()` helper.

The 43 invocations are not yet proven to be the same counted unit as the 39-phase contract.
Conditional calls and direct phase-like operations also need classification.

**Proposed change:** inventory the counted units and create one generated catalog only after
PERF-D6 defines its authority and relationship to handwritten execution.

**Recommended disposition:** approve PERF-D6/PA-05A inventory. Keep the documented 39-phase P1
contract authoritative until the counted unit, names, order, and generation rules are reconciled.
Do not approve another blind number replacement.

### C-03 — Zero-capacity behavior is proven; intended semantics are not

**Type:** implementation-blocking.

**Evidence:**

- `WorkerManager.get_stats()` reports worker utilization `1.0` when workers are zero;
- it separately reports queue utilization `1.0` when queue capacity is zero;
- `ResourceGovernor` treats either value at or above `0.9` as DEGRADED pressure;
- LOCAL performance profiles configure zero workers.

**Existing position:** the roadmap calls this a finalized sign/default defect and prescribes
`0.0`.

**New position:** worker-zero and queue-zero may mean unavailable, disabled, synchronous, or a
real bounded-zero condition; their contracts should be decided separately before correction.

**Recommended disposition:** approve the evidence and exposure, but require PERF-D1/PA-01 to
define both semantics. Use specification/corrected-golden tests rather than parity with false
DEGRADED behavior.

### C-04 — One determinism contract versus two execution contracts

**Type:** authority-blocking.

**Existing position:** `determinism_envelope_epic.md` asks maintainers to choose canonical mode
**or** live bounded mode.

**New position:** both are needed for different uses:

- Canonical/certification prohibits unrecorded timing/resource inputs from affecting semantics.
- Live bounded permits them only with a sufficient versioned control trace.

**Recommended disposition:** approve or reject PERF-D1 explicitly. If approved, update the P1
determinism epic and `docs/engine/deterministic_execution.md` to describe both contracts rather
than mutually exclusive alternatives.

### C-05 — Live bounded trace sufficiency

**Type:** implementation-blocking.

**Existing position:** record RuntimeMode transitions, trigger values, and ticks.

**New concern:** mode transitions alone may not reproduce cadence/admission choices, cutoff,
cancellation, coalescing/drop behavior, debt changes, or their effective ordering boundary.
Some fields may be deterministically derivable rather than stored.

**Recommended disposition:** PERF-D1 must classify each semantics-affecting decision as recorded
or derivable, prove replay sufficiency, define corrupt/missing-trace behavior, and bound trace size
and retention. Do not require redundant raw fields when derivation is proven.

### C-06 — Hash scheduling premise contradicts the live path

**Type:** implementation-blocking for hash changes; audit allowed.

**Existing position:** `performance_milestones_epic.md` says
`BudgetedCanonicalHasher` already rate-limits full hash calls.

**Executable evidence:** `Kernel._phase_persistence()` directly calls
`CanonicalStateHasher.get_hash()` when replay policy is `FULL`; finalization also directly
hashes. The budgeted wrapper exists but does not govern that persistence call.

**Proposed change:** audit every operational hash call before choosing schedule, proof-boundary,
freshness, or scheme changes; do not assume the unused wrapper describes the live path.

**Recommended disposition:** approve PA-03A as evidence-only work before PERF-D5. Block schedule,
freshness, tree-hash, and affected-baseline changes until PERF-D5.

### C-07 — Existing M2 preselects optimizations

**Type:** Stage 5 boundary.

**Existing position:** after limited M1 measurement, M2 advances spatial decomposition, narrow
SoA, memoization, and hierarchical hashing.

**New position:** each accelerator must be selected separately by Gate A using complete
end-to-end contribution, p95/p99, memory, processed-work cardinality, and correctness evidence.

**Recommended disposition:** retain these as candidates, not committed milestones. Approve no M2
implementation solely because it is listed.

### C-08 — Spatial decomposition is not automatically the best partition

**Type:** Stage 5 boundary.

**Existing position:** regions are presented as the preferred parallelism unit and canonical
sorting is cited as the main safety argument.

**New concern:** spatial partitioning can worsen skew, duplicate work, or destroy useful batching.
Canonical result sorting does not prove task ownership is complete and duplicate-free.

**Recommended disposition:** require measured imbalance/locality, deterministic ownership,
complete/duplicate-free coverage, and executor parity. Compare static chunks, spatial partitions,
cost-aware partitions, and bounded dynamic scheduling before selection.

### C-09 — Hierarchical hashing has proof-system risk

**Type:** Stage 5 boundary.

**Existing position:** hierarchical/incremental hashing is described as having zero
simulation-logic risk.

**New concern:** state evolution may remain unchanged, but scheme identity, freshness, dirty
invalidation, replay/certification consumers, and accidental flat/tree comparison can invalidate
proof claims.

**Recommended disposition:** require PERF-D5, same-scheme validation, scheme/tick/freshness
metadata, tree rebuild parity, independent flat auditing, and material Gate A cost.

### C-10 — Resolution concurrency is inside the performance epic

**Type:** Stage 6 boundary.

**Existing position:** M3 builds a job graph and runs provably independent Resolution phases
concurrently after domain declarations exist.

**New position:** declarations are necessary but insufficient. Concurrent authoritative
refinement also needs read/write proof, conflict behavior, staged mutation, commit/publication
semantics, fault handling, and evidence that serial Resolution is material.

**Recommended disposition:** remove concurrent Resolution from ordinary performance execution.
Retain domain/catalog safety work. Require Gate B and a separate architecture proposal.

### C-11 — Aggregate simulation is treated as normal epic continuation

**Type:** Stage 6 boundary.

**Existing position:** M4 continues from the performance epic into aggregate distant-region
simulation.

**New position:** aggregation intentionally changes fidelity and state evolution; it is not an
exact performance optimization.

**Recommended disposition:** require Gate B, a separate versioned semantic architecture,
transition rules, migration, conservation/invariant tests, and explicit SimQ/arena acceptance
bounds.

### C-12 — Interest-management ownership already exists

**Type:** ownership boundary.

**Evidence:** `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT` exists under the live-map program.

**Current controlling authority:** that existing epic owns interest-management implementation
unless its owner explicitly transfers or merges the scope.

**Risk:** creating another interest-management workstream from the performance proposal would
produce competing ownership.

**Proposed change:** no second implementation stream; the performance program measures costs and
returns findings to the existing owner.

**Recommended disposition:** allow performance measurement of projection/serialization/queue
cost, but retain implementation ownership in the existing live-map epic.

### C-13 — Performance contracts and the live gate disagree

**Type:** implementation-blocking for baseline promotion.

| Clause | Controlling/documented source and position | Live regression test |
|---|---|---|
| Warmup/sample | `perf_baseline_policy.md` requires at least 100/1,000 ticks | 10/50 |
| Latency | `perf_baseline_policy.md` specifies p50/p95/p99; `performance_contract.md` also describes a >5% average regression | Average only, limit `max(5 ms, baseline × 1.25)` |
| Memory | `perf_baseline_policy.md` requires RSS delta and GC stability checks | No memory assertion |
| Missing baseline | `perf_baseline_policy.md` says all commits pass automated gates | Missing file is skipped |
| RuntimeMode | `performance_contract.md` requires RuntimeMode in claims | Hard-scenario set is empty; warning-only handling |
| Hardware | `perf_baseline_policy.md` and `certification_contract.md` define conflicting class rules | Test trusts the profile recorded in each baseline |

**Evidence paths:** `docs/engine/performance_contract.md`,
`docs/engine/contracts/certification_contract.md`,
`docs/performance/perf_baseline_policy.md`, and
`tests/perf/test_perf_regression_baseline.py`.

**Proposed change:** PERF-D4 selects one clause-level authority and explicitly maps each clause to
either a cheap CI-fast projection or scheduled evidence; the two tiers must not make the same
claim unless they enforce the same requirement.

**Recommended disposition:** approve PERF-D4/PA-04 reconciliation before Stage 4 baseline
promotion. Preserve a cheap CI-fast smoke projection and separate it from scheduled capacity
evidence.

### C-14 — Phase declarations have valid independent value but a presumed M3 consumer

**Type:** Stage 6 boundary.

**Existing position:** the phase-domain epic explicitly keeps execution serial and says its graph
has standalone safety value; it also makes itself the hard prerequisite for performance M3
concurrency.

**New position:** catalog/domain declarations should be justified for identity, drift detection,
instrumentation, and feature growth without making concurrency the presumed next step.

**Recommended disposition:** preserve compatible declarative work under PERF-D6/PA-05. Replace
the automatic cross-epic M3 path with Gate B and separate-architecture wording.

### C-15 — Existing P1 optimization architecture overstates current completeness

**Type:** documentation drift.

**Current P1 claim:** `docs/performance/optimization_architecture.md` describes 17 authoritative
phases, universal `CandidateSelector` use, and an implemented five-layer optimization
architecture.

**Observed live evidence:** inspection finds incomplete phase catalogs and direct paths; C-02 and
C-13 separately establish phase-count and measurement-contract drift. These observations do not
derive their authority from the proposal.

**Proposed change:** classify each P1 statement as verified current behavior, target architecture,
or obsolete guidance.

**Recommended disposition:** PERF-D4/PERF-D6 must identify which claims are verified current
behavior, target architecture, or obsolete. Update or supersede inaccurate P1 claims.

### C-16 — Historical RabbitMQ ADR still has active P1 metadata

**Type:** documentation-status drift.

**Evidence:** `docs/architecture/performance_optimization.md` has
`status: active`, `authority: P1`, while its body says its RabbitMQ mechanism is superseded and
historical. RabbitMQ/Kafka were removed.

**Proposed change:** retain only verified surviving decisions as active authority and mark the
removed transport mechanism historical or superseded with a navigation link to its replacement.

**Recommended disposition:** the owner must make current status/scope unambiguous. Preserve
verified surviving decisions if still authoritative; do not revive removed transport design.

### C-17 — New planning artifacts are not yet durable

**Type:** authority-blocking.

**Drafting-time evidence:** on 2026-09-08, Git reported the proposal and execution plan as
untracked.

**Current controlling rule:** untracked or staging-only planning artifacts are not durable
authority and cannot release implementation tickets.

**Proposed change:** none to runtime architecture; make the planning chain durable before using
its approvals.

**Recommended disposition:** re-check during review. Both must be reviewed and committed/merged
before they can release implementation tickets; staging is insufficient.

## 5. Proposed P1 document changes if the new approach is approved

| Document | Required change |
|---|---|
| `design_enhancement_roadmap.md` | Make the prerequisite/Gate A order authoritative; replace unconditional Priority 0 correction wording with a capacity-semantics decision; separate Stage 6 |
| `determinism_envelope_epic.md` | Replace canonical-versus-live choice with approved PERF-D1 contract set and sufficient recorded/derivable trace rules |
| `subphase_domain_contracts_epic.md` | Reconcile 37/39/43 counted units; preserve serial safety work; remove presumed concurrency continuation |
| `performance_milestones_epic.md` | Correct hash premise; convert M2 items to Gate A candidates; move M3/M4 behind Gate B and separate proposals |
| `docs/performance/optimization_architecture.md` | Separate verified implementation from target claims; reconcile phase count and universal statements |
| `docs/architecture/performance_optimization.md` | Resolve active-P1 versus partially-superseded historical status |
| Performance/certification/baseline contracts | Select one PERF-D4 authority and declare CI-fast versus scheduled projections |
| `docs/engine/deterministic_execution.md` | Apply PERF-D1/PERF-D2 and any PERF-D5 hash-boundary consequences |
| Authoritative pipeline and generated guidance | Apply PERF-D6 through one selected source/generator; never hand-edit generated output |

The reviewer may recommend different wording or ownership, but must supply, for every affected P1
document, the exact accountable owner, resulting status (`active`, `subordinate`, `superseded`, or
another repository-valid status), and proposed transition text. It must also state which document
becomes the navigation authority. If an owner cannot be identified, approval remains blocked.

## 6. Approval matrix

Complete this table in the review result:

| Decision | Approve / Modify / Reject | Required owner(s) | Required evidence/change |
|---|---|---|---|
| PERF-D1 determinism contracts |  | Architecture + Simulation Correctness |  |
| PERF-D2 portability |  | Architecture + Release/Certification |  |
| PERF-D3 debt meaning |  | Simulation Semantics |  |
| PERF-D4 performance contract |  | Performance + Release/Certification |  |
| PERF-D5 hash policy |  | Simulation Correctness + Observability/Replay |  |
| PERF-D6 phase catalog |  | Engine Architecture |  |
| Gate A prerequisite sequence |  | Performance + Engine Architecture + Simulation Correctness |  |
| Stage 6 separation |  | Architecture + Simulation Correctness |  |
| P1 migration/supersession |  | Owners of each affected P1 document |  |

If no named person/team currently fills a role, report that as an approval blocker rather than
inventing an owner.

## 7. Required reviewer checks

The reviewer should:

1. Re-read the live code for every executable claim rather than trusting either plan.
2. Confirm 43 with AST call-site counting, not raw textual occurrence counting.
3. Verify the FULL persistence hash call and all other operational hash consumers.
4. Verify worker-zero and queue-zero behavior separately.
5. Compare contract clauses against the test that actually runs.
6. Search for existing tickets by behavior/code scope, not only proposed PA identifiers.
7. Check whether proposal/plan files are committed at review time.
8. Identify any P0 or P1 rule that the proposed approach would violate.
9. Confirm no conditional optimization is accidentally authorized.
10. Return exact file/section changes required for approval.

## 8. Copyable reviewer task

```text
Review the performance optimization architecture proposal, prerequisite execution plan,
and conflict approval brief. Treat the brief as a review index, not as authority.

Verify every material claim against live code and authority-P1/P0 documents. Decide whether
to APPROVE, APPROVE WITH MODIFICATIONS, or REJECT the new evidence-gated approach.

For C-01 through C-17:
- mark Confirmed, Modified, or Rejected;
- cite repository evidence;
- state the required disposition;
- identify the owner and P1 document change, if any.

Complete the PERF-D1 through PERF-D6 approval matrix. Pay particular attention to:
- P1 versus P2 authority;
- 37/39 documented counts versus 43 static run_phase() invocations;
- zero-worker and zero-queue semantics;
- canonical plus Live bounded determinism contracts;
- direct canonical hashing on the live FULL persistence path;
- Gate A evidence before Stage 5;
- separate Gate B architecture for Resolution concurrency and semantic simulation;
- performance-contract versus live-gate drift;
- existing interest-management ownership.

Do not implement code, create implementation tickets, or silently edit/supersede P1 documents.
Return a review report with exact recommended document changes and unresolved blockers.
```

## 9. Sources

- `docs/brainstorm/codex/system-design/performance_optimization_architecture_proposal.md`
- `docs/plans/design_enhancement/performance_optimization_prerequisite_execution_plan.md`
- `docs/plans/design_enhancement/design_enhancement_roadmap.md`
- `docs/plans/design_enhancement/determinism_envelope_epic.md`
- `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`
- `docs/plans/design_enhancement/performance_milestones_epic.md`
- `docs/architecture/performance_optimization.md`
- `docs/performance/optimization_architecture.md`
- `docs/engine/authoritative_pipeline.md`
- `docs/engine/deterministic_execution.md`
- `docs/engine/performance_contract.md`
- `docs/engine/contracts/certification_contract.md`
- `docs/performance/perf_baseline_policy.md`
- `src/engine/pipeline.py`
- `src/engine/kernel.py`
- `src/engine/worker_manager.py`
- `src/engine/governor.py`
- `src/engine/checkpoint.py`
- `tests/perf/test_perf_regression_baseline.py`
