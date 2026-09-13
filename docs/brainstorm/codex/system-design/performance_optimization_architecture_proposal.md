---
status: active
layer: performance
authority: P2
audience: developer
---

# Performance Optimization Architecture Proposal and Evidence-Gated Execution Plan

Date: 2026-09-07
Last revised: 2026-09-08
Status: canonical architecture proposal and prerequisite execution plan; conditional optimizations not approved
Scope: performance architecture for the deterministic, single-authority simulation engine
Authorization: after architecture approval, prerequisite packages may enter the normal ticket workflow;
Stage 5 and Stage 6 remain unauthorized

Readiness: **ready for architecture review and for prerequisite work through Decision Gate A; not
ready to authorize conditional optimization workstreams.** Measured workload contribution, a
reconciled benchmark contract, and approved determinism semantics must select later work.

This document is the canonical performance architecture and gated execution plan. Architecture
decisions remain subject to their named approvers; repository behavior and higher-authority
contracts override unapproved proposal text. The phase catalog, performance contract,
determinism contract, and hash policy must each identify one source of truth. Generated
documentation must be regenerated from its authority rather than hand-edited, and this proposal
must not be forked into parallel evolving architecture documents.

## Executive proposal

Evolve the engine through a measured optimization ladder:

```text
establish truthful measurements
        ↓
eliminate unnecessary work
        ↓
reuse deterministic work
        ↓
reduce data movement
        ↓
improve hot-path memory layout
        ↓
improve parallel load balancing
        ↓
change simulation fidelity only as a last resort
```

This ordering preserves the engine's defining architecture: immutable parallel Collection,
canonical ordering, one authoritative writer, and deterministic application through the
refinement pipeline. It deliberately does not recommend an ECS rewrite, distributed authority,
or immediate parallelization of Resolution.

Most techniques in this proposal are established designs from parallel computing, incremental
computation, data-oriented game engines, and high-performance scheduling. The project-specific
contribution is their composition and adoption order under this engine's determinism and
single-authority constraints.

## 1. Context and corrected baseline

### 1.1 Load-bearing constraints

Performance work must preserve:

1. One authoritative world state.
2. The Singular Bottleneck Law: authoritative changes are represented as `StateUpdate` and pass
   through the authoritative refinement pipeline.
3. Immutable/read-only state during parallel Collection.
4. Canonical semantic ordering independent of worker completion order.
5. Bounded memory, queues, worker counts, replay, and observability.
6. Passive clients that consume authoritative projections rather than simulate the world.

The performance objective is therefore not simply maximum ticks per second. It is the largest
useful simulated world that can meet a declared tick budget without making canonical semantics
depend unintentionally on wall-clock timing, worker scheduling, machine pressure, or client
presence.

### 1.2 Current-state corrections

Several earlier brainstorm artifacts contain premises that have drifted from the live code:

- `src/engine/pipeline.py` currently contains **43** `run_phase()` calls. Older materials refer to
  37 or 39 phases.
- `Kernel._phase_persistence()` directly calls `CanonicalStateHasher.get_hash()` on every tick
  whose replay policy is `FULL`. `BudgetedCanonicalHasher` exists but is not used on that path.
- `WorkerManager.get_stats()` reports `worker_utilization = 1.0` when `max_workers == 0`.
  It uses the same `1.0` fallback when `max_queue_depth == 0`. `ResourceGovernor` interprets either
  utilization at or above `0.9` as DEGRADED pressure, and DEGRADED policy changes cadence,
  budgets, LOD-related selection, and opportunistic work. This is capable of affecting both
  benchmark validity and simulation evolution. Local performance profiles configure zero workers,
  so the worker case is exercised by the standard benchmark path.
- Work debt is presently aggregate `Dict[subsystem_id, int]` accounting. It is not a durable queue
  of original deferred operations with entity identity, snapshot version, preconditions, or expiry.
- Per-tick timing already covers the seven macro phases, while refinement timing is grouped into
  coarse subphase families. The current harness does not yet expose all 43 `run_phase()` calls as
  individual latency distributions with input cardinality.
- Nominal hardware/entity targets already exist in `docs/performance/perf_baseline_policy.md`, but
  that policy records a hardware-class conflict with the certification contract and explicitly
  says the live CI test does not use the documented `PerfRegressionGate`. The live regression test
  samples 50 ticks after 10 warmup ticks, checks average compute time with a 25%/5 ms allowance,
  skips missing baseline files, and has no hard RuntimeMode scenarios configured. These facts do
  not satisfy the stronger 100/1,000-tick, percentile, memory, and mode-stability contract.
- `src/perf/long_run_harness.py` treats each integer work-debt value as if it had `len()`. A run
  carrying non-empty debt can therefore fail in the measurement harness instead of reporting it.

These corrections are prerequisites for interpreting measurements and should be reflected in any
future roadmap derived from this proposal.

### 1.3 Controlled classification vocabulary

Every evidence finding and work package uses exactly one label from this vocabulary:

| Label | Meaning |
|---|---|
| Required architecture decision | A named authority must choose a contract or policy before dependent work proceeds |
| Verified defect correction | Repository authority already defines expected behavior and executable behavior contradicts it |
| Verified behavior | An executable or documented fact, without implying that it is defective |
| Documentation drift | Documentation or generated inventories disagree with executable reality |
| Contract ambiguity | Authorities or executable surfaces do not establish one intended behavior |
| Measurement gap | Existing observation cannot support a claimed conclusion |
| Required measurement | Evidence-producing work that does not change the measured behavior or workload admission |
| Architectural enablement | Structure or contract reconciliation that preserves behavior and does not authorize a conditional accelerator |
| Low-risk optimization | Exact optimization on an established boundary with a demonstrated material cost |
| Conditional exact optimization | Semantics-preserving accelerator requiring Gate A evidence and adoption tests |
| Conditional serving optimization | Client/projection accelerator that cannot affect authoritative simulation |
| Semantic change | Change to admitted work, fidelity, ordering, or state evolution requiring separate approval and versioning |

### 1.4 Current-state evidence

| Finding | Classification | Repository evidence | Operational impact | Required response |
|---|---|---|---|---|
| The refinement method has 43 `run_phase()` call sites | Documentation drift | `src/engine/pipeline.py::AuthoritativeApplyPipeline.refine` | Counts and inventories based on 37/39 are incomplete | Inventory executable order and generate documentation from one catalog |
| Authoritative docs say 39; the older audit/epic describe 37 plus direct calls | Documentation drift | `docs/engine/authoritative_pipeline.md`; `docs/audits/D19_domain_phase_inventory.md`; `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`; generated `AGENTS.md` | Architecture enforcement and future feature admission use inconsistent inventories | Reconcile through the generator/authoritative source, not hand-edit generated files |
| `PhaseDependencyGraph` claims 17 phases, contains only a subset, and runs unknown names | Contract ambiguity | `src/engine/phase_graph.py::PhaseDependencyGraph` | New phases silently receive broad always-run behavior | Complete catalog and reject or explicitly classify unregistered phases |
| Seven macro timings and about 22 refinement-family timings exist; all-43 timing/cardinality does not | Measurement gap | `src/engine/kernel.py::_tick_once_inner`; `src/engine/pipeline.py` `costs[...]`; `src/perf/bench_harness.py` | Cannot attribute phase growth or normalize phase cost by relevant work | Add stable per-phase timing and bounded cardinality metrics |
| FULL replay persistence directly computes the flat canonical hash | Verified behavior | `src/engine/kernel.py::_phase_persistence`; `src/engine/checkpoint.py::CanonicalStateHasher` | Full state serialization can enter ordinary tick cost | Audit intent, freshness, dependencies, and cost before D5 |
| `BudgetedCanonicalHasher` and `CanonicalHashScheduler` exist but are not used by that kernel path | Documentation drift | `src/engine/checkpoint.py`; repository call-site search | Documented scheduling/rate limiting does not govern live persistence | Reconcile only after D5, without exposing a stale digest as current proof |
| Zero worker capacity reports worker utilization `1.0` | Verified behavior | `src/engine/worker_manager.py::get_stats` | The value can be interpreted as saturated capacity even when the pool is disabled or unavailable | D1 must define zero-worker semantics before correction |
| Zero queue capacity reports queue utilization `1.0` | Verified behavior | `src/engine/worker_manager.py::get_stats` | Queue semantics may differ from worker-pool semantics and must not be assumed | Define queue-zero semantics independently if its contract differs |
| Utilization at or above `0.9` produces DEGRADED pressure | Verified behavior | `src/engine/governor.py::_get_indicated_mode` | Either zero-capacity value can change cadence, budgets, replay, and admitted work | Add signal-to-mode specification tests |
| Standard LOCAL performance profiles configure zero workers | Verified behavior | `src/perf/profiles.py::PERF_PROFILES`; `src/perf/bench_harness.py` | The standard local route is exposed to the zero-worker interpretation | Audit historical local results and RuntimeMode sequences after D1 |
| Work debt is an aggregate integer per subsystem | Verified behavior | `src/core/state.py::AuthoritativeState.work_debt`; `src/engine/scheduler.py`; `src/engine/executor.py` | It records capacity shortfall, not original deferred operations | Preserve as capacity debt unless feature semantics require a separate durable queue |
| Long-run measurement calls `len()` on integer debt values | Verified defect correction | `src/perf/long_run_harness.py::run` debt candidate calculation | Debt-bearing performance runs can fail or omit evidence | Repair before accepting debt-pressure results |
| Performance policy, certification contract, and live CI gate disagree | Contract ambiguity | `docs/performance/perf_baseline_policy.md`; `docs/engine/contracts/certification_contract.md`; `tests/perf/test_perf_regression_baseline.py` | Hardware classes, sample sizes, percentiles, memory, missing baselines, and mode gates lack one authority | Reconcile one machine-exercised contract |
| Live CI uses 10 warmup/50 sample ticks, average latency, skippable missing baselines, and no hard NORMAL scenarios | Measurement gap | `tests/perf/test_perf_regression_baseline.py` | Current gate cannot support the stronger percentile/memory/mode claims | Separate CI-fast smoke gates from scheduled evidence runs |
| Concurrency parity tests exist despite an authority-P1 document limiting the guarantee to sequential mode | Contract ambiguity | `tests/perf/test_concurrency_parity.py`; `tests/integration/kernel/test_determinism_suite.py`; `docs/engine/deterministic_execution.md` | Tested same-environment executor parity is stronger than the written contract, but cross-platform scope is unknown | Approve explicit portability tiers and update the contract |
| Apply constructs a new `AuthoritativeState`, then Kernel replaces its state reference | Verified behavior | `src/engine/apply.py::ApplyPath.apply_generation`; `src/engine/kernel.py::_phase_advancement` | Provides a single-owner generation replacement after successful construction, not proven crash-atomic persistence or general transactional isolation | Use precise wording; require stronger staging only for initiatives that need it |
| Replay records tick events and bounded chunks, but no complete replayable semantic control schema was found | Contract ambiguity | `src/engine/kernel.py::_phase_persistence`; `src/engine/replay_manager.py`; `src/core/diagnostic.py::TraceEvent` | Live wall-clock decisions cannot yet be reproduced solely from the replay trace | Define a bounded versioned control trace before relying on live-bounded reproducibility |

