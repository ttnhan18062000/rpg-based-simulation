[Milestone 3] - Bounded Runtime State and Lean Hot-Path Models

[Milestone Description]
Milestone 3 is the first resource-discipline milestone of the new engine. Its purpose is **not** to implement replay yet, and it is **not** to introduce the resource governor yet. Its purpose is to design the runtime state shape so the engine cannot accidentally recreate the same RAM and CPU pathologies that exist in the current system.

This milestone must lock the engine’s first bounded-state laws:

- which runtime structures exist in the hot path,
- which structures are long-lived,
- which data is export-only or diagnostic-only,
- what each long-lived structure is allowed to retain,
- how overflow behaves,
- and how runtime representation avoids heavy validation and serialization cost in authoritative execution.

The current source already shows the failure pattern this milestone must prevent: large in-memory accumulation, expensive object-graph handling, and heavy hot-path serialization. The tests also prove the system is already under active defense against memory spikes and hangs. This milestone exists so those failure modes are designed out of the new engine instead of being “managed later.”

[Milestone technical implementation]
Create one exact bounded runtime-state model and make the codebase obey it.

This milestone must implement these exact rules:

### Runtime state-shape rules

1. **Runtime vs export vs diagnostic model separation**
   - The engine must explicitly separate:
     - hot-path runtime models,
     - persistence/export models,
     - diagnostic/observability models.

   - Hot-path runtime models must be optimized for deterministic execution and bounded memory behavior.
   - Export and diagnostic models must not become the default runtime representation.

2. **Lean hot-path structures**
   - Authoritative hot-path structures must be lightweight and explicit.
   - Hot-path execution must avoid heavy schema-validation and deep object-graph conversion as a default behavior.
   - Hot-path structures must favor deterministic access patterns and low overhead.

3. **Bounded long-lived state**
   - Every long-lived runtime structure must declare:
     - owner,
     - purpose,
     - bound type,
     - exact size or retention rule,
     - overflow behavior,
     - and compaction/eviction behavior if applicable.

4. **No unbounded accumulation**
   - No history, cache, queue, registry, metric buffer, trace buffer, or diagnostic list may grow without an explicit bound or retention rule.
   - “We will monitor it later” is not an acceptable design rule.

5. **Overflow and compaction semantics**
   - Overflow behavior must be explicit.
   - Allowed overflow strategies may include:
     - reject,
     - truncate,
     - evict oldest,
     - compact to summary,
     - or disable optional enrichment.

   - Overflow behavior must not corrupt authoritative simulation state.

6. **Deterministic container behavior**
   - Runtime structures must preserve deterministic ordering where required by the kernel contract.
   - Data representation must not reintroduce nondeterminism through incidental iteration order.

### Runtime contract boundaries

7. **Bounded categories covered by this milestone**
   - This milestone must define bounds or retention rules for at least:
     - world history,
     - event logs,
     - replay pre-buffer structures if any exist,
     - worker queue structures if any placeholders exist,
     - registries,
     - caches,
     - metric buffers,
     - trace buffers,
     - and any other long-lived collection required by the runtime.

8. **Non-goals of this milestone**
   - Do not implement replay streaming here.
   - Do not implement the resource governor here.
   - Do not implement concurrency here.
   - Do not implement observability systems here.
   - Do not add adaptive degradation logic here.
   - Do not tune performance with profiling-driven micro-optimizations here.

9. **Clean-code boundary**

- Runtime model design, retention rules, overflow policy, and export/diagnostic shaping must be separated into explicit responsibilities.
- Do not bury bounds inside incidental implementation details.
- Do not let diagnostic convenience shape authoritative hot-path data structures.

[Milestone important notes]
The first trap in this milestone is pretending that data shape is “just implementation detail.” It is not. Bad data shape is where most resource disasters are born.

The second trap is using rich export or validation models as runtime truth because it feels clean. It is not clean. It is expensive laziness.

The third trap is allowing long-lived structures to exist with vague retention language. If a structure is allowed to exist for multiple ticks, it must have an exact retention rule.

The fourth trap is confusing boundedness with later enforcement. This milestone is about representation and declared retention discipline. The governor comes later. If the state shape is wrong now, the governor will only be a fancier way to fail.

[Milestone acceptance criteria]
At the end of Milestone 3, the codebase has:

- one exact separation between runtime, export, and diagnostic models,
- one exact bounded-state policy for all long-lived runtime structures,
- one exact overflow and compaction contract,
- one lean authoritative hot-path state model,
- and one deterministic test suite proving bounded-state behavior.

