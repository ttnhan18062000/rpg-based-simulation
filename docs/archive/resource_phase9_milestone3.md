---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 3] - Blockers, Leads, Knowledge Continuity, and Resource Intelligence Closure

## [Milestone Description]

Milestone 3 closes the knowledge-and-resource intelligence layer that turns strategic lack into directed future behavior.

Its purpose is to recover how actors recognize missing needs, preserve blockers, use leads, resolve knowledge gaps, and update strategic state over time without cheating.

This milestone covers:

- blocker generation and persistence,
- blocker resolution,
- lead creation, testing, retention, and suppression,
- knowledge continuity across ticks,
- source trust and certainty handling where preserved,
- and resource-intelligence behavior that sits above local action and below broader social meaning.

It is not a repetition of Phase 5’s bounded resource loop. It is the long-horizon intelligence layer built on top of it.

## [Milestone technical implementation]

Recover the supported blocker/lead/knowledge-intelligence layer in a way that is deterministic, bounded, and faithful to the preserved replacement surface.

This milestone must:

- recover supported blocker generation and persistence semantics,
- recover supported blocker-resolution logic tied to acquisitions and state change,
- recover supported lead retention, testing, suppression, and continuity behavior,
- recover supported uncertainty/anti-cheating rules where preservation is required,
- and keep the knowledge layer bounded rather than turning it into a perfect-information planner.

This milestone must not:

- duplicate Phase 5’s direct resource-resolution logic,
- duplicate Phase 8’s local-world semantics,
- absorb broader social contract meaning that belongs to the next milestone,
- or allow internal perfect state to silently override bounded knowledge surfaces.

## [Milestone important notes]

The trap here is silent cheating.

The easiest way to make this phase look good is to let actors know too much. That is exactly what this phase must prevent.

## [Milestone acceptance criteria]

At the end of Milestone 3:

- blocker and lead semantics are explicit,
- persistence and resolution behavior are explicit where supported,
- uncertainty and anti-cheating behavior are explicit where supported,
- resource intelligence remains bounded and long-horizon,
- and the project has one credible blocker/lead/knowledge slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit blocker, lead, and knowledge-continuity rows against current `src` intelligence behavior

#### [Task Description]

Find where long-horizon resource intelligence is already real, partial, or fake.

#### [Task technical implementation]

Review all Phase 9 blocker/lead/knowledge rows and map them to current `src` implementation points.

Identify:

- blocker generation already present,
- blocker persistence/resolution behavior already present,
- lead retention/testing/suppression behavior already present,
- uncertainty/trust metadata already present,
- and where resource intelligence still leaks perfect internal state.

#### [Task possible affected files]

