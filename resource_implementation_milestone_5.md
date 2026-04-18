[Milestone 5] - Resource Governor and Degradation State Machine

[Milestone Description]
Milestone 5 is the first active runtime-protection milestone of the new engine. Its purpose is **not** to implement replay yet, and it is **not** to introduce concurrency yet. Its purpose is to make the runtime enforce the resource-envelope contract defined in Milestone 1 by introducing one exact governor and one exact degradation model that protect the engine from exhausting memory, CPU budget, queue capacity, and optional-cost overhead.

This milestone must lock the engine’s first active safety laws:

- how runtime pressure is detected,
- which signals are authoritative for pressure decisions,
- how runtime modes change,
- what is allowed to degrade and in what order,
- what must never degrade,
- and how recovery from pressure behaves.

The previous milestones froze the kernel contract, built the minimal deterministic kernel, bounded runtime state, and introduced an explicit work model. This milestone turns those foundations into one exact safety-control layer so the engine can protect itself before the process becomes unstable.

[Milestone technical implementation]
Create one exact resource governor and one exact degradation state machine and make the runtime obey them.

This milestone must implement these exact rules:

### Pressure-detection rules

1. **Resource-envelope awareness**
   - The governor must consume the runtime-profile limits frozen in Milestone 1.
   - The governor must not invent floating limits outside the profile contract.
   - Pressure decisions must be made relative to the active profile.

2. **Pressure signals**
   - The governor must track explicit pressure signals for at least:
     - memory usage,
     - CPU or tick-budget usage,
     - queue pressure,
     - deferred-work pressure,
     - replay pre-budget pressure if any placeholders exist,
     - observability overhead if any placeholders exist,
     - and any mandatory internal budget signals already represented in the runtime.

3. **Exact threshold semantics**
   - Threshold meanings must be explicit.
   - Thresholds must support deterministic transitions.
   - Trend-based escalation rules must be explicit if supported.

### Runtime-mode rules

4. **Runtime modes**
   - The runtime must explicitly support:
     - `NORMAL`
     - `CONSTRAINED`
     - `DEGRADED`
     - `SURVIVAL`

5. **Mode meaning**
   - `NORMAL` means operation within profile comfort margins.
   - `CONSTRAINED` means pressure is rising and optional cost must begin shrinking.
   - `DEGRADED` means stronger shedding is required to preserve core simulation semantics.
   - `SURVIVAL` means the engine protects authoritative execution first and suppresses or minimizes all non-essential runtime cost allowed by contract.

6. **Deterministic mode transitions**
   - Mode transitions must be exact and testable.
   - Escalation conditions must be explicit.
   - Recovery conditions must be explicit.
   - Transition behavior must not rely on vague heuristics.

### Degradation rules

7. **What may degrade**
   - Only explicitly degradable behaviors may be reduced or disabled.
   - Allowed degradable categories include:
     - verbose diagnostics,
     - detailed replay richness,
     - optional metrics richness,
     - optional summaries,
     - opportunistic maintenance,
     - and non-critical enrichments.

8. **What must not degrade**
   - Authoritative simulation semantics must not degrade.
   - Kernel tick meaning, apply order, deterministic state progression, and correctness of authoritative state must remain intact.

9. **Degradation order**
   - The degradation order must be explicit and stable.
   - The governor must shed non-authoritative cost first.
   - Optional systems must never preempt core simulation semantics.

10. **Recovery behavior**

- Recovery from elevated pressure must be controlled and deterministic.
- Recovery must not thrash between modes.
- Hysteresis or equivalent stabilization rules must be explicit if used.

### Runtime contract boundaries

11. **Non-goals of this milestone**

- Do not implement replay persistence here.
- Do not implement observability plumbing here beyond what is required to surface governor behavior for tests.
- Do not implement concurrency here.
- Do not implement external orchestration or container controls here.
- Do not change kernel semantics here.

12. **Clean-code boundary**

- Pressure measurement, mode transition logic, degradation policy, and runtime enforcement must be separated into distinct responsibilities.
- Do not bury degradation rules inside scattered feature flags.
- Do not let optional subsystems define their own uncontrolled survival logic.

[Milestone important notes]
The first trap in this milestone is treating the governor as a monitoring tool. It is not a dashboard. It is an execution-control component.

The second trap is allowing the governor to skip authoritative work. That is not resilience. That is semantic corruption.

The third trap is vague degradation. If the order, trigger, and recovery rules are not exact, the system will oscillate and become impossible to reason about.

The fourth trap is trying to solve container deployment, OS-level controls, or external scaling policy here. Those matter later, but this milestone is about engine-level runtime control.

[Milestone acceptance criteria]
At the end of Milestone 5, the codebase has:

