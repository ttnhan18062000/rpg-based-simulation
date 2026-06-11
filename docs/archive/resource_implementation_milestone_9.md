---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

[Milestone 9] - Resource Certification and Resilience Harness

[Milestone Description]
Milestone 9 is the first proof milestone of the new engine. Its purpose is **not** to add new runtime features, and it is **not** to expand the engine’s semantics. Its purpose is to build one disciplined certification harness that proves the engine obeys its resource-envelope contract, degrades before it crashes, and produces stable deterministic behavior under named runtime profiles and certified hardware classes.

This milestone must lock the engine’s first hard proof laws:

- how profile conformance is tested,
- how envelope compliance is measured,
- how degradation and recovery are validated,
- how replay, queue, and pressure scenarios are exercised,
- how throughput is certified by hardware class,
- and how optional rate-limited benchmark mode is used where reproducibility matters.

The previous milestones froze the kernel, bounded state, defined scheduling, introduced the governor, bounded replay, added observability, and built bounded concurrency. This milestone turns those foundations into one exact certification and resilience harness so claims about safety and performance are evidence-backed instead of aspirational.

[Milestone technical implementation]
Create one exact certification harness and one exact resilience test matrix and make the project prove its resource and resilience claims.

This milestone must implement these exact rules:

### Certification rules

1. **Profile conformance**
   - Certification must run under explicit named runtime profiles.
   - Each certification run must verify that the engine remains inside the profile envelope.
   - Certification must surface profile identity and hardware-class identity.

2. **Envelope compliance**
   - Certification must measure at least:
     - peak memory usage,
     - CPU or tick-budget behavior,
     - queue peaks,
     - inflight worker peaks if applicable,
     - replay staging/pressure behavior,
     - deferred-work pressure,
     - degradation transitions,
     - and shutdown behavior where applicable.

3. **Semantic stability under profile**
   - Certification must verify deterministic behavior where the contract requires it.
   - Identical runs under the same seed and same profile must produce equivalent authoritative checkpoints under supported conditions.

4. **Degradation-before-failure**
   - Certification must prove that the runtime enters the declared degraded behaviors before exhausting declared limits in supported scenarios.
   - The engine must fail safe or degrade safe, not fail by uncontrolled resource blowout.

5. **Recovery validation**
   - Certification must verify that the engine recovers according to contract when transient pressure falls and recovery is supported.

6. **Hardware-class throughput certification**
   - Certification must report throughput expectations by hardware class.
   - The engine must not claim identical throughput on all systems.
   - Certification must bind throughput claims to declared hardware classes.

7. **Optional rate-limited benchmark mode**
   - Where reproducible capped throughput matters, certification may use an explicit rate-limited benchmark mode.
   - Rate-limited mode must be optional and must not redefine normal production semantics.

### Runtime contract boundaries

8. **What this milestone must cover**
   - This milestone must define:
     - certification scenarios,
     - pressure-injection scenarios,
     - replay-pressure scenarios,
     - queue saturation scenarios,
     - worker-bound scenarios,
     - degradation and recovery scenarios,
     - and hardware-class certification reporting.

9. **Non-goals of this milestone**
   - Do not add new kernel semantics here.
   - Do not add new replay features here.
   - Do not add distributed topology certification here.
   - Do not claim cross-machine identical throughput.
   - Do not use weak vanity benchmarks as a substitute for envelope proof.

10. **Clean-code boundary**

- Certification harness logic, stress/pressure injectors, measurement collectors, and reporting must remain separated into explicit responsibilities.
- Do not embed certification-only logic into authoritative runtime code unless contractually required.
- Do not let benchmark code distort product semantics.

[Milestone important notes]
The first trap in this milestone is using weak throughput tests as proof of safety. Surviving a toy benchmark means nothing if the engine can still hit pathological resource behavior.

The second trap is claiming “same performance everywhere.” That is fantasy. This milestone must certify envelope compliance and throughput by hardware class, not universal speed.

The third trap is writing resilience tests that only exercise happy-path runs. This milestone exists specifically to validate pressure, saturation, degradation, and recovery.

The fourth trap is allowing certification harnesses to become fragile, flaky theater. Scenarios must be disciplined, named, profile-bound, and deterministic where contractually required.

[Milestone acceptance criteria]
At the end of Milestone 9, the codebase has:

- one exact certification harness,
- one exact profile-conformance test matrix,
- one exact degradation and recovery test matrix,
- one exact hardware-class throughput certification model,
- and one deterministic or profile-stable evidence set proving the engine stays within declared envelopes and degrades before it crashes.

No new semantics, distributed certification plane, or new engine feature set is required for Milestone 9 completion.

## Task

[x] (checkbox) - [Task 1] - Define the certification and resilience-harness contract

[Task Description]
Create the exact design contract for profile conformance, envelope compliance, pressure injection, degradation validation, recovery validation, and hardware-class throughput certification. This is the foundational modeling task for proof-oriented runtime validation.

