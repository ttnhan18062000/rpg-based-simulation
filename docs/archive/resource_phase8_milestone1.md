Below is the **full detailed implementation plan for Phase 8**, using the same milestone/task structure style as your earlier implementation docs, and aligned with the Phase 8 high-level plan, the revised roadmap, the legacy replacement checklists, and the V2 completion rules in:

[resource_phase5_implementation_milestone_1.md](sandbox:/mnt/data/resource_phase5_implementation_milestone_1.md)
[resource_phases.md](sandbox:/mnt/data/resource_phases.md)
[legacy_logic_checklist_part1.md](sandbox:/mnt/data/legacy_logic_checklist_part1.md)
[legacy_logic_checklist_part4.md](sandbox:/mnt/data/legacy_logic_checklist_part4.md)
[legacy_logic_checklist_part5.md](sandbox:/mnt/data/legacy_logic_checklist_part5.md)
[src_principle.md](sandbox:/mnt/data/src_principle.md)

# Detailed Implementation Plan — Phase 8 of `src`

This plan assumes Phase 7 has already produced:

- a closed deterministic substrate for supported authority paths,
- explicit action/update and apply-path contracts,
- explicit snapshot/state integrity guarantees,
- explicit deterministic world/init/order contracts,
- and a Phase 7 exit package that later phases are required to trust.

Phase 8 is not a broad “bring back gameplay” phase.

It is the phase where the project must recover the next large semantic surface of original `src`:

- combat legality,
- direct combat outcome semantics,
- bounded local tactical behavior,
- and local environment/world-interaction semantics that materially shape direct action and combat behavior.

The semantic surface this phase is trying to close is:

- who can fight whom, when, and under what legality rules,
- how direct combat outcomes are authoritatively emitted and applied,
- how entities behave in immediate tactical conflict,
- how terrain/buildings/local position affect immediate action semantics,
- and how the supported local gameplay slice is proven against original `src` where preservation is required.

This document expands the high-level Phase 8 plan into implementation-ready milestone detail using the same milestone and task structure as the earlier plans.

---

# [Milestone 1] - Phase 7 Exit Closure and Phase 8 Readiness

## [Milestone Description]

Milestone 1 is the gate between completed substrate closure and legitimate Phase 8 semantic recovery.

Its purpose is to make sure Phase 8 does not inherit unstable ownership, vague closure conditions, or inflated combat/tactical claims from the Phase 7 handoff.

By this point, the project may already have:

- a formal Phase 7 exit package,
- explicit deterministic substrate contracts,
- and a broad sense that “the engine is finally ready for gameplay.”

That is still not enough.

This milestone exists because Phase 8 should not proceed while:

- combat/tactical/local-world rows are still mixed with Phase 7 substrate rows,
- combat/tactical rows are still mixed with Phase 9 strategy/social/progression rows,
- closure conditions for Phase 8 rows remain vague,
- or current support language implies more combat/tactical recovery than the branch actually has.

This milestone does not recover combat or tactical behavior itself.
It closes the substrate-to-semantics handoff honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 8.

This milestone must complete the readiness closure in five areas:

1. **Phase 8 row ownership closure**
   - combat, bounded local tactics, and local world-interaction rows assigned to Phase 8 must be frozen and separated from substrate, strategy, and compatibility rows.

2. **Phase 8 closure-condition closure**
   - every Phase 8 row must have explicit closure conditions, not broad “gameplay is restored” language.

3. **Dependency visibility closure**
   - later rows that depend on unsupported or unfinished combat semantics must be visibly blocked.

4. **Support-boundary closure**
   - the current support boundary for combat/tactical/world semantics must be restated honestly before implementation begins.

5. **Phase 8 baseline closure**
   - the project must publish one formal “this is the semantic gap set entering Phase 8” package.

This milestone must not:

- reopen Phase 7 substrate closure except for genuine handoff defects,
- begin progression or strategic recovery under the excuse of combat context,
- or allow ownership blur between combat, tactics, environment semantics, and later strategic layers.

## [Milestone important notes]

The trap here is scope collapse.

If you let Phase 8 absorb strategy, social, class/progression, or compatibility work, the phase stops being governable and later phases become duplicates of it.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- the exact Phase 8 row set is frozen,
- combat/tactical/local-world scope is separated from substrate and later semantic scope,
- closure conditions for Phase 8 rows are explicit,
- the current support boundary is restated honestly,
- and the branch has a formal “Phase 8 ready” gate.

---

## Task

### [x] - [Task 1] - Freeze the exact Phase 8 replacement-ledger row set as the official combat/tactical/local-world backlog

#### [Task Description]

Turn Phase 8 ownership into one explicit implementation backlog.

#### [Task technical implementation]

Create or refresh one Phase 8 row package covering only rows owned by:

- direct combat legality,
- direct combat outcomes,
- bounded local tactical behavior,
- and local terrain/building/world-interaction semantics that materially affect immediate action.

This task should:

