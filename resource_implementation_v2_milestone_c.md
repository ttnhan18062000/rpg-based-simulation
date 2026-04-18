[Milestone C] - Replay, Startup, Shutdown, and Operational Integrity

[Milestone Description]
Milestone C is the third v2 completion milestone. Its purpose is **not** to add a replay subsystem or an observability subsystem from scratch. Its purpose is to finish the engine’s operational lifecycle so startup, persistence, runtime status, and shutdown all obey exact contract behavior.

The current code already has:

- bounded replay staging,
- replay chunk rotation,
- manifest writing,
- startup profile validation,
- operational flags,
- surfaced runtime snapshots,
- and a shutdown path.

That means the lifecycle architecture exists. The problem is that operational integrity is still incomplete:

- replay pressure behavior is not fully hardened,
- shutdown timeout semantics are not fully real,
- startup validation is structurally correct but not fully complete,
- some runtime status/reporting surfaces remain weaker than the contract language,
- and replay lifecycle guarantees are still too dependent on comments and happy-path flow.

This milestone exists to fix that.

[Milestone technical implementation]
Create one fully trustworthy operational lifecycle model and make the engine start, persist, surface status, and shut down under contract rather than best effort.

This milestone must implement these exact rules:

### Operational lifecycle completion rules

1. **Replay remains strictly non-authoritative**
   - Replay failure must never corrupt authoritative state.
   - Replay slowdown must never create unbounded accumulation.
   - Replay output must remain bounded, mode-controlled, and pressure-aware.

2. **Replay staging and overflow behavior must be exact**
   - Buffer capacity must be exact.
   - Overflow/drop behavior must be exact.
   - Sink-pressure degradation behavior must be exact.
   - Chunk rotation and manifest updates must be deterministic.

3. **Startup validation must be complete for M7/M6 scope**
   - Invalid profiles must be rejected.
   - Unsafe flag combinations must be rejected.
   - Incomplete envelope definitions must be rejected.
   - Hardware realism may be warned, not treated as certified truth here.

4. **Shutdown must become a real contract path**
   - Shutdown sequencing must be explicit.
   - Non-authoritative flushes must be bounded by time/resource limits.
   - A stuck sink must not hang the engine indefinitely.
   - Final operational cleanup must not corrupt authoritative state.

5. **Runtime snapshotting must remain bounded and trustworthy**
   - Surfaced runtime snapshots must be closed, typed, and bounded.
   - Operational status must expose only contract-defined fields.
   - No runtime snapshot may become an open-ended telemetry dump.

6. **Operational flags must remain subordinate to the contract**
   - Safe overrides may exist.
   - Forbidden overrides must remain forbidden.
   - No flag may create alternate authoritative semantics.

### Runtime contract boundaries

7. **What this milestone must cover**
   - This milestone must complete:
     - replay lifecycle behavior,
     - replay overflow/drop rules,
     - sink-pressure handling,
     - startup validation closure,
     - operational flag closure,
     - shutdown timeout behavior,
     - runtime snapshot integrity.

8. **Non-goals of this milestone**
   - Do not deepen worker packet/result contracts here.
   - Do not deepen certification scenario logic here.
   - Do not add new governor signals here beyond operational lifecycle integration.
   - Do not add new gameplay semantics here.

9. **Clean-code boundary**

- Replay staging, replay sink interaction, startup validation, runtime snapshotting, and shutdown behavior must remain separated into explicit responsibilities.
- Do not let the kernel become a catch-all operational implementation host.
- Do not let replay and runtime snapshots blur into alternate state sources.

[Milestone important notes]
The first trap in this milestone is calling replay safe because it is bounded in memory. If sink pressure, manifest integrity, or shutdown behavior are vague, replay is still operationally unsafe.

The second trap is treating startup validation as “good enough” once obvious schema mistakes are rejected. Contradictory flags and inconsistent envelopes matter too.

The third trap is pretending shutdown is solved because there is a method called `shutdown()`. If non-authoritative flushes can still stall without a real timeout path, shutdown is still best-effort theater.

The fourth trap is allowing runtime snapshots to grow by convenience. A stable operational surface is not an excuse for telemetry sprawl.

[Milestone acceptance criteria]
At the end of Milestone C, the codebase has:

- one fully hardened replay lifecycle,
- one fully exact startup validation model,
- one fully bounded runtime snapshot model,
- one fully enforced shutdown timeout path for non-authoritative flushes,
- one fully explicit operational flag boundary,
- and one deterministic test suite proving operational lifecycle safety.

No worker deepening, certification deepening, or new gameplay semantics are required for Milestone C completion.

## Task

[ ] (checkbox) - [Task 1] - Audit and freeze the operational lifecycle contract

[Task Description]
Create the exact completion contract for replay lifecycle, startup validation, runtime snapshots, operational flags, and shutdown behavior. This task turns the current mostly-correct operational layer into one finished law set.

[Task technical implementation]
Create one new operational-lifecycle contract document and one code-facing contract section that define exactly:

### Replay lifecycle contract

