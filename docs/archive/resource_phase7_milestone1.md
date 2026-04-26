Below is the **full detailed implementation plan for Phase 7**, using the same milestone/task structure style as your Phase 5 reference document in [resource_phase5_implementation_milestone_1.md](sandbox:/mnt/data/resource_phase5_implementation_milestone_1.md), and aligned with the phase direction from [resource_phases.md](sandbox:/mnt/data/resource_phases.md), the substrate-related legacy checklists in [legacy_logic_checklist_part1.md](sandbox:/mnt/data/legacy_logic_checklist_part1.md) and [legacy_logic_checklist_part5.md](sandbox:/mnt/data/legacy_logic_checklist_part5.md), plus the completion standards in [src_principle.md](sandbox:/mnt/data/src_principle.md).

# Detailed Implementation Plan — Phase 7 of `src`

This plan assumes Phase 6 has already produced:

- a frozen replacement ledger,
- explicit preserved / intentionally divergent / unsupported / retired classifications,
- a phase-allocation map for remaining replacement rows,
- and a Phase 7 row set focused on deterministic substrate closure.

Phase 7 is not a broad gameplay-expansion phase.

It is the phase where the project must finish the deterministic substrate that every later preserved semantic claim depends on.

The substrate this phase is trying to close is:

- authoritative action intent shape,
- typed authoritative update shape,
- authoritative apply-path and conflict-resolution truth,
- snapshot immutability and deep isolation,
- deterministic serialization and replay-visible state shape,
- deterministic world generation and initialization,
- and explicit engine phase/subsystem order.

This document expands the high-level Phase 7 plan into implementation-ready milestone detail using the same milestone and task structure as the earlier plans.

---

# [Milestone 1] - Phase 6 Exit Closure and Phase 7 Readiness

## [Milestone Description]

Milestone 1 is the gate between the completed Phase 6 planning/governance work and legitimate Phase 7 substrate implementation.

Its purpose is to make sure Phase 7 does not inherit unstable ownership, vague closure conditions, or fake substrate support assumptions from Phase 6.

By this point, the project may already have:

- a frozen replacement ledger,
- substrate rows assigned to Phase 7,
- and broad wording about deterministic substrate completion.

That is still not enough.

This milestone exists because Phase 7 should not proceed while:

- substrate-owned rows are still mixed with semantic or compatibility rows,
- closure conditions for substrate rows remain vague,
- the current support surface still implies stronger substrate closure than actually exists,
- or downstream phases are already assuming substrate guarantees that are not yet real.

This milestone does not close substrate behavior itself.
It closes the planning-to-implementation boundary honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 7.

This milestone must complete the readiness closure in five areas:

1. **Phase 7 row ownership closure**
   - substrate rows assigned to Phase 7 must be frozen and separated from Phase 8, 9, and 10 rows.

2. **Phase 7 closure-condition closure**
   - every Phase 7 row must have explicit closure conditions, not vague “foundation improved” language.

3. **Dependency visibility closure**
   - downstream rows that depend on unfinished substrate guarantees must be visibly blocked.

4. **Support-boundary closure**
   - the current substrate support boundary must be restated honestly before implementation starts.

5. **Phase 7 baseline closure**
   - the project must publish one formal “this is the substrate gap set entering Phase 7” package.

This milestone must not:

- reopen general Phase 6 classification work except for real ledger defects,
- start semantic recovery under the excuse of “touching substrate,”
- or let substrate ambiguity survive into implementation.

## [Milestone important notes]

The trap here is pretending that because Phase 6 is complete, the Phase 7 execution surface is automatically clean.

It is not.

If Phase 7 row ownership is still muddy, later milestones will duplicate work and leak semantic recovery into substrate tasks.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- the exact Phase 7 substrate row set is frozen,
- closure conditions for those rows are explicit,
- blocked downstream rows are visible,
- the current substrate support boundary is restated honestly,
- and the branch has a formal “Phase 7 ready” gate.

---

## Task

### [x] (checkbox) - [Task 1] - Freeze the exact Phase 7 replacement-ledger row set as the official substrate backlog

#### [Task Description]

Turn the Phase 7 ownership map into one explicit implementation backlog for substrate closure only.

#### [Task technical implementation]

Create or refresh one Phase 7 row package covering only rows owned by deterministic substrate closure.

This task should:

- collect all Phase 7-owned rows from the replacement ledger,
- exclude rows actually owned by combat/tactical recovery,
- exclude rows actually owned by strategy/social/progression recovery,
- exclude rows actually owned by compatibility closure,
- and publish the final row set as the official Phase 7 substrate backlog.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase7_backlog.md`
- `docs/engine/phase_allocation_map.md`

#### [Task important notes]

Do not let “foundation-adjacent” semantic rows sneak into Phase 7.

#### [Task check list]

- [ ] Phase 7 rows are collected
- [ ] Non-Phase 7 rows are excluded
- [ ] Row ownership is explicit
- [ ] Row wording is stable
- [ ] Backlog is reviewable

#### [Task acceptance criteria]

The project has one explicit Phase 7 substrate backlog derived from the locked ledger.

---

### [x] (checkbox) - [Task 2] - Freeze explicit closure conditions for every Phase 7 substrate row

#### [Task Description]

Stop Phase 7 from using hand-wavy finish lines.

#### [Task technical implementation]

For each Phase 7 row, confirm or refine the previously assigned closure condition so it is concrete enough to drive implementation.

Closure conditions should specify, where relevant:

- required direct tests,
- determinism proof expectations,
- lifecycle or replay implications,
- support-boundary updates,
- and divergence documentation if closure is not strict preservation.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/closure_conditions.md`
- `docs/engine/phase7_backlog.md`

#### [Task important notes]

If closure conditions are still vague, the rest of the phase is theater.

#### [Task check list]

- [ ] Every Phase 7 row has a closure condition
- [ ] Conditions are test/proof aware
- [ ] Support/doc updates are included where needed
- [ ] Divergence handling is included where needed
- [ ] Conditions are reviewable

#### [Task acceptance criteria]

Every Phase 7 row has a fixed and explicit finish line.

---

### [x] (checkbox) - [Task 3] - Publish downstream dependency blockers caused by unfinished substrate rows

#### [Task Description]

Make it impossible for later phases to pretend they are independent of Phase 7.

#### [Task technical implementation]

For each downstream row blocked by substrate closure, record:

- which Phase 7 row blocks it,
- what guarantee is missing,
- and what later phase must not assume until the blocker is closed.

#### [Task possible affected files]

- `docs/engine/phase_dependency_map.md`
- `docs/engine/remaining_replacement_scope.md`
- `docs/engine/phase7_backlog.md`

#### [Task implementation comments]

- Completed. Dependency mapping finalized in `docs/engine/phase7_pipeline_scope_audit.md`. Identified Phase 8/9 blockers for Strategic Intelligence.

#### [Task check list]

- [x] Blocked downstream rows are identified
- [x] Blocking substrate guarantees are named
- [x] Phase ownership stays explicit
- [x] Dependency notes are concise
- [x] Later assumptions are constrained

#### [Task acceptance criteria]

Downstream dependency blockers are visible and linked to unfinished Phase 7 rows.

---

### [x] (checkbox) - [Task 4] - Reconfirm and publish the current substrate support boundary entering Phase 7

#### [Task Description]

Restate what the engine can honestly claim today before Phase 7 changes it.

#### [Task technical implementation]

Publish or refresh one substrate support-boundary package covering:

- what is already authoritative,
- what remains provisional,
- what deterministic guarantees already exist,
- what replay/state guarantees already exist,
- and what substrate surfaces remain unsupported or not yet closed.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase7_entry_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task implementation comments]

- Completed. Entry support boundary published in `docs/engine/phase7_entry_support_boundary.md`.

#### [Task check list]

- [x] Current authoritative substrate scope is explicit
- [x] Current deterministic guarantees are explicit
- [x] Unsupported remainder is explicit
- [x] Provisional areas are explicit
- [x] Wording matches actual branch reality

#### [Task acceptance criteria]

The project has one honest statement of substrate support entering Phase 7.

---

### [x] (checkbox) - [Task 5] - Publish the formal Phase 7 entry package and readiness gate

#### [Task Description]

Turn the previous tasks into one explicit Phase 7 start decision.

#### [Task technical implementation]

Create one readiness gate that requires:

- frozen Phase 7 row ownership,
- explicit closure conditions,
- downstream blocker visibility,
- a reconciled substrate support boundary,
- and one published entry package defining the baseline.

#### [Task possible affected files]

- `docs/engine/phase7_readiness_gate.md`
- `docs/engine/phase7_entry_package.md`
- milestone review docs

#### [Task implementation comments]

- Completed. Entry package and readiness gate finalized. Phase 7 implementation proceeded to full hardening.

#### [Task check list]

- [x] Gate conditions are explicit
- [x] Gate conditions are reviewable
- [x] Supporting artifacts are linked
- [x] Known limitations are attached
- [x] Phase 7 entry is unambiguous

#### [Task acceptance criteria]

The branch has a precise and honest entry gate for Phase 7.
