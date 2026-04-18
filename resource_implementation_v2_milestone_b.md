[Milestone B] - Real Runtime Signals and Governor Hardening

[Milestone Description]
Milestone B is the second v2 completion milestone. Its purpose is **not** to add a new protection model. Its purpose is to make the existing protection model operationally real.

The current code already has:

- `PressureSignals`,
- `RuntimeMode`,
- `RuntimeStatus`,
- `ResourceGovernor`,
- `GovernorPolicy`,
- and scheduler integration for degraded behavior.

That means the architecture exists. The problem is that too many runtime signals are still incomplete, placeholder-driven, weakly surfaced, or insufficiently proven under pressure. Some observability fields are still effectively decorative, and some protection behavior is only as trustworthy as the incomplete signals feeding it.

This milestone exists to fix that.

[Milestone technical implementation]
Create one fully trustworthy runtime-pressure model and make the governor operate on real bounded signals instead of partial approximations.

This milestone must implement these exact rules:

### Runtime signal completion rules

1. **Pressure signals must become real**
   - Queue utilization must be real.
   - Work-debt totals must be real.
   - Replay pressure must be real where replay is enabled.
   - Dropped-work accounting must be real.
   - Worker/inflight utilization must be real where concurrency is active.
   - Compute-time and memory trends must remain bounded and profile-aware.

2. **No decorative operational fields**
   - Any surfaced runtime field must either:
     - be real and sourced from actual engine behavior,
     - or be removed.

   - Placeholder zeros, fake defaults, or dummy counts are forbidden after this milestone.

3. **Signal history must remain bounded**
   - Runtime signal history, trend windows, and mode-transition history must remain explicitly bounded.
   - No operational control structure may accumulate unbounded historical data.

4. **Governor decisions must be driven by explicit profile-aware signals**
   - The governor must not infer pressure from vague or synthetic proxy values where direct signals exist.
   - All pressure thresholds must be evaluated relative to the active runtime profile.

5. **Recovery and anti-thrashing behavior must be exact**
   - Watermark logic must be explicit.
   - Dwell/cooldown behavior must be explicit.
   - Near-threshold oscillation must not cause uncontrolled mode flipping.

6. **Scheduler policy integration must stay semantically clean**
   - `GovernorPolicy` must expose explicit scheduler-facing decisions.
   - The scheduler must not reinterpret raw runtime mode on its own.
   - Policy may suppress only declared degradable work.

### Runtime contract boundaries

7. **What this milestone must cover**
   - This milestone must complete:
     - real runtime signal extraction,
     - bounded signal retention,
     - governor hardening,
     - degradation-order enforcement,
     - recovery behavior proof,
     - and real policy-to-scheduler boundaries.

8. **Non-goals of this milestone**
   - Do not deepen replay lifecycle here.
   - Do not deepen startup/shutdown behavior here.
   - Do not deepen worker packet/result contracts here.
   - Do not deepen certification scenarios here.
   - Do not add new gameplay semantics here.

9. **Clean-code boundary**

- Signal collection, runtime status storage, governor evaluation, policy emission, and scheduler filtering must remain separated into explicit responsibilities.
- Do not let the kernel directly own raw signal plumbing.
- Do not let the scheduler become the place where protection semantics are improvised.

[Milestone important notes]
The first trap in this milestone is believing the governor already works because the state machine exists. A state machine fed by partial or fake inputs is not a safety system. It is theater.

The second trap is letting observability and governance blur together. The governor needs real bounded signals, but the signal surface must remain operational and non-authoritative.

The third trap is keeping placeholder fields because tests still pass. Passing tests on fake metrics is not success. It is a false sense of safety.

The fourth trap is letting policy remain implicit. The scheduler must not interpret runtime pressure on intuition. It must consume explicit policy.

[Milestone acceptance criteria]
At the end of Milestone B, the codebase has:

- one fully real runtime signal model,
- one fully bounded signal-history model,
- one fully hardened resource governor,
- one fully exact degradation-order and recovery model,
- one explicit `GovernorPolicy` boundary for scheduler integration,
- and one deterministic test suite proving protection behavior on real signals.

No replay hardening, shutdown deepening, worker contract deepening, or certification expansion is required for Milestone B completion.

## Task

[ ] (checkbox) - [Task 1] - Audit and freeze the real runtime-signal contract

[Task Description]
Create the exact completion contract for operational signals and governor-facing pressure input. This task turns the current mixed real/placeholder signal surface into one finished law set.

[Task technical implementation]
Create one new runtime-signal contract document and one code-facing contract section that define exactly:

### Runtime-signal contract

- which runtime fields are required,
- what each field means,
- what unit each field uses,
- which fields are bounded histories or rolling windows,
- and which fields are governor-critical.

### Pressure-input contract

- how memory pressure is measured,
- how compute pressure is measured,
- how queue pressure is measured,
- how replay pressure is measured,
- how worker pressure is measured where active,
- and how these inputs map to governor evaluation.

### Non-goals

