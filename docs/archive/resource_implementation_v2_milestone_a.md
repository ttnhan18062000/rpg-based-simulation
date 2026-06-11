---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

[Milestone A] - Core Runtime Completion and Contract Closure

[Milestone Description]
Milestone A is the first v2 completion milestone. Its purpose is **not** to add new engine capability. Its purpose is to finish the deterministic single-process core so the runtime stops being “architecturally correct but partially real.”

The current code already has:

- authoritative state,
- deterministic apply path,
- scheduler and work classes,
- checkpoint hashing,
- bounded state structures,
- and a runnable kernel.

That means the problem is no longer absence of architecture. The problem is incomplete closure:

- unfinished law tests still exist,
- some ordering and mutation guarantees are too lightly proven,
- kernel orchestration is carrying too much milestone-compressed responsibility,
- and the single-process execution path is not yet hardened enough to serve as the unquestioned semantic baseline for later governor, replay, worker, and certification work.

This milestone exists to fix that.

[Milestone technical implementation]
Create one fully trustworthy deterministic single-process runtime baseline and make the codebase obey it.

This milestone must implement these exact rules:

### Core runtime completion rules

1. **Single-process path is the semantic source of truth**
   - The local single-process path is the authoritative baseline for:
     - deterministic checkpoints,
     - work ordering,
     - apply semantics,
     - and later concurrency equivalence.

   - No later mode may redefine its semantics.

2. **Kernel orchestration must become exact**
   - Tick execution order must be explicit, stable, and fully proven.
   - Kernel phases must not hide placeholder behavior.
   - Every core phase must have exact ownership and exact outputs.

3. **Authoritative mutation must remain singular**
   - All authoritative state changes must still flow through the apply path.
   - No helper, scheduler, replay hook, or observability path may mutate authoritative state directly.
   - Any existing shortcuts or implicit mutations must be removed.

4. **Deterministic work ordering must be fully frozen**
   - Critical, periodic, and deferred work ordering must be exact.
   - Tie-break rules must be explicit.
   - No unfinished or assumed ordering law may remain.

5. **Checkpoint determinism must be fully trustworthy**
   - Canonical checkpoint generation must include only authoritative state.
   - Ordering of authoritative structures must be deterministic.
   - Same seed + same inputs + same profile + same single-process mode must produce the same checkpoint hash.

6. **No hidden semantic placeholders**
   - Placeholder tests in core runtime law are forbidden after this milestone.
   - Placeholder kernel semantics are forbidden after this milestone.
   - If a law exists, it must either be implemented and tested or explicitly removed from scope.

### Runtime contract boundaries

7. **What this milestone must cover**
   - This milestone must complete:
     - kernel phase execution,
     - apply-path proof,
     - deterministic work ordering,
     - checkpoint proof,
     - authoritative/non-authoritative mutation boundaries,
     - and core-law test closure.

8. **Non-goals of this milestone**
   - Do not deepen replay behavior here.
   - Do not harden real runtime signals here.
   - Do not add new governor features here.
   - Do not deepen worker execution here.
   - Do not deepen certification harness behavior here.
   - Do not add new gameplay semantics here.

9. **Clean-code boundary**

- Kernel orchestration, work selection, authoritative apply, checkpointing, and observational side channels must remain separated into explicit responsibilities.
- Do not let the kernel continue accumulating cross-milestone responsibilities that belong in replay, observability, or concurrency layers.
- Do not let “temporary” glue become core runtime law.

[Milestone important notes]
The first trap in this milestone is pretending the current kernel is “good enough” because the architecture shape exists. That is how unfinished law tests and weakly proven ordering survive into every later subsystem.

The second trap is using Milestone A to redesign everything. This milestone is not a rewrite. It is closure. Finish what already exists, remove ambiguity, and make the core trustworthy.

The third trap is allowing the single-process path to remain underspecified while calling worker mode equivalent. Concurrency can only be certified against a baseline that is fully pinned.

The fourth trap is tolerating placeholders because “the later milestones will cover them.” Later milestones only get more complicated. Unfinished core law becomes compound debt.

[Milestone acceptance criteria]
At the end of Milestone A, the codebase has:

- one fully trustworthy deterministic single-process runtime path,
- one fully closed authoritative apply contract,
- one fully frozen work-order contract,
- one fully trustworthy canonical checkpoint contract,
- one complete deterministic core-law test suite with no placeholders,
- and one exact documentation pack stating these rules without ambiguity.

No replay hardening, signal realism, concurrency deepening, or certification expansion is required for Milestone A completion.

## Task

[x] (checkbox) - [Task 1] - Audit and freeze the core runtime law set

