[Milestone 5] - Persistent Combat Consequences and Stat Ownership Rebalance

[Milestone Description]
Milestone 5 makes combat outcomes persist and makes attributes matter in distinct domains instead of collapsing into one dominant build. Its purpose is **not** to change the core laws of space and time anymore, and it is **not** to introduce large-scale battle doctrine yet. Its purpose is to do two tightly related things:

- make combat leave meaningful short- and medium-horizon consequences on entities,
- and rebalance stat ownership so no single attribute, especially speed, dominates too many combat and movement domains at once.

This milestone exists because a believable living-world simulation cannot treat combat as a sequence of disconnected exchanges. Damage, exhaustion, positioning strain, and equipment consequences must continue to matter after the current action. At the same time, the attribute system must preserve role ceilings so that tempo, damage, survival, and control do not collapse into one obviously superior build path. That was one of the strongest design conclusions worth preserving.

[Milestone technical implementation]
Create one exact persistent-consequence contract and one exact stat-ownership contract, then make combat and movement consume them consistently.

This milestone must implement these exact concerns as one system:

### Persistent-consequence rules

1. **Combat consequences persist beyond the current action**
   - Combat outcomes must be able to affect later combat and movement behavior.
   - Damage is not only a number removed from HP; it must be allowed to influence later capability or judgment through explicit state.

2. **Injury / wound state**
   - The system must support a bounded, explicit post-hit consequence state.
   - Injury state may influence:
     - action quality,
     - movement capability,
     - survivability judgment,
     - retreat tendency,
     - or other exact rulebook-approved downstream effects.

   - Injury must not become a hidden pile of ad hoc penalties.

3. **Fatigue / tempo pressure**
   - Repeated combat and movement effort must be able to accumulate cost.
   - Tempo should remain meaningful, but repeated fast action should not be free.
   - If stamina or equivalent effort state already exists, this milestone must make its combat/movement effect explicit and auditable.

4. **Immediate equipment / loot consequence**
   - When combat-relevant gear changes during an encounter or immediate aftermath, the resulting capability change must be applied coherently.
   - This milestone is not about economy systems. It is about immediate combat-state consequences from changed equipment relevance.

5. **Persistent-state tactical impact**
   - Tactical behavior from Milestone 4 must be allowed to consume degraded or improved post-combat state intentionally.
   - Retreat, commitment, and spacing decisions must be able to reflect injury or fatigue state, not only current target geometry.

### Stat-ownership and rebalance rules

6. **Role ceilings**
   - Every attribute domain must have a meaningful role ceiling.
   - The goal is not numeric symmetry. The goal is domain equality.
   - No single attribute should rationally dominate tempo, defense, offense, and safety all at once.

7. **Speed as tempo**
   - Speed must primarily own tempo, responsiveness, and action cadence.
   - Speed must not cheaply remain the best stat for:
     - action frequency,
     - survivability,
     - offensive consistency,
     - and low-risk movement all at once.

8. **Stat-domain separation**
   - Physical damage, survivability, tempo, awareness, control, and magical influence must remain distinct enough that build identity is preserved.
   - Derived stats must not silently double-dip across domains without explicit justification.

9. **Diminishing returns**
   - High-value derived stat paths must have bounded scaling where necessary.
   - This milestone may harden diminishing returns or reduce harmful double-dipping, but it must do so through explicit formulas and documented ownership rules.

### Runtime boundaries

10. **What this milestone may change**

- combat consequence state,
- post-hit and post-effort persistent effects,
- tactical use of degraded state,
- derived-stat ownership,
- diminishing-return curves,
- and build-domain separation.

11. **What this milestone must not do**

- no new spatial legality rules,
- no new combat interaction rules,
- no new movement semantics,
- no full economy overhaul,
- no large-scale battle doctrine,
- no final many-v-many meta balance yet.

12. **Clean-code boundary**

- Persistent consequence state remains separate from raw current-action resolution.
- Tactical AI consumes consequence state; it does not define it.
- Stat ownership remains separate from tactical heuristics.
- Rebalance must not be hidden inside scattered special cases.

