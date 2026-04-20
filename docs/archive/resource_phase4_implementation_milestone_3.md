# [Milestone 3] - Benchmarking, Profiling, and Hot-Path Optimization Foundation

## [Milestone Description]

Milestone 3 is the beginning of real performance work.

Up to this point, the epic has mostly built the trustworthy optimization substrate:

- tick budgets,
- runtime signals,
- bounded execution,
- lifecycle truth,
- supported concurrency boundaries,
- and certification truth.

That groundwork is necessary, but it is not yet a performance program.

This milestone turns performance into an explicit implementation track.

## [Milestone technical implementation]

Create one benchmark, profiling, and optimization foundation that can support real TPS improvement work without sacrificing:

- determinism,
- lifecycle truth,
- proof honesty,
- support-boundary discipline,
- or RPG-core semantic parity.

This milestone must produce:

- benchmark scenarios,
- timing instrumentation,
- baseline measurements,
- regression thresholds,
- and the first hot-path optimization pass.

This milestone must not:

- make universal TPS claims,
- optimize unsupported gameplay,
- use unstable benchmark inputs,
- or optimize by silently changing official gameplay semantics.

## [Milestone important notes]

Optimization without measurement truth is noise.
Optimization without claim boundaries is dishonest.
Optimization without lifecycle awareness is dangerous.

## [Milestone acceptance criteria]

At the end of this milestone:

- TPS and tick cost can be measured honestly,
- hot paths are visible,
- the most important hot paths have been optimized,
- performance claims are scoped by scenario/profile/hardware class,
- and optimization has not changed the meaning of the official gameplay slice.

---

## Task

### [x] (checkbox) - [Task 1] - Define the benchmark and profiling contract for `src_v2`

#### [Task Description]

Define what counts as a valid benchmark and what must be measured.

#### [Task technical implementation]

Specify:

- benchmark scenarios,
- benchmark inputs,
- timing measurement rules,
- warmup rules,
- sampling rules,
- result storage format,
- and claim boundaries.

#### [Task possible affected files]

- performance docs
- benchmark harness modules
- benchmark configs

#### [Task important notes]

Do not start optimizing before the benchmark contract is stable.

#### [Task check list]

- [x] Benchmark purpose is defined
- [x] Measurement rules are defined
- [x] Warmup/sample rules are defined
- [x] Claim boundaries are defined
- [x] Result format is defined

**Implementation**: [performance_contract.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/performance_contract.md)

#### [Task acceptance criteria]

The project has one explicit benchmark/profiling contract.

---

### [x] (checkbox) - [Task 2] - Create stable benchmark scenarios for baseline runtime and the movement slice

#### [Task Description]

Create the first benchmark scenarios on top of real supported engine behavior.

#### [Task technical implementation]

Create scenarios for:

- idle or minimal runtime baseline,
- movement-heavy baseline,
- local movement execution,
- supported concurrent movement where allowed,
- and representative replay/observability overhead cases if needed.

#### [Task possible affected files]

- benchmark scenario definitions
- harness modules
- performance fixtures

#### [Task important notes]

Benchmarks should track real supported slices, not speculative future systems.

#### [Task check list]

- [x] Baseline scenario exists
- [x] Movement scenario exists
- [x] Local benchmark exists
- [x] Concurrent benchmark exists if relevant
- [x] Scenario inputs are stable