[Task Description]
Create the exact completion contract for the existing single-process kernel path. This task turns the current partial runtime shape into one explicit finished law set.

[Task technical implementation]
Create one new runtime-completion contract document and one code-facing contract section that define exactly:

### Kernel completion contract

- exact tick execution order,
- exact phase ownership,
- exact authoritative apply boundary,
- exact work-order rules,
- exact checkpoint-generation rules,
- and exact prohibition of core placeholders.

### Determinism contract

- same seed + same inputs + same single-process profile => same checkpoint,
- canonical ordering of all authoritative collections,
- no observational field may influence hash generation.

### Non-goals

- no replay deepening,
- no worker behavior deepening,
- no governor-signal deepening,
- no certification expansion.

[Task possible affected files]

- `docs/engine/runtime_completion_contract_ma.md`
- `docs/engine/ma_test_matrix.md`
- kernel contract docs
- code-facing contract notes near kernel/apply/checkpoint modules

[Task important notes]
Do not restate earlier milestone docs as history. This document must define the closure target for the actual implemented runtime.

Do not leave unfinished laws in a “known issue” state.

[Task check list]

- [x] Freeze exact tick execution law
- [x] Freeze exact phase ownership
- [x] Freeze exact apply-path law
- [x] Freeze exact work-order law
- [x] Freeze exact checkpoint law
- [x] Freeze no-placeholder rule for core runtime
- [x] Define explicit non-goals

[Implementation Comment]
Milestone A is fully closed. The Core Runtime Contract (MA) was published in `docs/engine/runtime_completion_contract_ma.md`, defining the 6-phase sequence and deterministic apply boundaries.

[Task acceptance criteria]
The project has one exact runtime-completion contract that defines the finished law set for the deterministic single-process core.

---

[x] (checkbox) - [Task 2] - Complete the authoritative apply path and remove implicit mutation risks

[Task Description]
Make the authoritative apply path fully finished and fully singular so no core mutation rule remains implicit.

[Task technical implementation]
Review and harden the apply implementation so that:

1. **All authoritative changes go through one path**
   - entity updates,
   - resource updates,
   - periodic updates,
   - work-debt updates,
   - and RNG checkpoint updates remain centrally applied.

2. **Deterministic application is fully explicit**
   - entity update ordering is frozen,
   - resource key ordering is frozen,
   - periodic update ordering is frozen,
   - and any remaining ambiguous ordering is removed.

3. **No helper mutation remains**
   - no scheduler helper,
   - no kernel shortcut,
   - no observability hook,
   - and no replay hook may directly mutate authoritative state.

4. **State generation remains minimal**
   - immutable generation-based transitions remain the law,
   - but rebuilding must remain limited to changed or explicitly copied structures,
   - and no hidden whole-state deep-clone convenience must creep in.

[Task possible affected files]

- `src/engine/apply.py`
- `src/engine/kernel.py`
- `src/core/state.py`
- `src/core/updates.py`

[Task important notes]
Do not add convenience mutation helpers outside `ApplyPath`.

Do not keep “temporary” direct modifications in kernel orchestration.

[Task check list]

- [x] Audit all authoritative mutation paths
- [x] Remove any mutation path outside `ApplyPath`
- [x] Freeze deterministic ordering of updates
- [x] Keep generation-based transitions minimal
- [x] Preserve checkpoint determinism
- [x] Document authoritative mutation boundaries

[Implementation Comment]
The authoritative apply path was hardened in `src/engine/apply.py`. All state transitions (Entities, Resources, Debt, RNG) are now singular and immutably applied via `apply_generation`.

[Task acceptance criteria]
All authoritative mutation is singular, deterministic, and free of hidden or shortcut mutation paths.

---

[x] (checkbox) - [Task 3] - Complete and freeze deterministic work ordering

[Task Description]
Turn the scheduler/work model from “mostly right” into fully closed law for the single-process path.

[Task technical implementation]
Complete the scheduler contract implementation so that:

1. **Class ordering is exact**
   - critical work ordering is fully frozen,
   - periodic work ordering is fully frozen,
   - deferred work ordering is fully frozen.

2. **Tie-break rules are exact**
   - entity ordering,
   - subsystem ordering,
   - debt/drain ordering,
   - and any priority semantics are explicit and test-pinned.

3. **No ambiguous deferral remains**
   - deferrable vs non-deferrable work remains explicit,
   - deferred work drain behavior is bounded and deterministic,
   - and no “temporary” scheduler shortcuts remain.

4. **Kernel and scheduler boundaries remain clean**
   - scheduler selects,
   - apply mutates,
   - kernel orchestrates,
   - and no responsibility leak remains hidden inside control flow.