- one exact resource governor,
- one exact pressure-signal model,
- one exact runtime mode state machine,
- one exact degradation order,
- one exact recovery model,
- and one deterministic test suite proving the governor protects core simulation semantics while shedding optional cost.

No replay sink, concurrency model, or external deployment control is required for Milestone 5 completion.

## Task

[ ] (checkbox) - [Task 1] - Define the resource-governor and degradation contract

[Task Description]
Create the exact design contract for pressure detection, runtime modes, degradation order, and recovery behavior. This is the foundational modeling task for runtime protection.

[Task technical implementation]
Create one new governor contract document and one code-facing contract section that define exactly:

### Governor contract

- what profile-defined limits are consumed,
- what pressure signals are observed,
- how thresholds are interpreted,
- how mode transitions occur,
- and how recovery is handled.

### Degradation contract

- which behaviors may degrade,
- which behaviors may not degrade,
- exact degradation order,
- and exact recovery behavior.

### Non-goals

- no replay implementation,
- no concurrency response,
- no container/cgroup controls,
- no external broker policy,
- no kernel semantic changes.

[Task possible affected files]

- `docs/engine/resource_governor_contract_m5.md`
- governor contract module
- degradation policy module
- runtime mode enum/state module

[Task important notes]
Do not write this as generic resilience prose. The contract must be exact enough to drive code and tests from it.

Do not leave any degradable category implicit.

[Task check list]

- [ ] Define profile-aware governor semantics
- [ ] Define pressure signal set
- [ ] Define threshold and trend semantics
- [ ] Define runtime modes
- [ ] Define degradable vs non-degradable behavior
- [ ] Define degradation order
- [ ] Define recovery behavior
- [ ] Define explicit non-goals

[Task acceptance criteria]
The project has one exact governor and degradation contract that can be used as the authoritative source for implementation and tests.

---

[ ] (checkbox) - [Task 2] - Implement pressure measurement and runtime mode transitions

[Task Description]
Make the runtime obey the frozen governor contract by implementing one exact pressure-evaluation and mode-transition path.

[Task technical implementation]
Implement or refactor the governor so that:

1. **Pressure evaluation**
   - consumes the active runtime profile,
   - measures the required pressure signals,
   - computes exact pressure state according to declared thresholds,
   - and produces deterministic mode decisions.

2. **Mode transitions**
   - implement escalation from `NORMAL` to `CONSTRAINED`, `DEGRADED`, and `SURVIVAL`,
   - implement deterministic recovery behavior,
   - and apply hysteresis or stabilization rules if defined by contract.

3. **Runtime enforcement boundary**
   - mode transition logic remains separate from the actual shedding behavior,
   - pressure detection remains separate from subsystem implementation detail.

[Task possible affected files]

- `src/engine/governor.py`
- `src/engine/pressure.py`
- `src/engine/runtime_modes.py`
- runtime profile integration module

[Task important notes]
Do not let subsystem code invent its own private pressure interpretation.

Do not fuse measurement and shedding into one opaque block.

[Task check list]

- [ ] Implement profile-aware pressure measurement
- [ ] Implement exact threshold evaluation
- [ ] Implement deterministic escalation rules
- [ ] Implement deterministic recovery rules
- [ ] Implement hysteresis if required
- [ ] Keep transitions separate from shedding logic

[Task acceptance criteria]
The engine has one exact pressure-measurement and mode-transition path that is deterministic and profile-aware.

---

[ ] (checkbox) - [Task 3] - Implement degradation policy enforcement for optional cost

[Task Description]
Make the runtime obey the frozen degradation contract by shedding or reducing only the costs that are explicitly allowed to degrade.

[Task technical implementation]
Implement exact enforcement behavior for:

1. **Verbose diagnostics**
   - reduce or disable according to mode rules.

2. **Replay richness placeholders**
   - if replay-related placeholders or pre-buffers exist, they must obey degradation policy without corrupting kernel behavior.

3. **Optional metrics richness**
   - reduce optional metric detail before core execution is threatened.

4. **Optional summaries and opportunistic maintenance**
   - defer, reduce, or suppress according to declared mode behavior.

5. **Non-critical enrichments**
   - shed in the explicit order defined by contract.

This task must guarantee:

- authoritative kernel semantics remain intact,
- optional work is shed in exact declared order,
- and no optional subsystem can bypass governor control.

[Task possible affected files]

- degradation policy module
- optional diagnostics module
- optional metrics/summary placeholders
- scheduler integration module for opportunistic work
- deferred work integration module

[Task important notes]
Do not let degradation silently change authoritative behavior.

Do not allow “temporary” bypasses for optional systems.

[Task check list]