- replay staging bound,
- overflow/drop policy,
- replay mode behavior,
- chunk rotation law,
- manifest integrity law,
- sink-pressure law,
- non-authoritative boundary.

### Startup and flag contract

- invalid profile rejection,
- contradictory flag rejection,
- allowed safe override rules,
- warning-only hardware realism rule.

### Shutdown and snapshot contract

- exact shutdown sequence,
- exact timeout behavior for non-authoritative flushes,
- exact final authoritative checkpoint emission rule,
- exact runtime snapshot field set and boundedness.

### Non-goals

- no worker contract deepening,
- no certification deepening,
- no gameplay changes.

[Task possible affected files]

- `docs/engine/operational_integrity_contract_mc.md`
- `docs/engine/mc_test_matrix.md`
- code-facing operational contract notes near replay/validator/observability modules

[Task important notes]
Do not leave timeout behavior as a comment-level idea.

Do not leave runtime snapshot fields semantically open-ended.

[Task check list]

- [ ] Freeze replay lifecycle law
- [ ] Freeze startup validation law
- [ ] Freeze operational flag law
- [ ] Freeze shutdown timeout law
- [ ] Freeze runtime snapshot law
- [ ] Define explicit non-goals

[Task acceptance criteria]
The project has one exact operational-lifecycle contract that defines the finished law set for replay, startup, runtime snapshots, flags, and shutdown.

---

[ ] (checkbox) - [Task 2] - Harden replay staging, overflow, chunk rotation, and manifest integrity

[Task Description]
Make replay behavior fully exact under normal and pressured conditions.

[Task technical implementation]
Complete and harden:

1. **Replay staging**
   - exact bounded staging capacity,
   - exact overflow/drop policy,
   - exact ordering preservation.

2. **Chunk rotation**
   - exact size/tick/time rotation triggers,
   - deterministic chunk closure,
   - deterministic chunk naming/identity.

3. **Manifest integrity**
   - manifest updates reflect actual chunk lifecycle,
   - incomplete or failed chunk writes are represented correctly,
   - manifest remains deterministic and bounded.

4. **Sink-pressure behavior**
   - sink slowdown handling is explicit,
   - replay shedding/degradation is explicit,
   - replay pressure never causes unbounded memory growth.

[Task possible affected files]

- `src_v2/engine/replay_buffer.py`
- `src_v2/engine/replay_sink.py`
- `src_v2/engine/replay_manager.py`
- manifest-related modules

[Task important notes]
Do not let replay remain “safe in memory but vague on disk.”

Do not rely on happy-path manifest behavior.

[Task check list]

- [ ] Harden replay staging capacity and overflow behavior
- [ ] Harden deterministic chunk rotation
- [ ] Harden manifest integrity logic
- [ ] Harden sink-pressure handling
- [ ] Preserve replay non-authoritative boundary
- [ ] Document final replay lifecycle law

[Task acceptance criteria]
Replay behavior is fully bounded, deterministic, pressure-aware, and operationally trustworthy.

---

[ ] (checkbox) - [Task 3] - Complete startup validation and operational flag enforcement

[Task Description]
Make startup and runtime control behavior exact rather than partially enforced.

[Task technical implementation]
Complete and harden:

1. **Profile validation**
   - required envelope fields,
   - sane numeric bounds,
   - contradictory setting rejection,
   - replay/observability/queue consistency checks.

2. **Operational flags**
   - safe overrides remain explicit,
   - forbidden overrides remain explicit,
   - flags cannot bypass profile or governor law,
   - flags cannot create alternate authoritative semantics.

3. **Hardware realism warnings**
   - keep warning-only semantics here,
   - clearly separate warning behavior from certification truth.

[Task possible affected files]

- `src_v2/config/validator.py`
- config/profile integration modules
- operational flag handling modules

[Task important notes]
Do not creep into M9-style feasibility certification here.

Do not let “temporary ops override” become a contract hole.

[Task check list]

- [ ] Harden profile validation rules
- [ ] Harden contradictory-flag rejection
- [ ] Harden safe-override rules
- [ ] Keep hardware realism as warning-only
- [ ] Document final startup and flag law

[Task acceptance criteria]
Startup validation and flag handling are exact, bounded, and incapable of bypassing the resource contract.

---

[ ] (checkbox) - [Task 4] - Implement real shutdown timeout behavior and finalize runtime snapshot integrity

[Task Description]
Make shutdown and runtime-status surfacing behave like real contract paths rather than thin wrappers around best-effort cleanup.

[Task technical implementation]
Complete and harden:

1. **Shutdown sequence**
   - suspend new work,
   - stop or degrade non-authoritative producers,
   - attempt bounded flush of non-authoritative sinks,
   - enforce timeout on stuck flushes,
   - emit final shutdown observational event if replay is active,
   - emit final authoritative checkpoint hash as diagnostic reference.

2. **Timeout semantics**
   - timeout must be real, not commented,
   - timeout handling must be explicit,
   - timeout failure must not corrupt authoritative state.

3. **Runtime snapshots**
   - `RuntimeSnapshot` remains closed and typed,
   - all surfaced fields remain bounded and meaningful,
   - no snapshot field remains decorative or placeholder-driven.

