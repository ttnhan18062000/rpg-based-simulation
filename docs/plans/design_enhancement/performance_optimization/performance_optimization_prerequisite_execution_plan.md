---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance, architecture, engine, determinism, observability, testing]
---

# Performance Optimization Prerequisite Execution Plan

Date: 2026-09-08

## 1. Purpose and planning boundary

This plan converts
`docs/brainstorm/codex/system-design/performance_optimization_architecture_proposal.md`
into an executable planning sequence through Decision Gate A. It coordinates architecture
decisions, verified baseline corrections, contract reconciliation, phase identity, bounded
observability, benchmark scenarios, and the Gate A bottleneck report.

The folder-level milestone decomposition for future ticket creation is
`docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md`.
That roadmap and its M0–M6 epic files split this plan into related ticket groups without changing
this document's gates or creating tickets.

This plan does **not** authorize engine changes by itself. A prerequisite package may enter the
normal `create-tickets` and `implement-ticket` workflows only after all three conditions hold:
its required performance decision is approved by the named decision owners, every conflicting
authority-P1 owner has recorded a disposition, and the normal ticket workflow approves the scope.
The sole sequencing exception is evidence-only PA-03A and PA-05A: after R0A, they may be ticketed
without PERF-D5/PERF-D6 only when their affected P1 owners record an explicit
no-behavior-change/evidence-only disposition. They cannot alter runtime policy, promote a catalog,
regenerate authority, or promote baselines before R0B.
It does not authorize:

- any Stage 5 optimization candidate;
- Resolution concurrency;
- hierarchical or aggregate simulation;
- a fidelity or workload-admission change;
- a change to the Singular Bottleneck Law;
- direct mutation of `AuthoritativeState` outside the authoritative refinement pipeline.

The source proposal is authority P2. The existing design-enhancement roadmap, its three epic
plans, and current performance architecture/contracts include authority-P1 documents. Therefore
this P2 plan cannot silently replace their scope or policy. The dispositions in section 5 are
mandatory release conditions: authority-P1 documents remain controlling until their owners amend
or supersede them.

### Identifier namespace

The proposal's D1-D6 are called **PERF-D1** through **PERF-D6** in this plan so they cannot be
confused with `design_enhancement_roadmap.md` Section D1-D3. They map one-to-one:

| Plan ID | Proposal ID | Decision |
|---|---|---|
| PERF-D1 | D1 | Canonical/certification and Live bounded determinism contracts |
| PERF-D2 | D2 | Determinism portability scope |
| PERF-D3 | D3 | Capacity debt versus semantic deferred work |
| PERF-D4 | D4 | Performance-contract authority |
| PERF-D5 | D5 | Hash policy |
| PERF-D6 | D6 | Phase-catalog authority |

PA identifiers retain the proposal's names because no conflicting PA namespace was found. Durable
decision output goes to `docs/architecture/performance_optimization_decisions.md`; ticket-scoped
evidence follows the repository convention `stored_artifacts/<ticket-id>/`. Gate A output goes
to `docs/performance/performance_optimization_gate_a.md`.

## 2. Intended outcome

The plan is complete when:

1. PERF-D1 through PERF-D6 have named, approved decision records.
2. Active authority-P1 design-enhancement plans have been reconciled with those decisions and
   current executable evidence.
3. Zero-capacity and debt-harness behavior no longer invalidate benchmark interpretation.
4. Hash behavior is audited before policy changes, and any policy correction follows PERF-D5.
5. One performance contract governs CI-fast and scheduled evidence.
6. One phase catalog accounts for live executable order and generates dependent documentation.
7. Bounded observability and the approved scenario matrix produce clean baseline evidence.
8. Decision Gate A names only material bottlenecks and either selects or rejects each conditional
   Stage 5 workstream.

Completion of this plan is **not** completion of the optimization program. It produces trustworthy
authorization evidence for later work.

## 3. Governing constraints

All packages must preserve:

- one authoritative owner and the Singular Bottleneck Law;
- immutable/read-only Collection inputs;
- a global barrier before authoritative application;
- canonical `WorkerResult` ordering independent of completion order;
- serial authoritative refinement unless a separate approved Stage 6 architecture changes it;
- the precise current guarantee of **single-owner generation reference replacement**, without
  claiming crash-atomic durable commit, external-side-effect rollback, general transactional
  isolation, or multi-reader atomicity;
- client-presence independence from authoritative simulation;
- bounded memory, queues, metrics, control traces, and retained benchmark artifacts;
- discardable derived indexes, caches, views, buckets, and hash trees with a
  correctness-preserving fallback;
- generated documentation being changed through its generator/source, never by hand.

Performance claims also obey these rules:

