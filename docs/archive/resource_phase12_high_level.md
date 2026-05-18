Below is the **high-level implementation plan for Phase 12** in the same milestone style as the earlier high-level phase plans.

This plan is grounded in the corrected roadmap and the ratification-first sequencing from [resource_phases.md](sandbox:/mnt/data/resource_phases.md) and the support/cutover discipline from [src_principle.md](sandbox:/mnt/data/src_principle.md).

---

# High-Level Implementation Plan — Phase 12 of `src`

This plan assumes Phase 11 has already produced:

- a final proof bundle,
- a final replacement verdict,
- a final replacement boundary,
- preserved/divergent/unsupported/retired baselines,
- and a formal Phase 11 exit package that explicitly defines what cutover is allowed to assume.

It also assumes the project has stopped pretending that ratified replacement truth automatically equals operational cutover.

Phase 12 is not the phase where the project should widen into new semantics, new compatibility closure, or legacy retirement.

It is the phase where `src` must become the **actual default operational surface** for the supported system.

The purpose of Phase 12 is:

- move supported execution paths from old `src` to `src`,
- move supported consumer-facing entrypoints and workflows to `src`,
- move CI, release, replay/report, and operational workflows to `src`,
- validate that supported cutover paths work under real operational conditions,
- keep unsupported/divergent/retired scope visible during the transition,
- and publish the operational cutover baseline that Phase 13 legacy retirement is allowed to rely on.

This is the phase where the ratified replacement claim becomes operational fact.

---

# [Milestone 1] - Phase 11 Exit Closure and Phase 12 Readiness

## [Milestone Description]

Milestone 1 is the entry gate for Phase 12.

Its purpose is to stop the team from starting cutover execution while Phase 11 truth is still unstable, overstated, or not actually constraining the work.

By this point, the project may already have:

- a final replacement verdict,
- a final replacement boundary,
- and strong pressure to “just switch everything to V2.”

That is still not enough.

This milestone exists because Phase 12 should not proceed while:

- cutover assumptions still exceed the ratified supported surface,
- unsupported/divergent/retired scope is not visibly constrained,
- consumer/workflow ownership for cutover is still vague,
- or rollback expectations are still undefined.

This milestone does not perform cutover itself.

It closes the ratification-to-operation handoff honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 12.

This milestone must:

- freeze the exact cutover-eligible surfaces from Phase 11,
- separate allowed cutover scope from unsupported/divergent/retired scope,
- define the consumer/workflow groups that will move to `src`,
- confirm rollback expectations and non-goals are explicit,
- and publish one formal “Phase 12 begins from this cutover baseline” record.

This milestone must not:

- reopen Phase 11 ratification except for genuine truth defects,
- silently expand the cutover surface,
- or let “operational urgency” override the ratified boundary.

## [Milestone important notes]

The trap here is impatience disguised as confidence.

If you let cutover scope outrun ratification scope, you are no longer migrating. You are gambling.

## [Milestone acceptance criteria]

At the end of this milestone:

- the exact cutover surface is frozen,
- unsupported/divergent/retired scope remains visible,
- cutover ownership is explicit,
- rollback expectations are explicit,
- and the branch has an explicit “Phase 12 ready” gate.

---

# [Milestone 2] - Supported Runtime Entrypoint and Consumer Cutover

## [Milestone Description]

Milestone 2 moves the supported entry and consumer-facing runtime surface to `src`.

Its purpose is to make `src` the default operational runtime for the cutover-allowed surface.

This milestone covers:

- supported CLI/entry usage,
- supported runtime server/serve paths,
- supported consumer entrypoints,
- supported headless/default runtime invocation,
- and supported direct operator-facing execution paths.

It is about real operational routing, not new feature work.

It does not yet close CI/release workflow migration or full operational artifact transition.

## [Milestone technical implementation]

Cut over supported runtime entry surfaces to `src` in a controlled way.

This milestone must:

- switch supported default entrypoints to `src`,
- switch supported serve/headless/runtime consumers to `src`,
- preserve explicit constraints for unsupported or divergent surfaces,
- validate that operator-visible behavior remains within the ratified cutover boundary,
- and keep fallback/rollback paths visible while cutover is still in progress.

This milestone must not:

- silently reroute unsupported consumers,
- treat partial entry migration as full operational cutover,
- or blur cutover success with residual dual-runtime behavior.

## [Milestone important notes]

The trap here is fake defaultness.

If old `src` is still the thing people really depend on, then you have not cut over, no matter what the roadmap says.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported runtime entrypoints default to `src`,
- supported consumers run through `src`,
- unsupported/divergent surfaces remain constrained,
- and the project has one credible runtime-entry cutover slice.

---

# [Milestone 3] - Workflow, CI, and Operational Artifact Cutover

## [Milestone Description]

Milestone 3 moves the project’s internal operating workflows to `src`.

