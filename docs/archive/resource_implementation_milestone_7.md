---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

[Milestone 7] - Observability and Operational Controls

[Milestone Description]
Milestone 7 is the first runtime-visibility milestone of the new engine. Its purpose is **not** to introduce concurrency yet, and it is **not** to build the final resilience certification harness yet. Its purpose is to make the engine inspectable and operable under bounded resource profiles without turning observability itself into a new resource hazard.

This milestone must lock the engine’s first runtime-visibility laws:

- what runtime signals are exposed,
- which metrics and state transitions are operationally important,
- how runtime profiles are surfaced,
- how unsafe startup configurations are rejected,
- how graceful shutdown behaves,
- and how observability remains subordinate to the resource envelope.

The previous milestones froze the kernel, bounded the state model, defined the work model, introduced the governor, and made replay bounded. This milestone turns those foundations into one exact visibility and control surface so test runs and deployments can be inspected and operated without guesswork.

[Milestone technical implementation]
Create one exact observability contract and one exact operational-control model and make the runtime obey them.

This milestone must implement these exact rules:

### Observability rules

1. **Profile-aware observability**
   - Observability behavior must obey the active runtime profile.
   - Metrics, traces, and runtime signals must not exceed profile-defined observability budgets.
   - Richer diagnostics must remain optional and degradable.

2. **Required runtime signals**
   - The engine must expose exact signals for at least:
     - current runtime profile,
     - current runtime mode,
     - memory usage and memory trend,
     - tick duration,
     - scheduler/work latency,
     - queue depth,
     - deferred-work pressure,
     - replay backlog or replay pressure where applicable,
     - dropped or reduced optional work,
     - and degradation transitions.

3. **Deterministic surfaced state**
   - Surfaced runtime signals must be stable in meaning and naming.
   - Identical engine conditions must produce consistent surfaced state.
   - Observability must not distort authoritative behavior.

4. **Observability remains non-authoritative**
   - Metrics, logs, traces, and surfaced diagnostics are explicitly non-authoritative.
   - Observability failures must not mutate or redefine simulation semantics.
   - Observability cost must remain subordinate to core execution.

### Operational-control rules

5. **Startup config validation**
   - The engine must validate runtime configuration and profile compatibility at startup.
   - Unsafe, contradictory, or out-of-contract configurations must be rejected before execution begins.
   - Validation rules must be explicit and testable.

6. **Safe runtime profiles**
   - The engine must expose named runtime profiles as first-class operational choices.
   - Profile selection must be surfaced clearly at runtime.
   - Profile identity must be inspectable for tests, CI, and deployment.

7. **Graceful shutdown behavior**
   - Shutdown behavior must be explicit.
   - Shutdown must preserve authoritative integrity.
   - Non-authoritative work may be flushed, truncated, or omitted only according to declared contract.
   - Shutdown under pressure must remain deterministic and controlled.

8. **Feature-flag boundaries**
   - Optional subsystems may be controlled through explicit operational flags only if those flags remain inside the profile and governor contract.
   - Flags must not create hidden alternate semantics.

### Runtime contract boundaries

9. **Non-goals of this milestone**
   - Do not implement concurrency here.
   - Do not implement final resilience certification here.
   - Do not implement distributed observability infrastructure here.
   - Do not implement broker-level operational controls here.
   - Do not allow observability to become a shadow replay system.

10. **Clean-code boundary**

- Metric extraction, runtime-state surfacing, startup validation, graceful shutdown behavior, and feature-flag handling must be separated into explicit responsibilities.
- Do not bury operational truth in ad hoc logging.
- Do not allow observability-specific code to define kernel behavior.

[Milestone important notes]
The first trap in this milestone is treating observability as something you “add later if needed.” That is how teams end up debugging by superstition.

The second trap is allowing observability cost to grow without bound because it feels operationally useful. That is how diagnostics become part of the problem.

The third trap is weak startup validation. If the engine allows contradictory profile settings or unsafe combinations at startup, the runtime is already lying before the first tick.

The fourth trap is graceful shutdown theater. If shutdown rules are vague, then shutdown under pressure will corrupt expectations exactly when you need control.

[Milestone acceptance criteria]
At the end of Milestone 7, the codebase has:

- one exact observability contract,
- one exact operational-control model,
- one exact startup-validation model,
- one exact graceful-shutdown model,
- one deterministic test suite proving surfaced signals and controls behave correctly,
- and one exact documentation pack stating these rules without ambiguity.

No concurrency, distributed control plane, or final resilience certification harness is required for Milestone 7 completion.

## Task

[x] (checkbox) - [Task 1] - Define the observability and operational-control contract

[Task Description]
Create the exact design contract for surfaced runtime signals, startup validation, runtime profile surfacing, graceful shutdown, and operational flags. This is the foundational modeling task for inspectable and controllable runtime behavior.

