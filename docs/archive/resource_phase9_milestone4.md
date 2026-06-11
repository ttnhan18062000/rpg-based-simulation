---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 4] - Social Consequence, Contracts, Trust, and Recruitment Closure

## [Milestone Description]

Milestone 4 closes the social meaning layer.

Its purpose is to recover how social memory, betrayal, trust, debt, contracts, and recruitment consequences shape future behavior rather than remaining isolated narrative artifacts.

This milestone covers:

- betrayal and social trauma consequences,
- trust/debt/reputation effects where preserved,
- recruitment and contract semantics,
- candidate filtering and alliance-related decision surfaces,
- and social state transitions that materially affect long-horizon behavior.

It does not close progression math, class identity, or reward formulas.

## [Milestone technical implementation]

Recover the supported social consequence and contract layer in native `src` terms.

This milestone must:

- recover supported betrayal-memory and social consequence semantics,
- recover supported recruitment-offer evaluation consequences,
- recover supported trust/debt/relationship effects where preservation is required,
- recover contract-related long-horizon semantics that materially affect strategic choice,
- and define the supported social boundary explicitly rather than leaving it implied.

This milestone must not:

- absorb broad economy or compatibility scope,
- reduce social meaning to generic mood modifiers,
- hide missing social semantics behind narrative wording,
- or treat stored memory as closure unless it actually affects future choice.

## [Milestone important notes]

The trap here is fake richness.

A few memory flags are not social consequence closure. What matters is whether those records change future strategic and contract behavior in preserved ways.

## [Milestone acceptance criteria]

At the end of Milestone 4:

- supported social consequence semantics are explicit,
- supported contract/recruitment semantics are explicit,
- trust/debt/reputation effects are explicit where supported,
- preserved versus divergent social semantics are explicit,
- and the project has one credible social/contract slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit social-consequence and contract rows against current `src` social behavior

#### [Task Description]

Find where social memory is already meaningful, partial, or decorative.

#### [Task technical implementation]

Review all Phase 9 social/contract rows and map them to current `src` implementation points.

Identify:

- betrayal or trauma memory already present,
- recruitment/offer evaluation already present,
- trust/debt/reputation effects already present,
- candidate filtering already present,
- and places where social state is stored but not behaviorally meaningful.

#### [Task possible affected files]

- `src/social/**`
- `src/strategic/**`
- `src/core/social/**`
- `docs/engine/replacement_ledger.md`

#### [Task important notes]

Stored social memory without behavioral consequence is fake closure.

#### [Task check list]

- [ ] Betrayal-memory behavior is mapped
- [ ] Recruitment behavior is mapped
- [ ] Trust/debt effects are mapped
- [ ] Candidate filtering is mapped
- [ ] Decorative social state is identified

#### [Task acceptance criteria]

The project has a concrete gap audit for social/contract rows.

---

### [ ] (checkbox) - [Task 2] - Recover supported betrayal-memory and social-consequence semantics

#### [Task Description]

Make painful social history alter future choices where preservation requires it.

#### [Task technical implementation]

Implement or refine supported social consequence behavior so preserved long-horizon effects can occur, including where relevant:

- betrayal trauma affecting later recruitment,
- remembered hostile or harmful social history,
- social caution or refusal tied to preserved records,
- and bounded persistence of those consequences across time.

#### [Task possible affected files]

- `src/social/**`
- `src/strategic/**`
- `tests/ai/**`
- `tests/social/**`

#### [Task important notes]

If betrayal exists only as flavor text, this milestone is not done.

#### [Task check list]

- [ ] Betrayal-memory rules are explicit
- [ ] Behavioral consequences are explicit
- [ ] Cross-time persistence is explicit
- [ ] Boundedness is explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported betrayal-memory and social-consequence semantics are explicit and behaviorally meaningful.

---

### [ ] (checkbox) - [Task 3] - Recover supported recruitment, contract, and candidate-filtering semantics

#### [Task Description]

Make social offers and contracts materially affect long-horizon choice.

#### [Task technical implementation]

Implement or refine supported recruitment/contract semantics so actors can:

- evaluate offers under preserved rules,
- accept or decline based on preserved conditions,
- filter candidates using supported social criteria,
- and carry contract-related effects into strategic behavior where required.

#### [Task possible affected files]

- `src/social/**`
- `src/strategic/**`
- `src/core/social/**`
- `tests/social/**`
- `tests/ai/**`

#### [Task important notes]

A contract record that does not alter future decision-making is paperwork, not gameplay semantics.

#### [Task check list]

- [ ] Offer-evaluation rules are explicit
- [ ] Accept/decline rules are explicit
- [ ] Candidate-filtering rules are explicit
- [ ] Contract effects are explicit where supported
- [ ] Behavior remains bounded

#### [Task acceptance criteria]

Supported recruitment/contract/candidate-filtering semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 4] - Recover supported trust, debt, and relationship effects where preserved

#### [Task Description]

Make social state materially alter long-horizon strategic and contract choices.

#### [Task technical implementation]

Implement or refine supported trust/debt/relationship semantics, including where preserved:

- trust shifts based on interactions or outcomes,
- debt-related filtering or preference behavior,
- relationship effects on candidate selection or cooperation,
- and explicit bounded persistence of those effects.

#### [Task possible affected files]

- `src/social/**`
- `src/core/social/**`
- `tests/social/**`
- `tests/integration/strategy/**`

#### [Task important notes]

Do not let this degrade into generic mood numbers with no consequence.

#### [Task check list]

- [ ] Trust rules are explicit
- [ ] Debt rules are explicit
- [ ] Relationship effects are explicit
- [ ] Bounded persistence is explicit
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported trust/debt/relationship semantics are explicit and behaviorally meaningful.

---

### [ ] (checkbox) - [Task 5] - Add direct contract and integration tests for social consequence and contracts

#### [Task Description]

Prove social meaning directly instead of assuming it from narrative data.

#### [Task technical implementation]

Add focused tests for:

- betrayal-memory consequences,
- recruitment acceptance/decline behavior,
- trust/debt effects,
- candidate filtering,
- and contract-related long-horizon behavior.

#### [Task possible affected files]

- `tests/social/**`
- `tests/ai/**`
- `tests/integration/strategy/**`

#### [Task important notes]

Do not leave social proof to broad simulation runs that are hard to diagnose.

#### [Task check list]

- [ ] Betrayal-consequence tests exist
- [ ] Recruitment tests exist
- [ ] Trust/debt tests exist
- [ ] Candidate-filtering tests exist
- [ ] Contract-behavior tests exist

#### [Task acceptance criteria]

The supported social/contract slice is directly proven by focused tests.

---

### [ ] (checkbox) - [Task 6] - Publish the social consequence and contract contract for supported Phase 9 scope

#### [Task Description]

Freeze social meaning into one explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- supported social memory rules,
- supported betrayal/trust/debt semantics,
- supported recruitment and contract semantics,
- supported candidate-filtering rules,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/social_consequence_contract.md`
- `docs/engine/contract_semantics_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase9_semantic_notes.md`

#### [Task important notes]

If the contract is not explicit, later progression or compatibility work will quietly distort it.

#### [Task check list]

- [ ] Social-memory rules are documented
- [ ] Trust/debt rules are documented
- [ ] Recruitment rules are documented
- [ ] Contract rules are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit contract for supported social consequence and contract semantics.