No replay sink, concurrency system, or resource-governor behavior is required for Milestone 3 completion.

## Task

[ ] (checkbox) - [Task 1] - Define the bounded runtime state model contract

[Task Description]
Create the exact design contract for runtime state shape, retention, and overflow behavior. This is the foundational modeling task for bounded execution.

[Task technical implementation]
Create one new runtime-state contract document and one code-facing contract section that define exactly:

### Model categories

- hot-path runtime models,
- export/persistence models,
- diagnostic/observability models.

### Required declarations for long-lived structures

Every long-lived structure must define:

- ownership,
- purpose,
- authoritative vs non-authoritative status,
- bound type,
- exact retention or size rule,
- overflow behavior,
- and compaction/eviction behavior if applicable.

### Non-goals

- no replay implementation,
- no observability implementation,
- no governor behavior,
- no concurrency model,
- no micro-optimization work.

[Task possible affected files]

- `docs/engine/runtime_state_contract_m3.md`
- runtime state module definitions
- model categorization module
- retention policy definitions

[Task important notes]
Do not write this as “best practice” prose. The contract must be exact enough to drive code and tests.

Do not leave any long-lived structure uncategorized.

[Task check list]

- [ ] Define model categories
- [ ] Define long-lived structure declaration requirements
- [ ] Define authoritative vs non-authoritative state rules
- [ ] Define bound and retention terminology
- [ ] Define overflow strategy terminology
- [ ] Define explicit non-goals
- [ ] Keep the contract exact and minimal

[Task acceptance criteria]
The project has one exact bounded runtime-state contract that can be used as the authoritative source for implementation and tests.

---

[ ] (checkbox) - [Task 2] - Implement lean hot-path runtime models

[Task Description]
Make the codebase use explicit lightweight runtime structures for authoritative execution rather than heavy export-style models.

[Task technical implementation]
Implement or refactor runtime structures so that:

1. **Authoritative hot-path models**
   - are explicit and lightweight,
   - avoid heavy boundary-validation semantics inside the core loop,
   - avoid deep conversion and incidental serialization cost,
   - and preserve deterministic access behavior.

2. **Export and diagnostic models**
   - are structurally separate,
   - do not become the default authoritative representation,
   - and can be built from runtime state rather than owning runtime state.

3. **No hidden runtime bloat**
   - authoritative-state structures must not embed unnecessary diagnostic payloads,
   - runtime execution must not allocate export-shaped structures by default.

[Task possible affected files]

- authoritative state model modules
- runtime entity/world state modules
- export/DTO modules
- diagnostic/trace model modules

[Task important notes]
Do not perform broad speculative abstractions here.

Do not reintroduce hidden complexity by building a conversion layer for everything before it is needed.

[Task check list]

- [ ] Create lightweight runtime models
- [ ] Separate export models from runtime models
- [ ] Separate diagnostic models from runtime models
- [ ] Remove unnecessary diagnostic payload from hot-path state
- [ ] Preserve deterministic access patterns
- [ ] Keep implementation lean and explicit

[Task acceptance criteria]
Authoritative execution uses lean runtime models and no longer depends on export-shaped or diagnostic-shaped structures in the hot path.

---

[ ] (checkbox) - [Task 3] - Implement bounds, retention rules, and overflow behavior for long-lived structures

[Task Description]
Apply the bounded-state contract to every long-lived runtime structure so no collection can silently grow without limit.

[Task technical implementation]
Implement exact retention and overflow behavior for:

- world history,
- event logs,
- registries,
- caches,
- metric buffers,
- trace buffers,
- and any other long-lived runtime collection currently present in the engine skeleton.

Each structure must define:

1. **Exact bound**
   - max count,
   - max age,
   - max bytes,
   - or another explicit rule.

2. **Exact overflow behavior**
   - reject,
   - truncate,
   - evict oldest,
   - compact to summary,
   - or explicit equivalent.

3. **Compaction behavior where needed**
   - summarization rules must be deterministic,
   - summary generation must not mutate authoritative state incorrectly,
   - and compaction must preserve required semantic usefulness for non-authoritative data.

[Task possible affected files]

- history module
- event log module
- cache modules
- registry modules
- metric/trace buffer placeholders
- retention policy helper modules

[Task important notes]
Do not leave “temporary” unbounded containers in place.

Do not use Python lists or dicts as effectively infinite buffers without declared retention logic.

[Task check list]

