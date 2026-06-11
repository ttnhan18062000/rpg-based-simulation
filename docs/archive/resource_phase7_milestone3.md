---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 3] - Authoritative Apply Path and Conflict Resolution Closure

## [Milestone Description]

Milestone 3 closes the authoritative application model.

Its purpose is to ensure one authoritative outcome is produced per tick through one authoritative apply path, even when proposals conflict, partially fail, or touch multiple update domains.

This milestone consumes the action/update substrate from Milestone 2.

It is about:

- authoritative mutation timing,
- conflict resolution,
- deterministic apply ordering,
- partial rejection safety,
- and authoritative outcome truth for replay and observability.

It does not yet close snapshot immutability or world-generation determinism.

## [Milestone technical implementation]

Close the authoritative apply path so that later semantic work cannot quietly redefine world truth.

This milestone must:

- ensure authoritative world mutation occurs only after proposal generation,
- ensure conflicting proposals resolve through one authoritative path,
- ensure partial rejection does not corrupt unrelated update domains,
- ensure apply-order behavior is explicit and deterministic,
- ensure authoritative outcomes are the source of replay/observability truth,
- and eliminate alternate quasi-authoritative application paths.

This milestone must not:

- defer partial-rejection correctness to later phases,
- let replay or observability become hidden semantic authorities,
- or preserve multiple application paths as “temporary convenience.”

## [Milestone important notes]

The trap here is believing that because something called “apply” exists, authority is already closed.

It is not.

Authority is only closed when conflict, rejection, ordering, and replay-visible truth all route through one deterministic path.

## [Milestone acceptance criteria]

At the end of Milestone 3:

- one authoritative apply path exists for supported substrate scope,
- conflict resolution behavior is explicit,
- partial rejection is safe across update domains,
- authoritative outcomes define replay-visible truth,
- and one authoritative outcome per tick is enforced.

---

## Task

### [x] (checkbox) - [Task 1] - Audit current authoritative application flow against Phase 7 apply-path rows

#### [Task Description]

Find where authoritative application is real, partial, or fake.

#### [Task technical implementation]

Map the current apply flow from proposal emission through authoritative mutation and outcome capture.

Identify:

- primary apply path,
- alternate mutation paths,
- ambiguous ownership boundaries,
- partial rejection weaknesses,
- and replay/observability truth leaks.

#### [Task possible affected files]

