[Milestone 6] - Streaming Replay and Bounded Persistence

[Milestone Description]
Milestone 6 is the first persistence-discipline milestone of the new engine. Its purpose is **not** to introduce concurrency yet, and it is **not** to build the full resilience certification harness yet. Its purpose is to make replay and persistence obey the resource-envelope contract by implementing one exact bounded streaming model instead of allowing replay or persistence to accumulate in memory and destabilize long runs.

This milestone must lock the engine’s first bounded persistence laws:

- how replay data is emitted,
- how replay data is buffered,
- how replay data is chunked and rotated,
- how replay modes change persistence cost,
- how persistence behaves under quota or sink pressure,
- and how replay remains non-authoritative.

The previous milestones froze the kernel, bounded runtime state, defined a deterministic work model, and introduced the governor. This milestone turns those foundations into one exact persistence model so replay and persistence become controlled runtime consumers instead of hidden RAM traps.

[Milestone technical implementation]
Create one exact streaming replay and bounded persistence model and make the runtime obey it.

This milestone must implement these exact rules:

### Replay and persistence rules

1. **Replay is non-authoritative**
   - Replay and persistence artifacts must be explicitly non-authoritative.
   - Failure, slowdown, or reduction in replay richness must not alter authoritative simulation semantics.
   - Replay must reflect authoritative events, not own them.

2. **Streaming write model**
   - Replay persistence must use streaming or append-style writes.
   - Replay must not require whole-run in-memory accumulation before flush.
   - Replay emission must be incremental and bounded.

3. **Chunking and rotation**
   - Replay output must be chunked by exact size, time, tick count, or explicit equivalent rule.
   - Rotation rules must be deterministic and testable.
   - Closed chunks must become immutable replay artifacts.

4. **Bounded in-memory window**
   - Any in-memory replay window or staging area must have an exact bound.
   - In-memory replay data must never be allowed to grow without limit.
   - Replay staging behavior must be profile-aware.

5. **Replay modes**
   - Replay behavior must be controlled by runtime profile and mode.
   - The engine must support explicit replay modes, at minimum:
     - `OFF`
     - `MINIMAL`
     - `DEBUG_WINDOWED`
     - `FORENSIC_SHORT_RUN`

6. **Quota and sink-pressure behavior**
   - Disk budget, sink slowdown, and replay backpressure behavior must be explicit.
   - Replay under pressure must degrade according to profile and governor policy.
   - Replay overflow behavior must not corrupt or stall authoritative execution beyond declared contract.

7. **Deterministic replay ordering**
   - Replay ordering must match authoritative event order as defined by the kernel.
   - Replay output must be deterministic for the same seed, inputs, and runtime profile where replay mode is the same.

### Runtime contract boundaries

8. **What this milestone must cover**
   - This milestone must define:
     - replay event capture boundaries,
     - replay chunk format boundaries,
     - bounded staging/window behavior,
     - replay mode behavior,
     - disk-budget behavior,
     - and sink-pressure behavior.

9. **Non-goals of this milestone**
   - Do not implement concurrency here.
   - Do not implement full observability plumbing here.
   - Do not implement the final certification harness here.
   - Do not implement external storage orchestration or remote replay shipping here.
   - Do not let replay become an alternate state source.

10. **Clean-code boundary**

- Replay event extraction, replay buffering, chunk rotation, persistence writing, and quota-pressure handling must remain separated into explicit responsibilities.
- Do not bury replay-cost control inside ad hoc logging behavior.
- Do not let diagnostic convenience dictate replay retention or chunk design.

[Milestone important notes]
The first trap in this milestone is treating replay as harmless debug output. It is not harmless. In the old design, replay accumulation is one of the clearest direct memory hazards. This milestone exists specifically so the new engine cannot repeat that mistake.

The second trap is trying to make replay “full fidelity by default.” That is the wrong default for a resource-safe engine. Replay richness must obey profile and mode, not developer wishful thinking.

The third trap is allowing replay slowdown to back up into authoritative execution with vague behavior. If sink pressure behavior is not exact, replay will become a hidden denial-of-service path.

The fourth trap is over-designing persistence infrastructure too early. This milestone is about exact bounded replay and persistence behavior, not distributed storage architecture.

[Milestone acceptance criteria]
At the end of Milestone 6, the codebase has:

- one exact streaming replay model,
- one exact replay chunking and rotation model,
- one exact bounded in-memory replay window,
- one exact replay-mode contract,
- one exact quota and sink-pressure behavior model,
- and one deterministic test suite proving replay remains bounded and non-authoritative.

No concurrency, remote persistence architecture, or final resilience certification harness is required for Milestone 6 completion.

## Task

[ ] (checkbox) - [Task 1] - Define the replay and bounded persistence contract