- no replay lifecycle redesign,
- no shutdown redesign,
- no worker contract redesign,
- no certification redesign.

[Task possible affected files]

- `docs/engine/runtime_signal_contract_mb.md`
- `docs/engine/mb_test_matrix.md`
- code-facing signal contract notes near observability/governor modules

[Task important notes]
Do not leave units implicit.

Do not keep fields whose only real meaning is “reserved for later.”

[Task check list]

- [ ] Freeze required runtime fields
- [ ] Freeze units and semantics for each field
- [ ] Freeze bounded-history rules
- [ ] Freeze governor-critical input rules
- [ ] Define explicit non-goals

[Task acceptance criteria]
The project has one exact runtime-signal contract that defines the finished law set for operational pressure input and bounded signal history.

---

[ ] (checkbox) - [Task 2] - Replace placeholder metrics with real bounded runtime signals

[Task Description]
Make the current runtime-signal surface truthful. This task removes placeholder and dummy fields and replaces them with real bounded measurements.

[Task technical implementation]
Complete and harden:

1. **Queue utilization**
   - report actual queue depth relative to bound,
   - or remove the field if the queue is not active in the current mode.

2. **Work debt**
   - report actual total debt from authoritative deferred/debt structures,
   - with exact bounded semantics.

3. **Dropped-work accounting**
   - count shed optional work accurately,
   - keep accounting bounded,
   - expose it through `RuntimeStatus`.

4. **Replay pressure**
   - report actual replay staging pressure where replay is active,
   - keep it explicit and bounded.

5. **Worker/inflight metrics**
   - report actual worker count, inflight tasks, and queue pressure where concurrency is active,
   - or explicitly omit them when not active.

6. **Compute and memory trending**
   - use profile-controlled sampling cadence,
   - use fixed-size windows or equivalent bounded structures,
   - define explicit units such as `MB/tick` and `ms/tick avg`.

[Task possible affected files]

- `src_v2/engine/observability.py`
- `src_v2/engine/runtime_status.py`
- `src_v2/engine/governor.py`
- `src_v2/engine/kernel.py`
- neighboring queue/replay/worker integration points

[Task important notes]
Do not keep fake zeros just because the field exists in tests.

Do not build unbounded trend history.

[Task check list]

- [ ] Replace placeholder queue metrics
- [ ] Replace placeholder dropped-work counters
- [ ] Replace placeholder worker metrics
- [ ] Replace placeholder replay pressure metrics
- [ ] Freeze bounded trend windows
- [ ] Freeze explicit units for surfaced trends

[Task acceptance criteria]
All surfaced runtime metrics used by the governor or by operational status are real, bounded, and free of placeholder semantics.

---

[ ] (checkbox) - [Task 3] - Harden governor transitions, degradation order, and recovery behavior

[Task Description]
Turn the governor from a structurally correct state machine into a fully trusted pressure controller.

[Task technical implementation]
Complete the governor so that:

1. **Transition rules are exact**
   - escalation thresholds are exact,
   - survival thresholds are exact,
   - recovery thresholds are exact,
   - and all are profile-relative.

2. **Recovery anti-thrashing is exact**
   - dwell/cooldown rules are explicit,
   - low-watermark conditions are explicit,
   - one-step recovery sequencing is explicit if retained,
   - oscillation handling is test-pinned.

3. **Degradation order is exact**
   - diagnostic richness,
   - opportunistic work,
   - metric richness,
   - non-authoritative periodic work,
   - and survival-floor behavior are all explicit and enforced.

4. **No authoritative corruption**
   - the governor must never suppress critical work,
   - must never alter authoritative checkpoint semantics,
   - and must never move governance state into authoritative state.

[Task possible affected files]

- `src_v2/engine/governor.py`
- `src_v2/core/governance.py`
- `src_v2/engine/runtime_status.py`
- `src_v2/engine/policy.py`

[Task important notes]
Do not add new runtime modes.

Do not make recovery or degradation “heuristic enough” to be hard to explain.

[Task check list]

- [ ] Freeze exact escalation rules
- [ ] Freeze exact recovery rules
- [ ] Freeze anti-thrashing logic
- [ ] Freeze degradation order
- [ ] Prove no authoritative contamination
- [ ] Document final governor law

[Task acceptance criteria]
Governor transitions, degradation order, and recovery behavior are exact, deterministic, bounded, and semantically safe.

---

[ ] (checkbox) - [Task 4] - Finish scheduler-policy integration and prove semantic safety under degradation

[Task Description]
Make scheduler behavior under pressure exact, explicit, and semantically safe.

[Task technical implementation]
Complete the scheduler-policy boundary so that:

1. **Policy is explicit**
   - `GovernorPolicy` exposes explicit scheduler-facing decisions such as:
     - allow or suppress opportunistic work,
     - allow or suppress non-authoritative periodic work,
     - bounded optional work allowance where relevant.

2. **Scheduler remains semantically clean**
   - the scheduler consumes policy,
   - but does not reinterpret runtime mode itself,
   - and does not change critical-work selection or authoritative ordering.

