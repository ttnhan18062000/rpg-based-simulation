# [Milestone E] - Certification, Proof, and Release Trust

## [Milestone Description]

Milestone E exists to turn v2’s certification layer from a promising harness into a complete trust system.

The current code already has the right skeleton:

- certification harness,
- conformance evaluator,
- measurement points,
- scenario expectations,
- failure kinds,
- proof recording,
- release-proof tests,
- and doc-integrity / final-gate style enforcement.

That is the good news.

The bad news is that this layer is still too narrow to be the final truth system. The existing conformance model proves useful things, but the scenario catalog is still small, the coverage breadth is still limited, the failure taxonomy is not yet deep enough to represent the full runtime truth space, and the proof bundle/release gate can still become a green-looking shell around an incomplete scenario universe.

Milestone E exists to make these things true:

- certification scenarios are broad enough to matter,
- failure classes are explicit and operationally honest,
- allowed failures preserve truth instead of hiding defects,
- semantic equivalence and reproducibility claims are proven under declared scope,
- profile/hardware/scenario claims are explicit,
- proof bundles are structurally complete and checkable,
- release gating depends on proof completeness instead of loose convention,
- and the engine can be certified headlessly at system, subsystem, and full-runtime levels.

This is not about “more tests.”
This is about turning proof into a product requirement.

---

## [Milestone technical implementation]

Create one complete certification and release-trust contract in which the engine’s claims are scenario-bounded, profile-bounded, hardware-bounded, failure-honest, and backed by exact proof artifacts.

This milestone must implement these exact rules.

### Certification completion rules

1. **Certification must certify declared claims, not vague quality**
   - Certification must be scoped by:
     - scenario,
     - profile,
     - hardware class,
     - runtime mode,
     - and supported execution mode.

   - No certification result may imply broader guarantees than the scenario matrix actually proves.

2. **Scenario expectations must be exact**
   - Every certification scenario must define:
     - required modes,
     - recovery expectations,
     - semantic equivalence requirements,
     - reproducibility requirements,
     - sampling requirements,
     - allowed failure kinds if any,
     - and exact pass/fail law.

3. **Failure classification must be complete and honest**
   - All certification-relevant runtime failure outcomes must map to explicit failure kinds.
   - Allowed failures must not erase truth.
   - “Pass with allowed failure observed” must remain distinguishable from clean pass.

4. **Certification must remain authoritative-truth aligned**
   - Authoritative equivalence, authoritative drift, recovery law, and profile envelope law must remain the core truth surface.
   - Operational failures may appear in certification, but must not be confused with authoritative divergence unless they truly cause it.

5. **Proof artifacts must be complete and checkable**
   - Certification runs must emit one declared proof bundle containing:
     - manifest,
     - scenario result(s),
     - measurements,
     - hashes/checkpoints,
     - environment/profile metadata,
     - and release-truth markers.

6. **Release gating must depend on proof completeness**
   - Releases must fail if proof bundle structure is incomplete,
   - if required scenarios are missing,
   - if required artifacts are missing,
   - or if proof semantics do not satisfy the declared release contract.

7. **Certification must cover multiple test levels**
   - subsystem scenarios,
   - headless engine scenarios,
   - concurrency equivalence scenarios,
   - lifecycle integrity scenarios,
   - runtime degradation/recovery scenarios,
   - and full-system contract scenarios
     must all be part of the overall certification universe.

8. **Reproducibility and equivalence claims must be exact**
   - same supported mode + same seed + same profile + same scenario must produce declared reproducibility outcomes,
   - local-vs-concurrent equivalence claims must only exist for declared supported slices,
   - and any non-equivalence boundary must be explicit.

9. **Certification reporting must be usable**
   - Proof output must be machine-checkable and human-readable.
   - Failure reasons must be exact enough to debug.
   - Allowed-failure results must stay honest.

10. **Certification must remain bounded**

- Measurement collection, proof artifacts, and scenario recording must obey bounded operational rules from earlier milestones.
- Certification must not reintroduce unbounded replay/telemetry behavior.

### Milestone E coverage boundary

11. **What this milestone must cover**

