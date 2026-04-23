# [Milestone 6] - Phase 12 Cutover Baseline and Phase 11 Exit Package

## [Milestone Description]

Milestone 6 is the exit gate for Phase 11.

Its purpose is to convert final replacement truth into a constrained handoff baseline for Phase 12.

This milestone does not begin cutover itself.
It does not retire old `src`.
It does not reopen implementation.

It closes the ratification phase and defines what cutover is now allowed to rely on.

## [Milestone technical implementation]

Create one Phase 11 exit package that binds Phase 12 to the ratified truth.

This milestone must:

- publish the Phase 11 exit package,
- define exactly which supported surfaces Phase 12 may cut over,
- define which unsupported/divergent/retired surfaces must not be assumed during cutover,
- and link all cutover assumptions back to the final ledger and proof bundle.

This milestone must not:

- quietly let cutover assume more than was ratified,
- let unsupported scope disappear into silence,
- or treat “mostly replaced” as a cutover license.

## [Milestone important notes]

The trap here is impatience.

After all this work, people will want cutover immediately. That is exactly why the exit package must be limiting, not just celebratory.

## [Milestone acceptance criteria]

At the end of Milestone 6:

- the Phase 11 exit package is published,
- Phase 12 assumptions are explicit and bounded,
- unsupported/divergent scope remains visible,
- and the branch has a formal “Phase 11 complete” handoff baseline.

---

## Task

### [ ] (checkbox) - [Task 1] - Define the exact supported cutover surface allowed after Phase 11

#### [Task Description]

Tell Phase 12 exactly what it may rely on and nothing more.

#### [Task technical implementation]

Publish one cutover-allowed surface package listing:

- which preserved or divergent-but-supported surfaces are eligible for cutover,
- what execution modes are allowed,
- what consumers are in-scope,
- and what assumptions are still forbidden.

#### [Task possible affected files]

- `docs/engine/phase12_cutover_allowed_surface.md`
- `docs/engine/final_replacement_boundary.md`
- `docs/engine/phase12_readiness_input.md`

#### [Task important notes]

If Phase 12 gets a vague handoff, it will assume too much.

#### [Task check list]

- [ ] Allowed supported surfaces are explicit
- [ ] Allowed execution modes are explicit
- [ ] In-scope consumers are explicit
- [ ] Forbidden assumptions are explicit
- [ ] Artifact is reviewable

#### [Task acceptance criteria]

The exact supported cutover surface is explicit and bounded.

---

### [ ] (checkbox) - [Task 2] - Publish explicit cutover constraints for divergent, unsupported, and retired scope

#### [Task Description]

Make sure Phase 12 cannot quietly absorb non-preserved assumptions.

#### [Task technical implementation]

Publish one constraints package covering:

- divergent-but-supported constraints,
- unsupported-scope exclusions,
- retired-scope exclusions,
- and any operational caveats that must remain visible during cutover.

#### [Task possible affected files]

- `docs/engine/phase12_cutover_constraints.md`
- `docs/engine/final_replacement_boundary.md`
- `docs/engine/phase11_non_preserved_baseline.md`

#### [Task important notes]

Cutover constraints are not optional footnotes. They are part of the truth.

#### [Task check list]

- [ ] Divergent constraints are explicit
- [ ] Unsupported exclusions are explicit
- [ ] Retired exclusions are explicit
- [ ] Operational caveats are explicit
- [ ] Artifact is reviewable

#### [Task acceptance criteria]

Phase 12 cutover constraints are explicit and tied to ratified non-preserved scope.

---

### [ ] (checkbox) - [Task 3] - Publish the formal Phase 11 exit package and Phase 12 readiness input

#### [Task Description]

Close ratification with one package that cutover planning must obey.

#### [Task technical implementation]

Publish one Phase 11 exit package containing:

- the final proof bundle,
- the final replacement verdict,
- the final replacement boundary,
- the preserved and non-preserved baselines,
- the allowed cutover surface,
- the cutover constraints,
- and the formal statement of what Phase 11 completed and what Phase 12 is now allowed to assume.

#### [Task possible affected files]

- `docs/engine/phase11_exit_package.md`
- `docs/engine/phase12_readiness_input.md`
- milestone review docs

#### [Task important notes]

This is the line between “we think V2 can replace `src`” and “Phase 12 is now allowed to act on ratified replacement truth.”

#### [Task check list]

- [ ] Exit package is published
- [ ] Final proof bundle is linked
- [ ] Final verdict is linked
- [ ] Cutover boundaries are linked
- [ ] Phase 12 assumptions are explicit

#### [Task acceptance criteria]

The project has a complete and reviewable Phase 11 exit package and Phase 12 handoff baseline.
