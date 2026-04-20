# [Milestone B] - Real Runtime Signals and Governor Hardening

## [Milestone Description]

Milestone B exists to turn runtime protection from “architecturally present” into “operationally trustworthy.”

The v2 code already has the right shape for runtime control:

- runtime profiles,
- runtime status,
- governor modes and policy,
- signal collection,
- scheduler integration points,
- and tests for degradation order and governance isolation.

That is the good news.

The bad news is that the current runtime control surface is still too dependent on estimated, simplified, or placeholder-flavored signals. In the existing code, queue utilization starts as `0.0`, some pressure values are inferred from local work counts rather than real system accounting, worker pressure is simplified, and replay pressure is estimated instead of being tracked from a stronger contract. That means the governor can still be correct in shape while being weak in truth. The v2 high-level plan explicitly calls this out as a Milestone B problem.
References: [resource_high_level_v2.md](sandbox:/mnt/data/resource_high_level_v2.md), [all_src_v2.py](sandbox:/mnt/data/all_src_v2.py)

This milestone exists to fix that.

At the end of Milestone B, the engine must not merely have a governor. It must have:

- real bounded runtime signals,
- deterministic degradation and recovery behavior,
- anti-thrashing protection,
- explicit scheduler-policy coupling,
- truthful runtime monitoring,
- and strict separation between governance state and authoritative simulation state.

This is the milestone that makes “profiles,” “monitoring,” and “system should not crash under pressure” start meaning something real.

---

## [Milestone technical implementation]

Create one fully trustworthy runtime control layer based on real bounded operational signals.

This milestone must implement these exact rules.

### Runtime signal completion rules

1. **Governor decisions must be based on real declared signals**
   - Runtime mode transitions must be driven by explicit named signals.
   - Decorative, blended, or placeholder-like metrics must not drive degradation law.
   - If a signal affects mode transitions, it must have a defined source, update rule, retention rule, and test coverage.

2. **Operational pressure must be split into explicit dimensions**
   - Queue pressure,
   - worker/inflight pressure,
   - dropped-work pressure,
   - replay pressure,
   - tick budget pressure,
   - memory pressure,
   - and work-debt pressure
     must each have explicit semantics.
   - Do not collapse unrelated pressure sources into one ambiguous “utilization” idea.

3. **Signal history must remain bounded**
   - Runtime signal collection must use bounded retention.
   - Trend calculations must be explicit and deterministic.
   - No monitoring or signal history may grow without profile-bound limits.

4. **Governor transitions must be deterministic and test-pinned**
   - NORMAL -> DEGRADED -> SURVIVAL transition rules must be explicit.
   - Recovery rules must be explicit.
   - Anti-thrashing rules must be explicit.
   - Transition timing and hysteresis must be test-pinned.

5. **Governor behavior must not contaminate authoritative state**
   - Runtime mode,
   - signal history,
   - scheduler pressure state,
   - and operational counters
     must remain non-authoritative.
   - They may influence runtime behavior, but they must not alter authoritative hash semantics directly.

6. **Policy-to-scheduler integration must be explicit**
   - If policy sheds work, the shed behavior must be declared.
   - If policy changes class selection or execution limits, that contract must be explicit.
   - Degradation must never silently redefine core simulation semantics.

7. **Runtime status must become truthful**
   - Runtime snapshots must expose real values, not decorative placeholders.
   - If a field exists in runtime monitoring, it must represent something precise.
   - If a value is estimated, that must be either eliminated or explicitly named as an estimate and kept out of law-critical logic.

### Milestone B coverage boundary

8. **What this milestone must cover**
   - runtime signal model completion,
   - governor transition law,
   - anti-thrashing and recovery law,
   - scheduler-policy integration,
   - runtime monitoring/status truthfulness,
   - governance-state isolation,
   - and real-signal test closure.

9. **Non-goals of this milestone**
   - no replay lifecycle hardening beyond the minimum needed to expose truthful pressure,
   - no deep worker-execution redesign,
   - no certification deepening,
   - no RPG domain attachment,
   - no full operational shutdown hardening,
   - no full failure-bundle/reporting system.

