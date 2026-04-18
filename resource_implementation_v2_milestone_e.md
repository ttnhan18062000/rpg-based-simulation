[Milestone E] - Certification, Proof, and Production Readiness

[Milestone Description]
Milestone E is the fifth and final v2 completion milestone. Its purpose is **not** to introduce certification for the first time. Its purpose is to turn the current certification harness and documentation system into a real proof system and a real production-readiness gate.

The current code already has:

- structured certification models,
- hardware classification,
- a harness,
- conformance evaluation,
- a recorder,
- documentation-integrity tests,
- contributor guardrails,
- and a lawbook/playbook direction.

That means the proof architecture exists. The problem is that it is still too shallow:

- conformance evaluation is still thinner than the milestone language,
- scenario expectation models are too small,
- failure taxonomy and evidence quality need hardening,
- report honesty needs stronger enforcement,
- docs/code terminology alignment is still incomplete,
- and production-readiness claims are still too close to aspiration.

This milestone exists to fix that.

[Milestone technical implementation]
Create one fully trustworthy proof system and make production-readiness claims evidence-backed rather than optimistic.

This milestone must implement these exact rules:

### Proof-system completion rules

1. **Machine-readable certification remains the source of truth**
   - Structured certification artifacts remain primary.
   - Human-readable reports remain derivative.
   - CI and release gates rely on structured evidence.

2. **Conformance must become multi-dimensional and exact**
   - Envelope compliance,
   - degradation-order compliance,
   - recovery compliance,
   - semantic equivalence where required,
   - reporting completeness,
   - and profile/scenario/environment binding must all be explicit.

3. **Scenario expectations must become explicit**
   - required modes,
   - required recovery,
   - semantic-equivalence requirement,
   - allowed failure kinds,
   - sampling cadence,
   - runtime bounds,
   - and expected proof shape must all be explicit.

4. **Failure taxonomy must be exact**
   - Failure kinds must be complete, explicit, and testable.
   - No ambiguous “failed somehow” outcomes are allowed.

5. **Report language must remain honest**
   - No universal performance claims.
   - All throughput and safety claims must be bound to:
     - runtime profile,
     - certification scenario,
     - hardware class,
     - and whether the hardware class was detected or overridden.

6. **Documentation and contribution law must be hardened**
   - Manifest-driven required docs,
   - terminology alignment,
   - extension templates,
   - contributor guardrails,
   - and CI-failing integrity checks must all be exact.

### Runtime contract boundaries

7. **What this milestone must cover**
   - This milestone must complete:
     - certification scenario model,
     - conformance logic,
     - baseline-vs-certified equivalence proof,
     - failure taxonomy,
     - report honesty,
     - doc/playbook integrity,
     - and production-readiness gating.

8. **Non-goals of this milestone**
   - Do not add new gameplay semantics here.
   - Do not add distributed cluster certification here.
   - Do not weaken earlier milestone boundaries here.

9. **Clean-code boundary**

- Certification models, scenario definitions, conformance evaluation, recording/reporting, and documentation-integrity enforcement must remain separated into explicit responsibilities.
- Do not let markdown reports become the source of truth.
- Do not let “green tests” replace structured evidence.

[Milestone important notes]
The first trap in this milestone is treating certification as a benchmark runner. It is not. It is the evidence system for whether the engine obeys its own laws.

The second trap is allowing failure reasons to remain vague. If a run fails, the reason must be exact enough to act on.

The third trap is allowing report language to become marketing language. Production readiness without scoped evidence is fraud.

The fourth trap is thinking the docs are done because files exist. Lawbooks, playbooks, manifests, templates, and terminology checks must agree with code and reports.

[Milestone acceptance criteria]
At the end of Milestone E, the codebase has:

- one fully trustworthy machine-readable certification system,
- one fully explicit conformance model,
- one fully explicit scenario expectation model,
- one fully explicit structured failure taxonomy,
- one fully honest and enforceable report language model,
- one fully hardened docs/playbook integrity system,
- and one real production-readiness gate based on evidence.

No new engine semantics are required for Milestone E completion.

## Task

[ ] (checkbox) - [Task 1] - Audit and freeze the proof-system contract

[Task Description]
Create the exact completion contract for certification, conformance, scenario expectations, reporting, and docs/playbook enforcement. This task turns the current certification architecture into one finished law set.

[Task technical implementation]
Create one new proof-system contract document and one code-facing contract section that define exactly:

### Certification contract

- machine-readable artifact law,
- profile/scenario/hardware binding law,
- baseline equivalence law,
- scenario expectation law,
- failure taxonomy law,
- reporting honesty law.

### Documentation/guardrail contract

- required-doc manifest law,
- terminology-alignment law,
- extension-template law,
- contributor-guardrail law,
- CI integrity-failure law.