- `src/strategic/**`
- `src/systems/strategic/**`
- `src/core/strategic/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Do not start “smartening” this layer before you know where cheating already exists.

#### [Task check list]

- [ ] Blocker behavior is mapped
- [ ] Lead behavior is mapped
- [ ] Knowledge continuity is mapped
- [ ] Anti-cheating gaps are identified
- [ ] Audit notes are reviewable

#### [Task acceptance criteria]

The project has a concrete gap audit for blocker/lead/knowledge rows.

---

### [ ] (checkbox) - [Task 2] - Complete supported blocker generation, persistence, and resolution semantics

#### [Task Description]

Make strategic lack explicit and persistent across time.

#### [Task technical implementation]

Implement or refine supported blocker behavior so actors can:

- generate blockers when required conditions are missing,
- preserve blockers across ticks,
- resolve blockers when material state changes justify it,
- and keep blocker semantics bounded and explicit.

#### [Task possible affected files]

- `src/systems/strategic/**`
- `src/core/strategic/**`
- `tests/contract/test_resource_intelligence_contract.py`
- `tests/strategy/**`

#### [Task important notes]

A blocker that appears once and is forgotten is not long-horizon intelligence.

#### [Task check list]

- [ ] Generation rules are explicit
- [ ] Persistence rules are explicit
- [ ] Resolution rules are explicit
- [ ] State-change linkage is explicit
- [ ] Behavior remains bounded

#### [Task acceptance criteria]

Supported blocker generation, persistence, and resolution semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 3] - Complete supported lead creation, testing, retention, and suppression behavior

#### [Task Description]

Recover how actors manage possible future knowledge without becoming omniscient.

#### [Task technical implementation]

Implement or refine supported lead semantics so actors can:

- retain candidate leads,
- test leads,
- suppress already-tested or exhausted leads,
- preserve lead continuity across ticks,
- and keep retention bounded by explicit capacity rules.

#### [Task possible affected files]

- `src/strategic/**`
- `src/core/strategic/**`
- `tests/strategy/**`
- `tests/integration/strategy/**`

#### [Task important notes]

Leads are not the same thing as perfect coordinates or guaranteed facts.

#### [Task check list]

- [ ] Lead retention rules are explicit
- [ ] Lead testing rules are explicit
- [ ] Lead suppression rules are explicit
- [ ] Cross-tick continuity is explicit
- [ ] Capacity bounds are enforced

#### [Task acceptance criteria]

Supported lead creation/testing/retention/suppression behavior is explicit and bounded.

---

### [ ] (checkbox) - [Task 4] - Recover supported uncertainty, source-trust, and anti-cheating semantics

#### [Task Description]

Prevent resource intelligence from becoming a perfect-information cheat layer.

#### [Task technical implementation]

Implement or refine supported uncertainty semantics, including where preserved:

- certainty differences between rumor and direct knowledge,
- source-trust recalibration,
- vague or partial lead detail,
- and anti-cheating rules that prevent actors from deriving exact truth they have not earned.

#### [Task possible affected files]

- `src/strategic/**`
- `src/core/strategic/**`
- `tests/integration/strategy/**`
- uncertainty docs

#### [Task important notes]

If actors always know where to go, this phase is lying about intelligence.

#### [Task check list]

- [ ] Certainty rules are explicit
- [ ] Source-trust rules are explicit
- [ ] Vague/partial lead rules are explicit
- [ ] Anti-cheating rules are explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported uncertainty/source-trust/anti-cheating semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 5] - Add direct contract and integration tests for blocker/lead/knowledge continuity behavior

#### [Task Description]

Prove long-horizon resource intelligence directly.

#### [Task technical implementation]

Add focused tests for:

- blocker generation and persistence,
- blocker resolution on acquisition,
- lead retention and suppression,
- tested-lead persistence,
- uncertainty and anti-cheating behavior,
- and trust recalibration where supported.

#### [Task possible affected files]

- `tests/strategy/**`
- `tests/integration/strategy/**`
- `tests/contract/test_resource_intelligence_contract.py`

#### [Task important notes]

Do not leave this proof hidden inside broad “integrated loop” tests alone.

#### [Task check list]

- [ ] Blocker tests exist
- [ ] Lead tests exist
- [ ] Persistence tests exist
- [ ] Anti-cheating tests exist
- [ ] Trust/uncertainty tests exist

#### [Task acceptance criteria]

The supported blocker/lead/knowledge slice is directly proven by focused tests.

---

### [ ] (checkbox) - [Task 6] - Publish the blocker/lead/knowledge-intelligence contract for supported Phase 9 scope

#### [Task Description]

Freeze long-horizon resource intelligence into one explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- supported blocker semantics,
- supported lead semantics,
- supported knowledge continuity rules,
- supported uncertainty/trust/anti-cheating rules,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/resource_intelligence_contract.md`
- `docs/engine/knowledge_continuity_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase9_semantic_notes.md`

#### [Task important notes]

If this contract is not explicit, later social or compatibility work will quietly rewrite it.

#### [Task check list]

- [ ] Blocker rules are documented
- [ ] Lead rules are documented
- [ ] Knowledge continuity rules are documented
- [ ] Uncertainty/trust rules are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit contract for supported blocker/lead/knowledge-intelligence semantics.