## 2. Research pedigree

The recommendations are adaptations of recognized designs, not a proposal to invent an entirely
new engine architecture.

| Proposal element | Established design | Application here |
|---|---|---|
| Parallel Collection, barrier, ordered Resolution | Bulk-Synchronous Parallel (BSP), fork/join, single-writer commit | Preserve the existing execution model and optimize within it |
| Dirty/affected processing | Incremental computation, dependency graphs, change-version filtering | Schedule and resolve only domains affected by canonical changes |
| Cadence buckets | Hashed/hierarchical timing wheels and calendar queues | Place deterministic tick/entity work into due buckets instead of repeatedly scanning everything |
| Deterministic result caching | Memoization and self-adjusting computation | Cache pure pathfinding, utility, perception, and static-rule calculations using complete semantic keys |
| Narrow hot-path arrays | Data-Oriented Design and structure-of-arrays processing | Derive disposable Collection projections without replacing the OO authoritative model |
| Dynamic balancing | Work stealing and locality-aware task scheduling | Balance uneven Collection work while preserving post-Collection canonical sort |
| Phase dependency metadata | Job/task graphs with declared read/write sets | Validate the 43-phase order before considering any concurrent phase execution |
| Hierarchical state hashes | Merkle/hash trees and incremental recomputation | Rehash dirty entity/region branches and retain periodic full verification |
| Serial-fraction measurement | Amdahl's law | Quantify the ceiling imposed by sorting, Resolution, hashing, and other serial work |
| Spatial subscriptions | Interest management | Reduce projection, serialization, and client traffic without changing simulation semantics |

The exact ladder in this document is a project-specific synthesis. It is not a single named
industry pattern.

## 3. Performance scaling without structural decay

Performance is the goal of this proposal. Structure is a constraint and an enabler: it should
make performance improvements composable as the RPG grows, without turning optimization into a
large framework rewrite.

### 3.1 Four different scaling pressures

| Scaling pressure | What grows | Main cost | Primary response |
|---|---|---|---|
| Feature scale | RPG rules and refinement phases | More scans, gates, merges, ordering dependencies, and permanent tick overhead | Phase admission rules, complete metadata, compact input routing |
| World scale | Entities, relationships, places, items, events | Candidate selection, Collection work, state traversal, proposal volume | Dirty sets, cadence, LOD, indexes, memoization |
| Hardware scale | Available cores and process/thread choices | Load imbalance, IPC, barriers, serial fraction | Measured chunking, locality-aware work distribution, selective parallelism |
| Serving scale | Clients and observed regions | Projection, serialization, bandwidth, queue memory | Interest management and bounded delta delivery |

These pressures should not be conflated. More workers do not fix a growing serial refinement
chain. Interest management does not reduce authoritative simulation work. Stronger LOD may shorten
a tick without making any system implementation faster.

### 3.2 Stable architecture — what does not change

Exact-performance work in this proposal preserves:

- the seven macro kernel phases;
- single-process, single-authority ownership;
- immutable Collection snapshots and the Collection/Resolution barrier;
- `StateUpdate` as the representation of proposed authoritative change;
- canonical proposal ordering independent of worker completion order;
- the Singular Bottleneck Law and initially serial authoritative refinement;
- the OO authoritative model;
- passive-client semantics.

Caches, indexes, phase-input views, SoA projections, worker partitions, and incremental hashes are
derived structures. They must be rebuildable from authoritative state and may not become a second
mutable truth.

### 3.3 What may change for performance

Within that stable spine, the following structures may evolve:

- candidate discovery can move from repeated scans to dirty/due indexes;
- cadence work can move to deterministic due-tick buckets when scanning is measured as expensive;
- accumulated proposals/updates can gain typed indices so a phase sees only relevant input;
- pure expensive functions can use complete, versioned deterministic cache keys;
- Collection packets can use measured locality-aware/dynamic distribution;
- hot loops can consume disposable generation-scoped data-oriented projections;
- hashing can become hierarchical while retaining periodic full verification;
- the handwritten refinement chain can be described by a complete static phase catalog and a
  startup-validated execution plan, without changing its order.

Each change remains subject to an end-to-end benchmark and determinism/parity gate. Structural
work with no demonstrated path to lower cost or safer future optimization is outside this proposal.

### 3.4 Why growing phases matter

The current 43-phase count is not itself a performance defect. A function call plus an O(1) skip
gate is cheap. Phase growth becomes a performance problem when a new RPG feature adds:

- an unconditional every-tick phase;
- a full scan of entities, relationships, world objects, or the accumulated update;
- repeated construction of a candidate subset another phase already computed;
- a broad `all` dependency that prevents dirty skipping;
- hidden same-tick coupling that prevents safe reordering or batching;
- permanent dispatch/import/feature-flag overhead inside the central method;
- manual inventories that drift, making measurements incomplete.

The relevant model is:

```text
T_resolution =
    T_dispatch(active and skipped phases)
  + Σ T_phase_i(relevant_input_i)
  + T_cross_phase_merge
  + T_apply_generation
```

The target is not the fewest phases. It is skipped phases near O(1), active phases proportional to
their relevant input rather than world size, and explicit dependencies instead of accidental
call-position coupling.

### 3.5 Admission rule for new RPG features

Adding a feature must not automatically add another global phase:

```text
Same invariant, domain, and ordering boundary as an existing phase?
  → add a typed handler to that phase

Existing phase can consume the new typed event/intent?
  → add compact routing to that handler

Work is only needed on a dirty event or deterministic cadence?
  → add an explicit gate and freshness guarantee

Correctness requires a distinct before/after boundary?
  → add a new declared phase
```

A new phase is justified when it establishes an invariant downstream phases must observe,
requires an independent OFF/SHADOW rollout boundary, or occupies a genuinely distinct semantic
ordering point. A different feature name or module is not sufficient justification.

Every new phase should declare accepted input kinds, read/write/emit domains, predecessors,
required and established invariants, gate/must-run reason, same-tick versus next-tick visibility,
and cost/cardinality metrics.

### 3.6 Minimal structural evolution of the existing phase mechanism

The engine already has the right starting pieces:

- `run_phase()` applies rollout modes and run/skip metrics;
- `PhaseDependencyGraph.should_run_phase()` supports dirty/cadence skipping;
- `pipeline_phases/` defines extracted handlers with a no-direct-mutation rule;
- macro-phase domain permissions protect the seven kernel phases;
- a scoped subphase-domain-contract epic already exists.

