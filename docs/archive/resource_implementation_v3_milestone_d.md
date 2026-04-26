# [Milestone D] - Bounded Concurrency That Can Be Trusted

## [Milestone Description]

Milestone D exists to move v2 from bounded concurrency **prototype** to bounded concurrency **contract**.

The current code already has the structural pieces:

- worker packet and worker result models,
- worker manager,
- local-vs-worker execution split,
- authoritative apply path,
- scheduler-selected work,
- and some concurrency-oriented tests.

That is the good news.

The bad news is that the current worker path is still not trustworthy enough to carry real RPG logic. The default worker logic is placeholder-level rather than real domain execution, and the concurrency surface still depends on thin assumptions around packet meaning, result meaning, fallback safety, batch behavior, and failure handling. That means the engine has a concurrency shape, but not yet concurrency law. See [all_src.py](sandbox:/mnt/data/all_src.py).

Milestone D exists to make these things true:

- worker execution becomes a real bounded execution path,
- packet and result contracts become exact,
- commit ordering remains authoritative and deterministic,
- worker failure and timeout behavior become explicit,
- local fallback becomes exact and safe,
- local-vs-concurrent equivalence becomes provable,
- batch execution remains bounded by profile,
- and concurrent execution becomes a trustworthy substrate for attaching real RPG logic.

This milestone is where the project earns the right to say:

“the single-process path remains the semantic source of truth, and the concurrent path is a bounded execution optimization that is proven equivalent under declared conditions.”

That is the real goal.

---

## [Milestone technical implementation]

Create one fully declared bounded concurrency contract in which worker execution is deterministic at the authoritative boundary, bounded by profile, safe under failure, and provably equivalent to the local baseline under supported conditions.

This milestone must implement these exact rules.

### Concurrency completion rules

1. **Single-process remains the semantic source of truth**
   - The local single-process path remains the reference semantics.
   - Worker mode may optimize execution, but it may not redefine authoritative meaning.
   - All concurrent execution must prove equivalence against the Milestone A baseline.

2. **Worker packet contract must be exact**
   - Every field in a worker packet must have one explicit meaning.
   - Snapshot inputs, neighbor views, work kind, tick context, and payload boundaries must be declared exactly.
   - Workers must not depend on undeclared global state.

3. **Worker result contract must be exact**
   - A worker result must contain only declared transient outputs.
   - Authoritative mutation still happens only through the apply path.
   - Results must be mergeable, auditable, and failure-classifiable.

4. **Concurrent execution must remain bounded**
   - Worker count,
   - inflight work,
   - submission behavior,
   - time spent waiting,
   - and fallback behavior
     must all obey profile-defined limits.

5. **Commit order must remain deterministic**
   - Parallel completion order is not authoritative order.
   - Authoritative application order must be frozen and independent of race timing.
   - Same seed + same inputs + same profile + same supported mode must produce equivalent authoritative results.

6. **Failure handling must be explicit**
   - Submit failure,
   - worker crash,
   - worker timeout,
   - partial batch completion,
   - invalid result,
   - and fallback-to-local
     must all have exact meaning.

7. **Fallback must be safe and bounded**
   - Local fallback must preserve authoritative semantics.
   - Fallback must be visible operationally.
   - Fallback must not silently turn into unbounded work amplification.

8. **Concurrent execution must be testable end-to-end**
   - Local-vs-concurrent equivalence must be directly testable.
   - Fault injection must be directly testable.
   - Headless system runs must be able to exercise concurrent execution under controlled conditions.

9. **Concurrency state must remain non-authoritative**
   - Worker pool state,
   - futures,
   - inflight counters,
   - failure counters,
   - and batch control metadata
     must not affect authoritative checkpoint identity directly.

10. **Real RPG logic attachment starts here**

- Milestone D is the milestone where real worker-based RPG logic becomes legitimate.
- Not all RPG systems need to land here, but the execution seam becomes trustworthy enough to attach real domain slices.

### Milestone D coverage boundary

11. **What this milestone must cover**

- worker packet/result contract closure,
- deterministic authoritative commit law under concurrency,
- worker manager boundedness and submission control,
- timeout/crash/failure/fallback law,
- local-vs-concurrent equivalence proof,
- worker metrics and runtime-control integration,
- headless concurrent system testing,
- and concurrency test closure.

