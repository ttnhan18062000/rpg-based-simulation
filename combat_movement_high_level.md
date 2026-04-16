## High-level implementation plan — corrected combat and movement overhaul

This version corrects the earlier high-level plan by doing three things:

- it starts with the **rulebook and time model** before feature work,
- it groups interacting mechanics into **coherent system milestones** instead of parallel patches,
- and it keeps the scope at the **implementation-shaping level**, not detailed task decomposition. That matches the review’s strongest correction: rulebook first, then engine/lifecycle, then combat-time, then movement, then AI, then balance and proof.

This plan assumes the following decisions are already accepted:

- Manhattan remains the shared metric for movement, attack range, and AoE radius,
- one entity per tile remains the default occupancy rule,
- ally pass-through is not added in this phase,
- AoE uses “impact center in range, radius outward,”
- entity actions remain readiness-based,
- world-time must continue even when no entity acts,
- and speed must be rebalanced as a **tempo stat**, not a universal dominance stat.

---

# Milestone 1 — Core rulebook and engine-time refactor

### Description

Freeze the combat and movement rulebook and make the runtime obey it. This is the foundational milestone. It must happen before anti-stalemate logic, AI heuristics, congestion handling, or balance tuning.

### Technical implementation

Define and implement one exact contract for:

- Manhattan distance and cardinal movement,
- one-unit-per-tile occupancy,
- adjacency and engagement semantics,
- AoE center/radius legality,
- line-of-sight scope,
- readiness-based action turns,
- and continuous world-time progression independent of whether any entity acted.

Refactor the engine loop so world-time and entity-turn cadence are no longer mixed together.

### Important notes

This milestone is not “plumbing.” It is the highest-risk integrity milestone. If the rulebook and time model are ambiguous, every later combat or movement fix becomes a patch on unstable ground. The review is right to elevate this above all later mechanics.

### Testing requirements

Use TDD to pin the rulebook first:

- rule-contract tests for distance, adjacency, occupancy, and AoE legality,
- lifecycle tests proving passive world-time still advances on quiet ticks,
- readiness-turn tests proving entities only act when ready,
- and determinism tests for tick progression.

### Acceptance criteria

The engine has one explicit spatial and temporal rulebook, and the loop obeys it consistently.

### Checklist

- [ ] Freeze spatial rules
- [ ] Freeze timing rules
- [ ] Separate world-time from entity action turns
- [ ] Add rule-contract tests
- [ ] Document the rulebook

---

# Milestone 2 — Combat interaction core

### Description

Build the actual combat-time model on top of the frozen rulebook. This milestone covers what happens between “an attack is legal” and “damage is applied,” including commitment, disengagement, pursuit, and loop-breaking.

### Technical implementation

Introduce one coherent combat interaction layer covering:

- spatial legality gates,
- attack context,
- engagement and disengagement behavior,
- opportunity-style punishment if retained,
- pursuit commitment,
- retreat consequences,
- target stickiness,
- and anti-stalemate handling.

This milestone should explicitly solve the common failure cases:

- equal-speed melee vs ranged loops,
- repeated step-back / step-forward loops,
- chase-without-resolution patterns,
- and “kite forever” behavior.

### Important notes

Do not implement anti-stalemate, context modifiers, and disengagement as unrelated features. They are one interaction model and must be designed together or they will fight each other. This is one of the biggest corrections from the earlier plan.

### Testing requirements

Use TDD at the system-contract level:

- legal attack vs illegal attack tests,
- disengagement and pursuit tests,
- anti-loop scenario tests,
- and archetype 1v1 flow tests that assert behavior patterns, not exact numbers.

### Acceptance criteria

Combat resolves through an explicit interaction model rather than accidental resolver order or binary chase/flee logic.

### Checklist

- [ ] Build combat legality layer
- [ ] Add combat context layer
- [ ] Add engagement/disengagement model
- [ ] Add anti-stalemate model
- [ ] Add 1v1 combat flow tests
- [ ] Document the combat-time model

---

# Milestone 3 — Movement model and congestion control

### Description

Turn movement into a layered, intention-driven system that remains compatible with hard occupancy. This milestone is about making entities move like actors in a world, not just pathfinding cursors.