The gap is completeness and single-source ownership. `PhaseDependencyGraph` is currently a partial
skip-policy table, not an execution dependency graph: it declares no ordering edges, performs no
topological validation, still describes 17 phases, and covers only a subset of the current 43.
Unregistered phases default to running. The existing subphase-contract epic still describes a
37-phase pipeline.

Evolve the existing `PhaseMetadata` concept rather than create a parallel framework:

1. Inventory the actual phase-like operations and reconcile the 43-call order.
2. Complete metadata for every phase without changing execution behavior.
3. Generate phase count/order documentation and parity tests from that catalog.
4. Compile one immutable execution plan at startup and prove it matches the handwritten order.
5. Add compact typed/domain input routing and precomputed rollout gates.
6. Retain serial execution until measurements prove the serial fraction warrants more complexity.

Only steps 4-5 are expected to improve runtime directly. Steps 1-3 are the minimum safety layer
that lets those optimizations remain correct as features continue to arrive.

### 3.7 Phase-growth performance gates

A new phase is acceptable only when:

1. Its distinct ordering boundary is documented.
2. Reusing an existing phase/handler was considered.
3. Its input cardinality and cost are observable.
4. It has a dirty, event, cadence, or explicit must-run policy.
5. It does not introduce an unmeasured full-world or full-update scan.
6. Its disabled and SHADOW behavior are tested where applicable.
7. Canonical-order and output parity checks remain green.

This keeps a well-designed structure in service of performance rather than making structural
abstraction an end in itself.

## 4. Governing optimization laws

### Law 1: measurements must describe work, not only time

Phase latency without workload cardinality is ambiguous. A faster tick may mean improved code, or
it may mean that degradation silently processed fewer entities.

### Law 2: remove work before accelerating it

Dirty filtering, readiness, cadence, LOD, dependency routing, and coalescing generally have higher
leverage than faster execution of work that did not need to run.

### Law 3: reuse before rearranging data

Deterministic memoization can remove entire computations. Data-oriented layout only accelerates
the computations that remain.

### Law 4: derived performance structures never become authority

Indexes, caches, SoA projections, worker partitions, incremental hashes, and client projections
must be rebuildable from authoritative state. Rebuildability is necessary but insufficient:
their presence, absence, hit rate, eviction order, rebuild timing, corruption, or instrumentation
overhead must not alter canonical work admission or results. A correctness-preserving fallback
must exist. If the fallback's extra time can cause a semantic governor transition, that transition
is either disabled in canonical mode or recorded as a live-mode control input.

### Law 5: operational order must not become semantic order

Worker assignment, completion order, queue contention, and cache hit order may affect latency but
must not affect canonical apply order or outcome.

### Law 6: approximation requires an explicit semantic contract

Hierarchical or lower-fidelity simulation is not a normal micro-optimization. It changes what is
computed and needs equivalence bounds, freshness guarantees, transition rules, and differential
tests.

### 4.1 Determinism envelope — prerequisite decision

The repository currently mixes deterministic state evolution with wall-clock and resource-pressure
decisions. This proposal recommends two explicit execution contracts:

| Contract | Permitted control inputs | Reproduction requirement | Intended use |
|---|---|---|---|
| Canonical/certification | State, seed/RNG checkpoint, rules/content/config versions, ordered external inputs, deterministic work-unit budgets | Reproduce without machine-timing input | parity, replay certification, optimization validation |
| Live bounded | The canonical inputs plus wall-clock pressure, timeouts, cancellations, and machine/resource signals | Persist a versioned control trace sufficient to replay every semantics-affecting decision | production deadline protection |

Canonical mode must not make semantic choices from unrecorded elapsed time, cache behavior,
instrumentation overhead, worker completion timing, or client presence. Live bounded mode may use
those signals only if every mode transition, mid-tick cutoff, dropped/coalesced operation, debt
insertion, timeout, and cancellation affecting state evolution is recorded with its effective tick
and canonical ordering position.

This decision blocks optimizations that change admission, cadence, or fidelity. It does **not**
block observational instrumentation, phase inventory reconciliation, or correction of telemetry
whose current value is demonstrably invalid.

Portability is a separate axis. Do not infer universal bitwise parity from same-machine tests:

| Tier | Scope |
|---|---|
| DET-PORT-0 | same build, dependencies, configuration, and machine profile |
| DET-PORT-1 | same approved Python/runtime and platform profile |
| DET-PORT-2 | approved runtime and hardware matrix |
| DET-PORT-3 | every supported deployment class |

The approving architecture owner must select the required tier and its controls for floating-point
behavior, canonical serialization, dependency versions, interpreter build, and platform libraries.
Only the approved tiers are certification promises.

### 4.2 Live bounded control-trace contract

Live bounded reproduction records the minimum semantics-affecting decisions, not an unlimited copy
of operational telemetry. Each versioned control event contains, where applicable:

```text
trace scheme/version
+ effective tick and ordering boundary
+ RuntimeMode and policy version
+ classified pressure result (raw inputs optional by retention policy)
+ admission/candidate budgets and cadence selection
+ timeout/cancellation/cutoff decision
+ dropped/coalesced work classification
+ capacity-debt delta
+ semantic-deferred-work reference, if that feature exists
+ stable reason code
```

Consecutive ticks with identical decisions may use deterministic range/epoch compression, provided
every effective boundary is recoverable. The approved contract must define maximum bytes per tick
and per checkpoint interval, retention and rotation, checkpoint linkage, schema migration, replay
behavior, and corruption behavior. Missing or corrupt required control events make live replay
unverifiable; they must not silently fall back to a claim of canonical reproduction.

### 4.3 Derived-structure lifecycle contract

Use the smallest lifecycle that preserves correctness:

| Structure | Authoritative? | Normal persistence | Required safeguards |
|---|---:|---|---|
| Dirty/domain index | No | Reconstruct or carry forward under a generation stamp | exhaustive invalidation audit, full-scan fallback |
| Due-work accelerator | No | Reconstruct from canonical eligibility function or authoritative due records | deterministic rebuild, version stamp, scan fallback, no missed/duplicate due item |
| Memoization cache | No | Do not checkpoint by default | complete versioned key, bounded eviction, bypass equivalence |
| SoA Collection view | No | Never checkpoint | immutable generation stamp, discard after generation |
| Worker partition/steal queues | No | Never checkpoint | canonical RNG/ID addressing and result ordering |
| Incremental hash tree | No | Optional diagnostic checkpoint only | versioned hash scheme, full tree rebuild comparison, independent flat audit |
| Client projection | No | Recreate/resnapshot | client-presence independence, sequence/gap detection |

Atomic publication is required when a reader could otherwise observe a partially rebuilt index or
view. Serialization of a derived structure is an optional startup optimization, not proof of
correctness: it must be version-checked and safely discarded.

## 5. Required Architecture Approval Decisions

These recommendations await the named authority. “Recommended” is not “approved.” Decisions are
placed before the execution plan so no dependent package can be mistaken for pre-approved work.

| ID | Recommended default | Alternatives considered | Consequences | Approver placeholder | Approval deadline | Blocks |
|---|---|---|---|---|---|---|
| D1 Determinism contracts | Adopt separate Canonical/certification and Live bounded contracts; require a replayable control trace for the latter | Canonical-only operation; one mixed contract; untraced live degradation | Makes wall-clock semantic influence explicit and testable; adds bounded trace work for live mode | [Architecture owner] + [Simulation correctness owner] | Before admission/cadence/fidelity or pressure-sensitive optimization | Stages 1 pressure-baseline promotion and 5-6 semantic-sensitive work |
| D2 Portability scope | Guarantee DET-PORT-1 (same approved runtime/platform) first; retain same-environment local/thread/process parity; expand to DET-PORT-2 or DET-PORT-3 only after a passing matrix | DET-PORT-0 only; immediate universal cross-platform promise | Avoids an untested bitwise portability promise while preserving meaningful reproducibility | [Architecture owner] + [Release/certification owner] | Before publishing certification portability claims | Cross-hardware gates and baseline portability |
| D3 Work-debt meaning | Keep current aggregate capacity debt; introduce a separate authoritative semantic-deferred-work model only for a concrete feature contract | Reinterpret the counter as an operation queue; build both immediately | Preserves the simple current model and prevents false recovery claims | [Simulation semantics owner] | Before changing debt scheduling or persistence | Deferred-work features and debt-pressure acceptance |
| D4 Performance contract authority | Create one authoritative reconciled performance contract and make the selected live CI/scheduled gates executable projections of it | Treat `PerfRegressionGate` alone as authority; treat current CI test alone as authority; preserve conflicting documents | Requires migration/versioning but eliminates contradictory targets and silent skips | [Performance owner] + [Release owner] | Before Stage 4 baselines are promoted | Baseline promotion and optimization performance claims |
| D5 Hash policy | Keep versioned flat SHA-256 as the canonical certification scheme at explicit boundaries; require freshness metadata; make per-tick replay hashing an explicit product choice; hierarchical hashing remains evidence-gated | Mandatory flat hash every tick; budgeted stale hashes; replace flat hash with tree root | Separates proof identity from diagnostics and prevents stale proof claims | [Simulation correctness owner] + [Observability/replay owner] | Before hash-schedule correction and baseline regeneration | Hash workstream and replay proof claims |
| D6 Phase catalog authority | Make one static catalog own phase identity/order/contracts/instrumentation and generate docs; compile/validate it against the handwritten path before it may drive execution | Keep handwritten order plus manual docs; use `PhaseDependencyGraph` only; introduce a second registry | Adds bounded metadata work but prevents continued 37/39/43 drift and supports feature growth | [Engine architecture owner] | Before catalog-derived execution or compact routing; inventory may start now | Stage 3 exit and routing workstream |