[Task possible affected files]

- `src_v2/engine/kernel.py`
- `src_v2/engine/observability.py`
- `src_v2/engine/runtime_status.py`
- replay integration modules
- shutdown-related modules

[Task important notes]
Do not block shutdown indefinitely for non-authoritative IO.

Do not let runtime snapshots become broad telemetry bags.

[Task check list]

- [ ] Implement explicit shutdown sequence
- [ ] Implement real non-authoritative flush timeout
- [ ] Emit final authoritative checkpoint reference
- [ ] Finalize `RuntimeSnapshot` field law
- [ ] Remove any remaining decorative snapshot fields
- [ ] Document final shutdown and snapshot law

[Task acceptance criteria]
Shutdown and runtime snapshot behavior are exact, bounded, and operationally trustworthy.

---

[ ] (checkbox) - [Task 5] - Complete the operational-integrity test suite and remove lifecycle ambiguity

[Task Description]
Close the proof gap in replay, startup, flag handling, runtime snapshots, and shutdown.

[Task technical implementation]
Complete or add exact tests for:

### Replay lifecycle tests

- staging bound enforcement,
- overflow/drop behavior,
- chunk rotation,
- manifest integrity,
- sink-pressure behavior,
- replay non-authoritative isolation.

### Startup and flag tests

- invalid profile rejection,
- contradictory flag rejection,
- safe override acceptance,
- forbidden override rejection,
- warning-only hardware realism behavior.

### Shutdown and snapshot tests

- bounded shutdown flush behavior,
- timeout handling,
- final checkpoint emission,
- runtime snapshot boundedness,
- no placeholder/decorative snapshot semantics.

### Suggested test groups

- `tests_v2/config/test_startup_validation.py`
- `tests_v2/engine/test_replay_contract.py`
- `tests_v2/engine/test_replay_chunk_rotation.py`
- `tests_v2/engine/test_replay_pressure.py`
- `tests_v2/engine/test_graceful_shutdown.py`
- `tests_v2/engine/test_operational_flags.py`
- `tests_v2/engine/test_observability_budgets.py`

[Task possible affected files]

- existing replay/startup/shutdown/ops test modules
- any missing new operational-integrity tests

[Task important notes]
Do not deepen certification here.

This milestone is about making the lifecycle itself real.

[Task check list]

- [ ] Finish replay lifecycle tests
- [ ] Finish startup validation tests
- [ ] Finish operational flag tests
- [ ] Finish shutdown timeout tests
- [ ] Finish runtime snapshot integrity tests
- [ ] Prove replay and shutdown remain non-authoritative

[Task acceptance criteria]
The operational-integrity layer is pinned by a complete deterministic test suite proving replay boundedness, startup safety, flag safety, shutdown timeout behavior, and runtime snapshot integrity.

---

[ ] (checkbox) - [Task 6] - Add exact Milestone C documentation pack

[Task Description]
Document the completed operational lifecycle so later milestones treat it as finished law instead of partially hardened infrastructure.

[Task technical implementation]
Create:

- `docs/engine/operational_integrity_contract_mc.md`
- `docs/engine/mc_test_matrix.md`

`operational_integrity_contract_mc.md` must contain these exact sections:

- Purpose
- Scope of Milestone C
- Replay lifecycle law
- Manifest and sink-pressure law
- Startup validation law
- Operational flag law
- Shutdown timeout law
- Runtime snapshot law
- Non-goals
- Completion guarantees

`mc_test_matrix.md` must contain these exact sections:

- Replay lifecycle tests
- Startup validation tests
- Operational flag tests
- Shutdown timeout tests
- Runtime snapshot integrity tests
- Non-authoritative isolation tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/operational_integrity_contract_mc.md`
- `docs/engine/mc_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not end Milestone C with code and passing tests only. The lifecycle law must be written down exactly.

[Task check list]

- [ ] Document replay lifecycle law
- [ ] Document startup and flag law
- [ ] Document shutdown timeout law
- [ ] Document runtime snapshot law
- [ ] Document non-authoritative lifecycle boundaries
- [ ] Document the exact test matrix

[Task acceptance criteria]
Milestone C has a complete exact documentation pack describing the finished operational lifecycle and the tests that freeze it.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking bounded replay and a `shutdown()` method are enough. Lifecycle safety is only real when pressure, manifest integrity, timeout behavior, and snapshot truth are all fully enforced.

What actions must be taken immediately
Freeze the operational lifecycle contract, harden replay staging and manifest integrity, complete startup validation and flag rules, implement a real shutdown timeout path, and finish the lifecycle proof suite.

What must stop or be eliminated
Stop relying on comments for timeout behavior. Stop accepting partial operational truth in surfaced snapshots. Stop letting replay remain operationally vague under sink pressure. Stop treating startup validation as finished because the easy cases are rejected.

The consequences and opportunity cost if this fails
The engine may remain architecturally elegant but still fail at exactly the moments that matter most operationally: startup, pressure, persistence, and shutdown.
