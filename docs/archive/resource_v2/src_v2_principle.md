# V2 Developer Validation Handbook

## Purpose

This handbook defines the completion standard for every new code change in the V2 epic.

It exists to stop three failure modes:

- adding code that works locally but violates the V2 runtime contract,
- rewriting behavior from the original `src` without preserving intended logic,
- and shipping features without enough proof that they are deterministic, bounded, lifecycle-safe, and truthfully reported.

This handbook should be used as the validation checklist before any new slice, subsystem, feature, or refactor is considered complete.

The current V2 runtime already includes profile contracts, authoritative state, conformance evaluation, lifecycle-aware certification flow, scoped reporting, startup validation, and law-style tests. This handbook assumes those are the foundation and defines how all future work must fit on top of them.

---

# 1. Core development principles

## 1.1 Preserve intended behavior, not accidental legacy behavior

When porting logic from the original `src` into `src`, the goal is **not** to preserve every historical quirk automatically.

The goal is to preserve:

- intended gameplay semantics,
- stable deterministic behavior,
- user-visible or system-relevant outcomes,
- and meaningful edge-case behavior.

The goal is **not** to preserve blindly:

- bugs,
- undefined behavior,
- incidental ordering,
- hidden side effects,
- or architecture leaks from the old runtime.

### Validation checklist

- [ ] I can describe the intended behavior of this slice in plain language.
- [ ] I can distinguish intended behavior from accidental legacy behavior.
- [ ] Any intentional difference from original `src` is written down explicitly.
- [ ] No behavior difference is being justified with “the rewrite is cleaner” unless it is documented and tested as an intentional divergence.

---

## 1.2 `src` is the behavior oracle; `src` is the new contract implementation

The original `src` should be treated as:

- a behavior reference,
- a characterization-test target,
- a source of pure data/constants where safe,
- and a comparison oracle during porting.

It should **not** be treated as the runtime implementation to import wholesale into `src`.

### Validation checklist

- [ ] I used original `src` behavior as a reference where needed.
- [ ] I did not import old runtime orchestration, authority paths, or lifecycle logic directly into `src`.
- [ ] Any reused code from `src` is limited to pure data, pure formulas, or static definitions.
- [ ] The new implementation is native to `src`’s contracts.

---

## 1.3 The single-process V2 path remains the semantic baseline

All supported behavior in V2 must be grounded first in the local semantic baseline.

Concurrent execution, replay, monitoring, certification, and optimization sit on top of that baseline. They do not redefine it.

### Validation checklist

- [ ] This new code has a local single-process reference behavior.
- [ ] The meaning of the feature does not depend on worker timing, replay timing, or certification tooling.
- [ ] If concurrent execution is supported, it is explicitly compared against the local path.
- [ ] The authoritative result is defined first in baseline terms.

---

## 1.4 All authoritative mutation must remain singular

The apply path is the only place that should mutate authoritative state.

New code must not create convenience mutation shortcuts through:

- scheduler logic,
- worker logic,
- runtime status,
- replay logic,
- or certification helpers.

### Validation checklist

- [ ] I know exactly where authoritative mutation happens.
- [ ] My new code does not mutate authoritative state outside the approved apply path.
- [ ] No helper method or convenience shortcut mutates authoritative state silently.
- [ ] Prior state remains unchanged after applying updates.
- [ ] Tests prove no hidden mutation leak exists.

---

## 1.5 Runtime truth is part of correctness

If a feature changes runtime pressure, fallback behavior, shutdown semantics, or certification output, then runtime signals and lifecycle truth are part of the feature.

A feature is not complete if it “works” but lies operationally.

The V2 runtime already treats profiles, measurement points, lifecycle outcome, conformance, and scoped reports as first-class truth surfaces. New code must stay aligned with that.

### Validation checklist

- [ ] I identified what runtime signals this code affects.
- [ ] I identified whether this code affects lifecycle outcome, replay, fallback, or shutdown.
- [ ] I updated runtime status, metrics, or certification inputs if needed.
- [ ] I did not introduce decorative or ambiguous operational fields.

---

## 1.6 Every new supported behavior must be bounded

No new code is complete if it can grow state, work, or artifacts without a declared bound.

This applies to:

- queues,
- histories,
- replay payloads,
- packets,
- result payloads,
- diagnostics,
- caches,
- and proof artifacts.

### Validation checklist

- [ ] Every new collection has an explicit bound, retention window, or overflow policy.
- [ ] Every new payload has a declared size or shape limit.
- [ ] Any overflow behavior is explicit and tested.
- [ ] No new “temporary” unbounded structure was introduced.

---

# 2. The mandatory validation model for all new code