- `src/engine/**`
- `src/apply/**`
- `src/replay/**`
- `tests/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Do not start patching blindly.
First map the real authority path.

#### [Task check list]

- [ ] Apply flow is mapped
- [ ] Alternate paths are identified
- [ ] Rejection weaknesses are identified
- [ ] Replay truth leaks are identified
- [ ] Audit output is reviewable

#### [Task acceptance criteria]

The project has a clear audit of current authoritative apply-path gaps.

---

### [x] (checkbox) - [Task 2] - Consolidate supported mutation into one authoritative apply pipeline

#### [Task Description]

Make one path the only supported source of authoritative mutation.

#### [Task technical implementation]

Refactor or tighten the engine so supported world mutation happens only through the intended authoritative apply pipeline.

This task should:

- route supported updates through one pipeline,
- eliminate bypasses where practical,
- isolate unsupported legacy shortcuts if temporary,
- and make pipeline entry and exit points explicit.

#### [Task possible affected files]

- `src/engine/**`
- `src/apply/**`
- `src/core/state/**`
- tests and contract docs

#### [Task important notes]

If there are still multiple real mutation paths, you do not have authority closure.

#### [Task check list]

- [ ] Supported mutation uses one pipeline
- [ ] Bypasses are removed or fenced off
- [ ] Entry/exit points are explicit
- [ ] Temporary exceptions are documented if any remain
- [ ] Support claims match reality

#### [Task acceptance criteria]

Supported authoritative mutation occurs through one explicit apply pipeline.

---

### [x] (checkbox) - [Task 3] - Define and enforce deterministic conflict-resolution and apply-order rules

#### [Task Description]

Stop authoritative outcome from depending on incidental proposal ordering or implementation accident.

#### [Task technical implementation]

Define and implement explicit rules for:

- proposal ordering,
- conflict handling,
- tie-breaking where needed,
- and apply-order determinism for supported update domains.

#### [Task possible affected files]

- `src/engine/**`
- `src/apply/**`
- `tests/engine/**`
- apply contract docs

#### [Task important notes]

If apply order is “whatever happens in practice,” determinism is fake.

#### [Task check list]

- [ ] Ordering rules are explicit
- [ ] Conflict handling rules are explicit
- [ ] Tie-breaking rules exist where needed
- [ ] Rules are deterministic
- [ ] Rules are documented

#### [Task acceptance criteria]

Conflict resolution and apply ordering are explicit and deterministic for supported substrate scope.

---

### [x] (checkbox) - [Task 4] - Implement safe partial-rejection behavior across update domains

#### [Task Description]

Prevent failure in one update domain from corrupting unrelated authoritative state.

#### [Task technical implementation]

Refine apply behavior so rejected or invalid updates can be isolated safely.

This task should:

- reject or trim only affected update domains where appropriate,
- preserve unrelated valid authoritative effects,
- avoid partial corruption of composite outcomes,
- and make rejection semantics explicit.

#### [Task possible affected files]

- `src/apply/**`
- `src/core/models/**`
- `tests/engine/test_partial_rejection.py`

#### [Task important notes]

Partial rejection is not a corner case.
It is a core authority property.

#### [Task check list]

- [ ] Rejection scope is explicit
- [ ] Unrelated valid updates survive
- [ ] Composite outcomes do not corrupt state
- [ ] Semantics are documented
- [ ] Failure handling remains deterministic

#### [Task acceptance criteria]

Partial rejection is safe and domain-isolated for supported substrate behavior.

---

### [x] (checkbox) - [Task 5] - Make authoritative outcomes the sole supported truth source for replay and observability

#### [Task Description]

Stop worker intent or intermediate pipeline state from acting like final truth.

#### [Task technical implementation]

Update replay/observability integration so supported truth is derived from authoritative outcomes rather than proposal intent alone or non-authoritative intermediate state.

#### [Task possible affected files]

- `src/replay/**`
- `src/observability/**`
- `src/engine/**`
- tests for replay/outcome truth

#### [Task important notes]

Replay and observability consume authority.
They do not define it.

#### [Task check list]

- [ ] Replay uses authoritative outcomes
- [ ] Observability uses authoritative outcomes
- [ ] Proposal intent is not treated as final truth
- [ ] Intermediate state leaks are removed
- [ ] Supported truth path is documented

#### [Task acceptance criteria]

Replay-visible and observability-visible truth are sourced from authoritative outcomes only.

---

### [x] (checkbox) - [Task 6] - Add direct contract tests for authoritative apply-path, conflict resolution, and rejection behavior

#### [Task Description]

Prove authoritative application directly.

#### [Task technical implementation]

Add focused tests for:

- one authoritative apply path,
- deterministic conflict resolution,
- deterministic apply order,
- safe partial rejection,
- and authoritative-outcome-driven replay behavior.

#### [Task possible affected files]

- `tests/engine/test_authoritative_apply_path.py`
- `tests/engine/test_conflict_resolution_contract.py`
- `tests/engine/test_partial_rejection.py`
- `tests/replay/test_authoritative_outcome_truth.py`

#### [Task important notes]

Do not leave authority proof to indirect downstream tests.

#### [Task check list]

- [ ] Apply-path tests exist
- [ ] Conflict tests exist
- [ ] Ordering tests exist
- [ ] Partial-rejection tests exist
- [ ] Replay truth tests exist

#### [Task acceptance criteria]

The authoritative apply pipeline is directly proven by focused contract tests.

---

### [x] (checkbox) - [Task 7] - Publish the authoritative apply and conflict-resolution contract for supported substrate scope

#### [Task Description]

Freeze authoritative application rules into a stable reference.

#### [Task technical implementation]

Publish one contract package covering:

- apply pipeline boundaries,
- conflict-resolution rules,
- deterministic ordering rules,
- partial-rejection rules,
- and replay/observability truth sourcing.

#### [Task possible affected files]

- `docs/engine/authoritative_apply_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase7_substrate_notes.md`

#### [Task important notes]

If this contract is not explicit, later phases will quietly re-interpret authority again.

#### [Task check list]

- [ ] Apply boundaries are documented
- [ ] Conflict rules are documented
- [ ] Ordering rules are documented
- [ ] Rejection rules are documented
- [ ] Truth-source rules are documented

#### [Task acceptance criteria]

The project has one explicit authoritative apply-path and conflict-resolution contract.

---