Feature admission continues to follow section 3.5. Phase-family ownership and budgets are selected
during D6/Stage 3 only if they improve accountability or measurement; they are not a prerequisite
abstraction.

## 6. Measurement foundation and benchmark contract

### 6.1 Correct telemetry before drawing conclusions

Correct the zero-worker and zero-queue-capacity utilization semantics and establish whether
previous benchmark or live runs entered false DEGRADED mode. A local/synchronous executor has no
worker-pool saturation; it must not report full pool utilization by construction. Capacity that
does not exist should be represented as unavailable/not-applicable separately from the utilization
of configured capacity, rather than overloaded onto either 0.0 or 1.0 without context.

Runtime mode affects candidate budgets and subsystem cadence. Consequently, a performance claim
must include its mode sequence, and a canonical benchmark should fail validation if it leaves its
declared mode unexpectedly.

### 6.2 Record the scheduling funnel

For each tick and major work domain, capture:

```text
total population
→ affected/dirty
→ ready
→ cadence-due
→ LOD-eligible
→ admitted by candidate budget
→ submitted to Collection
→ proposals produced
→ proposals accepted/rejected
→ results applied
→ dropped
→ coalesced
→ capacity debt
→ semantic deferred work, if supported
```

Aggregate counts should be available by domain, LOD tier, cadence bucket, runtime mode, and
rejection reason. All dimensions must be bounded.

### 6.3 Measure the complete tick cost

At minimum:

```text
T_tick =
    T_snapshot
  + T_schedule
  + T_collection_critical_path
  + T_collection_imbalance
  + T_barrier
  + T_worker_result_sort
  + T_state_update_construction
  + T_phase_input_routing
  + T_refinement_phases
  + T_apply_generation
  + T_hashing
  + T_delta_projection
  + T_serialization
  + T_broadcast
```

Record all 43 refinement-phase costs individually in benchmark/certification profiles. Also
record proposal cardinality per phase so cost can be normalized as both milliseconds per tick and
cost per relevant proposal. Keep low-overhead production counters separate from diagnostic
profiling: use monotonic high-resolution timers for the normal funnel, event-based call profiling
with `cProfile` only in isolated offline runs, and allocation tracing in separate runs so
observer overhead is measured rather than hidden. `cProfile` timing is neither repeatable by
definition nor operationally free.

The bounded metric schema includes per-phase input cardinality, run/skip count, rejection reasons,
worker and queue utilization, worker critical-path imbalance, snapshot/IPC bytes and allocations,
cache hits/misses/evictions/bypass mismatches, dirty-index size/rebuild cost, hash cost/scheme/
freshness, projection/delta bytes, per-client queue cost, memory high-water mark, RuntimeMode
sequence, control-trace volume, and instrumentation overhead. Labels use finite registered phase,
domain, reason, mode, backend, and scenario identifiers; never entity IDs or other unbounded values.

### 6.4 Reproducible benchmark protocol

Use `ScenarioCheckpointer` to restore a fixed warm state and benchmark the same tick range
repeatedly. Each result must declare:

- checkpoint/state identity;
- engine, rules, content, Python, and platform versions;
- runtime profile and flags;
- worker backend and worker count;
- warmup and sample ranges;
- runtime-mode sequence;
- replay/hash configuration;
- processed-work cardinalities;
- CPU time, wall time, memory, phase distribution, and variance.

Raw simulation throughput and operational overhead should be separate claims. For example,
`no_replay` is appropriate for a raw compute benchmark, while a second benchmark should quantify
the real cost of canonical hashing and replay.

The first measurement deliverable is reconciliation, not a new profiler framework:

1. Choose whether `tests/perf/test_perf_regression_baseline.py` or `PerfRegressionGate` owns the
   live CI contract.
2. Align the chosen gate with the documented warmup/sample windows, percentile and memory metrics,
   missing-baseline behavior, and RuntimeMode policy.
3. Repair debt-bearing long-run measurement before using it as evidence.
4. Record instrumentation overhead by running the same checkpoint with metrics at normal,
   detailed, and audit levels.

### 6.5 Objectives and measurable success

| Objective | Success evidence |
|---|---|
| Trustworthy reproducible measurement | Versioned identity tuple, declared mode sequence, repeated distribution, and bounded observer overhead |
| No accidental semantic degradation | Invalid telemetry cannot alter mode; canonical runs process the declared workload |
| Maximum useful workload within budget | Approved scenario meets its tick-latency and memory contract without hidden workload reduction |
| Bounded tail latency and memory | p95/p99/max and memory high-water/delta pass the authoritative gate |
| Deterministic executor behavior | Same-scheme canonical parity across the D2-approved executor/runtime matrix |
| Observable scheduling and Resolution cost | Complete funnel and tick decomposition reconcile with total tick cost |
| Safe derived acceleration | Rebuild/bypass/full-scan comparisons preserve eligible sets and authoritative outcomes |
| Sustainable RPG feature growth | Every new phase has identity, contracts, gate, cardinality, cost, and order parity |

### 6.6 Workload and hardware contract

The repository already proposes CLASS_A/B/C targets, but those targets are not yet a trustworthy
acceptance matrix because hardware classification conflicts with certification documentation and
the live CI scenarios are much smaller than several stated capacities. Reconcile rather than
discard them.

Each accepted performance claim must bind this tuple:

```text
scenario/content identity
+ total and active/eligible population
+ hotspot density and dominant subsystem
+ tick rate/deadline
+ p50/p95/p99/max tick latency
+ target hardware and Python/runtime version
+ local/thread/process backend and worker count
+ memory ceiling
+ client count and bandwidth, when serving is measured
+ replay/hash/observability configuration
+ expected RuntimeMode sequence
```

Maintain this scenario matrix. Braced fields are approval placeholders, not fabricated values:

| Workload | Initial-state source | Primary evidence | Protocol and expected mode | Lane |
|---|---|---|---|---|
| Certification-small | Versioned authored fixture/checkpoint | state/hash and local/thread/process parity | `{D4 CI-fast window}`, full audit, D2 matrix, declared canonical mode | CI-fast |
| Gameplay-medium | Versioned real corpus checkpoint | representative mixed-system latency/memory | `{D4 scheduled window/repetitions}`, production replay/observability, expected NORMAL | scheduled |
| World-large-sparse | Versioned builder/checkpoint with declared active ratio | population and scan scaling slope | `{D4 window/repetitions}`, expected mode declared | scheduled/nightly |
| World-large-dense | Same content/rules family with high active ratio | proposal volume, merge and Resolution slope | `{D4 window/repetitions}`, expected mode declared | nightly |
| Dense-hotspot | Versioned combat/pathfinding/market hotspot | locality, conflict, and tail latency | `{D4 window/repetitions}`, expected mode declared | scheduled/nightly |
| Serving-high-client | Committed state plus versioned client-interest workload | projection, serialization, queues, gaps/resnapshot | `{D4 serving window}`, client presence must not affect authority | scheduled/manual |
| Debt-pressure | Versioned overload checkpoint or deterministic setup | governor transition, capacity debt, fairness/recovery | D1 live-bounded trace; expected mode sequence declared | scheduled |
| Hash-intensive | Same logical state at approved size tiers | flat/tree hash cost, freshness, rebuild validation | D5 schemes/schedule; replay/audit configuration declared | scheduled/manual |
| Snapshot-IPC-intensive | Same checkpoint through local/thread/process backends | frozen-view construction, bytes, serialization, merge | D2 matrix and `{D4 repetitions}`; expected mode declared | scheduled/nightly |

Each concrete scenario specification supplies checkpoint usage, warmup/sample ranges, repetition
count, invariants, observability level, and the claims it is allowed to support. CI-fast results
are regression smoke evidence; they do not substitute for scheduled capacity evidence.

Product owners must choose the final values; architecture must not invent them. Until the existing
targets and live gates agree, benchmark results are diagnostic evidence, not release-capacity
claims.

## 7. Exact candidate A — eliminate unnecessary work

### 7.1 Strengthen existing gates

Dirty sets, readiness, cadence, deterministic LOD, and candidate budgets already exist. The next
step is to measure and tighten their composition:

- Report each gate's exclusion count.
- Avoid re-scanning the full population to rediscover already-known due work.
- Enforce maximum staleness for important domains.
- Ensure critical work cannot be excluded by an accidental conjunction of gates.
- Make dropped, skipped, coalesced, and debt-accounted work distinct metrics.

### 7.2 Consider deterministic due-work buckets

If profiling proves that cadence scheduling performs material full-population scans, maintain
bounded buckets keyed by due tick. Entity identity can deterministically stagger entries.

This is analogous to a timing wheel, but it should only be adopted if:

1. scheduling scans are a measured bottleneck;
2. rescheduling cost is lower than current selection cost;
3. due eligibility is canonical, either as a persisted record changed through `StateUpdate` or
   as a deterministic function of authoritative inputs such as tick, entity/system ID, cadence,
   and rules/content version;
4. the bucket is a derived accelerator that can be rebuilt deterministically;
5. missing or corrupt buckets fall back to an equivalent scan rather than omit work;
6. checkpoint restore reproduces the same due schedule and detects duplicate/missed entries.

### 7.3 Route compact phase inputs

The current global sort is specifically a sort of Collection `WorkerResult` objects by class
priority, descending local priority, and entity ID before one `StateUpdate` is constructed. It is
not evidence that the refinement pipeline performs one cross-phase sort of every intent type.
Preserve that worker-result ordering unless a separate equivalence proof justifies changing it.

The refinement pipeline is structurally batched into named phases, but that alone does not prove
efficient input routing. Build deterministic indices or typed views so each refinement phase sees
only the intent/update categories it can consume.

Adopt this only after measuring whether phases repeatedly traverse a large shared `StateUpdate` or
candidate collection. The intended effect is to reduce an accidental `O(phases × proposals)`
shape toward `O(proposals + relevant phase work)`.

A more aggressive candidate is a single traversal that buckets update entries by consuming phase,
followed by a stable canonical sort inside each bucket and fixed phase execution. It is valid only
if cross-bucket ordering has no meaning beyond the already-fixed phase order. Before adoption:

- measure current sort cost and repeated full-update scans separately;
- prove duplicate/conflict detection and same-tick emitted-work visibility are unchanged;
- compare the bucketed result with the current full pipeline across randomized insertion orders;
- retain a canonical full-path oracle in tests.

Treat this as a conditional optimization, not a correction implied by the current code.

### 7.4 Separate capacity debt from deferred semantic work

The current `Dict[subsystem_id, int]` is sufficient only when debt means “this subsystem received
less capacity” and repayment may legitimately execute generic subsystem work. Keep that concept
named **capacity debt**.

Do not claim that it preserves a postponed operation. If a future feature requires a specific
operation to survive deferral, model **semantic deferred work** explicitly with stable/idempotency
identity, entity and subsystem, origin tick, state/rule generation, preconditions, revalidation,
expiry, coalescing, cancellation outcome, priority aging, and maximum repayment budget. Such a
queue is authoritative state and must pass through `StateUpdate`; it should be introduced only
when required semantics cannot be expressed by capacity debt.

## 8. Exact candidate B — reuse deterministic computation

Prioritize pure, expensive, repeatedly invoked functions:

- pathfinding and reachability;
- utility/goal scoring;
- perception and proximity queries;
- terrain traversal calculations;
- region adjacency and static world relationships;
- content/rule-derived lookup tables.

A cache key must include every input that can alter the result, including a rules/content version
and the relevant state/index generation. Never key by object identity when identity can survive a
semantic change.

Certification mode should occasionally bypass the cache and compare recomputed results. This
turns a potentially silent invalidation defect into a detectable determinism violation.

Adoption gate: a target function must have measured cost, a stable complete input signature, and
a demonstrated reuse rate. Otherwise the cache adds memory and invalidation complexity without
benefit.

## 9. Exact candidate C — hashing and divergence diagnostics

### 9.1 Hash behavior audit and policy reconciliation

PA-03A first measures `CanonicalStateHasher`, inventories every operational call site, and records
freshness plus replay/certification dependencies without changing implementation. Only after D5
may PA-03B reconcile the approved schedule with the kernel path. A stale cached hash must never be
presented as the current tick's exact canonical proof. A skipped or stale result needs an explicit
scheme, freshness, and state-tick label.

### 9.2 Hierarchical design

If full-hash cost is material, use a hierarchy such as:

```text
field/component hash
        ↓
entity/object hash
        ↓
region/domain hash
        ↓
world root hash
```

Only dirty branches are recomputed. The hierarchy should improve divergence reports by locating
the first differing phase, region, entity, component, and originating update.

Periodic full canonical hashing remains an independent auditor. Incremental hashing and dirty
tracking must not be allowed to validate only each other.

The flat canonical digest and hierarchical root are different algorithms over different byte
compositions and are not expected to have the same digest value. Name and version them separately,
for example:

```text
flat-sha256-canonical-json/v1
tree-sha256-domain-entity/v1
```

Validation has two independent legs:

1. Rebuild the entire hierarchical tree from authoritative state and require its root to equal the
   incrementally maintained root for the same tree scheme.
2. Periodically recompute the legacy flat canonical hash as an independent semantic auditor. Its
   oracle is explicitly one of: another full flat recomputation from the same authoritative state,
   a same-scheme digest from an independent parity run, or a versioned golden checkpoint digest.

Every reported hash carries `scheme_id`, `state_tick`, `computed_at_tick`, and freshness
(`CURRENT`, `STALE`, or `SKIPPED`). A stale cached value must never satisfy a current-tick
proof request.

## 10. Exact candidate D — reduce data movement and improve layout

### 10.1 Snapshot and process-boundary costs

Before changing the entity model, measure:

- frozen-view construction and cache hit rates;
- per-tick allocations;
- bytes and time spent serializing process-pool packets;
- repeated world/context data transmitted with chunks;
- parent/worker merge costs.

Thread and process backends should be compared using the same checkpoint and workload. Python CPU
work does not automatically benefit from threads, while process parallelism can lose its benefit
to pickle/IPC overhead.

### 10.2 Narrow data-oriented projections

If a measured Collection loop remains large and homogeneous, derive a generation-scoped hot view:

```text
entity_ids[]
positions_x[]
positions_y[]
health[]
readiness[]
goal_ids[]
```

The view is read-only, disposable, and tied to one authoritative generation. It does not replace
`EntityState`, become independently mutable, or justify a full ECS conversion.

Adoption gate: compare end-to-end tick improvement, including projection construction. A faster
inner loop is not a win if building the projection costs more than it saves.

## 11. Exact candidate E — parallel load balancing

### 11.1 Do not assume spatial partitioning is automatically superior

Region-local batches can improve locality and reduce repeated spatial context, but dense cities or
battles can concentrate most work into one region and leave other workers idle.

Compare at least:

1. current flat/micro-chunk scheduling;
2. region-local static partitioning;
3. region-local tasks with oversized hot regions split into deterministic subpartitions;
4. dynamic work distribution with canonical post-Collection ordering.

Measure worker imbalance, IPC bytes, cache/index reuse, steal count, and end-to-end tick latency.

### 11.2 Work stealing is operational, never semantic

Work stealing is an established scheduler for uneven parallel work. It is safe here only because
Collection reads immutable state and Resolution sorts completed results canonically. Result order,
RNG addressing, IDs, and debt semantics must not depend on which worker executed a task.

### 11.3 Keep Resolution serial initially

Create an executable registry for all refinement phases containing:

- stable phase identifier and compatibility version;
- accepted intent/update types;
- state domains read and written;
- required and established invariants;
- explicit predecessors;
- feature flag and cadence;
- whether emitted work is visible this tick or next tick;
- instrumentation key.

Use the registry first for documentation generation, CI validation, compact input routing, and
dependency audits. Consider concurrent phase execution only when profiling proves a meaningful
serial ceiling and tests prove the selected phases disjoint.

## 12. Serving candidate — projection performance

Interest management is a standard and appropriate optimization for network/client scale:

```text
committed authoritative world
        ↓
projection and visibility layer
        ↓
per-client spatial/topic interest
        ↓
bounded delta stream
```

Client subscriptions may change what is serialized and transmitted, but never what the simulation
computes or commits. Measure delta construction, serialization bytes, per-client queue cost,
dropped/coalesced messages, and resnapshot frequency.

This work improves serving capacity, not necessarily simulation TPS, and should be prioritized
only against a real client-count or bandwidth requirement.

## 13. Advanced semantic candidates — last

Hierarchical regional simulation, aggregate populations, and approximate decision evaluation have
the highest theoretical ceiling and the greatest semantic risk.

Do not adopt them until conventional optimization fails a documented population/TPS target. Any
proposal must define:

- exact and approximate state representations;
- deterministic promotion/demotion triggers;
- conservation and invariant rules;
- maximum staleness and fidelity bounds;
- transitions between aggregate and individual state;
- observer/client independence;
- differential and metamorphic tests;
- checkpoint and replay compatibility.

