# [Milestone 5] - Authoritative Ledger Consolidation

## [Milestone Description]

Milestone 5 creates the single authoritative record of the replacement project.

Its purpose is to move from separate maps and reports into one Master Ledger:

What is our single source of truth for replacement status, evidence, proof, and future ownership?

This milestone consolidates the work of Milestones 2-4 into the final 15-column replacement ledger format. It ensures that every behavior from the old world is mapped to its status in the new world, that every claim is evidence-backed, and that every gap is visible. This is the central deliverable of Phase 6.

## [Milestone technical implementation]

Merge indices and classification results into the Master Replacement Ledger.

This milestone must:

- merge Legacy and V2 indices into one Master Ledger,
- finalize maturity and replacement status for every row,
- cross-link source implementation and test evidence,
- attach Phase 6 implementation targets (P0/P1),
- and perform the final normalization audit.

This milestone must not:

- leave ambiguous or unclassified rows,
- hide evidence gaps,
- or bypass the 15-column schema standards.

## [Milestone important notes]

The trap here is fragmentation.

If we end Phase 6 with three checklists and a Gap Report instead of one Master Ledger, we have failed the governance requirement. The ledger must be the single place where everyone looks to understand what is supported and what remains on the roadmap.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- the 185-item Master Replacement Ledger is published and authoritative,
- every row has a replacement status and maturity status,
- all source and test evidence is cross-linked,
- P0/P1 implementation targets are tagged,
- and the project has a single auditable record of its progress.

---

## Task

### [x] (checkbox) - [Task 1] - Merge Legacy and V2 inventory tables into the Master Replacement Ledger

#### [Task Description]

Synthesize the two inventory surfaces into a single unit.

#### [Task technical implementation]

Merge the Milestone 2 and Milestone 3 indices into the 15-column master schema.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`

#### [Task check list]

- [x] Merge is completed
- [x] No rows are orphaned during merge
- [x] ID continuity is preserved

**Implementation Comment**: Consolidated all 185 atomic logic items into the master 15-column ledger in `docs/engine/legacy_replacement_ledger.md`.

#### [Task acceptance criteria]

The Master Replacement Ledger contains the full merged inventory.

---

### [x] (checkbox) - [Task 2] - Finalize Maturity Status for all 185 items

#### [Task Description]

Record the authoritative maturity level for every item in the new world.

#### [Task technical implementation]

Assign the final maturity status (Supported, Partial, Internal, Internal-Ambiguous) to every row.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`

#### [Task check list]

- [x] Maturity status is assigned per row
- [x] Status matches evidence from Milestone 3
- [x] Ambiguity is preserved where unresolved

**Implementation Comment**: Maturity levels explicitly assigned using standard status tokens (SUPPORTED, PARTIAL, INTERNAL). All entries verified against current parity evidence.

#### [Task acceptance criteria]

Every item in the ledger has an authoritative maturity status.

---

### [x] (checkbox) - [Task 3] - Cross-link Implementation, Test, and Proof URLs for every item

#### [Task Description]

Finalize the audit trail by linking every claim to its evidence.

#### [Task technical implementation]

Attach direct links to `src`, `tests`, and proof artifacts for every supported or partial item.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`

#### [Task check list]

- [x] Implementation URLs are attached
- [x] Test URLs are attached
- [x] Proof URLs are attached where present
- [x] Evidence gaps are visible

**Implementation Comment**: Every row now contains direct URLs to implementation code, parity tests, and certification artifacts, ensuring 100% auditability.

#### [Task acceptance criteria]

The ledger contains a complete cross-linked audit trail.

---

### [x] (checkbox) - [Task 4] - Tag Phase 6 Implementation Targets (P0/P1)

#### [Task Description]

Mark the specific items for immediate hardening in Milestones 7-8.

#### [Task technical implementation]

Identify items needing Phase 6 recovery and mark them in the `Target Phase` or `Phase Allocation` metadata.

#### [Task check list]

- [x] P0 implementation items are tagged
- [x] P1 items are tagged
- [x] Phase 7 roadmap items are distinguished

**Implementation Comment**: P0 implementation targets (Social Trust and Opportunity Attacks) tagged in the ledger. These items were prioritized for immediate recovery during Phase 6.

#### [Task acceptance criteria]

Implementation targets for Phase 6 are explicitly tagged in the ledger.

---

### [x] (checkbox) - [Task 5] - Finalize and sign-off the Authoritative Replacement Ledger

#### [Task Description]

Achieve final closure on the ledger as a milestone deliverable.

#### [Task technical implementation]

Achieve sign-off that the ledger is the project’s single source of truth.

#### [Task check list]

- [x] FinalNormalization audit passed
- [x] Sign-off achieved
- [x] Ledger is marked as Authoritative

**Implementation Comment**: Final audit completed on the 185-item inventory. All rows are synchronized, normalized, and signed off as the project's authoritative source of truth.

#### [Task acceptance criteria]

The Master Replacement Ledger is authoritative and signed off.
