[Milestone 6] - Arena Harness, Scenario Regression, and Tuning Surface

[Milestone Description]
Milestone 6 builds the official validation and tuning surface for the combat and movement overhaul. Its purpose is **not** to invent a second combat engine, and it is **not** to jump into final release tuning yet. Its purpose is to create one deterministic, repeatable scenario harness that can prove whether the systems from Milestones 1 through 5 actually produce believable and stable outcomes.

This milestone exists because design truth and implementation truth are still not enough by themselves. After rulebook, combat interaction, movement model, tactical behavior, and stat ownership are in place, the project needs one authoritative place to answer questions like:

- does faster ranged usually beat slower melee in open space,
- does equal-speed ranged vs melee still stall too often,
- do chokepoints reduce swarm advantage,
- does AoE punish clumping,
- do role ceilings actually prevent one dominant build,
- and do later changes silently break these behaviors?

The corrected high-level plan explicitly moved this milestone **after** system contracts and stat ownership, because scenario regression should validate stable mechanics, not unstable experiments. It also explicitly rejected building a giant separate framework from scratch. This milestone should extend the existing arena / simulation direction rather than duplicate the runtime.

[Milestone technical implementation]
Create one exact arena-harness contract and make all high-frequency combat and movement validation consume it consistently.

This milestone must implement these exact concerns as one system:

### Arena-harness rules

1. **Single authoritative simulation surface**
   - The harness must use the real combat, movement, timing, and tactical systems.
   - It must not implement a second “test-only combat engine.”
   - Scenario execution must be representative of real runtime behavior.

2. **Scenario contract**
   - Every arena scenario must define, at minimum:
     - participating entities,
     - combat roles or capability profiles,
     - initial positions,
     - terrain / obstacle conditions,
     - relevant equipment or capability assumptions,
     - and victory / stop conditions.

   - Scenarios must be explicit, versionable, and deterministic.

3. **Scenario families**
   - The harness must support at least these scenario families:
     - 1v1,
     - 1v many,
     - many vs many,
     - open-field variants,
     - chokepoint / constrained-space variants.

4. **Outcome-pattern validation**
   - The harness must support expected-pattern validation rather than exact combat transcript equality.
   - The primary output is not “entity A always ends with 17 HP.”
   - The primary output is:
     - win-rate pattern,
     - fight-length pattern,
     - stall-rate pattern,
     - engagement-resolution pattern,
     - spacing / clumping pattern where relevant.

5. **Deterministic repeated execution**
   - The harness must support deterministic repeated runs under:
     - identical state,
     - controlled seeds if seeds are involved,
     - and controlled scenario definitions.

   - Repeated runs must support regression comparison.

6. **Metrics surface**
   - The harness must produce structured metrics for at least:
     - win/loss,
     - time-to-resolution,
     - stalemate / timeout incidence,
     - distance / engagement transition summaries where relevant,
     - and candidate balance signals such as whether one build path dominates too broadly.

   - This milestone does **not** require final balance dashboards, but it must produce the structured tuning surface that later tuning can consume.

7. **Regression baseline**
   - The harness must support committed scenario baselines so later changes can be evaluated against known expected behavior.
   - Regression checks must be narrow enough to be stable, but strong enough to catch design drift.

### Runtime boundaries

8. **What this milestone may change**
   - scenario execution surface,
   - deterministic combat/movement simulation harness,
   - structured metric extraction,
   - regression scenario definitions,
   - and balance-signal reporting.

9. **What this milestone must not do**
   - no rewriting of combat or movement logic inside the harness,
   - no hidden scenario-specific combat rules,
   - no final large-scale balance pass yet,
   - no replacement of lower-level contract tests from earlier milestones.

10. **Clean-code boundary**

- Contract tests from earlier milestones remain the source of truth for individual rule correctness.
- The arena harness is the source of truth for scenario-level behavioral regression.
- The harness must consume real runtime systems rather than simulating them with test-local shortcuts.

[Milestone important notes]
The first trap in this milestone is building a fake harness that reimplements simplified combat logic. That destroys trust immediately. The arena surface must run the real system.

