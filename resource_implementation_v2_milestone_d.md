[Milestone D] - Bounded Concurrency That Can Be Trusted

[Milestone Description]
Milestone D is the fourth v2 completion milestone. Its purpose is **not** to introduce concurrency for the first time. Its purpose is to move concurrency from bounded prototype to trustworthy execution mode.

The current code already has:

- worker packets,
- worker results,
- a bounded worker manager,
- a queue/inflight boundary,
- local fallback behavior,
- and local-vs-concurrent equivalence intent.

That means the concurrency architecture exists. The problem is that the contracts are still too thin:

- worker packet structure is underspecified,
- worker result identity is underspecified,
- deterministic commit order is too dependent on thin assumptions,
- failure semantics are incomplete,
- and fallback behavior is still not fully proven as part of the same authoritative commit law.

This milestone exists to fix that.

[Milestone technical implementation]
Create one fully trustworthy bounded concurrency model and make local and concurrent execution match exactly at the authoritative commit boundary.

This milestone must implement these exact rules:

### Concurrency completion rules

1. **Worker packets must be explicit and bounded**
   - A packet contains only the exact state required for the work item.
   - Context ordering is deterministic.
   - Packet identity is explicit.
   - Packet scope is bounded and lawful.

2. **Worker results must be explicit and safe to commit**
   - Result identity is explicit.
   - Commit ordering is explicit.
   - Result multiplicity rules are explicit.
   - Failure and invalid-result semantics are explicit.

3. **Authoritative equivalence is the law**
   - Local and concurrent execution must produce the same authoritative result under supported conditions.
   - The law is authoritative-equivalent at commit, not “bit-identical internal execution.”

4. **Commit order must be frozen**
   - If one-result-per-entity-per-tick is the rule, it must be frozen and tested.
   - If richer multiplicity is allowed, commit ordering must reflect a richer explicit identity than `entity_id` alone.
   - Sorting by convenience is forbidden.

5. **Fallback must remain part of the same law**
   - Local fallback under saturation or worker failure must join the same deterministic commit path.
   - Fallback must not create alternate authoritative semantics.

6. **Concurrency remains bounded**
   - Worker count remains bounded.
   - Inflight remains bounded.
   - Queue depth remains bounded.
   - Overflow behavior remains explicit.
   - Worker metrics remain real and surfaced.

### Runtime contract boundaries

7. **What this milestone must cover**
   - This milestone must complete:
     - worker packet contract,
     - worker result contract,
     - deterministic commit law,
     - worker failure semantics,
     - fallback law,
     - queue/inflight enforcement,
     - and real worker pressure surfacing.

8. **Non-goals of this milestone**
   - Do not redesign the single-process kernel here.
   - Do not redesign replay lifecycle here.
   - Do not deepen certification scenario richness here.
   - Do not add distributed fleet orchestration or external brokers here.

9. **Clean-code boundary**

- Packet construction, worker execution, worker result validation, commit ordering, fallback behavior, and queue/inflight enforcement must remain separated into explicit responsibilities.
- Do not let the kernel become the hidden home of concurrency policy.
- Do not let packet convenience override boundedness discipline.

[Milestone important notes]
The first trap in this milestone is thinking bounded queue depth equals trustworthy concurrency. It does not. If result identity and commit law are weak, the engine is still unsafe.

The second trap is confusing deterministic internal execution with deterministic authoritative equivalence. Completion order can vary. Commit law cannot.

The third trap is relying on `entity_id` sorting without freezing the one-result-per-entity rule. That is an underspecified promise waiting to break.

The fourth trap is treating fallback as a separate emergency path. Fallback must be semantically identical at the commit boundary or it is an alternate engine.

[Milestone acceptance criteria]
At the end of Milestone D, the codebase has:

- one fully explicit worker packet contract,
- one fully explicit worker result contract,
- one fully frozen deterministic commit law,
- one fully explicit fallback-to-local law,
- one fully bounded worker pressure model,
- and one deterministic test suite proving local/concurrent authoritative equivalence.

No distributed topology, broker integration, or new gameplay semantics are required for Milestone D completion.

## Task

[ ] (checkbox) - [Task 1] - Audit and freeze the bounded concurrency contract

