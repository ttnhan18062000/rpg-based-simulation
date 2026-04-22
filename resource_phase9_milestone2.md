# [Milestone 2] - Strategic Continuity, Bounded Cognition, and Explainability Closure

## [Milestone Description]

Milestone 2 closes the long-horizon strategic continuity layer and the bounded cognition layer that supports it.

Its purpose is to recover the part of the game where actors behave like they have limited minds with persistent priorities, bounded attention, and explainable continuity across ticks.

This milestone covers:

- project continuity and switching,
- interruption resistance,
- bounded active-slice logic,
- bounded concern intake and lead retention,
- cognition-capacity derivation,
- overload/explainability surfaces,
- and strategic continuity rules that persist across ticks.

It is about bounded mind and continuity, not local tactical combat behavior.

It does not yet close blocker/lead knowledge continuity, social consequence, or progression math itself.

## [Milestone technical implementation]

Recover the supported strategic continuity and cognition layer in native `src_v2` terms.

This milestone must:

- recover supported strategic continuity behavior across ticks,
- recover bounded cognition-capacity rules and deterministic profile derivation,
- recover interruption, abandonment, and switch/retention semantics where preservation is required,
- recover explainability metadata where the legacy surface requires it,
- and keep the cognition layer bounded rather than turning it into an uncontrolled planner.

This milestone must not:

- absorb local tactical logic already owned by Phase 8,
- absorb blocker/lead resolution specifics owned by the next milestone,
- absorb social consequence or progression logic owned by later milestones,
- or hide missing semantics behind vague “AI improvement” language.

## [Milestone important notes]

The trap here is pretending that better local behavior implies strategic continuity.

It does not.

Phase 9 starts where local behavior ends and persistent bounded intention begins.

## [Milestone acceptance criteria]

At the end of Milestone 2:

- strategic continuity rules are explicit,
- bounded cognition-capacity rules are explicit,
- continuity across ticks is explicit where supported,
- explainability surfaces are explicit where supported,
- and the project has one credible long-horizon strategic/cognitive slice.

---

## Task

### [ ] (checkbox) - [Task 1] - Audit strategic continuity and cognition rows against current `src_v2` long-horizon behavior

#### [Task Description]

Find where long-horizon continuity is already real, partial, or fake.

#### [Task technical implementation]

Review all Phase 9 strategic/cognitive rows and map them to current `src_v2` implementation points.

Identify:

- project continuity logic already present,
- project-switch and retention semantics already present,
- bounded active-slice or concern-cap behavior already present,
- cognition-capacity derivation or explainability surfaces already present,
- and where continuity still collapses into local decision logic.

#### [Task possible affected files]

- `src_v2/strategic/**`
- `src_v2/ai/**`
- `src_v2/core/strategic/**`
- `docs/engine/replacement_ledger.md`
- `docs/engine/phase9_backlog.md`

#### [Task important notes]

Do not start “making agents smarter” before you know which continuity gaps are actually real.

#### [Task check list]

- [ ] Strategic continuity paths are mapped
- [ ] Switch/retention behavior is mapped
- [ ] Cognition-capacity behavior is mapped
- [ ] Explainability surfaces are mapped
- [ ] Audit notes are reviewable

#### [Task acceptance criteria]

The project has a concrete gap audit for strategic continuity and cognition rows.

---

### [ ] (checkbox) - [Task 2] - Complete supported project continuity, switch, and retention semantics across ticks

#### [Task Description]

Make long-horizon continuity explicit instead of emergent.

#### [Task technical implementation]

Refine or complete the strategic continuity model so supported actors can:

- retain current projects under preserved conditions,
- switch when preserved thresholds or pressures require it,
- preserve active-objective continuity where required,
- and abandon or suspend work in bounded, explicit ways.

#### [Task possible affected files]

- `src_v2/strategic/**`
- `src_v2/core/strategic/**`
- `tests_v2/strategy/**`

#### [Task important notes]

A strategic system that merely recomputes from scratch every tick is not continuity.

#### [Task check list]

- [ ] Retention rules are explicit
- [ ] Switch rules are explicit
- [ ] Suspension/abandonment rules are explicit
- [ ] Continuity across ticks is explicit
- [ ] Behavior remains bounded

#### [Task acceptance criteria]

Supported long-horizon project continuity and switching semantics are explicit and enforced.

---

### [ ] (checkbox) - [Task 3] - Complete bounded cognition-capacity and active-slice semantics

#### [Task Description]

Recover limited-mind behavior rather than unconstrained planning.

#### [Task technical implementation]

Implement or refine supported cognition-capacity logic so actors are bounded by explicit capacity rules, including where preserved:

- planning budget,
- active-slice limit,
- concern intake limit,
- lead retention limit,
- candidate or ally evaluation limits,
- interruption resistance,
- and overload behavior.

