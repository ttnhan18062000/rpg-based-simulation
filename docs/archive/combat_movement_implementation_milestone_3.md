---
status: archive
authority: P2
audience: historical
layer: combat
original_date: unknown
---

[Milestone 3] - Movement Model and Congestion Control

[Milestone Description]
Milestone 3 builds the movement model that entities will actually live inside. Its purpose is **not** to improve combat intelligence yet, and it is **not** to rebalance combat outcomes yet. Its purpose is to turn movement from raw path execution into a layered, intention-driven, congestion-aware system that remains fully compatible with the Milestone 1 spatial rulebook and the Milestone 2 combat interaction model.

This milestone exists because the current movement problem is no longer just “find a path.” The real gap is embodied movement quality:

- why an entity is moving,
- how long it stays committed to that movement,
- how it behaves when allies block its lane,
- how it reacts to short-range obstacles without becoming jittery,
- and how one-unit-per-tile occupancy remains viable without introducing ally pass-through.

The review was right to keep this as one movement-system milestone instead of scattering it into separate “reroute,” “yield,” “anti-oscillation,” and “retreat movement” fixes. These are not isolated features. They are one movement model.

[Milestone technical implementation]
Create one exact movement contract and make all movement pass through it before tactical AI sophistication is expanded.

This milestone must implement these exact concerns as one system:

### Movement-layer rules

1. **Movement intention**
   - Every non-trivial movement decision must have an explicit intention class.
   - At minimum, the system must support exact intention categories for:
     - pursue,
     - retreat,
     - hold,
     - reposition,
     - intercept,
     - guard,
     - regroup.

   - Movement intention must be explicit runtime state, not inferred ad hoc from the current target alone.

2. **Route-level planning**
   - Movement must support a route-level plan toward an intended destination or tactical shape.
   - Route solving must remain compatible with:
     - Manhattan distance,
     - one-unit-per-tile occupancy,
     - no ally pass-through,
     - and Milestone 2 engagement/disengagement semantics.

   - Route planning must not be recomputed every action without cause.

3. **Local step selection**
   - Movement must support a local step-decision layer that can respond to:
     - temporarily blocked tiles,
     - nearby allies,
     - short-horizon obstacle changes,
     - and immediate congestion.

   - Local step choice must remain subordinate to the route-level intention, not replace it.

4. **Route commitment and hysteresis**
   - Entities must not constantly abandon and rebuild routes for tiny differences.
   - Route commitment must exist so movement looks stable rather than jitter-driven.
   - Replanning must require a meaningful trigger such as:
     - invalidated route,
     - blocked path beyond tolerance,
     - changed target or intention,
     - or a stronger local danger condition if already supported.

5. **Congestion control**
   - One-unit-per-tile remains the rule.
   - No ally pass-through is introduced in this milestone.
   - Congestion must instead be resolved through:
     - waiting,
     - yielding,
     - sidestepping,
     - local rerouting,
     - or another exact rulebook-approved movement response.

   - Congestion handling must work for common cases such as:
     - ally blocking a corridor,
     - two allies trying to use the same next tile,
     - and one ally preventing another from progressing toward a still-valid goal.

6. **Oscillation control**
   - The movement model must explicitly prevent common no-progress movement loops, including:
     - left-right or up-down step oscillation,
     - repeated reroute flip-flopping,
     - repeated wait-move-wait jitter without progress,
     - and repeated micro-retreat / micro-advance around the same position threshold outside Milestone 2 combat loops.

   - This must be handled as a movement-system rule, not only as a tactical AI preference.

### Runtime boundaries

7. **What this milestone may change**
   - movement planning structure,
   - local step execution behavior,
   - congestion handling,
   - route persistence,
   - oscillation prevention,
   - and movement intention state.

8. **What this milestone must not do**
   - no ally pass-through,
   - no global stat rebalance,
   - no higher-order tactical AI cover/chokepoint heuristics yet,
   - no many-v-many battle tuning yet,
   - no final combat balance tuning yet.

9. **Clean-code boundary**
   - Spatial legality from Milestone 1 remains separate.
   - Combat interaction from Milestone 2 remains separate.
   - Route planning remains separate from local step choice.
   - Movement intention remains separate from tactical scoring.
   - Congestion control remains part of movement execution, not hidden inside pathfinding alone.

[Milestone important notes]
The first trap in this milestone is trying to solve congestion by weakening the occupancy rule. Do not do that. The accepted design is still one-unit-per-tile and no ally pass-through. This milestone must make that viable through smarter movement, not by erasing the rule.

