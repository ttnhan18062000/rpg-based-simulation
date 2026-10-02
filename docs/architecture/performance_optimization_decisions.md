---
status: active
layer: architecture
authority: P2
audience: agent
tags: [performance, architecture, governance, determinism, review]
---

# Performance Optimization Decisions

Decision-record home named by `performance_optimization_prerequisite_execution_plan.md` (R0A,
Stage 0). Created by `TCK-20260913-PERF-M0-OWNER-TRIAGE` on 2026-10-02. This file records
dispositions and decision records; it does not change any behavior, and it does not edit or
supersede any authority-P1 document. A planner review is not owner approval (§1.3).

Status of this version: PERF-D1, D2, D4 and D6 were drafted by the planner session and **approved by the repository owner on 2026-10-03**; PERF-D3 is closed; PERF-D5 stays empty until the hash call-site inventory exists. Approval accepts the decisions. No P1 document is changed by this file, and each P1 edit a decision requires is applied by its own ticket.

## Working scale target (owner decision, 2026-10-03)

The owner asked the planner to proceed on its own recommendation. The recommendation, which the
owner can replace at any time, is:

| Use | Target | Source |
|---|---|---|
| Exact-optimization program (Gate A materiality, Gate B success) | The targets already published in `docs/performance/perf_baseline_policy.md` §2.2: 10,000 entities under 50 ms per tick on a Class A host, 2,500 under 40 ms on Class B, 500 under 30 ms on Class C | Existing P1 text; adopted, not invented |
| Data-oriented core proposal (sizing only) | 100,000 entities at 10 ticks per second on a Class A host | Planner's proposal for "very big"; an order of magnitude past the published Class A target |

Hardware classes are those of `docs/engine/contracts/certification_contract.md` §3 (PERF-D4).
For orientation only: one unrepeated 2026-09-14 observation put a 1,000-entity scenario near
270 ms per tick on a development sandbox, on a scenario builder later found defective. It is not
a baseline, and the distance to target is unknown until M4 measures it.

## Owner decisions in force (2026-10-02)

Both are recorded in `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md`,
section "Plan review, 2026-10-02". They are quoted here by reference; that section is the source.

**Ownership model** (roadmap, "Ownership model (owner decision, 2026-10-02)"):

| Function | Held by |
|---|---|
| Planning, decision drafting, and review of every PERF-D record, conflict disposition, and implementation evidence | The `perf-planner` session |
| Implementation of dispatched tickets | The `perf-implementer` session |
| Accountable approval of anything that amends or supersedes an authority-P1 document, activates a behavior change, or accepts a baseline | The repository owner |

The same section says the ten role names survive only as review perspectives and that "no named
owner" is no longer an approval blocker.

**Technology direction** (roadmap, "Technology direction (owner decision, 2026-10-02)"): the owner
directed that the performance program prefer "a modern, widely adopted stack, framework, or design,
even when it is more complex than a minimal local fix", applied first to measurement and assurance
tooling, with determinism, the single authoritative owner, and typed durable state not relaxed. Read
the roadmap section for the full wording and the status of the standing exclusions.

## 1. Review matrix

### 1.1 Role names mapped to the three functions

Every role name used by the three sources below maps to exactly one function. The M0 epic's own
"Entry conditions" paragraph already says the ten names are covered "as review perspectives", so each
role is a perspective from which the planner function reviews; none is a separate approver.

Sources: **E** = ten roles in `performance_m0_architecture_governance_epic.md` Entry conditions;
**R** = seven roles in the prerequisite plan's R0A action 2; **A** = owner groupings in the conflict
review's §6 approval matrix.

| Role name | In E | In R | In A | Function it maps to |
|---|---|---|---|---|
| Architecture | yes | yes | yes | Planning and review (`perf-planner`), as a review perspective |
| Engine Architecture | yes | yes | yes | Planning and review (`perf-planner`), as a review perspective |
| Simulation Correctness | yes | yes | yes | Planning and review (`perf-planner`), as a review perspective |
| Simulation Semantics | yes | yes | yes | Planning and review (`perf-planner`), as a review perspective |
| Performance | yes | yes | yes | Planning and review (`perf-planner`), as a review perspective |
| Release/Certification | yes | yes | yes | Planning and review (`perf-planner`), as a review perspective |
| Observability/Replay | yes | yes | yes | Planning and review (`perf-planner`), as a review perspective |
| Testing/CI | yes | no | no | Planning and review (`perf-planner`), as a review perspective |
| Arena | yes | no | no | Planning and review (`perf-planner`), as a review perspective |
| Simulation Quality | yes | no | no | Planning and review (`perf-planner`), as a review perspective |
| "Owners of each affected P1 document" | no | no | yes (P1 migration row) | Repository owner (approver of P1 changes) |

Implementation of dispatched tickets is held by `perf-implementer`; it is not a role name in any of
the three sources, so no role row maps to it. Nothing here names a person or team that the owner
did not decide.

### 1.2 Decisions mapped to functions and perspectives

"Perspectives" are the role names from the conflict review's §6 matrix. "P1 documents affected" are
the documents the review's §5 table says the decision would change; if any, the repository owner's
accountable approval is required before the change, and until then the decision is a draft.

