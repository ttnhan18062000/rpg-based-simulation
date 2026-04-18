Below is the rewritten high-level implementation plan.

It is now aligned to the constraints you locked in:

- fresh project, not a migration,
- no backward-compatibility burden,
- TDD from the start,
- stable and bounded resource usage by profile,
- deterministic semantics,
- resource-envelope certification instead of fake “same performance everywhere” claims,
- and milestone-first delivery in the same reference style as your combat/movement plan.

It is also shaped by the actual failure modes seen in the current source and tests: replay accumulation, expensive snapshotting, heavy serialization, distributed snapshot broadcast, and aggressive resource-kill tests proving that RAM/CPU exhaustion is already a real risk.

---

# High-level implementation plan — resource-safe simulation engine rebuild

This plan defines the high-level delivery order for rebuilding the simulation engine as a fresh project.

It follows a milestone-first structure, keeps the semantic rulebook explicit, enforces test-driven development from the start, and treats resource safety as a product requirement rather than a later optimization pass.

This is **not** the detailed task list.
This is the implementation frame: what gets built first, what depends on what, and what each milestone must accomplish before the next one starts.

This plan is shaped around the major decisions already discussed:

- this is a fresh project, not a legacy migration,
- original system behavior is used as a requirements source, not an implementation constraint,
- deterministic simulation semantics must be explicit,
- bounded resource usage is mandatory,
- runtime profiles must define fixed resource envelopes,
- replay, observability, and concurrency must obey budgets,
- TDD must drive every milestone,
- and success must be measured by semantic correctness, envelope compliance, and certified throughput by hardware class, not vague benchmark vanity.

---

# Milestone 1 — Freeze the simulation kernel and resource-envelope contract

### Description

Define the exact semantic and operational contract that every later implementation must obey.

This milestone exists to stop the rebuild from drifting into accidental behavior, hidden assumptions, or fake performance goals.

### Technical implementation

Create one exact design contract for:

- world tick semantics,
- action readiness semantics,
- authoritative apply order,
- deterministic RNG behavior,
- authoritative state vs derived state,
- failure boundaries,
- and runtime resource-envelope rules.

This milestone must explicitly define:

- what state is authoritative,
- what outputs must be deterministic for the same seed and profile,
- what can be degraded without changing core semantics,
- what each runtime profile is allowed to consume,
- and what “equivalent behavior” means for the new engine.

The resource-envelope contract must define, per profile:

- max RAM,
- max CPU/core usage,
- max worker count,
- max queue depth,
- max replay budget,
- max observability budget,
- max per-tick work budget,
- degradation thresholds,
- and minimum certified throughput by hardware class.

### Important notes

Do not start with concurrency, replay, scheduling tricks, or broker decisions before this contract is frozen.

Do not use “same performance on any machine” as a requirement.
The correct requirement is:

- same semantics,
- same resource envelope,
- same degradation behavior,
- and certified throughput by hardware class.

### Testing requirements

Add contract tests for:

- deterministic seed reproduction,
- authoritative apply-order expectations,
- tick semantics,
- authoritative vs non-authoritative state boundaries,
- and resource-profile validation expectations.

These are contract tests, not feature tests.

### Acceptance criteria

The project has one explicit simulation-kernel contract and one explicit resource-envelope contract, both pinned by deterministic tests.

### Checklist

- [ ] Freeze simulation semantics
- [ ] Freeze authoritative apply order
- [ ] Freeze deterministic RNG contract
- [ ] Freeze authoritative vs derived-state boundaries
- [ ] Freeze runtime profile model
- [ ] Freeze resource-envelope rules
- [ ] Add contract tests
- [ ] Add kernel and resource-envelope documentation

---

# Milestone 2 — Build the minimal deterministic single-thread kernel

### Description

Build the smallest correct engine core before introducing replay, workers, advanced observability, or optimization layers.

This milestone exists to establish one trustworthy baseline that is easy to reason about and easy to test.

### Technical implementation

Implement a minimal single-thread kernel with:

- world state,
- deterministic RNG,
- tick advancement,
- readiness-based action gating,
- authoritative action application,
- lifecycle progression,
- and stable phase ordering.

