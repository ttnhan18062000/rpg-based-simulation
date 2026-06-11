---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
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

## Task

### [ ] (checkbox) - [Task 1] - Define the exact removable versus still-live old-`src` surface after cutover

#### [Task Description]

Tell Phase 13 exactly what it may touch and what it must not.

#### [Task technical implementation]

Publish one retirement-surface package listing:

- old-`src` paths still operationally live,
- old-`src` paths now removable,
- old-`src` paths retained for rollback/reference only,
- and the evidence that supports each classification.

#### [Task possible affected files]

- `docs/engine/phase13_retirement_surface.md`
- `docs/engine/phase12_residual_legacy_dependencies.md`
- `docs/engine/phase13_readiness_input.md`

#### [Task important notes]

If Phase 13 gets a vague handoff, it will either delete too much or too little.

#### [Task check list]

- [x] Live paths are explicit
- [x] Removable paths are explicit
- [x] Rollback/reference-only paths are explicit
- [x] Evidence is linked
- [x] Artifact is reviewable

#### [Task acceptance criteria]

The exact removable versus still-live old-`src` surface is explicit and bounded.

---

### [ ] (checkbox) - [Task 2] - Publish explicit legacy-retirement constraints based on validated cutover truth

#### [Task Description]

Make sure Phase 13 inherits discipline instead of enthusiasm.

#### [Task technical implementation]

Publish one retirement-constraints package covering:

- what cannot be removed yet,
- what may be removed in what order,
- what residual rollback guarantees must be preserved during retirement,
- and what evidence Phase 13 must keep visible while retiring legacy paths.

#### [Task possible affected files]

- `docs/engine/phase13_retirement_constraints.md`
- `docs/engine/phase12_validated_cutover_baseline.md`
- `docs/engine/phase13_readiness_input.md`

#### [Task important notes]

Retirement constraints are not bureaucratic. They are how you avoid self-inflicted outages.

#### [Task check list]

- [x] Non-removable constraints are explicit
- [x] Removal-order constraints are explicit
- [x] Rollback guarantees are explicit
- [x] Evidence-retention constraints are explicit
- [x] Artifact is reviewable

#### [Task acceptance criteria]

Phase 13 retirement constraints are explicit and tied to validated cutover truth.

---

### [ ] (checkbox) - [Task 3] - Publish the formal Phase 12 exit package and Phase 13 readiness input

#### [Task Description]

Close cutover with one package that retirement work must obey.

#### [Task technical implementation]

Publish one Phase 12 exit package containing:

- the validated cutover baseline,
- the default-authority declaration,
- the post-cutover support statement,
- the residual legacy dependency list,
- the removable-versus-live legacy surface,
- the retirement constraints,
- and the formal statement of what Phase 12 completed and what Phase 13 is now allowed to assume.

#### [Task possible affected files]

- `docs/engine/phase12_exit_package.md`
- `docs/engine/phase13_readiness_input.md`
- milestone review docs

#### [Task important notes]

This is the line between “we are running on V2” and “we are now allowed to remove legacy runtime with discipline.”

#### [Task check list]

- [x] Exit package is published
- [x] Cutover baseline is linked
- [x] Default-authority declaration is linked
- [x] Retirement constraints are linked
- [x] Phase 13 assumptions are explicit

#### [Task acceptance criteria]

The project has a complete and reviewable Phase 12 exit package and Phase 13 handoff baseline.