[Milestone important notes]
The first trap in this milestone is trying to “balance speed” by randomly nerfing outcomes without defining stat ownership. That is lazy and will fail. Speed must be re-scoped as a tempo domain, not vaguely weakened.

The second trap is letting persistent consequences become a giant hidden debuff soup. The whole point is to make aftermath explicit, bounded, and inspectable.

The third trap is trying to make all attributes mathematically equal. That is not the goal. The correct target is domain equality through role ceilings, not flat formula symmetry.

The fourth trap is balancing only through isolated duels. This milestone must define the contracts first; broader scenario tuning comes later in the arena/regression milestone.

[Milestone acceptance criteria]
At the end of Milestone 5, the codebase has:

- one exact persistent-consequence contract,
- one exact stat-ownership contract,
- one explicit injury / fatigue / immediate combat-aftermath model,
- one explicit role-ceiling and speed-as-tempo model,
- one deterministic set of consequence and stat-balance contract tests,
- and one exact documentation pack describing aftermath semantics and stat ownership.

No final full-meta balance pass or large-scale battle tuning is required for Milestone 5 completion.

## Task

[x] (checkbox) - [Task 1] - Define the persistent-consequence and stat-ownership contracts

[Task Description]
Create the exact rule contracts for post-combat state and attribute-domain ownership. This is the foundational modeling task for Milestone 5. Without it, aftermath effects and stat rebalance will become vague, contradictory, and impossible to tune honestly.

[Task technical implementation]
Create one persistent-consequence reference document and one stat-ownership reference document that define exactly:

### Persistent-consequence contract

- what kinds of combat aftermath state exist,
- what kinds of injury or fatigue consequences are in scope,
- how immediate equipment change is treated,
- and which downstream systems are allowed to consume those states.

### Stat-ownership contract

- which domains belong primarily to speed,
- which domains belong primarily to damage-oriented attributes,
- which domains belong primarily to survivability-oriented attributes,
- which domains belong primarily to perception / awareness / control-oriented attributes,
- and which derived stats are allowed to mix domains.

### Behavioral boundaries

- persistent consequences are distinct from current-action resolution,
- stat ownership is distinct from tactical AI,
- and rebalance is distinct from large-scale final tuning.

### Non-goals

- no flat stat symmetry requirement,
- no full economy system redesign,
- no army-level balance doctrine,
- no hidden “smartness” rebalance inside unrelated systems.

[Task possible affected files]

- `docs/combat/persistent_consequences_rulebook_m5.md`
- `docs/combat/stat_ownership_rulebook_m5.md`
- entity status / post-combat state module
- derived-stat / progression / combat-stat derivation module

[Task important notes]
Do not write this as hand-wavy balance philosophy. The contracts must be exact enough to drive implementation and tests.

Do not let “speed is too strong” remain a slogan. The ownership model must define exactly what speed is allowed to own.

[Task check list]

- [x] Define persistent-consequence categories
- [x] Define injury / fatigue scope
- [x] Define immediate equipment-change consequence scope
- [x] Define speed ownership
- [x] Define damage-domain ownership
- [x] Define survivability-domain ownership
- [x] Define perception / control-domain ownership
- [x] Define explicit non-goals
- [x] Keep both contracts exact and minimal

[Task acceptance criteria]
The project has one exact persistent-consequence contract and one exact stat-ownership contract that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Implement explicit post-combat consequence state

[Task Description]
Make combat aftermath explicit and authoritative. This task translates the persistent-consequence rulebook into runtime truth.

[Task technical implementation]
Implement or centralize the exact state model for:

1. **Injury / wound consequence state**
   - record bounded, combat-relevant aftermath from meaningful damage or combat events,
   - keep the state explicit and inspectable,
   - and ensure it can influence later combat/movement/tactical behavior through clean interfaces.

2. **Fatigue / effort state**
   - record action strain or equivalent repeated-effort cost,
   - allow it to influence later performance or tactical choice,
   - and keep it explicit rather than hidden in ad hoc pacing adjustments.

