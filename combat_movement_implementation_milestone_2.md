[Milestone 2] - Combat Interaction Core

[Milestone Description]
Milestone 2 builds the actual combat-time model on top of the frozen Milestone 1 laws of space and time. Its purpose is **not** to make movement smarter yet, and it is **not** to do global balance tuning yet. Its purpose is to define and implement the exact interaction layer that sits between:

- spatially legal combat,
- and internal hit / damage / effect resolution.

This milestone exists because the current weak point is no longer raw legality. The real gap is interaction quality:

- when combatants commit,
- when they can disengage,
- how retreat is punished or tolerated,
- how pursuit persists or ends,
- how target-switching is stabilized,
- and how repeated chase / kite / no-contact loops are broken.

The review was right to force this into one coherent milestone instead of scattering it across separate “opportunity attack,” “anti-kiting,” and “context modifier” tickets. These are not separate systems. They are one combat-time model.

[Milestone technical implementation]
Create one exact combat interaction contract and make all combat actions pass through it before internal combat math is applied.

This milestone must implement these exact concerns as one system:

### Interaction-layer rules

1. **Engagement state**
   - Define when two entities are considered actively engaged in close combat.
   - Engagement must be derived from exact spatial and combat-state conditions, not vague “in combat” flags.
   - Engagement must be stable enough to support disengagement rules and pursuit rules.

2. **Disengagement**
   - Define when an entity is attempting to leave engagement.
   - Leaving engagement must not behave the same as ordinary movement.
   - Disengagement must expose the entity to an explicit consequence model in this milestone.

3. **Pursuit commitment**
   - Define when a pursuing entity remains committed to a target.
   - Pursuit must not reset every action unless a meaningful condition breaks commitment.
   - Pursuit must be able to terminate cleanly instead of looping indefinitely.

4. **Attack context**
   - Combat outcomes must be allowed to depend on context such as:
     - whether the attacker moved to get here,
     - whether the defender is already engaged,
     - whether the attacker is disengaging,
     - whether the target is under immediate pressure,
     - whether the attack is part of a persistent pursuit or a fresh contact.

   - This milestone does **not** require final tuning values. It requires the model and hooks.

5. **Target stickiness**
   - Combatants must not constantly retarget without cause.
   - A target-switching rule must exist so combat feels committed rather than jittery.
   - Switching targets must require a meaningful threshold or trigger.

6. **Anti-stalemate policy**
   - The system must explicitly handle common no-resolution loops, including:
     - equal-speed ranged vs melee chase loops,
     - repeated step-back / step-forward combat loops,
     - repeated disengage / re-engage loops,
     - chase-without-contact loops.

   - This milestone must define a general anti-stalemate framework, not isolated patches.

### Runtime boundaries

7. **What this milestone may change**
   - combat interaction flow,
   - engagement and disengagement semantics,
   - pursuit persistence,
   - combat-context hooks,
   - anti-stalemate resolution behavior.

8. **What this milestone must not do**
   - no global movement intention system yet,
   - no congestion / corridor resolution system yet,
   - no speed/stat rebalance yet,
   - no broader tactical AI heuristics yet,
   - no final combat balance tuning yet.

9. **Clean-code boundary**
   - Spatial legality from Milestone 1 remains separate.
   - Combat interaction remains separate from raw hit / damage / crit math.
   - Anti-stalemate remains part of combat interaction, not tactical AI glue code.
   - This milestone must keep those responsibilities distinct.

[Milestone important notes]
The first trap in this milestone is implementing anti-stalemate as a pile of special cases. That will rot immediately. Equal-speed loops, disengage abuse, and kite loops are symptoms of the same missing interaction model, not unrelated bugs.

The second trap is over-tuning before the model exists. This milestone is about defining and enforcing the interaction contract. Fine balance values can be tuned later.

The third trap is letting combat behavior still depend mostly on resolver order. Movement-before-attack or attack-before-skill may remain as engine ordering, but the actual interaction semantics must not be accidental side effects of that order anymore.

