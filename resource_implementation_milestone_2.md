[Milestone 2] - Minimal Deterministic Single-Thread Kernel

[Milestone Description]
Milestone 2 is the first executable foundation of the new engine. Its purpose is **not** to make the engine scalable yet, and it is **not** to introduce bounded replay, worker execution, or degradation modes yet. Its purpose is to build the smallest correct runtime that obeys the Milestone 1 kernel contract and proves the engine can execute deterministic simulation-time progression without hidden infrastructure complexity.

This milestone must lock the first runnable kernel laws:

- how one tick actually executes,
- how world-time advances,
- how readiness gates entity action,
- how authoritative state is mutated,
- how deterministic randomness is consumed,
- and how stable checkpoints are produced for testing.

The previous milestone defined what the engine means. This milestone turns that contract into one minimal, explicit, runnable kernel.

[Milestone technical implementation]
Create one minimal single-thread simulation kernel and make the runtime obey it.

This milestone must implement these exact behaviors:

### Runtime execution rules

1. **Single-thread execution**
   - All authoritative execution is single-threaded in this milestone.
   - No worker execution, async authority paths, or remote dispatch are introduced here.
   - Tick execution order must be explicit and stable.

2. **Tick phase execution**
   - The runtime must execute the exact phase skeleton frozen in Milestone 1.
   - The kernel must expose one deterministic tick entry point.
   - Each tick must advance simulation-time in one explicit place.

3. **World-time progression**
   - World-time progression must execute every tick.
   - Passive time-driven state must continue advancing even when no entity is ready.
   - Quiet ticks are valid kernel behavior, not exceptional behavior.

4. **Readiness-gated entity action**
   - Entity action is allowed only when readiness rules say the entity is due.
   - A lack of ready entities must not block tick advancement.
   - Readiness handling must remain structurally separate from world-time progression.

5. **Authoritative state mutation**
   - Authoritative state changes must occur through one explicit apply path.
   - The kernel must not allow observational or derived data to mutate authoritative outcomes.
   - Deterministic apply order must remain exact.

6. **Deterministic RNG consumption**
   - Randomness must be consumed through the Milestone 1 RNG contract only.
   - The same seed and same inputs must yield the same authoritative checkpoints.
   - The kernel must not leak deterministic behavior through incidental iteration order.

7. **Stable checkpointing for tests**
   - The kernel must provide a stable way to produce authoritative checkpoint hashes or summaries for test assertions.
   - Checkpoint representation must be deterministic and independent of non-authoritative fields.

### Runtime contract boundaries

8. **Non-goals of this milestone**
   - Do not add scheduler optimization here.
   - Do not add replay persistence here.
   - Do not add resource governor behavior here.
   - Do not add observability systems beyond what is minimally required for tests.
   - Do not add concurrency here.
   - Do not add profile-based degradation here.

9. **Clean-code boundary**

- Tick execution, readiness evaluation, world-time advancement, and authoritative apply must be separated into distinct responsibilities.
- Do not bury deterministic apply order inside mixed orchestration logic.
- Do not let helper code mutate authoritative state implicitly.

[Milestone important notes]
The first trap in this milestone is trying to make the kernel “production-like” too early. That is avoidance. A minimal deterministic kernel is not a temporary toy. It is the reference truth for every later milestone.

The second trap is smuggling in future architecture because it feels efficient. Replay sinks, worker interfaces, and optimization hooks do not belong here unless the kernel contract explicitly requires them.

The third trap is allowing test convenience to distort semantics. Fake time progression, fake readiness bypasses, or non-deterministic helpers will poison every later milestone.

The fourth trap is treating checkpoint hashing as optional. It is not optional. If you cannot produce stable authoritative checkpoints, you cannot prove determinism.

[Milestone acceptance criteria]
At the end of Milestone 2, the codebase has:

- one minimal runnable single-thread kernel,
- one exact tick execution path,
- one exact separation between world-time and readiness-gated action,
- one exact authoritative apply path,
- one deterministic checkpoint mechanism,
- and one deterministic test suite proving kernel correctness.

No replay system, bounded persistence, worker execution, or degradation control is required for Milestone 2 completion.

## Task

[ ] (checkbox) - [Task 1] - Implement the minimal kernel tick execution path

[Task Description]
Build the smallest exact runnable kernel loop that obeys the Milestone 1 contract. This is the core execution task for the milestone.

[Task technical implementation]
Implement one kernel entry point such as `tick()` or equivalent that performs:

### Required tick responsibilities