The second trap is asserting exact turn-by-turn outcomes everywhere. That is brittle and useless for higher-level balance validation. The right level here is patterned outcome expectations and stable regression envelopes.

The third trap is turning this into a giant exhaustive matrix before the core scenarios are proven valuable. Start with the common archetypes and the most important environmental variants.

The fourth trap is confusing this milestone with final tuning. This milestone builds the instrument panel, baseline scenario set, and regression surface. It does not finish balancing the whole game.

[Milestone acceptance criteria]
At the end of Milestone 6, the codebase has:

- one exact arena-harness contract,
- one deterministic scenario execution surface using real runtime systems,
- one explicit set of core scenario families,
- one structured metrics and regression-baseline model,
- one deterministic set of scenario-regression tests,
- and one exact documentation pack describing the arena contract and baseline scenarios.

No final release-wide balance pass or UI-level balancing dashboard is required for Milestone 6 completion.

## Task

[ ] (checkbox) - [Task 1] - Define the arena harness and scenario contract

[Task Description]
Create the exact rule contract for scenario-based combat and movement validation. This is the foundational modeling task for Milestone 6. Without it, arena scenarios, repeated runs, and regression baselines will remain ad hoc and untrustworthy.

[Task technical implementation]
Create one arena reference document and one code-facing scenario contract that define exactly:

### Arena contract

- what the harness runs,
- how scenarios are defined,
- what required scenario fields exist,
- what counts as a valid outcome pattern,
- what metrics the harness must emit,
- and how deterministic repeated execution is guaranteed.

### Scenario contract

Every scenario must define:

- participant set,
- role / capability assumptions,
- spawn or initial placement,
- terrain / obstacle conditions,
- stop conditions,
- and expected regression pattern type.

### Behavioral boundaries

- harness consumes real runtime systems,
- harness is distinct from unit-level rule tests,
- harness is distinct from final balance tuning,
- regression patterns are distinct from exact combat transcript equality.

### Non-goals

- no second combat engine,
- no scenario-specific hidden combat rules,
- no giant exhaustive content matrix yet,
- no final meta-balance conclusions yet.

[Task possible affected files]

- `docs/combat/arena_harness_rulebook_m6.md`
- arena / simulation harness module
- scenario definition module
- regression baseline / metric model module

[Task important notes]
Do not define scenarios loosely in prose-only form.
Do not leave expected behavior as “looks reasonable.”

The contract must be exact enough to drive implementation, tests, and future baseline updates.

[Task check list]

- [ ] Define arena harness boundaries
- [ ] Define scenario required fields
- [ ] Define outcome-pattern semantics
- [ ] Define metric requirements
- [ ] Define determinism requirements
- [ ] Define regression-baseline expectations
- [ ] Define explicit non-goals
- [ ] Keep the contract exact and minimal

[Task acceptance criteria]
The project has one exact arena-harness contract and one exact scenario contract that can be used as the authoritative source for implementation and tests.

---

[ ] (checkbox) - [Task 2] - Implement deterministic scenario execution on real runtime systems

[Task Description]
Make the harness run real combat and movement systems deterministically. This task translates the arena contract into executable runtime truth.

[Task technical implementation]
Implement one authoritative scenario execution layer that:

1. **Uses the real systems**
   - combat legality,
   - combat interaction,
   - movement model,
   - tactical AI behavior,
   - persistent consequences,
   - and stat-ownership behavior must all be consumed from the real runtime.

2. **Supports deterministic repeated execution**
   - identical scenario inputs must produce stable repeated results under the same deterministic conditions.

3. **Supports scenario stop conditions**
   - victory,
   - timeout / stalemate,
   - survivor threshold,
   - or other exact rulebook-approved stop semantics.

4. **Supports scenario-family execution**
   - 1v1,
   - 1v many,
   - many vs many,
   - open-field,
   - constrained-space / chokepoint.

[Task possible affected files]

- arena harness runtime module
- scenario execution / orchestration layer
- deterministic runner integration layer
- stop-condition / scenario result model

[Task important notes]
Do not “mock away” the real combat and movement systems here.
Do not fork the runtime into a simplified test-only mode.

The point is authoritative scenario execution.

[Task check list]