Its purpose is to make the team’s own execution, testing, replay/report, and release routines depend on `src` rather than old `src`.

This milestone covers:

- CI/runtime invocation,
- replay/report/proof generation,
- artifact production,
- automated validation workflows,
- and internal/operator workflows that still point at old `src`.

It is about operational dependency migration, not feature closure.

It does not yet close final production-style validation or legacy retirement.

## [Milestone technical implementation]

Cut over supported project workflows and artifacts to `src`.

This milestone must:

- switch CI paths and validation jobs to `src`,
- switch replay/report/proof generation paths to `src`,
- switch release/build or packaging flows to `src` where ratified,
- ensure operational artifacts come from the new supported source of truth,
- and preserve visibility of any workflows still intentionally excluded.

This milestone must not:

- keep old `src` as the real hidden dependency while claiming migration,
- allow artifact truth to come from mixed runtimes,
- or overclaim completion if core workflows still depend on old `src`.

## [Milestone important notes]

The trap here is ceremonial migration.

If CI and artifact generation still lean on the old runtime, the organization itself is telling you what the real system still is.

## [Milestone acceptance criteria]

At the end of this milestone:

- supported CI and operational workflows run on `src`,
- supported artifacts are generated from `src`,
- mixed-runtime truth surfaces are eliminated where cutover was allowed,
- and the project has one credible workflow/artifact cutover slice.

---

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

# [Milestone 5] - Default-Authority Transition and Phase 13 Readiness Baseline

## [Milestone Description]

Milestone 5 turns the validated cutover into the new default authority for supported operation.

Its purpose is to establish `src` as the real operational default before legacy runtime retirement begins.

This milestone covers:

- default-authority declaration for supported surfaces,
- final cutover boundary publication,
- residual old-`src` dependency visibility,
- post-cutover support statement,
- and the handoff baseline for legacy retirement.

It is the closure milestone for cutover truth.

## [Milestone technical implementation]

Publish and enforce `src` as the supported operational default for the ratified cutover surface.

This milestone must:

- declare `src` the default authority for supported operational use,
- publish any remaining residual old-`src` dependencies still allowed before retirement,
- restate the cutover boundary after validation,
- publish what Phase 13 is now allowed to remove,
- and define what must still remain until retirement is complete.

This milestone must not:

- pretend legacy dependencies are gone if they still exist,
- let unsupported/divergent scope disappear from view,
- or confuse default-authority transition with full legacy retirement.

## [Milestone important notes]

The trap here is premature cleanup language.

Phase 12 ends when `src` becomes the operational default for supported scope. It does **not** end when every trace of old `src` is gone.

## [Milestone acceptance criteria]

At the end of this milestone:

- `src` is the default authority for supported operational use,
- residual legacy dependencies are explicit,
- the validated cutover boundary is explicit,
- and the branch has a formal “Phase 12 complete” handoff baseline for Phase 13.

---

# [Milestone 6] - Phase 12 Exit Package and Legacy-Retirement Constraints

## [Milestone Description]

Milestone 6 is the exit gate for Phase 12.

Its purpose is to bind Phase 13 legacy retirement to the real post-cutover truth rather than to wishful assumptions.

This milestone does not retire old `src` itself.
It does not reopen semantics or compatibility.
It does not expand the cutover surface.

It closes cutover and defines what retirement is now allowed to touch.

## [Milestone technical implementation]

Create one Phase 12 exit package that constrains Phase 13.

This milestone must:

- publish the Phase 12 exit package,
- define exactly what old-`src` paths are still live versus eligible for removal,
- define retirement constraints based on validated cutover truth,
- and link all retirement assumptions back to the final replacement verdict and Phase 12 validation output.

This milestone must not:

- silently imply that cutover means retirement is trivial,
- let residual old-`src` dependencies disappear into ambiguity,
- or allow Phase 13 to remove anything not explicitly authorized.

## [Milestone important notes]

The trap here is triumphalism.

After cutover, people start talking like retirement is automatic. That is how teams delete the wrong things or keep the wrong bridges forever.

## [Milestone acceptance criteria]

At the end of this milestone:

- the Phase 12 exit package is published,
- legacy-retirement constraints are explicit,
- live versus removable old-`src` paths are explicit,
- and the branch has a formal “Phase 12 complete” handoff baseline.

---

## Why these milestones do not duplicate each other

Milestone 2 is about **runtime entry and supported consumer cutover**.

Milestone 3 is about **workflow, CI, and operational-artifact cutover**.

Milestone 4 is about **real-condition validation and rollback discipline**.

Milestone 5 is about **default-authority transition**, not retirement.

Milestone 6 is about **retirement constraints and handoff**, not deletion.

If you merge these, you will create a fake “cutover phase” that sounds decisive and hides the difference between being default, being validated, and being safe to retire against.