- scenario catalog expansion,
- scenario expectation law closure,
- failure taxonomy expansion,
- allowed-failure honesty closure,
- semantic equivalence and reproducibility proof closure,
- proof bundle structure closure,
- release gate closure,
- certification docs/test matrix closure,
- and final trust/regression guardrails.

12. **Non-goals of this milestone**

- no new runtime architecture,
- no deep new gameplay systems,
- no distributed certification farm,
- no performance-marketing claims beyond declared certified throughput/profile scope,
- no vague “AI quality” certification outside declared deterministic/system contracts.

13. **Clean-code boundary**

- harness orchestrates certification runs,
- scenario definitions declare expectations,
- conformance evaluator judges outcomes,
- recorder writes proof artifacts,
- release gate validates required proof completeness,
- runtime and engine layers remain separate from certification policy,
- and proof output stays external to authoritative state itself.

---

## [Milestone important notes]

The first trap is treating certification as “big end-to-end tests.” That is too weak. Certification is the claim system.

The second trap is allowing scenario labels to overclaim. A scenario that proves one narrow degradation path must not be used to imply general resilience.

The third trap is hiding bad news behind allowed-failure semantics. If a failure is observed, the proof must say so clearly even when that outcome is whitelist-allowed.

The fourth trap is making proof bundles decorative. If the proof directory exists but its contents are incomplete or semantically thin, that is fake release trust.

The fifth trap is claiming reproducibility or equivalence outside the exact supported scope. That is how honest deterministic systems turn into dishonest marketing systems.

---

## [Milestone acceptance criteria]

At the end of Milestone E, the codebase has:

- one exact certification and release-trust contract,
- one expanded and explicit scenario matrix,
- one complete certification failure taxonomy,
- one honest allowed-failure reporting contract,
- one exact semantic-equivalence and reproducibility proof contract,
- one complete proof-bundle structure contract,
- one exact release-gate contract,
- one complete certification test suite,
- and one final documentation pack describing the trusted claim surface of v2.

At that point, v2 is ready to say:

- what it proves,
- under what scenarios,
- under what profiles,
- on what hardware classes,
- with what failure semantics,
- and with what release proof.

That is the end of the trust-building sequence.

---

# ## Task

---

## [ ] (checkbox) - [Task 1] - Freeze the certification and release-trust law set

### [Task Description]

Create one exact contract for certification scope, scenario expectations, conformance rules, proof artifacts, and release-gate requirements.

### [Task technical implementation]

Write one Milestone E contract document that defines:

- exact purpose of certification,
- exact scope of certified claims,
- exact scenario model,
- exact expectation model,
- exact failure taxonomy expectations,
- exact semantic-equivalence and reproducibility rules,
- exact proof-bundle structure,
- exact release-gate rules,
- exact honest-reporting rules,
- exact profile/hardware/scenario scope language,
- and exact out-of-scope list.

This document must explicitly define:

- what “certified” means,
- what “passed with allowed failure observed” means,
- what “clean pass” means,
- what “reproducible” means,
- what “equivalent” means,
- what “proof bundle complete” means,
- and what “release blocked” means.

### [Task possible affected files]

- `docs/engine/certification_contract_me.md`
- `docs/engine/me_test_matrix.md`
- `src/certification/harness.py`
- `src/certification/conformance.py`
- `src/certification/models.py`
- release-gate docs

### [Task important notes]

Do not let certification semantics remain implied across tests and markdown fragments.
Do not let release truth live only in CI folklore.

### [Task check list]

- [ ] Freeze certification scope
- [ ] Freeze scenario/expectation law
- [ ] Freeze failure and allowed-failure law
- [ ] Freeze equivalence/reproducibility law
- [ ] Freeze proof-bundle law
- [ ] Freeze release-gate law
- [ ] Freeze scope language for certified claims
- [ ] Freeze non-goals

### [Task acceptance criteria]

The project has one exact certification and release-trust contract defining the finished Milestone E law set.

---

## [ ] (checkbox) - [Task 2] - Expand and normalize the certification scenario catalog

### [Task Description]

Turn the current scenario set from a narrow sample into a meaningful certification universe.