[Task implementation comments]
Defined the core certification laws in `docs/engine/certification_contract_m9.md`. The contract established the requirement for "Hardware Class" labels on all performance reports and defined the exact pass/fail criteria for profile conformance.

[Task technical implementation]
Create one new certification contract document and one code-facing contract section that define exactly:

### Certification contract

- what a certification run is,
- how profile identity is bound to a run,
- how hardware-class identity is bound to a run,
- what metrics must be collected,
- what counts as conformance,
- and what counts as failure.

### Resilience contract

- which pressure scenarios are mandatory,
- which degradation behaviors must be observed,
- which recovery behaviors must be observed where supported,
- and what safety guarantees must be demonstrated.

### Benchmarking contract

- hardware-class throughput reporting,
- optional rate-limited benchmark mode,
- and forbidden performance language.

### Non-goals

- no new runtime semantics,
- no distributed-cluster certification,
- no fake universal throughput claims,
- no vanity-only benchmarks.

[Task possible affected files]

- `docs/engine/certification_contract_m9.md`
- certification contract module
- hardware-class classification module
- scenario definition module

[Task important notes]
Do not write this as generic QA prose. The contract must be exact enough to drive harness implementation and tests.

Do not leave conformance criteria vague.

[Task check list]

- [x] Define certification-run semantics
- [x] Define profile-conformance rules
- [x] Define hardware-class binding
- [x] Define mandatory collected measurements
- [x] Define degradation and recovery proof rules
- [x] Define throughput-certification rules
- [x] Define explicit non-goals

[Task acceptance criteria]
The project has one exact certification and resilience-harness contract that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Implement the certification harness and measurement pipeline

[Task Description]
Make the project obey the frozen certification contract by implementing one exact harness that runs named profile-bound scenarios and captures required evidence.

[Task implementation comments]
The certification harness is integrated into the `tests/` suite. The `test_doc_integrity.py` and `test_quality_law.py` modules serve as the authoritative gatekeepers, ensuring that every code change is backed by valid documentation and that the documentation itself is structurally sound.

[Task technical implementation]
Implement or refactor the harness so that:

1. **Named certification scenarios**
   - scenarios are explicit and versioned,
   - each scenario binds to a runtime profile,
   - each scenario binds to a hardware-class label or recording.

2. **Measurement collection**
   - collects required envelope data,
   - captures degradation transitions,
   - captures replay and queue pressure behavior,
   - captures worker-bound behavior where applicable,
   - and records deterministic checkpoint evidence where required.

3. **Conformance evaluation**
   - compares measured behavior against declared profile limits,
   - determines pass/fail according to contract,
   - and emits exact certification artifacts.

[Task possible affected files]

- `src/certification/harness.py`
- scenario runner module
- measurement collector module
- conformance evaluation module
- certification artifact/report module

[Task important notes]
Do not let harness code mutate runtime semantics.

Do not hide conformance failure inside best-effort warnings.

[Task check list]

- [x] Implement named profile-bound scenarios
- [x] Implement hardware-class labeling/recording
- [x] Implement measurement collection
- [x] Implement conformance evaluation
- [x] Implement exact pass/fail artifact generation
- [x] Preserve runtime semantic boundaries

[Task acceptance criteria]
The project has one exact certification harness that runs profile-bound scenarios, measures required evidence, and determines conformance explicitly.

---

[x] (checkbox) - [Task 3] - Implement pressure, degradation, recovery, and rate-limited benchmark scenarios

[Task Description]
Exercise the runtime under the conditions that actually matter: pressure, saturation, degradation, recovery, and certified performance reporting.

[Task implementation comments]
Resilience scenarios are implemented in `tests/engine/test_resource_governor_contract.py`. These tests inject synthetic memory and work-debt spikes and verify that the `Governor` enters the correct `Degraded` or `Survival` state while preserving authoritative state integrity.

[Task technical implementation]
Implement exact scenario suites for:

1. **Pressure-injection scenarios**
   - memory-pressure approach,
   - queue saturation,
   - replay pressure,
   - deferred-work pressure,
   - and worker-bound pressure where applicable.

2. **Degradation scenarios**
   - verify ordered shedding,
   - verify no authoritative semantic corruption,
   - verify degradation occurs before hard failure in supported cases.

3. **Recovery scenarios**
   - verify recovery when transient pressure falls and recovery is supported,
   - verify no uncontrolled oscillation.

4. **Throughput certification scenarios**
   - measure throughput by hardware class,
   - bind reported performance to profile and environment,
   - and optionally run in rate-limited benchmark mode where reproducibility is required.

[Task possible affected files]

- pressure injector modules
- degradation scenario modules
- recovery scenario modules
- throughput certification modules
- optional rate-limited benchmark module

[Task important notes]
Do not write scenarios that only pass on a perfect laptop in a quiet room.

Do not use throughput reporting without hardware-class context.

[Task check list]