Distance alone is not a sufficient semantic rule. Active combat, commitments, economic settlement,
or other consequential state may require exact processing regardless of location.

## 14. Architectural dependencies by initiative

Do not turn general architecture work into a blanket prerequisite. Require a dependency only where
the optimization can exercise it:

| Initiative | Required dependency | Why |
|---|---|---|
| Observational measurement | Bounded metrics and measured observer overhead | Instrumentation must not create the pressure it reports |
| Compact phase routing | Complete accepted/emitted type contracts and same-tick visibility rules | Routing must not hide inputs emitted by an earlier phase |
| Due buckets | Canonical due records and equivalent scan fallback | Missing accelerator state must not omit semantic work |
| Memoization/index/SoA | Generation/version contract and exhaustive invalidation | Prevent stale derived data from changing results |
| Dynamic Collection scheduling | Deterministic RNG/ID addressing, failure/timeout semantics, canonical result order | Worker ownership and completion timing remain operational |
| Incremental hashing | Stable canonical serialization plus versioned tree scheme | Prevent diagnostic identity from becoming ambiguous |
| Resolution concurrency | Explicit read/write sets, transactional mutation staging, conflict detection, atomic tick commit | Disjointness and all-or-nothing authority must be mechanically proved |
| Client interest management | Ordered delta sequence, gap detection, resnapshot | Serving loss must not feed back into simulation |
| Semantic approximation | Versioned fidelity contract, conservation rules, transition/replay compatibility | It intentionally changes computed semantics |

Crash recovery and broader protocol/versioning work should be cross-referenced when an initiative
depends on it, not absorbed into this performance proposal.

The current apply path constructs a replacement `AuthoritativeState` and assigns it to the
single-owner Kernel only after construction returns. This proposal calls that a **single-owner
generation reference replacement**. It does not claim crash-atomic durable commit, multi-reader
transactional isolation, external-side-effect rollback, or a general mutation transaction.
Stronger staging/commit machinery is a future dependency only for work such as concurrent
Resolution or crash-safe publication that actually requires it.

## 15. Revised priority and evidence matrix

This is a decision order, not a promise to implement every row:

Priorities 3 and 4 may proceed together: the inventory stabilizes phase identity while
instrumentation supplies the cost evidence. Completing dependency metadata is not a reason to
delay safe macro/sort/hash measurements that already have stable boundaries.

| Priority | Initiative | Classification | Expected value | Complexity | Determinism risk | Completion/adoption evidence |
|---:|---|---|---|---|---|---|
| 0 | Decide canonical versus live-bounded determinism contract | Required architecture decision | Removes ambiguity from every later result | Medium | Critical if omitted | Accepted contract and replay/control-trace tests |
| 1 | Apply approved zero-capacity semantics and correct the verified debt-harness defect | Verified defect correction | Restores trustworthy modes and measurements | Low | Low; outcomes may correctly differ from buggy baseline | Approved capacity contract; specification-based tests pass |
| 2 | Reconcile hardware classes, workload targets, CI gate, and baseline protocol | Required measurement | Makes claims comparable and actionable | Medium | Low | One authoritative contract exercised by live CI |
| 3 | Complete phase catalog and prove current-order parity | Architectural enablement | Prevents structural drift as RPG features grow | Medium | Low while behavior is unchanged | Every live phase declared; generated plan equals current order |
| 4 | Add scheduling funnel, 43-phase cardinality/timing, sort/merge, hash, snapshot and IPC metrics | Required measurement | Identifies actual end-to-end contributors | Medium | Low if overhead is bounded | Observer overhead measured; representative profiles captured |
| 5 | Tighten existing dirty/cadence/index gates | Low-risk optimization | Potentially very high | Low-medium | Low | Measured scan removal and exact state parity |
| 6 | Compact typed phase inputs; research per-phase bucketing | Conditional exact optimization | High if repeated full-update scans are material | Medium | Low-medium | Scan/sort attribution plus insertion-order and full-path parity |
| 7 | Memoize measured pure functions | Conditional exact optimization | High only with reuse | Medium | Medium invalidation risk | Hit rate, memory bound, complete keys, bypass equivalence |
| 8 | Audit hash behavior, dependencies, freshness, and cost | Required measurement | Establishes evidence for D5 without changing runtime behavior | Low | None | Complete call-site inventory and measured per-tick contribution |
| 9 | Reconcile approved hash policy | Architectural enablement | Makes scheme, schedule, and freshness authoritative after D5 | Low-medium | Low | Explicit schedule, metadata, and freshness tests |
| 10 | Hierarchical hashing | Conditional exact optimization | Medium-high if full hashing is material | High | Medium | Tree rebuild parity plus independent flat-hash audit |
| 11 | Snapshot/IPC and Collection load balancing | Conditional exact optimization | High for process/uneven workloads | Medium-high | Low-medium | Better end-to-end p95/p99 with executor parity |
| 12 | Narrow SoA Collection projections | Conditional exact optimization | High only for homogeneous hot loops | High | Medium invalidation risk | Construction cost included in positive end-to-end result |
| 13 | Interest management | Conditional serving optimization | High with many clients | Medium | None if boundary holds | Client/bandwidth target and gap/resnapshot tests |
| 14 | Resolution concurrency prerequisites | Architectural enablement | Potentially high | Very high | High | Serial bottleneck, complete contracts, and stronger commit proof in a separate proposal |
| 15 | Hierarchical/approximate simulation | Semantic change | Potentially enormous | Very high | Very high | Exact methods insufficient; versioned fidelity contract accepted |

### 15.1 Evidence-gated execution stages

| Stage | Authorized scope | Deliverables | Exit gate |
|---:|---|---|---|
| 0 Architecture decisions | Repository inspection and D1-D6 decision records | Approved/rejected decisions, rationale, owners, affected contracts | Every decision blocking the next selected stage has an explicit disposition |
| 1 Baseline corrections | Approved telemetry correction, verified harness correction, and hash-policy audit | Specification oracles, tests, affected-baseline inventory, documentation updates | Approved zero-capacity semantics cannot create false pressure; debt runs measure successfully; hash evidence is ready for D5 |
| 2 Performance contract | Reconcile policy, certification, CI-fast, and scheduled evidence | One authoritative contract, baseline identity/version, hardware/RuntimeMode rules | Selected live gates exercise the authoritative contract; missing evidence cannot silently pass |
| 3 Phase identity and observability | Catalog and instrumentation without order changes | Complete inventory, metadata, generated docs, order-parity and observer-overhead tests | Every live phase is represented; unregistered behavior is explicit; catalog order equals current execution |
| 4 Measurement baseline | Run approved scenarios with complete metrics | Versioned results and bottleneck report with latency contribution, scaling slope, memory, risk, and scenario coverage | **Decision Gate A:** only measured material contributors may enter Stage 5 |
| 5 Conditional exact optimization | Only workstreams selected at Gate A | Per-workstream reference path, benchmarks, parity, memory, rollout and rollback evidence | **Decision Gate B:** rerun complete matrix and determine whether approved targets are met |
| 6 Advanced/semantic design | Separate architecture proposals only | Resolution-concurrency proof or versioned fidelity contract | Independent architecture approval; never automatic continuation from Stage 5 |

Conditional-workstream mapping: 5A scan/due/index work is in sections 7.1-7.2; 5B compact routing
in 7.3; 5C memoization in section 8; 5D hashing in section 9; 5E snapshot/IPC in 10.1; 5F Collection
balancing in section 11; 5G data-oriented projections in 10.2; and 5H serving in section 12.
Resolution concurrency and approximation remain Stage 6 topics in sections 11.3 and 13.

Stages 1-3 may overlap where decisions permit and shared files do not conflict. Catalog inventory
may begin before D6, but catalog authority and catalog-driven execution cannot be finalized before
D6. Stage 4 baseline promotion waits for relevant D1-D6 decisions, PA-01 through PA-06, and
Stages 1-3 because measurements made under invalid telemetry, conflicting contracts, or unstable
phase identity are not durable evidence. Heavy-instrumentation runs measure observer cost; they
are never promoted as clean timing baselines.

### 15.2 Immediate prerequisite work packages

Approval of this document authorizes creation, review, and scheduling of these prerequisite
packages through Decision Gate A under the normal ticket and change-control workflow. It does not
merge or deploy code and does not authorize any Stage 5 accelerator or Stage 6 semantic work.