| Decision | Perspectives to review from | Draft and review | Implement evidence | P1 documents affected (owner approval needed) |
|---|---|---|---|---|
| PERF-D1 determinism contracts | Architecture, Simulation Correctness | planner | implementer (evidence tickets only) | `determinism_envelope_epic.md`, `docs/engine/deterministic_execution.md` |
| PERF-D2 portability | Architecture, Release/Certification | planner | implementer | `docs/engine/deterministic_execution.md` |
| PERF-D3 debt meaning | Simulation Semantics | planner (closed, §3.2) | none | none (matches current behavior) |
| PERF-D4 performance contract | Performance, Release/Certification | planner | implementer | performance, certification and baseline contracts (`performance_contract.md`, `certification_contract.md`, `perf_baseline_policy.md`) |
| PERF-D5 hash policy | Simulation Correctness, Observability/Replay | planner | implementer (PA-03A audit) | `docs/engine/deterministic_execution.md` if a hash boundary changes |
| PERF-D6 phase catalog | Engine Architecture | planner | implementer (PA-05A inventory) | `authoritative_pipeline.md`, `subphase_domain_contracts_epic.md` |
| Gate A prerequisite sequence | Performance, Engine Architecture, Simulation Correctness | planner | none | `design_enhancement_roadmap.md`, `performance_milestones_epic.md` |
| Stage 6 separation | Architecture, Simulation Correctness | planner | none | `performance_milestones_epic.md`, `subphase_domain_contracts_epic.md` |
| P1 migration/supersession | owners of each affected P1 document | planner drafts transition text | implementer applies once approved | every row above plus `docs/performance/optimization_architecture.md` and `docs/architecture/performance_optimization.md` |

### 1.3 Rules this matrix does not relax

- A review by `perf-planner` is not owner approval.
- A decision that changes a P1 document stays a draft until the repository owner accepts it.
- Activating a behavior change or accepting a baseline also needs the repository owner, whatever
  the document.
- No ticket of this program edits `src/` or accepts a baseline before the RPG-core entry gate in the
  roadmap's "RPG-core stability entry gate" is lifted.

## 2. Conflict dispositions C-01..C-17

Source of every disposition: `design_enhancement_roadmap.md` Section A, "C-01..C-17 disposition
(recorded 2026-09-13, per review)", which adopts the proposed dispositions in
`performance_optimization_conflict_approval_review.md` §4 with two corrections, plus the updates
this ticket was told to make from `TCK-20260913-PERF-M0-SOURCE-AUDIT`
(`stored_artifacts/TCK-20260913-PERF-M0-SOURCE-AUDIT/source_inventory.md`, "T01"). Nothing was
re-derived.

Evidence-status vocabulary: **re-verified here** (checked against the repository on 2026-10-02 by
this ticket); **re-verified by planner** (stated as still true in the roadmap's "Live-state
corrections" for 2026-10-02, not re-run here); **carried** (taken from the review brief, not
re-checked by this ticket); **T01** (measured by the source audit).

"Route" names who decides: P1-owner means the repository owner as approver of P1 changes (§1.3);
planner means drafting and review by `perf-planner`.

