---
status: archive
authority: P2
audience: historical
layer: combat
original_date: unknown
---

[Milestone 4] - Tactical AI Behavior

[Milestone Description]
Milestone 4 teaches entities to use the combat and movement systems deliberately. Its purpose is **not** to change the laws of space or time anymore, and it is **not** to do full combat balance tuning yet. Its purpose is to make entities behave believably in common tactical situations by consuming:

- the Phase 1 spatial and timing rulebook,
- the Milestone 2 combat interaction model,
- and the Milestone 3 movement model.

This milestone exists because a correct combat engine and a correct movement engine still do not guarantee believable behavior. The remaining gap is tactical use:

- when to take a safe shot,
- when to keep distance,
- when to retreat,
- when to hold,
- when to use a chokepoint,
- when to commit,
- and when not to throw away position.

The corrected high-level plan explicitly placed this milestone **after** combat interaction and movement semantics, because tactical AI should consume stable primitives rather than invent behavior around unstable ones.

[Milestone technical implementation]
Create one exact tactical-behavior contract and make AI combat and movement choice consume it consistently.

This milestone must implement these exact concerns as one system:

### Tactical-behavior rules

1. **Safe-shot behavior**
   - Ranged-capable entities must prefer legal attacks that preserve better immediate survival conditions.
   - “Safe shot” must be an explicit tactical concept rather than an accidental side effect of target order.
   - Safe-shot reasoning may consider:
     - maintained spacing,
     - reduced immediate threat exposure,
     - preserved retreat lane,
     - or improved defensive geometry if already visible to the movement layer.

2. **Distance management**
   - Tactical behavior must explicitly differentiate:
     - close distance,
     - maintain distance,
     - widen distance,
     - and hold current distance.

   - Ranged entities must not reduce to binary “attack or flee.”
   - Melee entities must not reduce to binary “charge forever.”

3. **Retreat behavior**
   - Retreat must become a first-class tactical choice.
   - Retreat must not be equivalent to panic-only behavior.
   - Tactical retreat may be chosen because of:
     - low current survivability,
     - positional disadvantage,
     - bad engagement state,
     - or inability to make useful progress in current contact.

4. **Position-value behavior**
   - Tactical behavior must be able to distinguish better versus worse local positions.
   - At minimum, the system must support explicit tactical preference for:
     - preserving ranged spacing,
     - not throwing away chokepoints,
     - not stepping into obviously bad contact,
     - and not abandoning a currently good local position without reason.

5. **Commitment versus disengagement**
   - Tactical AI must consume the Milestone 2 engagement/disengagement rules intentionally.
   - It must not disengage casually into punishment.
   - It must not stay committed forever when the current fight geometry is losing.

6. **Role-sensitive tactical use**
   - Tactical behavior must differ by combat role or combat capability, not only by current target.
   - At minimum, the system must support differentiated behavior for:
     - melee-biased entities,
     - ranged-biased entities,
     - entities with usable AoE pressure,
     - and entities with low-confidence or retreat-biased states.

7. **Small-group tactical coordination**
   - This milestone may introduce light tactical coordination for common cases.
   - At minimum, entities must not constantly undermine each other in obvious ways, such as:
     - ranged units collapsing spacing without cause,
     - multiple allies discarding a chokepoint at once,
     - or group members repeatedly taking equivalent bad lanes when a better local option exists.

   - This is **not** full formation AI yet.

### Runtime boundaries

8. **What this milestone may change**
   - tactical scoring / tactical preference logic,
   - target and position evaluation,
   - retreat threshold behavior,
   - ranged skirmish behavior,
   - basic local role-sensitive coordination.

9. **What this milestone must not do**
   - no changes to Phase 1 rules,
   - no changes to Milestone 2 interaction semantics,
   - no changes to Milestone 3 movement legality or congestion laws,
   - no broad stat rebalance,
   - no large-scale formation system,
   - no full many-v-many army doctrine layer yet.

10. **Clean-code boundary**

- Tactical AI remains separate from:
  - spatial legality,
  - combat interaction semantics,
  - movement execution semantics,
  - and final balance tuning.

- Tactical AI should select among valid combat and movement primitives. It must not secretly redefine them.

[Milestone important notes]
The first trap in this milestone is pushing tactical behavior down into movement or combat primitives. Do not do that. Movement and combat already define what is legal and how interaction works. Tactical AI is responsible for choosing among those options.

The second trap is trying to build full strategic intelligence here. This milestone is about short-horizon tactical use, not long-horizon planning.

The third trap is binary behavior. “Attack if possible, else run” and “charge until dead” are exactly the patterns this milestone exists to replace.