10. **Clean-code boundary**

- signal collection gathers facts,
- governor interprets those facts,
- scheduler/policy executes allowed runtime restrictions,
- runtime status surfaces the facts,
- authoritative state remains separate,
- and checkpointing remains authoritative-only.

---

## [Milestone important notes]

The first trap is pretending that “roughly correct signals” are good enough. They are not. A governor driven by fake or weak signals is fake safety.

The second trap is treating monitoring as cosmetic. It is not. In this engine, monitoring is part of runtime protection. If the surfaced values are not real, your degradation model is lying.

The third trap is allowing policy degradation to drift into semantic degradation. Milestone B is allowed to shed declared operational cost, but it is not allowed to quietly redefine the simulation’s core correctness contract.

The fourth trap is allowing governance state to leak into authoritative identity. The current code and tests already care about governance/hash isolation. Milestone B must preserve that separation aggressively, not just incidentally.
References: [all_tests_v2.py](sandbox:/mnt/data/all_tests_v2.py), [all_src_v2.py](sandbox:/mnt/data/all_src_v2.py)

---

## [Milestone acceptance criteria]

At the end of Milestone B, the codebase has:

- one exact runtime-signal contract,
- one fully bounded signal-history model,
- one deterministic governor transition law,
- one explicit anti-thrashing and recovery law,
- one truthful runtime-status surface,
- one explicit policy-to-scheduler integration contract,
- one proven isolation boundary between governance and authoritative state,
- and one complete real-signal test suite with no placeholder runtime-pressure semantics.

No replay finalization hardening, bounded worker deepening, certification expansion, or real RPG logic attachment is required for Milestone B completion.
References: [resource_high_level_v2.md](sandbox:/mnt/data/resource_high_level_v2.md)

---

# ## Task

---

## [ ] (checkbox) - [Task 1] - Freeze the runtime signal and governor law set

### [Task Description]

Create one exact contract for runtime pressure signals, governor transitions, recovery behavior, and scheduler-policy enforcement.

### [Task technical implementation]

Write one Milestone B contract document that defines:

- exact runtime signals,
- exact signal producers,
- exact signal update cadence,
- exact bounded-history rules,
- exact transition rules for NORMAL / DEGRADED / SURVIVAL,
- exact recovery conditions,
- exact anti-thrashing rules,
- exact scheduler-policy effects,
- exact authoritative/non-authoritative separation,
- and exact out-of-scope list.

This document must explicitly define every signal that may affect runtime mode, including:

- `memory_rss_mb`
- `memory_trend_mb_per_tick`
- `tick_compute_ms`
- `tick_compute_ms_avg`
- `queue_utilization`
- `worker_utilization`
- `work_debt`
- `replay_pressure`
- `active_workers`
- dropped-work counters
- fallback counters
- worker-failure counters
- replay-failure counters

It must also state:

- which signals are hard envelope checks,
- which signals are degradation hints,
- which signals are recovery gates,
- which signals are observational only,
- and which values must never affect authoritative hashing.

### [Task possible affected files]

- `docs/engine/runtime_signals_contract_mb.md`
- `docs/engine/mb_test_matrix.md`
- `src_v2/governance/governor.py`
- `src_v2/observability/runtime_status.py`
- `src_v2/observability/signals.py`
- nearby profile and policy docs

### [Task important notes]

Do not leave runtime signal semantics implicit in tests or code comments.
Do not let “utilization” remain a vague catch-all term.

### [Task check list]

- [ ] Freeze exact signal catalog
- [ ] Freeze signal ownership and update rules
- [ ] Freeze signal boundedness rules
- [ ] Freeze transition law
- [ ] Freeze recovery law
- [ ] Freeze anti-thrashing law
- [ ] Freeze scheduler-policy law
- [ ] Freeze governance/authoritative separation
- [ ] Freeze non-goals

### [Task acceptance criteria]

The project has one exact runtime-signal and governor contract defining the finished operational law set for Milestone B.

---

