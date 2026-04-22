# [Milestone 5] - Deterministic World Generation and Engine Phase-Order Closure

## [Milestone Description]

Milestone 5 closes the execution substrate that defines how the world is formed and how the engine advances it in deterministic order.

Its purpose is to stop later phases from inheriting drift caused by world-init nondeterminism, ordering ambiguity, or unstable subsystem sequencing.

This milestone covers:

- deterministic world generation,
- deterministic entity initialization relevant to supported scope,
- explicit engine phase order,
- explicit subsystem tick order,
- and baseline tick-integrity guarantees.

It does not cover broader gameplay semantic recovery.

## [Milestone technical implementation]

Close the deterministic runtime baseline so later semantic work sits on a stable execution substrate.

This milestone must:

- ensure supported world-generation behavior is deterministic under equivalent inputs,
- ensure supported entity initialization is deterministic where required,
- ensure engine tick phases execute in explicit deterministic order,
- ensure subsystem sequencing is not defined by incidental implementation details,
- ensure tick-integrity rules are explicit,
- and define what is preserved versus intentionally divergent versus currently out of scope.

This milestone must not:

- silently preserve accidental legacy ordering quirks without classification,
- let concurrency or infrastructure timing redefine baseline semantics,
- or leave subsystem ordering as an implementation accident.

## [Milestone important notes]

The trap here is treating world generation and engine order as low-level mechanics that can be cleaned up later.

That is backwards.

If the baseline world or tick order drifts, later parity mismatches will be misdiagnosed as gameplay problems.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- supported world generation is deterministic,
- supported entity initialization is deterministic,
- engine phase order is explicit,
- subsystem tick order is explicit,
- and later semantic phases inherit a stable deterministic baseline.

---

## Task

### [x] (checkbox) - [Task 1] - Audit world generation, entity initialization, and engine sequencing against Phase 7 determinism rows

#### [Task Description]

Map the actual runtime baseline before trying to fix it.

#### [Task technical implementation]

Review:

- world creation inputs,
- entity initialization flow,
- random-source usage,
- engine tick phases,
- subsystem execution order,
- and any concurrency-sensitive sequencing that could leak into baseline semantics.

#### [Task possible affected files]

- `src_v2/world/**`
- `src_v2/engine/**`
- `src_v2/config/**`
- `tests_v2/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

If baseline sequencing is not mapped first, determinism fixes will be blind and partial.

#### [Task check list]

- [ ] World-generation inputs are mapped
- [ ] Entity-init flow is mapped
- [ ] Random-source usage is mapped
- [ ] Engine phases are mapped
- [ ] Subsystem order is mapped

#### [Task acceptance criteria]

The project has a concrete audit of world/init/order determinism gaps.

---

### [x] (checkbox) - [Task 2] - Canonicalize deterministic world generation and initialization inputs for supported substrate scope

#### [Task Description]

Make the baseline world depend on explicit inputs rather than incidental runtime state.

#### [Task technical implementation]

Refine supported world generation and initialization so equivalent declared inputs yield equivalent authoritative baseline state.

This task should:

- define required world-generation inputs,
- eliminate hidden nondeterministic dependencies,
- normalize seed and config consumption,
- and document any intentionally divergent initialization behavior.

#### [Task possible affected files]

- `src_v2/world/**`
- `src_v2/config/**`
- `src_v2/core/state/**`
- determinism docs

#### [Task important notes]

A world generator that is deterministic only “most of the time” is not supportable.

#### [Task check list]

- [ ] Required inputs are explicit
- [ ] Hidden dependencies are removed
- [ ] Seed/config use is normalized
- [ ] Divergences are documented where needed
- [ ] Supported baseline is deterministic

#### [Task acceptance criteria]

Supported world generation and initialization depend on one explicit deterministic input set.

---

### [x] (checkbox) - [Task 3] - Define and enforce explicit engine phase order for supported runtime paths

#### [Task Description]

Stop engine semantics from depending on incidental function ordering.

#### [Task technical implementation]

Define the supported engine phase order and enforce it through code structure and tests.

This task should make clear:

- what the supported phases are,
- in what order they run,
- and what later phases must not assume outside that order.

#### [Task possible affected files]

- `src_v2/engine/**`
- `tests_v2/engine/test_engine_phase_order.py`
- engine contract docs

#### [Task important notes]

If phase order is not explicit, “deterministic runtime” is a slogan, not a fact.

#### [Task check list]

- [ ] Engine phases are explicit
- [ ] Engine phase order is explicit
- [ ] Enforcement exists in code/tests
- [ ] Unsupported assumptions are excluded
- [ ] Contract is documentable

#### [Task acceptance criteria]

Supported engine phase order is explicit, enforced, and test-visible.

---

### [x] (checkbox) - [Task 4] - Define and enforce explicit subsystem tick sequencing and tick-integrity rules

#### [Task Description]

Make subsystem advancement deterministic and auditable.

#### [Task technical implementation]

Define the supported subsystem sequence within a tick and the integrity rules that govern advancement.

This task should include:

- deterministic subsystem ordering,
- clear boundaries between phases/subsystems,
- tick ownership rules,
- and protection against accidental sequencing drift.

#### [Task possible affected files]

- `src_v2/engine/**`
- `tests_v2/engine/test_subsystem_tick_order.py`
- tick-integrity docs

#### [Task important notes]

Subsystem order should be a contract, not an implementation rumor.

#### [Task check list]

- [ ] Subsystem order is explicit
- [ ] Tick ownership rules are explicit
- [ ] Sequencing drift protections exist
- [ ] Determinism is test-visible
- [ ] Boundaries are documented

#### [Task acceptance criteria]

Supported subsystem sequencing and tick-integrity rules are explicit and enforced.

---

### [x] (checkbox) - [Task 5] - Add determinism tests for world generation, initialization, phase order, and subsystem order

#### [Task Description]

Prove the runtime baseline directly.

#### [Task technical implementation]

Add focused tests for:

- equivalent-input world-generation determinism,
- equivalent-input initialization determinism,
- engine phase-order stability,
- subsystem tick-order stability,
- and baseline/local-path determinism where relevant.

#### [Task possible affected files]

- `tests_v2/world/test_world_generation_determinism.py`
- `tests_v2/world/test_entity_init_determinism.py`
- `tests_v2/engine/test_engine_phase_order.py`
- `tests_v2/engine/test_subsystem_tick_order.py`

#### [Task important notes]

Do not rely on broad end-to-end runs to prove baseline determinism.

#### [Task check list]

- [ ] World determinism tests exist
- [ ] Initialization determinism tests exist
- [ ] Engine order tests exist
- [ ] Subsystem order tests exist
- [ ] Standard validation flow includes them

#### [Task acceptance criteria]

Deterministic world/init/order substrate is directly proven by focused tests.

---

### [x] (checkbox) - [Task 6] - Publish the deterministic world/init/order contract for supported substrate scope

#### [Task Description]

Freeze the baseline runtime execution model into an explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- deterministic world-generation inputs,
- deterministic initialization guarantees,
- supported engine phase order,
- supported subsystem sequencing,
- tick-integrity rules,
- and known exclusions or intentional divergences.

#### [Task possible affected files]

- `docs/engine/deterministic_runtime_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase7_substrate_notes.md`

#### [Task important notes]

If later phases cannot point to this contract, they will reinvent baseline assumptions.

#### [Task check list]

- [ ] World-input contract is documented
- [ ] Initialization guarantees are documented
- [ ] Engine order is documented
- [ ] Subsystem order is documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit deterministic world/init/order contract for supported substrate scope.