- Faster ticks caused by processing less undeclared work are not implementation speedups.
- Every result includes RuntimeMode sequence and processed-work cardinality.
- Unexpected mode transitions invalidate a baseline unless the scenario tests that transition.
- CI-fast smoke results are not capacity claims.
- Profiling/allocation-tracing runs measure observer cost and are not clean timing baselines.
- Microbenchmark wins do not authorize promotion.
- End-to-end p95/p99, memory, and reference-path correctness are required for promotion.

## 4. Authority and document ownership

| Concern | Current authority/evidence | Required owner action |
|---|---|---|
| Singular Bottleneck Law and authoritative phase contract | `docs/engine/authoritative_pipeline.md`, generated `AGENTS.md`, live pipeline | Preserve; reconcile the documented count/order through the authoritative source and generator |
| Existing program ordering | `design_enhancement_roadmap.md` (authority P1) | Amend or explicitly supersede conflicting performance sequencing |
| Determinism envelope | `determinism_envelope_epic.md` (authority P1), PERF-D1/PERF-D2 proposal | Decide PERF-D1/PERF-D2, then update the P1 epic and engine contract |
| Phase-domain work | `subphase_domain_contracts_epic.md` (authority P1), PERF-D6 proposal, live pipeline | Reframe around one catalog and the verified executable inventory |
| Performance milestones | `performance_milestones_epic.md` (authority P1), Gate A proposal | Remove preselection and separate Stage 6 work before prerequisite tickets begin |
| Current optimization architecture | `docs/performance/optimization_architecture.md` (authority P1) | Reconcile its 17-phase and universal-implementation claims through PERF-D4/PERF-D6 |
| Historical V1 optimization ADR | `docs/architecture/performance_optimization.md` (authority P1, prose says partially superseded) | Correct metadata/current-use boundary; do not revive removed RabbitMQ design |
| Performance contract | `docs/engine/performance_contract.md`, certification contract, baseline policy, live CI | PERF-D4 names one authority and executable projections |
| Hash policy | Live persistence path, checkpoint hash utilities, PERF-D5 | PA-03A measures first; PERF-D5 decides; PA-03B reconciles |
| This execution plan | This file (authority P2) | Coordinate prerequisite work only; never override P1/P0 authority |

The proposal and this plan must be placed under version control together before either is treated
as durable planning authority. At creation time, the proposal's directory is untracked in the
working tree; an untracked source cannot safely govern ticket execution.

## 5. Existing-plan conflict register

Standalone approval handoff:
`docs/plans/design_enhancement/performance_optimization_conflict_approval_review.md`.

### Conflict severity

- **Authority-blocking** — decision/ticket authorization cannot proceed until the higher-authority
  owner records a disposition; read-only investigation remains allowed.
- **Implementation-blocking** — evidence gathering may proceed, but behavior, schedule, or baseline
  promotion cannot change until the conflict is resolved.
- **Stage-boundary** — prerequisite work may proceed, but the conflicting Stage 5/6 item remains
  unauthorized.
- **Documentation drift** — inventory/catalog work may start, but no authority claim may be
  finalized until reconciliation.