| ID | Classification | Objective and completion artifact | Dependency | Correctness oracle and exit criterion | May change simulation results? |
|---|---|---|---|---|---|
| PA-00 | Required architecture decision | Record D1-D6 dispositions, owners, versions, blocked work, and authority links; artifact: six decision records | Formal architecture approval | Every decision has one disposition and every dependent package is either released or blocked | No; decisions alone change no runtime behavior |
| PA-01 | Architectural enablement | Define worker-zero and queue-zero semantics separately, correct signals where required, and audit affected baselines; artifacts: capacity contract, tests, audit | D1 and named performance/engine owners | Specification tests map each capacity state to its signal and RuntimeMode; no unavailable/disabled capacity is falsely treated as saturated | Yes, intentionally, if correction removes false DEGRADED behavior; use the approved specification, not broken-behavior parity |
| PA-02 | Verified defect correction | Repair integer debt measurement and add debt-bearing harness coverage; artifact: corrected harness tests and result fixture | D3 terminology | A non-empty integer debt map completes and reports exact counts without changing the checkpoint or admitted workload | No authoritative result change; measurement output changes |
| PA-03A | Required measurement | Inventory flat canonical hash call sites, cost, freshness, replay/certification dependencies, and documentation; artifact: D5 evidence report | Stable Stage 1 harness identity; D5 not required | Every operational hash path and reported digest has known scheme/freshness semantics; per-tick cost is measured; no runtime policy changes | No |
| PA-03B | Architectural enablement | Apply D5's approved schedule and scheme/tick/freshness metadata, reconcile documentation, and version affected baselines; artifact: hash-policy manifest and conformance tests | D5 and PA-03A | No stale digest satisfies a current-state proof; comparisons require the same scheme; flat and tree values are never directly equated | No canonical state change; diagnostic timing/availability may change as approved by D5 |
| PA-04 | Architectural enablement | Establish one authoritative performance contract for class, workload, sampling, percentiles, memory, missing baselines, modes, and identity; artifact: contract plus executable gate mapping | D4 | CI-fast and scheduled gates declare and test the clauses they enforce; missing required evidence cannot pass | No |
| PA-05 | Architectural enablement | Inventory phase-like calls and define a catalog reproducing live order without driving it; artifact: generated inventory and order-parity report | Inventory may start immediately; final authority requires D6 | All live phases/direct calls are reconciled; generated order equals current execution; no catalog-driven execution is enabled | No |
| PA-06 | Required measurement | Define bounded metric schema and quantify normal/detailed/audit observer overhead; artifact: schema and overhead report | D1 plus PA-04/PA-05 stable identities | Same-checkpoint state parity holds; labels and buffers are bounded; heavy runs are excluded from clean baselines | No; must not change workload admission |
| PA-07 | Required measurement | Materialize approved scenarios and run the baseline matrix; artifact: versioned benchmark corpus and results | PA-01 through PA-06 as applicable, including PA-03B when D5 changes baseline identity | Results include identity, environment, RuntimeMode sequence, processed-work cardinality, distributions, variance, memory, and valid trace status | No; scenario workload is fixed and declared |
| PA-08 | Required measurement | Rank end-to-end contributors and nominate only supported Stage 5 workstreams; artifact: Decision Gate A bottleneck report | PA-07 | Each nomination cites material scenario cost and adoption criteria; non-material candidates are rejected or deferred | No |

### 15.3 Standard work-package contract

Every package derived from this plan records:

```text
ID/title and classification
problem statement and repository evidence
objective; in scope; out of scope
dependencies and affected invariants
proposed approach and simpler alternatives
deliverables and bounded metrics
acceptance criteria and correctness oracle
determinism/parity matrix and performance scenario
memory/observability/control-trace impact
risks, OFF/SHADOW/reference path, rollback and retirement rule
documentation/authority updates
decision gate, owner placeholder, status
```

Before Gate A, approved prerequisite tickets may correct verified defects, reconcile authorities,
add bounded observation, materialize scenarios, and produce the bottleneck report. They may not
introduce memoization, timing wheels/due buckets, SoA views, dynamic work stealing, hierarchical
hashing, fidelity changes, Resolution concurrency, or any accelerator merely because it appears in
this proposal. Conditional workstreams must not become implementation-ready tickets before Gate A.

## 16. Reference Architecture and Conditional Acceleration Points

Legend:

- **Stable spine** — required architecture that remains unchanged.
- **`[D#]` decision point** — proposed architecture whose exact contract awaits the named approval.
- **Conditional acceleration point** — may be introduced only after Gate A demonstrates material
  cost and the workstream passes its adoption criteria.

```text
                     AUTHORITATIVE STATE t
                              │
            ┌─────────────────┴─────────────────┐
            │                                   │
      generation/versioned                 spatial/static indexes
        immutable view                      dependency/dirty sets
            │                                   │
            └─────────────────┬─────────────────┘
                              │
                     deterministic scheduler
     canonical due eligibility/records + readiness/LOD
                 [conditional] derived due buckets
                              │
                    measured scheduling funnel
              [conditional] dynamic task assignment
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   worker task           worker task           worker task
 [conditional] cache   [conditional] cache   [conditional] cache
 [conditional] hot     [conditional] hot     [conditional] hot
  Collection view       Collection view       Collection view
        │                     │                     │
        └──────────────── proposals ────────────────┘
                              │
                        global barrier
                              │
                 canonical WorkerResult sort
                              │
              [conditional] typed phase routing
                              │
                  serial authoritative refinement
                proposed catalog-validated plan
               matching the live 43-phase order
                              │
          single-owner generation reference replacement
                              │
                     AUTHORITATIVE STATE t+1
                              │
             ┌────────────────┼────────────────┐
             │                │                │
 [conditional] incremental  [conditional] dirty    [D5] approved flat
   hierarchical hash       projection deltas       hash/audit schedule
                              │
                [conditional] interest management
                              │
                         passive clients
```

## 17. Explicit non-goals

- Increasing taxonomy coverage for its own sake.
- Collapsing phases merely to reduce the phase count; phase granularity follows invariants and
  ordering boundaries, not a target number.
- Replacing the authoritative OO domain model with a full ECS without evidence.
- Allowing caches, indexes, projections, hashes, or worker partitions to become authority.
- Introducing client prediction, rollback, distributed writers, CRDTs, or eventual consistency.
- Parallelizing Resolution merely because Collection already runs concurrently.
- Returning stale hashes as if they prove the state of the current tick.
- Calling aggregate debt counts a recoverable queue of postponed operations.
- Allowing machine pressure or client presence to silently change canonical semantics.
- Claiming an optimization from microbenchmark improvement without an end-to-end tick result.

## 18. Proposed validation suite

Validation depends on the change category:

| Change | Required oracle |
|---|---|
| Semantics-preserving optimization | Identical canonical state and ordered authoritative outcomes |
| Bug fix | Specification/corrected golden result; document intentional difference from broken baseline |
| Intended semantic change | Version bump, explicit expected differences, invariant and migration tests |
| Observability-only change | Identical canonical state; separately measure observer overhead |
| Approximation/fidelity change | Declared differential bounds, conservation/invariant checks, deterministic transitions |

The zero-worker governor correction is a concrete warning against blind old/new parity: reproducing
the old false DEGRADED evolution would preserve a defect. Its oracle is the defined utilization and
mode contract.

For semantics-preserving changes, exercise:

- one, two, four, and maximum Collection workers;
- local, thread, and process execution where supported;
- randomized worker delay and completion order;
- different `PYTHONHASHSEED` values;
- cache enabled versus certification recomputation;
- derived index/view present, absent, rebuilt, and deliberately invalidated;
- full run versus checkpoint/restore continuation;
- normal instrumentation versus audit instrumentation;
- current full-scan/full-path oracle versus optimized implementation on identical checkpoints;
- canonical mode across the runtime/hardware tiers approved by D2;
- live bounded replay using a recorded control trace.

Performance tests should report distributions, not single averages: p50, p95, p99, maximum,
variance, working-set cardinalities, mode sequence, memory delta, CPU time, and wall time.
Correctness and timing samples should be separated when heavy profiling or allocation tracing
would materially perturb the tick.

### 18.1 Risk register

| Risk | Failure mode | Detection | Prevention | Recovery |
|---|---|---|---|---|
| False performance gain | DEGRADED mode processes less work | funnel plus mode/control trace | fixed scenario contract | invalidate/rebuild baseline |
| Invalid capacity telemetry | absent pool/queue appears saturated | zero-capacity governor tests | explicit unavailable versus utilized semantics | disable affected signal and audit runs |
| Cache invalidation defect | stale result changes state | certification bypass comparison | complete versioned keys/generations | disable and rebuild cache |
| Dirty/index omission | eligible work disappears | full-scan differential test | exhaustive dirty mapping and version stamp | equivalent scan fallback |
| Instrumentation observer effect | profiling changes admission/mode | same-checkpoint overhead comparison | separate production, benchmark, call, allocation, and audit tiers | rerun clean benchmark |
| Hash identity/freshness confusion | stale or different-scheme digest is accepted | scheme/tick/freshness assertions | versioned schemes and explicit oracle | force same-scheme recomputation |
| Due-bucket drift | missed or duplicate work | compare with canonical eligibility | deterministic rebuild and bounded version identity | discard bucket and scan |
| Work-stealing semantic leak | owner/completion order changes result | executor/delay parity | context-addressed IDs/RNG and canonical sort | disable dynamic scheduler |
| Control-trace loss/growth | replay is unverifiable or storage exceeds bounds | trace integrity/volume metrics | compact versioned epochs, checkpoint rotation, declared budget | mark replay unverifiable; restore earlier valid checkpoint |
| Phase catalog drift | metadata and execution diverge | generated order/coverage test | one catalog authority | reject CI/startup plan promotion |
| Baseline identity drift | incompatible results are compared | baseline fingerprint | versioned scenario/build/config/environment identity | regenerate, never silently migrate |
| Overstated apply atomicity | design assumes rollback/isolation not provided | fault and publication review | precise current guarantee | block dependent initiative |
| Permanent dual paths | reference and optimized paths both decay | rollout-age/coverage review | explicit retirement decision at promotion | roll back or retire optimized path |

