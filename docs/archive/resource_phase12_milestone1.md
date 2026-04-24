Below is the **full detailed implementation plan for Phase 12**, in the same milestone/task structure style as your earlier implementation docs, and aligned with the Phase 12 high-level plan plus the ratification-first sequencing from [resource_phases.md](sandbox:/mnt/data/resource_phases.md) and the support/cutover discipline from [src_v2_principle.md](sandbox:/mnt/data/src_v2_principle.md).

# Detailed Implementation Plan — Phase 12 of `src_v2`

This plan assumes Phase 11 has already produced:

- a final proof bundle,
- a final replacement verdict,
- a final replacement boundary,
- preserved/divergent/unsupported/retired baselines,
- and a formal Phase 11 exit package that explicitly defines what cutover is allowed to assume.

Phase 12 is not a new implementation phase.

It is the phase where the project must turn ratified replacement truth into **operational default reality** for the supported system surface.

The cutover surface this phase is trying to close is:

- supported runtime entrypoints,
- supported consumer-facing execution paths,
- supported CI and operational workflows,
- supported replay/report/artifact generation paths,
- supported real-condition validation and rollback discipline,
- and the bounded post-cutover truth that Phase 13 retirement is allowed to rely on.

This document expands the high-level Phase 12 plan into implementation-ready milestone detail using the same milestone and task structure as the earlier plans.

---

# [Milestone 1] - Phase 11 Exit Closure and Phase 12 Readiness

## [Milestone Description]

Milestone 1 is the gate between ratified replacement truth and legitimate cutover execution.

Its purpose is to make sure Phase 12 does not inherit unstable scope, vague rollback expectations, or inflated operational assumptions from Phase 11.

By this point, the project may already have:

- a final replacement verdict,
- a final replacement boundary,
- and strong pressure to “just switch everything to V2.”

That is still not enough.

This milestone exists because Phase 12 should not proceed while:

- cutover-eligible surfaces are still mixed with unsupported/divergent/retired scope,
- consumer/workflow ownership is still vague,
- rollback expectations are still implicit,
- or operational cutover assumptions still exceed the Phase 11 verdict.

This milestone does not perform cutover itself.

It closes the ratification-to-operation handoff honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 12.

This milestone must complete readiness closure in six areas:

1. **Cutover-surface closure**
   - the exact cutover-eligible surfaces from Phase 11 must be frozen.

2. **Scope-separation closure**
   - supported cutover scope must be separated from unsupported/divergent/retired scope.

3. **Ownership closure**
   - consumer groups, workflows, and operator surfaces being moved to `src_v2` must be explicitly identified.

4. **Rollback closure**
   - rollback expectations, fallback behavior, and non-goals must be explicit.

5. **Constraint closure**
   - Phase 12 must be bound to the Phase 11 verdict rather than free-floating operational confidence.

6. **Phase 12 baseline closure**
   - the project must publish one formal “this is the cutover baseline entering Phase 12” package.

This milestone must not:

- reopen Phase 11 ratification except for genuine truth defects,
- silently expand the cutover surface,
- or let operational urgency override the ratified boundary.

## [Milestone important notes]

The trap here is impatience disguised as confidence.

If you let cutover scope outrun ratification scope, you are not migrating. You are gambling.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- the exact cutover surface is frozen,
- unsupported/divergent/retired scope remains visible,
- cutover ownership is explicit,
- rollback expectations are explicit,
- and the branch has a formal “Phase 12 ready” gate.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the exact Phase 12 cutover-eligible surface from the Phase 11 exit package

#### [Task Description]

Turn the ratified replacement truth into one explicit cutover target.

#### [Task technical implementation]

Create or refresh one Phase 12 cutover package covering only the surfaces explicitly allowed by the Phase 11 exit artifacts.

This task should:

- collect all cutover-eligible preserved and divergent-but-supported surfaces,
- exclude unsupported scope,
- exclude retired scope,
- exclude future retirement-only work,
- and publish the resulting cutover set as the official Phase 12 baseline.

#### [Task possible affected files]

- `docs/engine/phase12_cutover_allowed_surface.md`
- `docs/engine/phase12_readiness_input.md`
- `docs/engine/final_replacement_boundary.md`

#### [Task important notes]

Do not let “probably okay” surfaces sneak into cutover.

#### [Task check list]

- [x] Allowed surfaces are collected
- [x] Unsupported surfaces are excluded
- [x] Retired surfaces are excluded
- [x] Scope is frozen
- [x] Baseline is reviewable

#### [Task acceptance criteria]

The project has one explicit Phase 12 cutover-eligible surface.

---

### [ ] (checkbox) - [Task 2] - Publish explicit cutover ownership for consumers, workflows, and operator surfaces

#### [Task Description]

Make it clear who and what is actually moving in Phase 12.

#### [Task technical implementation]

Define the operational groups being migrated, including:

- runtime entry consumers,
- server/headless consumers,
- CI and automation paths,
- replay/report/proof workflows,
- and operator-facing execution surfaces.

#### [Task possible affected files]

- `docs/engine/phase12_cutover_ownership.md`
- `docs/engine/phase_dependency_map.md`
- `docs/engine/phase12_readiness_input.md`

#### [Task important notes]

If ownership is vague, responsibility will disappear the moment cutover gets messy.

#### [Task check list]

- [x] Consumer groups are explicit
- [x] Workflow groups are explicit
- [x] Operator surfaces are explicit
- [x] Ownership mapping is explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

The project has one explicit ownership map for Phase 12 cutover work.

---

### [ ] (checkbox) - [Task 3] - Publish rollback expectations, fallback rules, and explicit non-goals for Phase 12

#### [Task Description]

Stop Phase 12 from pretending cutover is irreversible or unlimited.

#### [Task technical implementation]

Publish one cutover-control package that defines:

- rollback expectations,
- fallback paths allowed during transition,
- explicit non-goals,
- and boundaries on what Phase 12 must not attempt.

#### [Task possible affected files]

- `docs/engine/phase12_rollback_plan.md`
- `docs/engine/phase12_cutover_constraints.md`
- `docs/engine/phase12_readiness_input.md`

#### [Task important notes]

If rollback is only assumed and not defined, it does not exist.

#### [Task check list]

- [x] Rollback expectations are explicit
- [x] Fallback rules are explicit
- [x] Non-goals are explicit
- [x] Constraints are explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

Rollback, fallback, and non-goals are explicit before cutover begins.

---

### [ ] (checkbox) - [Task 4] - Publish the formal Phase 12 entry package and readiness gate

#### [Task Description]

Turn the previous tasks into one explicit Phase 12 start decision.

#### [Task technical implementation]

Create one readiness gate that requires:

- frozen cutover-eligible scope,
- explicit ownership,
- explicit rollback/fallback definitions,
- ratification-bound constraints,
- and one published entry package defining the cutover baseline.

#### [Task possible affected files]

- `docs/engine/phase12_readiness_gate.md`
- `docs/engine/phase12_entry_package.md`
- milestone review docs

#### [Task important notes]

This is the line between “we want to cut over” and “we are ready to cut over.”

#### [Task check list]

- [x] Gate conditions are explicit
- [x] Gate conditions are reviewable
- [x] Supporting artifacts are linked
- [x] Known limitations are attached
- [x] Phase 12 entry is unambiguous

#### [Task acceptance criteria]

The branch has a precise and honest entry gate for Phase 12.