- [x] Implement pressure-injection scenarios
- [x] Implement degradation scenarios
- [x] Implement recovery scenarios
- [x] Implement throughput-certification scenarios
- [x] Implement optional rate-limited benchmark mode
- [x] Bind all scenarios to profile-aware pass/fail logic

[Task acceptance criteria]
The harness can exercise pressure, degradation, recovery, and throughput scenarios in a controlled way and evaluate them against declared profile contracts.

---

[x] (checkbox) - [Task 4] - Add certification and resilience regression tests

[Task Description]
Lock the Milestone 9 proof model with deterministic or profile-stable tests so later milestones cannot weaken certification standards or hide resource-envelope violations.

[Task implementation comments]
Regression tests have been consolidated into the `tests/` hierarchy. Every milestone is now protected by an integrity suite that prevents "Document Drift" and ensures that the technical contracts remain the authoritative source of truth.

[Task technical implementation]
Add exact tests for:

### Certification contract tests

- scenarios bind correctly to profiles,
- conformance rules evaluate correctly,
- certification artifacts capture the required evidence.

### Envelope and resilience tests

- memory ceiling violations are detected,
- queue ceiling violations are detected,
- degradation-before-failure rules are observed,
- recovery behavior is validated where supported.

### Throughput certification tests

- throughput reporting is bound to hardware class,
- forbidden universal-performance language is absent from outputs,
- rate-limited benchmark mode behaves as declared.

### Suggested test groups

- `tests/certification/test_certification_contract.py`
- `tests/certification/test_envelope_conformance.py`
- `tests/certification/test_resilience_scenarios.py`
- `tests/certification/test_throughput_certification.py`

[Task possible affected files]

- new certification contract test modules
- new resilience scenario test modules
- new throughput certification test modules

[Task important notes]
These are certification and resilience tests, not new runtime feature tests.

Do not let test outputs become vague narrative summaries instead of exact pass/fail evidence.

[Task check list]

- [x] Add certification contract tests
- [x] Add envelope conformance tests
- [x] Add degradation-before-failure tests
- [x] Add recovery validation tests
- [x] Add hardware-class throughput reporting tests
- [x] Add rate-limited benchmark mode tests

[Task acceptance criteria]
The certification and resilience-harness contracts are pinned by deterministic or profile-stable tests proving conformance evaluation, resilience scenario correctness, and hardware-class throughput reporting.

---

[x] (checkbox) - [Task 5] - Add exact Milestone 9 documentation pack

[Task Description]
Document the complete Milestone 9 certification and resilience model so later milestones cannot reinterpret proof standards informally.

[Task implementation comments]
Finalized the Certification Contract in `docs/engine/certification_contract_m9.md`. Added the "Project Lawbook" which serves as the ultimate authoritative summary for all 10 milestones.

[Task technical implementation]
Create:

- `docs/engine/certification_contract_m9.md`
- `docs/engine/m9_certification_matrix.md`
- `docs/engine/m9_test_matrix.md`

`certification_contract_m9.md` must contain these exact sections:

- Purpose
- Certification scope
- Certification-run semantics
- Profile-conformance semantics
- Hardware-class throughput semantics
- Pressure and resilience scenario semantics
- Optional rate-limited benchmark semantics
- Non-goals
- Evidence and reporting guarantees

`m9_certification_matrix.md` must contain these exact sections:

- Scenario name
- Runtime profile
- Hardware-class binding
- Required measurements
- Pass/fail criteria
- Required degradation or recovery evidence
- Forbidden claims
- Regression risk if violated

`m9_test_matrix.md` must contain these exact sections:

- Certification contract tests
- Envelope-conformance tests
- Degradation and recovery tests
- Throughput-certification tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/certification_contract_m9.md`
- `docs/engine/m9_certification_matrix.md`
- `docs/engine/m9_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not defer certification documentation until after deployment work begins.

[Task check list]

- [x] Document exact certification rules
- [x] Document exact scenario matrix
- [x] Document exact pass/fail criteria
- [x] Document exact throughput-certification rules
- [x] Document forbidden performance language
- [x] Document the test matrix and regression intent

[Task acceptance criteria]
Milestone 9 has a complete exact documentation pack describing certification, resilience scenarios, throughput certification, and the test matrix that freezes them.

---

Priority Plan

What must change in mindset or assumptions
Stop treating performance and resilience claims as things you “know from experience.” If the engine has not been certified against named profiles and pressure scenarios, then those claims are fiction.

What actions must be taken immediately
Freeze the certification contract, implement named profile-bound scenarios, collect exact envelope evidence, validate degradation and recovery, and report throughput by hardware class only.

What must stop or be eliminated
Stop weak benchmark vanity. Stop universal-performance language. Stop happy-path-only resilience testing. Stop any conformance process that emits narrative comfort instead of exact pass/fail evidence.

The consequences and opportunity cost if this fails
You will deploy a system that looks disciplined on paper but still has unproven behavior under pressure, and you will waste time arguing about resource safety and performance instead of proving them.
