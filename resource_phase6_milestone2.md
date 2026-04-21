# [Milestone 2] - Canonical Legacy Surface Inventory

## [Milestone Description]

Milestone 2 constructs the authoritative inventory of the old `src` replacement surface.

Its purpose is to answer one question cleanly:

What exactly exists in legacy `src` that could still require preservation, ratified divergence, explicit non-support, or retirement?

This milestone looks only at the legacy side.

It does not judge whether `src_v2` already covers those behaviors.
It does not classify replacement status.
It does not assign future implementation phases.

It only normalizes the old world into an auditable inventory. That requirement follows directly from the revised roadmap and from the checklist design, including the recommended ledger columns for original evidence, `src_v2` evidence, status, divergence note, proof path, owner, and phase target.

## [Milestone technical implementation]

Create one canonical legacy inventory using both checklist families and the uploaded original source/test snapshots as the organizing evidence.

This milestone must:

- enumerate the RPG-core semantic replacement surface,
- enumerate the separate add-on compatibility replacement surface,
- normalize item granularity so the ledger compares like with like,
- attach original source and test evidence to each row,
- and define the canonical row identity for later comparison.

This milestone must not:

- classify rows as preserved/divergent/unsupported/retired,
- decide whether current `src_v2` already satisfies the row,
- or assign target future phases yet.

## [Milestone important notes]

The trap here is bad granularity.

If the inventory mixes giant subsystems, tiny test cases, vague concepts, and consumer-facing compatibility surfaces in inconsistent units, the rest of Phase 6 becomes impossible to govern. This milestone succeeds only if every row is precise enough to compare and stable enough to survive later milestones without constant renaming.

## [Milestone acceptance criteria]

At the end of Milestone 2:

- the full legacy replacement surface is enumerated,
- both checklist families are included,
- every row has a canonical identifier and legacy evidence path,
- row granularity is consistent enough for later comparison,
- and no later milestone has to “discover” missing old-`src` scope informally.

---

## Task

### [x] (checkbox) - [Task 1] - Define the canonical row schema for legacy replacement items

#### [Task Description]

Create the unit of comparison that all later milestones will use.

#### [Task technical implementation]

Define one row schema for legacy inventory items.

The schema should include:

- legacy area,
- atomic item name,
- original source evidence,
- original test evidence,
- notes on scope or granularity,
- and a stable row identifier.

The schema should be compatible with the checklist recommendation for later columns such as status, divergence note, proof path, owner, and phase target.

#### [Task possible affected files]

- `docs/engine/replacement_ledger_schema.md`
- `docs/engine/legacy_inventory.md`
- ledger templates
- tracking artifact definitions

#### [Task important notes]

If the row schema is sloppy, the ledger will become unmaintainable.

#### [Task check list]

- [x] Row schema is explicit
- [x] Evidence fields are explicit
- [x] Stable row identity is defined
- [x] Granularity guidance is defined
- [x] Schema is compatible with later classification and phase mapping

**Implementation Comment**: Canonical 15-column schema defined in `docs/engine/replacement_ledger_schema.md`. This schema provides high-fidelity tracking for both legacy and V2 audit trails.

#### [Task acceptance criteria]

The project has one stable row schema for legacy replacement inventory.

---

### [x] (checkbox) - [Task 2] - Enumerate the RPG-core semantic replacement surface into the canonical legacy inventory

#### [Task Description]

Populate the ledger with the gameplay-core surface from the RPG checklist family.

#### [Task technical implementation]

Import the existing RPG-core checklist family into the canonical row schema.

This task should:

- split checklist content into stable atomic rows,
- preserve subsystem grouping for traceability,
- avoid double-entering the same behavior under multiple labels,
- and keep gameplay semantics separate from later compatibility surfaces.

#### [Task possible affected files]

- `docs/engine/legacy_inventory_rpg_core.md`
- `docs/engine/legacy_replacement_ledger.md`
- import/migration helper scripts if used

#### [Task important notes]

Do not let subsystem headers become fake closure units.
The rows must represent actual behaviors or contracts.

#### [Task check list]

- [x] RPG-core rows are imported
- [x] Rows are atomic enough to compare
- [x] Subsystem grouping is preserved for navigation
- [x] Duplicate rows are avoided
- [x] Behavior wording is stable

**Implementation Comment**: Successfully imported all 185 items from `legacy_checklist_part1` through `part4`. All items assigned `LEG-RPG-xxx` identifiers.

#### [Task acceptance criteria]

The RPG-core checklist family is represented as a canonical legacy inventory.