- advances simulation-time exactly once,
- executes the frozen phase order,
- advances passive world-time systems,
- determines which entities are ready,
- executes ready entity actions through an explicit apply path,
- and finalizes a deterministic post-tick authoritative state.

### Required boundaries

- no hidden mutation outside the tick path,
- no observational system allowed to modify authoritative outcomes,
- no concurrency,
- no replay,
- no background work.

[Task possible affected files]

- `src/engine/kernel.py`
- `src/engine/tick.py`
- `src/engine/phases.py`
- authoritative world-state module
- readiness gating module

[Task important notes]
Do not over-generalize the kernel entry point.

Do not add extension hooks for future milestones unless the Milestone 1 contract already requires them.

[Task check list]

- [ ] Implement one deterministic tick entry point
- [ ] Advance simulation-time in one explicit place
- [ ] Execute frozen phase order
- [ ] Keep authoritative mutation inside explicit paths
- [ ] Keep the kernel single-threaded
- [ ] Avoid future-milestone leakage

[Task acceptance criteria]
The engine has one minimal runnable tick execution path that obeys the kernel contract and contains no hidden authority paths.

---

[ ] (checkbox) - [Task 2] - Implement world-time progression and readiness separation

[Task Description]
Make the runtime obey the separation between general world-time progression and readiness-gated entity action.

[Task technical implementation]
Implement two distinct runtime responsibilities:

1. **World-time progression**
   - progresses every tick,
   - updates passive time-driven state,
   - remains valid even during quiet ticks.

2. **Entity action progression**
   - evaluates readiness,
   - allows only due entities to act,
   - does not control whether passive world-time progression occurs.

This task must prove structurally that:

- quiet ticks are real ticks,
- passive systems do not depend on action presence,
- entity action is gated by readiness only.

[Task possible affected files]

- `src/engine/tick.py`
- `src/engine/world_time.py`
- `src/engine/readiness.py`
- passive lifecycle/state progression modules

[Task important notes]
Do not solve quiet-tick behavior by forcing placeholder actions.

Do not leave world-time progression hidden inside action-processing code.

[Task check list]

- [ ] Implement world-time progression path
- [ ] Implement readiness evaluation path
- [ ] Ensure quiet ticks still advance passive time
- [ ] Keep readiness separate from world-time advancement
- [ ] Preserve deterministic ordering
- [ ] Keep implementation minimal and exact

[Task acceptance criteria]
World-time progression and readiness-gated action are structurally separate, and quiet ticks still produce valid deterministic simulation progression.

---

[ ] (checkbox) - [Task 3] - Implement the authoritative apply path

[Task Description]
Create the single explicit path through which authoritative state is mutated.

[Task technical implementation]
Implement an apply layer that:

- receives authoritative state changes,
- applies them in deterministic order,
- rejects invalid or out-of-contract mutation attempts,
- and prevents observational state from modifying authoritative outcomes.

The apply path must be exact enough to support later milestones without changing its semantic meaning.

This task should include:

- deterministic update ordering,
- conflict handling rules if applicable at this stage,
- and explicit separation between state derivation and state mutation.

[Task possible affected files]

- `src/engine/apply.py`
- authoritative state mutation module
- action/result application module
- validation module for authoritative updates

[Task important notes]
Do not let helpers mutate world state directly.

Do not introduce future conflict-resolution complexity unless it is required for minimal correctness.

[Task check list]

- [ ] Create one authoritative apply path
- [ ] Enforce deterministic update ordering
- [ ] Reject invalid mutation attempts
- [ ] Keep derived state outside authoritative mutation
- [ ] Keep the apply layer minimal and exact

[Task acceptance criteria]
All authoritative state changes flow through one deterministic apply path and no implicit mutation path remains in the minimal kernel.

---

[ ] (checkbox) - [Task 4] - Implement deterministic RNG plumbing and stable checkpoint hashing

[Task Description]
Make deterministic execution provable rather than assumed.

[Task technical implementation]
Implement:

### Deterministic RNG plumbing

- one explicit kernel RNG instance or policy,
- deterministic seed initialization,
- deterministic consumption rules,
- and prohibition of ambient randomness in authoritative behavior.

### Stable checkpointing

- one authoritative checkpoint serializer, hash builder, or canonical summary generator,
- exclusion of non-authoritative fields from checkpoint material,
- stable ordering guarantees for checkpoint generation.

The same seed and same inputs must produce the same checkpoints over repeated runs.

[Task possible affected files]

- RNG module
- kernel initialization module
- checkpoint/hash utility module
- authoritative state serializer/canonicalizer