- [ ] Run real combat systems
- [ ] Run real movement systems
- [ ] Support deterministic repeated execution
- [ ] Support scenario stop conditions
- [ ] Support core scenario families
- [ ] Keep the execution layer authoritative and minimal

[Task acceptance criteria]
Arena scenarios execute deterministically on the real combat and movement runtime rather than on a second simplified engine.

---

[ ] (checkbox) - [Task 3] - Implement the core scenario matrix

[Task Description]
Define the minimum scenario set that validates the most important common combat and movement patterns. This task creates the first authoritative regression matrix for the overhaul.

[Task technical implementation]
Implement one core scenario matrix that includes at least:

### 1v1 scenarios

- melee vs melee
- faster ranged vs slower melee
- faster melee vs slower ranged
- equal-speed ranged vs melee
- ranged vs ranged
- AoE-capable entity vs single target

### 1v many scenarios

- one melee vs many melee
- one melee vs many ranged
- one ranged vs many melee
- one elite vs many weak

### many vs many scenarios

- melee line vs melee line
- melee front plus ranged back vs same
- mixed group vs AoE-heavy group
- open-field engagement
- chokepoint engagement

Each scenario must specify:

- exact participant archetypes or fixtures,
- map / terrain shape,
- stop condition,
- and the type of pattern the scenario is intended to validate.

[Task possible affected files]

- scenario definition module
- core arena scenario pack
- fixture / archetype factory or scenario entity builder

[Task important notes]
Do not expand endlessly here.
Start with the common and design-critical scenarios first.

Do not encode full class lore or content-specific assumptions into the scenario matrix unless that is already part of the accepted fixture model.

[Task check list]

- [ ] Add core 1v1 scenarios
- [ ] Add core 1v many scenarios
- [ ] Add core many-vs-many scenarios
- [ ] Add open-field variants
- [ ] Add chokepoint variants
- [ ] Keep scenarios explicit and versionable

[Task acceptance criteria]
The project has one authoritative core scenario matrix that covers the most important combat and combat-movement archetypes.

---

[ ] (checkbox) - [Task 4] - Implement structured metric extraction and regression baselines

[Task Description]
Turn scenario execution into a usable tuning and regression surface. This task ensures the harness produces stable signals instead of raw noisy transcripts.

[Task technical implementation]
Implement one structured metrics model that extracts at least:

- win/loss result,
- survivor state summary,
- fight length / time-to-resolution,
- timeout / stalemate incidence,
- engagement transition summary where relevant,
- spacing / clumping summary where relevant,
- and repeated-run aggregate summaries.

Implement one regression-baseline model that allows:

- expected pattern envelopes,
- acceptable regression thresholds,
- and scenario-family baseline comparison.

This task must support comparing later code changes against known behavior without requiring exact move-by-move equality.

[Task possible affected files]

- arena metrics module
- regression-baseline model
- repeated-run aggregation module
- scenario result serialization / reporting layer

[Task important notes]
Do not dump raw logs and call that a metric surface.
Do not require exact transcript equality for scenario regression.

The goal is stable, meaningful tuning and regression signals.

[Task check list]

- [ ] Add structured scenario metrics
- [ ] Add repeated-run aggregation
- [ ] Add regression-baseline model
- [ ] Add acceptable regression-envelope support
- [ ] Keep metrics stable and interpretable
- [ ] Avoid transcript-equality overreach

[Task acceptance criteria]
Scenario execution produces structured tuning metrics and stable regression baselines rather than only raw combat logs.

---

[ ] (checkbox) - [Task 5] - Add scenario-regression and balance-signal tests

[Task Description]
Lock the Milestone 6 contract with deterministic scenario-regression tests so later tuning and feature work cannot silently corrupt common combat patterns.

[Task technical implementation]
Add exact tests for the arena and regression layer.

### Arena contract tests

Add test coverage for:

- deterministic repeated execution,
- correct scenario stop-condition handling,
- structured metric generation,
- baseline comparison behavior.

### Core scenario regression tests

Add test coverage for:

- faster ranged vs slower melee pattern,
- faster melee vs slower ranged pattern,
- equal-speed ranged vs melee loop/stall behavior,
- one elite vs many weak pattern,
- AoE vs clumping pattern,
- chokepoint vs open-field difference pattern.