[Task Description]
Create the exact design contract for streaming replay, bounded replay staging, replay modes, quota handling, and sink-pressure behavior. This is the foundational modeling task for persistence discipline.

[Task technical implementation]
Create one new replay contract document and one code-facing contract section that define exactly:

### Replay contract

- what authoritative events are eligible for replay capture,
- how replay ordering maps to authoritative execution,
- how streaming emission works,
- how chunks are defined and rotated,
- and how replay remains non-authoritative.

### Replay mode contract

- `OFF`
- `MINIMAL`
- `DEBUG_WINDOWED`
- `FORENSIC_SHORT_RUN`

For each mode, define:

- what is captured,
- what is omitted,
- what in-memory window is allowed,
- and what profile restrictions apply.

### Persistence-pressure contract

- disk-budget behavior,
- sink slowdown behavior,
- bounded staging behavior,
- overflow behavior,
- and interaction with governor-controlled degradation.

### Non-goals

- no remote transport,
- no distributed replay storage,
- no concurrency-aware replay pipelines,
- no full observability system,
- no certification harness.

[Task possible affected files]

- `docs/engine/replay_contract_m6.md`
- replay contract module
- replay mode enum/module
- persistence-pressure policy module

[Task important notes]
Do not write this as generic persistence prose. The contract must be exact enough to drive implementation and tests.

Do not leave mode behavior vague.

[Task check list]

- [ ] Define replay capture semantics
- [ ] Define replay ordering semantics
- [ ] Define chunking and rotation semantics
- [ ] Define replay mode behavior
- [ ] Define bounded staging/window semantics
- [ ] Define quota and sink-pressure behavior
- [ ] Define explicit non-goals

[Task acceptance criteria]
The project has one exact replay and bounded-persistence contract that can be used as the authoritative source for implementation and tests.

---

[ ] (checkbox) - [Task 2] - Implement the streaming replay core and chunk rotation

[Task Description]
Make the codebase obey the frozen replay contract by implementing one exact streaming replay path and one exact chunk lifecycle.

[Task technical implementation]
Implement or refactor the replay layer so that:

1. **Streaming emission**
   - replay events are emitted incrementally,
   - no whole-run in-memory replay build is required,
   - and replay writes remain bounded by staging rules.

2. **Chunk lifecycle**
   - new chunk creation follows exact rules,
   - chunk rotation follows exact size/tick/time rules,
   - closed chunks become immutable artifacts,
   - and manifest/index information is updated deterministically if part of the contract.

3. **Replay ordering**
   - replay event order follows authoritative execution order,
   - repeated identical runs produce the same replay ordering under the same mode.

[Task possible affected files]

- `src/engine/replay.py`
- replay chunk writer module
- replay rotation module
- replay manifest/index module if used
- authoritative event-to-replay extraction module

[Task important notes]
Do not let replay emission own authoritative state.

Do not introduce giant serialization steps that rebuild whole object graphs unnecessarily.

[Task check list]

- [ ] Implement incremental replay emission
- [ ] Implement replay chunk creation
- [ ] Implement deterministic chunk rotation
- [ ] Implement closed-chunk immutability behavior
- [ ] Implement deterministic replay ordering
- [ ] Keep replay non-authoritative

[Task acceptance criteria]
The engine has one exact streaming replay core that emits bounded replay data incrementally and rotates chunks deterministically.

---

[ ] (checkbox) - [Task 3] - Implement bounded staging, replay modes, and sink-pressure behavior

[Task Description]
Make replay obey bounded-memory and profile-driven persistence rules under normal and pressured conditions.

[Task technical implementation]
Implement exact behavior for:

1. **Bounded replay staging/window**
   - explicit in-memory window size or equivalent bound,
   - explicit overflow behavior,
   - deterministic trimming or eviction behavior if applicable.

2. **Replay modes**
   - `OFF`
   - `MINIMAL`
   - `DEBUG_WINDOWED`
   - `FORENSIC_SHORT_RUN`

Each mode must enforce:

- exact capture richness,
- exact retention/window behavior,
- exact constraints under the active runtime profile.

3. **Sink-pressure and disk-budget behavior**
   - explicit handling when write sink slows down,
   - explicit handling when budget is approached or exceeded,
   - correct interaction with governor-controlled degradation,
   - and no unauthorized impact on authoritative execution.

[Task possible affected files]

- replay staging/window module
- replay mode enforcement module
- disk-budget handling module
- sink-pressure handling module
- governor integration module for degradable replay behavior

[Task important notes]
Do not allow replay to silently accumulate backlog under sink pressure.

Do not allow replay mode behavior to drift outside the profile contract.

[Task check list]

- [ ] Implement bounded replay staging
- [ ] Implement replay-window overflow behavior
- [ ] Implement replay mode enforcement
- [ ] Implement disk-budget handling
- [ ] Implement sink-pressure behavior
- [ ] Integrate replay degradation with governor rules
- [ ] Preserve authoritative execution safety