[Task important notes]
Do not hash arbitrary object graphs directly.

Do not allow unordered collections to poison checkpoint determinism.

[Task check list]

- [ ] Implement deterministic seed handling
- [ ] Route authoritative randomness through one policy
- [ ] Implement canonical checkpoint generation
- [ ] Exclude non-authoritative fields from checkpoints
- [ ] Add stable ordering rules for checkpoint material
- [ ] Keep checkpoint representation test-friendly

[Task acceptance criteria]
The engine can prove deterministic execution by producing identical authoritative checkpoints for repeated runs with the same seed and input.

---

[ ] (checkbox) - [Task 5] - Add minimal-kernel deterministic test suite

[Task Description]
Lock the Milestone 2 runtime behavior with deterministic tests so later milestones cannot silently change the kernel foundation.

[Task technical implementation]
Add exact tests for:

### Kernel execution tests

- one tick advances simulation-time exactly once,
- frozen phase order is executed,
- quiet ticks remain valid,
- readiness gates action eligibility correctly,
- authoritative state mutates only through the apply path.

### Determinism tests

- same seed + same inputs => same authoritative checkpoints,
- different seeds may produce different checkpoints where randomness is relevant,
- checkpoint generation is stable across repeated runs.

### Boundary tests

- observational state does not affect authoritative state,
- invalid mutation attempts are rejected,
- no-ready-entity ticks still progress world-time correctly.

### Suggested test groups

- `tests/engine/test_minimal_kernel.py`
- `tests/engine/test_authoritative_apply.py`
- `tests/engine/test_rng_determinism.py`
- `tests/engine/test_checkpoint_hashing.py`

[Task possible affected files]

- new engine kernel test modules
- new deterministic checkpoint test modules

[Task important notes]
These are correctness and determinism tests, not performance tests.

Do not add worker, replay, or governor tests here.

[Task check list]

- [ ] Add tick-execution tests
- [ ] Add quiet-tick progression tests
- [ ] Add readiness gating tests
- [ ] Add authoritative apply-path tests
- [ ] Add deterministic RNG tests
- [ ] Add stable checkpoint tests
- [ ] Add invalid-mutation rejection tests

[Task acceptance criteria]
The minimal kernel is pinned by deterministic tests proving correct phase execution, correct readiness behavior, correct authoritative mutation, and stable checkpoint reproducibility.

---

[ ] (checkbox) - [Task 6] - Add exact Milestone 2 documentation pack

[Task Description]
Document the complete Milestone 2 kernel implementation so later milestones build on a frozen executable reference rather than informal memory.

[Task technical implementation]
Create:

- `docs/engine/minimal_kernel_m2.md`
- `docs/engine/m2_test_matrix.md`

`minimal_kernel_m2.md` must contain these exact sections:

- Purpose
- Minimal kernel scope
- Tick execution path
- World-time progression semantics
- Readiness-gated action semantics
- Authoritative apply-path semantics
- Deterministic RNG usage
- Stable checkpoint semantics
- Non-goals
- Determinism guarantees

`m2_test_matrix.md` must contain these exact sections:

- Tick execution tests
- Quiet-tick tests
- Readiness tests
- Authoritative apply tests
- RNG determinism tests
- Checkpoint reproducibility tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/minimal_kernel_m2.md`
- `docs/engine/m2_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer it until after later infrastructure exists.

[Task check list]

- [ ] Document exact minimal-kernel scope
- [ ] Document tick execution semantics
- [ ] Document readiness/world-time separation
- [ ] Document apply-path semantics
- [ ] Document deterministic RNG usage
- [ ] Document checkpoint semantics
- [ ] Document test matrix and regression intent

[Task acceptance criteria]
Milestone 2 has a complete exact documentation pack describing the minimal kernel and the deterministic test matrix that freezes it.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of this milestone as “basic scaffolding.” It is the first executable truth of the engine. If the minimal kernel is sloppy, every later layer will be contaminated.

What actions must be taken immediately
Implement the single-thread tick path, separate world-time from readiness, centralize authoritative mutation, route randomness through one deterministic policy, and pin the result with stable checkpoints and tests.

What must stop or be eliminated
Stop adding future architecture early. Stop implicit world mutation. Stop assuming determinism without proving it. Stop letting quiet ticks behave like missing time.

The consequences and opportunity cost if this fails
Later milestones will be built on an untrustworthy kernel, and you will waste time debugging replay, governor, scheduler, or worker behavior when the real defect is that the executable foundation was never truly frozen.
