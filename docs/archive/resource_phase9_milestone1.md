---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

Below is the **full detailed implementation plan for Phase 9**, in the same milestone/task structure style as your earlier implementation docs, and aligned with the Phase 9 high-level plan plus the roadmap/checklist surfaces in [resource_phases.md](sandbox:/mnt/data/resource_phases.md), [legacy_logic_checklist_part4.md](sandbox:/mnt/data/legacy_logic_checklist_part4.md), [legacy_logic_checklist_part5.md](sandbox:/mnt/data/legacy_logic_checklist_part5.md), and [src_principle.md](sandbox:/mnt/data/src_principle.md).

# Detailed Implementation Plan — Phase 9 of `src`

This plan assumes Phase 8 has already produced:

- a supported direct combat semantic slice,
- a supported bounded local tactical slice,
- a supported local environment/world-interaction slice,
- explicit divergences and unsupported remainder for those local semantics,
- and a formal Phase 8 exit package that later phases are required to trust.

Phase 9 is not a broad “AI overhaul” phase.

It is the phase where the project must recover the next large long-horizon semantic surface of original `src`:

- strategic continuity,
- bounded cognition and explainability,
- blockers, leads, and knowledge continuity,
- social consequence and contracts,
- progression, classes, skills, attributes, and rewards.

The semantic surface this phase is trying to close is:

- how actors preserve and switch long-horizon intentions across ticks,
- how bounded cognition limits and explains that behavior,
- how blockers, leads, trust, and uncertainty shape future choices,
- how social memory and contracts alter strategic decisions,
- and how outcomes accumulate into meaningful progression truth over time.

This document expands the high-level Phase 9 plan into implementation-ready milestone detail using the same milestone and task structure as the earlier plans.

---

# [Milestone 1] - Phase 8 Exit Closure and Phase 9 Readiness

## [Milestone Description]

Milestone 1 is the gate between completed local-gameplay closure and legitimate Phase 9 long-horizon semantic recovery.

Its purpose is to make sure Phase 9 does not inherit unstable ownership, vague closure conditions, or inflated support claims from the Phase 8 handoff.

By this point, the project may already have:

- credible local combat and tactical behavior,
- a formal Phase 8 exit package,
- and pressure to “just bring back AI, social, and progression.”

That is still not enough.

This milestone exists because Phase 9 should not proceed while:

- strategic/cognitive rows are still mixed with Phase 8 tactical rows,
- blocker/lead rows are still mixed with Phase 5 direct resource-resolution rows,
- social/contract rows are still mixed with compatibility or cutover rows,
- progression rows are still mixed with local combat semantics already owned by Phase 8,
- or current support language implies broader long-horizon closure than the branch actually has.

This milestone does not recover strategic, social, or progression behavior itself.
It closes the local-gameplay-to-long-horizon handoff honestly.

## [Milestone technical implementation]

Create one explicit entry gate for Phase 9.

This milestone must complete readiness closure in six areas:

1. **Phase 9 row ownership closure**
   - strategic, cognitive, blocker/lead, social, and progression rows assigned to Phase 9 must be frozen and separated from Phase 8 and Phase 10 rows.

2. **Phase 9 closure-condition closure**
   - every Phase 9 row must have explicit closure conditions, not broad “AI/progression is back” language.

3. **Dependency visibility closure**
   - later rows that depend on unfinished long-horizon semantics must be visibly blocked.

4. **Support-boundary closure**
   - the current support boundary for strategic/social/progression scope must be restated honestly before implementation begins.

5. **Cross-phase boundary closure**
   - Phase 5 resource loops, Phase 8 tactical semantics, and Phase 9 long-horizon intelligence/progression semantics must be distinguished explicitly.

6. **Phase 9 baseline closure**
   - the project must publish one formal “this is the semantic gap set entering Phase 9” package.

This milestone must not:

- reopen Phase 8 local semantic closure except for genuine handoff defects,
- start compatibility work under the excuse of “consumer-facing AI behavior,”
- or allow long-horizon meaning to blur back into local tactical ownership.

## [Milestone important notes]

The trap here is lazy naming.

If “AI,” “memory,” “strategy,” “social,” and “progression” are left as one fuzzy blob, the phase becomes impossible to govern and every milestone starts duplicating every other one.

## [Milestone acceptance criteria]

At the end of Milestone 1:

- the exact Phase 9 row set is frozen,
- strategic/cognitive/social/progression scope is separated from local tactical and compatibility scope,
- closure conditions for Phase 9 rows are explicit,
- the current support boundary is restated honestly,
- cross-phase ownership boundaries are explicit,
- and the branch has a formal “Phase 9 ready” gate.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the exact Phase 9 replacement-ledger row set as the official long-horizon semantic backlog

#### [Task Description]

Turn Phase 9 ownership into one explicit implementation backlog.

#### [Task technical implementation]

Create or refresh one Phase 9 row package covering only rows owned by:

- strategic continuity,
- bounded cognition and explainability,
- blockers/leads/knowledge continuity,
- social consequence/contracts/trust/recruitment,
- and progression/classes/skills/attributes/rewards.

This task should:

- collect all Phase 9-owned rows from the replacement ledger,
- exclude rows owned by Phase 8 local gameplay semantics,
- exclude rows owned by Phase 10 compatibility closure,
- and publish the resulting row set as the official Phase 9 backlog.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/phase9_backlog.md`
- `docs/engine/phase_allocation_map.md`

#### [Task important notes]

Do not let “AI-adjacent” become an excuse for importing compatibility or local tactical rows into this phase.

#### [Task check list]

- [ ] Phase 9 rows are collected
- [ ] Non-Phase 9 rows are excluded
- [ ] Ownership is explicit
- [ ] Row wording is stable
- [ ] Backlog is reviewable

#### [Task acceptance criteria]

The project has one explicit Phase 9 backlog derived from the locked ledger.

---

### [ ] (checkbox) - [Task 2] - Freeze explicit closure conditions for every Phase 9 row

#### [Task Description]

Stop Phase 9 from using soft finish lines.

#### [Task technical implementation]

For each Phase 9 row, confirm or refine its closure condition so it is concrete enough to guide implementation.

Closure conditions should specify, where relevant:

- direct strategic/social/progression contract tests,
- characterization and differential proof against original `src`,
- support-boundary updates,
- divergence-log updates,
- and explainability or boundedness proof where those are part of the preserved surface.

#### [Task possible affected files]

- `docs/engine/replacement_ledger.md`
- `docs/engine/closure_conditions.md`
- `docs/engine/phase9_backlog.md`

#### [Task important notes]

If the finish line is “agents feel smarter,” the phase is already corrupted.

#### [Task check list]

- [ ] Every Phase 9 row has a closure condition
- [ ] Conditions are test/proof aware
- [ ] Docs/support updates are included
- [ ] Divergence handling is included where needed
- [ ] Boundedness/explainability obligations are explicit where needed

#### [Task acceptance criteria]

Every Phase 9 row has a fixed and explicit finish line.

---

### [ ] (checkbox) - [Task 3] - Publish downstream dependency blockers caused by unfinished Phase 9 semantics

#### [Task Description]

Make later phases stop pretending they can float above unfinished long-horizon meaning.

#### [Task technical implementation]

For each downstream row blocked by unfinished strategic/social/progression semantics, record:

- which Phase 9 row blocks it,
- what guarantee is missing,
- and what later phases must not assume until the blocker is closed.

#### [Task possible affected files]

- `docs/engine/phase_dependency_map.md`
- `docs/engine/remaining_replacement_scope.md`
- `docs/engine/phase9_backlog.md`

#### [Task important notes]

If blocker visibility is missing, teams will build compatibility or cutover logic on fake semantic closure.

#### [Task check list]

- [ ] Blocked downstream rows are identified
- [ ] Missing guarantees are named
- [ ] Phase ownership stays explicit
- [ ] Dependency notes are concise
- [ ] Later assumptions are constrained

#### [Task acceptance criteria]

Downstream dependency blockers are visible and linked to unfinished Phase 9 rows.

---

### [ ] (checkbox) - [Task 4] - Reconfirm and publish the current strategic/social/progression support boundary entering Phase 9

#### [Task Description]

Restate what the engine can honestly claim before Phase 9 changes it.

#### [Task technical implementation]

Publish or refresh one support-boundary package covering:

- what strategic continuity is already supported,
- what blocker/lead/knowledge continuity semantics already exist,
- what social/contract semantics already exist,
- what progression semantics already exist,
- and what remains unsupported, provisional, or merely implemented.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase9_entry_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Do not start Phase 9 while pretending long-horizon semantics are broader than they are.

#### [Task check list]

- [ ] Current strategic support is explicit
- [ ] Current blocker/lead support is explicit
- [ ] Current social/contract support is explicit
- [ ] Current progression support is explicit
- [ ] Unsupported remainder is explicit

#### [Task acceptance criteria]

The project has one honest statement of strategic/social/progression support entering Phase 9.

---

### [ ] (checkbox) - [Task 5] - Publish the Phase 9 cross-phase boundary note for resource loops, local tactics, and long-horizon semantics

#### [Task Description]

Stop three different kinds of meaning from collapsing into one vague layer.

#### [Task technical implementation]

Publish one boundary note that clearly distinguishes:

- Phase 5 direct resource loop and town-resolution semantics,
- Phase 8 local combat/tactical/world semantics,
- Phase 9 long-horizon blocker/lead/social/progression semantics.

#### [Task possible affected files]

- `docs/engine/phase9_boundary_notes.md`
- `docs/engine/replacement_status_overview.md`
- `docs/engine/phase9_backlog.md`

#### [Task important notes]

This is the task that prevents duplicated work and fake ownership.

#### [Task check list]

- [ ] Phase 5 boundary is explicit
- [ ] Phase 8 boundary is explicit
- [ ] Phase 9 boundary is explicit
- [ ] Overlap points are explained
- [ ] Ownership ambiguity is reduced

#### [Task acceptance criteria]

The project has one explicit boundary note separating local and long-horizon semantics.

---

### [ ] (checkbox) - [Task 6] - Publish the formal Phase 9 entry package and readiness gate

#### [Task Description]

Turn the previous tasks into one explicit Phase 9 start decision.

#### [Task technical implementation]

Create one readiness gate that requires:

- frozen Phase 9 row ownership,
- explicit closure conditions,
- downstream blocker visibility,
- a reconciled Phase 9 support boundary,
- a cross-phase boundary note,
- and one published entry package defining the semantic gap set.

#### [Task possible affected files]

- `docs/engine/phase9_readiness_gate.md`
- `docs/engine/phase9_entry_package.md`
- milestone review docs

#### [Task important notes]

This is the line between “Phase 9 is discussed” and “Phase 9 is executable.”

#### [Task check list]

- [ ] Gate conditions are explicit
- [ ] Gate conditions are reviewable
- [ ] Supporting artifacts are linked
- [ ] Known limitations are attached
- [ ] Phase 9 entry is unambiguous

#### [Task acceptance criteria]

The branch has a precise and honest entry gate for Phase 9.