## [ ] (checkbox) - [Task 2] - Replace placeholder or weak runtime pressure signals with real bounded accounting

### [Task Description]

Turn simplified runtime metrics into real bounded operational facts.

### [Task technical implementation]

Audit every currently surfaced or consumed runtime signal and classify it as:

- already real enough,
- weak estimate,
- placeholder,
- or missing.

Then implement real accounting for at least these dimensions:

1. **Queue pressure**
   - Replace local or decorative queue approximation with explicit queue depth / queue capacity accounting.
   - If multiple queues exist conceptually, either unify them under one declared queue law or surface separate queue metrics explicitly.

2. **Worker pressure**
   - Replace simplified worker pressure inference with explicit inflight count, active worker count, and worker-capacity utilization.
   - Distinguish submitted work from inflight work and inflight work from completed work.

3. **Dropped work**
   - Add explicit counters for dropped items, shed items, or skipped work due to profile/policy pressure.
   - Differentiate:
     - intentionally deferred,
     - intentionally shed,
     - failed,
     - and not selected.

4. **Replay pressure**
   - Replace weak replay-pressure estimation with a stronger bounded accounting model.
   - At minimum, track pending event count, staged bytes or closer-size estimate, overflow count, and flush failure count.
   - If exact bytes are not yet cheap enough, use one declared bounded approximation and keep it explicit.

5. **Tick pressure**
   - Make per-tick compute accounting explicit and reproducible.
   - Preserve rolling average or trend semantics as declared bounded values.

6. **Memory pressure**
   - Ensure memory usage and trend values are updated deterministically and surfaced consistently.

### [Task possible affected files]

- `src_v2/observability/signals.py`
- `src_v2/observability/runtime_status.py`
- `src_v2/engine/kernel.py`
- `src_v2/engine/scheduler.py`
- `src_v2/engine/worker_manager.py`
- `src_v2/replay/replay.py`
- `src_v2/config/profiles.py`

### [Task important notes]

Do not solve every future production metric here.
Solve the runtime facts the governor actually depends on.

Do not keep fields that sound precise but are not.

### [Task check list]

- [ ] Audit current pressure fields
- [ ] Replace fake queue accounting
- [ ] Replace weak worker pressure accounting
- [ ] Add dropped-work accounting
- [ ] Strengthen replay pressure accounting
- [ ] Harden tick-budget signal updates
- [ ] Harden memory-trend updates
- [ ] Remove or rename ambiguous pressure fields

### [Task acceptance criteria]

Every runtime signal that affects policy or mode transitions is backed by explicit bounded accounting rather than placeholder semantics.

---

## [ ] (checkbox) - [Task 3] - Complete the bounded signal-history and trend model

### [Task Description]

Make runtime history and trend calculation deterministic, bounded, and profile-safe.

### [Task technical implementation]

Implement one bounded signal-retention model that defines:

- retention window size,
- update cadence,
- smoothing or averaging rules,
- trend computation rules,
- reset rules,
- and overflow behavior.

This must cover:

- rolling tick compute averages,
- memory trend,
- replay pressure trend if used,
- queue trend if used,
- and any governor history needed for anti-thrashing.

All histories must remain bounded by declared retention length and must not accumulate indefinitely.

If a signal uses trend logic, define:

- exact formula,
- exact sampling window,
- exact startup behavior before the window fills,
- and exact deterministic handling of missing or skipped updates.

### [Task possible affected files]

- `src_v2/observability/signals.py`
- `src_v2/observability/runtime_status.py`
- `src_v2/governance/governor.py`
- `src_v2/config/profiles.py`

### [Task important notes]

Do not let trend behavior be implicit math scattered across modules.
Do not let history buffers grow “temporarily.”

### [Task check list]

- [ ] Freeze retention window rules
- [ ] Freeze rolling average rules
- [ ] Freeze trend computation rules
- [ ] Freeze startup behavior before full window
- [ ] Freeze reset behavior
- [ ] Bound all signal histories
- [ ] Document trend semantics

### [Task acceptance criteria]

