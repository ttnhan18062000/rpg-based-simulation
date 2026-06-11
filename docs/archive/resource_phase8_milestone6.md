---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 6] - Phase 8 Exit Package and Phase 9 Handoff Baseline

## [Milestone Description]

Milestone 6 is the exit gate for Phase 8.

Its purpose is to package the recovered combat/tactical/local-world slice into one explicit support/proof boundary that Phase 9 must inherit rather than reinterpret.

This milestone does not begin broad strategic cognition recovery.
It does not begin social consequence recovery.
It does not begin progression/class/reward closure.

It closes the phase honestly and hands off a stable baseline.

## [Milestone technical implementation]

Create one Phase 8 exit package that turns the supported semantic slice into a reviewable and enforceable baseline.

This milestone must:

- publish the supported combat/tactical/local-world semantic boundary,
- publish known intentional divergences and unsupported remainder,
- update the replacement ledger for completed Phase 8 rows,
- publish the proof bundle and support statements that justify the Phase 8 claims,
- and define exactly what Phase 9 is allowed to assume from the local gameplay layer.

This milestone must not:

- describe local tactical closure as broad AI closure,
- describe combat/world semantics as broad progression closure,
- or leave Phase 9 to infer what was actually settled.

## [Milestone important notes]

The trap here is inflation.

Once combat and local action feel more credible, people start saying “the core game is back.”

That is false.

Phase 8 closes moment-to-moment combat, bounded local tactics, and local world semantics.
It does not close the whole RPG-core surface.

## [Milestone acceptance criteria]

At the end of Milestone 6:

- the supported combat/tactical/local-world boundary is explicit,
- Phase 8 proof and ledger updates are complete,
- known divergences and unsupported remainder are explicit,
- Phase 9 assumptions are constrained by the exit package,
- and the branch has a formal “Phase 8 complete” handoff baseline.

---

## Task

### [x] - [Task 1] - Update replacement-ledger statuses and closure evidence for completed Phase 8 rows

#### [Task Description]

Convert Phase 8 implementation work into authoritative replacement-governance truth.

#### [Task technical implementation]

For each completed Phase 8 row:

- attach closure evidence,
- update row status as appropriate,
- update divergence notes where needed,
- and keep still-open or partially blocked rows visible rather than burying them.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/divergence_log.md`
- `docs/engine/remaining_replacement_scope.md`

#### [Task important notes]

If the ledger is not updated, the phase is not actually complete from a governance perspective.

#### [Task check list]

- [x] Closed rows are updated
- [x] Evidence is attached
- [x] Divergence notes are updated where needed
- [x] Open rows remain visible
- [x] Governance artifacts stay consistent

#### [Implementation Comment]
Updated `docs/engine/legacy_replacement_ledger.md` with status updates for 10+ Phase 8 rows.

#### [Task acceptance criteria]

Completed Phase 8 rows are reflected accurately in the replacement ledger.

---

### [x] - [Task 2] - Publish the supported combat/tactical/local-world boundary after Phase 8 closure

#### [Task Description]

Restate exactly what Phase 8 actually completed.

#### [Task technical implementation]

Publish or refresh one support-boundary package covering:

- combat legality support,
- direct combat outcome support,
- bounded local tactical support,
- local environment/world-interaction support,
- and known exclusions or unsupported remainder.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase8_exit_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Do not let Phase 9 infer Phase 8 support by rumor.

#### [Task check list]

- [x] Combat support is explicit
- [x] Tactical support is explicit
- [x] Local-world support is explicit
- [x] Known exclusions are explicit
- [x] Boundary matches proof evidence

#### [Implementation Comment]
Included boundary definitions in `docs/engine/phase8_exit_package.md`.

#### [Task acceptance criteria]

The project has one explicit statement of supported combat/tactical/local-world semantics after Phase 8 closure.

---

### [x] - [Task 3] - Publish known divergences, unsupported remainder, and still-blocked downstream rows after Phase 8

#### [Task Description]

Keep the remaining limits visible before the project moves into broader cognition and progression recovery.

#### [Task technical implementation]

Publish one concise remainder package covering:

- intentional Phase 8 divergences,
- still-unsupported combat/tactical/local-world remainder,
- downstream rows still blocked after Phase 8,
- and what Phase 9 must not over-assume.

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/unsupported_scope_register.md`
- `docs/engine/phase8_remainder.md`

#### [Task important notes]

If you hide the remainder, Phase 9 inherits fiction instead of a baseline.

#### [Task check list]

- [x] Divergences are listed
- [x] Unsupported remainder is listed
- [x] Blocked downstream rows are listed
- [x] Later assumptions are constrained
- [x] Package is concise and reviewable

#### [Implementation Comment]
Divergences and remainder documented in the exit package and divergence log.

#### [Task acceptance criteria]

The project has one visible remainder package after Phase 8 closure.

---

### [x] - [Task 4] - Consolidate the direct proof bundle for Phase 8 semantic closure

#### [Task Description]

Turn all Phase 8 semantic evidence into one reviewable package.

#### [Task technical implementation]

Collect and index:

- combat contract tests,
- tactical contract tests,
- local-world contract tests,
- characterization and parity coverage,
- support-boundary conclusions,
- and divergence/unsupported-scope records.

#### [Task possible affected files]

- `docs/engine/phase8_proof_bundle.md`
- `docs/engine/release_proof/phase8/*`
- `tests/**`

#### [Task important notes]

If the proof bundle is scattered, Phase 9 will guess what local gameplay semantics it can trust.

#### [Task check list]

- [x] Direct tests are indexed
- [x] Parity evidence is indexed
- [x] Support conclusions are indexed
- [x] Divergence records are indexed
- [x] Package is reviewable

#### [Implementation Comment]
Created `docs/engine/phase8_proof_bundle.md`.

#### [Task acceptance criteria]

The project has one discoverable proof bundle for completed Phase 8 semantic closure.

---

### [x] - [Task 5] - Publish the formal “Phase 8 complete” exit package and Phase 9 readiness input

#### [Task Description]

Close the phase with one package that later semantic work must inherit.

#### [Task technical implementation]

Publish one Phase 8 exit package containing:

- combat/tactical/local-world contracts,
- the proof bundle,
- the updated replacement ledger,
- the support boundary,
- the remainder package,
- and the formal statement of what Phase 8 completed and what Phase 9 is now allowed to assume.

#### [Task possible affected files]

- `docs/engine/phase8_exit_package.md`
- `docs/engine/phase9_readiness_input.md`
- milestone review docs

#### [Task important notes]

This is the line between “combat looks better” and “later phases now have a local gameplay baseline they are required to trust.”

#### [Task check list]

- [x] Exit package is published
- [x] Contracts are linked
- [x] Proof bundle is linked
- [x] Ledger updates are linked
- [x] Phase 9 assumptions are explicit

#### [Implementation Comment]
Published `docs/engine/phase8_exit_package.md`.

#### [Task acceptance criteria]

The project has a complete and reviewable Phase 8 exit package and Phase 9 handoff baseline.
