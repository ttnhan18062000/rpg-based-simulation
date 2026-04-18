[Milestone 1] - Simulation Kernel Contract and Resource-Envelope Rulebook

[Milestone Description]
Milestone 1 is the foundation for the new simulation engine. Its purpose is **not** to make the engine fast yet, and it is **not** to introduce concurrency, replay, or degradation behavior yet. Its purpose is to define one exact, deterministic, auditable contract for:

- what the simulation kernel means,
- what state is authoritative,
- how time advances,
- how actions become valid and are applied,
- what determinism means,
- and what resource-envelope guarantees every later milestone must obey.

This milestone must lock the engine’s basic laws:

- what a tick means,
- what authoritative state means,
- what order state transitions happen in,
- how deterministic randomness works,
- which runtime behavior is allowed to degrade and which is not,
- and how runtime profiles define fixed resource ceilings.

The high-level plan already made this the first milestone because everything later depends on it. If this milestone is vague, every later optimization or safety feature becomes patchwork, and the project will drift into accidental semantics and fake performance claims.

[Milestone technical implementation]
Create one exact simulation-kernel contract and make the project structure obey it.

This milestone must implement these exact rules:

### Simulation semantics rules

1. **Tick semantics**
   - A tick is the smallest authoritative simulation-time unit.
   - Tick progression is explicit and deterministic.
   - The simulation must define exactly what phases occur inside one tick.
   - Tick advancement must not depend on observability, replay, or optional diagnostics.

2. **Authoritative state**
   - The engine must explicitly define which state is authoritative.
   - Authoritative state includes only data required to determine future simulation outcomes.
   - Derived, diagnostic, replay-only, and observability-only data must be explicitly classified as non-authoritative.
   - Non-authoritative state must never be allowed to alter authoritative outcomes.

3. **Apply-order semantics**
   - The order in which authoritative updates are applied must be exact and deterministic.
   - Tie-break behavior must be explicit.
   - The same seed, same profile, and same inputs must produce the same authoritative state transitions.

4. **Action readiness semantics**
   - The engine must explicitly define when an entity is eligible to act.
   - Eligibility to act must be separate from general world-time progression.
   - A lack of ready entities must not imply a lack of simulation-time progression.

5. **Deterministic RNG contract**
   - All simulation randomness must flow through one explicit deterministic RNG policy.
   - No authoritative behavior may depend on unordered iteration, ambient system randomness, wall-clock time, or thread scheduling.
   - The same seed and same input stream must produce the same authoritative results.

### Runtime contract boundaries

6. **Authoritative vs degradable behavior**
   - The engine must explicitly define what may degrade under resource pressure.
   - Core simulation semantics must not be degradable.
   - Replay richness, observability richness, optional summaries, and optional diagnostics may be degradable.
   - Degradation boundaries must be documented now, even though the governor is implemented later.

7. **Runtime profiles**
   - The engine must define named runtime profiles as first-class configuration contracts.
   - A profile defines the maximum resources the engine is allowed to consume.
   - A profile is not a suggestion. It is a hard execution envelope.

8. **Resource-envelope semantics**
   - Every runtime profile must define:
     - max RAM,
     - max CPU/core usage,
     - max worker count,
     - max queue depth,
     - max replay budget,
     - max observability budget,
     - max per-tick work budget,
     - degradation thresholds,
     - and certified throughput expectations by hardware class.

9. **Correct performance language**
   - The engine must not claim identical performance on all machines.
   - The correct contract is:
     - same semantics,
     - same resource envelope,
     - same degradation behavior,
     - and certified throughput by hardware class.

10. **Clean-code boundary**

- Simulation semantics, resource-envelope definitions, and future operational controls must be separated into distinct responsibilities.
- Do not bury authoritative-state rules, deterministic ordering rules, or profile ceilings as scattered implicit behavior.
- This milestone must make those rules centralized and inspectable.