The fourth trap is trying to solve this with smarter AI before the combat system supports the behavior. Tactical AI comes later. This milestone must first give AI a correct interaction model to use.

[Milestone acceptance criteria]
At the end of Milestone 2, the codebase has:

- one exact combat interaction contract,
- one explicit engagement and disengagement model,
- one explicit pursuit and target-stickiness model,
- one explicit anti-stalemate framework,
- one deterministic set of interaction-level tests,
- and one exact documentation pack describing the combat-time model.

No tactical movement sophistication, congestion handling, or stat rebalance is required for Milestone 2 completion.

## Task

[ ] (checkbox) - [Task 1] - Define the combat interaction contract

[Task Description]
Create the exact rule contract for combat interaction semantics. This is the foundational modeling task for Milestone 2. Without it, engagement, disengagement, pursuit, and anti-loop behavior will remain implicit and contradictory.

[Task technical implementation]
Create one combat interaction reference document and one code-facing interaction contract that define exactly:

### Interaction contract

- when an entity becomes engaged,
- when an entity is considered to be disengaging,
- what a pursuing entity remains committed to,
- when target switching is allowed,
- what kinds of combat loops count as unresolved loops,
- and what class of anti-stalemate response is legal.

### Behavioral boundaries

- interaction happens after spatial legality,
- interaction happens before internal combat resolution,
- interaction is distinct from tactical AI decision policy,
- interaction is distinct from stat-balance tuning.

### Non-goals

- no movement congestion logic,
- no cover-centric tactical AI,
- no stat rebalance,
- no group tactics yet.

[Task possible affected files]

- `docs/combat/combat_interaction_rulebook_m2.md`
- combat interaction layer / combat engine module
- combat state / engagement tracking module
- scheduler or action sequencing integration points

[Task important notes]
Do not write this as vague behavior prose. The contract must be exact enough to derive tests and implementation boundaries from it.

Do not let anti-stalemate live as an undocumented emergency patch.

[Task check list]

- [ ] Define engagement semantics
- [ ] Define disengagement semantics
- [ ] Define pursuit commitment semantics
- [ ] Define target-stickiness semantics
- [ ] Define anti-stalemate problem classes
- [ ] Define interaction-layer boundaries
- [ ] Define explicit non-goals
- [ ] Keep the contract exact and minimal

[Task acceptance criteria]
The project has one exact combat interaction contract that can be used as the authoritative source for implementation and tests.

---

[ ] (checkbox) - [Task 2] - Implement the engagement and disengagement state model

[Task Description]
Make combat interaction state explicit and authoritative. This task translates the engagement/disengagement portion of the rulebook into runtime truth.

[Task technical implementation]
Implement or centralize the exact state model for:

1. **Engagement entry**
   - entering active close combat,
   - retaining engagement across immediate successive actions when appropriate,
   - and clearing engagement when the rulebook says contact is broken.

2. **Disengagement attempt**
   - detect when a movement or combat action is an attempt to leave engagement,
   - mark it distinctly from ordinary repositioning,
   - route it through the combat interaction layer.

3. **Disengagement consequence hook**
   - define the place where disengagement consequences are evaluated,
   - without forcing final numerical tuning in this milestone.

4. **Combat-state persistence**
   - combat interaction state must persist long enough to support pursuit and anti-loop logic,
   - but not become a hidden permanent state blob.

[Task possible affected files]

- combat state / interaction state module
- movement-to-combat transition logic
- combat engine / action application integration
- entity transient state / current combat context module

[Task important notes]
Do not implement this as loose scattered flags.
Do not treat “moved away” and “disengaged” as identical concepts.

The whole point is to make combat contact state explicit and auditable.

[Task check list]