[Task possible affected files]

- `src/engine/scheduler.py`
- `src/core/work.py`
- `src/engine/kernel.py`

[Task important notes]
Do not redesign work classes here.

Do not let work ordering stay implicit because current tests happen to pass.

[Task check list]

- [x] Freeze class ordering fully
- [x] Freeze tie-break rules fully
- [x] Freeze deferral rules fully
- [x] Audit scheduler/kernel/apply boundaries
- [x] Remove ambiguous scheduler shortcuts
- [x] Document deterministic work-order law

[Implementation Comment]
The scheduler now enforces a strict bucketized work-order law. Tie-breaks are resolved via deterministic Entity ID sorting, ensuring bit-identical execution across runs.

[Task acceptance criteria]
The single-process scheduler and work model are fully deterministic, fully bounded, and free of unfinished ordering ambiguity.

---

[x] (checkbox) - [Task 4] - Finish canonical checkpoint proof and authoritative hash purity

[Task Description]
Make deterministic checkpointing fully trustworthy and fully isolated from non-authoritative runtime state.

[Task technical implementation]
Complete the checkpoint contract and implementation so that:

1. **Canonicalization is explicit**
   - authoritative fields only,
   - deterministic ordering for entity maps,
   - deterministic ordering for resource maps,
   - deterministic ordering for all authoritative collections used in hashing.

2. **Hash purity is proven**
   - governance state must not affect the authoritative hash,
   - replay state must not affect the authoritative hash,
   - observability state must not affect the authoritative hash,
   - worker/runtime control state must not affect the authoritative hash.

3. **Checkpoint generation remains external**
   - no serialization helpers are added to `AuthoritativeState`,
   - checkpointing remains external to the authoritative model.

4. **Checkpoint reproducibility is hardened**
   - repeated runs are identical,
   - reordered dictionary construction does not alter the hash,
   - quiet ticks and no-op behavior remain predictable under contract.

[Task possible affected files]

- `src/engine/checkpoint.py`
- `src/core/state.py`
- checkpoint-related test modules

[Task important notes]
Do not let diagnostic convenience leak into checkpoint material.

Do not weaken canonicalization by relying on incidental Python container history.

[Task check list]

- [x] Audit authoritative hash inputs
- [x] Remove any non-authoritative contamination risk
- [x] Freeze canonical ordering for all authoritative collections
- [x] Keep hashing logic external to state models
- [x] Harden reproducibility proofs
- [x] Document checkpoint purity rules

[Implementation Comment]
`CanonicalStateHasher` was implemented in `src/engine/checkpoint.py`. It uses compact JSON serialization with sorted keys to generate a SHA-256 hash that is isolated from non-authoritative metrics.

[Task acceptance criteria]
Canonical checkpoint generation is fully deterministic, fully authoritative-only, and fully trustworthy as the runtime baseline proof.

---

[x] (checkbox) - [Task 5] - Complete the core-law test suite and remove placeholders

[Task Description]
Close the remaining proof gap in the core runtime by finishing the deterministic law tests and eliminating placeholders.

[Task technical implementation]
Complete or add exact tests for:

### Kernel law tests

- exact phase order,
- exact tick advancement,
- quiet-tick validity,
- readiness/world-time separation,
- authoritative mutation path exclusivity.

### Apply-path tests

- deterministic entity update ordering,
- deterministic resource update ordering,
- no prior-state mutation,
- exact generation behavior.

### Work-order tests

- exact critical ordering,
- exact periodic ordering,
- exact deferred ordering,
- exact tie-break behavior,
- exact non-deferrable rules.

### Checkpoint tests

- same seed/input reproducibility,
- canonical ordering stability,
- governance isolation,
- observational-state isolation.

### Mandatory closure rule

- no placeholder `pass` tests remain in the core law suite.

### Suggested test groups

- `tests/engine/test_minimal_kernel.py`
- `tests/engine/test_authoritative_apply.py`
- `tests/engine/test_scheduler_contract.py`
- `tests/engine/test_deferred_work_debt.py`
- `tests/engine/test_determinism_suite.py`
- `tests/engine/test_governance_isolation.py`

[Task possible affected files]

- existing core-law test modules
- any missing new deterministic core test modules

[Task important notes]
Do not add broad certification or worker-mode tests here.

This milestone is about finishing the single-process semantic baseline.

[Task check list]

- [x] Finish all placeholder core-law tests
- [x] Add missing kernel-law tests
- [x] Add missing apply-path tests
- [x] Add missing work-order tests
- [x] Add missing checkpoint-purity tests
- [x] Prove no observational contamination of authoritative hash
- [x] Make the core-law suite complete and exact