[Task implementation comments]
Defined the core observability laws in `docs/engine/observability_contract_m7.md`. The contract established the requirement for structured `ActionReason` payloads and mandatory telemetry for memory and work debt.

[Task technical implementation]
Create one new observability contract document and one code-facing contract section that define exactly:

### Observability contract

- which runtime signals are required,
- what each surfaced field means,
- how observability remains non-authoritative,
- how observability obeys profile budgets,
- and what degradation rules apply to observability richness.

### Operational-control contract

- startup validation rules,
- runtime profile surfacing rules,
- graceful shutdown behavior,
- optional flag boundaries,
- and forbidden operational behaviors.

### Non-goals

- no concurrency observability,
- no distributed tracing backend design,
- no final resilience certification,
- no remote operations plane.

[Task possible affected files]

- `docs/engine/observability_contract_m7.md`
- observability contract module
- startup validation module
- graceful shutdown contract module
- runtime profile surfacing module

[Task important notes]
Do not write this as generic ops prose. The contract must be exact enough to drive code and tests from it.

Do not leave any surfaced signal vague.

[Task check list]

- [x] Define required runtime signals
- [x] Define observability budget rules
- [x] Define startup-validation rules
- [x] Define runtime-profile surfacing rules
- [x] Define graceful shutdown rules
- [x] Define operational flag boundaries
- [x] Define explicit non-goals

[Task acceptance criteria]
The project has one exact observability and operational-control contract that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Implement surfaced runtime signals and startup validation

[Task Description]
Make the codebase obey the frozen observability and operational-control contract by implementing one exact surfaced-state path and one exact startup-validation path.

[Task implementation comments]
Surfaced signals are implemented as typed presenters in `src/api/presenters.py`. Startup validation for runtime profiles is enforced by `src/config/validator.py`, which rejects mismatched envelope settings before the tick loop begins.

[Task technical implementation]
Implement or refactor the runtime so that:

1. **Surfaced runtime signals**
   - required metrics and state indicators are exposed,
   - naming and semantics are stable,
   - surfaced state includes runtime profile and runtime mode,
   - and observability remains non-authoritative.

2. **Startup validation**
   - validates profile configuration,
   - rejects contradictory or unsafe settings,
   - and fails before runtime execution begins when config is out of contract.

3. **Profile-aware observability**
   - surfaced diagnostics obey profile-defined budgets and degradation rules,
   - and optional diagnostic richness remains under governor control.

[Task possible affected files]

- `src/engine/observability.py`
- `src/engine/runtime_status.py`
- `src/config/validation.py`
- profile integration module
- governor integration module

[Task important notes]
Do not turn surfaced-state generation into a heavy object-graph serializer.

Do not allow startup validation to be partial or best-effort.

[Task check list]

- [x] Implement surfaced runtime signals
- [x] Surface current profile and runtime mode
- [x] Implement stable signal naming and meaning
- [x] Implement startup validation
- [x] Enforce profile-aware observability limits
- [x] Preserve non-authoritative observability boundaries

[Task acceptance criteria]
The engine exposes the required runtime signals consistently and rejects unsafe or contradictory startup configurations before execution.

---

[x] (checkbox) - [Task 3] - Implement graceful shutdown and operational flag handling

[Task Description]
Make runtime shutdown and operational controls obey exact contract behavior rather than ad hoc process behavior.

[Task implementation comments]
Graceful shutdown is coordinated by the `Kernel` in `src/engine/kernel.py`, ensuring all in-memory replay chunks are flushed to the persistence sink. Operational flags for feature rollout are managed via the `Governor` to ensure they respect active mode constraints.

[Task technical implementation]
Implement exact behavior for:

1. **Graceful shutdown**
   - explicit shutdown sequence,
   - preservation of authoritative integrity,
   - exact handling of non-authoritative buffers,
   - exact flush or truncate behavior according to contract.

2. **Shutdown under pressure**
   - behavior remains deterministic and controlled,
   - shutdown does not bypass safety boundaries,
   - optional work handling follows declared shutdown rules.

3. **Operational flags**
   - feature or mode flags are applied through explicit validated pathways,
   - flags cannot alter authoritative semantics implicitly,
   - and flags remain subordinate to profile and governor rules.

[Task possible affected files]

- graceful shutdown module
- replay integration module
- observability integration module
- flag/config application module

[Task important notes]
Do not let shutdown semantics depend on incidental process teardown.

Do not let feature flags become a second configuration system with looser rules.

[Task check list]

- [x] Implement explicit shutdown sequence
- [x] Implement shutdown handling for non-authoritative buffers
- [x] Implement deterministic shutdown-under-pressure behavior
- [x] Implement validated operational flag handling
- [x] Preserve authoritative integrity on shutdown
- [x] Keep flags subordinate to profile and governor rules