Every new code change must pass through **all** of the following validation layers.

## 2.1 Behavior characterization

If the change ports or preserves logic from original `src`, first capture the old behavior.

### Required evidence

- black-box tests against original behavior,
- examples of normal, edge, and invalid cases,
- deterministic outcome expectations,
- and any known intentional mismatch.

### Validation checklist

- [ ] I wrote characterization tests or scenario notes for original `src` behavior.
- [ ] I captured at least one normal case.
- [ ] I captured at least one edge case.
- [ ] I captured at least one invalid/guardrail case if applicable.
- [ ] I recorded any original behavior that should **not** be preserved.

---

## 2.2 Differential validation

For any rewritten slice, compare old behavior and new behavior under equivalent conditions.

### Required evidence

- same input state,
- same seed where applicable,
- same scenario,
- same expected semantic result,
- explicit comparison between `src` and `src`.

### Validation checklist

- [ ] I compared original `src` and `src` for the slice where parity is expected.
- [ ] I compared final state or authoritative deltas directly.
- [ ] I investigated every mismatch.
- [ ] Every accepted mismatch is documented as an intentional divergence.

---

## 2.3 V2 contract validation

Even if the new code matches old behavior, it still must obey V2 rules.

### Required evidence

- authoritative mutation path compliance,
- deterministic baseline behavior,
- profile-bound behavior,
- lifecycle-safe behavior,
- and proof/report compatibility where relevant.

### Validation checklist

- [ ] The feature obeys V2 state boundaries.
- [ ] The feature obeys V2 lifecycle semantics.
- [ ] The feature obeys V2 profile and boundedness rules.
- [ ] The feature obeys V2 conformance/reporting semantics where relevant.
- [ ] No legacy shortcut was preserved just to match old behavior.

---

## 2.4 Regression-proof validation

A feature is not complete if it cannot be defended against future breakage.

### Required evidence

- direct tests,
- integrity checks,
- docs updated,
- and clear “done means done” rules.

### Validation checklist

- [ ] I added direct tests for the new behavior.
- [ ] I added regression tests for the most likely failure mode.
- [ ] I updated relevant docs.
- [ ] I did not rely on vague indirect test coverage.

---

# 3. Required test categories for every new feature or slice

A feature is not complete until the correct categories of tests exist.

## 3.1 Characterization tests

Use when preserving behavior from original `src`.

### Checklist

- [ ] Tests describe what original `src` does.
- [ ] Tests are black-box where possible.
- [ ] Tests cover normal and edge behavior.
- [ ] Tests do not assume the rewrite is correct.

---

## 3.2 Differential tests

Use when porting from `src` to `src`.

### Checklist

- [ ] Same scenario is executed against `src` and `src`.
- [ ] The comparison target is explicit:
  - [ ] final authoritative state
  - [ ] deltas
  - [ ] deterministic hash
  - [ ] lifecycle-visible outcome

- [ ] Every mismatch is explained.

---

## 3.3 Contract tests

Use for V2-specific law enforcement.

The V2 test suite already demonstrates this style through profile validation, anti-thrashing, lifecycle conformance, release proof, and allowed-failure truth. New code must follow the same model.

### Checklist

- [ ] The feature has direct V2 contract tests.
- [ ] Tests verify authoritative boundaries.
- [ ] Tests verify deterministic or equivalent behavior where required.
- [ ] Tests verify boundedness.
- [ ] Tests verify lifecycle/reporting effects where relevant.

---

## 3.4 Property or invariant tests

Use when the feature has broad correctness rules.

### Examples

- movement never exceeds allowed step,
- readiness never goes below declared floor,
- queue growth never exceeds bound,
- fallback never mutates state outside apply,
- shutdown outcome remains stable under timeout conditions.

### Checklist

- [ ] I identified the key invariants for this code.
- [ ] I added tests for those invariants.
- [ ] I covered at least one failure or invalid-input path.

---

# 4. Completion checklist for every new code change

Use this section as the default “ready to merge” checklist.

## 4.1 Scope and intent

- [ ] I can describe exactly what this change adds, changes, or ports.
- [ ] I can explain why this change belongs in the current epic phase.
- [ ] I can state whether this is:
  - [ ] new behavior
  - [ ] ported behavior
  - [ ] refactor only
  - [ ] contract repair
  - [ ] performance-only change

- [ ] I can state whether original `src` parity is required.

## 4.2 Original behavior preservation

- [ ] I reviewed original `src` behavior for this slice.
- [ ] I captured expected old behavior before or during implementation.
- [ ] I compared `src` and `src` where parity matters.
- [ ] I wrote down every intentional divergence.

## 4.3 V2 authority and determinism