| ID | Severity | Existing statement | Current proposal/evidence | Required disposition |
|---|---|---|---|---|
| C-01 | Authority-blocking | Existing design-enhancement and performance architecture documents are authority P1 and define current policy/order | The source proposal and this plan are authority P2 | Named P1 owners must amend/supersede the older documents or reject conflicting proposal portions; P2 text cannot do so |
| C-02 | Documentation drift | The roadmap/phase epic describe 37 or 39 Resolution phases | Live `AuthoritativeApplyPipeline.refine` contains 43 static `run_phase()` invocations; this is not yet proven to be the same counted unit as the authority-P1 39-phase contract | PERF-D6 must classify calls, names, conditional invocations, and direct phase-like operations; the documented 39-phase contract remains authority until reconciled |
| C-03 | Implementation-blocking | The roadmap calls zero-worker utilization a finalized sign/default defect and prescribes `0.0` | Current evidence proves reported `1.0`, DEGRADED interpretation, and LOCAL exposure, but worker-zero and queue-zero meanings are not yet authoritative | PERF-D1/PA-01 must define unavailable, disabled, synchronous, and bounded-zero semantics separately before correcting signals |
| C-04 | Authority-blocking | The determinism epic asks maintainers to choose canonical mode **or** live bounded mode | The proposal recommends distinct Canonical/certification **and** Live bounded contracts for different uses | PERF-D1 must approve one contract set; then the authority-P1 epic and `deterministic_execution.md` must use the same model |
| C-05 | Implementation-blocking | The live-bounded option records mode transitions, trigger values, and ticks | The proposal identifies additional semantics-affecting decisions whose replay sufficiency is unresolved | PERF-D1 classifies each cutoff, admission/cadence choice, cancellation, drop/coalesce action, debt delta, and ordering boundary as recorded or deterministically derivable, then proves sufficiency and bounds |
| C-06 | Implementation-blocking | The performance epic says `BudgetedCanonicalHasher` already rate-limits the full hash calls | The live FULL persistence path directly invokes `CanonicalStateHasher.get_hash()`; the budgeted scheduler is not on that path | PA-03A audit is expressly allowed; hash implementation and affected baseline promotion remain blocked until PERF-D5 |
| C-07 | Stage-boundary | Performance M2 preselects spatial decomposition, SoA projection, memoization, and hierarchical hashing after its M1 | The proposal requires complete Stage 4 evidence and Gate A materiality before any Stage 5 candidate | Reclassify these as candidates; Gate A selects them individually using end-to-end contribution and adoption evidence |
| C-08 | Stage-boundary | Spatial region decomposition is presented as the preferred parallelism unit and safe by canonical sorting | The proposal treats spatial, static, and dynamic partitioning as workload-dependent; canonical sorting does not prove complete/duplicate-free task ownership | Require measured imbalance/locality plus ownership and parity tests before selection |
| C-09 | Stage-boundary | Hierarchical hashing is described as zero simulation-logic risk | Hash scheme identity, freshness, dirty invalidation, proof consumers, and replay/certification dependencies create correctness risk even if state evolution is unchanged | PERF-D5 and PA-03B establish policy; Gate A must show material cost before a tree is considered |
| C-10 | Stage-boundary | Performance M3 includes a concurrent Resolution job graph in the same epic | The proposal keeps Resolution serial and requires Gate B plus a separate architecture with read/write proof, conflict handling, staged mutation, and stronger commit semantics | Remove it from ordinary performance execution; retain only prerequisite measurement/domain evidence |
| C-11 | Stage-boundary | Performance M4 includes aggregate distant-region simulation as continuation of the performance epic | Aggregate simulation intentionally changes fidelity and state evolution | Require Gate B, a separate versioned semantic architecture, product acceptance bounds, migration, and SimQ/arena evidence |
| C-12 | Stage-boundary | Interest management already belongs to `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT` and the live-map roadmap | The proposal lists interest management as a conditional serving candidate | Keep existing ownership; this plan may measure serving cost but must not create a competing implementation scope |
| C-13 | Implementation-blocking | The policy, certification contract, engine contract, and live regression test disagree or omit clauses listed below | PERF-D4 requires one authoritative performance contract with explicit CI-fast and scheduled projections | PA-04 must reconcile/version each clause before Stage 4 promotion |
| C-14 | Stage-boundary | The phase-domain epic has standalone safety value but is linked as the hard prerequisite for the performance epic's presumed M3 concurrency work | PERF-D6 requires one catalog for identity/order/contracts/instrumentation, while concurrency remains unapproved | Preserve the declarative safety work; replace the presumed M3 continuation with Gate B and separate-architecture language |
| C-15 | Documentation drift | `docs/performance/optimization_architecture.md` describes 17 authoritative phases, universal `CandidateSelector` use, and a fully implemented five-layer stack | Live evidence and the proposal identify incomplete catalogs, direct phase paths, and contract drift | PERF-D4/PERF-D6 must classify current versus target behavior and update or supersede inaccurate P1 claims |
| C-16 | Documentation drift | `docs/architecture/performance_optimization.md` has active authority-P1 metadata while its body calls its RabbitMQ design superseded/historical | RabbitMQ/Kafka paths were removed; only separately verified surviving decisions remain relevant | Owner must mark the document's current scope/status unambiguously; no removed transport design enters this plan |
| C-17 | Authority-blocking | Drafting-time evidence on 2026-09-08 found the proposal and this plan untracked | Untracked artifacts are not durable shared authority | Re-check Git state at R0A; both files must be reviewed and committed/merged before they release implementation tickets; staging alone is insufficient |

### C-13 clause-level evidence

| Clause | Authority/document claim | Live gate behavior |
|---|---|---|
| Warmup/sample | Engine contract and baseline policy require at least 100/1,000 ticks | `test_perf_regression_baseline.py` runs 10/50 |
| Latency statistic | Policy describes p50/p95/p99 and engine contract says >5% average regression is flagged | Live test checks only average against `max(5 ms, baseline × 1.25)` |
| Memory | Policy requires RSS-delta and GC stability checks | Live regression test has no memory assertion |
| Missing baseline | Policy says commits must pass automated gates | Live test skips a missing baseline |
| RuntimeMode | Engine contract requires scoped RuntimeMode and the live test contains an excursion helper | The hard-scenario set is empty, so current scenarios use warning-only mode handling |
| Hardware | Baseline policy and certification contract publish conflicting class definitions | Live regression test selects the profile stored in each baseline and does not enforce the documented class matrix |