### [Task technical implementation]

Audit the current scenario catalog and expand it into one explicit scenario matrix covering at least these families:

1. **Clean baseline scenarios**
   - idle clean,
   - steady-state normal operation,
   - quiet tick stability,
   - no-op reproducibility.

2. **Pressure and degradation scenarios**
   - RAM pressure,
   - tick-budget pressure,
   - queue/inflight pressure,
   - replay pressure,
   - work-debt buildup,
   - controlled degraded-mode entry,
   - controlled survival-mode entry.

3. **Recovery scenarios**
   - degraded -> normal recovery,
   - survival -> degraded -> normal recovery,
   - bounded recovery time,
   - no false recovery under active pressure.

4. **Equivalence scenarios**
   - local-vs-concurrent supported-slice equivalence,
   - repeated-run reproducibility,
   - no semantic drift under supported concurrent mode.

5. **Lifecycle scenarios**
   - startup validation success/failure,
   - replay overflow with authoritative survival,
   - sink failure with authoritative survival,
   - shutdown timeout with authoritative survival,
   - final authoritative emission survival.

6. **Fault-handling scenarios**
   - worker rejection/fallback,
   - worker timeout/fallback,
   - invalid worker result classification,
   - allowed-failure observed scenarios,
   - unallowed-failure rejection scenarios.

7. **Release-proof scenarios**
   - proof bundle completeness,
   - manifest correctness,
   - missing artifact blocking,
   - exact release-block conditions.

For every scenario define:

- scenario ID,
- purpose,
- inputs,
- required expectations,
- allowed execution modes,
- allowed profiles,
- and required artifacts.

### [Task possible affected files]

- `src/certification/scenarios.py`
- `docs/engine/certification_scenario_matrix.md`
- scenario-related tests

### [Task important notes]

Do not inflate the catalog with duplicates that prove nothing new.
Each scenario must justify its existence by proving one exact contract.

### [Task check list]

- [ ] Audit existing scenario set
- [ ] Add missing baseline scenarios
- [ ] Add degradation/recovery scenarios
- [ ] Add equivalence scenarios
- [ ] Add lifecycle scenarios
- [ ] Add fault-handling scenarios
- [ ] Add release-proof scenarios
- [ ] Document scenario matrix

### [Task acceptance criteria]

The certification catalog is broad enough to represent the declared trust surface of v2 without vague coverage gaps.

---

## [ ] (checkbox) - [Task 3] - Complete and harden the scenario expectation model

### [Task Description]

Make every certification scenario judgeable by one exact expectation contract.

### [Task technical implementation]

Audit and extend `ScenarioExpectations` so it can express all required certification rules, including:

- required governor modes,
- recovery required / not required,
- recovery time limit,
- semantic equivalence required,
- reproducibility required,
- allowed failure kinds,
- required sampling interval,
- expected runtime mode sequence constraints,
- required final authoritative status,
- expected lifecycle outcome if applicable,
- expected proof artifact set if applicable,
- execution-mode compatibility,
- and profile/hardware applicability.

Ensure every scenario uses one exact expectation object or equivalent declared expectation structure.

Also ensure that expectations can represent:

- clean pass scenarios,
- pass-with-allowed-failure-observed scenarios,
- must-fail scenarios,
- must-block-release scenarios,
- and equivalence-only proof scenarios.

### [Task possible affected files]

- `src/certification/models.py`
- `src/certification/scenarios.py`
- `src/certification/conformance.py`
- expectation-model tests

### [Task important notes]

Do not keep scenario law spread across ad hoc test code.
Scenarios must declare their rules, not imply them.

### [Task check list]

- [ ] Audit current expectation fields
- [ ] Add missing expectation semantics
- [ ] Freeze scenario-to-expectation mapping
- [ ] Support allowed-failure scenarios explicitly
- [ ] Support lifecycle/release-proof expectations explicitly
- [ ] Add expectation-model tests
- [ ] Document expectation law

### [Task acceptance criteria]

Every certification scenario is governed by one complete exact expectation contract.

---

## [ ] (checkbox) - [Task 4] - Expand and normalize the certification failure taxonomy

