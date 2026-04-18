[Milestone 8] - Safe Concurrency and Bounded Worker Execution

[Milestone Description]
Milestone 8 is the first scale-out milestone of the new engine. Its purpose is **not** to introduce distributed systems infrastructure yet, and it is **not** to build the final certification harness yet. Its purpose is to add concurrency only after the deterministic kernel, bounded state, work model, governor, replay, and operational controls are stable, so concurrency improves throughput within the resource envelope instead of multiplying architectural waste.

This milestone must lock the engine’s first bounded concurrency laws:

- what work can be executed concurrently,
- what a worker receives,
- what a worker returns,
- how inflight work is bounded,
- how queue depth is bounded,
- how fallback to local execution behaves,
- and how deterministic semantics are preserved under the same seed and profile.

The previous milestones froze the kernel, bounded runtime state, defined the scheduler, introduced the governor, made replay bounded, and added operational controls. This milestone turns those foundations into one exact concurrency model that can improve throughput without resurrecting replicated memory blowups or unstable queue growth.

[Milestone technical implementation]
Create one exact bounded worker-execution model and make the runtime obey it.

This milestone must implement these exact rules:

### Worker-execution rules

1. **Compact work packets**
   - Worker execution must use compact bounded work packets.
   - Work packets must contain only the state required for the assigned work.
   - Worker execution must not depend on whole-world clones or giant serialized object graphs.

2. **Bounded inflight work**
   - The number of inflight worker tasks must be exact and profile-controlled.
   - Inflight work must be bounded.
   - Worker execution must not create uncontrolled backlog.

3. **Bounded queue depth**
   - Worker queues must have exact depth limits.
   - Overflow behavior must be explicit.
   - Queue growth must not become an implicit memory expansion path.

4. **Deterministic execution boundaries**
   - Under the same seed, inputs, and runtime profile, authoritative results must remain deterministic.
   - Concurrency must not redefine kernel semantics.
   - Worker execution order may differ internally only if the committed authoritative results remain exactly equivalent under the contract.

5. **Fallback-to-local behavior**
   - If worker execution becomes unavailable, exceeds contract limits, or is disabled by profile, the engine must fall back to local execution according to exact rules.
   - Fallback behavior must remain safe and deterministic.

6. **Profile-aware concurrency**
   - Worker count, queue depth, payload size, and inflight limits must obey the active runtime profile.
   - Concurrency is not a free scaling knob. It is a bounded profile-controlled feature.

### Runtime contract boundaries

7. **What this milestone must cover**
   - This milestone must define:
     - worker packet structure,
     - worker result structure,
     - inflight bounds,
     - queue bounds,
     - fallback behavior,
     - and deterministic equivalence requirements.

8. **Non-goals of this milestone**
   - Do not introduce external brokers here.
   - Do not introduce distributed cluster orchestration here.
   - Do not implement remote worker fleets here.
   - Do not relax deterministic semantics for “best effort” throughput.
   - Do not allow concurrency to rewrite the scheduler contract.

9. **Clean-code boundary**

- Worker packet construction, worker execution, result application, fallback behavior, and queue/inflight control must remain separated into explicit responsibilities.
- Do not bury concurrency control inside scheduler internals.
- Do not let transport convenience define the state model.

[Milestone important notes]
The first trap in this milestone is adding concurrency before payload discipline. If worker packets are not compact and bounded, concurrency will just replicate waste faster.

The second trap is pretending a queue is bounded because you hope it stays small. Exact queue limits and overflow behavior must exist in code.

The third trap is allowing concurrency to drift kernel semantics. If concurrency changes authoritative outcomes, then the engine is no longer trustworthy.

The fourth trap is introducing brokers or distributed plumbing too early. This milestone is about safe bounded local concurrency first, not infrastructure theater.

[Milestone acceptance criteria]
At the end of Milestone 8, the codebase has:

- one exact compact worker-packet model,
- one exact bounded inflight and queue model,
- one exact fallback-to-local model,
- one exact deterministic-equivalence contract for concurrent execution,
- and one deterministic test suite proving concurrency stays within profile limits and preserves authoritative behavior.

No external broker, distributed fleet, or remote orchestration system is required for Milestone 8 completion.

## Task

[ ] (checkbox) - [Task 1] - Define the bounded worker-execution contract