[Task acceptance criteria]
Shutdown and operational flag behavior are explicit, validated, and safe, and do not alter authoritative semantics implicitly.

---

[x] (checkbox) - [Task 4] - Add deterministic observability and operational-control tests

[Task Description]
Lock the Milestone 7 visibility and control rules with deterministic tests so later milestones cannot silently turn observability into instability or operational controls into guesswork.

[Task implementation comments]
Observability tests in `tests/engine/test_observability_contract.py` verify that structured reasons are correctly populated for both success and failure paths. Graceful shutdown tests ensure bit-identical replay output after a controlled termination.

[Task technical implementation]
Add exact tests for:

### Observability tests

- required runtime signals are exposed,
- surfaced signal meanings remain stable,
- profile and mode surfacing work correctly,
- observability remains non-authoritative.

### Startup validation tests

- valid configurations are accepted,
- contradictory or unsafe configurations are rejected,
- invalid profile combinations fail before execution starts.

### Graceful shutdown tests

- shutdown preserves authoritative integrity,
- non-authoritative buffers follow declared shutdown behavior,
- shutdown under pressure follows declared rules.

### Operational flag tests

- flags are validated,
- flags cannot bypass profile constraints,
- flags cannot create hidden semantic changes.

### Suggested test groups

- `tests/engine/test_observability_contract.py`
- `tests/config/test_startup_validation.py`
- `tests/engine/test_graceful_shutdown.py`
- `tests/engine/test_operational_flags.py`

[Task possible affected files]

- new observability contract test modules
- new startup validation test modules
- new shutdown and flag-behavior test modules

[Task important notes]
These are observability and operational-control tests, not final resilience certification tests.

Do not add distributed runtime cases in this milestone.

[Task check list]

- [x] Add surfaced-signal tests
- [x] Add profile and mode surfacing tests
- [x] Add startup-validation tests
- [x] Add graceful-shutdown tests
- [x] Add shutdown-under-pressure tests
- [x] Add operational-flag boundary tests

[Task acceptance criteria]
The observability and operational-control contracts are pinned by deterministic tests proving stable signal exposure, correct startup validation, correct shutdown behavior, and safe flag handling.

---

[x] (checkbox) - [Task 5] - Add exact Milestone 7 documentation pack

[Task Description]
Document the complete Milestone 7 observability and operational-control model so later milestones cannot reinterpret runtime visibility and control behavior informally.

[Task implementation comments]
Finalized the Observability Contract and Operational Control Matrix. Documented the `ReasonCode` taxonomy used by the structured reason system.

[Task technical implementation]
Create:

- `docs/engine/observability_contract_m7.md`
- `docs/engine/m7_operational_controls_matrix.md`
- `docs/engine/m7_test_matrix.md`

`observability_contract_m7.md` must contain these exact sections:

- Purpose
- Observability scope
- Required runtime signals
- Profile-aware observability rules
- Non-authoritative observability semantics
- Startup-validation rules
- Graceful shutdown rules
- Operational flag boundaries
- Non-goals
- Safety guarantees

`m7_operational_controls_matrix.md` must contain these exact sections:

- Control or surfaced signal
- Purpose
- Authoritative vs non-authoritative status
- Profile constraints
- Degradation behavior
- Forbidden behavior
- Regression risk if violated

`m7_test_matrix.md` must contain these exact sections:

- Observability contract tests
- Startup-validation tests
- Graceful-shutdown tests
- Operational flag tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/observability_contract_m7.md`
- `docs/engine/m7_operational_controls_matrix.md`
- `docs/engine/m7_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer operational documentation until after certification exists.

[Task check list]

- [x] Document exact observability rules
- [x] Document exact startup-validation rules
- [x] Document exact graceful-shutdown rules
- [x] Document exact operational flag boundaries
- [x] Document forbidden operational behavior
- [x] Document the deterministic test matrix

[Task acceptance criteria]
Milestone 7 has a complete exact documentation pack describing runtime visibility, operational controls, startup validation, shutdown behavior, and the deterministic test matrix that freezes them.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of observability as optional polish. If the engine cannot expose its profile, mode, pressure, and control state clearly, every later debugging and deployment decision becomes guesswork.

What actions must be taken immediately
Freeze the observability contract, implement surfaced runtime signals, validate startup configs strictly, define graceful shutdown exactly, and pin the whole model with deterministic tests.

What must stop or be eliminated
Stop ad hoc runtime logging as a substitute for surfaced operational truth. Stop partial startup validation. Stop vague shutdown behavior. Stop any flag system that can quietly bypass profile and governor rules.

The consequences and opportunity cost if this fails
Later milestones will run on a runtime that may be bounded and governed on paper but remains opaque and operationally unsafe in practice, and you will waste time diagnosing issues that the engine never made visible in the first place.
