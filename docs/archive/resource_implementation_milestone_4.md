---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

[Milestone 4] - Deterministic Scheduler and Work Model

[Milestone Description]
Milestone 4 is the first execution-shaping milestone of the new engine. Its purpose is **not** to implement resource-pressure response yet, and it is **not** to introduce concurrency yet. Its purpose is to replace naive “scan everything and do everything” execution with one exact, deterministic, explainable work model that preserves kernel semantics while reducing structural waste.

This milestone must lock the engine’s first explicit work-execution laws:

- how ready work is selected,
- how deterministic ordering is preserved,
- how work classes are defined,
- how periodic and deferred work are represented,
- how bounded work debt behaves,
- and how optional work stays subordinate to authoritative execution.

The previous milestones froze the kernel contract, built the minimal single-thread kernel, and bounded the runtime state model. This milestone turns those foundations into one explicit execution model that later milestones can govern, observe, and scale without semantic drift.

[Milestone technical implementation]
Create one exact deterministic scheduler and work-class model and make the runtime obey it.

This milestone must implement these exact rules:

### Work-selection rules

1. **Readiness-aware scheduling**
   - The scheduler must select entity work according to the readiness semantics frozen in Milestone 1 and executed in Milestone 2.
   - The scheduler must not change what “ready to act” means.
   - The scheduler is responsible for selecting due work, not redefining eligibility.

2. **Deterministic ordering**
   - Work selection order must be exact and deterministic.
   - Tie-break behavior must be explicit.
   - The same seed, same inputs, and same runtime profile must produce the same work ordering for authoritative execution.

3. **No broad per-tick waste**
   - The scheduler must not rely on uncontrolled “scan everything and sort everything” behavior as the long-term execution model.
   - This milestone must introduce explicit work representation rather than accidental full-pool processing.

### Work-class rules

4. **Work classes**
   - The engine must explicitly classify work into:
     - critical,
     - periodic,
     - opportunistic,
     - and deferred.

5. **Critical work**
   - Critical work is required to preserve authoritative simulation semantics.
   - Critical work must always execute according to kernel rules.
   - Critical work must not be displaced by optional runtime activity.

6. **Periodic work**
   - Periodic work executes on explicit cadence rules.
   - Cadence must be deterministic and testable.
   - Periodic work must not redefine core tick semantics.

7. **Opportunistic work**
   - Opportunistic work is optional and must never be allowed to alter authoritative semantics.
   - Opportunistic work must remain subordinate to critical work.
   - Opportunistic work may exist only if it has exact execution conditions.

8. **Deferred work**
   - Deferred work represents work intentionally postponed from the current execution window.
   - Deferred work must be bounded.
   - Deferred work must have exact accumulation and drain rules.
   - Deferred work must not become an unbounded shadow backlog.

9. **Bounded work debt**
   - If non-critical work is postponed, the system must represent that debt explicitly.
   - Debt accumulation must be bounded and deterministic.
   - Overflow behavior for deferred work must be exact.

### Runtime contract boundaries

10. **Non-goals of this milestone**

- Do not implement the resource governor here.
- Do not implement degradation modes here.
- Do not implement concurrency here.
- Do not implement replay systems here.
- Do not implement observability systems here beyond what is minimally required to prove scheduler correctness.
- Do not introduce fancy scheduling abstractions that outgrow the current kernel needs.

11. **Clean-code boundary**

- Readiness evaluation, work selection, work classification, deferred debt handling, and authoritative apply must remain separated into distinct responsibilities.
- Do not bury work-priority semantics inside ad hoc control flow.
- Do not let optional work gain implicit authority over tick semantics.

[Milestone important notes]
The first trap in this milestone is trying to solve resource governance too early. This milestone defines deterministic work structure, not pressure response. The governor comes later.

The second trap is using scheduler optimization as an excuse to alter semantics. That is not optimization. That is rule drift.

The third trap is creating a work queue system with vague debt behavior. Deferred work without exact bounds is just a delayed memory leak.

The fourth trap is over-engineering the scheduler before the runtime actually needs it. This milestone must remain exact and lean, not architecture theater.

[Milestone acceptance criteria]
At the end of Milestone 4, the codebase has:

- one exact deterministic scheduler,
- one exact work-class model,
- one exact deferred-work and bounded-debt model,
- one deterministic set of scheduler contract tests,
- and one exact documentation pack stating these rules without ambiguity.

No resource governor, replay system, concurrency model, or degraded-mode behavior is required for Milestone 4 completion.

## Task

[x] (checkbox) - [Task 1] - Define the scheduler and work-class contract

[Task Description]
Create the exact design contract for deterministic work selection and work classification. This is the foundational modeling task for controlled execution.