No conflicting existing plan is edited by this task. Conflict closure requires explicit
architecture-owner action because the affected documents have higher authority than this plan.

## 6. Dependency sequence

```text
R0A durability + owner assignment + evidence-only authority
 │
 └── PA-00 opens: draft PERF-D1..PERF-D6 charters
        ├── PA-03A hash audit ──────────────> PERF-D5 approval
        ├── PA-05A phase inventory/schema ─> PERF-D6 approval
        └── other repository evidence ──────> PERF-D1..PERF-D4 approvals
                                                   │
                                                   v
                         R0B reconcile/supersede conflicting P1 plans
                                                   │
       ┌───────────────────────────────────────────┼───────────────────────┐
       v                                           v                       v
 PA-01 after PERF-D1                         PA-04 after PERF-D4     PA-05B after PERF-D6
 PA-02 after PERF-D3                         PA-03B after PERF-D5
                                             (conditional or no-op)
       └──────────────────────────┬────────────────┴───────────────────────┘
                                  v
             PA-06 after stable PA-04/PA-05B identities and PERF-D1
                                  │
                                  v
 PA-07 after PA-01, PA-02, PA-03A, PA-04, PA-05B, PA-06, and PA-03B
 only when PERF-D5 changes schedule/schema/baseline identity
                                  │
                                  v
                  PA-08 Gate A report and owner decision
                         ├── reject/defer candidate
                         └── nominate Stage 5 ticket scope
```

PA-00 remains open across the evidence and approval steps; it does not pretend PERF-D5/PERF-D6
can be approved before their audits. PA-05A is inventory/schema/order-parity evidence only.
PA-05B is post-PERF-D6 authority promotion and generated-document reconciliation. PA-03B records
an explicit no-change disposition if PERF-D5 preserves current behavior; it changes code only
when the approved policy requires it. Stage 4 baselines wait for every correction or contract
that changes their identity or interpretation.

## 7. Execution phases

### R0A — Establish durability, owners, and evidence-only authority

Actions:

1. Review and merge the proposal and this plan as one durable planning change; staging alone does
   not satisfy this condition.
2. Assign an accountable person or team to each decision role: Architecture, Engine Architecture,
   Simulation Correctness, Simulation Semantics, Performance, Release/Certification, and
   Observability/Replay. Record assignments in
   `docs/architecture/performance_optimization_decisions.md`.
3. Assign an owner and initial status to C-01 through C-17.
4. Authorize only decision drafting, read-only repository inspection, PA-03A, and PA-05A. No
   runtime policy or baseline is changed in R0A. The affected P1 owners must record the
   evidence-only/no-behavior-change dispositions that release PA-03A and PA-05A.
5. Search existing tickets semantically by affected code, behavior, and deliverable—not only by
   PA label. For every overlap, record reuse, merge, close, supersede, or defer.

Artifacts:

- durable proposal and plan commits;
- named owner/role table and draft decision charters;
- conflict-disposition record in `docs/architecture/performance_optimization_decisions.md` with
  owner, status, and P1 change evidence for C-01 through C-17;
- semantic ticket-scope collision report.

Exit:

- proposal and plan are merged and registered;
- evidence-only PA-03A/PA-05A scopes and their P1-owner dispositions are approved;
- no runtime implementation package is released yet.

### Stage 0 — Architecture decisions

PA-00 stays open while it produces PERF-D1 through PERF-D6 in
`docs/architecture/performance_optimization_decisions.md`. Draft PERF-D1 through PERF-D4 from
repository evidence, run PA-03A before approving PERF-D5, and run PA-05A before approving
PERF-D6. Each record must include:

Dependency: R0A exit.

- decision and alternatives;
- evidence and assumptions;
- named approvers;
- authority/source-of-truth location;
- compatibility and migration consequences;
- dependent packages released or blocked;
- rollback/revisit condition.

Exit: PERF-D1 through PERF-D6 are approved by all named roles or each dependent package remains
explicitly blocked.

### R0B — Reconcile higher-authority plans

After Stage 0:

1. Apply C-01 through C-17 dispositions to the authority-P1 documents through their owners.
2. Select one navigation outcome:
   - the P1 design-enhancement roadmap remains the program authority and links this plan as its
     prerequisite execution detail;
   - this plan is promoted through an approved authority change and older overlapping epics are
     marked superseded; or
   - the proposal is rejected in whole or part and this plan is revised accordingly.
