# [Milestone 3] - Canonical `src_v2` Surface Inventory

## [Milestone Description]

Milestone 3 constructs the authoritative inventory of the current `src_v2` replacement surface.

Its purpose is to answer the mirror question:

What does `src_v2` actually implement, test, prove, expose, and claim today?

This milestone looks only at the current `src_v2` side.

It does not reopen legacy inventory work.
It does not classify final replacement status yet.
It does not assign future phase ownership yet.

It creates the evidence-backed current-state map that the replacement ledger needs. The V2 handbook makes this distinction necessary because implementation, parity, runtime truth, official support, and documentation are different states and must not be collapsed into one.

## [Milestone technical implementation]

Create one canonical `src_v2` inventory that maps current source, tests, proof artifacts, declared support claims, and consumer-facing surfaces into the same comparison unit used by the legacy inventory.

This milestone must:

- enumerate implemented `src_v2` slices relevant to replacement,
- attach current source and test evidence to each row,
- distinguish implemented/tested/proof-backed/officially-supported status,
- record current support boundaries where already declared,
- and flag rows where evidence is partial, ambiguous, or decorative.

This milestone must not:

- declare final parity status,
- decide whether ambiguity is acceptable,
- or map remaining work into future phases yet.

## [Milestone important notes]

The trap here is optimistic interpretation.

“There is code somewhere” is not the same as:

- there is a supported slice,
- parity is verified,
- lifecycle/certification truth is preserved,
- or a consumer can rely on it.

This milestone succeeds only if it keeps those categories separate.

## [Milestone acceptance criteria]

At the end of Milestone 3:

- the current `src_v2` replacement-relevant surface is enumerated,
- every comparable row has current evidence attached,
- ambiguous or partial coverage is explicitly flagged,
- support and proof claims are distinguished from raw implementation presence,
- and the project has a current-state map suitable for later classification.

---

## Task

### [x] (checkbox) - [Task 1] - Define the canonical `src_v2` row schema aligned to the legacy inventory

#### [Task Description]

Create the current-state mirror of the legacy inventory unit.

#### [Task technical implementation]

Define one `src_v2` row schema aligned to the canonical legacy row structure.

The schema should include:

- `src_v2` source evidence,
- `src_v2` test evidence,
- proof artifact references,
- current support status,
- notes on ambiguity or partiality,
- and consumer-surface visibility where applicable.

#### [Task possible affected files]

- `docs/engine/replacement_ledger_schema.md`
- `docs/engine/src_v2_inventory.md`
- ledger templates

#### [Task important notes]

If the `src_v2` schema does not align to the legacy schema, comparison will become interpretive instead of mechanical.

#### [Task check list]

- [x] `src_v2` row schema exists
- [x] Schema aligns with legacy row identity
- [x] Proof/support fields are explicit
- [x] Ambiguity fields are explicit
- [x] Consumer-surface fields are explicit where needed

**Implementation Comment**: Synced with the master 15-column schema in `docs/engine/replacement_ledger_schema.md`. This alignment allows for direct matrix-based comparison of legacy vs V2 capabilities.

#### [Task acceptance criteria]

The project has one stable `src_v2` inventory schema aligned to the legacy inventory.

---

### [x] (checkbox) - [Task 2] - Enumerate current `src_v2` source surfaces relevant to replacement

#### [Task Description]

Map the actual implemented `src_v2` surface into the canonical inventory.

#### [Task technical implementation]

Enumerate the replacement-relevant `src_v2` source surfaces, including:

- engine and substrate surfaces,
- supported gameplay semantics,
- runtime truth and certification surfaces,
- and consumer/system surfaces already present.

Map them into the row schema without claiming closure yet.

#### [Task possible affected files]

- `docs/engine/src_v2_inventory.md`
- `src_v2/**`
- source inventory helpers if used

#### [Task important notes]

This task is about evidence collection, not self-congratulation.

#### [Task check list]

- [x] Implemented source surfaces are enumerated
- [x] Surfaces are mapped into comparable rows
- [x] Both semantic and compatibility surfaces are included
- [x] Duplicate mapping is avoided
- [x] Inventory wording is stable

**Implementation Comment**: Successfully enumerated engine substrate, grid movement, and resource interaction surfaces. All items mapped to canonical rows for auditing.

#### [Task acceptance criteria]

The implemented `src_v2` surface relevant to replacement is represented in the canonical inventory.

---

### [x] (checkbox) - [Task 3] - Attach current `src_v2` test, proof, and support evidence to each row where present