### [Task Description]

Turn certification failure reporting into one explicit, comprehensive truth surface.

### [Task technical implementation]

Audit current `FailureKind` values and extend them to cover the full trust surface, including at least:

- reporting incomplete,
- telemetry gap,
- envelope failure,
- degradation-sequence failure,
- recovery-timeout failure,
- semantic drift,
- reproducibility failure,
- lifecycle startup failure,
- replay overflow or persistence-loss class if certification-relevant,
- manifest/proof-bundle incomplete,
- release-gate blocking failure,
- worker failure propagation class if certification-relevant,
- invalid proof artifact structure,
- missing required scenario,
- and any “certification misconfigured” class if needed.

For each failure kind define:

- exact trigger,
- severity,
- whether it is authoritative,
- whether it is operational,
- whether it can ever be allowlisted,
- how it must appear in proof output.

### [Task possible affected files]

- `src/certification/models.py`
- `src/certification/conformance.py`
- `src/certification/recorder.py`
- failure-taxonomy tests

### [Task important notes]

Do not create dozens of overlapping failure kinds.
Make the taxonomy small, exact, and useful.

### [Task check list]

- [ ] Audit existing failure kinds
- [ ] Add missing certification failure classes
- [ ] Freeze trigger rules for each class
- [ ] Freeze authoritative vs operational classification
- [ ] Freeze allowlist eligibility rules
- [ ] Add taxonomy tests
- [ ] Document failure taxonomy

### [Task acceptance criteria]

Certification failure kinds form one exact, complete, and operationally honest taxonomy.

---

## [ ] (checkbox) - [Task 5] - Harden honest allowed-failure semantics

### [Task Description]

Make sure whitelisted failure does not become hidden failure.

### [Task technical implementation]

The current code already preserves failure truth by returning success while retaining the observed failure kind and reason when the failure is allowlisted. Milestone E must turn that into one complete honest-reporting law.

Define and enforce:

1. **Allowed failure does not erase observed failure**
   - proof output must still record the failure kind,
   - proof output must still record the failure reason,
   - proof output must explicitly mark allowed-failure-observed.

2. **Allowed failure scope is scenario-bounded**
   - allowlists belong to scenario expectations,
   - not to global suppression.

3. **Allowed failure semantics are explicit in release truth**
   - a clean pass is distinct from a pass with allowed failure observed,
   - release-gate rules must declare whether allowed failures are acceptable for release.

4. **Allowed-failure misuse is impossible**
   - unlisted failures must fail,
   - wrong-kind allowlist must fail,
   - allowlist overbreadth must be prevented by exact failure-kind matching.

### [Task possible affected files]

- `src/certification/conformance.py`
- `src/certification/models.py`
- `src/certification/recorder.py`
- allowed-failure tests

### [Task important notes]

Do not let allowed failure become “green but lying.”
That would destroy the whole certification layer.

### [Task check list]

- [ ] Freeze allowed-failure reporting law
- [ ] Separate clean pass from allowed-failure pass
- [ ] Freeze scenario-scoped allowlists
- [ ] Add exact matching rules
- [ ] Add release-gate interaction rules
- [ ] Add allowed-failure honesty tests
- [ ] Document honest-reporting law

### [Task acceptance criteria]

Allowed failures remain fully visible, scenario-scoped, and impossible to confuse with clean success.

---

## [ ] (checkbox) - [Task 6] - Complete semantic-equivalence and reproducibility proof closure

### [Task Description]

Turn semantic drift and reproducibility checks into exact trust claims.

### [Task technical implementation]

Audit and harden certification support for:

- baseline-vs-final authoritative equivalence,
- local-vs-concurrent supported-slice equivalence,
- repeated-run reproducibility,
- quiet-run reproducibility,
- and scenario-specific non-equivalence boundaries.

Define exactly:

- when baseline hash comparison is required,
- when final-vs-secondary hash comparison is required,
- when state-level assertions are better than hash alone,
- which scenarios require reproducibility,
- which scenarios require only bounded recovery correctness,
- and which scenarios are intentionally non-equivalence scenarios.