### Non-goals

- no gameplay changes,
- no distributed cluster certification,
- no weakening of earlier milestone rules.

[Task possible affected files]

- `docs/engine/proof_system_contract_me.md`
- `docs/engine/me_test_matrix.md`
- code-facing certification/playbook integrity notes

[Task important notes]
Do not leave “pass/fail” as the whole certification story.

Do not leave report honesty as a cultural hope instead of a rule.

[Task check list]

- [ ] Freeze certification law
- [ ] Freeze scenario expectation law
- [ ] Freeze failure taxonomy law
- [ ] Freeze reporting honesty law
- [ ] Freeze docs/playbook guardrail law
- [ ] Define explicit non-goals

[Task acceptance criteria]
The project has one exact proof-system contract that defines the finished law set for certification, reporting, and documentation guardrails.

---

[ ] (checkbox) - [Task 2] - Deepen certification scenario and conformance models

[Task Description]
Make certification evidence richer, more explicit, and more enforceable.

[Task technical implementation]
Complete and harden:

1. **Scenario expectations**
   - required governor modes,
   - required recovery,
   - semantic equivalence requirement,
   - allowed failure kinds,
   - sampling cadence,
   - tick/runtime limit,
   - scenario-specific proof expectations.

2. **Conformance evaluation**
   - envelope compliance,
   - degradation-order compliance,
   - recovery compliance,
   - semantic equivalence compliance,
   - reporting completeness compliance,
   - invalid-scenario/environment handling.

3. **Baseline binding**
   - baseline run identity,
   - baseline artifact binding,
   - exact comparison semantics,
   - explicit reproducibility metadata.

[Task possible affected files]

- `src_v2/certification/models.py`
- `src_v2/certification/conformance.py`
- `src_v2/certification/harness.py`
- related scenario definition modules

[Task important notes]
Do not keep scenario models too thin.

Do not reduce conformance to ceiling violations only.

[Task check list]

- [ ] Deepen scenario expectation model
- [ ] Deepen conformance logic
- [ ] Deepen baseline binding/equivalence logic
- [ ] Freeze exact pass/fail reasoning
- [ ] Document final proof model

[Task acceptance criteria]
Certification scenarios and conformance logic are explicit, complete, and capable of proving more than simple resource ceilings.

---

[ ] (checkbox) - [Task 3] - Harden structured failure taxonomy and honest reporting

[Task Description]
Make certification outputs operationally trustworthy by ensuring failures are exact and report language cannot overclaim.

[Task technical implementation]
Complete and harden:

1. **Failure taxonomy**
   - expand or finalize explicit failure kinds,
   - make failure reasons structured and actionable,
   - forbid vague generic failure states.

2. **Hardware-class integrity**
   - record detected hardware class,
   - record effective hardware class,
   - record override status,
   - keep override behavior explicit in reports and JSON.

3. **Honest reporting**
   - all claims bound to profile/scenario/hardware class,
   - no universal throughput language,
   - no unscoped safety language,
   - report-language compliance checks enforced.

[Task possible affected files]

- `src_v2/certification/models.py`
- `src_v2/certification/recorder.py`
- report-language compliance tests
- hardware classification integration modules

[Task important notes]
Do not allow override status to be hidden.

Do not leave report truthfulness to manual review only.

[Task check list]

- [ ] Finalize explicit failure taxonomy
- [ ] Finalize hardware-class reporting integrity
- [ ] Finalize honest report language rules
- [ ] Add report-language enforcement checks
- [ ] Document final reporting law

[Task acceptance criteria]
Certification failures are exact, reports are scoped and honest, and environment binding is explicit and testable.

---

[ ] (checkbox) - [Task 4] - Harden docs/playbook/guardrail integrity and production-readiness gating

[Task Description]
Turn the documentation and contributor control system into a real release and maintenance gate.

[Task technical implementation]
Complete and harden:

1. **Required-doc manifest**
   - required architecture docs declared in one manifest,
   - mandatory headers declared,
   - manifest-driven integrity tests.

2. **Terminology alignment**
   - runtime modes,
   - replay modes,
   - hardware classes,
   - failure kinds,
   - and other contract-critical terms must align between code and docs.

3. **Extension templates**
   - runtime profile template,
   - certification scenario template,
   - subsystem extension template,
   - retention/budget declaration template.

4. **Contributor guardrails**
   - no unbounded retained collections,
   - no universal performance claims,
   - no alternate authority paths,
   - no telemetry leakage into authoritative state,
   - no undocumented degradation behavior.

5. **Production-readiness gate**
   - release requires certification evidence,
   - release requires docs integrity,
   - release requires no outstanding law placeholders.