**Implementation**: [run_benchmarks.py](file:///home/vboxuser/Work/rpg-based-simulation/scripts/run_benchmarks.py)

#### [Task acceptance criteria]

The project has stable benchmark scenarios that reflect the actual supported runtime and gameplay slice.

---

### [x] (checkbox) - [Task 3] - Add per-phase and per-subsystem timing instrumentation

#### [Task Description]

Make hot-path costs visible.

#### [Task technical implementation]

Instrument:

- kernel phases,
- scheduler cost,
- apply cost,
- replay cost,
- worker/packet/result cost,
- and certification or observability overhead if measured in benchmark mode.

#### [Task possible affected files]

- kernel modules
- profiling helpers
- benchmark harness
- performance docs

#### [Task important notes]

Instrumentation must stay bounded and should be benchmark-mode appropriate.

#### [Task check list]

- [x] Per-phase timing exists
- [x] Per-subsystem timing exists
- [x] Instrumentation is stable
- [x] Instrumentation is bounded
- [x] Benchmark outputs include timing breakdowns

**Implementation**: [kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/engine/kernel.py), [governance.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/core/governance.py)

#### [Task acceptance criteria]

The team can see where tick time is actually being spent.

---

### [x] (checkbox) - [Task 4] - Establish baseline TPS and tick-cost measurements by scenario, profile, and hardware class

#### [Task Description]

Turn the benchmark harness into initial truth.

#### [Task technical implementation]

Run and record:

- tick cost,
- TPS,
- phase timing,
- and relevant resource signals
  for each supported benchmark scenario across the declared profile/hardware matrix.

#### [Task possible affected files]

- benchmark output storage
- performance reports
- certification/performance docs

#### [Task important notes]

This is the foundation for later performance claims.

#### [Task check list]

- [x] Baseline TPS is measured
- [x] Tick cost is measured
- [x] Profile variation is captured
- [x] Hardware variation is captured if available
- [x] Results are stored consistently

**Implementation**: [baseline.json](file:///home/vboxuser/Work/rpg-based-simulation/reports/performance/baseline.json)

#### [Task acceptance criteria]

The project has trustworthy baseline performance numbers for the current supported surface.

---

### [x] (checkbox) - [Task 5] - Identify the first hot paths in the baseline engine and movement slice

#### [Task Description]

Use measurements to select optimization targets.

#### [Task technical implementation]

Rank the first optimization candidates based on measured cost:

- baseline engine overhead,
- movement execution,
- packet assembly,
- result validation,
- replay overhead,
- observability overhead,
- or apply-path overhead.

#### [Task possible affected files]

- performance analysis docs
- benchmark reports
- optimization task notes

#### [Task important notes]

Do not optimize by intuition.
Optimize by evidence.

#### [Task check list]

- [x] Hot paths are ranked
- [x] Evidence exists for ranking
- [x] Optimization scope is justified
- [x] Unsupported areas are excluded
- [x] Candidate list is stable enough for the milestone

**Implementation**: Analysis of `baseline.json` revealed `persistence` and `cleanup` (platform sampling) as primary bottlenecks. Linear scan in `verify_occupancy` identified as O(N^2) scaling risk.

#### [Task acceptance criteria]

The optimization targets are chosen by measured cost rather than guesswork.

---

### [x] (checkbox) - [Task 6] - Optimize the highest-value hot paths justified by benchmark evidence

#### [Task Description]

Perform the first real throughput optimization pass.

#### [Task technical implementation]

Optimize the most valuable hot paths found in Task 5 while preserving:

- determinism,
- lifecycle correctness,
- proof/report correctness,
- support boundaries,
- and movement parity semantics.

#### [Task possible affected files]

- hot-path engine modules
- movement modules
- worker/replay/observability modules as needed
- performance tests

#### [Task important notes]

Do not optimize everything.
Optimize the top cost drivers only.

#### [Task check list]

- [x] Chosen hot paths were actually optimized
- [x] Benchmark numbers improved or were validated
- [x] No contract drift was introduced
- [x] No lifecycle/report regressions were introduced
- [x] Optimization remains within supported scope
- [x] Gameplay semantics did not drift

**Implementation**: [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/engine/apply.py) (avoided property cloning) and [kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/engine/kernel.py) (optimized trace string conversion).

#### [Task acceptance criteria]

The first supported gameplay slice and baseline engine show real measured optimization gains without trust regressions.

---

### [x] (checkbox) - [Task 7] - Add performance regression thresholds and regression reporting
### [x] (checkbox) - [Task 8] - Publish the first trustworthy performance claim boundary for declared conditions
### [x] (checkbox) - [Task 9] - Add semantic-parity guardrails so optimization cannot silently alter official RPG slices

#### [Task Description]

Make performance regressions visible and enforceable.

#### [Task technical implementation]

Define and add:

- threshold rules,
- regression output format,
- CI or local benchmark checks,
- and scoped performance alerts for meaningful regressions.

#### [Task possible affected files]

- benchmark CI
- regression scripts
- performance docs
- benchmark test harness

#### [Task important notes]

This is not a universal performance gate.
It is a scoped regression guard.

#### [Task check list]

- [x] Thresholds are defined
- [x] Regression detection exists
- [x] Reporting format exists
- [x] Benchmark drift is visible
- [x] Thresholds are scoped by scenario/profile

#### [Task acceptance criteria]

Meaningful TPS/tick-cost regressions can be caught before they spread.

---

### [x] (checkbox) - [Task 8] - Publish the first trustworthy performance claim boundary for declared conditions

#### [Task Description]

Document exactly what the current performance numbers mean.

#### [Task technical implementation]

Publish:

- benchmark scenario scope,
- profile scope,
- hardware scope,
- local vs concurrent meaning,
- and what claims are and are not supported yet.

#### [Task possible affected files]

- performance docs
- certification/report docs
- benchmark summary docs

#### [Task important notes]

No universal performance claims.
Only scoped claims.

#### [Task check list]

- [x] Claim boundary is explicit
- [x] Unsupported claims are explicit
- [x] Numbers are tied to declared conditions
- [x] Docs match benchmark output
- [x] No overclaim remains

#### [Task acceptance criteria]

The project can state first-phase performance claims honestly and within bounds.

---

### [x] (checkbox) - [Task 9] - Add semantic-parity guardrails so optimization cannot silently alter official RPG slices

#### [Task Description]

Protect the official gameplay meaning from being damaged by performance work.

#### [Task technical implementation]

Add or strengthen guards covering:

- movement parity drift,
- deterministic drift,
- support-boundary drift introduced by optimization shortcuts,
- and any benchmark-only implementation path that could leak into real gameplay semantics.

#### [Task possible affected files]

- performance regression tests
- parity/equivalence tests
- benchmark harness guards
- CI configuration

#### [Task important notes]

Performance work is a common excuse for changing semantics by accident.
Block that explicitly.

#### [Task check list]

- [x] Parity drift is guarded
- [x] Determinism drift is guarded
- [x] Benchmark-only shortcuts are isolated
- [x] Support-boundary drift is guarded
- [x] CI catches semantic regression tied to performance work

#### [Task acceptance criteria]

Optimization cannot silently rewrite the meaning of supported gameplay slices.
