# [Milestone 5] - Proof Path Mapping and Future Phase Allocation

## [Milestone Description]

Milestone 5 converts the classified ledger into the execution architecture for the remaining rewrite.

Its purpose is to answer two questions for every row that is not already closed:

- What proof path is required?
- Which future phase owns closure?

This milestone consumes the classifications from Milestone 4.
It does not re-decide those classifications.
It does not build sprint-level engineering tickets yet.

It turns replacement truth into future-phase structure. The revised roadmap already separates the remaining work into substrate, gameplay-semantic, and system-compatibility fronts, and the handbook requires explicit proof and closure conditions rather than vague “we will validate later” language.

## [Milestone technical implementation]

Create one allocation model that maps every open ledger row to:

- a proof path,
- a target phase,
- a dependency chain,
- and a closure condition.

This milestone must:

- define the allowed proof-path taxonomy,
- assign proof path type to every non-closed row,
- assign each non-closed row to Phases 7 through 10,
- identify rows that depend on earlier substrate closure,
- and define what counts as closure so later phases do not improvise finish lines.

This milestone must not:

- reopen classification,
- create generic “future work” buckets,
- or hide unresolved ambiguity inside proof-path placeholders.

## [Milestone important notes]

The trap here is phase pollution.

If combat rows leak into substrate ownership, if compatibility rows are buried under gameplay work, or if proof paths are left as vague “testing later,” then later phases will duplicate work and miss their real blockers. This milestone succeeds only if future work becomes cleaner and stricter than before.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- every non-closed row has an assigned proof path,
- every non-closed row has an assigned target phase,
- cross-phase dependencies are explicit,
- closure conditions are explicit,
- and Phases 7 through 10 can be planned without re-litigating Phase 6 decisions.

---

## Task

### [ ] (checkbox) - [Task 1] - Define the allowed proof-path taxonomy for open replacement rows

#### [Task Description]

Create the controlled vocabulary for how open rows can be proven or closed later.

#### [Task technical implementation]

Define the allowed proof-path categories, such as:

- characterization,
- differential parity,
- V2 contract,
- regression,
- lifecycle/replay,
- certification/conformance,
- compatibility black-box validation,
- cutover validation.

Each category should have a short definition and a rule for when it is sufficient or insufficient.

#### [Task possible affected files]

- `docs/engine/proof_path_taxonomy.md`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

If proof paths are not standardized, later phases will invent flattering labels for weak evidence.

#### [Task check list]

- [ ] Proof categories are explicit
- [ ] Category definitions are explicit
- [ ] Sufficiency rules are explicit
- [ ] Redundant categories are avoided
- [ ] Taxonomy is usable by later phases

#### [Task acceptance criteria]

The project has one explicit proof-path taxonomy for open replacement rows.

---

### [ ] (checkbox) - [Task 2] - Assign a proof path to every non-closed ledger row

#### [Task Description]

Turn proof expectations into row-level obligations.

#### [Task technical implementation]

For each non-closed row, assign at least one proof path and note whether multiple proof layers are required.

Examples:

- preserved-but-not-yet-proven rows may need characterization plus differential plus contract proof,
- compatibility rows may need black-box validation plus regression,
- substrate rows may need contract plus determinism plus lifecycle validation.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- proof assignment notes

#### [Task important notes]

Do not let “proof path” become a cosmetic field.

#### [Task check list]

- [ ] Every non-closed row has a proof path
- [ ] Multi-proof rows are labeled where needed
- [ ] Weak placeholder proof labels are avoided
- [ ] Assignment matches row type
- [ ] Proof expectations are reviewable

#### [Task acceptance criteria]

Every non-closed row has a concrete proof-path assignment.

---

### [ ] (checkbox) - [Task 3] - Assign every non-closed row to a target closure phase across Phases 7 through 10

#### [Task Description]

Turn open replacement scope into phase-owned work.

#### [Task technical implementation]

Assign each non-closed row to one future target phase based on the corrected roadmap:

- Phase 7 for deterministic substrate closure,
- Phase 8 for combat/tactical/world-interaction semantics,
- Phase 9 for strategic/social/progression intelligence,
- Phase 10 for legacy system compatibility.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase_allocation_map.md`

#### [Task important notes]

Do not dump difficult rows into a catch-all “later” bucket.

#### [Task check list]

- [ ] Every open row has a target phase
- [ ] Target phase matches row type
- [ ] Catch-all buckets are avoided
- [ ] System-compatibility rows remain separate
- [ ] Phase ownership is explicit

#### [Task acceptance criteria]

Every non-closed row is assigned to a future closure phase.

---

### [ ] (checkbox) - [Task 4] - Record row dependencies and prerequisite chains across phases

#### [Task Description]

Prevent later phases from pretending they can close rows that depend on unfinished earlier work.

#### [Task technical implementation]

For each non-closed row, record dependency notes such as:

- requires substrate closure first,
- requires proof taxonomy support first,
- requires consumer-surface harness first,
- or depends on earlier support-boundary ratification.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase_dependency_map.md`

#### [Task important notes]

Rows without dependency notes will later be scheduled in impossible order.

#### [Task check list]

- [ ] Dependencies are explicit
- [ ] Prerequisites are explicit
- [ ] Cross-phase blockers are visible
- [ ] Impossible sequencing is reduced
- [ ] Dependency notes are concise

#### [Task acceptance criteria]

Open ledger rows have explicit dependency and prerequisite notes.

---

### [ ] (checkbox) - [Task 5] - Define explicit closure conditions for every non-closed row

#### [Task Description]

Fix the later finish lines now so future phases cannot move them opportunistically.

#### [Task technical implementation]

For each non-closed row, define what closure actually requires.

Examples:

- one or more tests,
- one or more docs/support updates,
- divergence-log update if not preserved,
- lifecycle/certification review where relevant,
- black-box compatibility proof where relevant.

This follows the handbook’s official-support and completion standards directly.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/closure_conditions.md`

#### [Task important notes]

If closure conditions are not explicit now, later phases will declare victory on vibes.

#### [Task check list]

- [ ] Closure condition exists per non-closed row
- [ ] Closure condition matches row type
- [ ] Docs/divergence requirements are included where needed
- [ ] Lifecycle/certification implications are included where needed
- [ ] Closure conditions are reviewable

#### [Task acceptance criteria]

Every non-closed row has an explicit closure condition.

---

### [ ] (checkbox) - [Task 6] - Publish the authoritative phase-allocation map derived from the replacement ledger

#### [Task Description]

Turn row-level allocation into the official bridge from Phase 6 to later phases.

#### [Task technical implementation]

Publish one phase-allocation map that summarizes:

- open rows by target phase,
- open rows by proof-path type,
- major dependency clusters,
- and the key blockers that later phases inherit.

#### [Task possible affected files]

- `docs/engine/phase_allocation_map.md`
- `docs/engine/remaining_replacement_scope.md`

#### [Task important notes]

Later phase planning should consume this map, not reinvent it.

#### [Task check list]

- [ ] Map is published
- [ ] Rows are grouped by phase
- [ ] Proof-path groups are visible
- [ ] Dependency clusters are visible
- [ ] Later-phase consumers can use it directly

#### [Task acceptance criteria]

The project has one authoritative phase-allocation map derived from the ledger.