[Task implementation comments]
Defined the core scheduler contract in `docs/engine/scheduler_contract_m4.md`. The contract introduced the four mandatory work classes (Critical, Periodic, Opportunistic, Deferred) and established how "Work Debt" is formally tracked.

[Task technical implementation]
Create one new scheduler contract document and one code-facing contract section that define exactly:

### Scheduler contract

- what inputs the scheduler consumes,
- how readiness-driven work becomes schedulable,
- how deterministic ordering is defined,
- what tie-break rules exist,
- and how the scheduler hands work to authoritative execution.

### Work-class contract

- critical work,
- periodic work,
- opportunistic work,
- deferred work,
- and bounded work debt semantics.

### Non-goals

- no governor behavior,
- no degradation policy,
- no concurrency scheduling,
- no replay scheduling,
- no advanced fairness heuristics.

[Task possible affected files]

- `docs/engine/scheduler_contract_m4.md`
- scheduler contract module
- work classification module
- deferred work/debt policy module

[Task important notes]
Do not write this as abstract “task management” prose. The contract must be exact enough to generate code and tests from it.

Do not allow any work class to remain informally defined.

[Task check list]

- [x] Define readiness-driven scheduling semantics
- [x] Define deterministic ordering rules
- [x] Define tie-break rules
- [x] Define work classes
- [x] Define bounded work debt semantics
- [x] Define explicit non-goals
- [x] Keep the contract exact and minimal

[Task acceptance criteria]
The project has one exact scheduler and work-class contract that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Implement the deterministic scheduler core

[Task Description]
Make the codebase obey the frozen scheduling contract by implementing one exact deterministic work-selection path.

[Task implementation comments]
Scheduler core implemented in `src/engine/scheduler.py`. It provides a `select_work` method that consumes the `RuntimeStatus` (and its policy) to filter ready work-items in a deterministic, seed-stable order.

[Task technical implementation]
Implement or refactor the scheduler so that:

1. **Ready work selection**
   - selects only work that is due according to readiness and cadence rules,
   - preserves kernel semantics,
   - and does not allow informal direct execution outside scheduler control.

2. **Deterministic ordering**
   - applies exact tie-break rules,
   - yields stable selection order,
   - and produces the same scheduling outcome under repeated identical runs.

3. **Minimal execution shape**
   - remains single-threaded in this milestone,
   - does not embed future concurrency assumptions,
   - and does not mix work selection with authoritative mutation.

[Task possible affected files]

- `src/engine/scheduler.py`
- readiness integration module
- tick execution orchestration module
- work item representation module

[Task important notes]
Do not let the scheduler directly mutate authoritative state.

Do not add clever priority systems that are not required by the frozen contract.

[Task check list]

- [x] Implement ready-work selection
- [x] Implement deterministic ordering
- [x] Implement stable tie-break handling
- [x] Keep the scheduler single-threaded
- [x] Keep selection separate from apply
- [x] Avoid future-milestone leakage

[Task acceptance criteria]
The engine has one exact deterministic scheduler core that selects work correctly and preserves kernel semantics.

---

[x] (checkbox) - [Task 3] - Implement work classes and bounded deferred-work handling

[Task Description]
Represent non-identical work explicitly so the runtime can distinguish mandatory execution from optional and postponed execution.

[Task implementation comments]
Work-class models and debt storage are finalized in `src/core/work.py` and `src/core/state.py`. The kernel tracks `work_debt_total` as an authoritative field, ensuring that deferred work remains bounded and deterministic across world ticks.

[Task technical implementation]
Implement exact representation and handling for:

1. **Critical work**
   - explicit representation,
   - guaranteed execution in accordance with the kernel contract.

2. **Periodic work**
   - explicit cadence representation,
   - deterministic due-evaluation rules.

3. **Opportunistic work**
   - explicit optional representation,
   - no authority over kernel semantics.

4. **Deferred work**
   - explicit deferred-work queue or equivalent structure,
   - exact accumulation rules,
   - exact drain rules,
   - exact bound or retention rules.

5. **Bounded debt**
   - explicit work-debt accounting,
   - exact overflow behavior if debt bound is reached,
   - deterministic handling of postponed work.

[Task possible affected files]

- work item module
- periodic work module
- deferred work queue/debt module
- scheduler integration module

[Task important notes]
Do not let deferred work become an unbounded backlog.

Do not permit optional work to masquerade as critical because it is convenient.

[Task check list]

- [x] Implement critical work representation
- [x] Implement periodic work representation
- [x] Implement opportunistic work representation
- [x] Implement deferred-work representation
- [x] Implement bounded debt accounting
- [x] Implement exact overflow behavior for deferred work
- [x] Preserve deterministic ordering