3. Regenerate `docs/REGISTRY.yaml` after status/authority changes.

Exit: one active prerequisite ordering is discoverable, every conflicting P1 document has an
explicit status, and released packages have both their PERF decision and P1-owner disposition.

### Stage 1 — Baseline corrections and hash audit

#### PA-01 — Zero-capacity semantics and signal correction

Dependency: PERF-D1 approval and R0B disposition of C-03/C-04.

- Apply PERF-D1-approved semantics independently to worker and queue capacity.
- Test unavailable, disabled, synchronous/local, configured-zero, idle, and saturated states.
- Verify the exact signal-to-`RuntimeMode` mapping.
- Audit affected LOCAL baselines and verification-level output.
- Use specification/corrected-golden oracles; do not require parity with false DEGRADED behavior.

Exit artifact: capacity contract, tests, and affected-baseline invalidation report.

#### PA-02 — Debt-harness correction

Dependency: PERF-D3 terminology and R0B release.

- Correct integer debt accounting in the long-run harness.
- Add non-empty debt fixtures and exact count assertions.
- Prove the measurement does not alter checkpoint state or workload admission.

Exit artifact: passing harness tests and a debt-pressure result fixture.

#### PA-03A — Hash behavior and policy audit

Dependency: R0A evidence-only authorization; PERF-D5 is deliberately not a prerequisite.

- Inventory flat-hash call sites and all digest consumers.
- Record scheme, state tick, computation tick, freshness, and replay/certification dependency.
- Measure hash contribution on approved size tiers.
- Compare implementation and documentation.
- Make no runtime schedule or algorithm change.

The FULL persistence path means `Kernel._phase_persistence()` when replay policy is `FULL`;
PA-03A also inventories finalization and any other direct calls.

Exit artifact: evidence report sufficient for PERF-D5.

#### PA-03B — Hash policy reconciliation

Dependency: PERF-D5, PA-03A, and R0B disposition of C-06/C-09.

- Start only after PERF-D5 and PA-03A.
- Apply the approved flat-hash schedule and metadata.
- Enforce same-scheme comparisons and current-state freshness.
- Never compare a hierarchical root to a flat digest as equal values.
- Update/version affected documentation and baselines.

If PERF-D5 approves no implementation change, PA-03B closes with a documented no-change
disposition and any required documentation clarification.

Exit artifact: hash-policy manifest, conformance tests, and baseline migration or no-change record.

### Stage 2 — Performance contract

#### PA-04 — Authoritative contract reconciliation

Dependency: PERF-D4 and R0B disposition of C-13/C-15.

The PERF-D4 authority must inventory and reconcile at least
`tests/perf/test_perf_regression_baseline.py`, any CI workflow that selects it,
`src/perf/regression_gate.py`, `docs/engine/performance_contract.md`,
`docs/engine/contracts/certification_contract.md`, and
`docs/performance/perf_baseline_policy.md`. It must define:

- scenario and workload identity;
- hardware/runtime class and DET-PORT tier;
- warmup, sampling window, repetitions, and variance;
- p50/p95/p99/maximum and memory rules;
- RuntimeMode and processed-work-cardinality validity;
- missing-baseline behavior;
- CI-fast versus scheduled/nightly/manual claim limits;
- baseline versioning and incompatibility behavior.

Exit artifact: one authoritative contract plus an executable mapping from every live gate to the
clauses it enforces. Missing required evidence cannot silently pass.

### Stage 3 — Phase identity and bounded observability

#### PA-05A — Phase inventory and catalog proposal

Dependency: R0A evidence-only authorization; PERF-D6 is deliberately not a prerequisite.

- Inventory every `run_phase()` call, named phase, direct phase-like call, and existing timing key.
- Explain the 39-versus-43 discrepancy by counted unit rather than choosing a number by assertion.
- Define one proposed catalog for identity, order, input/output domains, accepted update types,
  invariants, timing identity, and documentation generation.
- Validate catalog order against the handwritten path without letting the catalog drive execution.

Current sources must be recorded explicitly:

- executable invocation evidence: `src/engine/pipeline.py`;
- current authority-P1 prose: `docs/engine/authoritative_pipeline.md`;
- generated `AGENTS.md` wording:
  `tools/agent_orchestration_codex_adapter/generator.py::_AUTHORITATIVE_PIPELINE_NOTE`.

There is no verified single generator for all three surfaces today. PA-05A proposes one source
and generation/conformance command for PERF-D6; it does not assume that choice in advance.

Exit artifact: executable inventory, proposed catalog schema, and current-order parity report.

#### PA-05B — Catalog authority promotion

Dependency: PERF-D6, PA-05A, and R0B disposition of C-02/C-14/C-15.