All runtime signal histories and trends are deterministic, bounded, and fully defined by one explicit contract.

---

## [ ] (checkbox) - [Task 4] - Harden governor transition, hysteresis, and anti-thrashing behavior

### [Task Description]

Turn the governor from simple threshold switching into a trustworthy runtime control layer.

### [Task technical implementation]

Review and harden the transition logic so that:

1. **Transition thresholds are exact**
   - Define exact entry conditions for NORMAL -> DEGRADED.
   - Define exact entry conditions for DEGRADED -> SURVIVAL.
   - Define exact recovery conditions for SURVIVAL -> DEGRADED and DEGRADED -> NORMAL.

2. **Hysteresis is exact**
   - Recovery thresholds must not equal degradation thresholds if that causes oscillation.
   - Cooling or minimum-stay rules must be explicit if used.
   - Recovery must require declared evidence, not just one lucky sample.

3. **Multi-signal interaction is exact**
   - Define how memory, queue, worker, debt, and replay signals combine.
   - Define whether any signals are hard-fail vs soft-pressure vs recovery-only.

4. **Mode progression remains monotonic under rising pressure**
   - No invalid jumps.
   - No silent recovery while pressure is still above threshold.
   - No SURVIVAL entry without declared qualifying pressure.

5. **Anti-thrashing is explicit**
   - Add a deterministic stabilization rule:
     - minimum hold period,
     - rolling confirmation,
     - or equivalent exact mechanism.

### [Task possible affected files]

- `src_v2/governance/governor.py`
- `src_v2/governance/models.py`
- `src_v2/observability/signals.py`
- governor-related tests

### [Task important notes]

Do not hide anti-thrashing inside ad hoc conditionals.
Do not make recovery “feel right.” Define it exactly.

### [Task check list]

- [ ] Freeze degradation entry rules
- [ ] Freeze recovery exit rules
- [ ] Freeze hysteresis rules
- [ ] Freeze multi-signal interaction rules
- [ ] Freeze SURVIVAL admission law
- [ ] Add deterministic anti-thrashing behavior
- [ ] Document exact transition semantics

### [Task acceptance criteria]

Governor transition and recovery behavior are deterministic, bounded, and robust against oscillation.

---

## [ ] (checkbox) - [Task 5] - Make scheduler-policy integration exact and non-semantic

### [Task Description]

Ensure degradation policy changes runtime cost, not simulation truth.

### [Task technical implementation]

Define and implement exact policy effects for each mode.

For each runtime mode, specify:

- which work classes remain mandatory,
- which work classes may be deferred,
- which work classes may be shed,
- what execution limits apply,
- and how that affects queueing, debt, and dropped-work counters.

The integration must be explicit between:

- governor mode,
- scheduler selection,
- deferred-work handling,
- periodic-work handling,
- runtime status accounting,
- and debt/drain reporting.

This task must ensure:

1. **Policy never silently changes core semantics**
   - core authoritative law remains intact,
   - only declared operational cost is shed.

2. **Deferral and shedding are distinguishable**
   - deferred work is not the same as dropped work,
   - skipped work under policy is not the same as not-yet-due work.

3. **Mode-specific scheduling remains deterministic**
   - same inputs + same signals + same profile -> same selected work plan.

4. **All policy effects are surfaced operationally**
   - if policy causes work shedding or deferral, runtime status must show it.

### [Task possible affected files]

- `src_v2/engine/scheduler.py`
- `src_v2/governance/governor.py`
- `src_v2/core/work.py`
- `src_v2/observability/runtime_status.py`
- related scheduler/governor tests

### [Task important notes]

Do not let scheduler semantics drift silently under governor pressure.
If the governor changes runtime behavior, that must be one declared law.

### [Task check list]

- [ ] Freeze policy effect per mode
- [ ] Distinguish deferred vs dropped vs not-selected
- [ ] Freeze deterministic selection under pressure
- [ ] Surface policy effects in runtime status
- [ ] Add scheduler-policy boundary tests
- [ ] Document operational shedding law

### [Task acceptance criteria]

