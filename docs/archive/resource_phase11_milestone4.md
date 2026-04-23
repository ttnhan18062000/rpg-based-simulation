# [Milestone 4] - Master-Ledger Reconciliation and Silent-Gap Elimination

## [Milestone Description]

Milestone 4 closes the governance gap between all project truth surfaces.

Its purpose is to eliminate disagreement between:

- the replacement ledger,
- the support matrix,
- divergence logs,
- unsupported/retired registers,
- proof bundles,
- and docs/release-truth surfaces.

This milestone is where the project stops having multiple partially correct truths.

## [Milestone technical implementation]

Run one full reconciliation pass across all authoritative governance artifacts.

This milestone must:

- cross-check every ledger row against linked evidence,
- verify support matrix entries match ledger status,
- verify divergence and unsupported registers match ledger status,
- verify proof bundles and docs do not imply unsupported claims,
- and eliminate orphaned, duplicated, or silently contradictory rows.

This milestone must not:

- tolerate “close enough” alignment,
- leave row references broken or stale,
- or allow any outward-facing support surface to outrun the ledger.

## [Milestone important notes]

The trap here is believing that mostly aligned truth surfaces are good enough.

They are not.

If there are multiple competing truths, cutover becomes a political act instead of an engineering act.

## [Milestone acceptance criteria]

At the end of Milestone 4:

- the ledger, support matrix, divergence log, unsupported/retired registers, and proof surfaces agree,
- contradictory rows are eliminated,
- orphaned scope is eliminated,
- and the project has one coherent governance truth.

---

## Task

### [ ] (checkbox) - [Task 1] - Cross-check every ledger row against all linked governance artifacts

#### [Task Description]

Use the ledger as the central control surface and verify every linked artifact agrees with it.

#### [Task technical implementation]

For each row in the master ledger, check:

- support matrix mapping,
- divergence or unsupported register mapping where relevant,
- proof bundle linkage,
- and public/docs/release-truth implications.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/support_matrix.md`
- `docs/engine/divergence_log.md`
- proof-bundle indexes

#### [Task important notes]

This is the boring part people skip. It is also the part that prevents disaster later.

#### [Task check list]

- [ ] Ledger-to-support mapping is checked
- [ ] Ledger-to-divergence mapping is checked
- [ ] Ledger-to-proof mapping is checked
- [ ] Broken links are recorded
- [ ] Contradictions are recorded

#### [Task acceptance criteria]

Every ledger row has been cross-checked against the project’s other governance artifacts.

---

### [ ] (checkbox) - [Task 2] - Eliminate orphaned, duplicated, and contradictory scope records

#### [Task Description]

Remove silent gaps and duplicated truths.

#### [Task technical implementation]

For any row or behavior that is:

- duplicated under multiple names,
- referenced in proof but absent from the ledger,
- present in the ledger but absent from support truth,
- or described inconsistently across artifacts,

correct the governance surfaces so one authoritative record remains.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/support_matrix.md`
- `docs/engine/divergence_log.md`
- `docs/engine/unsupported_scope_register.md`

#### [Task important notes]

Multiple half-correct records are worse than one missing record.

#### [Task check list]

- [ ] Duplicate rows are merged or clarified
- [ ] Orphaned proof references are resolved
- [ ] Contradictory status records are corrected
- [ ] One authoritative record remains
- [ ] Correction notes are preserved where needed

#### [Task acceptance criteria]

No material behavior remains orphaned, duplicated, or silently contradictory across governance artifacts.

---

### [ ] (checkbox) - [Task 3] - Reconcile release-truth and outward-facing documentation with the master ledger

#### [Task Description]

Ensure public-facing support claims no longer outrun internal ratified truth.

#### [Task technical implementation]

Review release/readiness docs, support overviews, and summary materials and narrow or correct any wording that exceeds the master ledger and ratified proof surfaces.

#### [Task possible affected files]

- `README.md`
- `docs/engine/replacement_status_overview.md`
- `docs/engine/release_readiness.md`
- `docs/engine/support_matrix.md`

#### [Task important notes]

If docs sound better than the proof, the project is lying.

#### [Task check list]

- [ ] Overclaims are removed
- [ ] Wording matches ledger truth
- [ ] Wording matches proof truth
- [ ] Unsupported scope remains visible
- [ ] Summary docs agree with detailed docs

#### [Task acceptance criteria]

Outward-facing documentation is reconciled with the master ledger and proof surfaces.

---

### [ ] (checkbox) - [Task 4] - Publish the master-governance reconciliation package

#### [Task Description]

Make the reconciled governance system reviewable as one artifact set.

#### [Task technical implementation]

Publish one reconciliation package summarizing:

- corrections made,
- remaining known limits,
- final artifact alignment,
- and the statement that the ledger now governs all replacement truth.

#### [Task possible affected files]

- `docs/engine/phase11_governance_reconciliation.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

If reconciliation exists only in commit history, it will be forgotten.

#### [Task check list]

- [ ] Corrections are summarized
- [ ] Remaining limits are summarized
- [ ] Artifact alignment is explicit
- [ ] Governance authority is explicit
- [ ] Package is reviewable

#### [Task acceptance criteria]

The project has one master-governance reconciliation package.