- [ ] Define bounds for world history
- [ ] Define bounds for event logs
- [ ] Define bounds for registries
- [ ] Define bounds for caches
- [ ] Define bounds for metric/trace buffers
- [ ] Implement explicit overflow behavior
- [ ] Implement compaction/summarization where required
- [ ] Preserve deterministic behavior under eviction/compaction

[Task acceptance criteria]
Every long-lived runtime structure has an exact bound and explicit overflow behavior enforced in code.

---

[ ] (checkbox) - [Task 4] - Add deterministic bounded-state and overflow tests

[Task Description]
Lock the Milestone 3 state-shape laws with deterministic tests so later milestones cannot reintroduce unbounded growth through convenience.

[Task technical implementation]
Add exact tests for:

### Model-category tests

- authoritative runtime models remain structurally separate from export/diagnostic models,
- non-authoritative fields are not required for authoritative execution.

### Bounded-state tests

- world history respects retention rules,
- event logs respect max size or max age rules,
- caches evict according to declared policy,
- registries obey declared retention or compaction logic,
- metric and trace buffers remain bounded.

### Overflow behavior tests

- overflow uses the declared strategy,
- overflow behavior is deterministic,
- compaction produces stable summaries where required,
- overflow does not mutate authoritative simulation outcomes unexpectedly.

### Suggested test groups

- `tests/engine/test_runtime_state_contract.py`
- `tests/engine/test_bounded_collections.py`
- `tests/engine/test_overflow_behavior.py`

[Task possible affected files]

- new bounded-state contract test modules
- new overflow/retention test modules

[Task important notes]
These are bounded-state tests, not replay tests and not governor tests.

Do not add stress harnesses or system-wide performance tests in this milestone.

[Task check list]

- [ ] Add model-category separation tests
- [ ] Add history retention tests
- [ ] Add event-log bound tests
- [ ] Add cache eviction tests
- [ ] Add registry retention/compaction tests
- [ ] Add overflow determinism tests
- [ ] Add non-authoritative overflow safety tests

[Task acceptance criteria]
The bounded runtime-state contract is pinned by deterministic tests proving separation, retention correctness, overflow correctness, and bounded long-lived behavior.

---

[ ] (checkbox) - [Task 5] - Add exact Milestone 3 documentation pack

[Task Description]
Document the complete Milestone 3 bounded-state model so later milestones cannot drift back into unbounded convenience.

[Task technical implementation]
Create:

- `docs/engine/runtime_state_contract_m3.md`
- `docs/engine/m3_retention_matrix.md`
- `docs/engine/m3_test_matrix.md`

`runtime_state_contract_m3.md` must contain these exact sections:

- Purpose
- Model categories
- Authoritative hot-path model rules
- Export model rules
- Diagnostic model rules
- Long-lived structure declaration rules
- Bound types
- Overflow and compaction semantics
- Non-goals
- Determinism rules

`m3_retention_matrix.md` must contain these exact sections:

- Structure name
- Owner
- Authoritative vs non-authoritative
- Bound type
- Exact retention rule
- Overflow behavior
- Compaction behavior
- Regression risk if violated

`m3_test_matrix.md` must contain these exact sections:

- Model-category tests
- Bounded-state tests
- Overflow tests
- Determinism regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/runtime_state_contract_m3.md`
- `docs/engine/m3_retention_matrix.md`
- `docs/engine/m3_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer retention and overflow documentation until after the governor exists.

[Task check list]

- [ ] Document exact model-category rules
- [ ] Document exact hot-path model rules
- [ ] Document all retention rules
- [ ] Document all overflow behaviors
- [ ] Document all compaction behaviors
- [ ] Document test matrix and regression purpose

[Task acceptance criteria]
Milestone 3 has a complete exact documentation pack describing bounded runtime state, retention rules, overflow rules, and the deterministic test matrix that freezes them.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of memory safety as a runtime guard problem only. It starts with state shape. If the runtime structures are wrong, later controls will only be expensive bandages.

What actions must be taken immediately
Freeze the bounded runtime-state contract, separate hot-path models from export and diagnostic models, define retention and overflow rules for every long-lived structure, and pin all of it with deterministic tests.

What must stop or be eliminated
Stop using export-shaped objects in authoritative execution. Stop allowing any long-lived structure to exist without an exact bound. Stop vague retention language. Stop treating diagnostic convenience as a runtime design priority.

The consequences and opportunity cost if this fails
Later milestones will inherit hidden state bloat, accidental retention, and expensive hot-path object behavior, and you will waste time building governors, replay, and scheduling on top of a runtime shape that was already designed to fail.
