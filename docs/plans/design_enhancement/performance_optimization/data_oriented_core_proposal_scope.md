---
status: active
layer: architecture
authority: P2
audience: developer
tags: [performance, architecture, engine, determinism]
---

# Scope — Data-Oriented (ECS) Core Architecture Proposal

Date: 2026-10-02

## Status and boundary

The owner decided on 2026-10-02 that the ECS/data-oriented core is scoped now, as an architecture
proposal only, in parallel with the performance foundation (`performance_stack_survey.md`, "Owner
decisions"). This file is that scope: it fixes what the proposal must answer, which options it
compares, and what evidence it needs. It is not the proposal, it selects no design, and it
authorizes no code. Nothing here is implemented before the owner approves the finished proposal
and the roadmap's RPG-core stability entry gate has lifted.

This scope stands in for the M6-T05 "advanced architecture proposal" request, moved ahead of Gate B
as a document. Gate A and Gate B keep their roles for anything that is built.

## Why a proposal and not an optimization ticket

Measured on `origin/main` at `7dfd1349`:

- `src/` is 744 Python files and about 126,000 lines. `AuthoritativeState`, `StateUpdate`,
  `EntityUpdate`, and `EntityState` are four of the five most connected nodes in the code graph
  (1,759, 911, 648, and 409 edges).
- 124 source files read `state.entities` directly, and component access is written as attribute
  chains (`entity.strategic` 207 times, `entity.combat` 163 times, and so on).
- `docs/core/state.md` is authority **P0** and states an Immutability Law: every component and the
  `AuthoritativeState` container is a frozen dataclass, and a transition produces a new state
  object.

A data-oriented core changes how authoritative state is stored and iterated. That touches a P0
law and the most connected types in the engine, so it is an architecture change with a migration,
not a semantics-preserving accelerator that Gate A can select.

## What the engine already has

The current design is closer to ECS than its storage suggests, and the proposal should build on
that instead of replacing it:

- Entities are already composed of typed components: `EntityState` holds sixteen component
  objects (identity, attributes, combat, navigation, inventory, strategic, social, biological,
  lifecycle, and others), each a frozen, slotted dataclass.
- Systems already read a frozen snapshot and return typed `StateUpdate` proposals; only
  `ApplyPath.apply_generation()` commits. That is the ECS "systems read, commands write" model
  with a single commit point.
- `src/engine/phase_domain_permissions.py` already declares read/write/emit domains, at kernel
  phase granularity. The P1 sub-phase domain-contract epic extends it to each RESOLUTION phase.

What is missing is the storage and scheduling half: state is an object per entity in a Python
dict, every phase iterates Python objects, and RESOLUTION runs its 44 phase calls serially.

## The three layers the proposal must treat separately

An "ECS" bundles three things that can be adopted independently. The proposal evaluates each on
its own and says which combinations are coherent.

| Layer | Question | Current state |
|---|---|---|
| Storage | Is authoritative component data held in columnar or archetype tables instead of an object per entity? | Object per entity, frozen dataclasses |
| Scheduling | Do systems declare component read/write access, and does a scheduler order and parallelize them from those declarations? | Handwritten serial order; domain declarations at kernel-phase level only |
| Query API | Do systems ask for "all entities with components X and Y" instead of walking `state.entities`? | Direct dict iteration, plus derived indexes and `CandidateSelector` |

## Options the proposal compares

| Option | Summary | What it keeps | Main cost or risk |
|---|---|---|---|
| A. Derived column views only | Disposable Arrow or NumPy views built from the object state for hot loops (already an M5 candidate) | Everything; P0 law untouched | View construction cost every tick; ceiling is low |
| B. Access-declared scheduling over current storage | Finish sub-phase domain contracts, generate the phase order from declarations, parallelize provably independent phases | Storage and the Immutability Law | Needs the conflict, staging, and commit design the plan already demands for concurrent RESOLUTION |
| C. Columnar authoritative storage behind the existing facade | Components stored in per-archetype columns with double-buffered generations (read generation N, write N+1); `EntityState` becomes a typed view | The apply path, typed updates, single owner | Rewords the P0 Immutability Law from "frozen objects" to "immutable generations"; every direct reader must go through the facade |
| D. Native core | Option C's storage and option B's scheduler implemented in Rust (an existing ECS library or a purpose-built store) exposed through PyO3, with systems migrating from Python over time | Semantics and determinism contracts | Two-language engine; build, debugging, and agent-tooling cost; the boundary crossing cost must be measured |
| E. Full engine port | Rewrite the engine on a native ECS | Content and rules only | Abandons the certified Python reference; listed so that it is rejected explicitly, not by omission |

The planner's starting hypothesis, to be tested and not assumed: B, then C, then D, as a strangler
migration behind a stable facade, with the current object model kept as the reference path that
parity is checked against at each step.

## Questions the proposal must answer

1. **Immutability.** What replaces "frozen dataclasses" as the P0 guarantee, in words precise
   enough to test? How do read-only worker snapshots stay valid while generation N+1 is written?
2. **Determinism.** What is the canonical iteration order when storage order follows archetype
   moves instead of entity id? How are float reductions ordered? Does the canonical hash change,
   and if so under which versioned scheme (PERF-D5)?
3. **Single commit point.** Does `ApplyPath.apply_generation()` remain the only writer, and how
   do the 44 refinement phases map onto systems with declared access (PERF-D6)?
4. **Durable-state rules.** How does a typed, inspectable component schema registry satisfy the
   repository's durable-state rule (typed model, stable location, lifecycle, debug visibility,
   tests) for every component, including ones RPG-core adds later?
