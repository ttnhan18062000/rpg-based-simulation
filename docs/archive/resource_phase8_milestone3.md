# [Milestone 3] - Bounded Tactical Engagement and Local Decision Closure

## [Milestone Description]

Milestone 3 closes the bounded tactical behavior that sits on top of direct combat semantics.

Its purpose is to recover how actors behave in immediate conflict without widening into long-horizon strategy.

This milestone covers:

- target selection and local tactical prioritization,
- engage versus disengage behavior,
- pursuit, stickiness, and retreat behavior where preserved,
- anti-stalemate handling,
- and bounded tactical evaluation rules.

It does not close broader strategic continuity, social reasoning, or progression effects.

## [Milestone technical implementation]

Recover the supported bounded tactical layer in a deterministic, local, and Phase-7-compatible way.

This milestone must:

- recover supported target-selection and local tactical prioritization behavior,
- recover supported engagement/disengagement/pursuit rules,
- recover supported retreat or local fallback behavior where preservation is required,
- close anti-stalemate or local-combat deadlock handling where preserved,
- and keep the tactical evaluator bounded rather than turning it into an uncontrolled strategic planner.

This milestone must not:

- absorb long-horizon project/blocker/lead logic from Phase 9,
- redefine direct combat legality from Milestone 2,
- or hide tactical ambiguity behind a generic “AI improvement” label.

## [Milestone important notes]

The trap here is letting “AI” become a garbage bucket.

Phase 8 owns bounded local tactical behavior only.

## [Milestone acceptance criteria]

At the end of Milestone 3:

- bounded local tactical behavior is explicit,
- engage/disengage/pursuit/retreat behavior is explicit where supported,
- anti-stalemate behavior is explicit where supported,
- tactical logic remains bounded and local,
- and the project has a credible tactical behavior slice built on closed direct combat semantics.

---

## Task

### [x] - [Task 1] - Audit current tactical decision paths against Phase 8 bounded-tactical rows

#### [Task Description]

Map where local tactical behavior is real, partial, conflated with strategy, or missing.

#### [Task technical implementation]

Review local tactical decision paths and map them to the Phase 8 tactical row set.

Identify:

- local target-selection logic,
- engagement and disengagement triggers,
- pursuit or retreat behavior,
- deadlock or anti-stalemate handling,
- and places where tactical logic is still entangled with longer-horizon strategic reasoning.

#### [Task possible affected files]

- `src/ai/**`
- `src/combat/**`
- `src/engine/**`
- `docs/engine/replacement_ledger.md`
- `docs/engine/phase8_backlog.md`

#### [Task important notes]

If local tactics and long-horizon strategy are still mixed, the phase boundary is already broken.

#### [Task check list]

- [x] Tactical decision paths are mapped
- [x] Strategy leakage is identified
- [x] Engage/disengage logic is identified
- [x] Pursuit/retreat logic is identified
- [x] Audit notes are reviewable

#### [Implementation Comment]
Created `docs/engine/phase8_m3_audit.md`. Identified lack of centralized AI and mapped gaps to backlog rows.

#### [Task acceptance criteria]

The project has a concrete gap audit for bounded local tactical behavior.

---

### [x] - [Task 2] - Complete supported target-selection and local tactical prioritization behavior

#### [Task Description]

Make immediate tactical choices explicit and bounded.

#### [Task technical implementation]

Refine or complete local tactical decision logic so supported actors can:

- choose targets using explicit local criteria,
- prioritize immediate conflict-relevant options deterministically,
- and avoid relying on undefined or far-horizon strategic data.

#### [Task possible affected files]

- `src/ai/**`
- `src/combat/**`
- `tests/tactical/**`

#### [Task important notes]

Local tactical prioritization is not the same thing as strategic planning.

#### [Task check list]

- [x] Target-selection rules are explicit
- [x] Local prioritization rules are explicit
- [x] Deterministic tie-breaking exists where needed
- [x] Far-horizon strategy leakage is reduced
- [x] Supported behavior stays bounded

#### [Implementation Comment]
Implemented `TacticalDecisionSystem.select_best_target` with HP > Distance > ID priority.

#### [Task acceptance criteria]

Supported local target-selection and tactical prioritization behavior are explicit and bounded.

---

### [x] - [Task 3] - Complete engage, disengage, pursuit, stickiness, and retreat behavior where preserved

#### [Task Description]

Recover the immediate conflict behavior that makes combat feel coherent rather than random.

#### [Task technical implementation]