12. **Non-goals of this milestone**

- no distributed or remote worker system,
- no broker architecture,
- no cluster scheduling,
- no full certification expansion beyond concurrency proof needs,
- no full gameplay breadth explosion,
- no broad production observability platform beyond concurrency truth needs.

13. **Clean-code boundary**

- scheduler selects work,
- packet builder prepares declared worker inputs,
- worker executes bounded transient logic,
- result validator/classifier checks outputs,
- apply path commits authoritative changes,
- worker manager owns execution control,
- runtime status surfaces concurrency truth,
- and the kernel orchestrates without absorbing detailed worker semantics.

---

## [Milestone important notes]

The first trap is thinking “workers already exist, so concurrency is mostly done.” That is false. A worker pool is not a concurrency contract.

The second trap is allowing concurrent completion timing to influence authoritative ordering. That would destroy determinism at the point where the engine claims to preserve it.

The third trap is treating fallback as a safety blanket without cost. Fallback is part of the runtime law. If it is not bounded and surfaced, it becomes hidden load amplification.

The fourth trap is attaching real RPG logic before packet, result, failure, and equivalence laws are closed. That would turn every gameplay bug into an execution-contract bug at the same time.

The fifth trap is writing tests that prove incidental behavior instead of concurrency law. For this milestone, that means no fake confidence from submission order, future collection order, or race timing that “usually looks stable.”

---

## [Milestone acceptance criteria]

At the end of Milestone D, the codebase has:

- one exact bounded concurrency contract,
- one exact worker packet and worker result law,
- one explicit authoritative commit-order law under concurrent execution,
- one explicit worker failure and fallback law,
- one bounded worker-manager execution contract,
- one truthful concurrency-status surface,
- one complete local-vs-concurrent equivalence test suite,
- one complete concurrency fault-injection test suite,
- and one trustworthy worker execution seam for attaching real RPG logic.

No full certification expansion or full gameplay breadth is required for Milestone D completion.

---

# ## Task

---

## [ ] (checkbox) - [Task 1] - Freeze the bounded concurrency law set

### [Task Description]

Create one exact contract for concurrent execution, worker inputs, worker outputs, authoritative commit order, failure handling, fallback behavior, and equivalence proof.

### [Task technical implementation]

Write one Milestone D contract document that defines:

- exact purpose of concurrent mode,
- exact supported execution model,
- exact packet contract,
- exact result contract,
- exact authoritative ordering contract,
- exact failure classes,
- exact fallback rules,
- exact boundedness rules,
- exact equivalence definition,
- exact authoritative/non-authoritative separation,
- and exact out-of-scope list.

This document must explicitly define:

- what “equivalent to local mode” means,
- what fields are allowed inside worker packets,
- what worker code may and may not assume,
- what makes a result valid,
- what makes a batch valid,
- and what counts as concurrency success vs partial-success.

### [Task possible affected files]

- `docs/engine/bounded_concurrency_contract_md.md`
- `docs/engine/md_test_matrix.md`
- `src/engine/worker_manager.py`
- `src/engine/kernel.py`
- `src/core/work.py`
- `src/core/updates.py`

### [Task important notes]

Do not let concurrency semantics remain implicit in test shape.
Do not let “equivalence” remain hand-wavy.

### [Task check list]

- [ ] Freeze concurrent execution purpose
- [ ] Freeze packet law
- [ ] Freeze result law
- [ ] Freeze authoritative ordering law
- [ ] Freeze failure and fallback law
- [ ] Freeze boundedness law
- [ ] Freeze equivalence law
- [ ] Freeze non-goals

### [Task acceptance criteria]

The project has one exact bounded concurrency contract defining the finished Milestone D law set.

---

## [ ] (checkbox) - [Task 2] - Complete and harden the worker packet contract

### [Task Description]

Turn worker input from a thin transport object into a strict execution boundary.

### [Task technical implementation]

Audit `WorkerPacket` and define exact semantics for every field, including:

- subject entity snapshot,
- subject identity and tick context,
- neighbor view,
- work kind,
- mode/policy context if allowed,
- payload shape,
- random context if any,
- and any deterministic execution metadata.

Then harden packet creation so that:

1. **Packets are self-sufficient within declared scope**
   - a worker must not depend on undeclared global state,
   - a packet must contain all declared inputs for the supported work kind.