[Task Description]
Create the exact completion contract for worker packets, worker results, commit ordering, fallback, and bounded execution. This task turns the current concurrency prototype into one finished law set.

[Task technical implementation]
Create one new bounded-concurrency contract document and one code-facing contract section that define exactly:

### Worker packet contract

- required fields,
- forbidden fields,
- bounded context rules,
- deterministic context ordering,
- packet identity rules.

### Worker result contract

- required fields,
- deterministic result identity,
- allowed multiplicity,
- commit-order inputs,
- failure/error result behavior.

### Concurrency-bound contract

- max worker count,
- max inflight count,
- max queue depth,
- overflow behavior,
- fallback law.

### Non-goals

- no distributed topology,
- no external broker,
- no certification deepening,
- no gameplay changes.

[Task possible affected files]

- `docs/engine/bounded_concurrency_contract_md.md`
- `docs/engine/md_test_matrix.md`
- code-facing concurrency contract notes near worker modules

[Task important notes]
Do not leave one-result-per-entity as an assumption.

Do not leave packet context ordering implicit.

[Task check list]

- [ ] Freeze worker packet law
- [ ] Freeze worker result law
- [ ] Freeze commit-order law
- [ ] Freeze fallback law
- [ ] Freeze queue/inflight bound law
- [ ] Define explicit non-goals

[Task acceptance criteria]
The project has one exact bounded-concurrency contract that defines the finished law set for packets, results, commit ordering, fallback, and bounds.

---

[ ] (checkbox) - [Task 2] - Harden worker packet/result contracts and deterministic commit ordering

[Task Description]
Make the worker protocol exact and make authoritative commit behavior independent of thin hidden assumptions.

[Task technical implementation]
Complete and harden:

1. **Worker packets**
   - add explicit packet identity,
   - add explicit work identity/kind,
   - freeze deterministic neighbor/context ordering,
   - freeze exact bounded context scope.

2. **Worker results**
   - add explicit result identity,
   - add explicit relation to packet/work identity,
   - define error/failure result handling where relevant,
   - define whether multiple results per entity per tick are allowed.

3. **Commit law**
   - if one-result-per-entity-per-tick is retained, freeze and test it,
   - otherwise introduce richer deterministic commit keys,
   - commit ordering must remain explicit and test-pinned.

[Task possible affected files]

- `src_v2/core/worker_protocol.py`
- `src_v2/engine/worker_manager.py`
- `src_v2/engine/kernel.py`
- apply/commit integration modules

[Task important notes]
Do not continue relying on `entity_id` sorting alone unless the law is frozen and proved.

Do not let packet context shape remain implementation detail.

[Task check list]

- [ ] Add explicit packet identity
- [ ] Add explicit result identity
- [ ] Freeze deterministic context ordering
- [ ] Freeze one-result-per-entity or richer commit law
- [ ] Harden result validation semantics
- [ ] Document final commit law

[Task acceptance criteria]
Worker packet/result semantics and authoritative commit order are fully explicit, deterministic, and free of hidden assumptions.

---

[ ] (checkbox) - [Task 3] - Harden fallback, failure handling, and bounded execution controls

[Task Description]
Make concurrency safe under saturation and failure rather than only under successful runs.

[Task technical implementation]
Complete and harden:

1. **Fallback-to-local**
   - exact trigger conditions,
   - exact insertion into the same commit law,
   - exact bounded behavior under queue saturation.

2. **Worker failure handling**
   - worker exception behavior,
   - invalid packet/result behavior,
   - task cancellation or timeout behavior if applicable,
   - safe failure semantics without authoritative corruption.

3. **Bounded execution controls**
   - inflight limits,
   - queue depth limits,
   - overflow behavior,
   - worker pressure surfacing.

[Task possible affected files]

- `src_v2/engine/worker_manager.py`
- `src_v2/engine/kernel.py`
- fallback/failure integration points
- runtime signal integration modules

[Task important notes]
Do not allow fallback to become an alternate semantic lane.

Do not leave worker failure as an unstructured exception path.

[Task check list]

- [ ] Freeze fallback trigger law
- [ ] Freeze fallback commit-law integration
- [ ] Freeze worker failure semantics
- [ ] Freeze queue/inflight overflow behavior
- [ ] Surface real worker pressure
- [ ] Document bounded execution controls