Keep this kernel deliberately small and explicit.

Do not add:

- worker execution,
- replay persistence,
- remote transport,
- adaptive degradation,
- or advanced instrumentation beyond what is needed to validate behavior.

### Important notes

Do not contaminate the baseline kernel with speculative infrastructure.

A correct minimal kernel is the reference truth for every later optimization.

### Testing requirements

Use TDD to add:

- phase-order tests,
- quiet-tick lifecycle tests,
- readiness gating tests,
- deterministic state-hash checkpoint tests,
- and invalid-state rejection tests.

### Acceptance criteria

The project has one minimal deterministic kernel that passes semantic correctness tests without advanced infrastructure.

### Checklist

- [ ] Implement minimal world loop
- [ ] Implement deterministic RNG plumbing
- [ ] Implement authoritative apply phase
- [ ] Implement lifecycle progression
- [ ] Add stable checkpoint hashing
- [ ] Add minimal-kernel tests
- [ ] Document baseline runtime phases

---

# Milestone 3 — Build bounded runtime state and lean hot-path models

### Description

Design runtime data structures so the new engine cannot accidentally recreate the old memory and CPU pathologies.

This milestone exists because most runaway systems are born from bad state shape, not from one dramatic bug.

### Technical implementation

Separate model categories into:

- **runtime models** for hot-path execution,
- **persistence/export models** for replay and APIs,
- **diagnostic models** for observability and debugging.

Use lean hot-path structures and explicit retention discipline.

Every long-lived structure must declare:

- ownership,
- max size or retention window,
- compaction or eviction policy,
- overflow behavior,
- and observability hooks.

This applies to:

- world history,
- event logs,
- caches,
- registries,
- replay buffers,
- worker queues,
- metrics buffers,
- and debug traces.

### Important notes

Do not use rich validation-heavy models as the default runtime representation.

Use validation at boundaries, not as the main execution model.

### Testing requirements

Add bounded-state tests for:

- history retention,
- queue depth limits,
- cache eviction,
- replay window bounds,
- and registry compaction behavior.

### Acceptance criteria

Every persistent or long-lived runtime structure has an explicit bound or compaction rule enforced by tests.

### Checklist

- [ ] Separate runtime vs export vs diagnostic models
- [ ] Define bounds for all long-lived structures
- [ ] Define eviction and compaction rules
- [ ] Define overflow behavior
- [ ] Add bounded-state tests
- [ ] Document runtime state-shape rules

---

# Milestone 4 — Build the scheduler and deterministic work model

### Description

Replace naive “scan everything and do everything” execution with an explicit, deterministic, budget-aware work model.

This milestone exists because the engine must remain predictable under load without changing semantics.

### Technical implementation

Implement:

- readiness-aware scheduling,
- deterministic candidate selection,
- fixed tie-break rules,
- explicit work classes,
- deferred maintenance work,
- and bounded work debt.

Split work into:

- critical,
- periodic,
- opportunistic,
- and deferred.

Critical work must always execute within kernel semantics.
Optional work must never be allowed to distort authoritative behavior.

The scheduler must preserve the semantic contract defined in Milestone 1.

### Important notes

Do not make the scheduler “faster” by making it vague.

The execution model must stay deterministic and explainable.

### Testing requirements

Add scheduler tests for:

- readiness ordering,
- tie-break determinism,
- quiet-tick behavior,
- periodic-work cadence,
- and bounded deferred-work handling.

### Acceptance criteria

The engine executes authoritative work efficiently and deterministically without broad per-tick waste.

### Checklist

- [ ] Implement readiness-aware scheduler
- [ ] Freeze deterministic tie-break rules
- [ ] Add work classes
- [ ] Add deferred work handling
- [ ] Add scheduler determinism tests
- [ ] Add heavy-load scheduler tests
- [ ] Document the work model

---

# Milestone 5 — Build the resource governor and degradation state machine

### Description

Add the runtime control layer that protects the engine from exhausting RAM, CPU, queue capacity, and persistence budgets.