2. **Packet contents are bounded**
   - neighbor view size must be bounded,
   - payload must be bounded,
   - serialization or copy cost must be bounded,
   - packet assembly must obey profile-safe limits.

3. **Packet semantics are deterministic**
   - same state and same selection -> same packet contents,
   - ordering of neighbor/context inputs must be deterministic,
   - packet construction must not depend on incidental container order.

4. **Unsupported work kinds are explicit**
   - if a work kind is not concurrency-safe yet, packet generation must reject it or route it to local mode explicitly.

### [Task possible affected files]

- `src/engine/worker_manager.py`
- `src/core/work.py`
- `src/core/state.py`
- `src/engine/kernel.py`
- packet-related tests

### [Task important notes]

Do not build bloated packets full of convenience state.
Do not let workers read live world state behind the packet boundary.

### [Task check list]

- [ ] Audit all packet fields
- [ ] Freeze packet field meanings
- [ ] Bound neighbor/payload size
- [ ] Freeze deterministic packet assembly
- [ ] Reject unsupported concurrent work kinds
- [ ] Add packet contract tests
- [ ] Document packet law

### [Task acceptance criteria]

Worker packets are exact, deterministic, bounded, and self-sufficient within declared concurrency scope.

---

## [ ] (checkbox) - [Task 3] - Complete and harden the worker result contract

### [Task Description]

Turn worker results into an exact transient output format that can be validated, classified, and committed safely.

### [Task technical implementation]

Audit `WorkerResult` and related update models so that:

1. **Result semantics are exact**
   - success result,
   - failed result,
   - timed-out result,
   - invalid-result classification,
   - fallback-requesting result if applicable,
   - and no-op result
     must all be distinct and explicit.

2. **Result payload is bounded**
   - number of updates per result must be bounded,
   - result payload size must be bounded,
   - diagnostic/error metadata must be bounded.

3. **Result validation is explicit**
   - reject malformed updates,
   - reject unsupported update kinds,
   - reject contradictory or incomplete result state,
   - classify validation failure explicitly.

4. **Result meaning remains non-authoritative until apply**
   - worker result is transient evidence,
   - authoritative mutation still belongs exclusively to apply.

### [Task possible affected files]

- `src/core/updates.py`
- `src/engine/worker_manager.py`
- `src/engine/apply.py`
- result-validation tests

### [Task important notes]

Do not let result shape imply direct mutation authority.
Do not use generic booleans when classification is needed.

### [Task check list]

- [ ] Audit result fields
- [ ] Freeze result categories
- [ ] Bound result payload size
- [ ] Add result validation layer
- [ ] Reject malformed or contradictory results
- [ ] Keep result meaning transient until apply
- [ ] Add result contract tests

### [Task acceptance criteria]

Worker results are exact, bounded, classifiable, and safe to validate before authoritative application.

---

## [ ] (checkbox) - [Task 4] - Replace placeholder worker execution with a real bounded execution seam

### [Task Description]

Remove the current placeholder simulation behavior from the worker path and replace it with a trustworthy execution seam for real domain logic.

### [Task technical implementation]

The current default worker logic is placeholder-level. Milestone D must replace that with one explicit execution design:

- a pluggable worker execution adapter,
- a local reference executor,
- and one concurrency-safe supported domain slice.

The first supported slice should be narrow and deterministic, such as:

- movement,
- simple interaction,
- or another low-side-effect action path.

This task must ensure:

1. **Worker execution logic is real**
   - not just readiness decrement,
   - not just dummy updates,
   - not just placeholder result fabrication.

2. **Local reference executor exists**
   - the same supported work kind must have one local reference path used for equivalence proof.

3. **Unsupported work kinds stay local**
   - combat, rich AI, inventory chains, or other complex work must stay local until explicitly declared concurrency-safe.

4. **Execution seam is extensible without semantic drift**
   - new supported work kinds can be added later without changing packet/result/apply law.

### [Task possible affected files]

- `src/engine/worker_manager.py`
- `src/engine/kernel.py`
- `src/core/work.py`
- supported domain execution modules
- local reference executor modules

### [Task important notes]

Do not try to attach the whole RPG here.
Attach one thin concurrency-safe slice and prove it.

### [Task check list]

