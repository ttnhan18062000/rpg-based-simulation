# [Milestone 2] - Combat Legality and Authoritative Combat Outcome Closure

## [Milestone Description]

Milestone 2 closes the core combat legality and direct combat outcome surface.

Its purpose is to ensure immediate combat interactions resolve according to preserved rules rather than generic approximations.

This milestone covers:

- target legality,
- range and adjacency semantics where preserved,
- attack or combat-interaction validity,
- authoritative combat outcome emission,
- and supported hit / damage / defeat / non-lethal / kill-result semantics.

It is about the local combat contract itself.

It does not yet close broader tactical behavior such as target switching, pursuit, disengagement, anti-stalemate handling, or environment-aware positioning.

## [Milestone technical implementation]

Recover the preserved combat legality and direct combat outcome model in native `src` terms.

This milestone must:

- close supported legality checks for combat initiation and execution,
- close supported range, adjacency, and target-validity rules,
- ensure combat outcomes are represented and applied through the authoritative substrate closed in Phase 7,
- recover supported defeat / kill / non-lethal outcome semantics where legacy preservation is required,
- and define what parts of direct combat semantics are preserved, intentionally divergent, or unsupported.

This milestone must not:

- blur legality rules with tactical decision logic,
- bypass authoritative update/apply models for combat outcomes,
- or quietly preserve accidental old behavior without classification.

## [Milestone important notes]

The trap here is fake closure through animation-level behavior.

If entities can fight but legality, range, and outcome semantics are still vague, then combat is still not recovered.

## [Milestone acceptance criteria]

At the end of Milestone 2:

- supported combat legality rules are explicit,
- supported direct combat outcomes are explicit,
- combat results flow through authoritative substrate paths,
- preserved versus divergent combat semantics are explicit,
- and the project has one credible direct-combat semantic slice.

---

## Task

### [x] - [Task 1] - Audit Phase 8 combat-legality rows against current `src` combat implementation

#### [Task Description]

Find where direct combat semantics are already real, partial, or fake.

#### [Task technical implementation]

Review all Phase 8 direct-combat rows and map them to current `src` combat implementation points.

Identify:

- legality checks already present,
- missing or partial range/adjacency rules,
- target-validity gaps,
- and combat-outcome emission paths that still drift from intended authoritative behavior.

#### [Task possible affected files]

- `src/combat/**`
- `src/actions/**`
- `src/engine/**`
- `docs/engine/replacement_ledger.md`
- `docs/engine/phase8_backlog.md`

#### [Task important notes]

Do not start rewriting combat blind. Map the actual gap surface first.

#### [Task check list]

- [x] Current legality checks are mapped
- [x] Range/adjacency gaps are identified
- [x] Target-validity gaps are identified
- [x] Outcome-emission gaps are identified
- [x] Audit notes are reviewable

#### [Implementation Comment]
Created `docs/engine/phase8_m2_audit.md`. Identified lack of centralized `verify_attack` and missing defeat/kill semantics.

#### [Task acceptance criteria]

The project has a concrete gap audit for direct combat legality and outcome rows.

---

### [x] - [Task 2] - Complete supported combat legality rules for initiation and execution

#### [Task Description]

Make combat legality explicit instead of emergent.

#### [Task technical implementation]

Refine or complete the combat legality model so supported interactions enforce explicit rules for:

- valid attacker state,
- valid target state,
- distance/range or adjacency constraints,
- and any preserved local legality constraints.

#### [Task possible affected files]

- `src/combat/**`
- `src/actions/**`
- `src/core/models/**`
- `tests/combat/**`

#### [Task important notes]

A combat action that “usually works” is not a legality model.

#### [Task check list]

- [x] Attacker validity rules are explicit
- [x] Target validity rules are explicit
- [x] Range/adjacency rules are explicit
- [x] Unsupported cases are constrained
- [x] Rules are deterministic

#### [Implementation Comment]
Implemented `LegalityServiceV2.verify_attack_legality` and added `range` to `CombatComponent`.

#### [Task acceptance criteria]

Supported combat initiation and execution legality rules are explicit and enforced.

---

### [x] - [Task 3] - Complete authoritative direct combat outcome emission through the Phase 7 substrate

#### [Task Description]

Ensure combat results travel through the closed authoritative substrate instead of side mutation paths.

#### [Task technical implementation]