[Task Description]
Create the exact design contract for worker packets, result packets, inflight bounds, queue bounds, deterministic-equivalence requirements, and fallback behavior. This is the foundational modeling task for safe concurrency.

[Task technical implementation]
Create one new worker contract document and one code-facing contract section that define exactly:

### Worker contract

- what state a worker packet may contain,
- what state it must not contain,
- how worker results are represented,
- how results are applied back into authoritative execution,
- and how deterministic equivalence is defined.

### Concurrency-bound contract

- max worker count,
- max inflight work,
- max queue depth,
- max payload size or equivalent bound,
- and fallback-to-local rules.

### Non-goals

- no external broker,
- no cluster orchestration,
- no remote fleet management,
- no best-effort semantic drift,
- no distributed topology design.

[Task possible affected files]

- `docs/engine/worker_contract_m8.md`
- worker contract module
- queue/inflight policy module
- fallback behavior module

[Task important notes]
Do not write this as generic parallelism prose. The contract must be exact enough to drive implementation and tests.

Do not allow any worker packet to remain “open ended.”

[Task check list]

- [ ] Define worker packet semantics
- [ ] Define result packet semantics
- [ ] Define deterministic-equivalence requirements
- [ ] Define inflight bounds
- [ ] Define queue bounds
- [ ] Define fallback-to-local rules
- [ ] Define explicit non-goals

[Task acceptance criteria]
The project has one exact bounded worker-execution contract that can be used as the authoritative source for implementation and tests.

---

[ ] (checkbox) - [Task 2] - Implement compact worker packets and bounded execution controls

[Task Description]
Make the codebase obey the frozen worker contract by implementing one exact bounded worker path with compact payloads and explicit control limits.

[Task technical implementation]
Implement or refactor the concurrency layer so that:

1. **Compact worker packets**
   - include only required actor-local and neighborhood state,
   - exclude unnecessary world-wide or diagnostic state,
   - and remain bounded by declared contract.

2. **Bounded inflight control**
   - enforce exact inflight work limits,
   - enforce exact queue depth limits,
   - reject or defer overflow according to declared behavior.

3. **Bounded worker execution**
   - worker execution remains profile-aware,
   - concurrency does not bypass the governor or scheduler contract,
   - and result application remains separate from worker computation.

[Task possible affected files]

- `src/engine/workers.py`
- worker packet module
- queue/inflight control module
- scheduler integration module
- authoritative apply integration module

[Task important notes]
Do not serialize full world state into worker payloads.

Do not let worker execution directly mutate authoritative state outside the apply path.

[Task check list]

- [ ] Implement compact worker packets
- [ ] Implement bounded inflight control
- [ ] Implement bounded queue control
- [ ] Keep worker execution separate from authoritative apply
- [ ] Keep concurrency profile-aware
- [ ] Avoid whole-world payload leakage

[Task acceptance criteria]
The engine has one exact bounded worker-execution path using compact packets and enforcing exact inflight and queue limits.

---

[ ] (checkbox) - [Task 3] - Implement deterministic fallback-to-local execution

[Task Description]
Ensure the engine remains safe and usable when worker execution is unavailable, constrained, or disabled.

[Task technical implementation]
Implement exact behavior for:

1. **Fallback triggers**
   - worker subsystem unavailable,
   - worker limits exceeded,
   - profile disables worker mode,
   - or equivalent exact contract conditions.

2. **Fallback behavior**
   - work returns to local execution safely,
   - no semantic drift occurs,
   - and fallback remains deterministic.

3. **Recovery boundary**
   - fallback must not create hidden alternate semantics,
   - recovery or re-enable behavior must be explicit if supported in this milestone.

[Task possible affected files]

- fallback execution module
- worker failure-handling module
- scheduler integration module
- runtime mode/profile integration module

[Task important notes]
Do not let fallback logic become a silent catch-all path with different semantics.

Do not make worker failure corrupt authoritative execution ordering.

[Task check list]

- [ ] Implement exact fallback triggers
- [ ] Implement deterministic local fallback behavior
- [ ] Preserve scheduler and apply semantics under fallback
- [ ] Keep fallback profile-aware
- [ ] Define recovery behavior if supported
- [ ] Avoid hidden alternate semantics

[Task acceptance criteria]
Worker failure or disablement leads to deterministic local fallback behavior that preserves authoritative semantics and stays within profile rules.