The second trap is pretending pathfinding is enough. Pathfinding answers how to get somewhere in static terms. It does not answer why the entity is moving, when it should wait, when it should sidestep, or when it should keep its current route despite temporary blockage.

The third trap is letting movement intention become tactical AI bloat. This milestone must add the movement primitives and contracts, not a giant world-brain.

The fourth trap is overreactive replanning. If every small local change causes a total route rebuild, movement will look fake and performance will degrade.

[Milestone acceptance criteria]
At the end of Milestone 3, the codebase has:

- one exact movement intention contract,
- one explicit route-planning versus local-step model,
- one explicit congestion-handling framework compatible with hard occupancy,
- one explicit anti-oscillation framework for movement,
- one deterministic set of movement-model tests,
- and one exact documentation pack describing the movement semantics.

No ally pass-through, tactical cover intelligence, or stat rebalance is required for Milestone 3 completion.

## Task

[x] (checkbox) - [Task 1] - Define the movement intention and execution contract

[Task Description]
Create the exact rule contract for movement semantics. This is the foundational modeling task for Milestone 3. Without it, route planning, rerouting, congestion handling, and anti-oscillation behavior will remain implicit and contradictory.

[Task technical implementation]
Create one movement reference document and one code-facing movement contract that define exactly:

### Movement contract

- what movement intention categories exist,
- what route-level planning is responsible for,
- what local step selection is responsible for,
- when replanning is allowed,
- what class of congestion responses is legal,
- and what class of oscillation-prevention response is legal.

### Behavioral boundaries

- movement occurs after Phase 1 legality rules are satisfied,
- movement cooperates with Milestone 2 combat interaction,
- movement intention is distinct from tactical combat scoring,
- congestion handling is distinct from changing the occupancy rule.

### Non-goals

- no ally pass-through,
- no cover/chokepoint tactical behavior yet,
- no speed rebalance,
- no large-scale group tactic layer yet.

[Task possible affected files]

- `docs/combat/movement_rulebook_m3.md`
- movement planning module
- movement execution / step-selection module
- pathfinding integration layer
- transient movement state / navigation state module

[Task important notes]
Do not write this as vague movement prose. The contract must be exact enough to derive tests and implementation boundaries from it.

Do not let congestion handling become an undocumented pile of exceptions.

[Task check list]

- [x] Define movement intention categories
- [x] Define route-planning responsibility
- [x] Define local-step responsibility
- [x] Define replanning triggers
- [x] Define legal congestion responses
- [x] Define legal anti-oscillation responses
- [x] Define interaction boundaries
- [x] Define explicit non-goals
- [x] Keep the contract exact and minimal

[Task acceptance criteria]
The project has one exact movement contract that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Implement explicit movement intention state

[Task Description]
Make movement purpose explicit and authoritative. This task translates the intention portion of the rulebook into runtime truth.

[Task technical implementation]
Implement or centralize the exact movement intention state model for at least:

- pursue,
- retreat,
- hold,
- reposition,
- intercept,
- guard,
- regroup.

This task must ensure:

1. movement intention is stored as explicit transient state,
2. route generation can consume that intention,
3. local step selection can consume that intention,
4. and intention changes only occur when the rulebook says they may occur.

The intention model must be compatible with:

- pursuit and disengagement semantics from Milestone 2,
- one-unit-per-tile movement,
- and route commitment.

[Task possible affected files]

- movement / navigation state module
- movement planning module
- AI-to-movement bridge layer
- transient entity state / navigation aspect

[Task important notes]
Do not implement intention as a loose string scattered across systems.
Do not let “current target exists” substitute for actual movement intention.

The whole point is to make movement purpose explicit and auditable.

[Task check list]

- [x] Add explicit movement intention state
- [x] Add intention persistence rules
- [x] Add intention change triggers
- [x] Connect intention to planning
- [x] Connect intention to local step selection
- [x] Remove or isolate conflicting legacy assumptions

[Task acceptance criteria]
Movement intention is explicit, deterministic runtime state rather than emergent side effect.

---

[x] (checkbox) - [Task 3] - Implement route-level planning and local-step separation

[Task Description]
Separate “where the entity is trying to go” from “which tile it steps to right now.” This is the structural core of believable movement.

[Task technical implementation]
Implement one exact two-layer movement execution model:

1. **Route-level planning**
   - derives a route or route target from current intention,
   - persists that route long enough to support commitment,
   - only replans when a rulebook-approved trigger occurs.

2. **Local-step selection**
   - chooses the next step along or near the route,
   - may react to temporary blockages or local congestion,
   - must not replace route-level purpose.

This task must also define exact replanning triggers, such as:

- route invalidated,
- next segment blocked beyond tolerance,
- intention changed,
- target changed,
- path no longer legal.