[Task acceptance criteria]
Replay staging remains bounded, replay modes behave exactly as declared, and sink-pressure behavior stays within contract without corrupting core simulation semantics.

---

[ ] (checkbox) - [Task 4] - Add deterministic replay and bounded-persistence tests

[Task Description]
Lock the Milestone 6 replay rules with deterministic tests so later milestones cannot silently reintroduce in-memory accumulation or uncontrolled persistence cost.

[Task technical implementation]
Add exact tests for:

### Replay contract tests

- replay output is non-authoritative,
- replay ordering follows authoritative event order,
- repeated identical runs with the same mode produce identical replay ordering.

### Chunking and staging tests

- chunk rotation occurs exactly when declared,
- bounded in-memory staging remains within declared limits,
- staging overflow follows exact behavior,
- closed chunks remain immutable.

### Replay mode tests

- `OFF` disables capture correctly,
- `MINIMAL` captures only declared minimum,
- `DEBUG_WINDOWED` respects declared window,
- `FORENSIC_SHORT_RUN` obeys declared restrictions.

### Pressure and budget tests

- sink slowdown follows declared behavior,
- disk-budget thresholds trigger declared behavior,
- replay degradation follows governor policy,
- replay pressure never mutates authoritative state.

### Suggested test groups

- `tests/engine/test_replay_contract.py`
- `tests/engine/test_replay_chunk_rotation.py`
- `tests/engine/test_replay_modes.py`
- `tests/engine/test_replay_pressure_behavior.py`

[Task possible affected files]

- new replay contract test modules
- new chunk/staging test modules
- new replay mode and pressure test modules

[Task important notes]
These are replay and bounded-persistence tests, not concurrency tests and not final resilience certification tests.

Do not add distributed storage cases in this milestone.

[Task check list]

- [ ] Add replay non-authoritative tests
- [ ] Add replay ordering tests
- [ ] Add chunk rotation tests
- [ ] Add bounded staging tests
- [ ] Add replay mode tests
- [ ] Add sink-pressure tests
- [ ] Add disk-budget tests

[Task acceptance criteria]
The replay and bounded-persistence contracts are pinned by deterministic tests proving correct ordering, correct chunking, correct bounded staging, correct mode behavior, and correct pressure handling.

---

[ ] (checkbox) - [Task 5] - Add exact Milestone 6 documentation pack

[Task Description]
Document the complete Milestone 6 replay and bounded-persistence model so later milestones cannot reinterpret persistence behavior informally.

[Task technical implementation]
Create:

- `docs/engine/replay_contract_m6.md`
- `docs/engine/m6_replay_mode_matrix.md`
- `docs/engine/m6_test_matrix.md`

`replay_contract_m6.md` must contain these exact sections:

- Purpose
- Replay scope
- Non-authoritative replay semantics
- Replay capture semantics
- Replay ordering semantics
- Streaming write semantics
- Chunking and rotation semantics
- Staging/window semantics
- Sink-pressure and budget semantics
- Non-goals
- Safety guarantees

`m6_replay_mode_matrix.md` must contain these exact sections:

- Replay mode
- Capture richness
- Window/staging behavior
- Profile constraints
- Degradation behavior
- Forbidden behavior
- Regression risk if violated

`m6_test_matrix.md` must contain these exact sections:

- Replay contract tests
- Replay ordering tests
- Chunk rotation tests
- Staging and overflow tests
- Replay mode tests
- Pressure and budget tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/replay_contract_m6.md`
- `docs/engine/m6_replay_mode_matrix.md`
- `docs/engine/m6_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer replay-mode and pressure documentation until later observability exists.

[Task check list]

- [ ] Document exact replay rules
- [ ] Document exact replay-mode behavior
- [ ] Document exact chunking and staging rules
- [ ] Document exact pressure and budget behavior
- [ ] Document forbidden replay behavior
- [ ] Document the deterministic test matrix

[Task acceptance criteria]
Milestone 6 has a complete exact documentation pack describing streaming replay, bounded persistence, replay modes, pressure behavior, and the deterministic test matrix that freezes them.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of replay as free debugging convenience. Replay is a bounded, profile-controlled runtime cost and must be treated like one.

What actions must be taken immediately
Freeze the replay contract, implement incremental replay emission and deterministic chunk rotation, bound all replay staging, define exact replay modes, and pin the whole model with deterministic tests.

What must stop or be eliminated
Stop whole-run replay accumulation. Stop vague replay-richness defaults. Stop sink-pressure behavior that quietly backs up into memory. Stop any design that lets replay become an alternate state source.

The consequences and opportunity cost if this fails
Later milestones will inherit persistence behavior that can still destabilize long runs, and you will waste time building observability, concurrency, and certification around a replay system that was never made safe at the structural level.