Also ensure that certification output states:

- equivalence proven,
- reproducibility proven,
- equivalence not required,
- reproducibility not required,
- or equivalence/reproducibility failed.

### [Task possible affected files]

- `src/certification/conformance.py`
- `src/certification/harness.py`
- `src/engine/checkpoint.py`
- equivalence/reproducibility tests

### [Task important notes]

Do not overclaim reproducibility outside declared scope.
Do not use hash comparison where scenario truth requires richer assertions.

### [Task check list]

- [ ] Freeze equivalence proof rules
- [ ] Freeze reproducibility proof rules
- [ ] Freeze scenario-level proof requirements
- [ ] Add supported local-vs-concurrent certification scenarios
- [ ] Add repeated-run certification scenarios
- [ ] Add explicit non-equivalence boundaries
- [ ] Document equivalence/reproducibility law

### [Task acceptance criteria]

Equivalence and reproducibility claims are exact, scenario-scoped, and directly proven where declared.

---

## [ ] (checkbox) - [Task 7] - Complete measurement, telemetry, and sampling law for certification

### [Task Description]

Make certification measurements trustworthy enough that conformance results are meaningful.

### [Task technical implementation]

Audit and harden certification measurement rules for:

- sampling cadence,
- missing-sample behavior,
- telemetry-gap law,
- bounded measurement retention,
- measurement completeness,
- signal source truth,
- and measurement serialization into proof output.

Define exactly:

- required sampling interval per scenario,
- acceptable gap thresholds,
- what counts as reporting incomplete,
- what counts as telemetry-gap failure,
- how headless/system runs emit measurement points,
- and how measurement streams are attached to proof artifacts.

Ensure measurement capture remains bounded and does not violate earlier runtime envelope constraints.

### [Task possible affected files]

- `src/certification/models.py`
- `src/certification/harness.py`
- `src/certification/recorder.py`
- measurement-related tests

### [Task important notes]

Do not let certification pass on a half-blind measurement stream.
Do not let measurement verbosity reintroduce unbounded runtime overhead.

### [Task check list]

- [ ] Freeze sampling cadence law
- [ ] Freeze gap/incomplete-reporting law
- [ ] Freeze measurement serialization rules
- [ ] Freeze bounded retention rules
- [ ] Add telemetry completeness tests
- [ ] Add telemetry-gap tests
- [ ] Document certification measurement law

### [Task acceptance criteria]

Certification measurements are exact, bounded, and sufficient to support trustworthy conformance evaluation.

---

## [ ] (checkbox) - [Task 8] - Complete proof-bundle structure and recorder integrity

### [Task Description]

Turn certification output into one exact proof package rather than a loose directory of artifacts.

### [Task technical implementation]

Define and enforce one proof-bundle structure containing at least:

- proof manifest,
- scenario metadata,
- profile metadata,
- hardware class metadata,
- execution mode metadata,
- measurement stream or references,
- final authoritative hash/checkpoint references,
- equivalence/reproducibility results,
- conformance result summary,
- failure kind/reason if any,
- allowed-failure-observed marker if any,
- lifecycle result markers if relevant,
- and release-readiness markers if relevant.

Also define:

- file naming,
- schema versioning,
- required vs optional artifacts,
- partial-proof detection,
- and recorder failure behavior.

Ensure the recorder:

- writes deterministically,
- never silently drops required proof elements,
- and marks incomplete bundles explicitly if something fails.

### [Task possible affected files]

- `src/certification/recorder.py`
- `src/certification/models.py`
- proof-bundle tests
- release-bundle docs/tests

### [Task important notes]

Do not confuse “directory exists” with “proof exists.”
The bundle must be structurally and semantically complete.

### [Task check list]

- [ ] Freeze proof-bundle schema
- [ ] Freeze required artifact set
- [ ] Freeze naming/versioning rules
- [ ] Freeze incomplete-bundle detection
- [ ] Harden recorder failure semantics
- [ ] Add proof-bundle integrity tests
- [ ] Document proof-bundle law

### [Task acceptance criteria]

Certification proof output is one exact, checkable, deterministic proof bundle with explicit completeness semantics.