5. **Feature growth.** RPG-core is adding state and phases now. What does adding a component or a
   system cost under each option, compared with today?
6. **Reference path and parity.** What is the oracle at each migration step, and when may the
   object model be retired?
7. **Boundaries.** What crosses the Python/native boundary per tick under option D, and what does
   that cost at 1,000, 10,000, and 100,000 entities?
8. **Non-entity state.** Regions, resource nodes, buildings, terrain, groups, and item instances
   live beside entities in `AuthoritativeState`. Which become components, which stay resources?
9. **Checkpoint, replay, and API.** What happens to checkpoint format, replay, presenters, and the
   read-model cache?
10. **Scale target.** What entity count, tick rate, and hardware class is the design sized for?
    Without a stated product target, no option can be judged sufficient.

## Evidence the proposal needs, and when it can be gathered

| Evidence | Source | Available |
|---|---|---|
| Where tick time goes by phase and by work cardinality | M3 instrumentation, M4 baseline matrix | After the entry gate |
| How many entities reach each phase after readiness, LOD, and cadence gates | P1 roadmap item 2 | After the entry gate |
| Read/write domain of every RESOLUTION phase | PA-05A inventory script, sub-phase domain contracts | PA-05A can start now |
| Component access map: which systems read and write which components | Static analysis of `src/` (read-only tooling) | Can start now |
| Boundary-crossing and columnar-view prototype costs | A throwaway spike outside `src/`, under `experiments/` | Can start now, as a spike only |
| Product scale target | Owner | Needed before the proposal can conclude |

The proposal may be drafted before the timing evidence exists, but it cannot recommend an option
for approval without it.

## Out of scope for the proposal

- Any change to `src/`, to P0 or P1 documents, or to the certified reference path.
- Distributed or multi-writer simulation, CRDTs, eventual consistency, and client prediction.
- Aggregate or reduced-fidelity simulation of distant regions, which is a semantics change with
  its own proposal.
- Choosing a compiled kernel for the current engine; that remains a Gate A decision.

## Deliverables and sequence

1. Component access map and PA-05A phase inventory, as re-runnable read-only tooling.
2. A written comparison of options A–E against questions 1–10.
3. A spike report with measured boundary and view costs.
4. The proposal itself, with a recommended option, migration steps, reference-path and parity
   plan, rollback points, and the exact P0 and P1 wording changes it would need.
5. Owner review. Approval of the proposal authorizes ticket creation for its first step only.

## Sources

- `performance_stack_survey.md`, section C
- `performance_m6_gate_b_future_architecture_epic.md`, "Conditional advanced-proposal boundary"
- `../subphase_domain_contracts_epic.md`
- `../../../core/state.md`
- `src/core/state.py`, `src/engine/pipeline.py`, `src/engine/phase_domain_permissions.py`