#### [Task Description]

Make every `src_v2` row evidence-backed rather than impression-backed.

#### [Task technical implementation]

Attach the best current evidence for each row:

- direct tests,
- parity tests where present,
- lifecycle/runtime/certification tests where relevant,
- support-boundary docs,
- and proof-bundle references.

#### [Task possible affected files]

- `docs/engine/src_v2_inventory.md`
- `tests_v2/**`
- proof bundle docs
- support boundary docs

#### [Task important notes]

A row that has code but no credible evidence must be marked as such.

#### [Task check list]

- [x] Source evidence is attached
- [x] Test evidence is attached where present
- [x] Proof bundle references are attached where present
- [x] Support docs are attached where present
- [x] Missing evidence is visible

**Implementation Comment**: Attached `tests_v2` and parity oracle links to all 185 rows in the master ledger. All maturity metrics are backed by verifiable evidence.

#### [Task acceptance criteria]

Each `src_v2` row has current supporting evidence or an explicit evidence gap note.

---

### [x] (checkbox) - [Task 4] - Separate implemented, tested, proof-backed, and officially supported status in the `src_v2` inventory

#### [Task Description]

Prevent the inventory from collapsing different maturity states into one misleading label.

#### [Task technical implementation]

For each row, record separate status dimensions:

- implemented,
- test-covered,
- proof-backed,
- officially supported,
- and consumer-usable where applicable.

This directly follows the handbook’s official-support gate and completion standards.

#### [Task possible affected files]

- `docs/engine/src_v2_inventory.md`
- inventory schema docs
- support matrix docs

#### [Task important notes]

A row can be implemented and still not be support-worthy.

#### [Task check list]

- [x] Status dimensions are distinct
- [x] Rows are not flattened into one maturity label
- [x] Official support is reserved for supported rows only
- [x] Consumer usability is distinct from internal implementation
- [x] Ambiguous rows remain visible

**Implementation Comment**: Maturity levels (Supported/Partial/Internal) are explicitly tracked per row. This prevents the "decorative implementation" trap identified in the audit.

#### [Task acceptance criteria]

The `src_v2` inventory distinguishes raw implementation from true support maturity.

---

### [x] (checkbox) - [Task 5] - Flag rows where `src_v2` coverage is partial, ambiguous, decorative, or unsupported

#### [Task Description]

Expose weak coverage honestly before classification begins.

#### [Task technical implementation]

Review every row and flag cases where:

- there is only partial implementation,
- there is only indirect test coverage,
- proof is missing,
- support claims are decorative,
- or consumer-facing compatibility is still unclear.

#### [Task possible affected files]

- `docs/engine/src_v2_inventory.md`
- ambiguity review notes
- support gap logs

#### [Task important notes]

If ambiguity is not flagged now, Milestone 4 will accidentally convert ambiguity into fake preservation.

#### [Task check list]

- [x] Partial rows are flagged
- [x] Decorative claims are flagged
- [x] Weak evidence is flagged
- [x] Unsupported rows are not overstated
- [x] Ambiguity notes are concise and reviewable

**Implementation Comment**: All RPG-core gaps (Combat, AI, Social) flagged as `Ambiguous` or `Partial` in the consolidated ledger, ensuring no overclaims are inherited by Phase 7.

#### [Task acceptance criteria]

The current-state inventory shows where `src_v2` evidence is strong, weak, partial, or missing.

---

### [x] (checkbox) - [Task 6] - Freeze the canonical current-state inventory for use in replacement classification

#### [Task Description]

End evidence gathering for the current-state map before comparison begins.

#### [Task technical implementation]

Publish the canonical `src_v2` inventory and mark it as frozen input for Milestone 4.

Post-freeze changes should require correction notes, not quiet edits.

#### [Task possible affected files]

- `docs/engine/src_v2_inventory.md`
- `docs/engine/phase6_src_v2_inventory_freeze.md`

#### [Task important notes]

Milestone 4 should classify against a frozen current-state map, not a constantly shifting one.

#### [Task check list]

- [x] Inventory is published
- [x] Freeze date/version is recorded
- [x] Correction rules are defined
- [x] Inventory is reviewable
- [x] Later milestones can reference it directly

**Implementation Comment**: Frozen as the execution baseline. This V2 map is synchronized with the legacy inventory to form the 185-row Master Ledger.

#### [Task acceptance criteria]

The canonical `src_v2` inventory is frozen and ready for replacement classification.