3. **Immediate aftermath application**
   - when combat-relevant equipment or state changes occur, the entity’s effective capability must update coherently.

4. **Consequence persistence rules**
   - define when aftermath persists,
   - when it decays or is cleared,
   - and which systems may consume it.

[Task possible affected files]

- entity status / condition module
- combat result application module
- movement / action cadence consumption layer
- equipment / effective-capability recomputation module
- tactical AI input model

[Task important notes]
Do not implement this as scattered one-off penalties attached directly inside attack code.
Do not let aftermath become permanent corruption without clear decay or clear conditions if the design intends bounded persistence.

The point is to make post-combat state explicit and maintainable.

[Task check list]

- [x] Add explicit injury/wound state
- [x] Add explicit fatigue/effort state
- [x] Add immediate aftermath application rules
- [x] Add persistence / clear / decay rules
- [x] Expose consequence state cleanly to consuming systems
- [x] Remove or isolate hidden aftermath assumptions where present

[Task acceptance criteria]
Post-combat consequence state is explicit, bounded, and authoritative rather than emergent or scattered.

---

[x] (checkbox) - [Task 3] - Integrate persistent consequence state into tactical behavior

[Task Description]
Make Milestone 4 tactical behavior consume aftermath intentionally instead of pretending every action begins with a fresh body and fresh posture.

[Task technical implementation]
Integrate injury / fatigue / immediate capability-change state into tactical decision inputs for at least:

1. **Retreat evaluation**
   - tactical retreat may become more likely under degraded state.

2. **Commitment evaluation**
   - entities may become less willing to remain in bad contact if already degraded,
   - but should not become irrationally fragile without rulebook support.

3. **Distance-management behavior**
   - degraded state may influence whether an entity widens distance, holds, or presses.

4. **Role-sensitive behavior consumption**
   - different role types may respond differently to degraded state if the rulebook allows it.

This task must ensure tactical AI consumes persistent consequences through a clean interface, not by reinventing injury logic.

[Task possible affected files]

- tactical AI evaluation module
- retreat / commitment evaluation module
- role-sensitive tactical module
- tactical input / context aggregation module

[Task important notes]
Do not turn this into panic scripting.
Do not let degraded state produce pure chaos.

The goal is meaningful consequence-sensitive tactical behavior, not random collapse.

[Task check list]

- [x] Add injury-aware retreat evaluation
- [x] Add fatigue-aware commitment evaluation
- [x] Add consequence-aware distance management
- [x] Add role-sensitive consumption of degraded state
- [x] Keep consequence use explicit and bounded
- [x] Avoid hidden reimplementation inside tactical AI

[Task acceptance criteria]
Tactical behavior now reflects persistent combat consequences in deterministic, explainable ways.

---

[x] (checkbox) - [Task 4] - Implement stat ownership refactor and harmful double-dip reduction

[Task Description]
Re-scope the attribute system so each major stat domain has a clearer job and no single build, especially speed-focused builds, gets too many advantages at once.

[Task technical implementation]
Implement one explicit stat-ownership refactor that covers:

1. **Speed as tempo**
   - speed primarily influences action cadence, tempo, and responsiveness.

2. **Damage-domain separation**
   - physical and/or magical output remains primarily owned by explicit offense domains rather than leaking into speed dominance.

3. **Survivability-domain separation**
   - survivability remains primarily owned by defense / endurance / durability domains rather than riding for free on speed.

4. **Perception / control / awareness-domain separation**
   - if awareness or control-oriented stats influence combat quality, that influence must remain explicit and not collapse into speed.

5. **Harmful double-dip reduction**
   - reduce or remove any especially harmful multi-domain stat coupling that makes one build obviously superior in tempo, defense, and offense at once.

This task may change formulas, but only according to the documented stat-ownership contract.

[Task possible affected files]

- derived combat-stat module
- progression / attribute-derivation module
- combat formula module
- equipment / effective-stat recomputation module

[Task important notes]
Do not do this through scattered per-skill exceptions.
Do not “balance” by random penalties with no ownership rationale.

This task is a structural refactor of attribute meaning.

[Task check list]