This milestone exists because external watchdogs are not a runtime safety strategy.

### Technical implementation

Implement a `ResourceGovernor` responsible for tracking:

- memory usage,
- CPU/tick budget usage,
- queue pressure,
- replay backlog,
- serialization cost,
- observability overhead,
- and worker pressure.

Define runtime modes:

- `NORMAL`
- `CONSTRAINED`
- `DEGRADED`
- `SURVIVAL`

Define exactly what each mode reduces or disables.

The degradation order must prioritize preserving core simulation semantics while shedding non-authoritative cost first, such as:

1. verbose diagnostics,
2. detailed replay payloads,
3. optional metrics,
4. high-cost summaries,
5. opportunistic maintenance,
6. non-critical enrichments.

### Important notes

Degradation must not silently skip or corrupt authoritative entity logic.

The governor protects execution quality. It does not rewrite game rules.

### Testing requirements

Add governor tests for:

- pressure threshold detection,
- trend-based escalation,
- degradation mode transitions,
- optional-work shedding,
- and recovery after pressure drops.

### Acceptance criteria

The engine can detect pressure early, degrade optional cost in a controlled order, and protect core execution without crashing.

### Checklist

- [ ] Implement resource governor
- [ ] Define pressure signals
- [ ] Define degradation modes
- [ ] Define per-mode subsystem behavior
- [ ] Add mode-transition tests
- [ ] Add shedding and recovery tests
- [ ] Document degradation policy

---

# Milestone 6 — Build streaming replay and bounded persistence

### Description

Implement replay and persistence as bounded streaming systems rather than in-memory accumulation traps.

This milestone exists because replay must never be allowed to destabilize long runs.

### Technical implementation

Implement replay as:

- append-only chunked writes,
- bounded recent in-memory window,
- size- or tick-based rotation,
- optional compression on closed chunks,
- manifest/index metadata,
- and profile-controlled replay modes.

Replay modes must include at least:

- `OFF`
- `MINIMAL`
- `DEBUG_WINDOWED`
- `FORENSIC_SHORT_RUN`

Replay behavior must be governed by the runtime profile and monitored by the governor.

### Important notes

Replay is observational infrastructure.
It is not entitled to unlimited RAM or CPU.

### Testing requirements

Add replay tests for:

- chunk rotation,
- bounded in-memory window,
- disk quota handling,
- replay mode behavior,
- sink slowdown handling,
- and logical event ordering.

### Acceptance criteria

Replay no longer creates unbounded memory growth and its cost is bounded, visible, and profile-controlled.

### Checklist

- [ ] Implement chunked replay sink
- [ ] Add replay mode system
- [ ] Add bounded recent window
- [ ] Add disk-budget handling
- [ ] Add replay pressure metrics
- [ ] Add replay safety tests
- [ ] Document replay modes

---

# Milestone 7 — Build observability and operational controls

### Description

Expose the runtime signals needed to inspect pressure, budget use, degradation, and throughput without turning observability into a new resource problem.

This milestone exists because systems that cannot be inspected end up being tuned by superstition.

### Technical implementation

Expose structured metrics for:

- RSS and memory trend,
- tick duration,
- scheduler latency,
- queue depth,
- replay backlog,
- payload sizes,
- dropped optional work,
- degradation transitions,
- compaction runs,
- and profile identity.

Add operational controls:

- startup config validation,
- safe runtime profiles,
- feature flags for optional subsystems,
- graceful shutdown behavior,
- and explicit runtime mode surfacing.

### Important notes

Observability itself must obey budgets.

Do not rebuild the old mistake where heavy instrumentation quietly becomes part of the resource problem.

### Testing requirements

Add tests for:

- stable metric exposure,
- startup rejection of unsafe configs,
- graceful shutdown behavior,
- and deterministic degradation reporting.

### Acceptance criteria

The engine is inspectable and operable under test and production profiles without violating its own envelope discipline.

### Checklist

- [ ] Expose resource and pressure metrics
- [ ] Expose degradation signals
- [ ] Add startup config validation
- [ ] Add safe runtime profiles
- [ ] Add graceful shutdown handling
- [ ] Add observability contract tests
- [ ] Document operational controls