- collect all Phase 8-owned rows from the replacement ledger,
- exclude rows owned by Phase 7 deterministic substrate closure,
- exclude rows owned by Phase 9 strategic/social/progression recovery,
- exclude rows owned by Phase 10 compatibility closure,
- and publish the resulting row set as the official Phase 8 backlog.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase8_backlog.md`
- `docs/engine/phase_allocation_map.md`

#### [Task important notes]

Do not let “combat-adjacent” become an excuse for importing strategy rows into this phase.

#### [Task check list]

- [x] Phase 8 rows are collected
- [x] Non-Phase 8 rows are excluded
- [x] Ownership is explicit
- [x] Row wording is stable
- [x] Backlog is reviewable

#### [Implementation Comment]
Created `docs/engine/phase8_backlog.md` with 12 items. Reallocated 6 strategic/social rows to Phase 9.

#### [Task acceptance criteria]

The project has one explicit Phase 8 semantic backlog derived from the locked ledger.

---

### [x] - [Task 2] - Freeze explicit closure conditions for every Phase 8 row

#### [Task Description]

Stop Phase 8 from using soft finish lines.

#### [Task technical implementation]

For each Phase 8 row, confirm or refine its closure condition so it is concrete enough to guide implementation.

Closure conditions should specify, where relevant:

- required direct combat contract tests,
- tactical behavior tests,
- differential/parity tests against original `src`,
- support-boundary updates,
- and divergence-log updates where strict preservation is not intended.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/closure_conditions.md`
- `docs/engine/phase8_backlog.md`

#### [Task important notes]

If the finish line is “combat feels better,” the phase is already corrupt.

#### [Task check list]

- [x] Every Phase 8 row has a closure condition
- [x] Conditions are test/proof aware
- [x] Docs/support updates are included
- [x] Divergence handling is included where needed
- [x] Conditions are reviewable

#### [Implementation Comment]
Created `docs/engine/phase8_closure_conditions.md` defining finish lines for combat legality and tactical behavior.

#### [Task acceptance criteria]

Every Phase 8 row has a fixed and explicit finish line.

---

### [x] - [Task 3] - Publish downstream dependency blockers caused by unfinished Phase 8 semantics

#### [Task Description]

Make later phases stop pretending they can float above local gameplay semantics.

#### [Task technical implementation]

For each downstream row blocked by unfinished combat/tactical/local-world semantics, record:

- which Phase 8 row blocks it,
- what guarantee is missing,
- and what later phases must not assume until the blocker is closed.

#### [Task possible affected files]

- `docs/engine/phase_dependency_map.md`
- `docs/engine/remaining_replacement_scope.md`
- `docs/engine/phase8_backlog.md`

#### [Task important notes]

If blocker visibility is missing, teams will build strategy or progression logic on fake local semantics.

#### [Task check list]

- [x] Blocked downstream rows are identified
- [x] Missing guarantees are named
- [x] Phase ownership stays explicit
- [x] Dependency notes are concise
- [x] Later assumptions are constrained

#### [Implementation Comment]
Created `docs/engine/phase_dependency_map.md`. Identified blockers for Phase 9 Belief and Betrayal logic.

#### [Task acceptance criteria]

Downstream dependency blockers are visible and linked to unfinished Phase 8 rows.

---

### [x] - [Task 4] - Reconfirm and publish the current combat/tactical/local-world support boundary entering Phase 8

#### [Task Description]

Restate what the engine can honestly claim before Phase 8 changes it.

#### [Task technical implementation]

Publish or refresh one support-boundary package covering:

- what combat legality is already supported,
- what direct combat outcome semantics already exist,
- what local tactical guarantees already exist,
- what local world-interaction guarantees already exist,
- and what remains unsupported, provisional, or merely implemented.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase8_entry_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Do not start Phase 8 while pretending local gameplay support is broader than it is.

#### [Task check list]

- [x] Current combat support is explicit
- [x] Current tactical support is explicit
- [x] Current local world-interaction support is explicit
- [x] Unsupported remainder is explicit
- [x] Wording matches actual branch reality

#### [Implementation Comment]
Created `docs/engine/phase8_entry_support_boundary.md`. Established BRONZE semantics baseline.

#### [Task acceptance criteria]

The project has one honest statement of combat/tactical/local-world support entering Phase 8.

---

### [x] - [Task 5] - Publish the formal Phase 8 entry package and readiness gate

#### [Task Description]

Turn the previous tasks into one explicit Phase 8 start decision.

#### [Task technical implementation]

Create one readiness gate that requires:

- frozen Phase 8 row ownership,
- explicit closure conditions,
- downstream blocker visibility,
- a reconciled Phase 8 support boundary,
- and one published entry package defining the semantic gap set.

#### [Task possible affected files]

- `docs/engine/phase8_readiness_gate.md`
- `docs/engine/phase8_entry_package.md`
- milestone review docs

#### [Task important notes]

This is the line between “Phase 8 is discussed” and “Phase 8 is executable.”

#### [Task check list]

- [x] Gate conditions are explicit
- [x] Gate conditions are reviewable
- [x] Supporting artifacts are linked
- [x] Known limitations are attached
- [x] Phase 8 entry is unambiguous

#### [Implementation Comment]
Created `docs/engine/phase8_entry_package.md` and `docs/engine/phase8_readiness_gate.md`. Phase 8 is officially OPEN.

#### [Task acceptance criteria]

The branch has a precise and honest entry gate for Phase 8.