- [ ] Remove placeholder worker semantics from supported path
- [ ] Add local reference executor
- [ ] Add one real concurrency-safe work slice
- [ ] Route unsupported work kinds to local mode
- [ ] Add worker/local execution parity tests
- [ ] Keep extension boundary clean
- [ ] Document supported concurrent work scope

### [Task acceptance criteria]

The worker path executes at least one real bounded domain slice and is no longer placeholder-only for the supported concurrency path.

---

## [ ] (checkbox) - [Task 5] - Freeze deterministic authoritative commit order under concurrent completion

### [Task Description]

Ensure race timing never becomes authoritative truth.

### [Task technical implementation]

Define and implement exact commit ordering rules for applying concurrent results, independent of future completion timing.

This must cover:

- batch ordering,
- entity ordering,
- work-class ordering,
- tie-break rules,
- no-op result placement,
- invalid result handling,
- and fallback-substituted result ordering.

Then ensure:

1. **Result collection order is not authoritative**
   - completion race order must not decide commit order.

2. **Commit order is deterministic**
   - same selected work set -> same authoritative apply order.

3. **Fallback preserves order**
   - if a worker fails and local fallback is used, the resulting authoritative order must still match the declared contract.

4. **Partial batch behavior is explicit**
   - valid results may commit only under declared conditions,
   - missing or invalid results must not silently shift law.

### [Task possible affected files]

- `src/engine/kernel.py`
- `src/engine/apply.py`
- `src/engine/worker_manager.py`
- concurrency ordering tests

### [Task important notes]

Do not rely on executor future collection order as proof.
Do not let race timing leak through “stable enough in practice” behavior.

### [Task check list]

- [ ] Freeze concurrent commit-order law
- [ ] Decouple commit order from completion order
- [ ] Freeze fallback result placement
- [ ] Freeze partial-batch handling
- [ ] Add authoritative ordering tests under race conditions
- [ ] Add repeated-run determinism tests
- [ ] Document concurrent commit law

### [Task acceptance criteria]

Authoritative commit order under concurrency is deterministic and independent of worker completion timing.

---

## [ ] (checkbox) - [Task 6] - Harden worker-manager boundedness, submission control, and inflight limits

### [Task Description]

Turn worker execution from “thread pool usage” into a profile-bounded runtime contract.

### [Task technical implementation]

Define and enforce exact worker-manager laws for:

- max workers,
- max inflight items,
- max queued submissions,
- submission rejection behavior,
- wait behavior,
- timeout behavior,
- shutdown behavior,
- and fallback behavior under saturation.

This task must explicitly distinguish:

- work selected by scheduler,
- work submitted to worker manager,
- work accepted by worker manager,
- inflight work,
- completed work,
- timed-out work,
- rejected work,
- and fallback-executed work.

Also define bounded submission policy:

- block within limit,
- reject,
- fallback immediately,
- or queue within declared capacity.

### [Task possible affected files]

- `src/engine/worker_manager.py`
- `src/config/profiles.py`
- `src/observability/runtime_status.py`
- worker-manager tests

### [Task important notes]

Do not let worker-manager pressure become a hidden queue outside runtime law.
If inflight work is bounded, prove it.

### [Task check list]

- [ ] Freeze max inflight and queue rules
- [ ] Freeze submission acceptance/rejection rules
- [ ] Freeze worker timeout handling
- [ ] Freeze saturation fallback behavior
- [ ] Surface accepted/rejected/inflight counters
- [ ] Add boundedness tests
- [ ] Document worker-manager law

### [Task acceptance criteria]

Worker execution is fully bounded by profile with explicit submission, inflight, saturation, and timeout behavior.

---

## [ ] (checkbox) - [Task 7] - Complete explicit worker failure, timeout, and fallback semantics

### [Task Description]

Define the exact meaning of concurrent execution failure and make recovery behavior safe and visible.

### [Task technical implementation]

Create one explicit worker failure taxonomy covering:

- submission rejection,
- worker startup failure,
- worker runtime exception,
- invalid result,
- worker timeout,
- batch partial completion,
- cancelled result,
- fallback success,
- fallback failure.

For each class, define:

- severity,
- whether local fallback is allowed,
- whether the tick may continue,
- whether the work is retried,
- whether the work is dropped,
- whether authoritative semantics remain intact,
- and what counters/status fields are updated.

Then implement:

- structured classification,
- bounded retry or no-retry policy,
- fallback routing,
- and exact visibility in runtime status.

### [Task possible affected files]

- `src/engine/worker_manager.py`
- `src/observability/runtime_status.py`
- `src/governance/governor.py` if concurrency pressure affects mode
- concurrency failure tests

### [Task important notes]

Do not swallow worker failures into generic logs.
Do not treat fallback as a generic success without recording the failure that caused it.

### [Task check list]

- [ ] Define failure classes
- [ ] Define timeout semantics
- [ ] Define fallback eligibility rules
- [ ] Define retry/no-retry law
- [ ] Surface failure and fallback counters
- [ ] Add worker fault-injection tests
- [ ] Document failure/fallback law

### [Task acceptance criteria]

Worker failure and fallback behavior are explicit, bounded, and operationally visible without corrupting authoritative semantics.

---

## [ ] (checkbox) - [Task 8] - Prove local-vs-concurrent authoritative equivalence for supported work

### [Task Description]

Make equivalence a proven contract instead of a slogan.

### [Task technical implementation]

Define the supported equivalence set:

- which work kinds,
- which action types,
- which runtime modes,
- which profile constraints,
- and which failure-free conditions
  must produce equivalent authoritative results between local and concurrent execution.

Then add direct equivalence proof for:

- same input state,
- same selected work set,
- same seed,
- same profile,
- same supported work mode,
- local execution vs concurrent execution,
- repeated runs.

Use authoritative checkpoint/hash comparison where appropriate, plus explicit state assertions where narrower proof is better.

Also define non-equivalence boundaries:

- unsupported work kinds,
- known local-only systems,
- degraded fallback cases,
- partial-success concurrency cases.

### [Task possible affected files]

- `tests/engine/test_worker_local_equivalence.py`
- `tests/engine/test_determinism_suite.py`
- `src/engine/checkpoint.py`
- supported concurrent domain tests

### [Task important notes]

Do not overclaim equivalence.
Prove it only for the supported concurrency-safe slice.

### [Task check list]

- [ ] Freeze supported equivalence scope
- [ ] Add local-vs-concurrent state equivalence tests
- [ ] Add repeated-run equivalence tests
- [ ] Add hash-based equivalence where appropriate
- [ ] Define non-equivalence boundaries explicitly
- [ ] Document equivalence law

### [Task acceptance criteria]

The supported concurrent work slice is directly proven equivalent to the local baseline under declared conditions.

---

## [ ] (checkbox) - [Task 9] - Integrate concurrency truth into runtime signals and status

### [Task Description]

Make concurrent execution operationally visible so pressure, fallback, and failure do not stay hidden.

### [Task technical implementation]

Extend runtime status and signal collection to surface at least:

- active workers,
- inflight count,
- accepted submissions,
- rejected submissions,
- timed-out work count,
- worker failure count,
- fallback count,
- local fallback load,
- batch completion ratio,
- unsupported-work-local-routing count,
- and any concurrency pressure signal that affects policy.

For each field, define:

- source,
- update cadence,
- cumulative vs instant vs rolling nature,
- reset behavior,
- and whether it is policy-relevant or monitoring-only.

If concurrency pressure affects governor behavior, define exactly how that signal enters Milestone B law without blending it ambiguously into other signals.

### [Task possible affected files]

- `src/observability/runtime_status.py`
- `src/observability/signals.py`
- `src/engine/worker_manager.py`
- `src/governance/governor.py`
- observability tests

### [Task important notes]

Do not add a vanity dashboard.
Surface the few concurrency facts the engine actually needs to tell the truth.

### [Task check list]

- [ ] Freeze concurrency status field set
- [ ] Define source/cadence/reset for each field
- [ ] Surface fallback and failure counters
- [ ] Surface inflight/accepted/rejected counts
- [ ] Add concurrency-status truth tests
- [ ] Document concurrency observability law

### [Task acceptance criteria]

The engine exposes one truthful concurrency-status surface suitable for runtime control, debugging, and headless testing.

---

## [ ] (checkbox) - [Task 10] - Complete concurrency-focused headless and system-level test coverage

### [Task Description]

Make concurrent execution provable at full-system and part-system levels, not just unit-test level.

### [Task technical implementation]

Add headless and system-level tests covering:

### Packet/result contract tests