The fourth trap is over-coordination. This milestone should improve common small-group tactical coherence without trying to implement a full doctrine, formation, or commander system.

[Milestone acceptance criteria]
At the end of Milestone 4, the codebase has:

- one exact tactical-behavior contract,
- one explicit safe-shot and distance-management model,
- one explicit tactical retreat model,
- one explicit role-sensitive combat-behavior model,
- one deterministic set of tactical scenario tests,
- and one exact documentation pack describing tactical behavior semantics.

No full balance-tuning pass, large-scale formation AI, or stat ownership rebalance is required for Milestone 4 completion.

## Task

[x] (checkbox) - [Task 1] - Define the tactical-behavior contract

[Task Description]
Create the exact rule contract for tactical combat and combat-movement behavior. This is the foundational modeling task for Milestone 4. Without it, safe-shot logic, retreat logic, ranged spacing, and melee commitment will remain implicit and contradictory.

[Task technical implementation]
Create one tactical behavior reference document and one code-facing tactical contract that define exactly:

### Tactical contract

- what counts as a safe shot,
- what tactical distance-management modes exist,
- what counts as tactical retreat,
- what local position-value signals are allowed,
- how commitment and disengagement are tactically judged,
- what minimum role-sensitive behavior classes exist,
- and what level of small-group coordination is in scope.

### Behavioral boundaries

- tactical AI consumes legal options from prior milestones,
- tactical AI does not redefine legality or interaction semantics,
- tactical AI is distinct from long-horizon strategic behavior,
- tactical AI is distinct from final balance tuning.

### Non-goals

- no full formation system,
- no large-scale doctrine system,
- no stat rebalance,
- no many-v-many macro-coordination layer.

[Task possible affected files]

- `docs/combat/tactical_behavior_rulebook_m4.md`
- tactical AI evaluation module
- combat choice / target evaluation module
- movement-intention selection bridge layer
- role classification / tactical profile module

[Task important notes]
Do not write this as vague “fight smarter” prose. The contract must be exact enough to derive tests and implementation boundaries from it.

Do not let role behavior become undocumented magic.

[Task check list]

- [x] Define safe-shot semantics
- [x] Define distance-management modes
- [x] Define tactical retreat semantics
- [x] Define local position-value semantics
- [x] Define commitment/disengagement tactical use
- [x] Define minimum role-sensitive behavior classes
- [x] Define small-group coordination scope
- [x] Define explicit non-goals
- [x] Keep the contract exact and minimal

[Task acceptance criteria]
The project has one exact tactical-behavior contract that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Implement safe-shot and distance-management behavior

[Task Description]
Teach entities to make better short-horizon ranged and melee spacing decisions. This task translates the core tactical-use portion of the rulebook into runtime behavior.

[Task technical implementation]
Implement or centralize tactical logic for:

1. **Safe-shot evaluation**
   - evaluate legal attacks not only by damage opportunity,
   - but also by immediate tactical safety and follow-up viability.

2. **Distance-management modes**
   - support explicit tactical choice among:
     - close,
     - maintain,
     - widen,
     - hold.

3. **Ranged spacing**
   - ranged-capable entities must prefer maintaining workable distance rather than collapsing into contact unnecessarily.

4. **Melee pressure**
   - melee-capable entities must prefer closing and sustaining useful contact rather than blindly resetting pursuit every time range changes.

This task must consume:

- Milestone 2 combat interaction state,
- Milestone 3 movement intention and route-step model,
- and current combat role/capability state.

[Task possible affected files]

- tactical AI scoring / evaluation module
- target and position evaluation module
- ranged combat tactical module
- melee tactical module
- AI-to-movement intention bridge layer

[Task important notes]
Do not hardcode this into one ranged-only special case.
Do not reduce distance management to a single scalar threshold.

This task is about tactical use of space, not raw damage optimization.

[Task check list]

- [x] Add safe-shot evaluation
- [x] Add distance-management modes
- [x] Add ranged spacing behavior
- [x] Add melee pressure behavior
- [x] Consume interaction and movement state cleanly
- [x] Remove or isolate binary legacy logic where present

[Task acceptance criteria]
Entities can deliberately manage range and choose safer attacks instead of relying on accidental or binary behavior.

---

[x] (checkbox) - [Task 3] - Implement tactical retreat and commitment behavior

[Task Description]
Make retreat and continued engagement deliberate tactical choices rather than crude panic switches or endless stubborn contact.

[Task technical implementation]
Implement one explicit tactical retreat model that supports:

1. **Retreat triggers**
   - low survivability,
   - poor local geometry,
   - bad engagement state,
   - no useful near-term progress,
   - or other exact rulebook-approved tactical failure conditions.