[Milestone important notes]
The first trap in this milestone is trying to optimize before the kernel contract is frozen. That is backwards. If you start with scheduler tricks, concurrency, or replay design before authoritative state, tick semantics, and RNG rules are frozen, you will create a system that is fast in the wrong shape.

The second trap is confusing “fresh project” with “freedom to improvise.” It is the opposite. Because there is no backward-compatibility burden, this milestone must be stricter, not looser.

The third trap is treating resource limits as operational details to define later. They are part of the product contract. The current source and tests already prove that RAM and CPU exhaustion are real failure modes, so this milestone must make bounded resource usage explicit from the start.

The fourth trap is writing vague performance goals. This milestone must not allow “same performance everywhere” language. It must define envelope compliance and hardware-class certification instead.

The fifth trap is hiding authoritative semantics inside emergent behavior. This milestone must not rely on “the implementation will naturally behave this way.” The laws must become exact and testable.

[Milestone acceptance criteria]
At the end of Milestone 1, the project has:

- one exact simulation-kernel contract,
- one exact authoritative-state classification,
- one exact deterministic RNG contract,
- one exact runtime-profile and resource-envelope contract,
- one deterministic set of kernel contract tests,
- and one exact documentation pack stating these rules without ambiguity.

No scheduler optimization, replay system, concurrency model, or degradation mechanism is required for Milestone 1 completion.

## Task

[x] (checkbox) - [Task 1] - Define the simulation kernel contract

[Task Description]
Create the exact design contract for simulation semantics. This is the foundational modeling task for the new engine. Without it, later milestones will drift into hidden assumptions, accidental ordering rules, and fake determinism.

[Task implementation comments]
Implemented the core contract in `docs/engine/simulation_kernel_contract_m1.md` and `src_v2/core/contracts.py`. The kernel orchestrator in `src_v2/engine/kernel.py` strictly follows the phase-ordered tick loop (INIT, GOVERNANCE, SCHEDULING, PACKETIZATION, RESOLUTION, PERSISTENCE). Deterministic progression is guaranteed via the `ApplyPath` mechanism and `AuthoritativeState` partitioning.

[Task technical implementation]
Create one new kernel-contract reference document and one code-facing contract section that define exactly:

### Simulation contract

- what a tick means,
- what phases a tick contains,
- what makes an entity eligible to act,
- what state is authoritative,
- what state is derived or observational only,
- how authoritative updates are ordered,
- and how deterministic state progression is defined.

### Determinism contract

- all authoritative randomness flows through one explicit RNG policy,
- no authoritative logic depends on wall-clock time,
- no authoritative logic depends on unordered collection traversal,
- no authoritative logic depends on ambient process state.

### Non-goals

- no scheduler optimization,
- no replay implementation,
- no concurrency model,
- no degradation logic implementation,
- no observability implementation beyond contract visibility,
- no performance tuning.

[Task possible affected files]

- `docs/engine/simulation_kernel_contract_m1.md`
- `src/engine/` kernel or world loop contract module
- `src/core/` authoritative state model definitions
- configuration/profile contract module

[Task important notes]
Do not write this as vague architecture prose. The contract must be exact enough to generate tests and code from it.

Do not mix this contract with future milestone implementation detail.

[Task check list]

- [x] Define tick semantics
- [x] Define tick phase ordering
- [x] Define authoritative state boundaries
- [x] Define action-readiness semantics
- [x] Define deterministic apply-order semantics
- [x] Define deterministic RNG semantics
- [x] Define explicit non-goals
- [x] Keep the contract exact and minimal

[Task acceptance criteria]
The project has one exact simulation-kernel contract that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Define the runtime-profile and resource-envelope contract

[Task Description]
Create the exact operational contract for stable and bounded resource usage. This task freezes what a runtime profile is and what limits it must define.