- [ ] Implement verbose-diagnostics degradation
- [ ] Implement replay-richness placeholder degradation
- [ ] Implement optional-metrics degradation
- [ ] Implement summary/maintenance degradation
- [ ] Implement non-critical enrichment shedding
- [ ] Preserve authoritative semantics
- [ ] Preserve exact degradation order

[Task acceptance criteria]
Optional runtime cost is shed in the exact declared order while core simulation semantics remain unchanged.

---

[ ] (checkbox) - [Task 4] - Add deterministic governor and degradation tests

[Task Description]
Lock the Milestone 5 runtime-protection rules with deterministic tests so later milestones cannot silently turn the governor into an unstable or unsafe control layer.

[Task technical implementation]
Add exact tests for:

### Pressure and transition tests

- profile-defined thresholds are respected,
- pressure signals produce the correct mode transitions,
- trend-based escalation behaves as declared,
- recovery behaves as declared,
- hysteresis prevents uncontrolled thrashing if applicable.

### Degradation tests

- only degradable categories are reduced,
- degradation occurs in the exact declared order,
- authoritative behavior remains unchanged under mode changes,
- optional costs are reduced correctly in `CONSTRAINED`, `DEGRADED`, and `SURVIVAL`.

### Safety-boundary tests

- governor never skips authoritative kernel steps,
- invalid degradation attempts against non-degradable behavior are rejected,
- repeated identical pressure patterns produce identical mode behavior.

### Suggested test groups

- `tests/engine/test_resource_governor_contract.py`
- `tests/engine/test_runtime_mode_transitions.py`
- `tests/engine/test_degradation_order.py`

[Task possible affected files]

- new governor contract test modules
- new mode-transition test modules
- new degradation-policy test modules

[Task important notes]
These are governor and degradation tests, not replay tests and not concurrency tests.

Do not add system-wide stress certification here. That belongs later.

[Task check list]

- [ ] Add threshold evaluation tests
- [ ] Add mode-transition tests
- [ ] Add recovery and hysteresis tests
- [ ] Add degradation-order tests
- [ ] Add authoritative-safety boundary tests
- [ ] Add deterministic repeated-pattern tests

[Task acceptance criteria]
The resource governor and degradation rules are pinned by deterministic tests proving correct pressure handling, correct mode transitions, correct degradation order, and preservation of authoritative behavior.

---

[ ] (checkbox) - [Task 5] - Add exact Milestone 5 documentation pack

[Task Description]
Document the complete Milestone 5 runtime-protection model so later milestones cannot reinterpret pressure handling and degradation informally.

[Task technical implementation]
Create:

- `docs/engine/resource_governor_contract_m5.md`
- `docs/engine/m5_degradation_matrix.md`
- `docs/engine/m5_test_matrix.md`

`resource_governor_contract_m5.md` must contain these exact sections:

- Purpose
- Governor scope
- Pressure signal semantics
- Threshold semantics
- Runtime modes
- Mode transition semantics
- Recovery semantics
- Non-goals
- Safety guarantees

`m5_degradation_matrix.md` must contain these exact sections:

- Degradable category
- Authoritative vs non-authoritative status
- Allowed mode reductions
- Exact shedding order
- Recovery behavior
- Forbidden degradation behavior
- Regression risk if violated

`m5_test_matrix.md` must contain these exact sections:

- Pressure evaluation tests
- Runtime mode transition tests
- Recovery tests
- Degradation-order tests
- Authoritative-safety tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/resource_governor_contract_m5.md`
- `docs/engine/m5_degradation_matrix.md`
- `docs/engine/m5_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer degradation documentation until replay or observability exists.

[Task check list]

- [ ] Document exact governor rules
- [ ] Document exact runtime modes
- [ ] Document exact degradation order
- [ ] Document exact recovery behavior
- [ ] Document forbidden degradation behavior
- [ ] Document the deterministic test matrix

[Task acceptance criteria]
Milestone 5 has a complete exact documentation pack describing pressure handling, runtime modes, degradation behavior, recovery behavior, and the deterministic test matrix that freezes them.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of runtime protection as something external to the engine. The engine itself must know how to protect its resource envelope before external watchdogs or deployment constraints are involved.

What actions must be taken immediately
Freeze the governor contract, implement exact pressure measurement and mode transitions, define exact degradable categories and shedding order, and pin the whole model with deterministic tests.

What must stop or be eliminated
Stop vague “best effort” degradation. Stop letting optional systems define their own uncontrolled survival behavior. Stop treating pressure measurement as observability only. Stop any design that allows the governor to skip authoritative semantics.

The consequences and opportunity cost if this fails
Later milestones will build on a runtime that can detect pressure but cannot control it safely, and you will waste time blaming replay, scheduling, or deployment when the real defect is that the engine never learned how to protect itself.