---

# Milestone 8 — Build safe concurrency and bounded worker execution

### Description

Add concurrency only after the deterministic kernel, bounded state, scheduler, governor, replay, and observability are stable.

This milestone exists because concurrency amplifies architectural mistakes if introduced too early.

### Technical implementation

Implement worker execution around compact bounded work packets:

- actor-local state slice,
- required neighborhood/world slice,
- compact decision results,
- bounded inflight batches,
- bounded queue depth,
- fixed worker limits by profile,
- and safe fallback to local execution.

Concurrency must be profile-controlled and resource-envelope aware.

It must never depend on shipping giant object graphs or retaining large world clones per worker.

### Important notes

Do not introduce external brokers unless profiling later proves they are necessary.

The first goal is bounded, deterministic, local concurrency.

### Testing requirements

Add concurrency tests for:

- compact packet correctness,
- inflight cap enforcement,
- queue-depth limits,
- fallback-to-local execution,
- deterministic equivalence under the same seed and profile,
- and bounded-memory worker stress cases.

### Acceptance criteria

Concurrency improves throughput within declared profile limits without creating replicated memory blowups or unstable queue growth.

### Checklist

- [ ] Define compact work packet contract
- [ ] Add bounded inflight execution
- [ ] Add worker and queue caps
- [ ] Add fallback-to-local execution
- [ ] Add concurrency correctness tests
- [ ] Add worker stress tests
- [ ] Document concurrency model

---

# Milestone 9 — Build the resource certification and resilience harness

### Description

Create one disciplined harness for proving envelope compliance, resilience, degradation, and throughput under named profiles.

This milestone exists to replace weak benchmark vanity with hard operational evidence.

### Technical implementation

Build a reusable certification harness for:

- long-run single-thread execution,
- long-run worker execution,
- replay stress,
- queue saturation,
- serialization stress,
- memory-pressure injection,
- degraded-mode entry and recovery,
- and graceful shutdown under pressure.

Certification must verify three things:

1. semantic correctness under a profile,
2. resource-envelope compliance under a profile,
3. throughput achieved on a certified hardware class.

Add optional **rate-limited benchmark mode** for cases where you want reproducible capped throughput on stronger machines.

### Important notes

Do not claim “same performance on all systems.”

The correct output of this milestone is:

- stable resource usage by profile,
- reproducible degradation behavior,
- and certified throughput by hardware class.

### Testing requirements

Add certification suites for:

- profile conformance,
- memory and queue ceilings,
- degradation-before-failure behavior,
- recovery after transient pressure,
- deterministic semantics under repeated runs,
- and hardware-class throughput certification.

### Acceptance criteria

The project has a repeatable certification harness proving that the engine stays within declared resource envelopes and degrades before it crashes.

### Checklist

- [ ] Create profile-based certification harness
- [ ] Add pressure-injection scenarios
- [ ] Add degradation and recovery scenarios
- [ ] Add replay and queue stress scenarios
- [ ] Add hardware-class throughput certification
- [ ] Add optional rate-limited benchmark mode
- [ ] Document certification matrix

---

# Milestone 10 — Finalize the documentation pack and engineering playbook

### Description

Make the new engine understandable enough that future work does not reintroduce the same failures in cleaner-looking code.

This milestone exists so the architecture remains maintainable under growth.

### Technical implementation

Finalize the documentation pack:

- simulation-kernel contract,
- runtime profile and resource-envelope rules,
- bounded-state rules,
- scheduler and work model,
- governor and degradation policy,
- replay design,
- observability contract,
- concurrency model,
- certification matrix,
- and TDD rules for future features.

Also create the engineering playbook:

- how to add a subsystem safely,
- how to declare a resource budget,
- how to define a retention policy,
- how to write contract tests first,
- how to add scenario tests,
- and how to avoid turning diagnostics into production cost.

### Important notes

Do not end this project with “the team knows how it works.”

That is how the next failure gets planted.

### Testing requirements

Add documentation-integrity checks for:

- runtime profiles,
- surfaced metrics,
- replay modes,
- degradation modes,
- and certification expectations.

### Acceptance criteria

The project is understandable, inspectable, and maintainable without tribal memory.

### Checklist

- [ ] Finalize architecture docs
- [ ] Finalize runtime-profile docs
- [ ] Finalize TDD playbook
- [ ] Finalize degradation matrix docs
- [ ] Finalize certification docs
- [ ] Add documentation-integrity checks
- [ ] Publish contributor guardrails

---

## Recommended implementation order

1. Milestone 1 — Freeze the simulation kernel and resource-envelope contract
2. Milestone 2 — Build the minimal deterministic single-thread kernel
3. Milestone 3 — Build bounded runtime state and lean hot-path models
4. Milestone 4 — Build the scheduler and deterministic work model
5. Milestone 5 — Build the resource governor and degradation state machine
6. Milestone 6 — Build streaming replay and bounded persistence
7. Milestone 7 — Build observability and operational controls
8. Milestone 8 — Build safe concurrency and bounded worker execution
9. Milestone 9 — Build the resource certification and resilience harness
10. Milestone 10 — Finalize the documentation pack and engineering playbook

This order is the right one because it prevents the usual failure pattern:

- parallelize before the kernel is stable,
- persist before budgets exist,
- instrument without bounds,
- then discover too late that the architecture itself is what causes resource collapse.

---

## TDD guidance for the whole plan

Across all milestones:

- write the contract test first,
- implement the smallest coherent behavior,
- refactor to isolate responsibility,
- add scenario regression coverage,
- then add stress and certification coverage once semantics are stable.

Use TDD in this order:

1. contract tests,
2. minimal implementation,
3. refactor,
4. scenario tests,
5. stress tests,
6. certification tests.

Do not start with giant end-to-end suites before the semantic contract is frozen.
Do not start with concurrency before bounded state and the governor exist.
Do not start with vague performance benchmarks before resource profiles are defined.

---

## Modern stack guidance for this epic

Use modern tools where they reduce cost and complexity, not where they create architecture theater.

Recommended direction:

- Python core runtime for fast iteration and TDD
- `pytest` for core, scenario, and certification tests
- `hypothesis` for invariants and bounded-state property tests
- lean runtime dataclasses or similarly lightweight hot-path structures
- Pydantic only at configuration and external boundaries
- `orjson` or `msgspec` for fast serialization where needed
- `psutil` for runtime resource visibility
- Prometheus metrics
- OpenTelemetry traces where justified
- optional chunk compression for replay
- bounded local multiprocessing before any external broker

Do not start with broker-first architecture.
Do not start with rewrite-in-a-lower-level-language fantasies unless profiling later proves a narrow kernel truly needs it.

---

## Final delivery condition

This rebuild is complete only when all of the following are true:

- the simulation kernel contract is explicit and test-pinned,
- runtime profiles define fixed resource envelopes,
- the minimal kernel is deterministic and correct,
- runtime state is bounded by design,
- replay and observability cannot silently destabilize long runs,
- the governor degrades optional cost before failure,
- concurrency remains within declared limits,
- certification proves envelope compliance and resilience,
- and throughput is documented by hardware class instead of fake universal claims.

---

## Priority Plan

What you must change in mindset or assumptions
Stop thinking of performance as one abstract number. The real target is deterministic semantics plus bounded resource envelopes plus certified throughput by hardware class.

What actions you must take immediately
Freeze the kernel and profile contract first. Build the minimal kernel second. Define bounded-state rules before replay and workers. Add the governor before concurrency. Make certification a core milestone, not cleanup.

What you must stop or eliminate
Stop carrying migration logic into a fresh project. Stop tolerating unbounded structures anywhere. Stop using weak TPS bars as proof of success. Stop pretending identical performance across different hardware is a real requirement.

The consequences and opportunity cost if you fail to change
You will rebuild the same structural failures in cleaner code, then waste months tuning symptoms. The only winning path is contract-first, bound-first, and certification-first engineering.

If you want, next I’ll turn this into the detailed milestone-by-milestone implementation task plan in the same format.