| ID | Type | Disposition | Evidence status | Route | Safe interim interpretation |
|---|---|---|---|---|---|
| C-01 | authority-blocking | Adopted. The P2 package does not supersede P1. Either the existing roadmap becomes parent authority with the P2 plan linked beneath it, or the owner promotes the plan through an explicit authority change; silent replacement is rejected. Roadmap Section A already states the P2 package "is not yet authorized to supersede this document". | carried | P1-owner (PERF-M0-T09) | `design_enhancement_roadmap.md` and the P1 epics stay controlling; the performance_optimization/ folder is review scope until M0 closes. |
| C-02 | documentation drift | Adopted, **updated**: the static `run_phase()` count in `AuthoritativeApplyPipeline.refine` is **44**, not 43. Keep the 39-phase `authoritative_pipeline.md` contract authoritative until counted unit, names, order and generation rules are reconciled; no blind number replacement. | re-verified here (AST count of `src/engine/pipeline.py::refine` = 44; `authoritative_pipeline.md` heading and table still say 39) | PERF-D6 (planner); PA-05A inventory by implementer | Treat 37, 38 (D19 audit), 39 (contract), 43 and 44 as different counted units, not one number with errors (T01 finding F-07). Quote no single count without naming its unit. |
| C-03 | implementation-blocking | Adopted with correction: the **worker-utilization half is already fixed** by `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER`; the **queue-utilization-zero half is open**. That fix landed ahead of PERF-D1, so **PERF-D1 ratifies or revises it**: it must define unavailable, disabled, synchronous and bounded-zero semantics separately for workers and for queues, using specification or corrected-golden tests rather than parity with false DEGRADED behavior. | re-verified here (`src/engine/worker_manager.py` returns `0.0` when `_max_workers` is 0 and `1.0` when `_max_queue_depth` is 0) | PERF-D1 (planner); P1-owner if P1 text changes | Worker-zero reports `0.0` (fixed). Queue-zero still reports `1.0`. Do not treat either value as final semantics, and do not tighten any gate on top of the queue-zero value. |
| C-04 | authority-blocking | Adopted. Both a Canonical/certification contract and a Live bounded contract are needed; PERF-D1 approves or rejects that explicitly, and if approved the P1 determinism epic and `deterministic_execution.md` are updated to describe both. Roadmap Section A groups C-03/C-04 for the worker-utilization correction; the fix itself concerns C-03's signal, and C-04's contract choice remains open. | carried | PERF-D1 (planner); P1-owner for the P1 edits | `deterministic_execution.md` and the determinism envelope epic stay as written; a run that ever reaches DEGRADED or SURVIVAL keeps its `REDUCED` verification label. |
| C-05 | implementation-blocking | Adopted. PERF-D1 classifies each semantics-affecting decision as recorded or derivable, proves replay sufficiency, defines corrupt/missing-trace behavior, and bounds trace size and retention. | carried | PERF-D1 (planner) | No claim that a Live run is reproducible from a mode-transition log alone. |
| C-06 | implementation-blocking (audit allowed) | Adopted. PA-03A is evidence-only and precedes PERF-D5; schedule, freshness, tree-hash and baseline changes stay blocked until PERF-D5. | re-verified here (`Kernel._phase_persistence` calls `CanonicalStateHasher.get_hash` directly at `src/engine/kernel.py:1186` and finalization at `:1255`; `BudgetedCanonicalHasher` is defined at `src/engine/checkpoint.py:141` and has no production caller, only `tests/unit/engine/test_resource_budget_gate.py`; `CanonicalHashScheduler` is defined at `src/engine/checkpoint.py:231` and is called only from `src/certification/harness.py` (lines 185 and 310), not from the kernel — so three hash classes exist: the kernel hashes directly, the budgeted wrapper is unused in production, and the scheduler governs only the certification harness) | PERF-D5 (planner); PA-03A by implementer | No hash-schedule mechanism governs the live persistence path; do not assume the budgeted wrapper or the scheduler describes it. Cost numbers wait for the entry gate. |
| C-07 | stage boundary | Adopted with correction: spatial decomposition, narrow SoA, memoization and hierarchical hashing stay **candidates**, not committed milestones; **M2 item 4 (DOD hot-path projection) is excluded** from the preselected set because the roadmap already gates it on its M1 measurement (unlike M2 items 3, 5, 6). | carried | Gate A (M4/M5) | No M2 implementation is approved solely because it is listed. |
| C-08 | stage boundary | Adopted. Partition choice needs measured imbalance and locality, deterministic ownership, complete and duplicate-free coverage, and executor parity; compare static, spatial, cost-aware and bounded-dynamic options. | carried | M5 selection | Canonical result sorting is not evidence of complete, duplicate-free task ownership. |
| C-09 | stage boundary | Adopted. Hierarchical hashing needs PERF-D5, same-scheme validation, scheme/tick/freshness metadata, tree-rebuild parity, independent flat auditing and a material Gate A cost. | carried | PERF-D5 (planner) | Hierarchical hashing is not described as zero-risk. |
| C-10 | stage boundary | Adopted. Concurrent Resolution leaves ordinary performance execution; domain/catalog safety work is retained; Gate B and a separate architecture proposal are required. The owner's technology direction (roadmap, "Technology direction") reopened this exclusion for evaluation under M6-T05; the interim interpretation is unchanged until that proposal is approved. | carried | Gate B (M6) | Resolution stays serial. |
| C-11 | stage boundary | Adopted. Aggregate simulation requires Gate B, a separate versioned semantic architecture, transition rules, migration, conservation/invariant tests and explicit SimQ/arena bounds. The owner's technology direction (roadmap, "Technology direction") reopened this exclusion for evaluation under M6-T05; the interim interpretation is unchanged until that proposal is approved. | carried | Gate B (M6) | Aggregation is a fidelity change, not an exact optimization. |
| C-12 | stage boundary | Adopted. Keep implementation ownership in `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`; the performance program may measure projection, serialization and queue cost and returns findings to that owner. | T01 (the epic exists, status OPEN, dispositioned "defer / no merge" for this reason) | owner of the live-map epic | No second interest-management implementation stream. |
| C-13 | implementation-blocking (baseline promotion) | Adopted. PERF-D4/PA-04 select one clause-level authority and map each clause to a CI-fast projection or scheduled evidence; preserve a cheap CI-fast smoke projection and keep it separate from capacity evidence. | re-verified by planner (regression gate still samples 10/50 ticks, average only, skips a missing baseline, has an empty hard-scenario set; 12 of 53 `assert_perf_threshold` call sites pass `hard=True`) | PERF-D4 (planner); P1-owner for contract edits | No baseline is promoted and no soft check becomes blocking, per the roadmap's entry gate. |
| C-14 | stage boundary | Adopted. Keep the compatible declarative phase/domain safety work under PERF-D6/PA-05; replace the automatic cross-epic M3 path with Gate B and separate-architecture wording. | carried | PERF-D6 (planner); P1-owner for `subphase_domain_contracts_epic.md` | Phase declarations are justified for identity, drift detection and instrumentation, not as a presumed step to concurrency. |
| C-15 | documentation drift | Adopted. Each P1 statement in `docs/performance/optimization_architecture.md` is classified as verified current behavior, target architecture or obsolete; inaccurate P1 claims are updated or superseded by their owner. | carried | PERF-D4/PERF-D6 (planner); P1-owner | Read that document's phase count and "universal" claims as target statements until classified. |
| C-16 | documentation-status drift | Adopted. The owner makes `docs/architecture/performance_optimization.md`'s status and scope unambiguous: keep verified surviving decisions, mark the removed RabbitMQ mechanism historical or superseded, do not revive removed transport design. | carried | P1-owner (PERF-M0-T09) | Treat the RabbitMQ mechanism as historical; this ticket does not edit the document. |
| C-17 | authority-blocking | **Resolved**, updated from T01: the proposal and the performance_optimization/ folder (11 files) are tracked in git since PR #185, and the folder is registered in `docs/REGISTRY.yaml`. Residual: the source proposal sits under the registry-skipped `docs/brainstorm/` tree and is never registered (T01 finding F-05). | T01 (`git ls-files`, `git log --diff-filter=A` showing `2f6b1551`; source_inventory.md §2) | none | The planning chain is durable; the residual registration gap does not block releasing evidence-only tickets. |