- [ ] Add explicit engagement state
- [ ] Add explicit disengagement detection
- [ ] Add disengagement consequence hook
- [ ] Add engagement clear conditions
- [ ] Keep state transient and authoritative
- [ ] Remove or isolate conflicting legacy assumptions

[Task acceptance criteria]
Engagement and disengagement are explicit, deterministic runtime concepts rather than emergent side effects.

---

[ ] (checkbox) - [Task 3] - Implement combat context and target-stickiness hooks

[Task Description]
Add the missing middle layer between spatial legality and raw combat math so combat behavior can depend on what is happening, not only on where entities stand.

[Task technical implementation]
Implement the exact context hooks needed for later tuning:

1. **Attack context hook**
   - whether attacker recently moved,
   - whether defender is currently engaged,
   - whether attacker is disengaging,
   - whether the attack is part of ongoing pursuit,
   - and whether contact is fresh or persistent.

2. **Target-stickiness rule**
   - current target is retained unless a meaningful break condition occurs,
   - target switching requires an explicit trigger or threshold,
   - repeated re-evaluation must not cause jitter every action.

3. **Interaction-to-resolution boundary**
   - internal damage/hit logic must consume a structured interaction context,
   - not reconstruct one ad hoc.

[Task possible affected files]

- combat interaction module
- target selection / combat focus module
- combat resolution input model
- transient action-context model

[Task important notes]
Do not tune every modifier now.
This task is about adding the right structure and boundaries.

Do not let target stickiness become “never retarget.” It is controlled persistence, not blindness.

[Task check list]

- [ ] Add structured combat context
- [ ] Add moved / engaged / pursuit context hooks
- [ ] Add target-stickiness rule
- [ ] Add explicit retarget triggers
- [ ] Pass interaction context into combat resolution
- [ ] Remove ad hoc reconstruction where possible

[Task acceptance criteria]
Combat resolution receives explicit interaction context, and target switching is stable instead of jitter-driven.

---

[ ] (checkbox) - [Task 4] - Implement the anti-stalemate framework

[Task Description]
Create one general mechanism for resolving no-progress combat loops. This is the core corrective task for the current equal-speed and repeated disengage failures.

[Task technical implementation]
Implement one explicit anti-stalemate framework that covers at least these problem classes:

1. **Equal-speed pursuit loops**
   - melee and ranged entities repeatedly maintain non-contact without decisive change.

2. **Repeated disengage / re-engage loops**
   - entities repeatedly leave and restore the same contact state without meaningful progress.

3. **Step-back / step-forward loops**
   - entities keep exchanging the same movement pattern around one range threshold.

4. **Chase-without-resolution loops**
   - pursuit persists without contact, payoff, or clean abandonment.

This framework must define:

- how unresolved repetition is detected,
- what counts as progress,
- and what class of response is allowed:
  - forced commitment,
  - disengagement consequence,
  - pursuit break,
  - or another exact rulebook-approved resolution.

This milestone does **not** require final tuning of every threshold, but it must implement the system shape and deterministic behavior.

[Task possible affected files]

- combat interaction module
- pursuit / chase state module
- action history / short-horizon combat memory module
- combat engine orchestration layer

[Task important notes]
Do not solve each loop type with separate unrelated hacks.
Do not hide this logic inside tactical AI scoring.

The anti-stalemate layer is part of combat interaction, not personality.

[Task check list]

- [ ] Define repeated-loop detection
- [ ] Define progress vs no-progress criteria
- [ ] Handle equal-speed pursuit loops
- [ ] Handle disengage / re-engage loops
- [ ] Handle step-threshold loops
- [ ] Handle chase-without-resolution loops
- [ ] Keep the response deterministic
- [ ] Keep the framework general rather than patch-based

[Task acceptance criteria]
Common no-progress combat loops are detected and resolved through one explicit, deterministic interaction framework.

---

[ ] (checkbox) - [Task 5] - Add combat interaction and anti-stalemate tests

[Task Description]
Lock the Milestone 2 contract with deterministic tests so later tactical AI and balance work cannot silently break the combat interaction model.