[Task implementation comments]
Implemented the profile schema in `src_v2/config/profiles.py` and validation logic in `src_v2/config/validator.py`. Reference profiles are defined in `src_v2/config/__init__.py`. The resource envelope (RAM, CPU, Queue, Work Debt) is now a first-class requirement for every certified simulation run.

[Task technical implementation]
Create one exact profile contract that defines:

### Runtime profile semantics

- a profile is a named execution contract,
- a profile declares hard ceilings,
- the engine must reject invalid or contradictory profile definitions,
- and all later runtime systems must consume profile-defined limits rather than hard-coded defaults.

### Resource-envelope fields

Every profile must define:

- max RAM,
- max CPU/core usage,
- max worker count,
- max queue depth,
- max replay budget,
- max observability budget,
- max per-tick work budget,
- degradation thresholds,
- and throughput certification expectations by hardware class.

### Performance language

The contract must explicitly state:

- same profile does not guarantee identical throughput on all hardware,
- same profile does guarantee the same resource ceilings and same semantic behavior,
- stronger hardware may perform better within the same envelope,
- weaker hardware may degrade earlier but must not exceed the envelope.

[Task possible affected files]

- `docs/engine/runtime_profiles_m1.md`
- configuration/profile schema module
- profile validation module

[Task important notes]
Do not make profile limits advisory.

Do not use vague phrases like “reasonable resource usage.” Every profile field must be explicit.

[Task check list]

- [x] Define runtime profile semantics
- [x] Define hard resource-envelope fields
- [x] Define profile validation rules
- [x] Define performance-language contract
- [x] Define hardware-class certification concept
- [x] Keep profile rules exact and enforceable

[Task acceptance criteria]
The project has one exact runtime-profile contract that defines stable resource ceilings and correct performance language.

---

[x] (checkbox) - [Task 3] - Implement authoritative state classification and kernel phase skeleton

[Task Description]
Make the codebase reflect the frozen kernel contract at a structural level. This task does not implement full engine behavior. It creates the exact boundaries and skeleton that later milestones will fill.

[Task implementation comments]
The skeletal engine is implemented in `src_v2/engine/kernel.py`. Authoritative state is strictly typed in `src_v2/core/state.py`. Kernel phases are explicitly defined as generators in `src_v2/engine/phases.py`, ensuring deterministic execution order across all world ticks.

[Task technical implementation]
Implement or scaffold:

1. **Authoritative state classification**
   - mark or separate authoritative state structures,
   - separate derived/observational state structures,
   - make the distinction explicit in code organization.

2. **Kernel phase skeleton**
   - create the explicit tick phase structure required by the contract,
   - define deterministic phase order,
   - define phase boundaries clearly enough that later milestones can plug in logic without changing the contract.

3. **Readiness and world-time boundary**
   - create the explicit structural separation between world-time advancement and entity action eligibility,
   - do not yet optimize scheduling,
   - do not yet implement advanced action systems.

[Task possible affected files]

- kernel/world loop module
- authoritative state model module
- derived/observational state module
- action-readiness contract module
- simulation tick phase module

[Task important notes]
Do not start filling this skeleton with replay, concurrency, or governor code.

Do not hide authoritative-state separation inside comments only. It must be reflected in code boundaries.

[Task check list]

- [x] Separate authoritative and derived state structures
- [x] Create explicit kernel phase skeleton
- [x] Freeze deterministic phase order in code
- [x] Separate world-time and readiness boundaries
- [x] Keep the implementation skeletal and exact
- [x] Avoid future-milestone leakage

[Task acceptance criteria]
The project structure reflects the kernel contract and exposes explicit boundaries for authoritative state, tick phases, and readiness semantics.

---

[x] (checkbox) - [Task 4] - Add deterministic kernel-contract and profile-contract tests

[Task Description]
Lock the Milestone 1 contract with deterministic tests so later milestones cannot silently change the engine’s laws.

[Task implementation comments]
Implemented contract tests in `tests_v2/engine/test_simulation_kernel_contract.py` and `tests_v2/config/test_runtime_profile_contract.py`. These tests verify deterministic RNG seeding, phase ordering, and profile ceiling enforcement.

