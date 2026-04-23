Below is the **full detailed implementation plan for Phase 10**, in the same milestone/task structure style as your earlier implementation docs, and aligned with the Phase 10 high-level plan plus the roadmap and V2 completion rules in [resource_phases.md](sandbox:/mnt/data/resource_phases.md), [src_v2_principle.md](sandbox:/mnt/data/src_v2_principle.md), and the legacy system-compatibility surface captured in [legacy_logic_checklist_part2.md](sandbox:/mnt/data/legacy_logic_checklist_part2.md).

# Detailed Implementation Plan — Phase 10 of `src_v2`

This plan assumes Phase 9 has already produced:

- a supported long-horizon strategic/cognitive slice,
- a supported blocker/lead/knowledge slice,
- a supported social/contract slice,
- a supported progression/class/skill/reward slice,
- explicit divergences and unsupported remainder for those long-horizon semantics,
- and a formal Phase 9 exit package that later phases are required to trust.

Phase 10 is not a cleanup phase.

It is the phase where the project must recover the remaining **legacy system-compatibility surface** required for true replacement of original `src`.

The compatibility surface this phase is trying to close is:

- CLI and entrypoint behavior,
- environment-flag and disabled-infrastructure behavior,
- replay/logging/metrics/report artifact compatibility,
- API/protocol/transport behavior,
- headless/final-system execution behavior,
- and the proof surface that distinguishes preserved compatibility from deliberate divergence.

This document expands the high-level Phase 10 plan into implementation-ready milestone detail using the same milestone and task structure as the earlier plans.

---

# [Milestone 1] - Phase 9 Exit Closure and Phase 10 Readiness

## [Milestone Description]

Milestone 1 is the gate between completed semantic recovery and legitimate Phase 10 compatibility closure.

Its purpose is to make sure Phase 10 does not inherit unstable ownership, vague closure conditions, or inflated system-surface claims from the Phase 9 handoff.

By this point, the project may already have:

- a much more complete gameplay-semantic surface,
- a formal Phase 9 exit package,
- and broad pressure to “just switch the consumers to V2.”

That is still not enough.

This milestone exists because Phase 10 should not proceed while:

- compatibility rows are still mixed with semantic rows already owned by Phases 5 through 9,
- compatibility rows are still mixed with Phase 11 proof-ratification work or Phase 12 cutover work,
- closure conditions for compatibility rows remain vague,
- or current support language still overstates entry, observability, API, or headless compatibility that has not actually been proven.

This milestone does not close compatibility behavior itself.

It closes the semantics-to-system-surface handoff honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 10.

This milestone must complete readiness closure in six areas:

1. **Phase 10 row ownership closure**
   - compatibility rows assigned to Phase 10 must be frozen and separated from semantic rows and later cutover/retirement rows.

2. **Phase 10 closure-condition closure**
   - every Phase 10 row must have explicit closure conditions, not broad “system ready” language.

3. **Dependency visibility closure**
   - later rows that depend on unfinished compatibility behavior must be visibly blocked.

4. **Support-boundary closure**
   - the current support boundary for entry, disabled-mode, operational-artifact, and consumer/system compatibility scope must be restated honestly before implementation begins.

5. **Cross-phase boundary closure**
   - semantic closure, compatibility closure, proof-ratification, and cutover must be explicitly distinguished.

6. **Phase 10 baseline closure**
   - the project must publish one formal “this is the compatibility gap set entering Phase 10” package.

This milestone must not:

- reopen Phase 9 semantic closure except for genuine handoff defects,
- start cutover or retirement work under the excuse of “compatibility prep,”
- or allow compatibility work to dissolve into vague “general cleanup.”

## [Milestone important notes]

The trap here is calling compatibility “polish.”

That is fraud.

If the old system’s entry, disabled-mode, replay/report, API, or headless behavior still matters to users, operators, or tooling, then this is real replacement scope.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- the exact Phase 10 row set is frozen,
- compatibility scope is separated from semantic closure and later cutover scope,
- closure conditions for Phase 10 rows are explicit,
- the current compatibility support boundary is restated honestly,
- cross-phase boundaries are explicit,
- and the branch has a formal “Phase 10 ready” gate.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the exact Phase 10 replacement-ledger row set as the official compatibility backlog

#### [Task Description]

Turn Phase 10 ownership into one explicit implementation backlog.

#### [Task technical implementation]

Create or refresh one Phase 10 row package covering only rows owned by:

- CLI and entry compatibility,
- environment-flag and disabled-infrastructure compatibility,
- replay/logging/metrics/report compatibility,
- API/protocol/transport compatibility,
- and headless/final-system compatibility.

This task should:

- collect all Phase 10-owned rows from the replacement ledger,
- exclude rows owned by semantic phases,
- exclude rows owned by Phase 11 proof-ratification work,
- exclude rows owned by Phase 12 cutover and Phase 13 retirement,
- and publish the resulting row set as the official Phase 10 backlog.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase10_backlog.md`
- `docs/engine/phase_allocation_map.md`

#### [Task important notes]

Do not let “system-related” become an excuse to smuggle cutover work into this phase.

#### [Task check list]

- [ ] Phase 10 rows are collected
- [ ] Non-Phase 10 rows are excluded
- [ ] Ownership is explicit
- [ ] Row wording is stable
- [ ] Backlog is reviewable

#### [Task acceptance criteria]

The project has one explicit Phase 10 compatibility backlog derived from the locked ledger.

---

### [ ] (checkbox) - [Task 2] - Freeze explicit closure conditions for every Phase 10 row

#### [Task Description]

Stop Phase 10 from using fake finish lines like “usable enough.”

#### [Task technical implementation]

For each Phase 10 row, confirm or refine its closure condition so it is concrete enough to guide implementation.

Closure conditions should specify, where relevant:

- direct compatibility contract tests,
- characterization and differential proof against original `src`,
- support-boundary updates,
- divergence-log updates,
- and black-box or consumer-facing validation where those are part of the preserved surface.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/closure_conditions.md`
- `docs/engine/phase10_backlog.md`

#### [Task important notes]

If the finish line is “works for us,” the phase is already compromised.

#### [Task check list]

- [ ] Every Phase 10 row has a closure condition
- [ ] Conditions are test/proof aware
- [ ] Docs/support updates are included
- [ ] Divergence handling is included where needed
- [ ] Consumer-surface validation is explicit where needed

#### [Task acceptance criteria]

Every Phase 10 row has a fixed and explicit finish line.

---

### [ ] (checkbox) - [Task 3] - Publish downstream dependency blockers caused by unfinished compatibility rows

#### [Task Description]

Make later phases stop pretending cutover can happen on unproven compatibility.

#### [Task technical implementation]

For each downstream row blocked by unfinished compatibility behavior, record:

- which Phase 10 row blocks it,
- what guarantee is missing,
- and what later phases must not assume until the blocker is closed.

#### [Task possible affected files]

- `docs/engine/phase_dependency_map.md`
- `docs/engine/remaining_replacement_scope.md`
- `docs/engine/phase10_backlog.md`

#### [Task important notes]

If blocker visibility is missing, people will try to cut over on vibes.

#### [Task check list]

- [ ] Blocked downstream rows are identified
- [ ] Missing guarantees are named
- [ ] Phase ownership stays explicit
- [ ] Dependency notes are concise
- [ ] Later assumptions are constrained

#### [Task acceptance criteria]

Downstream dependency blockers are visible and linked to unfinished Phase 10 rows.

---

### [ ] (checkbox) - [Task 4] - Reconfirm and publish the current compatibility support boundary entering Phase 10

#### [Task Description]

Restate what the engine can honestly claim before Phase 10 changes it.

#### [Task technical implementation]

Publish or refresh one support-boundary package covering:

- what entry/CLI compatibility already exists,
- what disabled-mode or infrastructure-isolation behavior already exists,
- what replay/logging/metrics/report compatibility already exists,
- what API/protocol/headless behavior already exists,
- and what remains unsupported, provisional, or merely implemented.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase10_entry_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Do not start Phase 10 while pretending the old system surface is already mostly replaced.

#### [Task check list]

- [ ] Current entry compatibility is explicit
- [ ] Current disabled-mode compatibility is explicit
- [ ] Current artifact compatibility is explicit
- [ ] Current consumer/API compatibility is explicit
- [ ] Unsupported remainder is explicit

#### [Task acceptance criteria]

The project has one honest statement of compatibility support entering Phase 10.

---

### [ ] (checkbox) - [Task 5] - Publish the Phase 10 cross-phase boundary note for semantics, compatibility, ratification, and cutover

#### [Task Description]

Stop four different kinds of work from collapsing into one fake “system finish” phase.

#### [Task technical implementation]

Publish one boundary note that clearly distinguishes:

- semantic recovery already owned by Phases 5 through 9,
- compatibility closure owned by Phase 10,
- proof-ratification owned by Phase 11,
- and consumer cutover owned by Phase 12.

#### [Task possible affected files]

- `docs/engine/phase10_boundary_notes.md`
- `docs/engine/replacement_status_overview.md`
- `docs/engine/phase10_backlog.md`

#### [Task important notes]

This is the task that prevents fake completion claims later.

#### [Task check list]

- [ ] Semantic boundary is explicit
- [ ] Compatibility boundary is explicit
- [ ] Ratification boundary is explicit
- [ ] Cutover boundary is explicit
- [ ] Ownership ambiguity is reduced

#### [Task acceptance criteria]

The project has one explicit boundary note separating compatibility from proof-ratification and cutover.

---

### [ ] (checkbox) - [Task 6] - Publish the formal Phase 10 entry package and readiness gate

#### [Task Description]

Turn the previous tasks into one explicit Phase 10 start decision.

#### [Task technical implementation]

Create one readiness gate that requires:

- frozen Phase 10 row ownership,
- explicit closure conditions,
- downstream blocker visibility,
- a reconciled Phase 10 support boundary,
- a cross-phase boundary note,
- and one published entry package defining the compatibility gap set.

#### [Task possible affected files]

- `docs/engine/phase10_readiness_gate.md`
- `docs/engine/phase10_entry_package.md`
- milestone review docs

#### [Task important notes]

This is the line between “Phase 10 is discussed” and “Phase 10 is executable.”

#### [Task check list]

- [ ] Gate conditions are explicit
- [ ] Gate conditions are reviewable
- [ ] Supporting artifacts are linked
- [ ] Known limitations are attached
- [ ] Phase 10 entry is unambiguous

#### [Task acceptance criteria]

The branch has a precise and honest entry gate for Phase 10.
