# Updated Implementation Plan — [Phase 4] of the `src_v2` Epic

## [Phase Name]

**Phase 4 — Controlled RPG-Core Attachment and Resource Loop Recovery**

---

## [Phase Description]

Phase 4 is the current implementation phase of the `src_v2` epic.

Its purpose is to move the project from infrastructure-heavy hardening into a disciplined gameplay attachment phase **without** drifting away from the original `src` RPG-core logic.

This phase begins from a mixed reality:

- the `src_v2` substrate already has substantial runtime/governance/certification structure,
- movement parity has improved materially and is now close to the original path,
- but substrate freeze is **not** closed,
- declared resource truth is **not** fully closed,
- and the original RPG-core resource loop is only **partially** represented in `src_v2`.

This phase is therefore **not** a generic “add more gameplay” phase.
It is the phase where the project must:

- close the remaining substrate truth defects,
- freeze only what is actually freeze-worthy,
- preserve original `src/tests` behavior where parity is required,
- attach official gameplay slices in the correct order,
- recover the original resource loop rather than inventing a cleaner but different one,
- and consolidate support/certification/performance claims around what is truly implemented.

This phase exists to stop the port from quietly becoming a fork.

---

## [Phase technical implementation]

Phase 4 is implemented through one gating layer plus five milestone blocks.

### 1. **Pre-Milestone Gate: Resource Truth Closure**

Before any freeze is allowed, the project must close the remaining truth gaps that would otherwise be frozen into the substrate.

This gate must close:

- replay pressure truth,
- declared resource truth,
- concurrency support-boundary truth,
- and behavior-oracle truth for official gameplay slices.

### 2. **Milestone 1: Substrate Freeze and Baseline Readiness**

Freeze the repaired substrate only after the truth-closure gate passes.

This milestone freezes:

- semantic baseline law,
- runtime/lifecycle vocabulary,
- proof bundle contract,
- supported concurrency boundaries,
- parity-or-divergence rules against original `src/tests`,
- and baseline drift guardrails.

### 3. **Milestone 2: Deterministic Grid Movement as the First Official RPG Slice**

Make movement the first officially supported gameplay slice, but only in its original meaning.

This milestone must preserve:

- grid/tile semantics,
- Manhattan distance rules,
- occupancy/blocking rules,
- blocked-move behavior,
- local authoritative commit semantics,
- and supported concurrent behavior only where explicitly proven.

### 4. **Milestone 3: Benchmarking, Profiling, and Hot-Path Optimization Foundation**

Begin real performance work only after one preserved gameplay slice exists.

This milestone establishes:

- stable benchmark scenarios,
- per-phase and per-subsystem timing,
- resource-aware measurement,
- hot-path ranking,
- optimization passes bounded by parity and lifecycle truth,
- and scoped performance claims.

### 5. **Milestone 4: Deterministic Resource Interaction Core**

Recover the second actual RPG-core slice from the original engine, rather than adding a vague “interaction” system.

This milestone must target the original resource loop components that sit immediately after movement:

- channeled looting,
- channeled harvesting,
- inventory slot pressure,
- inventory weight pressure,
- node depletion/respawn behavior,
- blocked or aborted interaction behavior,
- and authoritative state/apply integration for those systems.

This milestone must **not** expand into broad combat, quest systems, or rich AI trees.

### 6. **Milestone 5: Supported Gameplay Surface Consolidation**

Turn the attached slices into one explicit, supportable, benchmarked, and certifiable gameplay surface.

This milestone must unify:

- support matrix truth,
- certification coverage,
- benchmark coverage,
- release-proof expectations,
- regression guards,
- and explicit divergence reporting.

---

## [Phase important notes]

This phase has three major traps.

### Trap 1: freezing too early

The current branch still has known substrate defects and resource-truth gaps.
Freezing too early would formalize dishonesty.

### Trap 2: generic gameplay wording

The original `src` does not implement a generic gameplay loop.
It implements a specific RPG-core loop built around:

- grid movement,
- local occupancy rules,
- loot/harvest channeling,
- slot/weight inventory pressure,
- resource-node behavior,
- and town-driven material/gold/capability resolution.

If the phase plan uses generic slice language, the team will drift.

### Trap 3: using passing tests as a substitute for parity

A growing test count is not enough.
The current updated code shows exactly why:

- movement is now much closer to parity,
- but the resource loop is still incomplete,
- replay truth is still not fully closed,
- and substrate freeze tests still fail.

So this phase must treat original `src/tests` as the behavior oracle wherever parity is intended.

---

## [Phase acceptance criteria]

At the end of Phase 4:

- the substrate freeze is honest and test-backed,
- every declared in-scope runtime resource is either fully governed or explicitly removed from the contract,
- movement is officially supported under preserved grid/occupancy semantics,
- the second official slice preserves the original resource interaction loop rather than inventing a substitute,
- benchmark and certification claims are scoped to the actually supported gameplay surface,
- support boundaries and intentional divergences are explicit,
- and the project can state what `src_v2` currently supports **without** overstating gameplay or runtime truth.

---