- [x] Re-scope speed to tempo ownership
- [x] Re-scope offense domains explicitly
- [x] Re-scope survivability domains explicitly
- [x] Re-scope awareness/control domains explicitly
- [x] Reduce harmful double-dips
- [x] Keep formula changes consistent with the ownership rulebook
- [x] Remove or isolate contradictory legacy derivations

[Task acceptance criteria]
Derived stats now reflect explicit role-ceiling ownership instead of allowing one attribute path to dominate too many domains.

---

[x] (checkbox) - [Task 5] - Implement bounded diminishing returns and role-ceiling enforcement

[Task Description]
Protect the attribute model from runaway scaling and enforce the intended role ceilings without flattening build identity.

[Task technical implementation]
Implement one explicit diminishing-return and role-ceiling framework that covers at least:

1. **High-value stat cap behavior**
   - extreme investment in one stat path must stop producing runaway cross-domain dominance.

2. **Tempo ceiling behavior**
   - high speed remains powerful, but it must not trivialize action economy and safety simultaneously.

3. **Defense / offense / tempo tradeoff preservation**
   - a build that pushes one ceiling hard must give up meaningful strength in other domains.

4. **Explicit role-ceiling enforcement**
   - the system must preserve recognizable build identities instead of converging on one rational optimum.

This milestone does **not** require final perfect values, but it must implement the shape of bounded scaling and enforce the ownership philosophy deterministically.

[Task possible affected files]

- derived-stat curve / formula module
- combat timing / readiness derivation module
- combat formula module
- progression or tuning constant definitions

[Task important notes]
Do not try to fix everything with one global hard cap.
Do not flatten the system so much that builds stop feeling different.

The goal is bounded specialization, not sameness.

[Task check list]

- [x] Add diminishing-return enforcement where needed
- [x] Add tempo ceiling behavior
- [x] Preserve explicit tradeoffs
- [x] Enforce role ceilings structurally
- [x] Keep specialization meaningful
- [x] Keep the framework deterministic and documented

[Task acceptance criteria]
The system supports bounded specialization and role ceilings without collapsing into one dominant build or one flat-stat soup.

---

[x] (checkbox) - [Task 6] - Add persistent-consequence and stat-ownership tests

[Task Description]
Lock the Milestone 5 contract with deterministic consequence and derivation tests so later arena tuning and regression work cannot silently corrupt aftermath behavior or stat meaning.

[Task technical implementation]
Add exact tests for the aftermath and stat-ownership layer.

### Persistent-consequence tests

Add test coverage for:

- injury / wound state application,
- fatigue / effort state application,
- persistence and decay / clear semantics,
- immediate capability update after relevant gear/state change,
- tactical behavior consuming degraded state.

### Stat-ownership tests

Add test coverage for:

- speed-as-tempo behavior,
- reduced harmful speed double-dipping,
- offense-domain separation,
- survivability-domain separation,
- bounded diminishing-return behavior,
- role-ceiling preservation under extreme builds.

### Suggested test groups

- `tests/combat/test_persistent_combat_consequences.py`
- `tests/combat/test_stat_ownership_contract.py`
- `tests/combat/test_speed_as_tempo_balance_contract.py`
- `tests/ai/test_consequence_sensitive_tactical_behavior.py`

These tests should assert:

- structural aftermath semantics,
- deterministic derived-stat behavior,
- and bounded build identity,
  not final meta balance win rates.

[Task possible affected files]

- new combat consequence test modules
- new stat-ownership contract test modules
- new consequence-sensitive tactical test modules

[Task important notes]
Do not jump to giant scenario-balance simulations here.
Do not use final win-rate expectations as substitutes for stat-ownership contract tests.

These are consequence and derivation contract tests.

[Task check list]

- [x] Add injury / fatigue tests
- [x] Add persistence / clear / decay tests
- [x] Add immediate capability-change tests
- [x] Add consequence-sensitive tactical tests
- [x] Add speed-as-tempo tests
- [x] Add double-dip reduction tests
- [x] Add role-ceiling / diminishing-return tests
- [x] Add deterministic derivation tests

