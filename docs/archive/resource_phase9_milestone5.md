---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 5] - Progression, Classes, Skills, Attributes, and Rewards Closure

## [Milestone Description]

Milestone 5 closes the RPG progression layer.

Its purpose is to recover the math and progression semantics that make outcomes accumulate into character growth and class identity over time.

This milestone covers:

- level-up and advancement behavior,
- veterancy and training semantics,
- talents and breakthroughs,
- class and gear identity where preserved,
- skill scaling,
- attribute synergy,
- kill/reward emission semantics,
- and other progression math that materially affects long-horizon gameplay truth.

It is not local combat, and it is not compatibility plumbing.

## [Milestone technical implementation]

Recover the supported progression layer in a way that is deterministic, bounded, and explicit about preserved versus divergent behavior.

This milestone must:

- recover supported leveling, veterancy, and training behavior,
- recover supported talent/breakthrough and class/gear semantics,
- recover supported skill-scaling and attribute-synergy behavior,
- recover supported reward-emission semantics tied to authoritative apply behavior,
- and define what parts of progression math are preserved, intentionally divergent, or still unsupported.

This milestone must not:

- duplicate Phase 8’s local combat semantics,
- hide broken formulas behind broad “balance changes” language,
- defer reward/emission truth to a future unspecified phase,
- or flatten distinct progression surfaces into one generic XP system.

## [Milestone important notes]

The trap here is hand-wavy balance talk.

This phase is not about whether the numbers feel nice. It is about whether preserved progression truth has actually been recovered or explicitly diverged.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- supported progression semantics are explicit,
- supported class/skill/attribute semantics are explicit,
- supported reward-emission semantics are explicit,
- preserved versus divergent progression math is explicit,
- and the project has one credible progression slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit progression, class, skill, attribute, and reward rows against current `src` progression behavior

#### [Task Description]

Find where RPG growth semantics are already real, partial, or fake.

#### [Task technical implementation]

Review all Phase 9 progression rows and map them to current `src` implementation points.

Identify:

- leveling or advancement behavior already present,
- veterancy/training behavior already present,
- class/gear and talent/breakthrough behavior already present,
- skill scaling and attribute synergy already present,
- and reward-emission behavior that still depends on incomplete combat/apply semantics.

#### [Task possible affected files]