- supported work kinds build valid packets,
- unsupported work kinds are rejected or routed local,
- result validation rejects malformed outputs.

### Ordering and determinism tests

- race timing does not change authoritative order,
- repeated concurrent runs remain equivalent under supported conditions,
- mixed success/fallback batches preserve declared order.

### Worker fault-injection tests

- submit failure,
- worker exception,
- worker timeout,
- invalid result,
- partial batch completion,
- fallback success,
- fallback failure classification.

### Boundedness tests

- inflight limits enforced,
- queue/submission limits enforced,
- fallback does not explode unboundedly,
- worker shutdown remains bounded.

### Headless/system tests

- full headless tick loop with concurrent supported slice,
- local baseline vs concurrent headless equivalence,
- concurrency under profile pressure,
- concurrency with lifecycle interactions where relevant.

### Suggested test groups

- `tests/concurrency/test_packet_contract.py`
- `tests/concurrency/test_result_contract.py`
- `tests/concurrency/test_commit_order.py`
- `tests/concurrency/test_worker_failures.py`
- `tests/concurrency/test_worker_timeouts.py`
- `tests/concurrency/test_fallback_semantics.py`
- `tests/concurrency/test_inflight_bounds.py`
- `tests/concurrency/test_headless_concurrent_loop.py`
- `tests/concurrency/test_local_vs_concurrent_equivalence.py`

### [Task possible affected files]

- new concurrency and headless test modules
- existing engine tests

### [Task important notes]

Do not rely on certification tests as a substitute.
Milestone D needs direct concurrency law proof.

### [Task check list]

- [ ] Add packet/result contract tests
- [ ] Add race-order determinism tests
- [ ] Add worker fault-injection tests
- [ ] Add timeout/fallback tests
- [ ] Add boundedness tests
- [ ] Add headless concurrent loop tests
- [ ] Add local-vs-concurrent equivalence tests

### [Task acceptance criteria]

The concurrency layer is pinned by a complete direct proof suite covering contract, boundedness, failure, fallback, and equivalence.

---

## [ ] (checkbox) - [Task 11] - Refactor concurrency responsibilities into clean execution boundaries

### [Task Description]

Remove concurrency responsibility leakage so worker execution stays understandable and trustworthy.

### [Task technical implementation]

Refactor the concurrent execution path so that:

- scheduler selects work only,
- packet builder constructs worker inputs,
- worker executor runs declared transient logic,
- result validator/classifier validates outputs,
- apply path remains the sole authoritative mutator,
- worker manager owns bounded execution control,
- runtime status reports concurrency truth,
- kernel orchestrates without hiding worker semantics.

Ensure that:

- worker code does not mutate authoritative state directly,
- packet construction does not secretly perform policy logic,
- result validation does not secretly apply updates,
- runtime status does not recompute execution logic,
- and kernel does not absorb worker-manager detail.

### [Task possible affected files]

- `src/engine/kernel.py`
- `src/engine/worker_manager.py`
- `src/engine/apply.py`
- `src/core/work.py`
- `src/core/updates.py`

### [Task important notes]

Do not over-engineer this into a framework.
Just stop execution responsibilities from leaking across modules.

### [Task check list]

- [ ] Audit concurrency responsibility boundaries
- [ ] Separate packet build / execute / validate / apply roles
- [ ] Keep authoritative mutation isolated
- [ ] Keep runtime-status reporting read-only
- [ ] Preserve deterministic behavior during refactor
- [ ] Document final execution boundaries

### [Task acceptance criteria]

Milestone D ends with one clean bounded-concurrency architecture rather than scattered worker logic.

---

## [ ] (checkbox) - [Task 12] - Add exact Milestone D documentation pack

### [Task Description]

Document the finished concurrency law so later milestones treat Milestone D as completed execution law rather than evolving implementation detail.

### [Task technical implementation]

Create:

- `docs/engine/bounded_concurrency_contract_md.md`
- `docs/engine/md_test_matrix.md`

`bounded_concurrency_contract_md.md` must contain these exact sections:

- Purpose
- Scope of Milestone D
- Single-process baseline relationship
- Supported concurrent work scope
- Worker packet law
- Worker result law
- Authoritative commit-order law
- Worker boundedness law
- Failure, timeout, and fallback law
- Local-vs-concurrent equivalence law
- Concurrency status surface
- Authoritative vs non-authoritative separation
- Non-goals
- Completion guarantees