### 18.2 Rollout and rollback rules

Every execution-structure optimization preserves a correctness reference path while evidence is
being gathered. Use OFF, and SHADOW where computation can be compared without authoritative
effects. Promotion requires:

1. the change-category oracle in section 18;
2. a positive end-to-end result on at least one approved target scenario;
3. no unacceptable regression on the remaining applicable matrix;
4. bounded memory and instrumentation/control-trace overhead;
5. an automatic-disable condition and tested fallback;
6. an explicit decision to retire one path after the confidence window.

A microbenchmark or inner-loop speedup alone cannot promote a change. Rollback restores the
reference execution path and invalidates incompatible derived caches and performance baselines; it
must not attempt to preserve a derived structure as authority.

### 18.3 Traceability matrix

| Concern | Architectural rule | Stage/package | Validation | Evidence artifact |
|---|---|---|---|---|
| Determinism envelope/portability | D1-D2; canonical inputs or recorded controls only | Stage 0 / PA-00 | executor/runtime matrix and live trace replay | decision records plus parity report |
| Governor correctness | no invalid capacity pressure | Stage 1 / PA-01 | signal-to-mode specification tests | affected-baseline audit |
| Phase growth/catalog | one identity/order/contracts source | Stage 3 / PA-05 | coverage and order parity | generated phase inventory |
| Workload targets/metrics | one D4 contract; bounded labels | Stage 2-4 / PA-04, PA-06, PA-07 | gate conformance and observer overhead | versioned benchmark artifacts |
| Debt semantics | capacity debt is not deferred operations | Stage 0-1 / D3, PA-02 | debt-bearing measurement/recovery | debt scenario result |
| Derived structures/due work | rebuild/bypass/scan equivalence | Stage 5A-5C when selected | invalidation, rebuild, full-scan parity | differential report |
| Hash schemes | compare same scheme; expose freshness | Stage 1 / PA-03A and PA-03B; Stage 5D only if selected | call-site/cost audit, policy conformance, tree rebuild and flat same-scheme audit | D5 evidence report plus hash manifest |
| Sorting/routing | WorkerResult order remains canonical; routing preserves visibility | Stage 5B when selected | randomized insertion/full-path parity | routing benchmark and proof |
| Snapshot/IPC/load balancing | operational ownership cannot alter semantics | Stage 5E-5F when selected | backend/worker/delay parity | IPC/imbalance report |
| Memory bounds | every accelerator and trace is bounded | All selected work | high-water/eviction/rotation tests | memory and retention report |
| Client independence | projection never controls simulation | Stage 5H when selected | presence/absence and gap/resnapshot tests | serving report |
| Semantic approximation | separate versioned fidelity contract | Stage 6 only | differential/conservation/transition suite | separate architecture decision |

## 19. Revisit triggers

Reconsider this ordering when one of the following is demonstrated:

- Resolution plus sorting exceeds 50% of p95 tick compute time after earlier optimizations.
- Snapshot construction or IPC exceeds 20% of p95 tick compute time.
- Full canonical hashing exceeds its declared operational budget.
- Scheduler selection is material despite dirty/cadence/LOD gates.
- Network projection or per-client queues limit supported clients before simulation compute does.
- Target population/TPS remains unmet after exact optimizations.

Thresholds are initial decision aids, not performance requirements. A future ticket should replace
them with targets tied to supported hardware classes and product scale.

## 20. Final readiness and authorization statement

| Dimension | Final status |
|---|---|
| Architectural direction | Ready for approval |
| Required architecture decisions | D1-D6 pending named approvers |
| Prerequisite execution plan | Ready for normal ticket workflow after architecture approval |
| Conditional optimization roadmap | Evidence-gated by Decision Gate A |
| Advanced/semantic work | Requires Decision Gate B and separate architecture approval |
| Determinism safety | Strong design; final guarantee depends on D1 and D2 |
| Measurement readiness | Plan ready; tooling and contracts require prerequisite correction |
| Current implementation authorization | Prerequisite packages only; no Stage 5 or Stage 6 authorization |

Architecture approval permits normal tickets for approved PA packages, D1-D6 decision records,
verified baseline/harness corrections, authority reconciliation, bounded observability, benchmark
scenario materialization, and the Gate A bottleneck report. It does not itself merge or deploy
code. Stage 5 requires material Gate A evidence; Stage 6 requires Gate B and a separate approved
architecture proposal.

## 21. Authoritative project sources and external foundations

### Project sources

- `docs/engine/authoritative_pipeline.md`
- `docs/engine/kernel.md`
- `docs/engine/deterministic_execution.md`
- `docs/architecture/kernel_concurrency_design_philosophy.md`
- `docs/engine/candidate_selection.md`
- `docs/core/dirty_state_and_dependency.md`
- `docs/engine/performance_contract.md`
- `docs/engine/contracts/certification_contract.md`
- `docs/performance/perf_baseline_policy.md`
- `docs/performance/optimization_architecture.md`
- `docs/brainstorm/simulation_design_taxonomy.html`
- `docs/brainstorm/performance_evolution_roadmap.html`
- `src/engine/kernel.py`
- `src/engine/pipeline.py`
- `src/engine/phase_graph.py`
- `src/engine/phase_domain_permissions.py`
- `src/engine/scheduler.py`
- `src/engine/worker_manager.py`
- `src/engine/checkpoint.py`
- `src/engine/scenario_checkpoint.py`
- `src/engine/semantic_entity_index.py`
- `src/perf/bench_harness.py`
- `src/perf/long_run_harness.py`
- `src/perf/regression_gate.py`
- `src/platform/rng.py`
- `tests/perf/test_perf_regression_baseline.py`
- `tests/perf/test_concurrency_parity.py`
- `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`
- `docs/audits/D19_domain_phase_inventory.md`

### External foundations

- Leslie G. Valiant, [A Bridging Model for Parallel Computation](https://web.mit.edu/6.976/www/handout/valiant2.pdf), Communications of the ACM, 1990 — Bulk-Synchronous Parallel.
- Robert D. Blumofe and Charles E. Leiserson, [Scheduling Multithreaded Computations by Work Stealing](https://www.cs.cornell.edu/courses/cs612/2006sp/papers/blumofe94.pdf), 1994 — dynamic load balancing for structured parallel work.
- George Varghese and Anthony Lauck, [Hashed and Hierarchical Timing Wheels](https://www.cs.columbia.edu/~nahum/w6998/papers/ton97-timing-wheels.pdf), IEEE/ACM Transactions on Networking — scalable timer scheduling.
- Andrey Mokhov, Neil Mitchell, and Simon Peyton Jones, [Build Systems à la Carte: Theory and Practice](https://www.microsoft.com/en-us/research/publication/build-systems-a-la-carte/), Journal of Functional Programming, 2020 — dependency-driven incremental computation.
- Unity Technologies, [EntityQuery filters](https://docs.unity.cn/Packages/com.unity.entities%401.0/manual/systems-entityquery-filters.html) and [version numbers](https://docs.unity.cn/Packages/com.unity.entities%401.0/manual/systems-version-numbers.html) — production change filtering and generation tracking.
- Unity Technologies, [Archetype and chunk concepts](https://docs.unity.cn/Packages/com.unity.entities%401.0/manual/concepts-archetypes.html) — tightly packed component arrays and data-oriented iteration.
- Ralph C. Merkle, [A Digital Signature Based on a Conventional Encryption Function](https://people.eecs.berkeley.edu/~raluca/cs261-f15/readings/merkle.pdf), 1987 — hash-tree foundation.
- Gene M. Amdahl, [Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities](https://doi.org/10.1145/1465482.1465560), 1967 — the serial-fraction limit on parallel speedup.
- Python Software Foundation, [The Python Profilers](https://docs.python.org/3/library/profile.html)
  and [`time.perf_counter_ns()`](https://docs.python.org/3/library/time.html#time.perf_counter_ns)
  — deterministic call profiling and monotonic high-resolution interval measurement.
- Python `pyperf`, [Tune the system for benchmarks](https://pyperf.readthedocs.io/en/latest/system.html)
  — controlling system noise and recording benchmark environment metadata.