Scheduler behavior under governor policy is explicit, deterministic, and operationally visible without redefining authoritative semantics.

---

## [ ] (checkbox) - [Task 6] - Harden governance-state isolation from authoritative state and checkpoints

### [Task Description]

Prove that runtime control state influences behavior without contaminating authoritative identity.

### [Task technical implementation]

Audit all governance and runtime-status structures and ensure they remain external to authoritative checkpoint material.

This must cover:

- runtime mode,
- signal histories,
- replay pressure counters,
- queue metrics,
- worker metrics,
- dropped-work counters,
- fallback counters,
- any anti-thrashing state,
- and any operational snapshot metadata.

Then add or harden tests proving that:

- changes in runtime mode do not change authoritative hash by themselves,
- changes in signal history do not change authoritative hash,
- changes in monitoring metadata do not change authoritative hash,
- policy state changes without authoritative impact do not alter checkpoint material.

If any current field is mixing operational and authoritative meaning, split it now.

### [Task possible affected files]

- `src_v2/core/state.py`
- `src_v2/engine/checkpoint.py`
- `src_v2/governance/governor.py`
- `src_v2/observability/runtime_status.py`
- `tests_v2/engine/test_governance_isolation.py`
- `tests_v2/engine/test_checkpoint_purity.py`

### [Task important notes]

Do not trust separation because “the tests currently pass.”
Audit field ownership explicitly.

### [Task check list]

- [ ] Audit all governance/runtime fields
- [ ] Separate any mixed-authority field
- [ ] Prove mode isolation from hash
- [ ] Prove signal-history isolation from hash
- [ ] Prove monitoring-state isolation from hash
- [ ] Document governance-isolation law

### [Task acceptance criteria]

Governance and operational state are fully isolated from authoritative checkpoint identity.

---

## [ ] (checkbox) - [Task 7] - Complete the truthful runtime-status and monitoring surface

### [Task Description]

Make runtime observability operationally useful instead of ornamental.

### [Task technical implementation]

Define one exact runtime-status model for headless and system-level monitoring that surfaces at least:

- current profile,
- current mode,
- current tick,
- memory rss,
- memory trend,
- tick compute time,
- tick rolling average,
- queue utilization,
- worker utilization,
- active workers,
- current work debt,
- deferred-work count,
- dropped-work count,
- fallback count,
- replay backlog,
- replay drop count,
- replay flush failure count,
- worker failure count,
- last mode transition,
- last authoritative hash if available,
- and any profile envelope breach markers.

For each field:

- define source,
- define update cadence,
- define whether it is instantaneous, rolling, or cumulative,
- define reset behavior,
- and define whether it is required in test assertions.

Also add one headless runtime snapshot output path suitable for:

- end-to-end tests,
- scenario monitoring,
- and later certification integration.

### [Task possible affected files]

- `src_v2/observability/runtime_status.py`
- `src_v2/observability/signals.py`
- `src_v2/engine/kernel.py`
- `src_v2/certification/harness.py`
- headless test utilities

### [Task important notes]

Do not add dozens of fancy metrics.
Add the small set of fields the engine actually needs to tell the truth under pressure.

### [Task check list]

- [ ] Freeze runtime-status field set
- [ ] Define source and cadence for every field
- [ ] Separate instant vs rolling vs cumulative values
- [ ] Add headless runtime snapshot output
- [ ] Add runtime-status truth tests
- [ ] Document monitoring semantics

### [Task acceptance criteria]

The engine exposes one truthful runtime-status surface that is usable for monitoring, tests, and later certification work.

---

## [ ] (checkbox) - [Task 8] - Complete the real-signal and governor behavior test suite

### [Task Description]

Pin Milestone B with exact tests so the runtime-control layer stops depending on trust and intuition.

### [Task technical implementation]

Complete or add tests for these groups.

### Signal truth tests

- queue utilization reflects declared queue state,
- worker utilization reflects declared inflight/capacity state,
- replay pressure reflects declared replay state,
- dropped-work counters distinguish dropped vs deferred vs not-selected,
- runtime-status fields update at the declared cadence.