[Task acceptance criteria]
The engine has explicit work classes and bounded deferred-work handling that preserve authoritative behavior and prevent implicit backlog growth.

---

[x] (checkbox) - [Task 4] - Add deterministic scheduler and work-model tests

[Task Description]
Lock the Milestone 4 execution model with deterministic tests so later milestones cannot silently distort scheduling semantics.

[Task implementation comments]
Scheduler contract tests reside in `tests/engine/test_scheduler_contract.py`. These tests verify that critical work is never deferred and that work item selection order is resilient to input list jitter.

[Task technical implementation]
Add exact tests for the rulebook.

### Scheduler contract tests

Add test coverage for:

- readiness-driven selection,
- deterministic tie-break handling,
- repeated identical input produces identical scheduling order,
- critical work always remains schedulable when due.

### Work-class tests

Add test coverage for:

- periodic cadence correctness,
- opportunistic work remaining non-authoritative,
- deferred-work accumulation rules,
- deferred-work drain rules,
- bounded work debt behavior,
- deferred-work overflow behavior.

### Suggested test groups

- `tests/engine/test_scheduler_contract.py`
- `tests/engine/test_work_classes.py`
- `tests/engine/test_deferred_work_debt.py`

[Task possible affected files]

- new scheduler contract test modules
- new work-class test modules
- new deferred-work and debt test modules

[Task important notes]
These are scheduler and work-model tests, not governor tests and not concurrency tests.

Do not add profile-pressure or degraded-mode scenarios in this milestone.

[Task check list]

- [x] Add ready-work selection tests
- [x] Add deterministic ordering tests
- [x] Add tie-break tests
- [x] Add periodic cadence tests
- [x] Add opportunistic-work boundary tests
- [x] Add deferred-work accumulation tests
- [x] Add bounded debt overflow tests

[Task acceptance criteria]
The scheduler and work-model contracts are pinned by deterministic tests proving correct selection, correct ordering, correct work classification, and correct bounded deferred-work behavior.

---

[x] (checkbox) - [Task 5] - Add exact Milestone 4 documentation pack

[Task Description]
Document the complete Milestone 4 execution model so later milestones cannot reinterpret scheduling and work semantics informally.

[Task implementation comments]
Finalized the Scheduler Contract documentation. Verified it correctly describes the "Work Debt" semantics now used by the Resource Governor in Milestone 5.

[Task technical implementation]
Create:

- `docs/engine/scheduler_contract_m4.md`
- `docs/engine/m4_work_model_matrix.md`
- `docs/engine/m4_test_matrix.md`

`scheduler_contract_m4.md` must contain these exact sections:

- Purpose
- Scheduler scope
- Readiness-driven selection semantics
- Deterministic ordering semantics
- Tie-break rules
- Hand-off to authoritative execution
- Non-goals
- Determinism guarantees

`m4_work_model_matrix.md` must contain these exact sections:

- Work class name
- Purpose
- Authoritative vs non-authoritative status
- Due rules
- Execution guarantees
- Deferral rules
- Bound/debt rules
- Overflow behavior
- Regression risk if violated

`m4_test_matrix.md` must contain these exact sections:

- Scheduler contract tests
- Deterministic ordering tests
- Work-class tests
- Deferred-work and debt tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/scheduler_contract_m4.md`
- `docs/engine/m4_work_model_matrix.md`
- `docs/engine/m4_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer work-model documentation until after the governor exists.

[Task check list]

- [x] Document exact scheduler rules
- [x] Document exact ordering and tie-break rules
- [x] Document exact work-class semantics
- [x] Document deferred-work and debt rules
- [x] Document exact non-goals
- [x] Document the deterministic test matrix

[Task acceptance criteria]
Milestone 4 has a complete exact documentation pack describing deterministic scheduling, work classes, deferred-work behavior, and the deterministic test matrix that freezes them.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of the scheduler as an optimization accessory. It is part of the engine’s law. If work selection is vague, later resource controls and concurrency will only amplify the ambiguity.

What actions must be taken immediately
Freeze the scheduler contract, implement the deterministic scheduler core, define explicit work classes, bound deferred work and debt, and pin the whole model with deterministic tests.

What must stop or be eliminated
Stop broad uncontrolled per-tick work selection. Stop vague optional-work behavior. Stop deferred work without explicit bounds. Stop burying execution priority in incidental control flow.

The consequences and opportunity cost if this fails
Later milestones will be built on unstable execution semantics, and you will waste time blaming the governor, replay, or concurrency for problems caused by a scheduler whose rules were never truly frozen.
