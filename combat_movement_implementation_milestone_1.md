[Milestone 1] - Core Rulebook and Engine-Time Refactor

[Milestone Description]
Milestone 1 is the foundation for the combat and movement overhaul. Its purpose is **not** to make combat smarter yet, and it is **not** to rebalance combat outcomes yet. Its purpose is to define one exact, deterministic, auditable contract for space, timing, and world progression so that all later combat, movement, AI, and balance work operates on one coherent rulebook.

This milestone must lock the simulation’s basic laws:

- what “distance” means,
- what “adjacent” means,
- whether a tile can hold more than one entity,
- how AoE legality works,
- when an entity is allowed to act,
- and whether the world continues progressing when no entity acts.

The current discussion and review already identified this as the highest-risk integrity layer. If this milestone is vague, every later milestone becomes patchwork.

[Milestone technical implementation]
Create one exact combat-movement rulebook contract and make the runtime obey it.

This milestone must implement these exact rules:

### Spatial rules

1. **Distance metric**
   - All movement distance, single-target attack range, and AoE radius calculations use **cardinal Manhattan distance**.
   - Manhattan distance is defined as `abs(dx) + abs(dy)`.
   - Diagonal positions are not treated as one-step adjacent.
   - If diagonal movement is currently impossible, this milestone must keep that behavior explicit rather than implicit.

2. **Adjacency**
   - Melee adjacency is orthogonal only.
   - A target is adjacent if and only if Manhattan distance is `1`.
   - No diagonal melee adjacency is allowed in this milestone.

3. **Tile occupancy**
   - One entity occupies one tile.
   - Occupied tiles are blocked for movement.
   - No ally pass-through is introduced in this milestone.
   - No tile stacking is introduced in this milestone.
   - This milestone may preserve goal-tile exceptions for pathing internals if already required by route solving, but movement execution must still respect one-entity-per-tile occupancy.

4. **AoE legality**
   - AoE skills use the exact rule:
     - chosen impact tile must be within attack range,
     - line of sight is checked to the impact tile,
     - affected entities are any entities within AoE radius of the impact tile using Manhattan distance.

   - A target may be affected beyond direct single-target range only if it lies inside the legal AoE radius from a legal impact center.
   - This milestone does not introduce per-tile LOS checking for every splash target.

5. **Spatial legality precedence**
   - Spatial legality must be evaluated before any combat resolution logic.
   - If a target or impact tile fails spatial legality, combat resolution must not proceed.

### Timing rules

6. **Entity action cadence**
   - Entity turns remain readiness-based.
   - An entity may only choose and execute an action when its next action time is due.
   - Milestone 1 does not change the speed formula itself. It only locks the turn model around readiness.

7. **World-time progression**
   - World-time must continue progressing even when no entity acts.
   - Passive systems must continue advancing on quiet ticks or quiet time windows.
   - Quiet ticks must not skip:
     - passive status progression,
     - recovery/decay processes,
     - lifecycle or world-time counters,
     - and any other time-driven state transitions already recognized as passive.

8. **Entity-turn vs world-time separation**
   - Entity decision/execution cadence must be separate from passive world progression.
   - A lack of proposals must not imply a lack of time progression.
   - This milestone must refactor the runtime loop so those two concepts are structurally separate.

### Runtime contract boundaries

9. **Non-goals of this milestone**
   - Do not add anti-stalemate logic here.
   - Do not add combat context modifiers here.
   - Do not add new kiting behavior here.
   - Do not add movement intentions here.
   - Do not rebalance speed or other attributes here.
   - Do not change AI tactical heuristics here.

10. **Clean-code boundary**

- Spatial rule evaluation, turn-readiness logic, and passive world progression must be separated into distinct responsibilities.
- Do not bury Manhattan checks, occupancy checks, and quiet-tick lifecycle progression as scattered implicit behavior.
- This milestone must make those rules centralized and inspectable.

[Milestone important notes]
The first trap in this milestone is trying to fix combat feel before locking the world laws. That is backwards. If you start with opportunity attacks, kiting changes, or congestion logic before distance, occupancy, AoE legality, and time progression are frozen, you will create behavior that depends on unstable foundations.

The second trap is treating readiness turns and world-time as the same thing. They are not the same thing. An entity not being ready to act does not mean the world stopped.

The third trap is hiding these rules in emergent behavior. This milestone must not rely on “the current code mostly behaves like this.” The rules must become explicit and testable.

The fourth trap is scope drift into balance. This milestone is not the place to decide whether speed is too strong or whether ranged should beat melee in a given scenario. This milestone only defines the laws under which those later questions can be answered truthfully.

[Milestone acceptance criteria]
At the end of Milestone 1, the codebase has:

- one exact spatial rule contract,
- one exact timing and lifecycle contract,
- one refactored runtime loop that separates world-time from entity turns,
- one deterministic set of rule-contract tests,
- and one exact documentation pack that states these rules without ambiguity.

No combat intelligence upgrade, anti-stalemate mechanic, or balance change is required for Milestone 1 completion.

## Task

[x] (checkbox) - [Task 1] - Define the combat-movement rulebook contract

[Task Description]
Create the exact design contract for spatial legality and timing semantics. This is the foundational modeling task for the overhaul. Without it, later milestones will drift into hidden assumptions and contradictory behavior.

[Task technical implementation]
Create one new rulebook reference document and one code-facing rule contract section that define exactly:

### Spatial contract

- Manhattan distance is the only metric for:
  - movement distance,
  - single-target attack range,
  - AoE radius.

- Orthogonal adjacency only.
- One entity per tile.
- No ally pass-through.
- AoE uses:
  - impact center in range,
  - LOS to center,
  - splash by Manhattan radius.

### Timing contract

- Entity turns are readiness-based.
- World-time always advances.
- Passive world progression is not gated by action proposals.

### Non-goals

- no combat-context logic,
- no anti-stalemate logic,
- no tactical AI improvements,
- no stat rebalance.

[Task possible affected files]

- `docs/combat/combat_movement_rulebook_m1.md`
- core runtime/engine loop module
- combat targeting / legality module
- movement / pathing legality module
- scheduler / turn cadence module

[Task important notes]
Do not write this as prose-only design fluff. The rulebook must be exact enough to generate code and tests from it.

Do not mix this contract with later milestone mechanics.

[Task check list]

- [x] Define Manhattan distance contract
- [x] Define orthogonal adjacency contract
- [x] Define one-unit-per-tile contract
- [x] Define no-pass-through contract
- [x] Define AoE impact/radius legality contract
- [x] Define readiness-turn contract
- [x] Define world-time progression contract
- [x] Define explicit non-goals
- [x] Keep the contract exact and minimal

[Task acceptance criteria]
The project has one exact combat-movement rulebook that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Implement exact spatial legality primitives

[Task Description]
Make the codebase obey the frozen spatial contract. This task translates the spatial rulebook into authoritative legality behavior.

[Task technical implementation]
Implement or centralize the exact spatial checks used by movement and attack systems:

1. Manhattan distance helper is the authoritative range metric for this milestone.
2. Adjacency helper returns true only for orthogonally adjacent tiles.
3. Occupied tiles are blocked for movement execution.
4. AoE legality checks:
   - impact tile within range,
   - LOS to impact tile,
   - splash radius applied outward by Manhattan distance.

5. Spatial legality must be checked before internal combat resolution begins.

Where existing code already does part of this, refactor toward one explicit contract rather than leaving multiple implicit versions.

[Task possible affected files]

- vector / distance helper module
- combat targeting / attack validation module
- AoE targeting module
- movement validation module
- pathfinding helper module

[Task important notes]
Do not add diagonal adjacency support.
Do not add partial occupancy semantics.
Do not add ally pass-through exceptions.

This task is not for combat balance. It is for legality consistency.

[Task check list]

- [x] Centralize Manhattan distance usage
- [x] Centralize orthogonal adjacency usage
- [x] Enforce occupancy on movement execution
- [x] Enforce AoE center legality
- [x] Enforce splash radius from impact center
- [x] Ensure combat resolution is gated by legality
- [x] Remove or isolate conflicting legacy checks

[Task acceptance criteria]
Spatial legality behavior is exact, centralized, and consistent with the Milestone 1 rulebook.

---

[x] (checkbox) - [Task 3] - Refactor the engine loop to separate world-time from entity action turns

[Task Description]
Repair the core lifecycle model so passive world progression no longer depends on whether any entity acted.

[Task technical implementation]
Refactor the runtime loop into two distinct layers:

1. **World-time progression**
   - advances every tick or time step,
   - updates passive time-driven systems,
   - continues even when no entity is ready.

2. **Entity action progression**
   - selects only entities whose action time is due,
   - executes their actions,
   - does not control whether passive time progression happens.

This task must ensure that quiet ticks still advance passive systems and that entity readiness remains the only gate for entity decisions.

[Task possible affected files]

- world loop / simulation loop module
- action scheduling module
- passive lifecycle / recovery module
- status progression / passive effect module

[Task important notes]
Do not solve this by forcing idle entities to emit fake actions.
Do not leave passive world progression hidden inside action-application code.

This refactor must make the separation structural.

[Task check list]

- [x] Separate world-time progression path
- [x] Separate entity-turn execution path
- [x] Ensure quiet ticks still progress passive systems
- [x] Preserve readiness-based entity turns
- [x] Remove proposal-gated passive progression where present
- [x] Keep deterministic processing order

