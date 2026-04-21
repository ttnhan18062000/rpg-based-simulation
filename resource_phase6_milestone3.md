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

### [ ] (checkbox) - [Task 1] - Define the canonical `src_v2` row schema aligned to the legacy inventory

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

- [ ] `src_v2` row schema exists
- [ ] Schema aligns with legacy row identity
- [ ] Proof/support fields are explicit
- [ ] Ambiguity fields are explicit
- [ ] Consumer-surface fields are explicit where needed

#### [Task acceptance criteria]

The project has one stable `src_v2` inventory schema aligned to the legacy inventory.

---

### [ ] (checkbox) - [Task 2] - Enumerate current `src_v2` source surfaces relevant to replacement

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

- [ ] Implemented source surfaces are enumerated
- [ ] Surfaces are mapped into comparable rows
- [ ] Both semantic and compatibility surfaces are included
- [ ] Duplicate mapping is avoided
- [ ] Inventory wording is stable

#### [Task acceptance criteria]

The implemented `src_v2` surface relevant to replacement is represented in the canonical inventory.

---

### [ ] (checkbox) - [Task 3] - Attach current `src_v2` test, proof, and support evidence to each row where present

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

- [ ] Source evidence is attached
- [ ] Test evidence is attached where present
- [ ] Proof bundle references are attached where present
- [ ] Support docs are attached where present
- [ ] Missing evidence is visible

#### [Task acceptance criteria]

Each `src_v2` row has current supporting evidence or an explicit evidence gap note.

---

### [ ] (checkbox) - [Task 4] - Separate implemented, tested, proof-backed, and officially supported status in the `src_v2` inventory

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

- [ ] Status dimensions are distinct
- [ ] Rows are not flattened into one maturity label
- [ ] Official support is reserved for supported rows only
- [ ] Consumer usability is distinct from internal implementation
- [ ] Ambiguous rows remain visible

#### [Task acceptance criteria]

The `src_v2` inventory distinguishes raw implementation from true support maturity.

---

### [ ] (checkbox) - [Task 5] - Flag rows where `src_v2` coverage is partial, ambiguous, decorative, or unsupported

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

- [ ] Partial rows are flagged
- [ ] Decorative claims are flagged
- [ ] Weak evidence is flagged
- [ ] Unsupported rows are not overstated
- [ ] Ambiguity notes are concise and reviewable

#### [Task acceptance criteria]

The current-state inventory shows where `src_v2` evidence is strong, weak, partial, or missing.

---

### [ ] (checkbox) - [Task 6] - Freeze the canonical current-state inventory for use in replacement classification

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

- [ ] Inventory is published
- [ ] Freeze date/version is recorded
- [ ] Correction rules are defined
- [ ] Inventory is reviewable
- [ ] Later milestones can reference it directly

#### [Task acceptance criteria]

The canonical `src_v2` inventory is frozen and ready for replacement classification.