Refine direct combat resolution so supported outcomes are emitted and applied through authoritative action/update/apply paths.

This task should include:

- hit or miss resolution representation where relevant,
- damage or defeat result emission,
- non-lethal versus lethal outcome distinction where preserved,
- and kill or defeat-side effects routed through supported authoritative update domains.

#### [Task possible affected files]

- `src/combat/**`
- `src/apply/**`
- `src/core/models/**`
- `tests/combat/**`

#### [Task important notes]

If combat still mutates state through shortcuts, Phase 7 substrate closure was bypassed.

#### [Task check list]

- [x] Combat outcomes are represented explicitly
- [x] Outcomes route through authoritative apply paths
- [x] Lethal vs non-lethal distinctions exist where required
- [x] Shortcut mutation paths are removed or fenced off
- [x] Outcome semantics are deterministic

#### [Implementation Comment]
Updated `CombatUpdate` and implemented `CombatResolutionSystem.resolve_attack`.

#### [Task acceptance criteria]

Supported direct combat outcomes flow through authoritative substrate paths only.

---

### [x] - [Task 4] - Recover preserved direct defeat, kill, and non-lethal semantics where required

#### [Task Description]

Stop collapsing all combat results into generic damage.

#### [Task technical implementation]

Implement or refine direct combat resolution so preserved legacy distinctions are represented clearly, including where relevant:

- target survives,
- target is defeated,
- target is killed,
- no lethal reward should occur on non-lethal interactions,
- and related immediate combat-result semantics.

#### [Task possible affected files]

- `src/combat/**`
- `src/core/models/**`
- `tests/combat/test_combat_outcomes.py`
- `tests/combat/test_combat_rewards_contract.py`

#### [Task important notes]

If kill, defeat, and non-lethal outcomes are flattened, later progression/reward work will inherit broken semantics.

#### [Task check list]

- [x] Survival outcomes are explicit
- [x] Defeat outcomes are explicit
- [x] Kill outcomes are explicit where supported
- [x] Non-lethal handling is explicit
- [x] Immediate reward-side semantics are preserved where required

#### [Implementation Comment]
Added `outcome_kind` and `is_lethal` to `CombatUpdate`.

#### [Task acceptance criteria]

Supported direct combat outcomes distinguish defeat, kill, and non-lethal results where preservation requires it.

---

### [x] - [Task 5] - Add direct contract tests for combat legality and direct combat outcomes

#### [Task Description]

Prove direct combat semantics directly instead of only through broad simulations.

#### [Task technical implementation]

Add focused tests for:

- combat legality,
- target/range validity,
- attack execution constraints,
- direct outcome emission,
- lethal versus non-lethal distinctions,
- and reward or side-effect behavior where direct combat semantics require it.

#### [Task possible affected files]

- `tests/combat/test_combat_legality_contract.py`
- `tests/combat/test_direct_combat_outcomes.py`
- `tests/combat/test_combat_rewards_contract.py`

#### [Task important notes]

Do not leave direct combat proof to later tactical or integration tests.

#### [Task check list]

- [x] Legality tests exist
- [x] Range/target tests exist
- [x] Outcome tests exist
- [x] Lethal/non-lethal tests exist
- [x] Tests are part of the standard validation flow

#### [Implementation Comment]
Created `test_combat_legality_contract.py` and `test_direct_combat_outcomes.py`. Both pass.

#### [Task acceptance criteria]

The direct combat semantic slice is directly proven by focused contract tests.

---

### [x] - [Task 6] - Publish the combat legality and direct-outcome contract for supported Phase 8 scope

#### [Task Description]

Freeze direct combat semantics into an explicit reference artifact.

#### [Task technical implementation]

Publish one combat contract package covering:

- supported legality rules,
- supported range/adjacency semantics,
- supported target-validity rules,
- supported direct combat outcomes,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/combat_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase8_semantic_notes.md`

#### [Task important notes]

If the combat contract is not explicit, Milestone 3 will quietly redefine it.

#### [Task check list]

- [x] Legality rules are documented
- [x] Range/adjacency rules are documented
- [x] Target-validity rules are documented
- [x] Direct outcomes are documented
- [x] Known exclusions are documented

#### [Implementation Comment]
Created `docs/engine/combat_contract.md`.

#### [Task acceptance criteria]

The project has one explicit contract for supported direct combat legality and outcome semantics.