2. **Retreat behavior**
   - retreat must choose valid movement intentions and legal movement responses,
   - not just arbitrary distance increase.

3. **Commitment retention**
   - entities must remain committed when the current engagement is still tactically sound,
   - and must not abandon good local positions without reason.

4. **Disengagement awareness**
   - retreat and disengagement must consume Milestone 2 consequence semantics intentionally,
   - rather than pretending disengage cost does not exist.

[Task possible affected files]

- tactical retreat / survival evaluation module
- engagement-value / commitment evaluation module
- AI-to-combat interaction bridge layer
- AI-to-movement intention bridge layer

[Task important notes]
Do not make retreat equivalent to “HP below X means run.”
Do not make commitment equivalent to “stay until dead.”

The goal is tactical judgment, not panic scripting.

[Task check list]

- [x] Add retreat trigger logic
- [x] Add tactical retreat behavior
- [x] Add commitment-retention logic
- [x] Add disengagement-aware retreat behavior
- [x] Consume combat interaction state correctly
- [x] Remove or isolate crude panic-only legacy behavior

[Task acceptance criteria]
Entities can retreat or remain committed for tactical reasons instead of only because of binary HP-state logic.

---

[x] (checkbox) - [Task 4] - Implement role-sensitive tactical behavior

[Task Description]
Different entity combat roles must produce different tactical use of the same combat and movement primitives. This task makes those differences explicit.

[Task technical implementation]
Implement a minimum role-sensitive tactical layer for at least:

- melee-biased entities,
- ranged-biased entities,
- AoE-capable entities,
- low-confidence / retreat-biased entities.

This task must ensure:

1. role differences are reflected in tactical selection,
2. roles use movement and combat primitives differently,
3. and entities with different combat capabilities stop collapsing into one generic behavior pattern.

AoE-capable behavior in this milestone is limited to tactical use of already-legal AoE opportunities. It is **not** a full large-battle blast-optimization system yet.

[Task possible affected files]

- combat role classification / tactical profile module
- tactical evaluation module
- AoE tactical selection module
- retreat-bias / confidence handling module

[Task important notes]
Do not hardcode class names all over the system.
Use role/capability categories that tactical logic can consume cleanly.

Do not let role-sensitive behavior become hidden scattered conditionals.

[Task check list]

- [x] Define or centralize tactical role categories
- [x] Add melee-biased behavior profile
- [x] Add ranged-biased behavior profile
- [x] Add AoE-capable tactical behavior
- [x] Add low-confidence / retreat-biased behavior
- [x] Keep role behavior explicit and auditable

[Task acceptance criteria]
Different combat-capable entities use the same system differently in deterministic, role-sensitive ways.

---

[x] (checkbox) - [Task 5] - Implement light small-group tactical coordination

[Task Description]
Improve common small-group behavior so allies stop undermining each other in obvious ways, without jumping to a full formation or doctrine system.

[Task technical implementation]
Implement one limited coordination layer that supports at least:

1. **Spacing preservation**
   - ranged-capable allies do not collapse spacing without reason.

2. **Local lane discipline**
   - allies do not repeatedly choose equivalent bad local lanes when a better local lane is available.

3. **Position preservation**
   - groups do not casually throw away useful local structures such as a held choke or a defensible contact line.

4. **Non-destructive cooperation**
   - allied tactical selection should reduce obvious self-sabotage in short-horizon local decisions.

This milestone does **not** require:

- formations,
- commander roles,
- doctrine trees,
- or large-scale coordinated maneuvers.

[Task possible affected files]

- small-group tactical coordination module
- allied local-position evaluation module
- movement-intention arbitration / coordination layer
- target/position group evaluation module

[Task important notes]
Do not turn this into a full squad AI system.
This milestone only fixes the most obvious local group self-sabotage patterns.

The point is better coherence, not perfect teamwork.

[Task check list]

- [x] Add ranged spacing-preservation logic
- [x] Add local lane-discipline logic
- [x] Add position-preservation logic
- [x] Add non-destructive allied local coordination
- [x] Keep coordination scope intentionally small
- [x] Avoid formation-system scope creep

[Task acceptance criteria]
Small groups behave more coherently in common local combat situations without requiring a full doctrine system.

---

[x] (checkbox) - [Task 6] - Add tactical-behavior scenario tests

[Task Description]
Lock the Milestone 4 contract with deterministic tactical scenario tests so later balance work and larger-scale battle work cannot silently break short-horizon behavior quality.

[Task technical implementation]
Add exact tests for the tactical layer.

### Tactical contract tests

Add test coverage for:

- safe-shot preference,
- distance-management mode selection,
- tactical retreat trigger behavior,
- commitment-retention behavior,
- role-sensitive tactical differentiation.