---

[ ] (checkbox) - [Task 4] - Add deterministic concurrency and bounded-worker tests

[Task Description]
Lock the Milestone 8 concurrency rules with deterministic tests so later milestones cannot silently reintroduce giant payloads, queue blowups, or semantic drift.

[Task technical implementation]
Add exact tests for:

### Worker contract tests

- worker packets contain only allowed bounded state,
- worker results follow declared structure,
- payload limits are enforced.

### Concurrency-bound tests

- inflight limits are enforced,
- queue depth limits are enforced,
- overflow behavior follows declared contract,
- profile constraints are respected.

### Deterministic-equivalence tests

- same seed + same inputs + same profile => same authoritative outcome,
- worker mode and local mode remain equivalent under supported conditions,
- repeated identical runs produce stable authoritative checkpoints.

### Fallback tests

- worker unavailability triggers declared fallback,
- fallback preserves semantics,
- fallback remains profile-aware and deterministic.

### Suggested test groups

- `tests/engine/test_worker_contract.py`
- `tests/engine/test_worker_bounds.py`
- `tests/engine/test_worker_determinism.py`
- `tests/engine/test_worker_fallback.py`

[Task possible affected files]

- new worker contract test modules
- new inflight/queue test modules
- new determinism-equivalence test modules
- new fallback test modules

[Task important notes]
These are safe-concurrency tests, not distributed-system tests and not final certification tests.

Do not add broker transport cases in this milestone.

[Task check list]

- [ ] Add worker-packet bound tests
- [ ] Add inflight-limit tests
- [ ] Add queue-depth tests
- [ ] Add deterministic-equivalence tests
- [ ] Add local-vs-worker equivalence tests
- [ ] Add fallback tests

[Task acceptance criteria]
The bounded worker-execution contract is pinned by deterministic tests proving packet discipline, bound enforcement, equivalence of authoritative outcomes, and safe fallback behavior.

---

[ ] (checkbox) - [Task 5] - Add exact Milestone 8 documentation pack

[Task Description]
Document the complete Milestone 8 bounded concurrency model so later milestones cannot reinterpret worker behavior informally.

[Task technical implementation]
Create:

- `docs/engine/worker_contract_m8.md`
- `docs/engine/m8_worker_bounds_matrix.md`
- `docs/engine/m8_test_matrix.md`

`worker_contract_m8.md` must contain these exact sections:

- Purpose
- Worker scope
- Worker packet semantics
- Result packet semantics
- Deterministic-equivalence rules
- Inflight and queue-bound rules
- Fallback-to-local rules
- Non-goals
- Safety guarantees

`m8_worker_bounds_matrix.md` must contain these exact sections:

- Bound name
- Purpose
- Profile source
- Overflow behavior
- Fallback behavior
- Forbidden behavior
- Regression risk if violated

`m8_test_matrix.md` must contain these exact sections:

- Worker contract tests
- Inflight and queue-bound tests
- Deterministic-equivalence tests
- Fallback tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/worker_contract_m8.md`
- `docs/engine/m8_worker_bounds_matrix.md`
- `docs/engine/m8_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer bounded-concurrency documentation until after certification exists.

[Task check list]

- [ ] Document exact worker rules
- [ ] Document exact inflight and queue bounds
- [ ] Document deterministic-equivalence rules
- [ ] Document fallback rules
- [ ] Document forbidden worker behavior
- [ ] Document the deterministic test matrix

[Task acceptance criteria]
Milestone 8 has a complete exact documentation pack describing bounded worker execution, deterministic equivalence, fallback behavior, and the deterministic test matrix that freezes them.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of concurrency as free performance. Concurrency is only useful if payloads are compact, queues are bounded, and authoritative outcomes remain deterministic.

What actions must be taken immediately
Freeze the worker contract, implement compact packets, enforce exact inflight and queue bounds, define deterministic local fallback, and pin the whole model with deterministic tests.

What must stop or be eliminated
Stop whole-world payload thinking. Stop unbounded queues. Stop best-effort worker semantics. Stop introducing brokers or distributed plumbing before bounded local concurrency is proven safe.

The consequences and opportunity cost if this fails
Later milestones will inherit a concurrency model that amplifies resource waste and semantic ambiguity, and you will waste time debugging queue growth, memory replication, and worker drift that should have been designed out from the start.