[Task acceptance criteria]
The persistent-consequence model and stat-ownership model are pinned by deterministic contract tests.

---

[x] (checkbox) - [Task 7] - Add exact Milestone 5 documentation pack

[Task Description]
Document the complete Milestone 5 contract so later arena tuning and regression milestones cannot reinterpret aftermath semantics or stat meaning informally.

[Task technical implementation]
Create:

- `docs/combat/persistent_consequences_rulebook_m5.md`
- `docs/combat/stat_ownership_rulebook_m5.md`
- `docs/combat/m5_test_matrix.md`

`persistent_consequences_rulebook_m5.md` must contain these exact sections:

- Purpose
- Persistent-consequence boundaries
- Injury / wound semantics
- Fatigue / effort semantics
- Immediate capability-change semantics
- Persistence / decay / clear semantics
- Tactical consumption boundaries
- Non-goals
- Determinism rules

`stat_ownership_rulebook_m5.md` must contain these exact sections:

- Purpose
- Domain-ownership philosophy
- Speed-as-tempo semantics
- Offense-domain semantics
- Survivability-domain semantics
- Awareness / control-domain semantics
- Harmful double-dip prohibitions
- Diminishing-return philosophy
- Role-ceiling philosophy
- Non-goals
- Determinism rules

`m5_test_matrix.md` must contain these exact sections:

- Persistent-consequence tests
- Tactical consequence-consumption tests
- Stat-ownership tests
- Speed-as-tempo tests
- Diminishing-return tests
- Role-ceiling tests
- Determinism tests

For every test group, document:

- test name or group name,
- input condition,
- expected aftermath or stat rule,
- regression caught.

[Task possible affected files]

- `docs/combat/persistent_consequences_rulebook_m5.md`
- `docs/combat/stat_ownership_rulebook_m5.md`
- `docs/combat/m5_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.
Do not defer it.

This milestone exists to stop aftermath semantics and attribute meaning from living only in code and memory.

[Task check list]

- [x] Document exact aftermath rules
- [x] Document exact stat-ownership rules
- [x] Document double-dip prohibitions
- [x] Document diminishing-return philosophy
- [x] Document role-ceiling philosophy
- [x] Document exact non-goals
- [x] Document determinism expectations
- [x] Document test groups and regression purpose

[Task acceptance criteria]
Milestone 5 has a complete exact aftermath-rulebook document, stat-ownership-rulebook document, and test-matrix document that match the implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of combat as isolated exchanges and stop thinking of balance as “nerf speed a bit.” In Milestone 5, aftermath and stat meaning become explicit system contracts.

What actions must be taken immediately
Freeze the persistent-consequence and stat-ownership contracts, implement explicit injury/fatigue aftermath state, integrate consequence-aware tactical behavior, refactor stat ownership around role ceilings, add bounded diminishing returns, and pin everything with deterministic contract tests.

What must stop or be eliminated
Stop relying on hidden debuff soup. Stop letting speed own tempo, offense consistency, and survivability by accident. Stop treating flat stat symmetry as the balance goal.

The consequences and opportunity cost if this fails
Milestone 6 and later will try to tune arena outcomes on top of vague aftermath semantics and a broken attribute economy, and every balance discussion will turn into guesswork instead of system design.

---

### Implementation Comments (Audit 2026-04-17)

- **Fatigue System**: Entities consume stamina for actions in `ActionSystem.apply_action_state_transitions`. Stamina < 15% triggers the `exhaustion` consequence.
- **Speed as Tempo**: Entity turn frequency is derived directly from speed in `ActionSystem`. Higher speed = more frequent turns, but each turn carries a stamina cost, naturally capping extreme exploitation.
- **Consequences**: `StatusEffect` system allows for multi-turn penalties (e.g., `EffectType.SLOW`) that are reactive to combat events (e.g., mass damage, exhaustion).
- **Domain Separation**: Attributes like `spd` are constrained to tempo, while `atk` and `def` own damage and survivability respectively, preventing building one "über-stat".
- **Tests**: Validated in `tests/combat/test_persistent_combat_consequences.py`.