### Technical implementation

Build movement as three layers:

- route-level movement planning,
- local step-level decision making,
- and explicit movement intention.

Introduce support for intentions such as:

- pursue,
- retreat,
- hold,
- reposition,
- intercept,
- guard,
- regroup.

Add congestion handling without ally pass-through, using:

- waiting,
- yielding,
- sidestepping,
- local rerouting,
- and route commitment / hysteresis.

### Important notes

Do not solve congestion by weakening occupancy too early. The design decision remains: keep one-unit-per-tile and make movement smarter instead. This milestone should make that viable.

### Testing requirements

Use TDD around movement contracts and scenarios:

- blocked-ally corridor tests,
- chokepoint navigation tests,
- pursuit and retreat stability tests,
- anti-oscillation tests,
- and intention-differentiation tests.

### Acceptance criteria

Movement becomes layered, intention-driven, and congestion-aware while preserving hard occupancy.

### Checklist

- [ ] Add movement intentions
- [ ] Add route commitment
- [ ] Add local congestion handling
- [ ] Preserve hard occupancy
- [ ] Add movement behavior tests
- [ ] Document movement semantics

---

# Milestone 4 — Tactical AI behavior

### Description

Teach entities to use the new combat and movement primitives in believable ways. This milestone should make tactical behavior emerge from explicit heuristics, not accidental geometry.

### Technical implementation

Integrate the new combat and movement model into AI behavior for:

- safe shot selection,
- distance maintenance,
- cover usage,
- retreat under threat,
- chokepoint preference,
- flanking preference if supported,
- and improved skirmish behavior for ranged entities.

AI should now choose from stable tactical primitives rather than trying to invent tactics from raw pathing and raw attacks.

### Important notes

This milestone must come after the combat interaction core and movement model. If done earlier, you will teach AI around unstable mechanics and then rewrite it later.

### Testing requirements

Use scenario-driven TDD:

- cover preference scenarios,
- retreat threshold scenarios,
- ranged-vs-melee tactical behavior scenarios,
- mixed-role small-group scenarios,
- and chokepoint vs open-field tactical comparisons.

### Acceptance criteria

AI uses the system deliberately and produces believable tactical behavior in common fights.

### Checklist

- [ ] Add safe-shot heuristics
- [ ] Add distance and cover heuristics
- [ ] Add retreat heuristics
- [ ] Add group-space tactical heuristics
- [ ] Add tactical AI scenario tests
- [ ] Document tactical behavior goals

---

# Milestone 5 — Persistent combat consequences and stat ownership rebalance

### Description

Make combat outcomes persist and rebalance the attribute model around role ceilings. This milestone turns encounters from isolated exchanges into continuing lived consequences, while preventing speed from becoming the single rational build.

### Technical implementation

Apply persistent consequences to combat and movement through:

- wounds or injury effects,
- fatigue / stamina-like tempo pressure if retained,
- recovery implications,
- immediate gear/loot consequence where relevant,
- and behavior changes driven by degraded state.

At the same time, rebalance the attribute model so:

- speed mainly owns tempo and responsiveness,
- strength owns physical output,
- durability stats own staying power,
- perception/wisdom-style stats own reading/awareness domains,
- and no one stat dominates tempo, defense, and offense at once.

### Important notes

Do not try to make all stats equal by formula. The goal is **domain equality through role ceilings**, not flat symmetry. That principle is one of the strongest decisions worth keeping.

### Testing requirements

Use TDD for both derivation and scenario effects:

- persistent-state effect tests,
- stat-ownership contract tests,
- diminishing-return tests,
- and arena duels comparing extreme builds.

### Acceptance criteria

Combat has meaningful aftereffects, and speed no longer behaves like the dominant answer to every combat and movement problem.

### Checklist

- [ ] Add persistent combat consequences
- [ ] Rebalance speed ownership
- [ ] Define stat role ceilings
- [ ] Add stat and consequence tests
- [ ] Document stat ownership and persistence rules

---

# Milestone 6 — Arena harness, scenario regression, and tuning surface

### Description

Build the official balance and behavior validation surface. This milestone exists to turn design expectations into repeatable scenario proof.

### Technical implementation

Create or extend a structured arena harness for:

- 1v1,
- 1v many,
- and many vs many archetype scenarios.

Use it to validate:

- faster ranged vs slower melee,
- faster melee vs slower ranged,
- equal-speed ranged vs melee,
- one elite vs many weak,
- melee front plus ranged back patterns,
- choke-point vs open-field patterns,
- and anti-stalemate regression.

The harness should assert outcome patterns and failure envelopes, not exact combat transcripts.

### Important notes

This should be the dedicated tuning and regression layer, not a giant second engine. Extend the existing arena/E2E direction instead of creating a separate world. That keeps clean-code boundaries intact.

### Testing requirements

This milestone is inherently test-heavy:

- archetype scenario suites,
- regression metrics for stalemate rates and fight length,
- and repeated deterministic simulations to catch balance drift.

### Acceptance criteria

The project has one stable simulation harness that can expose combat and movement regressions early and support safe tuning.

### Checklist

- [ ] Build or extend arena harness
- [ ] Add core archetype scenario matrix
- [ ] Add regression metrics
- [ ] Add deterministic repeated simulations
- [ ] Document the scenario contract

---

# Milestone 7 — Observability, rollout hardening, and final documentation

### Description

Expose the new systems clearly enough that they can be debugged, tuned, and maintained without guesswork.

### Technical implementation

Add observability for:

- readiness and world-time state,
- combat legality and blocked reasons,
- movement intention,
- congestion or waiting reasons,
- pursuit/disengage context,
- persistent-state impact,
- and the balance-relevant combat context needed for tuning.

Finalize the documentation pack:

- rulebook,
- combat-time model,
- movement model,
- tactical behavior guide,
- stat ownership guide,
- arena scenario matrix,
- and rollout/feature-flag guidance.

### Important notes

Do not leave the overhaul as code plus memory. If the system cannot be inspected and explained, future tuning will degrade into superstition.

### Testing requirements

Add observability and documentation-integrity checks for:

- stable exposed fields,
- deterministic explanations under identical state,
- and alignment between docs and surfaced runtime behavior.

### Acceptance criteria

The overhaul is observable, debuggable, and maintainable.

### Checklist

- [ ] Add runtime observability
- [ ] Add blocked-action explanations
- [ ] Finalize docs
- [ ] Add doc-integrity tests
- [ ] Add rollout hardening checks

---

## Recommended implementation order

1. Milestone 1 — Core rulebook and engine-time refactor
2. Milestone 2 — Combat interaction core
3. Milestone 3 — Movement model and congestion control
4. Milestone 4 — Tactical AI behavior
5. Milestone 5 — Persistent combat consequences and stat ownership rebalance
6. Milestone 6 — Arena harness, scenario regression, and tuning surface
7. Milestone 7 — Observability, rollout hardening, and final documentation

This is the corrected order because it follows the dependency chain the review was pushing toward:

- rules first,
- engine-time second,
- interaction model before AI,
- movement before tactical sophistication,
- balance after mechanics,
- and observability after the system shape is stable.

## Clean code and TDD guidance for the whole plan

Across all milestones:

- keep spatial legality separate from combat resolution,
- keep combat interaction separate from raw stat math,
- keep movement intention separate from route solving,
- keep world-time separate from entity action turns,
- keep balance tuning separate from rule definition,
- and keep observability separate from gameplay authority.

Use TDD in this sequence:

1. write the rule or behavior contract test,
2. implement the smallest coherent slice,
3. refactor to isolate responsibilities,
4. then add scenario-level regression coverage.

Do not start by writing giant end-to-end tests for an unsettled mechanic.
Do not start by decomposing everything into low-level tickets before the milestone contract is frozen.

## Final delivery condition

This overhaul is complete only when all of the following are true:

- combat and movement obey one explicit rulebook,
- world-time and entity turns are correctly separated,
- combat interaction no longer relies on accidental loops or binary kiting,
- movement is intention-driven and congestion-aware,
- hard occupancy remains viable without ally pass-through,
- speed is a tempo stat instead of a dominance stat,
- common archetype scenarios produce believable results,
- and the whole system is observable and documented.

If you want, next I’ll convert this corrected high-level plan into the **detailed milestone breakdown** in the same implementation-document format.
