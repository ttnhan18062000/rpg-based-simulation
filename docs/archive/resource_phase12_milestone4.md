# [Milestone 4] - Real-Condition Cutover Validation and Rollback Discipline

## [Milestone Description]

Milestone 4 validates that the cutover works under real operational conditions and remains bounded by rollback discipline.

Its purpose is to ensure the project is not declaring operational victory based only on lab conditions.

This milestone covers:

- supported end-to-end runtime validation,
- supported consumer-flow validation,
- rollback path validation,
- cutover health checks,
- and explicit monitoring of unsupported/divergent assumptions during the transition.

It is about operational confidence under ratified scope, not broad new testing theory.

## [Milestone technical implementation]

Validate supported cutover surfaces under realistic use and enforce rollback discipline.

This milestone must:

- run supported end-to-end validation on the cutover surface,
- confirm supported artifacts and workflows behave as expected,
- verify rollback or fallback procedures still work while needed,
- verify no forbidden unsupported scope is being implicitly relied on,
- and document operational findings against the ratified cutover boundary.

This milestone must not:

- use unbounded “it seems stable” language,
- treat absence of immediate failure as full validation,
- or let rollback disappear before Phase 13 is ready.

## [Milestone important notes]

The trap here is optimism under load.

A cutover is not valid because it worked once. It is valid because supported operational paths behave correctly and rollback remains real while the transition is incomplete.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported cutover surfaces have real-condition validation,
- rollback discipline remains explicit,
- forbidden assumptions remain visible,
- and the project has one credible validated cutover slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Run supported end-to-end operational validation against the cutover-eligible surface

#### [Task Description]

Validate the cutover under realistic supported conditions.

#### [Task technical implementation]

Execute end-to-end validation on the supported cutover surface, covering:

- runtime entry,
- supported consumer paths,
- supported workflow paths,
- supported artifact production,
- and supported operator-visible execution behaviors.

#### [Task possible affected files]

- `tests/e2e/**`
- operational validation scripts
- runbook validation notes

#### [Task important notes]

This is not a synthetic demo pass. It is operational validation against the allowed surface.

#### [Task check list]

- [x] Runtime entry is validated
- [x] Consumer paths are validated
- [x] Workflow paths are validated
- [x] Artifact production is validated
- [x] Findings are documented

#### [Task acceptance criteria]

The supported cutover surface has end-to-end operational validation coverage.

---

### [ ] (checkbox) - [Task 2] - Validate rollback and fallback procedures while old `src` is still intentionally available

#### [Task Description]

Prove rollback is real before legacy retirement begins.

#### [Task technical implementation]

Exercise the defined rollback/fallback paths for supported cutover surfaces and verify:

- rollback instructions are correct,
- fallback behavior still works,
- no hidden dependency makes rollback impossible,
- and operational runbooks reflect reality.

#### [Task possible affected files]

- `docs/engine/phase12_rollback_plan.md`
- runbook docs
- rollback validation notes

#### [Task important notes]

A rollback plan that has not been exercised is documentation theater.

#### [Task check list]

- [x] Rollback instructions are exercised
- [x] Fallback behavior is exercised
- [x] Hidden blockers are identified
- [x] Runbooks are updated
- [x] Validation is documented

#### [Task acceptance criteria]

Rollback and fallback procedures are real, exercised, and documented.

---

### [ ] (checkbox) - [Task 3] - Check for implicit reliance on unsupported, divergent, or retired scope during cutover validation

#### [Task Description]

Make sure operational success is not secretly leaning on forbidden assumptions.

#### [Task technical implementation]

During validation, explicitly inspect whether any supported cutover path is still depending on:

- unsupported legacy behavior,
- divergent behavior without declared constraints,
- retired paths,
- or old-`src` residuals outside the allowed transition boundary.

#### [Task possible affected files]

- validation notes
- `docs/engine/phase12_cutover_constraints.md`
- `docs/engine/phase_dependency_map.md`

#### [Task important notes]

If success depends on hidden forbidden scope, the cutover is fraudulent.

#### [Task check list]

- [x] Unsupported reliance is checked
- [x] Divergent constraints are checked
- [x] Retired-scope reliance is checked
- [x] Residual old-src reliance is checked
- [x] Findings are documented

#### [Task acceptance criteria]

Cutover validation explicitly checks and constrains forbidden assumptions.

---

### [ ] (checkbox) - [Task 4] - Publish the validated cutover baseline and operational findings

#### [Task Description]

Turn validation results into one explicit operational baseline.

#### [Task technical implementation]

Publish one validated cutover baseline summarizing:

- supported paths validated,
- rollback/fallback status,
- known operational caveats,
- forbidden assumptions that were checked,
- and any residual constraints that Phase 13 must respect.

#### [Task possible affected files]

- `docs/engine/phase12_validated_cutover_baseline.md`
- `docs/engine/phase12_cutover_constraints.md`
- runbook docs

#### [Task important notes]

This artifact must say what is true, not what is convenient.

#### [Task check list]

- [x] Validated paths are explicit
- [x] Rollback status is explicit
- [x] Caveats are explicit
- [x] Forbidden-assumption checks are explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

The project has one explicit validated cutover baseline.