- `src/progression/**`
- `src/combat/**`
- `src/core/progression/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Do not start tuning formulas before you know which preserved formulas are actually missing.

#### [Task check list]

- [ ] Advancement behavior is mapped
- [ ] Veterancy/training behavior is mapped
- [ ] Class/gear behavior is mapped
- [ ] Skill/attribute behavior is mapped
- [ ] Reward-emission behavior is mapped

#### [Task acceptance criteria]

The project has a concrete gap audit for progression/class/skill/attribute/reward rows.

---

### [ ] (checkbox) - [Task 2] - Recover supported leveling, veterancy, and training semantics

#### [Task Description]

Make growth over time explicit and deterministic.

#### [Task technical implementation]

Implement or refine supported progression behavior so actors can:

- level up under preserved conditions,
- gain veterancy where preserved,
- train attributes or growth channels under preserved rules,
- and carry growth meaning forward deterministically.

#### [Task possible affected files]

- `src/progression/**`
- `src/core/progression/**`
- `tests/progression/**`

#### [Task important notes]

A generic XP counter is not the same thing as preserved progression semantics.

#### [Task check list]

- [ ] Level-up rules are explicit
- [ ] Veterancy rules are explicit
- [ ] Training rules are explicit
- [ ] Cross-time persistence is explicit
- [ ] Deterministic growth is preserved

#### [Task acceptance criteria]

Supported leveling, veterancy, and training semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 3] - Recover supported talents, breakthroughs, classes, and gear-identity semantics

#### [Task Description]

Make class identity and character specialization materially meaningful where preservation requires it.

#### [Task technical implementation]

Implement or refine supported class/gear/talent behavior, including where preserved:

- class-based tendencies,
- starting or preferred gear semantics,
- talent-driven training differences,
- breakthrough states and their explicit effects,
- and class-related long-horizon identity rules.

#### [Task possible affected files]

- `src/progression/**`
- `src/core/progression/**`
- `tests/progression/**`
- `tests/core/gameplay/**`

#### [Task important notes]

Do not let this collapse into generic stat buffs with class labels pasted on top.

#### [Task check list]

- [ ] Class rules are explicit
- [ ] Gear-identity rules are explicit
- [ ] Talent rules are explicit
- [ ] Breakthrough rules are explicit
- [ ] Long-horizon identity is explicit

#### [Task acceptance criteria]

Supported talents, breakthroughs, class semantics, and gear identity are explicit and enforced.

---

### [ ] (checkbox) - [Task 4] - Recover supported skill-scaling and attribute-synergy semantics

#### [Task Description]

Make the RPG math explicit where preservation requires it.

#### [Task technical implementation]

Implement or refine supported skill and attribute semantics, including where preserved:

- physical skill scaling,
- magical or elemental scaling where relevant,
- luck/perception synergy,
- loot or crit-related attribute effects,
- and other preserved attribute-based formula surfaces.

#### [Task possible affected files]

- `src/progression/**`
- `src/core/gameplay/**`
- `src/combat/**`
- `tests/progression/**`
- `tests/core/gameplay/**`

#### [Task important notes]

If this is left as hand-wavy “balance,” the phase is lying about preserved RPG math.

#### [Task check list]

- [ ] Skill-scaling rules are explicit
- [ ] Attribute-synergy rules are explicit
- [ ] Formula surfaces are explicit
- [ ] Deterministic computation is explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported skill-scaling and attribute-synergy semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 5] - Recover supported reward-emission semantics tied to authoritative apply behavior

#### [Task Description]

Make progression reward truth flow from authoritative outcomes, not narrative convenience.

#### [Task technical implementation]

Implement or refine supported reward-emission behavior so preserved outcomes such as kills or milestone events emit rewards through authoritative apply behavior rather than ad hoc side paths.

#### [Task possible affected files]

- `src/progression/**`
- `src/engine/apply/**`
- `src/combat/**`
- `tests/progression/**`
- `tests/combat/**`

#### [Task important notes]

If reward emission is detached from authoritative outcomes, later progression proof is contaminated.

#### [Task check list]

- [ ] Reward triggers are explicit
- [ ] Authoritative emit path is explicit
- [ ] Non-lethal vs lethal reward distinctions are explicit where required
- [ ] Milestone or growth rewards are explicit where required
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported reward-emission semantics are explicit and tied to authoritative outcomes.

---

### [ ] (checkbox) - [Task 6] - Add direct contract tests for progression, class identity, skill math, and rewards

#### [Task Description]

Prove RPG growth semantics directly instead of assuming them from longer runs.

#### [Task technical implementation]

Add focused tests for:

- level-up and training behavior,
- veterancy behavior,
- class/gear/talent/breakthrough behavior,
- skill scaling and attribute synergy,
- and reward emission tied to authoritative outcomes.

#### [Task possible affected files]

- `tests/progression/**`
- `tests/combat/**`
- `tests/core/gameplay/**`

#### [Task important notes]

Do not hide progression proof inside broad integration runs that are hard to diagnose.

#### [Task check list]

- [ ] Advancement tests exist
- [ ] Class/talent tests exist
- [ ] Skill/attribute tests exist
- [ ] Reward-emission tests exist
- [ ] Tests are part of standard validation flow

#### [Task acceptance criteria]

The supported progression slice is directly proven by focused contract tests.

---

### [ ] (checkbox) - [Task 7] - Publish the progression, class, skill, attribute, and reward contract for supported Phase 9 scope

#### [Task Description]

Freeze progression truth into one explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- supported progression semantics,
- supported class and gear identity semantics,
- supported skill-scaling and attribute-synergy semantics,
- supported reward-emission rules,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/progression_contract.md`
- `docs/engine/skill_attribute_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase9_semantic_notes.md`

#### [Task important notes]

If the contract is not explicit, later compatibility or cutover work will quietly simplify it.

#### [Task check list]

- [ ] Progression rules are documented
- [ ] Class/gear rules are documented
- [ ] Skill/attribute rules are documented
- [ ] Reward rules are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit contract for supported progression/class/skill/attribute/reward semantics.