[Task technical implementation]
Add exact tests for the rulebook.

### Kernel contract tests

Add test coverage for:

- deterministic seed reproduction,
- stable phase ordering,
- authoritative-state classification expectations,
- same seed + same inputs => same authoritative checkpoints,
- lack of ready entities does not invalidate tick advancement semantics.

### Profile contract tests

Add test coverage for:

- valid runtime profile parsing,
- invalid or contradictory profile rejection,
- required ceiling fields presence,
- profile comparison semantics where needed,
- correct performance-language assumptions.

### Suggested test groups

- `tests/engine/test_simulation_kernel_contract.py`
- `tests/engine/test_deterministic_rng_contract.py`
- `tests/config/test_runtime_profile_contract.py`

[Task possible affected files]

- new engine contract test modules
- new profile validation test modules

[Task important notes]
These are contract tests, not performance tests.

Do not add heavy stress, replay, concurrency, or benchmark suites in this milestone.

[Task check list]

- [x] Add deterministic seed tests
- [x] Add phase-order tests
- [x] Add authoritative-state boundary tests
- [x] Add readiness/world-time boundary tests
- [x] Add profile-schema tests
- [x] Add invalid-profile rejection tests
- [x] Add performance-language contract tests

[Task acceptance criteria]
The simulation kernel and runtime-profile contracts are pinned by deterministic tests.

---

[x] (checkbox) - [Task 5] - Add exact Milestone 1 documentation pack

[Task Description]
Document the complete Milestone 1 contract so later milestones cannot reinterpret it informally.

[Task implementation comments]
Authoritative documentation pack created in `docs/engine/`. Contracts for kernel and profiles are verified by the automated doc-integrity suite implemented in Milestone 10.

[Task technical implementation]
Create:

- `docs/engine/simulation_kernel_contract_m1.md`
- `docs/engine/runtime_profiles_m1.md`
- `docs/engine/m1_test_matrix.md`

`simulation_kernel_contract_m1.md` must contain these exact sections:

- Purpose
- Tick semantics
- Tick phase order
- Authoritative state semantics
- Derived and observational state semantics
- Action-readiness semantics
- Deterministic apply-order semantics
- Deterministic RNG rules
- Non-goals
- Determinism guarantees

`runtime_profiles_m1.md` must contain these exact sections:

- Purpose
- Runtime profile semantics
- Resource-envelope fields
- Validation rules
- Performance-language rules
- Hardware-class certification concept
- Non-goals

`m1_test_matrix.md` must contain these exact sections:

- Kernel contract tests
- RNG contract tests
- Authoritative-state boundary tests
- Runtime profile tests
- Determinism regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/simulation_kernel_contract_m1.md`
- `docs/engine/runtime_profiles_m1.md`
- `docs/engine/m1_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer it.

[Task check list]

- [x] Document exact kernel rules
- [x] Document exact profile rules
- [x] Document exact non-goals
- [x] Document determinism expectations
- [x] Document contract-test groups
- [x] Document regression purpose of each test group

[Task acceptance criteria]
Milestone 1 has a complete exact kernel and runtime-profile documentation pack that matches the implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of Milestone 1 as architecture setup. It is lawmaking. The engine’s meaning and its resource contract must become exact before anything tries to make it fast.

What actions must be taken immediately
Freeze the simulation kernel contract, freeze the runtime-profile contract, reflect both in code boundaries, and pin the result with deterministic contract tests.

What must stop or be eliminated
Stop vague semantics. Stop implicit authoritative-state boundaries. Stop fuzzy performance language. Stop treating resource ceilings as operational details to “figure out later.”

The consequences and opportunity cost if this fails
Every later milestone will build on unstable semantics and unstable execution assumptions, and you will waste time optimizing a system whose rules were never truly frozen.