`md_test_matrix.md` must contain these exact sections:

- Packet contract tests
- Result contract tests
- Commit-order and determinism tests
- Worker failure and timeout tests
- Fallback semantics tests
- Boundedness tests
- Local-vs-concurrent equivalence tests
- Headless concurrent loop tests
- Regression intent

For every test group, document:

- test name or group,
- input condition,
- exact concurrency rule,
- regression caught,
- whether it is contract, ordering, failure, boundedness, or equivalence coverage.

### [Task possible affected files]

- `docs/engine/bounded_concurrency_contract_md.md`
- `docs/engine/md_test_matrix.md`

### [Task important notes]

Documentation is implementation here too.
Do not finish Milestone D with only code and passing tests.

### [Task check list]

- [ ] Document packet law
- [ ] Document result law
- [ ] Document commit-order law
- [ ] Document failure/fallback law
- [ ] Document boundedness law
- [ ] Document equivalence law
- [ ] Document concurrency status surface
- [ ] Document exact test matrix

### [Task acceptance criteria]

Milestone D has a complete documentation pack describing the finished bounded concurrency law and its proof matrix.

---

## [ ] (checkbox) - [Task 13] - Add Milestone D regression guardrails

### [Task Description]

Make it hard for concurrency trust to silently decay after Milestone D is declared complete.

### [Task technical implementation]

Add project-level guardrails that fail if:

- placeholder worker semantics return to the supported concurrent path,
- commit order starts depending on completion timing,
- packet or result contract drifts without doc/test updates,
- inflight or submission bounds are removed,
- worker failures stop being surfaced,
- fallback stops being counted,
- local-vs-concurrent equivalence coverage disappears,
- or concurrency state begins contaminating authoritative hash.

This can be done with:

- doc-integrity tests,
- focused concurrency CI targets,
- boundedness regression tests,
- contract-consistency tests for packet/result models,
- and placeholder guards for supported worker execution modules.

### [Task possible affected files]

- `tests/docs/*`
- `tests/concurrency/test_md_doc_integrity.py`
- CI config
- integrity helpers

### [Task important notes]

Do not create ceremony.
Just make concurrency regression visible and cheap.

### [Task check list]

- [ ] Add concurrency doc/test integrity checks
- [ ] Add focused concurrency CI target
- [ ] Add commit-order regression guard
- [ ] Add boundedness regression guard
- [ ] Add equivalence-coverage regression guard
- [ ] Record Milestone D completion gate

### [Task acceptance criteria]

Milestone D cannot silently regress without failing tests or integrity checks.

---

# [Recommended execution order inside Milestone D]

1. Task 1 — Freeze the concurrency law set
2. Task 2 — Harden the packet contract
3. Task 3 — Harden the result contract
4. Task 4 — Replace placeholder worker execution with a real supported slice
5. Task 5 — Freeze deterministic commit order
6. Task 6 — Harden worker-manager boundedness
7. Task 7 — Complete failure, timeout, and fallback law
8. Task 8 — Prove local-vs-concurrent equivalence
9. Task 9 — Integrate concurrency truth into runtime status
10. Task 10 — Complete concurrency test coverage
11. Task 11 — Refactor concurrency boundaries
12. Task 12 — Finalize docs
13. Task 13 — Add guardrails

This order matters because it follows dependency reality:

- first define the concurrency law,
- then define inputs and outputs,
- then replace fake execution with one real slice,
- then lock commit semantics,
- then bound execution control,
- then define failure and fallback meaning,
- then prove equivalence,
- then surface runtime truth,
- then finish direct proof,
- then clean structure,
- then lock docs and guardrails.

---

# [Milestone D done-means-done gate]

Milestone D is done only when all of these are true:

- the local path remains the semantic source of truth,
- the supported concurrent path is no longer placeholder-only,
- worker packets and results have exact bounded contracts,
- authoritative commit order is independent of race timing,
- worker-manager inflight and submission behavior are profile-bounded,
- failure, timeout, and fallback behavior are explicit,
- fallback is visible and bounded,
- supported local-vs-concurrent equivalence is directly proven,
- concurrency status fields are truthful,
- docs and tests describe the same concurrency law,
- and CI can catch concurrency contract regression.