## [Current verified starting state]

Phase 4 planning must reflect the real branch state, not the hoped-for branch state.

Current verified status:

- **Movement slice:** materially improved and close to the original path
- **Resource interaction slice:** partial only
- **Substrate freeze:** not closed
- **Resource truth closure:** not closed
- **Replay truth under pressure:** not closed
- **CPU resource contract:** not closed end-to-end

Known concrete issues already observed in the updated code path:

- replay early rotation / manifest truth issue,
- patch-unfriendly substrate freeze boundary around startup validation,
- tick-phase contract drift,
- interaction completion defect around node depletion,
- incomplete resource-loop parity: looting missing, weight pressure missing, town resource loop missing,
- and CPU still not wired end-to-end through measurement/governance/conformance.

This means Phase 4 is a **correction-and-attachment phase**, not a pure expansion phase.

---

## [Phase task structure]

### [x] (checkbox) - [Phase Task 1] - Close the Resource Truth Closure gate before any substrate freeze is claimed

#### [Task Description]

Resolve the remaining substrate/resource/replay/support-boundary defects that would make Milestone 1 dishonest.

#### [Task technical implementation]

This task must complete:

- replay async metadata correctness under rotation/pressure,
- explicit declared-resource closure for CPU and any other profile-declared resources,
- explicit concurrency support-boundary enforcement,
- and behavior-oracle capture rules for official gameplay slices.

#### [Task acceptance criteria]

The project cannot truthfully say “ready to freeze” until these closures are test-backed.

---

### [x] (checkbox) - [Phase Task 2] - Freeze the substrate only after truth closure is achieved

#### [Task Description]

Convert the repaired substrate into a stable build platform for gameplay attachment.

#### [Task technical implementation]

This task must freeze:

- semantic baseline law,
- lifecycle/runtime vocabulary,
- proof bundle contract,
- concurrency scope,
- and parity/divergence discipline against original `src/tests`.

#### [Task acceptance criteria]

Future gameplay work can rely on a stable substrate without reopening baseline truth every week.

---

### [x] (checkbox) - [Phase Task 3] - Finalize movement as the first official preserved RPG slice

#### [Task Description]

Make movement official only after it is scoped, parity-reviewed, support-bounded, and proof-visible.

#### [Task technical implementation]

This task must preserve and publish:

- grid/tile semantics,
- Manhattan movement rules,
- blocked-move behavior,
- occupancy constraints,
- local authoritative semantics,
- and concurrent support only where explicitly proven.

#### [Task acceptance criteria]

Movement is no longer just present in code.
It is officially supported under the correct original meaning.

---

### [ ] (checkbox) - [Phase Task 4] - Build benchmark and optimization foundations without changing gameplay meaning

#### [Task Description]

Measure and optimize only after preserved gameplay semantics exist.

#### [Task technical implementation]

This task must add:

- benchmark contract,
- movement-focused benchmark scenarios,
- resource-aware timing breakdowns,
- regression thresholds,
- and optimization passes that are constrained by parity/lifecycle/proof truth.

#### [Task acceptance criteria]

Performance work becomes real without becoming a semantic rewrite.

---

### [x] (checkbox) - [Phase Task 5] - Recover the original resource interaction core as the second official gameplay slice

#### [Task Description]

Implement the second supported slice along the original RPG-core path, not along generic interaction language.

#### [Task technical implementation]

This task must recover or complete:

- looting,
- harvesting,
- slot-pressure enforcement,
- weight-pressure enforcement,
- resource-node depletion/respawn,
- interaction interruption/abort semantics,
- and authoritative apply-path support for the slice.

This task should not claim closure until it covers the original post-movement resource loop well enough to be recognizable as the same game.

#### [Task acceptance criteria]

The second slice is an actual resource-interaction core, not a placeholder interaction subsystem.

---

### [x] (checkbox) - [Phase Task 6] - Consolidate the supported gameplay surface into one explicit truth package

#### [Task Description]

Turn the attached slices and supporting proofs into one precise supported-surface contract.

#### [Task technical implementation]

This task must publish and align:

- support matrix,
- benchmark matrix,
- certification matrix,
- release-proof expectations,
- known limitations,
- unsupported areas,
- and intentional divergences.

#### [Task acceptance criteria]

The project can state what Phase 4 actually delivered without inflating the support surface.

---

## [Phase out-of-scope boundaries]

Phase 4 must **not** silently widen into:

- broad combat systems,
- quest systems,
- rich AI behavior trees,
- large economy webs,
- universal performance claims,
- or broad concurrency support beyond what is explicitly proven.

If the team starts doing those things during this phase, it is avoiding closure work and creating future parity debt.

---

## [Shared Phase Exit Checklist]

- [x] Resource Truth Closure gate passed with tests
- [x] Substrate freeze passed with tests
- [x] Original `src/tests` oracle captured for official slices
- [x] Movement support boundary published
- [x] Resource interaction support boundary published
- [x] Divergence log updated
- [x] Benchmark scope published
- [x] Certification scope published
- [x] Release-proof scope updated
- [x] Known limitations recorded