### Small-group tactical tests

Add test coverage for:

- two ranged allies preserving spacing,
- allies avoiding identical bad local lanes,
- local choke/line preservation under pressure,
- reduced obvious self-sabotage in small mixed groups.

### Suggested test groups

- `tests/ai/test_tactical_behavior_contract.py`
- `tests/ai/test_safe_shot_and_distance_management.py`
- `tests/ai/test_tactical_retreat_and_commitment.py`
- `tests/ai/test_small_group_tactical_coordination.py`

These tests should assert:

- tactical behavior patterns,
- legal primitive selection,
- stable short-horizon behavior,
- and role-sensitive divergence,
  not final whole-system balance.

[Task possible affected files]

- new tactical behavior test modules
- new small-group tactical coordination test modules

[Task important notes]
Do not jump to giant many-v-many balance tests yet.
Do not use final win-rate expectations as substitutes for tactical-behavior contract tests.

These are tactical semantics tests.

[Task check list]

- [x] Add safe-shot tests
- [x] Add distance-management tests
- [x] Add retreat tests
- [x] Add commitment tests
- [x] Add role-sensitive behavior tests
- [x] Add small-group coordination tests
- [x] Add deterministic tactical-behavior tests

[Task acceptance criteria]
The tactical AI layer is pinned by deterministic contract tests and tactical scenario tests.

---

[x] (checkbox) - [Task 7] - Add exact Milestone 4 documentation pack

[Task Description]
Document the complete Milestone 4 contract so later balance and scenario milestones cannot reinterpret tactical behavior semantics informally.

[Task technical implementation]
Create:

- `docs/combat/tactical_behavior_rulebook_m4.md`
- `docs/combat/tactical_behavior_m4_test_matrix.md`

`tactical_behavior_rulebook_m4.md` must contain these exact sections:

- Purpose
- Tactical-layer boundaries
- Safe-shot semantics
- Distance-management semantics
- Tactical retreat semantics
- Commitment semantics
- Role-sensitive behavior semantics
- Small-group coordination scope
- Non-goals
- Determinism rules

`tactical_behavior_m4_test_matrix.md` must contain these exact sections:

- Safe-shot tests
- Distance-management tests
- Retreat tests
- Commitment tests
- Role-sensitive behavior tests
- Small-group coordination tests
- Determinism tests

For every test group, document:

- test name or group name,
- input condition,
- expected tactical rule,
- regression caught.

[Task possible affected files]

- `docs/combat/tactical_behavior_rulebook_m4.md`
- `docs/combat/tactical_behavior_m4_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.
Do not defer it.

This milestone exists to stop tactical behavior semantics from living only in code and memory.

[Task check list]

- [x] Document exact tactical rules
- [x] Document role-sensitive behavior classes
- [x] Document small-group coordination scope
- [x] Document exact non-goals
- [x] Document determinism expectations
- [x] Document tactical tests
- [x] Document regression purpose of each test group

[Task acceptance criteria]
Milestone 4 has a complete exact tactical-behavior rulebook document and exact test-matrix document that match the implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking that correct combat and movement primitives automatically produce believable tactical behavior. In Milestone 4, entities must learn to use those primitives deliberately.

What actions must be taken immediately
Freeze the tactical-behavior contract, implement safe-shot and distance-management behavior, add tactical retreat and commitment logic, add role-sensitive behavior, add light small-group coordination, and pin everything with deterministic tactical scenario tests.

What must stop or be eliminated
Stop relying on binary attack-or-run behavior. Stop making tactical quality an accidental side effect of target order or route choice. Stop trying to jump into full formation AI before fixing the common local cases.

The consequences and opportunity cost if this fails
Milestone 5 and later will try to tune balance on top of crude tactical behavior, and the simulation will still look unintelligent even if the underlying combat and movement systems are technically correct.

---

### Implementation Comments (Audit 2026-04-17)

- **TacticalEvaluator**: Canonical evaluation logic in `src/ai/tactical/evaluator.py`. It integrates current capability, enemy proximity, and terrain to derive `TacticalMode`.
- **Safe-Shot**: Implemented as high-priority target selection involving LOS checks and obstruction evaluation, ensuring entities don't step into danger for lower-value hits.
- **Distance Maintenance**: entities now select `MovementIntention` (e.g., `RETREAT`, `COOPERATIVE_REGROUP`) to preserve optimal range.
- **Retreat Behavior**: Integrated with `CombatInteractionService` OAs. Entities evaluation disengagement cost versus staying.
- **Coordination**: Light lane-discipline implemented in `MovementModel` via coordination hints (Wait/Yield).
- **Tests**: Validated in `tests/ai/test_tactical_evaluator.py`.