3. **Deferrable behavior remains lawful**
   - deferred work remains bounded,
   - only declared deferrable work may be postponed,
   - and degradation does not silently defer non-deferrable work.

[Task possible affected files]

- `src_v2/engine/scheduler.py`
- `src_v2/engine/policy.py`
- `src_v2/core/work.py`
- `src_v2/engine/kernel.py`

[Task important notes]
Do not let scheduler logic absorb governor behavior.

Do not let degradation create alternate kernel semantics.

[Task check list]

- [ ] Freeze explicit `GovernorPolicy` fields
- [ ] Remove raw runtime-mode interpretation from scheduler
- [ ] Freeze degradation-safe scheduler filtering
- [ ] Freeze non-deferrable protection
- [ ] Document final scheduler-policy boundary

[Task acceptance criteria]
Scheduler behavior under degradation is explicit, policy-driven, and guaranteed not to alter authoritative semantics.

---

[ ] (checkbox) - [Task 5] - Complete the runtime-protection test suite and eliminate weak proofs

[Task Description]
Close the proof gap in the safety-control layer by finishing the governor and runtime-signal tests and eliminating weak or decorative protections.

[Task technical implementation]
Complete or add exact tests for:

### Runtime-signal tests

- real queue utilization surfacing,
- real dropped-work accounting,
- real replay pressure surfacing,
- real worker pressure surfacing where active,
- bounded signal-history windows,
- stable units and snapshot semantics.

### Governor tests

- exact threshold transitions,
- exact anti-thrashing behavior,
- exact degradation order,
- exact recovery sequencing,
- no governance contamination of authoritative hash.

### Scheduler-policy tests

- policy suppresses only declared degradable work,
- critical work remains unaffected,
- authoritative periodic work remains in `SURVIVAL`,
- non-authoritative periodic work is shed correctly.

### Suggested test groups

- `tests_v2/engine/test_resource_governor_contract.py`
- `tests_v2/engine/test_degradation_order.py`
- `tests_v2/engine/test_anti_thrashing.py`
- `tests_v2/engine/test_governance_isolation.py`
- new or expanded runtime-signal truth tests

[Task possible affected files]

- existing governor/signal/policy test modules
- any missing new runtime-signal truth tests

[Task important notes]
Do not deepen replay or certification scenarios here.

This milestone is about making the protection model itself real.

[Task check list]

- [ ] Finish all runtime-signal truth tests
- [ ] Finish all governor transition tests
- [ ] Finish all anti-thrashing tests
- [ ] Finish all scheduler-policy boundary tests
- [ ] Prove governance isolation from authoritative hash
- [ ] Make the runtime-protection suite complete and exact

[Task acceptance criteria]
The runtime-protection layer is pinned by a complete deterministic test suite proving signal truthfulness, governor correctness, degradation order, recovery stability, and semantic safety.

---

[ ] (checkbox) - [Task 6] - Add exact Milestone B documentation pack

[Task Description]
Document the completed runtime-protection model so later milestones treat it as finished law rather than a provisional control layer.

[Task technical implementation]
Create:

- `docs/engine/runtime_signal_contract_mb.md`
- `docs/engine/mb_test_matrix.md`

`runtime_signal_contract_mb.md` must contain these exact sections:

- Purpose
- Scope of Milestone B
- Runtime signal law
- Bounded signal-history law
- Governor transition law
- Degradation-order law
- Recovery and anti-thrashing law
- Scheduler-policy boundary
- Non-goals
- Completion guarantees

`mb_test_matrix.md` must contain these exact sections:

- Runtime-signal truth tests
- Governor transition tests
- Degradation-order tests
- Recovery stability tests
- Governance-isolation tests
- Scheduler-policy boundary tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/runtime_signal_contract_mb.md`
- `docs/engine/mb_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not end Milestone B with only code and passing tests. The completed pressure model must be written down exactly.

[Task check list]

- [ ] Document runtime signal law
- [ ] Document bounded trend/history law
- [ ] Document governor transition law
- [ ] Document degradation-order law
- [ ] Document scheduler-policy law
- [ ] Document the exact test matrix

[Task acceptance criteria]
Milestone B has a complete exact documentation pack describing the finished runtime-pressure model and the tests that freeze it.

---

Priority Plan

What must change in mindset or assumptions
Stop believing the governor is “done” because modes and policies exist. It is only done when the signal truth feeding it is real, bounded, and fully proven.

What actions must be taken immediately
Freeze the runtime-signal contract, replace placeholder metrics with real bounded values, harden governor transitions and recovery, finish policy-to-scheduler integration, and close the runtime-protection proof suite.

What must stop or be eliminated
Stop surfacing decorative metrics. Stop feeding the governor partial truth. Stop letting the scheduler infer policy from raw modes. Stop treating anti-thrashing as a nice-to-have.

The consequences and opportunity cost if this fails
Replay, shutdown, concurrency, and certification will continue to rely on a protection layer that looks disciplined in code but still reasons over incomplete reality. That would keep the engine in prototype territory.
