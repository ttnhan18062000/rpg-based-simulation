---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 2] - Preserved-Surface Proof Closure and Coverage Reconciliation

## [Milestone Description]

Milestone 2 closes the proof story for all rows claimed as preserved.

Its purpose is to verify that every preserved behavior across semantic and compatibility surfaces actually has the evidence required to keep the “preserved” label.

This milestone covers:

- preserved gameplay-semantic rows,
- preserved substrate/runtime rows,
- preserved compatibility rows,
- coverage reconciliation between tests/docs/ledger,
- and downgrading preserved claims that are not actually proven.

It is about preserved-scope truth, not divergences or unsupported scope.

## [Milestone technical implementation]

Reconcile every preserved row against actual proof and support criteria.

This milestone must:

- confirm that each preserved row has appropriate characterization, differential, contract, black-box, or lifecycle proof,
- verify that proof scope matches the actual support claim,
- remove or downgrade preserved claims that are not sufficiently evidenced,
- and publish the reconciled preserved-surface baseline.

This milestone must not:

- rely on broad green suites as a substitute for row-level proof,
- keep preserved labels on rows that are only “probably correct,”
- or use vague confidence language instead of evidence.

## [Milestone important notes]

The trap here is proof inflation.

A branch with many tests creates false confidence. Phase 11 has to be row-honest, not suite-honest.

## [Milestone acceptance criteria]

At the end of Milestone 2:

- every preserved row has explicit supporting evidence,
- proof scope matches support scope,
- weak preserved claims are downgraded or corrected,
- and preserved replacement truth is no longer overstated.

---

## Task

### [ ] (checkbox) - [Task 1] - Enumerate all rows currently labeled preserved across Phases 5 through 10

#### [Task Description]

Create the exact surface that must survive preserved-proof review.

#### [Task technical implementation]

Collect every ledger row currently marked preserved and group them by subsystem family:

- resource/town/progression slices,
- substrate/runtime slices,
- combat/tactical/local-world slices,
- strategic/social/progression slices,
- compatibility slices.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase11_preserved_review.md`

#### [Task important notes]

This task is about scope assembly, not about deciding sufficiency yet.

#### [Task check list]

- [ ] All preserved rows are collected
- [ ] Rows are grouped by subsystem
- [ ] Duplicate preserved rows are eliminated
- [ ] Review package is stable
- [ ] Scope is reviewable

#### [Task acceptance criteria]

The project has one explicit preserved-row review package.

---

### [ ] (checkbox) - [Task 2] - Reconcile each preserved row against its required proof type and actual evidence

#### [Task Description]

Check whether each preserved claim is actually earned.

#### [Task technical implementation]

For each preserved row, verify:

- which proof types are required,
- which proof artifacts currently exist,
- whether the linked artifacts actually test the preserved behavior claimed,
- and whether the evidence is current and specific enough.

#### [Task possible affected files]

- `docs/engine/phase11_preserved_review.md`
- `docs/engine/replacement_ledger.md`
- phase proof bundle docs
- tests indexes

#### [Task important notes]

A row with tests nearby is not the same thing as a row with proof.

#### [Task check list]

- [ ] Required proof type is identified
- [ ] Actual evidence is linked
- [ ] Evidence matches the row claim
- [ ] Scope mismatch is recorded where found
- [ ] Review output is explicit

#### [Task acceptance criteria]

Every preserved row has an explicit proof sufficiency review.

---

### [ ] (checkbox) - [Task 3] - Downgrade or correct preserved rows whose support claims exceed their proof

#### [Task Description]

Remove dishonest preserved labels.

#### [Task technical implementation]

For any preserved row whose evidence is insufficient, update it to the correct status, such as:

- intentionally divergent,
- unsupported,
- or open/weak-proof remainder if still awaiting explicit resolution under the project’s governance rules.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase11_preserved_review.md`

#### [Task important notes]

This is where most teams flinch. Do not protect labels that the evidence cannot support.

#### [Task check list]

- [ ] Weak preserved rows are identified
- [ ] Status corrections are made
- [ ] Support matrix is updated
- [ ] Evidence mismatch is documented
- [ ] No inflated preserved labels remain

#### [Task acceptance criteria]

No preserved row remains preserved unless its evidence actually supports that claim.

---

### [ ] (checkbox) - [Task 4] - Publish the reconciled preserved-surface baseline

#### [Task Description]

Turn preserved-scope correction into an official project artifact.

#### [Task technical implementation]

Publish one preserved-surface baseline summarizing:

- preserved rows that remain preserved,
- rows downgraded during review,
- proof-type coverage by subsystem,
- and remaining weak-proof areas if any remain.

#### [Task possible affected files]

- `docs/engine/phase11_preserved_baseline.md`
- `docs/engine/support_matrix.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

This is the preserved-truth checkpoint. It should be uncomfortable if prior claims were too broad.

#### [Task check list]

- [ ] Remaining preserved rows are listed
- [ ] Downgraded rows are listed
- [ ] Proof coverage summary exists
- [ ] Weak-proof areas are explicit
- [ ] Artifact is reviewable

#### [Task acceptance criteria]

The project has one reconciled preserved-surface baseline.