[Task possible affected files]

- pathfinding module
- movement planning module
- movement execution / stepping module
- route cache or navigation memory module

[Task important notes]
Do not recompute the whole route every action by default.
Do not let local stepping silently become the real planner.

The purpose of this task is structural separation.

[Task check list]

- [x] Add route-level plan structure
- [x] Add local-step execution structure
- [x] Add exact replanning triggers
- [x] Add route persistence rules
- [x] Keep route and step logic separate
- [x] Remove or isolate pathfinding-overreach where present

[Task acceptance criteria]
Movement uses distinct route-planning and step-execution layers, with explicit replanning rules.

---

[x] (checkbox) - [Task 4] - Implement congestion handling without ally pass-through

[Task Description]
Create one general framework for resolving no-progress movement caused by occupied lanes while preserving hard occupancy.

[Task technical implementation]
Implement one explicit congestion-handling framework that supports at least these response classes:

1. **Wait**
   - tolerate temporary blockage when waiting is the correct low-cost choice.

2. **Yield**
   - allow an entity to defer local progression when another entity has the stronger local claim or clearer route need.

3. **Sidestep**
   - allow small local repositioning to free a path or avoid mutual blockage.

4. **Local reroute**
   - allow a short-horizon alternate step or route adjustment around an occupied lane.

This framework must cover at least these problem classes:

- ally blocks corridor,
- two allies converge on same next tile,
- ally blocks still-valid pursuit route,
- ally blocks retreat lane,
- repeated blocked-step no-progress loop.

This milestone must preserve:

- one entity per tile,
- blocked occupied-tile execution,
- and no ally pass-through.

[Task possible affected files]

- movement execution / collision-resolution layer
- local step-selection module
- route planning integration layer
- transient local movement memory / recent-step state

[Task important notes]
Do not introduce ally pass-through as a shortcut.
Do not solve congestion purely by endless rerouting.

This needs one coherent framework, not isolated if-statements.

[Task check list]

- [x] Add wait behavior
- [x] Add yield behavior
- [x] Add sidestep behavior
- [x] Add local reroute behavior
- [x] Handle corridor blockage
- [x] Handle same-next-tile conflicts
- [x] Handle blocked pursuit and retreat lanes
- [x] Keep the response deterministic
- [x] Preserve hard occupancy

[Task acceptance criteria]
Common ally-block and lane-block movement failures are resolved through one explicit, deterministic congestion framework without ally pass-through.

---

[x] (checkbox) - [Task 5] - Implement route commitment and anti-oscillation behavior

[Task Description]
Prevent movement from becoming jittery, flip-floppy, or locally rational but globally stupid.

[Task technical implementation]
Implement one explicit route-commitment and anti-oscillation framework that covers at least:

1. **Route commitment**
   - a route is retained unless a meaningful break trigger occurs,
   - small local changes do not cause full route abandonment.

2. **Oscillation prevention**
   - detect and suppress repeated local back-and-forth patterns,
   - suppress repeated reroute flipping,
   - suppress repeated wait-move-wait jitter without progress,
   - suppress repeated threshold dancing outside Milestone 2 combat-loop handling.

3. **Progress criteria**
   - define what counts as genuine forward progress for movement,
   - define what counts as repeated no-progress motion.

This task does **not** require final tuning of every threshold, but it must implement the system shape and deterministic behavior.

[Task possible affected files]

- navigation memory / recent-step history module
- movement execution module
- route planning module
- local conflict / congestion layer

[Task important notes]
Do not try to fix oscillation by making everything sticky forever.
Do not confuse healthy route commitment with refusal to adapt.

The goal is stable movement, not stubborn stupidity.

[Task check list]

- [x] Add route-commitment rules
- [x] Add progress vs no-progress criteria
- [x] Detect local back-and-forth oscillation
- [x] Detect reroute flip-flopping
- [x] Detect repeated jitter without progress
- [x] Keep the response deterministic
- [x] Keep commitment and adaptation balanced

[Task acceptance criteria]
Movement is stable rather than jitter-driven, and common no-progress oscillation patterns are explicitly suppressed.

---

[x] (checkbox) - [Task 6] - Add movement-model and congestion tests

[Task Description]
Lock the Milestone 3 contract with deterministic tests so later tactical AI and balance work cannot silently break the movement model.

[Task technical implementation]
Add exact tests for the movement layer.

### Movement contract tests

Add test coverage for:

- movement intention persistence,
- intention change triggers,
- route planning vs local stepping separation,
- replanning trigger behavior,
- route commitment behavior.

### Congestion tests

Add test coverage for:

- ally blocks corridor,
- two allies target same next tile,
- blocked pursuit lane,
- blocked retreat lane,
- deterministic wait / yield / sidestep resolution.

### Anti-oscillation tests

Add test coverage for:

- repeated local back-and-forth,
- repeated reroute flip-flop,
- repeated blocked-step jitter,
- stable progress under temporary blockage.

### Suggested test groups

- `tests/movement/test_movement_intention_contract.py`
- `tests/movement/test_congestion_control.py`
- `tests/movement/test_route_commitment_and_oscillation.py`

These tests should assert:

- movement semantics,
- stability,
- deterministic congestion handling,
- and no-progress suppression,
  not final combat balance.

[Task possible affected files]

- new movement contract test modules
- new congestion test modules
- new anti-oscillation test modules

[Task important notes]
Do not jump to giant many-v-many battlefield tests yet.
Do not use balance results as substitutes for movement contract results.

These are contract tests for movement-system semantics.

[Task check list]

- [x] Add movement intention tests
- [x] Add route/step separation tests
- [x] Add replanning-trigger tests
- [x] Add congestion tests
- [x] Add deterministic wait/yield/sidestep tests
- [x] Add anti-oscillation tests
- [x] Add deterministic movement progression tests

[Task acceptance criteria]
The movement model is pinned by deterministic contract tests, congestion tests, and anti-oscillation tests.

---

[x] (checkbox) - [Task 7] - Add exact Milestone 3 documentation pack

[Task Description]
Document the complete Milestone 3 contract so later tactical AI and balance milestones cannot reinterpret movement semantics informally.

[Task technical implementation]
Create:

- `docs/combat/movement_rulebook_m3.md`
- `docs/combat/movement_m3_test_matrix.md`

`movement_rulebook_m3.md` must contain these exact sections:

- Purpose
- Movement-layer boundaries
- Movement intention semantics
- Route-planning semantics
- Local-step semantics
- Replanning trigger semantics
- Congestion-response semantics
- Route-commitment semantics
- Anti-oscillation semantics
- Non-goals
- Determinism rules

`movement_m3_test_matrix.md` must contain these exact sections:

- Intention tests
- Route/step separation tests
- Replanning trigger tests
- Congestion tests
- Wait / yield / sidestep tests
- Anti-oscillation tests
- Determinism tests

For every test group, document:

- test name or group name,
- input condition,
- expected movement rule,
- regression caught.

[Task possible affected files]

- `docs/combat/movement_rulebook_m3.md`
- `docs/combat/movement_m3_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.
Do not defer it.

This milestone exists to stop movement semantics from living only in code and memory.

[Task check list]

- [x] Document exact movement rules
- [x] Document congestion response classes
- [x] Document anti-oscillation semantics
- [x] Document exact non-goals
- [x] Document determinism expectations
- [x] Document movement tests
- [x] Document regression purpose of each test group

[Task acceptance criteria]
Milestone 3 has a complete exact movement-rulebook document and exact test-matrix document that match the implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of movement as “pathfinding plus a few fixes.” In Milestone 3, movement becomes a full runtime model with intention, commitment, congestion control, and anti-oscillation behavior.

What actions must be taken immediately
Freeze the movement contract, implement explicit intention state, separate route planning from local stepping, add congestion handling without pass-through, add route commitment and anti-oscillation logic, and pin everything with deterministic contract tests.

What must stop or be eliminated
Stop solving blocked movement with isolated hacks. Stop relying on full reroute spam. Stop treating hard occupancy as the problem instead of making movement smart enough to live with it.

The consequences and opportunity cost if this fails
Milestone 4 and later will try to build tactical AI on top of brittle, jittery, congestion-prone movement, and the combat overhaul will still feel fake even if the combat rules themselves improve.

---

### Implementation Comments (Audit 2026-04-17)

- **MovementModel**: stateless service in `src/core/logic/movement_model.py` coordinating route planning and local stepping.
- **Intentions**: `MovementIntention` enum defines the "why" of movement. It is persisted in `entity.mind.navigation.intention`.
- **Two-Layer Planning**: `plan_route` generates the high-level path (cached in entity navigation), while `select_step` chooses the immediate tile based on local congestion.
- **Congestion Control**: `select_step` implements `WAIT`, `YIELD`, and `SIDESTEP` responses to occupied paths, maintaining the Milestone 1 "one-person-per-tile" rule without ally pass-through.
- **Persistence**: `blocked_ticks` and `cached_path` prevent oscillation and high-frequency replanning ripples.
- **Tests**: Verified in `tests/movement/test_congestion_control.py` and `tests/movement/test_movement_intentions.py`.