[Task acceptance criteria]
The runtime loop structurally separates world-time from entity action turns, and passive progression no longer depends on whether proposals existed.

---

[x] (checkbox) - [Task 4] - Add rule-contract and lifecycle tests

[Task Description]
Lock the Milestone 1 contract with deterministic tests so later milestones cannot silently change the laws of space and time.

[Task technical implementation]
Add exact tests for the rulebook.

### Spatial contract tests

Add test coverage for:

- Manhattan distance examples,
- orthogonal adjacency examples,
- occupied-tile movement blocking,
- no diagonal melee adjacency,
- AoE center-in-range legality,
- AoE splash by Manhattan radius,
- LOS to impact center.

### Timing contract tests

Add test coverage for:

- entity acts only when ready,
- quiet ticks still advance world-time,
- passive effects advance without proposals,
- repeated identical input produces deterministic tick progression.

### Suggested test groups

- `tests/combat/test_combat_movement_rulebook.py`
- `tests/engine/test_world_time_progression.py`
- `tests/engine/test_readiness_turns.py`

[Task possible affected files]

- new combat rulebook test modules
- new engine lifecycle test modules

[Task important notes]
These are contract tests, not tuning tests.
Do not use fuzzy expectations where exact semantics are known.

Do not add large scenario-balance tests in this milestone.

[Task check list]

- [x] Add Manhattan distance tests
- [x] Add adjacency tests
- [x] Add occupancy tests
- [x] Add AoE legality tests
- [x] Add readiness-turn tests
- [x] Add quiet-tick world progression tests
- [x] Add passive progression tests
- [x] Add deterministic lifecycle tests

[Task acceptance criteria]
The core laws of combat and movement are pinned by deterministic rule-contract tests.

---

[x] (checkbox) - [Task 5] - Add exact Milestone 1 documentation pack

[Task Description]
Document the complete Milestone 1 contract so later milestones cannot reinterpret it informally.

[Task technical implementation]
Create:

- `docs/combat/combat_movement_rulebook_m1.md`
- `docs/combat/combat_movement_m1_test_matrix.md`

`combat_movement_rulebook_m1.md` must contain these exact sections:

- Purpose
- Spatial rules
- Timing rules
- Distance and adjacency semantics
- Occupancy semantics
- AoE legality semantics
- World-time versus entity-turn semantics
- Non-goals
- Determinism rules

`combat_movement_m1_test_matrix.md` must contain these exact sections:

- Distance tests
- Adjacency tests
- Occupancy tests
- AoE legality tests
- Readiness-turn tests
- Quiet-tick lifecycle tests
- Determinism tests

For every test group, document:

- test name or test group name,
- input condition,
- exact expected rule,
- regression caught.

[Task possible affected files]

- `docs/combat/combat_movement_rulebook_m1.md`
- `docs/combat/combat_movement_m1_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.
Do not defer it.

[Task check list]

- [x] Document exact spatial rules
- [x] Document exact timing rules
- [x] Document exact non-goals
- [x] Document determinism expectations
- [x] Document rule-contract tests
- [x] Document lifecycle tests
- [x] Document regression purpose of each test group

[Task acceptance criteria]
Milestone 1 has a complete exact rulebook document and exact test-matrix document that match the implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of combat and movement as things to “improve” first. In Milestone 1, they must first become lawful.

What actions must be taken immediately
Freeze the rulebook, centralize spatial legality, separate world-time from entity turns, and pin the result with deterministic contract tests.

What must stop or be eliminated
Stop relying on hidden emergent behavior for distance, occupancy, AoE legality, or lifecycle progression. Stop proposal-gating passive world-time.

The consequences and opportunity cost if this fails
Every later combat and movement milestone will be built on contradictory laws, and you will waste time tuning broken behavior instead of fixing the foundation.

---

### Implementation Comments (Audit 2026-04-17)

- **Rulebook**: Canonical rules established in `docs/combat/combat_movement_rulebook_m1.md`.
- **LegalityService**: Centralized authoritative host for Manhattan distance (`check_range`), orthogonal adjacency (`is_orthogonal_adjacent`), and occupancy (`check_occupancy`) logic in `src/core/logic/legality_service.py`.
- **ActionSystem**: Enforces legality re-validation in `apply_action_state_transitions` to ensure all AI-proposed actions obey the rulebook before state mutation.
- **Engine Loop**: Structural separation accomplished in `src/engine/phases/presystems.py` (passive world-time progression) and `src/engine/phases/scheduling.py` (readiness-based turn identification).
- **Tests**: Core laws pinned in `tests/combat/test_combat_movement_rulebook.py` and `tests/combat/test_world_time_progression.py`.