## 3. PERF-D decision records

### 3.1 Record template

Every PERF-D record carries all eleven fields below. There is no automated structural check yet; field
completeness is verified by reading (ticket assumption).

```markdown
### PERF-Dn — <title>

- **Status:** open | drafted | approved | closed | blocked
- **Context:**
- **Decision:**
- **Rejected alternatives:**
- **Trade-offs:**
- **Evidence:** (include remaining uncertainty)
- **Authority:** (source-of-truth location)
- **Named approvers:** (per §1; a planner review is not owner approval)
- **Compatibility:** (baseline and migration consequences)
- **Verification:** (required audit evidence, failure routing, accountable gate owner)
- **Child packages:** (released or blocked)
- **Revisit condition:** (revisit or rollback)
```

### 3.2 PERF-D3 — Capacity-debt semantics

- **Status:** closed (recorded 2026-09-13 in `design_enhancement_roadmap.md` Section A, "PERF-D1–D6
  disposition"; carried here).
- **Context:** the proposal's default is to keep aggregate counters as capacity debt and to create a
  separate authoritative semantic-deferred-work state only for a concrete feature contract
  (conflict review §2, PERF-D3 row).
- **Decision:** capacity debt is the aggregate counter; no semantic deferred-work queue is created by
  this program. A future one needs its own feature contract.
- **Rejected alternatives:** a semantic deferred-work state without a concrete feature contract
  (rejected by the proposal's default; the roadmap found no competing pattern in `src/`).
- **Trade-offs:** none material: the closure matches existing behavior, so nothing changes.
- **Evidence:** `AuthoritativeState.work_debt` is `Dict[str, int]` (`src/core/state.py:1423`) and the
  governor consumes the total as `work_debt_total: int` (`src/core/governance.py:32`, summed from
  `work_debt.values()` at `src/engine/kernel.py:543`). The roadmap's statement of "no competing
  semantic-deferred-work pattern anywhere in `src/`" was re-checked by perf-planner on 2026-10-02 with a keyword search of `src/` for `deferred_work`, `deferred_queue`, `deferred_updates`, `deferred_actions`, `deferred_intents`, `work_backlog`, `pending_work`, `carry_over` and `debt_queue`, which found no match, and `work_debt` is written only through `StateUpdate.work_debt_updates` and `WorkerResult.work_debt_update`. This is a keyword search, not a proof. Nuance for
  the record: the state holds integer counters keyed by system, and "aggregate int" describes the
  governor's total.
- **Authority:** `design_enhancement_roadmap.md` Section A (P1) and `src/core/state.py`.
- **Named approvers:** none required: no P1 document changes. Drafted and reviewed by `perf-planner`.
- **Compatibility:** no baseline or migration consequence.
- **Verification:** none new. Any proposal to add deferred-work state must open a new decision.
- **Child packages:** PERF-M0-T05 needs no investigation beyond this record.
- **Revisit condition:** a concrete feature contract that needs authoritative deferred work.

### 3.3 Stubs to be drafted by the planner

Each follows §3.1 and is intentionally empty.

#### PERF-D1 — Determinism contracts (Canonical and Live bounded)

- **Status:** **approved by the repository owner on 2026-10-03** as drafted by `perf-planner`.
  The P1 document edits it requires are not yet applied; `PERF-M0-T09` applies them.
- **Context:** `docs/engine/deterministic_execution.md` (P1) promises that sequential execution is
  bit-identical for the same seed and initial state. Three wall-clock inputs break that promise
  today, in every execution mode unless `audit_mode` is on:
  1. `ResourceGovernor._get_indicated_mode()` chooses `RuntimeMode` from `tick_compute_ms`, RSS
     memory, and worker/queue utilization (`src/engine/governor.py:76-109`); the mode then sets
     cadence, LOD, scan policy, and phase budgets.
  2. `Kernel._phase_resolution()` compares elapsed wall-clock time with
     `profile.max_tick_budget_ms` while processing results; when exceeded and `audit_mode` is off
     it drops the remaining results, records dropped work, and forces `DEGRADED`
     (`src/engine/kernel.py:614-616`, `:588`).
  3. An end-of-tick check records dropped work when the final compute time exceeds the budget
     after tick 5 (`src/engine/kernel.py:461-463`).

  `docs/engine/runtime_profiles.md` §4 (the same profile yields identical semantics on different
  hardware classes) is false for the same reason. `INFRA-363` labels a run that reached
  `DEGRADED`/`SURVIVAL` as `verification_level = REDUCED`, which discloses the problem per run and
  does not make any run reproducible. The P1 determinism envelope epic asks the maintainer to
  choose a canonical mode **or** a live bounded mode (conflict C-04).
- **Decision (proposed):** adopt **both**, as two named contracts for two uses.
  - **Canonical contract.** No wall-clock or host-resource reading may influence authoritative
    state. Pressure signals are deterministic proxies (work-unit counts, queue depth against a
    fixed ceiling, work debt); the mid-tick cutoff and end-of-tick drop are driven by a work-unit
    budget or are off. Guarantee: same build, configuration, seed, and initial state give the same
    canonical hash at every tick, whatever the host load. Required for certification, determinism
    and replay tests, Simulation Quality calibration, and any benchmark that claims hash parity.
  - **Live bounded contract.** Real wall-clock and resource signals are allowed. Every decision
    that changes what is computed is either written to a versioned, bounded control trace or is
    derivable from one that is. Guarantee: a Live run is reproducible **given its trace** — a
    Canonical-mode replay that consumes the trace reaches the same hashes. The trace is not
    predictable in advance, and that is accepted.
  - **Control-input classification (answers C-05):**

    | Decision | Treatment |
    |---|---|
    | `RuntimeMode` transition (tick, from, to) | Recorded |
    | Mid-tick cutoff: how many sorted results were applied before the drop | Recorded (the mode alone does not say which results were lost) |
    | End-of-tick dropped-work marker | Recorded |
    | Phase budgets emitted from measured sub-phase cost | Recorded as emitted values; the costs that produced them are not |
    | Scan policy, cadence, LOD, sweep interval | Derived from the recorded mode and budgets; a test proves the derivation |
    | Worker completion order | Not recorded; results are canonically sorted before resolution |
    | Frame pacing, GC timing | Not recorded; no effect on authoritative state |

  - **Zero-capacity semantics (answers C-03):** zero workers means synchronous execution, so
    worker utilization does not apply and reports `0.0`. This **ratifies** the fix made by
    `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER`. Zero queue depth with zero
    workers means no queue exists, and queue utilization likewise reports `0.0`. Zero queue depth
    with one or more workers is a configuration error and is rejected when the worker manager is
    built, instead of being reported as permanent saturation. Idle is `0.0`, saturated is `1.0`,
    and "unavailable" is never encoded as a utilization value.
  - **Tied worker results:** the sort key `(class_priority, -local_priority, entity_id)` is
    assumed total because entity ids are unique. System-level results that share id zero are not
    covered by that argument; `PERF-M1-T04` verifies it and this decision does not change the key.
- **Rejected alternatives:** Canonical only (the live server could not shed load under real
  pressure); Live only (certification and regression tests could not be reproduced, which is the
  current failure); keep `REDUCED` labeling alone (honest, but nothing becomes reproducible);
  record only mode transitions (insufficient: the mid-tick cutoff discards specific results the
  mode does not identify).
- **Trade-offs:** two pressure-signal paths to maintain and test; trace storage and a format to
  version; Canonical runs model overload in work units, so they do not exercise real timing
  behavior, which only Live runs do.
- **Evidence:** the code locations above, read on 2026-10-03;
  `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` records the same seed passing and
  failing `test_1000_tick_determinism` on consecutive runs through input 2, and
  `TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION` records a gameplay consequence.
  **Uncertainty:** the three inputs are the ones found by reading the governor and the kernel
  tick path; a complete inventory of wall-clock and host-resource reads that reach authoritative
  state has not been made. Whether zero queue depth with workers occurs in any shipped profile is
  not checked.
- **Authority:** `docs/engine/deterministic_execution.md` becomes the home of both contracts;
  `docs/plans/design_enhancement/determinism_envelope_epic.md` M1 item 1 is answered "both";
  `docs/engine/runtime_profiles.md` §4 is qualified to the Canonical contract.
- **Named approvers:** repository owner. Reviewed from the Architecture and Simulation
  Correctness perspectives by `perf-planner`.
- **Compatibility:** no behavior changes on approval; this is a contract. Existing results from
  runs without `audit_mode` cannot be claimed hash-stable. `verification_level = REDUCED` remains
  the label for a Live run without a verified trace. Baselines taken before the Canonical path
  exists are provisional.
- **Verification:** a test that two Canonical runs with artificially injected delay produce the
  same mode sequence and hashes; a trace-replay test for Live; a static inventory of wall-clock
  and resource reads in the tick path, re-runnable like the phase and hash inventories.
- **Child packages:** releases the design of `PERF-M1-T01` (zero-capacity) and `PERF-M1-T04`
  (tied results), and an evidence-only inventory ticket for wall-clock reads. Implementation of
  any of them edits `src/engine/` and stays blocked by the RPG-core entry gate. Gives the parked
  slow-regression ticket its fix direction (run those tests under the Canonical contract).
- **Revisit condition:** the control trace cannot be bounded; a new executor (free-threaded or
  native) adds a semantics-affecting input not in the table; the inventory finds a fourth input.
- Related dispositions: C-03, C-04, C-05.

#### PERF-D2 — Portability

- **Status:** **approved by the repository owner on 2026-10-03** as drafted by `perf-planner`.
  The edit to `docs/engine/deterministic_execution.md` is not yet applied (`PERF-M0-T09`).
- **Context:** the determinism contract does not say across which environments the guarantee
  holds. `pyproject.toml` allows Python 3.11 and later, CI runs 3.13, and the contract lists
  float-rounding edge cases as a known risk. The owner's technology direction adds compiled
  kernels and possibly a free-threaded interpreter, each of which is a new runtime identity.
- **Decision (proposed):** state the guarantee in tiers, and claim only what a test matrix proves.

  | Tier | Scope | Claim |
  |---|---|---|
  | DET-PORT-0 | Same build, same interpreter minor version, same OS and CPU architecture, sequential executor, Canonical contract | Guaranteed; this is the certification reference |
  | DET-PORT-1 | DET-PORT-0 environment with a different executor backend (thread, process) or worker count, and any `PYTHONHASHSEED` | Guaranteed only for backends and counts in a passing parity matrix; otherwise unclaimed |
  | DET-PORT-2 | Different OS, CPU architecture, interpreter minor version, or native-extension build | Not guaranteed; a combination is promoted to a claim only after it passes the same matrix |

  The reference runtime is the one CI runs (CPython 3.13 on Linux x86-64). Every benchmark
  result, baseline, and hash proof records its tier and its runtime identity: interpreter
  version and build flavor, OS, architecture, and the versions of any native kernels.
- **Rejected alternatives:** claim cross-platform determinism now (untested; float library and
  interpreter differences are a known risk); claim nothing beyond one machine (too weak — executor
  parity is already partly tested in `tests/perf/test_concurrency_parity.py`).
- **Trade-offs:** a hash proof is only comparable within its tier; moving the reference runtime
  invalidates DET-PORT-0 proofs and needs a migration note.
- **Evidence:** `pyproject.toml` (`requires-python >=3.11`), `.github/workflows/test.yml` (3.13),
  `docs/engine/deterministic_execution.md` "Known non-determinism sources".
  **Uncertainty:** which executor backends and worker counts pass parity today has not been
  measured; the current contract text calls concurrent mode out of scope, which DET-PORT-1 would
  replace only for combinations that pass.
- **Authority:** `docs/engine/deterministic_execution.md`, "Scope of the guarantee".
- **Named approvers:** repository owner. Reviewed from the Architecture and Release/Certification
  perspectives by `perf-planner`.
- **Compatibility:** none until a claim is promoted; existing artifacts gain a tier label when
  their identity is known and are otherwise treated as unlabeled.
- **Verification:** the parity matrix in the prerequisite plan §9 (backends, worker counts,
  randomized completion order, several `PYTHONHASHSEED` values), run under the Canonical contract.
- **Child packages:** feeds PERF-D4 (runtime and hardware identity fields) and `PERF-M2-T02`
  (benchmark identity schema). No ticket is released by this decision alone.
- **Revisit condition:** adoption of a native kernel, a free-threaded interpreter, or a second
  supported platform.

#### PERF-D4 — Performance-contract authority

- **Status:** **approved by the repository owner on 2026-10-03** as drafted by `perf-planner`.
  The edits to the three P1 documents are not yet applied (`PERF-M0-T09`, after `PERF-M2-T01`).
- **Context:** three P1 documents and the live gate disagree (conflict C-13).
  `docs/engine/performance_contract.md` and `docs/performance/perf_baseline_policy.md` require 100
  warmup and 1,000 sampled ticks; the gate runs 10 and 50. The policy specifies p50/p95/p99 and
  memory bounds enforced by `PerfRegressionGate`; that class has no consumer, and the gate checks
  only an average against `max(5 ms, baseline × 1.25)`. The policy's hardware classes conflict
  with `docs/engine/contracts/certification_contract.md` §3, which the policy itself notes. A
  missing baseline is skipped. Threshold checks warn by default.
- **Decision (proposed):**
  1. `docs/engine/performance_contract.md` is the single clause-level authority for how
     performance is measured, compared, and claimed.
  2. `docs/engine/contracts/certification_contract.md` §3 is the single definition of hardware
     class (the logical-cores **and** RAM rule). The baseline policy's table is removed in its
     favor.
  3. `docs/performance/perf_baseline_policy.md` becomes the calibration procedure only; its §3
     thresholds, which describe a mechanism that does not run, are moved into the contract as
     targets for the controlled projection or deleted.
  4. The contract defines two executable projections with different names and different claims:
     a **tripwire** (fast, every relevant PR, detects change, makes no capacity claim) and a
     **capacity run** (warmup and sample sizes from the contract, percentiles, memory, repeated,
     on a controlled runner). The current 10/50 average check is honestly the tripwire.
  5. Every projection returns `PASS`, `REGRESSION`, `INCONCLUSIVE`, or `NOT_APPLICABLE`. A
     missing or incompatible baseline is `INCONCLUSIVE`, never a skip that reads as success.
  6. Every result carries the PERF-D2 runtime identity, the PERF-D1 contract it ran under, the
     `RuntimeMode` sequence, and the processed-work count.
  7. Per the owner's technology direction, the projections are built on established tooling
     (`performance_stack_survey.md`, section A), not by extending the bespoke harness.
- **Rejected alternatives:** make the baseline policy the authority (it describes a mechanism
  with no consumer); keep three documents and reconcile wording only (the drift recurs); harden
  the existing checks first and write the contract later (blocking gates on a broken instrument).
- **Trade-offs:** the contract grows; the baseline policy loses content; gates that now pass
  silently will report `INCONCLUSIVE` until baselines exist.
- **Evidence:** the three documents as read on 2026-10-03;
  `tests/perf/test_perf_regression_baseline.py` (10/50 ticks, average only, skip on missing
  baseline, empty hard-scenario set); 12 of 53 `assert_perf_threshold` call sites pass
  `hard=True`; `perf_baseline_policy.md` §3's own 2026-08-08 correction note.
  **Uncertainty:** the clause-by-clause inventory (`PERF-M2-T01`) has not been done; this decision
  selects the authority and the shape, and the inventory may add clauses.
- **Authority:** `docs/engine/performance_contract.md`.
- **Named approvers:** repository owner. Reviewed from the Performance and Release/Certification
  perspectives by `perf-planner`.
- **Compatibility:** existing JSON baselines in `tests/perf/baselines/` are tripwire references
  only and carry no capacity claim. No gate changes state on approval; changing a warning to a
  failure reaches RPG-core PRs through the `perf-cert-arena` job and waits for the entry gate.
- **Verification:** `PERF-M2-T06`'s gate-conformance map: each live gate names the clauses it
  enforces; tests for absent baseline, stale identity, and percentile handling.
- **Child packages:** releases `PERF-M2-T01` (clause inventory, documents and read-only) now.
  `PERF-M2-T02` to `T06` follow owner approval and, where they change gate behavior, the entry
  gate. Gate A materiality thresholds are **not** set here: they need the owner's scale target.
- **Revisit condition:** the clause inventory finds a clause this shape cannot express; a hosted
  tracking service is adopted and changes what a result record contains.
- Related dispositions: C-13, C-15.

#### PERF-D5 — Hash policy
- **Status:** open — drafted by `perf-planner`. All other fields: pending.
- Related dispositions: C-06, C-09.

#### PERF-D6 — Phase-catalog authority

- **Status:** **approved by the repository owner on 2026-10-03** as drafted by `perf-planner`
  from the PA-05A inventory. The catalog itself is a `src/engine/` change and waits for the
  RPG-core entry gate; the P1 document edits are not yet applied (`PERF-M0-T09`).
- **Context:** the repository states 37, 38, 39, and 44 as "the" phase count. The inventory
  (`docs/performance/phase_inventory.md`, generated by `tools/perf/phase_inventory.py`) shows
  these are not one number with errors:
  - `AuthoritativeApplyPipeline.refine` makes 44 `run_phase()` calls, all with literal names,
    none conditional, 12 behind a feature flag. Beside them are 9 direct transformations of the
    update and 5 direct service calls that are not phases by that definition, including
    `FactionDecisionPhase.execute`.
  - `docs/engine/authoritative_pipeline.md` lists 39 names: it lacks 6 executable phases and
    lists one name (`active_contracts`) that matches none. The D19 audit states 38, lists 36,
    lacks 10, and has 2 unmatched entries. The generator note (39) and the sub-phase epic (37)
    state a count with no list.
  - `PhaseDependencyGraph.PHASES` (`src/engine/phase_graph.py`) declares 31 names. Fourteen
    executable phases are absent from it, and `should_run_phase()` returns `True` for an unknown
    name, so those fourteen run every tick with no cadence or dirty-set gating. It also declares
    `compactor`, which is not a `run_phase()` call.
  - `src/engine/phase_domain_permissions.py` is keyed by the seven kernel `TickPhase` members,
    a different unit with no name overlap.

  So there are four partial phase lists and none is checked against the code.
- **Decision (proposed):**
  1. **Counted unit.** A *refinement phase* is one `run_phase()` call in `refine`, identified by
     its name literal. Kernel `TickPhase` members are *kernel phases*. Prose says which one it
     means and never states a refinement-phase count as a literal number; counts are generated.
  2. **One catalog.** `PhaseDependencyGraph.PHASES` is extended into the single normative phase
     catalog: one typed entry per refinement phase, in execution order, carrying its scheduling
     metadata (what it has today), feature flag, and the read/write domain declaration the P1
     sub-phase domain-contract epic calls for. It is the existing typed structure the engine
     already consults; no second registry is created.
  3. **Execution authority stays with the handwritten `refine`.** The catalog is metadata. A
     conformance test fails when the catalog's names and order differ from the `run_phase()`
     calls found by `tools/perf/phase_inventory.py`, so a phase cannot be added without a catalog
     entry. Catalog-driven execution is not approved by this decision.
  4. **Glue is declared.** Each direct transformation or direct service call in `refine` is
     either moved behind `run_phase()` or listed in the catalog as declared non-phase glue with
     a reason. `FactionDecisionPhase.execute` and `compactor` are the first two to classify.
  5. **Documents follow the catalog.** The phase table in `authoritative_pipeline.md`, the
     generator note behind `AGENTS.md`, and the count in `CLAUDE.md` are generated from, or
     checked against, the catalog. D19 is marked a historical snapshot.
  6. **The declarations are the on-ramp for access-declared scheduling.** The read/write domains
     recorded per phase are the same information an ECS-style scheduler needs
     (`data_oriented_core_proposal_scope.md`, scheduling layer), so this decision and that
     proposal share one declaration format instead of two.
- **Rejected alternatives:** a new YAML registry (a second source beside the typed structure the
  engine already reads); making the document table the source (prose cannot be enforced against
  code and has already drifted by 6 phases); choosing 39 or 44 as the official number (the
  count changes with every RPG-core phase; one was added between 2026-09-08 and 2026-10-02);
  driving execution from the catalog now (changes the engine's control flow for no measured gain).
- **Trade-offs:** adding a phase now takes a catalog entry and a domain declaration, by design;
  the fourteen unlisted phases need declarations written by people who know their semantics;
  generated prose is less readable than handwritten prose.
- **Evidence:** `docs/performance/phase_inventory.md` and `.json`;
  `src/engine/phase_graph.py:82-83`. **Uncertainty:** whether the fourteen phases were left out
  of the graph deliberately (always-run by intent) or by omission is unknown, and whether
  `active_contracts` is a renamed `contracts` phase is unverified. The always-run behaviour is a
  possible cost, not a measured one.
- **Authority:** `src/engine/phase_graph.py` (the catalog) with
  `docs/engine/authoritative_pipeline.md` as its documented contract.
- **Named approvers:** repository owner. Reviewed from the Engine Architecture perspective by
  `perf-planner`.
- **Compatibility:** no behaviour change on approval. Giving a currently-unlisted phase real
  skip or cadence metadata would change behaviour; that is out of this decision and needs its
  own ticket with a parity oracle. New entries start as "must run every tick", which preserves
  what happens today.
- **Verification:** the conformance test above; `tools/perf/phase_inventory.py --check` as the
  drift report; regenerated documents reproduce from the catalog.
- **Child packages:** releases the design of `PERF-M3-T01` and `T02` and the P1 sub-phase
  domain-contract epic's declaration work. All of them edit `src/engine/` and wait for the
  RPG-core entry gate. RPG-core tickets that add a phase before then are unaffected, and the
  drift report shows what to backfill.
- **Revisit condition:** approval of the data-oriented core proposal (the catalog would become
  its system registry); a need to reorder phases at runtime.
- Related dispositions: C-02, C-14, C-15.

## 4. Open findings carried forward (not fixed here)

From `TCK-20260913-PERF-M0-SOURCE-AUDIT` (source_inventory.md §4), carried into the dispositions above
rather than fixed:

| ID | Finding | Where it matters |
|---|---|---|
| F-05 | The source proposal is tracked but never registered, because `tools/generate_registry.py` skips `docs/brainstorm/`. | C-17 residual; decide whether "registered-source" should cover it |
| F-06 | `TCK-20260825-EPIC-PERFORMANCE-EVOLUTION` and `TCK-20260825-EPIC-SUBPHASE-DOMAIN-CONTRACTS` were named by the P1 plans and never created. | C-01 and PERF-M0-T09 (which P1 plans have tracking tickets) |
| F-07 | 38 (D19 audit), 39 (contract), 43 (earlier static count) and 44 (static count on 2026-10-02) are different counted units. | C-02, PERF-D6 |
| F-08 | `docs/REGISTRY.yaml` regenerates from the working tree, not from git `HEAD`, so uncommitted edits are registered. | any claim that a doc is "registered" |

Found while writing this ticket:

| ID | Finding | Where it matters |
|---|---|---|
| F-09 | Roadmap Section A groups the worker-utilization correction under "C-03/C-04", but the fix concerns C-03's signal; C-04 is the Canonical-versus-Live contract choice. | C-04 row; planner may want the roadmap wording clarified |
| F-10 | `performance_optimization_gate_a.md` (cited in the prerequisite plan) and the other PERF-D decision-record bodies do not exist yet; this file is the first of the planned deliverables. | T01 finding F-01 now satisfied for the decisions file only |
| F-11 | "Aggregate int" for `work_debt` simplifies a `Dict[str, int]` of per-system counters (see §3.2). | PERF-D3 wording |