### Boundedness tests

- signal history remains bounded,
- rolling averages do not grow unbounded,
- trend windows behave correctly before full warm-up,
- reset behavior is deterministic.

### Governor transition tests

- NORMAL -> DEGRADED under declared pressure,
- DEGRADED -> SURVIVAL under declared pressure,
- invalid SURVIVAL entry is rejected,
- monotonic degradation order is preserved,
- deterministic recovery to NORMAL is proven under declared recovery conditions.

### Anti-thrashing tests

- noisy signals do not cause mode flapping,
- recovery requires sufficient stability,
- hold periods or hysteresis windows behave exactly.

### Scheduler-policy integration tests

- policy-shed behavior is visible,
- deferred and dropped work are accounted distinctly,
- scheduler behavior under each mode is deterministic,
- no-governance-state contamination of authoritative hash.

### Suggested test groups

- `tests_v2/governance/test_signal_truth.py`
- `tests_v2/governance/test_signal_boundedness.py`
- `tests_v2/governance/test_governor_transitions.py`
- `tests_v2/governance/test_governor_antithrashing.py`
- `tests_v2/governance/test_scheduler_policy_integration.py`
- `tests_v2/engine/test_governance_isolation.py`
- `tests_v2/observability/test_runtime_status.py`

### [Task possible affected files]

- existing governance, observability, and runtime-status tests
- any missing new Milestone B test modules

### [Task important notes]

Do not use broad end-to-end certification tests as a substitute here.
Milestone B needs direct signal-law proof.

### [Task check list]

- [ ] Add signal-truth tests
- [ ] Add signal-boundedness tests
- [ ] Add transition and recovery tests
- [ ] Add anti-thrashing tests
- [ ] Add scheduler-policy tests
- [ ] Add runtime-status truth tests
- [ ] Remove weak or decorative assertions

### [Task acceptance criteria]

The runtime-control layer is pinned by a complete real-signal and governor-law test suite.

---

## [ ] (checkbox) - [Task 9] - Refactor signal collection, governance, and runtime status into clean responsibility boundaries

### [Task Description]

Reduce cross-module ambiguity so Milestone B hardening does not produce operational spaghetti.

### [Task technical implementation]

Refactor the runtime-control path so responsibilities are explicit:

- signal collection gathers and updates bounded metrics,
- governor evaluates metrics and determines mode,
- scheduler applies declared policy effects,
- runtime status surfaces state,
- kernel orchestrates without absorbing the logic.

Move scattered runtime-pressure logic out of ad hoc kernel conditionals where appropriate.

Ensure that:

- signal math is not duplicated across modules,
- mode transitions are not partly computed in one place and partly in another,
- runtime-status snapshots do not recompute business logic,
- and monitoring does not mutate or reinterpret authoritative state.

### [Task possible affected files]

- `src_v2/engine/kernel.py`
- `src_v2/governance/governor.py`
- `src_v2/observability/signals.py`
- `src_v2/observability/runtime_status.py`
- scheduler-related modules

### [Task important notes]

Do not over-abstract this into a framework.
Just remove responsibility leakage.

### [Task check list]

- [ ] Audit signal/governor/status responsibilities
- [ ] Remove duplicated signal logic
- [ ] Keep mode transitions centralized
- [ ] Keep runtime-status reporting read-only
- [ ] Preserve deterministic behavior during refactor
- [ ] Document final responsibility boundaries

### [Task acceptance criteria]

Milestone B ends with one clean runtime-control architecture rather than scattered pressure logic.

---

## [ ] (checkbox) - [Task 10] - Add exact Milestone B documentation pack

### [Task Description]

Document the finished runtime-control law set so later milestones treat Milestone B as completed operational law, not evolving guesswork.

### [Task technical implementation]

Create:

- `docs/engine/runtime_signals_contract_mb.md`
- `docs/engine/mb_test_matrix.md`

`runtime_signals_contract_mb.md` must contain these exact sections:

- Purpose
- Scope of Milestone B
- Runtime signal catalog
- Signal ownership and update cadence
- Bounded history and trend law
- Governor transition law
- Recovery and anti-thrashing law
- Scheduler-policy integration law
- Governance isolation law
- Runtime-status surface
- Non-goals
- Completion guarantees

`mb_test_matrix.md` must contain these exact sections:

- Signal truth tests
- Signal boundedness tests
- Governor transition tests
- Anti-thrashing tests
- Scheduler-policy tests
- Governance isolation tests
- Runtime-status truth tests
- Regression intent

For every test group, document:

- test name or group,
- input condition,
- exact expected runtime rule,
- regression caught,
- whether it is signal, control, boundary, or isolation coverage.

### [Task possible affected files]

- `docs/engine/runtime_signals_contract_mb.md`
- `docs/engine/mb_test_matrix.md`

### [Task important notes]

Documentation is part of implementation here too.
Do not finish Milestone B with only code and green tests.

### [Task check list]

- [ ] Document signal catalog
- [ ] Document bounded history and trend law
- [ ] Document governor transition law
- [ ] Document anti-thrashing law
- [ ] Document scheduler-policy law
- [ ] Document governance isolation law
- [ ] Document runtime-status semantics
- [ ] Document exact test matrix

### [Task acceptance criteria]

Milestone B has a complete documentation pack describing the finished runtime-control law and its proof matrix.

---

## [ ] (checkbox) - [Task 11] - Add Milestone B regression guardrails

### [Task Description]

Make it hard for operational truth to silently decay after Milestone B is declared complete.

### [Task technical implementation]

Add project-level guardrails that fail if:

- a runtime-law signal becomes placeholder-like again,
- a governor transition test group is skipped or renamed without doc update,
- runtime-status fields drift from the contract,
- bounded history becomes unbounded,
- governance state starts affecting authoritative hash,
- or anti-thrashing coverage is removed.

This can be done with:

- doc-integrity tests,
- focused governance/observability CI targets,
- lawbook consistency tests,
- lightweight placeholder guards,
- and regression assertions for bounded metrics.

### [Task possible affected files]

- `tests_v2/docs/*`
- `tests_v2/governance/test_mb_doc_integrity.py`
- CI config
- integrity helpers

### [Task important notes]

Do not create compliance theater.
Just make operational regression obvious and cheap to catch.

### [Task check list]

- [ ] Add signal-law doc/test integrity checks
- [ ] Add focused runtime-control CI target
- [ ] Add bounded-history regression guard
- [ ] Add governance-isolation regression guard
- [ ] Record Milestone B completion gate

### [Task acceptance criteria]

Milestone B cannot silently regress without failing tests or integrity checks.

---

# [Recommended execution order inside Milestone B]

1. Task 1 — Freeze the law set
2. Task 2 — Replace weak signals with real accounting
3. Task 3 — Complete bounded history and trend rules
4. Task 4 — Harden governor transition and anti-thrashing
5. Task 5 — Make scheduler-policy integration exact
6. Task 6 — Harden governance-state isolation
7. Task 7 — Complete runtime-status truth surface
8. Task 8 — Complete the real-signal test suite
9. Task 9 — Refactor responsibility boundaries
10. Task 10 — Finalize docs
11. Task 11 — Add guardrails

This order matters because it follows dependency reality:

- first define the operational law,
- then make the signals real,
- then bound the histories,
- then make transitions trustworthy,
- then enforce policy meaning,
- then prove isolation,
- then surface truth,
- then finish proof,
- then clean structure,
- then lock docs and guardrails.

---

# [Milestone B done-means-done gate]

Milestone B is done only when all of these are true:

- every mode-driving runtime signal has explicit bounded accounting,
- signal histories are bounded and deterministic,
- governor degradation and recovery are exact,
- anti-thrashing behavior is explicit and proven,
- scheduler-policy effects are deterministic and visible,
- governance state is isolated from authoritative checkpoint identity,
- runtime-status fields are truthful and defined,
- no placeholder runtime-pressure semantics remain in the control path,
- docs and tests describe the same runtime-control law,
- and CI can catch regressions in operational truth.