[Task acceptance criteria]
Fallback, saturation, and worker failure behavior are exact, bounded, and incapable of altering authoritative semantics.

---

[ ] (checkbox) - [Task 4] - Complete the bounded-concurrency test suite and prove authoritative equivalence

[Task Description]
Close the proof gap in local-vs-concurrent equivalence and bounded worker safety.

[Task technical implementation]
Complete or add exact tests for:

### Packet/result tests

- packet shape and forbidden-field tests,
- deterministic context-order tests,
- result-shape tests,
- result-identity tests.

### Commit-law tests

- one-result-per-entity proof or richer commit-order proof,
- deterministic commit ordering,
- no commit ambiguity under repeated runs.

### Fallback/failure tests

- queue saturation fallback,
- worker failure fallback,
- invalid result handling,
- no alternate semantics under fallback.

### Equivalence tests

- same seed/profile/input => same authoritative checkpoint,
- local-vs-worker equivalence,
- worker-mode deterministic equivalence across repeated runs.

### Suggested test groups

- `tests_v2/engine/test_worker_determinism.py`
- `tests_v2/engine/test_worker_bounds.py`
- `tests_v2/engine/test_worker_fallback.py`
- new packet/result/worker-failure tests

[Task possible affected files]

- existing worker test modules
- any missing new bounded-concurrency tests

[Task important notes]
Do not deepen certification here.

This milestone is about making concurrency itself trustworthy.

[Task check list]

- [ ] Finish packet/result tests
- [ ] Finish commit-law tests
- [ ] Finish fallback tests
- [ ] Finish worker failure tests
- [ ] Finish local-vs-worker equivalence tests
- [ ] Prove bounded worker safety

[Task acceptance criteria]
The bounded-concurrency layer is pinned by a complete deterministic test suite proving packet discipline, commit determinism, safe fallback, and authoritative equivalence.

---

[ ] (checkbox) - [Task 5] - Add exact Milestone D documentation pack

[Task Description]
Document the completed concurrency model so later milestones treat it as finished law instead of a prototype execution path.

[Task technical implementation]
Create:

- `docs/engine/bounded_concurrency_contract_md.md`
- `docs/engine/md_test_matrix.md`

`bounded_concurrency_contract_md.md` must contain these exact sections:

- Purpose
- Scope of Milestone D
- Worker packet law
- Worker result law
- Deterministic commit-order law
- Fallback-to-local law
- Queue/inflight bound law
- Failure-handling law
- Non-goals
- Completion guarantees

`md_test_matrix.md` must contain these exact sections:

- Packet/result tests
- Commit-order tests
- Fallback tests
- Worker failure tests
- Local-vs-worker equivalence tests
- Bound enforcement tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/bounded_concurrency_contract_md.md`
- `docs/engine/md_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not end Milestone D with code and tests only. The concurrency law must be written down exactly.

[Task check list]

- [ ] Document worker packet law
- [ ] Document worker result law
- [ ] Document deterministic commit law
- [ ] Document fallback law
- [ ] Document bounded execution controls
- [ ] Document the exact test matrix

[Task acceptance criteria]
Milestone D has a complete exact documentation pack describing the finished bounded-concurrency model and the tests that freeze it.

---

Priority Plan

What must change in mindset or assumptions
Stop treating bounded concurrency as “basically solved” because there is a worker pool and a fallback path. Trustworthy concurrency requires explicit packet/result law, explicit commit law, and explicit failure semantics.

What actions must be taken immediately
Freeze the bounded-concurrency contract, harden worker packet/result shapes, freeze deterministic commit ordering, make fallback join the same commit law, and close the concurrency proof suite.

What must stop or be eliminated
Stop relying on `entity_id` sorting unless the one-result-per-entity rule is frozen. Stop leaving context ordering implicit. Stop treating worker failure as an incidental exception path. Stop letting fallback become a semantic side route.

The consequences and opportunity cost if this fails
The engine will keep a concurrency layer that looks bounded in happy-path demos but remains underspecified exactly where pressure, multiplicity, and failure make determinism hardest to trust.