[Task technical implementation]
Add exact tests for the interaction layer.

### Interaction contract tests

Add test coverage for:

- engagement entry and exit,
- disengagement detection,
- target-stickiness behavior,
- retarget trigger behavior,
- interaction context passing into combat resolution.

### Anti-stalemate tests

Add test coverage for:

- equal-speed ranged vs melee no-progress scenario,
- repeated disengage / re-engage pattern,
- repeated step-back / step-forward pattern,
- chase-without-contact timeout or break behavior.

### Suggested test groups

- `tests/combat/test_combat_interaction_contract.py`
- `tests/combat/test_disengagement_and_pursuit.py`
- `tests/combat/test_anti_stalemate_behavior.py`

These tests should assert:

- structural combat behavior,
- stable progression,
- and loop resolution,
  not final balance numbers.

[Task possible affected files]

- new combat interaction test modules
- new anti-stalemate test modules

[Task important notes]
Do not write giant many-v-many tests yet.
Do not use balance expectations as substitutes for interaction expectations.

These are contract tests for combat-time semantics.

[Task check list]

- [ ] Add engagement tests
- [ ] Add disengagement tests
- [ ] Add target-stickiness tests
- [ ] Add context-passing tests
- [ ] Add equal-speed loop tests
- [ ] Add disengage loop tests
- [ ] Add chase loop tests
- [ ] Add deterministic progression tests

[Task acceptance criteria]
The combat interaction model is pinned by deterministic contract tests and loop-resolution tests.

---

[ ] (checkbox) - [Task 6] - Add exact Milestone 2 documentation pack

[Task Description]
Document the complete Milestone 2 contract so later milestones cannot reinterpret combat interaction semantics informally.

[Task technical implementation]
Create:

- `docs/combat/combat_interaction_rulebook_m2.md`
- `docs/combat/combat_interaction_m2_test_matrix.md`

`combat_interaction_rulebook_m2.md` must contain these exact sections:

- Purpose
- Interaction-layer boundaries
- Engagement semantics
- Disengagement semantics
- Pursuit commitment semantics
- Target-stickiness semantics
- Anti-stalemate problem classes
- Anti-stalemate resolution classes
- Non-goals
- Determinism rules

`combat_interaction_m2_test_matrix.md` must contain these exact sections:

- Engagement tests
- Disengagement tests
- Target-stickiness tests
- Combat-context tests
- Equal-speed loop tests
- Disengage loop tests
- Chase loop tests
- Determinism tests

For every test group, document:

- test name or group name,
- input condition,
- expected interaction rule,
- regression caught.

[Task possible affected files]

- `docs/combat/combat_interaction_rulebook_m2.md`
- `docs/combat/combat_interaction_m2_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.
Do not defer it.

This milestone exists to stop combat-time semantics from living only in code and memory.

[Task check list]

- [ ] Document exact interaction rules
- [ ] Document anti-stalemate classes
- [ ] Document exact non-goals
- [ ] Document determinism expectations
- [ ] Document interaction tests
- [ ] Document loop-resolution tests
- [ ] Document regression purpose of each test group

[Task acceptance criteria]
Milestone 2 has a complete exact interaction-rulebook document and exact test-matrix document that match the implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of disengagement, pursuit, target-switching, and anti-kiting as separate “features.” In Milestone 2, they are one combat interaction model.

What actions must be taken immediately
Freeze the interaction contract, implement engagement/disengagement state, add target stickiness and context hooks, build the anti-stalemate framework, and pin everything with deterministic contract tests.

What must stop or be eliminated
Stop solving chase and kiting failures with isolated patches. Stop relying on resolver order and AI guesswork to define combat interaction semantics.

The consequences and opportunity cost if this fails
Milestone 3 and later will try to build smarter movement and smarter AI on top of undefined combat contact behavior, and the entire overhaul will drift back into patchwork.