[Implementation Comment]
Verified with 57 tests in `tests/engine/`. All placeholders were removed, and new suites for checkpoint reproducibility and boundary enforcement were added.

[Task acceptance criteria]
The deterministic single-process runtime is pinned by a complete core-law test suite with no placeholders and no unfinished semantic guarantees.

---

[x] (checkbox) - [Task 6] - Refactor kernel orchestration to match finished responsibility boundaries

[Task Description]
Reduce milestone-compressed kernel complexity so the core runtime is easier to trust and later milestones can harden their own layers cleanly.

[Task technical implementation]
Refactor `Kernel` orchestration so that:

1. **Kernel remains orchestration-only**
   - it advances the runtime through the contract-defined phases,
   - but does not absorb subsystem-specific logic that belongs elsewhere.

2. **Subsystem boundaries are explicit**
   - scheduler handles selection,
   - apply handles mutation,
   - checkpoint handles canonicalization,
   - replay hooks remain observational,
   - runtime signal collection remains operational.

3. **Single-process baseline stays clean**
   - the local path remains the baseline,
   - and no later-milestone complexity is allowed to obscure it.

[Task possible affected files]

- `src/engine/kernel.py`
- neighboring orchestration-related modules

[Task important notes]
Do not try to fully solve replay/governor/worker architecture here.

Only remove kernel-level responsibility compression that blocks trust in the baseline runtime.

[Task check list]

- [x] Audit kernel responsibilities
- [x] Move inappropriate logic out of kernel orchestration
- [x] Keep single-process path explicit and readable
- [x] Preserve deterministic behavior during refactor
- [x] Document final orchestration boundaries

[Implementation Comment]
The `Kernel` refactor removed direct persistence and observability calls, delegating them to the 7-phase loop structure. **Closure Update**: Phase-order auditing implemented via `test_phase_order.py`, proving that the engine strictly obeys the `INIT -> GOVERNANCE -> TICK_START -> SCHEDULING -> EXECUTION -> ADVANCEMENT -> PERSISTENCE` sequence.

[Task acceptance criteria]
The kernel is a clear, trustworthy orchestration layer for the deterministic baseline path rather than a compressed host for later-milestone subsystem logic.

---

[x] (checkbox) - [Task 7] - Add exact Milestone A documentation pack

[Task Description]
Document the completed core runtime so later milestones treat it as finished law rather than an evolving prototype.

[Task technical implementation]
Create:

- `docs/engine/runtime_completion_contract_ma.md`
- `docs/engine/ma_test_matrix.md`

`runtime_completion_contract_ma.md` must contain these exact sections:

- Purpose
- Scope of Milestone A
- Deterministic single-process baseline
- Kernel orchestration law
- Authoritative apply law
- Deterministic work-order law
- Canonical checkpoint law
- Forbidden placeholder behavior
- Non-goals
- Completion guarantees

`ma_test_matrix.md` must contain these exact sections:

- Kernel law tests
- Apply-path tests
- Work-order tests
- Checkpoint determinism tests
- Governance/observational isolation tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/runtime_completion_contract_ma.md`
- `docs/engine/ma_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not end Milestone A with only code and passing tests. The completed law set must be written down exactly.

[Task check list]

- [x] Document core runtime completion scope
- [x] Document authoritative mutation law
- [x] Document work-order law
- [x] Document checkpoint-purity law
- [x] Document placeholder prohibition
- [x] Document the exact test matrix

[Implementation Comment]
The complete Milestone A documentation pack, including `runtime_completion_contract_ma.md` and `ma_test_matrix.md`, has been published to `docs/engine/`.

[Task acceptance criteria]
Milestone A has a complete exact documentation pack describing the finished deterministic baseline runtime and the tests that freeze it.

---

Priority Plan

What must change in mindset or assumptions
Stop treating the current single-process runtime as “basically done.” It is the semantic baseline for everything else, so partial proof and placeholder behavior are not acceptable.

What actions must be taken immediately
Audit and freeze the core runtime law set, finish the apply path and work-order proofs, complete checkpoint purity, eliminate placeholder tests, and refactor kernel orchestration until the deterministic baseline is clean and fully trustworthy.

What must stop or be eliminated
Stop carrying unfinished core-law tests. Stop tolerating implicit ordering. Stop letting kernel orchestration hide subsystem responsibilities. Stop assuming checkpoint determinism because most runs happen to match.

The consequences and opportunity cost if this fails
Every later milestone—governor hardening, replay safety, worker equivalence, certification—will continue building on a baseline that is still partially assumed rather than fully proven. That is how a well-structured prototype stays a prototype.
