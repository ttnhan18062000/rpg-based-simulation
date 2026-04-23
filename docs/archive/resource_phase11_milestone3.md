# [Milestone 3] - Divergence, Unsupported, and Retired-Scope Ratification

## [Milestone Description]

Milestone 3 closes the truth story for everything not preserved.

Its purpose is to ensure that intentional divergences, unsupported legacy behaviors, and retired scope are all explicit, justified, and discoverable.

This milestone covers:

- intentional divergence records,
- unsupported-scope records,
- retired-scope records,
- rationale completeness,
- and support-matrix alignment for all non-preserved rows.

It is about explicit non-equivalence, not preserved parity.

## [Milestone technical implementation]

Reconcile every non-preserved row against formal policy and explicit documentation.

This milestone must:

- verify every intentionally divergent row has explicit rationale and evidence,
- verify every unsupported row is named and constrained,
- verify every retired row has a real retirement rationale,
- align all non-preserved rows with the support matrix and replacement ledger,
- and eliminate silent or ambiguous non-preserved scope.

This milestone must not:

- leave known differences buried in tests or code comments,
- confuse unsupported with retired,
- or treat undocumented differences as harmless.

## [Milestone important notes]

The trap here is embarrassment-driven omission.

Teams hate documenting what they did not preserve. That discomfort is the entire point of this milestone.

## [Milestone acceptance criteria]

At the end of Milestone 3:

- every non-preserved row has explicit status and rationale,
- divergence/unsupported/retired boundaries are clean,
- support claims do not silently imply broader parity,
- and non-preserved scope is fully ratified.

---

## Task

### [ ] (checkbox) - [Task 1] - Enumerate all intentionally divergent, unsupported, and retired rows across the ledger

#### [Task Description]

Create the full non-preserved universe for ratification review.

#### [Task technical implementation]

Collect every row currently marked:

- intentionally divergent,
- unsupported,
- or retired,

and group them by subsystem and non-preserved type.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase11_non_preserved_review.md`

#### [Task important notes]

Do not let non-preserved rows remain scattered across separate artifact families.

#### [Task check list]

- [ ] Divergent rows are collected
- [ ] Unsupported rows are collected
- [ ] Retired rows are collected
- [ ] Grouping is explicit
- [ ] Review package is stable

#### [Task acceptance criteria]

The project has one explicit non-preserved review package.

---

### [ ] (checkbox) - [Task 2] - Verify rationale completeness for all intentionally divergent rows

#### [Task Description]

Make every accepted mismatch an explicit design decision.

#### [Task technical implementation]

For each intentionally divergent row, verify the record includes:

- old behavior,
- new behavior,
- reason for divergence,
- divergence category,
- linked tests or proof where relevant,
- and updated support/doc state.

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/replacement_ledger.md`
- `docs/engine/phase11_non_preserved_review.md`

#### [Task important notes]

If you cannot explain a divergence clearly, you have not earned the divergence label.

#### [Task check list]

- [ ] Old behavior is described
- [ ] New behavior is described
- [ ] Reason is explicit
- [ ] Evidence is linked where relevant
- [ ] Docs/support alignment is checked

#### [Task acceptance criteria]

Every intentionally divergent row has complete rationale and traceability.

---

### [ ] (checkbox) - [Task 3] - Verify rationale completeness for all unsupported and retired rows

#### [Task Description]

Make omission explicit instead of silent.

#### [Task technical implementation]

For each unsupported row, verify:

- the unsupported behavior is named,
- the non-support rationale is explicit,
- and consumer assumptions are constrained.

For each retired row, verify:

- retirement reason is explicit,
- the row is truly out of active replacement scope,
- and retirement is not being used to hide unresolved work.

#### [Task possible affected files]

- `docs/engine/unsupported_scope_register.md`
- `docs/engine/retired_scope_register.md`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Unsupported and retired are not euphemisms. They need real policy behind them.

#### [Task check list]

- [ ] Unsupported rationale is explicit
- [ ] Retired rationale is explicit
- [ ] Consumer assumptions are constrained
- [ ] Fake retirements are challenged
- [ ] Review notes are recorded

#### [Task acceptance criteria]

Every unsupported and retired row has complete rationale and constrained meaning.

---

### [ ] (checkbox) - [Task 4] - Publish the ratified non-preserved-scope baseline

#### [Task Description]

Turn non-preserved truth into an official artifact instead of scattered caveats.

#### [Task technical implementation]

Publish one non-preserved baseline summarizing:

- intentional divergences,
- unsupported scope,
- retired scope,
- and any corrections made during ratification.

#### [Task possible affected files]

- `docs/engine/phase11_non_preserved_baseline.md`
- `docs/engine/divergence_log.md`
- `docs/engine/support_matrix.md`

#### [Task important notes]

This is where the project earns honesty about what it did not preserve.

#### [Task check list]

- [ ] Divergences are summarized
- [ ] Unsupported scope is summarized
- [ ] Retired scope is summarized
- [ ] Corrections are listed
- [ ] Artifact is reviewable

#### [Task acceptance criteria]

The project has one ratified non-preserved-scope baseline.
