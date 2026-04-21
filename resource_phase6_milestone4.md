# [Milestone 4] - Replacement Classification and Support Ratification

## [Milestone Description]

Milestone 4 is where the replacement ledger stops being descriptive and starts being authoritative.

Its purpose is to compare the canonical legacy inventory against the canonical `src_v2` inventory and classify every row.

This milestone decides status.
It does not yet design future proof programs in detail.
It does not yet build the execution backlog for later phases.

Its job is to replace vague progress language with hard, auditable truth. The revised roadmap requires every remaining old-`src` item to be classified as preserved, intentionally divergent, unsupported, or retired, and the handbook requires divergences to be explicit rather than left as accidental mismatches.

## [Milestone technical implementation]

Create one authoritative classification pass across all ledger rows.

Every row must be classified as one of:

- preserved,
- intentionally divergent,
- unsupported,
- retired.

This milestone must:

- compare original evidence and `src_v2` evidence row by row,
- determine whether preservation is already achieved,
- determine whether mismatch is intentional and acceptable,
- determine whether a legacy item is explicitly unsupported,
- determine whether an item is truly retired and no longer part of product truth,
- and ratify the current official support boundary implied by those decisions.

This milestone must not:

- invent soft status labels like “mostly there,”
- hide undecided items under vague temporary notes,
- or turn missing evidence into assumed preservation.

## [Milestone important notes]

The trap here is cowardice.

If the team refuses to make hard calls, the ledger becomes a mood board instead of a governance artifact. The handbook already rejects “it probably matches,” “we will document divergence later,” and similar unfinished states. This milestone succeeds only if every material row gets one formal status and every non-preserved status is explicitly justified.

## [Milestone acceptance criteria]

At the end of Milestone 4:

- every inventory row has one formal replacement status,
- intentional divergences are distinguished from accidental mismatches,
- unsupported and retired behavior are explicitly named,
- the current official support boundary is ratified from those decisions,
- and no material legacy row remains unclassified.

---

## Task

### [ ] (checkbox) - [Task 1] - Compare canonical legacy rows and canonical `src_v2` rows one by one using the frozen inventories

#### [Task Description]

Perform the actual row-level comparison that turns two inventories into a replacement ledger.

#### [Task technical implementation]

For each canonical row:

- review original evidence,
- review `src_v2` evidence,
- compare behavior/contract scope,
- compare support maturity,
- and record the basis for classification.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- comparison notes
- review records

#### [Task important notes]

This task is not allowed to guess.
Every comparison must point to evidence.

#### [Task check list]

- [ ] Original evidence reviewed
- [ ] `src_v2` evidence reviewed
- [ ] Scope comparison is explicit
- [ ] Evidence basis is recorded
- [ ] No material row is skipped

#### [Task acceptance criteria]

Every canonical row has an evidence-backed comparison record.

---

### [ ] (checkbox) - [Task 2] - Classify each row as preserved, intentionally divergent, unsupported, or retired

#### [Task Description]

Make the formal replacement-status decision for every row.

#### [Task technical implementation]

Using the completed comparison records, assign one formal status per row.

Do not create hybrid statuses.
Do not create comfort labels.
If the row is not preserved and not explicitly retired, then it must become either intentionally divergent or unsupported.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- classification review docs

#### [Task important notes]

A ledger without hard statuses is theater.

#### [Task check list]

- [ ] Every row has exactly one status
- [ ] No hybrid statuses exist
- [ ] No “close enough” labels exist
- [ ] Status aligns to evidence
- [ ] Material rows are not left undecided

#### [Task acceptance criteria]

Every row in the replacement ledger has one formal status.

---

### [ ] (checkbox) - [Task 3] - Record divergence rationale for every intentionally divergent row

#### [Task Description]

Turn every accepted mismatch into an explicit design decision rather than an accidental drift.

#### [Task technical implementation]

For each intentionally divergent row, record:

- old behavior,
- new behavior,
- reason for divergence,
- divergence category,
- supporting tests or proof,
- and docs updated status.

This follows the handbook’s divergence-log requirement directly.

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/replacement_ledger.md`
- divergence review notes

#### [Task important notes]

If you cannot explain the divergence, you have not earned the divergence.

#### [Task check list]

- [ ] Old behavior is described
- [ ] New behavior is described
- [ ] Reason for divergence is explicit
- [ ] Supporting proof is linked
- [ ] Docs update status is recorded

#### [Task acceptance criteria]

Every intentionally divergent row has a complete divergence rationale.

---

### [ ] (checkbox) - [Task 4] - Record non-support rationale for every unsupported row

#### [Task Description]

Make non-support an explicit policy decision instead of silent omission.

#### [Task technical implementation]

For each unsupported row, record:

- what legacy behavior is not supported,
- why it is not supported,
- whether non-support is temporary or expected long-term,
- and what consumers or later phases must not assume about it.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/unsupported_scope_register.md`
- support matrix docs

#### [Task important notes]

Silently unsupported behavior is one of the fastest ways to create fake cutover confidence.

#### [Task check list]

- [ ] Unsupported behavior is named
- [ ] Rationale is explicit
- [ ] Temporary vs long-term status is explicit
- [ ] Consumer assumptions are constrained
- [ ] Unsupported rows remain visible

#### [Task acceptance criteria]

Every unsupported row has an explicit non-support rationale and scope note.

---

### [ ] (checkbox) - [Task 5] - Record retirement rationale for every retired row

#### [Task Description]

Stop dead scope from re-entering the project through vague memory.

#### [Task technical implementation]

For each retired row, record:

- why the legacy behavior is considered retired,
- what replaced it conceptually if anything,
- whether retirement is product-level or architecture-level,
- and why later phases should not treat it as open replacement scope.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/retired_scope_register.md`

#### [Task important notes]

Retired is not shorthand for “we do not want to think about this.”
It requires rationale.

#### [Task check list]

- [ ] Retirement reason is explicit
- [ ] Replacement context is explicit where relevant
- [ ] Product vs architecture retirement is clear
- [ ] Later-phase confusion is prevented
- [ ] Retired rows are searchable

#### [Task acceptance criteria]

Every retired row has a reviewable retirement rationale.

---

### [ ] (checkbox) - [Task 6] - Ratify the current official support boundary implied by completed classifications

#### [Task Description]

Derive the project’s real support boundary from the replacement ledger rather than from narrative summaries.

#### [Task technical implementation]

Aggregate the completed statuses and publish the current support boundary:

- preserved supported scope,
- intentionally divergent but supported scope,
- unsupported legacy scope,
- retired legacy scope,
- and open replacement scope.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/replacement_ledger.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Support should be derived from the ledger, not the other way around.

#### [Task check list]

- [ ] Preserved support is explicit
- [ ] Divergent-but-supported scope is explicit
- [ ] Unsupported scope is explicit
- [ ] Retired scope is explicit
- [ ] Open replacement remainder is explicit

#### [Task acceptance criteria]

The project has one official support boundary derived from ledger classifications.

---

### [ ] (checkbox) - [Task 7] - Publish the first complete authoritative replacement ledger

#### [Task Description]

Make the classification result real and reviewable.

#### [Task technical implementation]

Publish the first complete replacement ledger with:

- all rows,
- evidence,
- statuses,
- divergence notes,
- and support-boundary implications.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- milestone review docs

#### [Task important notes]

This is the first point where the project earns the phrase “authoritative replacement ledger.”

#### [Task check list]

- [ ] Ledger is complete
- [ ] Ledger is reviewable
- [ ] Evidence is attached
- [ ] Statuses are explicit
- [ ] Support implications are visible

#### [Task acceptance criteria]

The project has one published authoritative replacement ledger.