### Suggested test groups

- `tests/arena/test_arena_harness_contract.py`
- `tests/arena/test_core_scenario_regression.py`
- `tests/arena/test_balance_signal_metrics.py`

These tests should assert:

- deterministic scenario execution,
- stable regression signals,
- and preserved behavior patterns,
  not final balance perfection.

[Task possible affected files]

- new arena harness test modules
- new scenario-regression test modules
- new balance-signal metric test modules

[Task important notes]
Do not turn these into full release-balance approval tests.
Do not use exact HP-by-turn equality as the default regression oracle.

These are scenario-regression tests and balance-signal tests.

[Task check list]

- [ ] Add deterministic harness tests
- [ ] Add stop-condition tests
- [ ] Add structured-metric tests
- [ ] Add core scenario regression tests
- [ ] Add stall / timeout pattern tests
- [ ] Add chokepoint vs open-field tests
- [ ] Add balance-signal tests

[Task acceptance criteria]
The arena harness and scenario matrix are pinned by deterministic scenario-regression tests and stable balance-signal tests.

---

[ ] (checkbox) - [Task 6] - Add exact Milestone 6 documentation pack

[Task Description]
Document the complete Milestone 6 contract so later balancing and regression work cannot reinterpret scenario semantics informally.

[Task technical implementation]
Create:

- `docs/combat/arena_harness_rulebook_m6.md`
- `docs/combat/arena_scenario_matrix_m6.md`
- `docs/combat/arena_regression_m6_test_matrix.md`

`arena_harness_rulebook_m6.md` must contain these exact sections:

- Purpose
- Arena-harness boundaries
- Real-runtime execution semantics
- Determinism semantics
- Scenario contract
- Outcome-pattern semantics
- Metric semantics
- Regression-baseline semantics
- Non-goals
- Determinism rules

`arena_scenario_matrix_m6.md` must contain these exact sections:

- Core 1v1 scenarios
- Core 1v many scenarios
- Core many-vs-many scenarios
- Open-field variants
- Chokepoint variants
- For each scenario:
  - participant setup
  - terrain/setup summary
  - stop condition
  - expected pattern type

`arena_regression_m6_test_matrix.md` must contain these exact sections:

- Harness contract tests
- Determinism tests
- Stop-condition tests
- Metric tests
- Core scenario regression tests
- Stall / timeout regression tests
- Balance-signal tests

For every test group, document:

- test name or group name,
- input condition,
- expected regression or metric rule,
- regression caught.

[Task possible affected files]

- `docs/combat/arena_harness_rulebook_m6.md`
- `docs/combat/arena_scenario_matrix_m6.md`
- `docs/combat/arena_regression_m6_test_matrix.md`

[Task important notes]
Documentation is part of implementation in this milestone.
Do not defer it.

This milestone exists to stop scenario-regression behavior from living only in code and memory.

[Task check list]

- [ ] Document exact arena-harness rules
- [ ] Document exact scenario matrix
- [ ] Document metric semantics
- [ ] Document regression-baseline semantics
- [ ] Document exact non-goals
- [ ] Document determinism expectations
- [ ] Document regression test groups and purpose

[Task acceptance criteria]
Milestone 6 has a complete exact arena-harness rulebook, scenario-matrix document, and regression test-matrix document that match the implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop treating balance and combat feel as things you can judge by memory or a few hand-run fights. In Milestone 6, scenario validation becomes an explicit system.

What actions must be taken immediately
Freeze the arena contract, implement deterministic real-runtime scenario execution, define the core scenario matrix, add structured metrics and regression baselines, and pin everything with deterministic scenario-regression tests.

What must stop or be eliminated
Stop relying on ad hoc play impressions as the only truth surface. Stop building fake simplified harnesses. Stop expecting exact transcript equality to be the right regression oracle for high-level combat behavior.

The consequences and opportunity cost if this fails
Milestone 7 and later will try to tune and maintain the overhaul without a trustworthy scenario-validation surface, and every balance discussion will collapse into opinion fights instead of controlled evidence.