- Start only after PERF-D6 and R0B.
- Make the PERF-D6-selected catalog normative metadata.
- Generate or validate the handwritten execution order exactly as PERF-D6 specifies; it must not
  become a second independent ordering authority.
- Regenerate dependent documentation and `AGENTS.md` through the selected source/generator.
- Keep catalog-driven execution disabled unless PERF-D6 explicitly approves a later transition
  gate with current-order parity.

Exit artifact: catalog authority, reproducible generation/conformance command, regenerated phase
inventory, and zero-drift tests across code/catalog/docs.

#### PA-06 — Bounded measurement schema

Dependency: PERF-D1 plus stable PA-04 and PA-05B identities.

- Add stable per-phase timing and relevant input/output cardinalities.
- Record the full scheduling funnel, sort/merge, Resolution, snapshot/freeze, serialization/IPC,
  hash, replay, projection, and queue contributions.
- Bound labels, buffers, per-tick trace size, and retention.
- Measure normal/detailed/audit observer overhead from identical checkpoints.
- Keep high-overhead profiling samples separate from clean performance samples.

Exit artifact: versioned schema, overhead report, and tests proving state parity and bounds.

#### PA-06B — Continuous performance-assurance control plane

Dependency: PA-04 identity/gate policy and PA-06 bounded measurement schema.

- Define a conservative change-impact map from source domains and change kinds to mandatory unit,
  checkpoint/replay E2E, Arena, SimQ, long-horizon behavioral, and performance lanes.
- Provide a bounded PR-fast tripwire for immediate regression feedback and a controlled
  confirmation tier for noisy or expensive capacity measurements.
- Treat missing selection/evidence, stale identity, excessive variance, unsupported execution,
  and exhausted retries as explicit non-pass outcomes.
- Separate known historical performance/SimQ debt by owner and expiry so it cannot hide a new
  candidate-versus-base regression.
- Reuse the SimQ audit classifications (`EXPECTED_DRIFT`, `REGRESSION`, `DA_NEEDED`, `NO_ACTION`);
  never move an anchor for an unexplained regression.
- Define a schema-valid evidence bundle and durable performance audit summary linking tests,
  identities, before/after measurements, Arena/SimQ outcomes, exceptions, and rollback state.
- Wire alert and ticket handoff for unexplained regression or design-acknowledgment outcomes.

Exit artifact: approved assurance matrix, tested impact selector, CI lane contract, known-debt
ledger, audit schema/template, and evidence that required lanes cannot silently skip or under-select.

### Stage 4 — Continuous assurance, scenario baseline, and Decision Gate A

#### PA-07 — Scenario materialization and baseline run

Dependency: PA-01, PA-02, PA-03A, PA-04, PA-05B, PA-06, PA-06B, and PA-03B only when
PERF-D5 changes schedule/schema/baseline identity.

The following are required evidence identities proposed by the architecture; they are not claims
that matching builders already exist:

- certification-small;
- gameplay-medium;
- world-large-sparse;
- world-large-dense;
- dense-hotspot;
- serving-high-client;
- debt-pressure;
- hash-intensive;
- snapshot/IPC-intensive.

Before measurement, PERF-D4/PA-04 must map each identity to a committed builder or checkpoint,
configuration, workload cardinality, hardware/DET-PORT tier, executor/backend, and required
repetitions. All nine identities require a disposition. `NOT_APPLICABLE` is allowed only when
PERF-D4 predeclares an applicability rule and the Performance and Release/Certification owners
approve it before PA-07 runs. `BLOCKED` means required evidence is missing and prevents Gate A;
an unsupported backend or unavailable fixture cannot be converted into a silent skip.

Each artifact records build/config/content/checkpoint identity, DET-PORT tier, executor, worker
count, RuntimeMode sequence, processed-work cardinality, observation level, latency distribution,
CPU/wall time, memory, variance, and control-trace validity where applicable.

The baseline run also executes every PA-06B-required checkpoint/replay E2E, Arena, SimQ, and
long-horizon lane. A green performance measurement does not compensate for a correctness,
conformance, or quality regression. Expensive scheduled checks may finish after the fast tripwire,
but they must finish before Gate A or optimization promotion as assigned by the assurance matrix.

Exit: every applicable scenario is reproducible, every scenario identity has a disposition, no
scenario remains `BLOCKED`, and no invalid mode, trace, identity, or heavy-observer run is
promoted as a clean baseline.

#### PA-08 — Gate A bottleneck report

Dependency: valid PA-07 evidence.

Rank end-to-end contributors by scenario, contribution, scaling slope, tail impact, memory impact,
and serial fraction. For every candidate in the proposal, record one disposition:

- selected for Stage 5 ticket scoping;
- rejected because evidence is negative;
- deferred because evidence is insufficient;
- owned by another existing program;
- escalated to Stage 6 because it changes semantics or authority.

PERF-D4 must define numerical or comparative materiality thresholds per scenario before PA-07
runs. Gate A passes only when:

1. PA-07 has a valid disposition for every scenario, no scenario is `BLOCKED`, and each
   `NOT_APPLICABLE` disposition satisfies a predeclared PERF-D4 rule.
2. Every selected candidate exceeds its predeclared materiality threshold in at least one target
   scenario.
3. Every selected candidate has a reference path, correctness oracle, adoption threshold, memory
   bound, rollout/rollback strategy, and named owner.
4. Required test, E2E, Arena, SimQ, long-horizon, and audit evidence is present and passing or has
   an explicitly approved `NOT_APPLICABLE` disposition from the predeclared impact contract.
5. The Performance, Engine Architecture, and Simulation Correctness owners all approve
   `docs/performance/performance_optimization_gate_a.md`.

Gate A approval authorizes normal ticket creation for the selected candidates; it does not approve
or merge their implementation.

## 8. Candidate authorization after Gate A

Gate A may nominate, but does not implement, these exact workstreams:

| Workstream | Required evidence before ticket creation |
|---|---|
| Scan/due/index tightening | Material scheduler/full-scan cost; canonical eligibility oracle and scan fallback |
| Typed phase-input routing | Material repeated routing scans; insertion-order and full-path parity |
| Deterministic memoization | Material pure-function cost, stable complete key, reuse rate, bounded memory |
| Hierarchical hashing | PERF-D5-approved policy plus material flat-hash cost and independent flat audit |
| Snapshot/IPC improvement | Material freeze/serialization/IPC cost on supported backend |
| Dynamic Collection balancing | Measured imbalance/tail cost; ownership completeness and executor parity |
| Narrow SoA Collection view | Demonstrated homogeneous hot loop; construction cost included |
| Interest management | Material serving cost and confirmation that the existing live-map epic owns implementation |

Resolution concurrency and approximation never enter this table. They remain Stage 6 and require
Gate B plus separate architecture approval.

### Gate B boundary

Gate B is the post-Stage-5 complete-matrix decision described by the source proposal sections
15.1 and 20. Its evidence is the PA-07 matrix rerun after all selected Stage 5 work is either
promoted, rejected, or rolled back. The Performance, Engine Architecture, and Simulation
Correctness owners record whether exact optimization met the approved capacity targets.

- If Stage 5 work ran, Gate B evaluates its final clean matrix.
- If Gate A selected no Stage 5 work, Gate B may record “no exact work selected”; this does not
  prevent a separately justified semantic proposal, but that proposal must show that exact options
  were considered and why product scale still requires semantic change.
- Gate B never authorizes Resolution concurrency or fidelity change directly. It only supplies
  evidence to a new authority-reviewed architecture proposal.

## 9. Validation and correctness matrix

| Change category | Required oracle | Minimum assurance |
|---|---|---|
| Verified defect correction | Approved specification or corrected golden; intentional difference from broken output documented | Unit/property plus affected E2E/Arena/SimQ and baseline invalidation |
| Contract/document reconciliation | All authorities and executable gates agree; generated artifacts reproduce from source | Contract/gate conformance and under-selection tests |
| Observability-only | Identical canonical state; bounded buffers/labels; measured observer overhead | Observer OFF/light/detail/audit parity plus performance comparison |
| Semantics-preserving accelerator | Canonical state and ordered authoritative outcomes match the reference path | Unit, differential E2E, affected Arena/SimQ/behavioral lanes, paired performance, audit summary |
| Serving-only accelerator | Client presence/absence cannot change authority; gap/resnapshot behavior passes | API/E2E, serving load, passive-client, memory/backpressure, audit summary |
| Semantic change | Out of this plan; versioned expected differences, migrations, invariants, and product-quality bounds | Separate architecture plus explicit Arena/SimQ acceptance and migration audit |

The applicable matrix includes local/thread/process backends, supported worker counts, randomized
worker delay/completion order, multiple `PYTHONHASHSEED` values, cache/index present/absent/rebuilt,
checkpoint/restore continuation, normal versus audit observation, same-scheme hash checks, and
PERF-D2-approved runtime/hardware profiles.

## 10. Ticketization and ownership

- R0 is a planning/architecture reconciliation, not an engine ticket.
- PA-00 may become one decision umbrella with six independently approvable records, or six small
  decision tickets if owners differ.