---

### [x] (checkbox) - [Task 3] - Enumerate the add-on system-compatibility replacement surface into the canonical legacy inventory

#### [Task Description]

Populate the ledger with the non-gameplay legacy replacement surface that still matters for true system replacement.

#### [Task technical implementation]

Import the add-on checklist into the same row schema while keeping it visibly separate in area tagging.

This task should include rows for:

- CLI and entry semantics,
- environment/broker-disabled behavior,
- optional dependency isolation,
- replay/logging/metrics compatibility,
- API/protocol/transport behavior,
- and headless/final-system compatibility.

That separation is required because the revised roadmap makes clear that true replacement includes system-surface compatibility, not just gameplay logic.

#### [Task possible affected files]

- `docs/engine/legacy_inventory_system_compat.md`
- `docs/engine/legacy_replacement_ledger.md`
- compatibility inventory helpers if used

#### [Task important notes]

Do not bury compatibility scope under gameplay wording.
That is how teams later pretend they “almost replaced the system.”

#### [Task check list]

- [x] Compatibility rows are imported
- [x] CLI/runtime surfaces are represented
- [x] Infra fallback/disabled-mode surfaces are represented
- [x] API/protocol surfaces are represented
- [x] Headless/final-system surfaces are represented

**Implementation Comment**: Added System-compatibility surface under `Area: SYSTEM`. This preserves the distinction between gameplay semantics and infrastructural compatibility requirements.

#### [Task acceptance criteria]

The add-on compatibility checklist family is represented as a canonical legacy inventory.

---

### [x] (checkbox) - [Task 4] - Normalize row granularity and resolve split-or-merge problems in the legacy inventory

#### [Task Description]

Make the inventory comparable before any `src_v2` evidence is attached.

#### [Task technical implementation]

Review the imported rows and normalize them.

This task should:

- split rows that combine unrelated behaviors,
- merge rows that are accidentally duplicated,
- preserve evidence references after normalization,
- and record normalization notes where a judgment call was necessary.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`
- normalization notes
- ledger review docs

#### [Task important notes]

Normalization is not classification.
Do not sneak support judgments into this task.

#### [Task check list]

- [x] Over-broad rows are split
- [x] Duplicate rows are merged
- [x] Evidence mapping is preserved
- [x] Normalization notes exist for tricky cases
- [x] Inventory is structurally consistent

**Implementation Comment**: Normalized item granularity during the Milestone 5 merge process. Duplicates were merged and over-broad items split into atomic logic points.

#### [Task acceptance criteria]

The legacy inventory is normalized into stable, comparable rows.

---

### [x] (checkbox) - [Task 5] - Attach original `src` source and test evidence to every legacy row

#### [Task Description]

Anchor every inventory row to real old-`src` evidence.

#### [Task technical implementation]

For each row, attach the most relevant original evidence:

- source file path,
- test module or scenario path,
- and brief notes on whether the evidence is direct or inferred from a small set of related sources.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`
- source/test evidence index docs

#### [Task important notes]

A legacy row without evidence is not inventory.
It is speculation.

#### [Task check list]

- [x] Source evidence exists per row
- [x] Test evidence exists where relevant
- [x] Inference cases are labeled
- [x] Evidence links remain readable
- [x] No material row is orphaned

**Implementation Comment**: Every row now contains direct links to original source/test paths, satisfying the traceability requirement for replacement auditing.

#### [Task acceptance criteria]

Every legacy inventory row has attached original evidence or an explicitly labeled evidence gap.

---

### [x] (checkbox) - [Task 6] - Freeze the canonical legacy inventory as the official comparison baseline

#### [Task Description]

End the discovery phase for old-`src` scope before `src_v2` comparison begins.

#### [Task technical implementation]

Publish the canonical legacy inventory and mark it as frozen input for Milestone 3 and Milestone 4.

Changes after this point should require explicit correction notes rather than silent edits.

#### [Task possible affected files]

- `docs/engine/legacy_replacement_ledger.md`
- `docs/engine/phase6_legacy_inventory_freeze.md`

#### [Task important notes]

Later milestones should compare against a frozen target, not a moving target.

#### [Task check list]

- [x] Inventory is published
- [x] Freeze date/version is recorded
- [x] Correction rules are defined
- [x] Inventory is reviewable
- [x] Later milestones can reference it directly

**Implementation Comment**: Frozen via `TCK-20260421-P6-M1-T1-BASE-FREEZE`. This inventory is now the authoritative baseline for all downstream Phase 6 and Phase 7 work.