- [ ] The new code does not mutate authoritative state outside the apply path.
- [ ] Deterministic behavior is preserved where required.
- [ ] The local path remains the semantic baseline.
- [ ] Any concurrent support is explicitly scoped and proven, not assumed.

## 4.4 Runtime truth and lifecycle truth

- [ ] I identified whether the feature affects:
  - [ ] runtime signals
  - [ ] replay behavior
  - [ ] shutdown behavior
  - [ ] certification outcome
  - [ ] proof bundle content

- [ ] I updated lifecycle handling if the feature changes shutdown/finalization behavior.
- [ ] I updated certification or conformance input if the feature changes certified truth.
- [ ] I did not collapse meaningful outcomes into vague success/fail states.

## 4.5 Boundedness

- [ ] Every new list, queue, buffer, packet, or artifact has a bound.
- [ ] Overflow behavior is explicit.
- [ ] Retention behavior is explicit.
- [ ] No “temporary” unbounded growth is introduced.

## 4.6 Test coverage

- [ ] Characterization tests exist where needed.
- [ ] Differential tests exist where needed.
- [ ] Contract tests exist.
- [ ] Regression tests exist.
- [ ] Failure-path tests exist.
- [ ] No critical behavior is validated only manually.

## 4.7 Documentation

- [ ] The code change is reflected in the relevant handbook/law/test-matrix docs.
- [ ] Any new runtime field, lifecycle state, or proof artifact is documented.
- [ ] Any intentional divergence from original `src` is documented.
- [ ] Terminology stays aligned with enums and manifest-monitored names. The existing V2 docs tests already enforce terminology and structural alignment, so new docs must remain consistent with that discipline.

## 4.8 Evidence of completion

- [ ] I can point to the exact tests that prove this change.
- [ ] I can point to the exact docs that describe this change.
- [ ] I can state the remaining known limitations.
- [ ] I can state what is **not** supported yet.

---

# 5. Porting checklist from original `src` into `src`

Use this when moving any RPG-core logic into V2.

## 5.1 Slice selection

- [ ] The porting target is narrow and well-defined.
- [ ] The porting target does not bundle multiple subsystems unnecessarily.
- [ ] The porting target is small enough to validate fully.

## 5.2 Old behavior capture

- [ ] I identified the old entry points in `src`.
- [ ] I identified old state dependencies.
- [ ] I identified old side effects.
- [ ] I identified hidden assumptions that should not come into V2.

## 5.3 V2 contract mapping

- [ ] I defined what authoritative state V2 needs for this slice.
- [ ] I defined what input/work item V2 needs for this slice.
- [ ] I defined what apply-path output V2 expects for this slice.
- [ ] I defined what runtime/lifecycle/certification implications this slice has.

## 5.4 Rebuild, not blind transplant

- [ ] I implemented the slice natively in `src`.
- [ ] I did not import old runtime orchestration code directly.
- [ ] Any reused old code is pure and contract-safe.
- [ ] The slice fits V2’s authority, lifecycle, and proof model.

## 5.5 Porting completion

- [ ] The slice matches original behavior where intended.
- [ ] Divergences are documented.
- [ ] V2 contract tests pass.
- [ ] Runtime/lifecycle/certification effects are covered.
- [ ] The slice is ready to become “officially supported” if that is the goal.

---

# 6. Special validation rules by epic concern

## 6.1 For semantic baseline changes

If the change affects the baseline engine path:

- [ ] phase order remains explicit,
- [ ] apply-path exclusivity remains intact,
- [ ] scheduler ordering remains deterministic,
- [ ] checkpoint/hash purity remains intact,
- [ ] local baseline semantics remain independent of concurrent execution timing.

---

## 6.2 For runtime signal or governor changes

If the change affects runtime pressure or control:

- [ ] every mode-driving field has one exact source,
- [ ] no decorative signal is being used for policy,
- [ ] anti-thrashing still works,
- [ ] bounded history rules still hold,
- [ ] runtime status remains truthful.

The current V2 tests already exercise anti-thrashing and recovery confidence behavior; new signal-related code must preserve that standard.

---

## 6.3 For replay, startup, or shutdown changes

If the change affects lifecycle behavior:

- [ ] startup invalid states are still rejected early,
- [ ] replay remains bounded,
- [ ] timeout/failure states remain distinct,
- [ ] final authoritative truth is preserved,
- [ ] certification and lifecycle reporting remain aligned.

The current V2 code already feeds lifecycle outcome into conformance, so changes here must preserve that truth chain.

---

## 6.4 For concurrency-related changes

If the change affects worker execution or supported concurrent slices:

- [ ] local baseline meaning is still primary,
- [ ] packet and result contracts are explicit,
- [ ] authoritative commit order does not depend on race timing,
- [ ] fallback behavior is visible and bounded,
- [ ] equivalence is proven only for declared supported scope.

---

## 6.5 For certification or proof changes

If the change affects certification, conformance, recorder output, or release proof:

- [ ] allowed failures remain honest,
- [ ] failure kinds remain explicit,
- [ ] lifecycle outcomes remain truthful,
- [ ] artifact naming is consistent across code and tests,
- [ ] reports remain scoped to profile/scenario/hardware/commit context.

The current V2 certification code and tests already enforce honest allowed failures, scoped report language, and release target binding; new changes must not weaken those guarantees.

---

# 7. Divergence log requirement

Every time `src` intentionally does not match original `src`, record it.

## Required divergence log fields

- slice or subsystem
- old behavior
- new behavior
- reason for divergence
- whether divergence is:
  - [ ] bug fix
  - [ ] contract hardening
  - [ ] boundedness fix
  - [ ] lifecycle truth fix
  - [ ] certification truth fix
  - [ ] intentional gameplay change

- tests proving the new truth
- docs updated

### Checklist

- [ ] I created or updated the divergence log.
- [ ] I did not leave a behavior mismatch unexplained.
- [ ] The divergence is intentional, not accidental.

---

# 8. Review checklist for code review or self-review

Use this before merge.

## 8.1 Behavior review

- [ ] What exact behavior changed?
- [ ] What old behavior was preserved?
- [ ] What old behavior was intentionally changed?
- [ ] What evidence proves that?

## 8.2 Contract review

- [ ] Does this violate authority boundaries?
- [ ] Does this change determinism expectations?
- [ ] Does this change profile-bounded behavior?
- [ ] Does this change lifecycle truth?
- [ ] Does this change certification truth?

## 8.3 Test review

- [ ] Are the tests direct enough?
- [ ] Are edge cases covered?
- [ ] Is there at least one failure-path test?
- [ ] Is parity tested where required?
- [ ] Are docs/integrity tests still valid?

## 8.4 Operational review

- [ ] Could this cause hidden runtime pressure?
- [ ] Could this create unbounded growth?
- [ ] Could this introduce ambiguous metrics?
- [ ] Could this make proof artifacts inconsistent?
- [ ] Could this break release-gate assumptions?

## 8.5 Merge readiness

- [ ] No known critical gap remains for the declared scope.
- [ ] Limitations are explicit.
- [ ] The code is ready for the next slice or next phase.

---

# 9. Completion gates for official support

A slice is not “officially supported” just because it exists.

It becomes officially supported only when all of these are true:

- [ ] behavior is implemented in `src`
- [ ] original behavior has been characterized if needed
- [ ] parity is verified where intended
- [ ] divergences are documented
- [ ] V2 contract tests pass
- [ ] runtime/lifecycle/certification truth is preserved
- [ ] boundedness is explicit
- [ ] docs are updated
- [ ] future regressions are catchable

If one of these is missing, the slice is still experimental.

---

# 10. What must never be accepted as “done”

Reject any change that matches any of these patterns:

- [ ] “It works manually.”
- [ ] “It probably matches the old behavior.”
- [ ] “The rewrite is cleaner, so drift is acceptable.”
- [ ] “The tests pass, but we did not compare against original behavior.”
- [ ] “We will document the divergence later.”
- [ ] “We used a temporary unbounded buffer.”
- [ ] “The lifecycle state is close enough.”
- [ ] “The certification report is basically correct.”
- [ ] “Fallback happened, but we did not surface it.”
- [ ] “The new code mutates state directly only in one helper.”

These are not completion states.
These are unfinished states.

---

# 11. Final completion statement template

Use this template whenever declaring a new code slice complete.

## Completion statement

- [ ] **Scope completed:** `<slice / subsystem / feature>`
- [ ] **Original `src` behavior reviewed:** yes / no
- [ ] **Characterization tests added:** yes / no
- [ ] **Differential tests added:** yes / no / not applicable
- [ ] **V2 contract tests added:** yes / no
- [ ] **Lifecycle/runtime/certification impact reviewed:** yes / no
- [ ] **Boundedness reviewed:** yes / no
- [ ] **Intentional divergences documented:** yes / no / none
- [ ] **Docs updated:** yes / no
- [ ] **Known limitations remaining:** `<list>`
- [ ] **Ready for official support:** yes / no

---

# 12. Final principle

A rewrite into `src` is complete only when it preserves intended original behavior **and** satisfies the new V2 runtime contract.

Not one or the other.

Both.

That is the standard this handbook enforces.