---

## [ ] (checkbox) - [Task 9] - Harden release-gate enforcement and proof completeness rules

### [Task Description]

Make release blocking depend on truth, not convention.

### [Task technical implementation]

Define one exact release-gate contract that checks at least:

- proof bundle directory exists,
- required manifest exists,
- required proof artifacts exist,
- required scenarios were run,
- required scenarios passed under declared release rules,
- no unallowed certification failures exist,
- allowed-failure rules for release are obeyed,
- final authoritative hash/checkpoint references exist where required,
- and artifact schema/integrity is valid.

Also define:

- whether release requires clean pass only,
- or whether some allowed-failure-observed outcomes are acceptable,
- and how that rule is represented in release metadata.

Add explicit blocking reasons for:

- missing bundle,
- incomplete bundle,
- missing scenario,
- scenario failed,
- proof schema invalid,
- or release policy violated.

### [Task possible affected files]

- `tests/certification/test_final_gate.py`
- release-gate helpers
- proof-bundle validation modules
- release docs

### [Task important notes]

Do not let the release gate check only existence.
It must check meaning.

### [Task check list]

- [ ] Freeze release-gate rule set
- [ ] Freeze required scenario set for release
- [ ] Freeze allowed-failure release policy
- [ ] Add explicit blocking reasons
- [ ] Add proof-schema validation to release gate
- [ ] Add release-block tests
- [ ] Document release-truth law

### [Task acceptance criteria]

Release gating is exact, proof-complete, and impossible to satisfy with decorative artifacts.

---

## [ ] (checkbox) - [Task 10] - Add certification coverage for subsystem, headless, and full-system proof layers

### [Task Description]

Make certification usable across the levels you actually care about: part of system, headless system, and full runtime.

### [Task technical implementation]

Define one certification layering model covering:

1. **Subsystem certification**
   - scheduler/governor/lifecycle/concurrency-specific scenarios,
   - direct contract proof at subsystem level.

2. **Headless engine certification**
   - end-to-end headless runtime scenarios,
   - lifecycle under headless operation,
   - equivalence and recovery under headless operation.

3. **Full-system certification**
   - integrated scenario bundles that combine:
     - runtime pressure,
     - lifecycle behavior,
     - concurrency behavior,
     - and proof output integrity.

For each layer define:

- purpose,
- artifact expectations,
- scenario types,
- required measurements,
- and release relevance.

Ensure the harness and scenario model can support all three layers cleanly.

### [Task possible affected files]

- `src/certification/harness.py`
- `src/certification/scenarios.py`
- `docs/engine/certification_layers.md`
- headless/full-system certification tests

### [Task important notes]

Do not flatten all certification into one giant scenario suite.
Different layers prove different things.

### [Task check list]

- [ ] Freeze subsystem certification layer
- [ ] Freeze headless certification layer
- [ ] Freeze full-system certification layer
- [ ] Map scenario families to layers
- [ ] Add layer-specific artifact rules
- [ ] Add layer-coverage tests
- [ ] Document certification layering model

### [Task acceptance criteria]

Certification supports exact subsystem, headless, and full-system proof layers without collapsing them into one vague test universe.

---

## [ ] (checkbox) - [Task 11] - Refactor certification responsibilities into clean proof boundaries

### [Task Description]

Remove proof-logic sprawl so certification remains understandable and trustworthy.

### [Task technical implementation]

Refactor the certification path so that:

- scenarios define expectations,
- harness runs scenarios and gathers measurements,
- conformance evaluator judges outcomes,
- recorder writes proof artifacts,
- proof-validator/release-gate checks bundle completeness,
- and docs define the claim surface.

Ensure that:

- harness does not contain conformance policy,
- conformance evaluator does not contain file-system release logic,
- recorder does not define scenario law,
- release gate does not duplicate conformance law,
- and certification state does not leak into authoritative runtime semantics.

### [Task possible affected files]

- `src/certification/harness.py`
- `src/certification/conformance.py`
- `src/certification/recorder.py`
- release-validation modules
- docs

### [Task important notes]

Do not build a meta-framework.
Just stop certification responsibilities from leaking across modules.