[Task possible affected files]

- `docs/engine/manifest.json`
- `docs/engine/engineering_playbook_m10.md`
- `docs/engine/project_lawbook_m10.md`
- `CONTRIBUTING.md`
- docs-integrity test modules
- CI validation integration

[Task important notes]
Do not let docs remain “nice to have.”

Do not let contributor rules stay purely cultural.

[Task check list]

- [ ] Harden manifest-driven docs integrity
- [ ] Harden terminology alignment checks
- [ ] Add/finish extension templates
- [ ] Harden contributor guardrails
- [ ] Define production-readiness release gate
- [ ] Document final lawbook/playbook rules

[Task acceptance criteria]
Documentation integrity, contributor guardrails, and production-readiness gating are enforceable, testable, and incapable of drifting silently.

---

[ ] (checkbox) - [Task 5] - Complete the proof-system test suite and final evidence gate

[Task Description]
Close the last proof gap so the engine’s “ready” claim is evidence-backed and enforceable.

[Task technical implementation]
Complete or add exact tests for:

### Certification proof tests

- deterministic baseline equivalence,
- semantic drift detection,
- degradation-before-failure,
- recovery compliance,
- structured failure-kind correctness,
- hardware override recording correctness.

### Reporting tests

- honest report language,
- scoped performance language,
- machine-readable artifact completeness,
- markdown derivative alignment.

### Docs/guardrail tests

- required-doc existence,
- required-section existence,
- terminology alignment,
- extension template presence,
- contributor-guardrail presence,
- forbidden-language checks.

### Suggested test groups

- `tests_v2/certification/test_envelope_violations.py`
- `tests_v2/certification/test_harness_contract.py`
- `tests_v2/certification/test_resilience_recovery.py`
- `tests_v2/certification/test_certification_determinism.py`
- `tests_v2/docs/test_doc_integrity.py`
- `tests_v2/docs/test_contributor_guardrails.py`

[Task possible affected files]

- existing certification and docs test modules
- any missing new final proof-system tests

[Task important notes]
Do not treat passing markdown generation as proof.

This milestone is about final evidence quality.

[Task check list]

- [ ] Finish certification-proof tests
- [ ] Finish failure-taxonomy tests
- [ ] Finish report-honesty tests
- [ ] Finish docs/playbook integrity tests
- [ ] Make final release gate exact and enforceable

[Task acceptance criteria]
The final proof-system layer is pinned by a complete deterministic test suite proving certification truth, reporting truth, docs/playbook integrity, and production-readiness gating.

---

[ ] (checkbox) - [Task 6] - Add exact Milestone E documentation pack

[Task Description]
Document the completed proof system so the engine’s final trust model is written down as exact law rather than inferred from code and tests.

[Task technical implementation]
Create:

- `docs/engine/proof_system_contract_me.md`
- `docs/engine/me_test_matrix.md`

`proof_system_contract_me.md` must contain these exact sections:

- Purpose
- Scope of Milestone E
- Machine-readable certification law
- Scenario expectation law
- Conformance law
- Failure taxonomy law
- Honest reporting law
- Docs/playbook guardrail law
- Production-readiness gate
- Non-goals
- Completion guarantees

`me_test_matrix.md` must contain these exact sections:

- Certification proof tests
- Semantic equivalence tests
- Recovery/degradation tests
- Failure-taxonomy tests
- Report-honesty tests
- Docs/playbook integrity tests
- Regression intent

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/engine/proof_system_contract_me.md`
- `docs/engine/me_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.

Do not end Milestone E with code and passing tests only. The final trust model must be written down exactly.

[Task check list]

- [ ] Document machine-readable certification law
- [ ] Document scenario/conformance law
- [ ] Document failure-taxonomy law
- [ ] Document honest reporting law
- [ ] Document docs/playbook guardrail law
- [ ] Document production-readiness gate
- [ ] Document the exact test matrix

[Task acceptance criteria]
Milestone E has a complete exact documentation pack describing the finished proof system and the tests that freeze it.

---

Priority Plan

What must change in mindset or assumptions
Stop treating certification as a nicer test runner and docs as a cleanup step. This milestone is where the engine earns the right to claim readiness.

What actions must be taken immediately
Freeze the proof-system contract, deepen scenario and conformance models, harden failure taxonomy and report honesty, harden docs/playbook integrity, and complete the final evidence gate.

What must stop or be eliminated
Stop relying on green tests without structured evidence. Stop vague failure reasons. Stop unscoped performance language. Stop documentation drift between code, reports, and lawbook.

The consequences and opportunity cost if this fails
The engine may be technically strong, but it still will not have a trustworthy proof system or a trustworthy maintenance-control system. That means “production-ready” will remain a belief, not a fact.
