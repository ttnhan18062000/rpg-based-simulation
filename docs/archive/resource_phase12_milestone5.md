---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
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

Phase 12 ends when `src` becomes the operational default for supported scope. It does not end when every trace of old `src` is gone.

## [Milestone acceptance criteria]

At the end of this milestone:

- `src` is the default authority for supported operational use,
- residual legacy dependencies are explicit,
- the validated cutover boundary is explicit,
- and the branch has a formal “Phase 12 complete” handoff baseline for Phase 13.

---

## Task

### [ ] (checkbox) - [Task 1] - Declare `src` the default authority for supported operational surfaces

#### [Task Description]

Make the new runtime the real default for supported operation.

#### [Task technical implementation]

Update operational docs, runbooks, launch guidance, and workflow ownership so supported operational use now explicitly names `src` as the authoritative default.

#### [Task possible affected files]

- `README.md`
- runbook docs
- `docs/engine/phase12_validated_cutover_baseline.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

If people still reach for old `src` by default, this milestone is not done.

#### [Task check list]

- [x] Default authority is explicit
- [x] Runbooks reflect the new default
- [x] Workflow guidance reflects the new default
- [x] Supported scope is explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

`src` is explicitly declared the default authority for supported operational use.

---

### [ ] (checkbox) - [Task 2] - Publish residual old-`src` dependencies still intentionally allowed before retirement

#### [Task Description]

Expose what is still left, instead of pretending the migration is cleaner than it is.

#### [Task technical implementation]

Publish one residual-dependency package listing:

- old-`src` paths still live,
- why they are still live,
- whether they are rollback-only, reference-only, or still operationally required,
- and what Phase 13 is expected to do with each one.

#### [Task possible affected files]

- `docs/engine/phase12_residual_legacy_dependencies.md`
- `docs/engine/phase13_readiness_input.md`
- `docs/engine/phase12_validated_cutover_baseline.md`

#### [Task important notes]

A hidden residual dependency becomes a future outage or a permanent bridge. Usually both.

#### [Task check list]

- [x] Live old-src paths are listed
- [x] Reasons are explicit
- [x] Dependency type is explicit
- [x] Phase 13 expectation is explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

Residual old-`src` dependencies are explicit and classified.

---

### [ ] (checkbox) - [Task 3] - Publish the post-cutover support statement and Phase 13 readiness baseline

#### [Task Description]

Restate exactly what is now true after cutover and what retirement is allowed to assume.

#### [Task technical implementation]

Publish one post-cutover package covering:

- supported default-authority surfaces,
- remaining exclusions and caveats,
- validated cutover boundary,
- residual legacy dependencies,
- and explicit Phase 13 readiness assumptions.

#### [Task possible affected files]

- `docs/engine/phase12_post_cutover_support.md`
- `docs/engine/phase13_readiness_input.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

This is the bridge from operational truth to deletion discipline.

#### [Task check list]

- [x] Default-authority surfaces are explicit
- [x] Remaining caveats are explicit
- [x] Residual dependencies are explicit
- [x] Phase 13 assumptions are explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

The project has one explicit post-cutover support statement and Phase 13 readiness baseline.