### [Task check list]

- [ ] Audit certification responsibility boundaries
- [ ] Keep scenario law separate from evaluation law
- [ ] Keep proof writing separate from proof validation
- [ ] Keep release logic separate from runtime logic
- [ ] Preserve deterministic behavior during refactor
- [ ] Document final certification boundaries

### [Task acceptance criteria]

Milestone E ends with one clean certification architecture rather than scattered proof logic.

---

## [ ] (checkbox) - [Task 12] - Complete the certification, proof, and release test suite

### [Task Description]

Pin Milestone E with direct proof-layer tests instead of relying on confidence from earlier milestones.

### [Task technical implementation]

Complete or add tests for these groups.

### Scenario and expectation tests

- every scenario has valid expectation mapping,
- scenario IDs are unique,
- expectation fields are complete,
- unsupported combinations are rejected.

### Failure taxonomy tests

- every failure kind triggers exactly under declared conditions,
- allowed vs unallowed failures behave correctly,
- clean pass vs allowed-failure pass remain distinct.

### Conformance tests

- envelope violations fail correctly,
- degradation-sequence failures fail correctly,
- recovery failures fail correctly,
- semantic-drift failures fail correctly,
- reproducibility failures fail correctly,
- telemetry-gap and incomplete-reporting failures fail correctly.

### Proof-bundle tests

- manifest completeness,
- required artifact completeness,
- incomplete-bundle detection,
- recorder failure marking,
- deterministic proof structure.

### Release-gate tests

- missing bundle blocks release,
- missing scenario blocks release,
- failed scenario blocks release,
- invalid proof schema blocks release,
- allowed-failure release policy is enforced exactly.

### Layered certification tests

- subsystem certification scenarios work,
- headless certification scenarios work,
- full-system certification scenarios work,
- proof outputs remain correct at each layer.

### Suggested test groups

- `tests/certification/test_scenario_matrix.py`
- `tests/certification/test_expectation_model.py`
- `tests/certification/test_failure_taxonomy.py`
- `tests/certification/test_allowed_failure_truth.py`
- `tests/certification/test_conformance_semantics.py`
- `tests/certification/test_proof_bundle_integrity.py`
- `tests/certification/test_release_gate.py`
- `tests/certification/test_certification_layers.py`

### [Task possible affected files]

- existing certification tests
- missing new Milestone E certification/proof test modules

### [Task important notes]

Do not rely on broad engine tests as a substitute.
Milestone E needs direct proof-layer law tests.

### [Task check list]

- [ ] Add scenario/expectation tests
- [ ] Add failure-taxonomy tests
- [ ] Add conformance-rule tests
- [ ] Add allowed-failure honesty tests
- [ ] Add proof-bundle integrity tests
- [ ] Add release-gate tests
- [ ] Add certification-layer tests

### [Task acceptance criteria]

The certification and release-trust layer is pinned by a complete direct proof suite.

---

## [ ] (checkbox) - [Task 13] - Add exact Milestone E documentation pack

### [Task Description]

Document the final trusted-claim surface of v2 so the engine says exactly what it proves and nothing more.

### [Task technical implementation]

Create:

- `docs/engine/certification_contract_me.md`
- `docs/engine/me_test_matrix.md`
- `docs/engine/certification_scenario_matrix.md`
- `docs/engine/certification_layers.md`

`certification_contract_me.md` must contain these exact sections:

- Purpose
- Scope of Milestone E
- What certification proves
- Scenario expectation law
- Failure taxonomy
- Honest allowed-failure law
- Equivalence and reproducibility law
- Measurement and telemetry law
- Proof-bundle law
- Release-gate law
- Certified claim scope language
- Non-goals
- Completion guarantees

`me_test_matrix.md` must contain these exact sections:

- Scenario and expectation tests
- Failure taxonomy tests
- Conformance-rule tests
- Allowed-failure honesty tests
- Proof-bundle integrity tests
- Release-gate tests
- Certification-layer tests
- Regression intent

For every test group, document:

- test name or group,
- input condition,
- exact certification rule,
- regression caught,
- whether it is scenario, conformance, artifact, release, or honesty coverage.