#### [Task possible affected files]

- `src_v2/ai/**`
- `src_v2/strategic/**`
- `src_v2/core/cognition/**`
- `tests_v2/ai/**`

#### [Task important notes]

If the system can think about everything, it is not a bounded cognition model.

#### [Task check list]

- [ ] Capacity limits are explicit
- [ ] Active-slice rules are explicit
- [ ] Intake/retention limits are explicit
- [ ] Interruption resistance is explicit
- [ ] Overload behavior is explicit where required

#### [Task acceptance criteria]

Supported cognition-capacity and active-slice behavior are explicit, bounded, and deterministic.

---

### [ ] (checkbox) - [Task 4] - Complete deterministic cognition-profile derivation and non-mutation guarantees

#### [Task Description]

Make cognition capacity derivation explicit and safe.

#### [Task technical implementation]

Refine or complete profile derivation so supported cognition-capacity profiles are:

- deterministic for the same entity state,
- independent of incidental tick state where preservation requires that,
- non-mutating to source attributes/caps/stamina,
- and returned as fresh profile objects where required.

#### [Task possible affected files]

- `src_v2/ai/**`
- `src_v2/core/cognition/**`
- `tests_v2/ai/**`

#### [Task important notes]

If deriving a cognition profile mutates source state, the system is lying about its own reasoning substrate.

#### [Task check list]

- [ ] Same-state derivation is deterministic
- [ ] Non-mutation is explicit
- [ ] Fresh object semantics are explicit where required
- [ ] Tick independence is explicit where required
- [ ] Tests cover preserved cases

#### [Task acceptance criteria]

Supported cognition-profile derivation is deterministic and non-mutating.

---

### [ ] (checkbox) - [Task 5] - Recover explainability and overload metadata where preserved

#### [Task Description]

Make long-horizon cognition observable without pretending it is omniscient.

#### [Task technical implementation]

Implement or refine supported explainability surfaces, including where preserved:

- overload reason metadata,
- continuity rationale,
- project-switch rationale,
- bounded capacity indicators,
- and other explicit explainability fields required by legacy behavior or proof surfaces.

#### [Task possible affected files]

- `src_v2/strategic/**`
- `src_v2/core/cognition/**`
- `tests_v2/ai/**`
- explainability docs

#### [Task important notes]

Explainability fields must reflect actual bounded logic, not decorative logging.

#### [Task check list]

- [ ] Overload metadata is explicit
- [ ] Continuity rationale is explicit
- [ ] Switch rationale is explicit
- [ ] Capacity indicators are explicit
- [ ] Decorative fields are avoided

#### [Task acceptance criteria]

Supported explainability and overload metadata are explicit and tied to real bounded logic.

---

### [ ] (checkbox) - [Task 6] - Add direct contract tests for strategic continuity, cognition capacity, and explainability

#### [Task Description]

Prove long-horizon continuity directly instead of only through broad runs.

#### [Task technical implementation]

Add focused tests for:

- project retention and switching,
- active-slice and concern/lead capacity bounds,
- deterministic cognition-profile derivation,
- non-mutation guarantees,
- interruption resistance and bounded continuity behavior,
- and explainability/overload metadata.

#### [Task possible affected files]

- `tests_v2/ai/test_bounded_strategic_slice.py`
- `tests_v2/ai/test_cognition_capacity_determinism.py`
- `tests_v2/ai/test_cognition_capacity_non_mutation.py`
- `tests_v2/ai/test_cognition_explainability.py`
- `tests_v2/strategy/**`

#### [Task important notes]

Do not leave strategic continuity proof hidden inside broad integration tests.

#### [Task check list]

- [ ] Continuity tests exist
- [ ] Capacity-bound tests exist
- [ ] Determinism tests exist
- [ ] Non-mutation tests exist
- [ ] Explainability tests exist

#### [Task acceptance criteria]

The supported strategic/cognitive slice is directly proven by focused contract tests.

---

### [ ] (checkbox) - [Task 7] - Publish the strategic continuity and cognition contract for supported Phase 9 scope

#### [Task Description]

Freeze long-horizon cognition semantics into one explicit reference artifact.

#### [Task technical implementation]

Publish one contract package covering:

- supported strategic continuity rules,
- supported cognition-capacity limits,
- supported project-switch/retention semantics,
- supported explainability fields,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/strategic_continuity_contract.md`
- `docs/engine/cognition_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase9_semantic_notes.md`

#### [Task important notes]

If the contract is not explicit, later milestones will quietly rewrite it.

#### [Task check list]

- [ ] Continuity rules are documented
- [ ] Capacity rules are documented
- [ ] Switch/retention rules are documented
- [ ] Explainability rules are documented
- [ ] Known exclusions are documented

#### [Task acceptance criteria]

The project has one explicit contract for supported strategic continuity and bounded cognition.