- PA-01, PA-02, PA-03A, conditional PA-03B, PA-04, PA-05A, PA-05B, and PA-06 should be
  independently reversible tickets unless investigation proves a shared-file dependency requires
  a narrower sequence.
- PA-06B is the assurance-control foundation; its impact routing and CI/audit mechanisms should be
  independently ticketed where ownership differs.
- PA-07 is scenario/baseline and assurance-matrix materialization after prerequisite identity
  stabilizes.
- PA-08 is a decision report, not an optimization implementation ticket.
- Stage 5 candidates receive new tickets only after Gate A.
- Stage 6 candidates require new architecture proposals; they must not be children of this plan.

Every ticket investigation must re-read live code. The evidence in the proposal and this plan is a
baseline, not permission to carry a stale claim into implementation.

## 11. Documentation update map

| Decision/package | Expected documentation surface |
|---|---|
| R0 | Existing P1 roadmap/epics, proposal/plan cross-links, supersession status |
| PERF-D1/PERF-D2 | `docs/engine/deterministic_execution.md`, replay/control-trace contracts, certification claims |
| PERF-D3/PA-02 | Work-debt terminology and harness documentation |
| PERF-D4/PA-04 | Performance contract, certification contract, baseline policy, live gate documentation |
| PERF-D5/PA-03A/B | Hash policy, `docs/engine/deterministic_execution.md`, checkpoint/replay schema, baseline identity |
| PERF-D6/PA-05A/B | Catalog authority, generated authoritative-pipeline inventory, phase-domain references |
| PA-06 | Observability schema, retention/bounds, benchmark protocol |
| PA-06B | Test-impact matrix, CI gate semantics, known-debt quarantine, audit schema/template, optimization audit ledger |
| PA-07/08 | Versioned benchmark/assurance artifacts and Gate A decision record |

Behavior-changing tickets must update parity-ledger entries in the same workflow where required.
Generated `AGENTS.md` or generated inventories must be changed through their generator.

## 12. Risks and stop conditions

| Risk | Stop condition | Recovery |
|---|---|---|
| P2 plan silently overrides P1 program | Conflicting ticket is about to be created without P1 disposition | Stop ticketing; return to R0 |
| Broken baseline becomes golden | Run has invalid mode/trace/identity or changed workload | Invalidate artifact and rerun after correction |
| Measurement perturbs behavior | Observer level changes state, admission, or mode | Reduce/disable instrumentation; keep run only as overhead evidence |
| Catalog becomes a second registry | Identity/order differs from live execution or another authority | Do not promote catalog; reconcile under PERF-D6 |
| Hash proof becomes ambiguous | Scheme/tick/freshness absent or different schemes compared | Reject proof; recompute under the approved scheme |
| Conditional candidate becomes presumed roadmap | Ticket lacks Gate A contributor evidence | Reject/defer ticket |
| Derived structure loses fallback | Failure can omit/duplicate authoritative work | Block promotion and restore reference path |
| Changed-file routing misses a relevant lane | Core/state/phase change selects no E2E, Arena, SimQ, or performance coverage | Fail selector; use conservative broad fallback and repair the map |
| Existing red lane hides new drift | Informational/known-debt status masks candidate delta | Compare base/candidate, classify new delta, block promotion, assign owner/expiry |
| Baseline or anchor is refreshed to make CI green | No approved cause, compatible identity, and audit record | Reject refresh; retain failure and create regression/DA ticket |
| Stage 6 leaks into performance work | Fidelity, Resolution authority, or commit semantics change | Stop; require separate architecture approval |

## 13. Completion and handoff

This plan reaches its terminal outcome when PA-08 publishes an approved Gate A report and all
prerequisite artifacts are durable and traceable. Handoff then consists of:

1. selected Stage 5 ticket candidates with evidence and owners;
2. rejected/deferred candidate dispositions;
3. any separate Stage 6 proposal requests;
4. reconciled P1 roadmap/epic status;
5. the baseline and validation artifacts used by Gate A;
6. the active fast/targeted/scheduled assurance routes, durable audit summaries, and regression
   alert/ticket ownership that remain after this plan closes.

If Gate A finds no material candidate worth its complexity, “no Stage 5 optimization authorized”
is a successful outcome.

## 14. Sources

- `docs/brainstorm/codex/system-design/performance_optimization_architecture_proposal.md`
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
- `src/engine/kernel.py`
- `src/engine/pipeline.py`
- `src/engine/worker_manager.py`
- `src/engine/governor.py`
- `src/engine/checkpoint.py`
- `src/perf/bench_harness.py`
- `src/perf/long_run_harness.py`
- `src/perf/regression_gate.py`
- `tests/perf/test_perf_regression_baseline.py`
- `tools/agent_orchestration_codex_adapter/generator.py`