### [Task possible affected files]

- `docs/engine/certification_contract_me.md`
- `docs/engine/me_test_matrix.md`
- `docs/engine/certification_scenario_matrix.md`
- `docs/engine/certification_layers.md`

### [Task important notes]

Documentation is implementation here too.
This is the milestone where the project defines its final truth language.

### [Task check list]

- [ ] Document certification scope
- [ ] Document scenario law
- [ ] Document failure taxonomy
- [ ] Document allowed-failure honesty law
- [ ] Document equivalence/reproducibility law
- [ ] Document proof-bundle and release-gate law
- [ ] Document claim-scope language
- [ ] Document exact test matrix

### [Task acceptance criteria]

Milestone E has a complete documentation pack describing the finished certification and release-trust law.

---

## [ ] (checkbox) - [Task 14] - Add Milestone E regression guardrails

### [Task Description]

Make it hard for proof honesty and release truth to silently decay after Milestone E is declared complete.

### [Task technical implementation]

Add project-level guardrails that fail if:

- scenarios drift from the documented matrix,
- expectation models lose required fields,
- allowed-failure semantics become dishonest,
- proof bundles lose required artifacts,
- release gate weakens into existence-only checks,
- certified claim docs overstate scenario coverage,
- or certification state starts mixing with runtime semantics improperly.

This can be done with:

- doc-integrity tests,
- scenario-matrix integrity tests,
- proof-schema validation tests,
- release-gate integrity tests,
- and claim-scope consistency checks between docs and required scenario sets.

### [Task possible affected files]

- `tests/docs/*`
- `tests/certification/test_me_doc_integrity.py`
- CI config
- integrity helpers

### [Task important notes]

Do not create paperwork theater.
Just make proof regression visible and cheap to catch.

### [Task check list]

- [ ] Add certification doc/test integrity checks
- [ ] Add scenario-matrix regression guard
- [ ] Add proof-schema regression guard
- [ ] Add release-gate regression guard
- [ ] Add claim-scope consistency guard
- [ ] Record Milestone E completion gate

### [Task acceptance criteria]

Milestone E cannot silently regress without failing proof, release, or documentation integrity checks.

---

# [Recommended execution order inside Milestone E]

1. Task 1 — Freeze the certification law set
2. Task 2 — Expand and normalize the scenario catalog
3. Task 3 — Harden the scenario expectation model
4. Task 4 — Expand the failure taxonomy
5. Task 5 — Harden honest allowed-failure semantics
6. Task 6 — Complete equivalence and reproducibility proof closure
7. Task 7 — Complete measurement and sampling law
8. Task 8 — Complete proof-bundle structure and recorder integrity
9. Task 9 — Harden release-gate enforcement
10. Task 10 — Add subsystem/headless/full-system certification layers
11. Task 11 — Refactor certification boundaries
12. Task 12 — Complete the certification test suite
13. Task 13 — Finalize docs
14. Task 14 — Add guardrails

This order matters because it follows dependency reality:

- first define what certification means,
- then define what gets certified,
- then define how scenarios express truth,
- then define how failure is classified,
- then preserve honesty under allowlists,
- then prove equivalence and reproducibility where claimed,
- then ensure measurement is trustworthy,
- then make proof output structurally exact,
- then enforce release truth,
- then organize certification layers,
- then clean structure,
- then pin everything with direct tests,
- then lock docs and guardrails.

---

# [Milestone E done-means-done gate]

Milestone E is done only when all of these are true:

- certification scope is exact,
- scenario coverage matches the declared trust surface,
- every scenario has one exact expectation contract,
- failure kinds are complete and honest,
- allowed-failure results remain visibly distinct from clean pass,
- equivalence and reproducibility claims are exact and scenario-scoped,
- measurement and telemetry are sufficient and bounded,
- proof bundles are structurally complete and checkable,
- release gating depends on proof meaning, not mere artifact existence,
- subsystem, headless, and full-system certification layers are all explicit,
- docs and tests describe the same trusted-claim surface,
- and CI can catch regression in proof honesty or release truth.