Refine or complete local tactical movement/commitment rules so supported actors can:

- choose whether to engage,
- disengage under preserved conditions,
- pursue when preserved semantics require it,
- retain local target commitment or stickiness where required,
- and retreat or fallback where required.

#### [Task possible affected files]

- `src/ai/**`
- `src/combat/**`
- `src/navigation/**`
- `tests/tactical/**`

#### [Task important notes]

If every combatant just oscillates or tunnels blindly, local tactics are still not recovered.

#### [Task check list]

- [x] Engage rules are explicit
- [x] Disengage rules are explicit
- [x] Pursuit rules are explicit
- [x] Stickiness rules are explicit where required
- [x] Retreat/fallback behavior is explicit where required

#### [Implementation Comment]
Implemented `evaluate_entity_intent` with retreat thresholds and stickiness radius.

#### [Task acceptance criteria]

Supported engage/disengage/pursuit/stickiness/retreat behavior is explicit and deterministic.

---

### [x] - [Task 4] - Recover anti-stalemate and local-combat deadlock handling where preserved

#### [Task Description]

Prevent immediate combat loops from degenerating into repetitive or broken local behavior.

#### [Task technical implementation]

Implement or refine bounded local anti-stalemate handling for preserved scenarios, such as:

- stuck engagement loops,
- futile repeated actions,
- local deadlock repositioning or fallback,
- and other preserved immediate-conflict stabilization behaviors.

#### [Task possible affected files]

- `src/ai/**`
- `src/combat/**`
- `tests/tactical/test_anti_stalemate.py`

#### [Task important notes]

Do not let this become a generic escape hatch for bad tactical design.
Keep it narrow and explicit.

#### [Task check list]

- [x] Local stalemate cases are identified
- [x] Supported anti-stalemate handling is explicit
- [x] Escape-hatch vagueness is avoided
- [x] Deterministic stabilization behavior exists
- [x] Tests cover preserved cases

#### [Implementation Comment]
Added `stale_ticks` tracking and `STALEMATE_BREAK` retreat behavior.

#### [Task acceptance criteria]

Supported anti-stalemate and local-combat deadlock handling are explicit and bounded.

---

### [x] - [Task 5] - Add direct contract tests for bounded tactical behavior

#### [Task Description]

Prove tactical behavior directly instead of letting it hide inside broad simulations.

#### [Task technical implementation]

Add focused tests for:

- local target selection,
- engage/disengage behavior,
- pursuit and retreat behavior,
- target stickiness where supported,
- and anti-stalemate/local deadlock handling.

#### [Task possible affected files]

- `tests/tactical/test_target_selection_contract.py`
- `tests/tactical/test_engagement_behavior.py`
- `tests/tactical/test_pursuit_and_retreat.py`
- `tests/tactical/test_anti_stalemate.py`

#### [Task important notes]

Do not rely on “it looks smarter in a run” as tactical proof.

#### [Task check list]

- [x] Target-selection tests exist
- [x] Engage/disengage tests exist
- [x] Pursuit/retreat tests exist
- [x] Stickiness tests exist where relevant
- [x] Anti-stalemate tests exist

#### [Implementation Comment]
Created comprehensive test suite in `tests/tactical/`. All tests pass.

#### [Task acceptance criteria]

The bounded local tactical slice is directly proven by focused contract tests.

---

### [x] - [Task 6] - Publish the bounded tactical engagement contract for supported Phase 8 scope

#### [Task Description]

Freeze local tactical behavior into one explicit reference artifact.

#### [Task technical implementation]

Publish one tactical contract package covering:

- supported target-selection rules,
- supported local prioritization rules,
- supported engage/disengage semantics,
- supported pursuit/retreat/stickiness semantics,
- supported anti-stalemate behavior,
- and known exclusions or divergences.

#### [Task possible affected files]

- `docs/engine/tactical_contract.md`
- `docs/engine/support_matrix.md`
- `docs/engine/phase8_semantic_notes.md`

#### [Task important notes]

If the tactical contract is not explicit, later phases will quietly rewrite it.

#### [Task check list]

- [x] Target-selection rules are documented
- [x] Engagement rules are documented
- [x] Pursuit/retreat/stickiness rules are documented
- [x] Anti-stalemate behavior is documented
- [x] Known exclusions are documented

#### [Implementation Comment]
Created `docs/engine/tactical_contract.md`.

#### [Task acceptance criteria]

The project has one explicit contract for supported bounded tactical behavior.
