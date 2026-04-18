[Milestone 7] - Observability, Rollout Hardening, and Final Documentation

[Milestone Description]
Milestone 7 makes the overhaul inspectable, debuggable, and maintainable. Its purpose is **not** to add new combat mechanics anymore, and it is **not** to reopen the rulebook or rebalance the core formulas again. Its purpose is to expose the new combat and movement systems clearly enough that:

- developers can understand why entities behaved the way they did,
- regressions can be diagnosed without guesswork,
- rollout can be controlled safely,
- and the completed overhaul does not survive only as tribal knowledge.

This milestone exists because by this point the system already contains:

- the core spatial and timing rulebook,
- the combat interaction model,
- the movement model,
- the tactical behavior layer,
- the aftermath and stat-ownership layer,
- and the arena regression surface.

Without explicit observability and final documentation, all of that complexity becomes hard to trust and harder to maintain. The corrected high-level plan placed this milestone last on purpose: observability and rollout hardening should reflect stable system contracts, not shifting prototypes.

[Milestone technical implementation]
Create one exact observability contract and one exact rollout-hardening contract, then make the combat and movement overhaul expose enough runtime truth to be safely debugged, verified, and maintained.

This milestone must implement these exact concerns as one system:

### Observability rules

1. **Runtime inspection surface**
   - The system must expose enough structured runtime state to explain combat and movement behavior.
   - At minimum, observability must cover:
     - readiness and world-time state,
     - combat legality outcomes,
     - engagement / disengagement state,
     - pursuit and target-stickiness state where relevant,
     - movement intention,
     - route / local-step blockage reasons where relevant,
     - congestion-response outcomes,
     - tactical choice reasons at a bounded level,
     - persistent consequence state,
     - and balance-relevant derived-state summaries.

2. **Blocked-action explanation**
   - When an action or movement step is rejected, delayed, or redirected, the system must be able to expose a structured reason.
   - This reason must be bounded and inspectable rather than hidden in logs only.

3. **Stable explanation model**
   - Explanations must be deterministic for identical input state.
   - This milestone does **not** require perfect natural-language storytelling.
   - It does require stable, structured reasons that developers and future tools can consume.

4. **Observability boundary**
   - Observability must expose runtime truth.
   - It must not silently reconstruct or “repair” missing state by guessing from the outside.
   - If a state does not exist, the fix is to expose or model it properly, not fake it in the presenter.

### Rollout-hardening rules

5. **Feature-boundary control**
   - The overhaul must support controlled rollout boundaries for major completed system families where appropriate.
   - This milestone must make it possible to enable, disable, or isolate major behavior changes during stabilization without corrupting domain truth.

6. **Safe degradation**
   - If a completed feature family must be temporarily disabled or isolated during rollout, the behavior must degrade in a controlled and documented way.
   - This must not silently create contradictory rules.

7. **Regression visibility during rollout**
   - Arena and scenario-regression results from Milestone 6 must be usable as a rollout validation surface.
   - Rollout hardening must make it easy to detect whether enabling a feature family changed expected behavioral envelopes.

### Documentation completion rules

8. **Final documentation pack**
   - The overhaul must end with one coherent, maintainable documentation set, not scattered milestone fragments alone.
   - The final pack must unify:
     - the rulebook,
     - combat interaction semantics,
     - movement semantics,
     - tactical behavior semantics,
     - aftermath and stat ownership,
     - arena scenario matrix,
     - observability surface,
     - and rollout guidance.

9. **Documentation-integrity alignment**
   - Every documented surfaced field, explanation type, scenario baseline, and rollout control must correspond to real implementation.
   - Documentation must not drift ahead of code or behind it.

### Runtime boundaries

10. **What this milestone may change**

- presenter / inspector / debug-facing schema surfaces,
- structured explanation models,
- rollout/config boundaries,
- documentation structure,
- and documentation-integrity / observability tests.

11. **What this milestone must not do**

- no new combat legality rules,
- no new combat interaction mechanics,
- no new movement semantics,
- no new tactical AI systems,
- no new balance-formula changes unless required to fix a discovered contradiction in surfaced truth.

12. **Clean-code boundary**

- Observability remains separate from gameplay authority.
- Presenters and inspectors consume authoritative runtime state rather than inventing it.
- Rollout controls remain separate from design semantics.
- Documentation remains aligned with the real system rather than describing aspirational behavior.

[Milestone important notes]
The first trap in this milestone is building observability by scraping logs and calling that an explanation system. That is weak and unstable. Observability must consume structured runtime state.

The second trap is making rollout hardening an excuse for permanently hidden complexity. Feature boundaries should help stabilization, not turn the system into a maze of semi-supported modes.

The third trap is writing final documentation as a marketing summary. This milestone is not for pretty words. It is for exact maintenance-grade references.

The fourth trap is allowing presenter or inspector layers to become hidden truth reconstructors. If the runtime does not expose a needed state cleanly, fix the runtime boundary instead of faking insight in the UI/debug layer.

[Milestone acceptance criteria]
At the end of Milestone 7, the codebase has:

- one exact observability contract,
- one explicit structured explanation surface for combat and movement behavior,
- one explicit rollout-hardening and controlled-degradation model,
- one finalized overhaul documentation pack,
- one deterministic set of observability and documentation-integrity tests,
- and one stable maintenance surface that lets future work debug and tune the system without guesswork.

No new mechanics are required for Milestone 7 completion.

## Task

[x] (checkbox) - [Task 1] - Define the observability and rollout-hardening contracts

[Task Description]
Create the exact rule contracts for runtime inspection, explanation surfacing, rollout control, and documentation completion. This is the foundational modeling task for Milestone 7. Without it, explanations will remain ad hoc, rollout will remain risky, and documentation will drift into vague summaries.

[Task technical implementation]
Create one observability reference document and one rollout-hardening reference document that define exactly:

### Observability contract

- which runtime states must be inspectable,
- which blocked / redirected action reasons must be surfaced,
- which explanation classes exist,
- what determinism guarantees explanations must obey,
- and which layers are allowed to expose those states.

### Rollout-hardening contract

- which completed system families may have controlled rollout boundaries,
- how safe degradation works,
- how rollout validation uses regression baselines,
- and what kinds of toggles or isolation controls are allowed.

### Documentation contract

- what the final overhaul pack must contain,
- how milestone docs are unified,
- and how code-to-doc alignment is enforced.

### Non-goals

- no gameplay-authority logic in presenters,
- no log-scrape-only explanation model,
- no undocumented fallback behavior,
- no aspirational docs that outrun implementation.

[Task possible affected files]

- `docs/combat/observability_rulebook_m7.md`
- `docs/combat/rollout_hardening_rulebook_m7.md`
- presenter / inspector / debug schema modules
- rollout / configuration boundary modules

[Task important notes]
Do not define observability as “whatever logs already exist.”
Do not define rollout hardening as “toggle random pieces and hope.”

The contracts must be exact enough to drive implementation and tests.

[Task check list]

- [x] Define observability boundaries
- [x] Define required surfaced runtime states
- [x] Define blocked-action explanation classes
- [x] Define rollout-hardening boundaries
- [x] Define safe degradation expectations
- [x] Define final documentation-pack expectations
- [x] Define explicit non-goals
- [x] Keep both contracts exact and minimal

[Task acceptance criteria]
The project has one exact observability contract and one exact rollout-hardening contract that can be used as the authoritative source for implementation and tests.

---

[x] (checkbox) - [Task 2] - Implement structured runtime observability for combat and movement

[Task Description]
Expose enough authoritative runtime state to explain what happened in combat and movement without relying on hidden reconstruction.

[Task technical implementation]
Implement or centralize the structured runtime observability surface for at least:

1. **Time and turn state**
   - readiness state,
   - world-time progression state,
   - and action-eligibility state.

2. **Combat interaction state**
   - combat legality result,
   - engagement / disengagement state,
   - pursuit or target-stickiness state where relevant,
   - and blocked or redirected combat-action reasons where relevant.

3. **Movement state**
   - movement intention,
   - route-level state summary,
   - local-step blocked reason where relevant,
   - congestion-response outcome,
   - and no-progress / wait / yield / sidestep reason where relevant.

4. **Tactical state**
   - bounded tactical choice explanation,
   - such as safe-shot choice, retreat trigger, or maintained-distance choice where supported by prior milestones.

5. **Persistent consequence and derived-state summary**
   - injury / fatigue or equivalent consequence summary,
   - and relevant derived-state balance summaries if needed for debugging.

This task must surface authoritative state rather than reconstructing it externally.

[Task possible affected files]

- combat presenter / debug serialization module
- movement presenter / debug serialization module
- entity inspection / inspector output module
- structured explanation / reason model module
- combat and movement runtime state models

[Task important notes]
Do not dump every internal variable.
Do not expose only raw logs.

The goal is structured, bounded, developer-meaningful observability.

[Task check list]

- [x] Expose readiness and world-time state
- [x] Expose combat interaction state
- [x] Expose movement intention and blocked-step state
- [x] Expose congestion-response state
- [x] Expose bounded tactical reasoning state
- [x] Expose persistent consequence summary
- [x] Keep observability authoritative and structured

[Task acceptance criteria]
Combat and movement runtime behavior can be inspected through structured authoritative state rather than hidden assumptions or log digging.

---

[x] (checkbox) - [Task 3] - Implement blocked-action and redirection explanation semantics

[Task Description]
Make rejections, delays, redirects, and forced responses explainable in a deterministic, bounded way.

[Task technical implementation]
Implement one explicit explanation model for at least:

1. **Blocked movement**
   - occupied tile,
   - invalid route segment,
   - congestion response,
   - wait / yield / sidestep reason,
   - or no-progress suppression reason.

2. **Blocked combat**
   - failed legality gate,
   - disengagement consequence,
   - interaction-state restriction,
   - or tactical redirection cause where applicable.

3. **Redirection semantics**
   - when the system changes an intended action into a different legal action class or response,
   - the reason must be surfaced explicitly.

4. **Deterministic reason ordering**
   - when multiple candidate reasons exist,
   - explanation selection must be deterministic.

This model does **not** require polished narrative prose. It requires stable structured reason categories and payloads.

[Task possible affected files]

- structured reason / explanation model module
- combat blocked-action serialization
- movement blocked-action serialization
- inspector / debug-facing reason renderer

[Task important notes]
Do not reduce explanations to free-form strings only.
Do not let explanation selection vary nondeterministically.

The system needs machine-stable and human-readable bounded reasons.

[Task check list]

- [x] Add blocked-movement reason model
- [x] Add blocked-combat reason model
- [x] Add redirection reason model
- [x] Add deterministic reason ordering
- [x] Keep explanation output structured
- [x] Avoid string-only hidden semantics

[Task acceptance criteria]
Blocked or redirected combat and movement behavior surfaces deterministic structured reasons rather than ambiguous logs or guesswork.

---

[x] (checkbox) - [Task 4] - Implement rollout boundaries and safe degradation controls

[Task Description]
Make the overhaul safe to stabilize and deploy by defining controlled boundaries for completed feature families.

[Task technical implementation]
Implement one explicit rollout-hardening layer that supports:

1. **Controlled feature-family boundaries**
   - major completed system families may be isolated or toggled at rollout boundaries where appropriate.

2. **Safe degradation**
   - if a feature family is isolated, the fallback behavior must remain documented, deterministic, and non-contradictory.

3. **Regression-linked rollout validation**
   - rollout decisions can be validated against Milestone 6 regression baselines,
   - so enabling or disabling a feature family can be measured rather than guessed.

4. **Configuration clarity**
   - rollout controls must be visible and documented,
   - not hidden scattered booleans with unclear interaction.

This task is about stabilization controls, not about leaving the project in permanent fragmented modes.

[Task possible affected files]

- configuration / feature-boundary module
- scenario regression runner integration
- rollout validation helper module
- release-hardening docs and config surfaces

[Task important notes]
Do not turn this into permanent complexity debt.
Do not allow undocumented fallback behavior.

Rollout hardening should support stabilization, not justify ambiguity.

[Task check list]

- [x] Add controlled feature-family boundaries
- [x] Add safe fallback behavior definitions
- [x] Link rollout validation to regression baselines
- [x] Centralize rollout controls
- [x] Document fallback semantics
- [x] Avoid scattered hidden toggles

[Task acceptance criteria]
The overhaul can be stabilized and deployed through explicit, documented, regression-aware rollout controls instead of risky all-or-nothing changes.

---

[x] (checkbox) - [Task 5] - Finalize the unified overhaul documentation pack

[Task Description]
Turn the completed milestone documentation into one maintainable reference set for future development, debugging, and tuning.

[Task technical implementation]
Create one unified final documentation pack that at minimum includes:

1. **Core rulebook reference**
   - spatial and timing rules from Milestone 1.

2. **Combat interaction reference**
   - engagement, disengagement, pursuit, and anti-stalemate semantics from Milestone 2.

3. **Movement model reference**
   - intention, route / local-step split, congestion, and anti-oscillation semantics from Milestone 3.

4. **Tactical behavior reference**
   - safe-shot, distance-management, retreat, commitment, role-sensitive behavior, and light coordination semantics from Milestone 4.

5. **Persistent consequence and stat ownership reference**
   - aftermath semantics and role-ceiling philosophy from Milestone 5.

6. **Arena and regression reference**
   - scenario matrix, metrics, and regression-baseline semantics from Milestone 6.

7. **Observability and rollout reference**
   - surfaced fields, explanation types, rollout boundaries, and safe degradation semantics from this milestone.

This task must unify milestone fragments into a coherent maintenance-grade reference set.

[Task possible affected files]

- `docs/combat/combat_movement_overhaul_spec.md`
- `docs/combat/combat_movement_overhaul_test_matrix.md`
- `docs/combat/combat_movement_observability_contract.md`
- `docs/combat/combat_movement_rollout_guide.md`

[Task important notes]
Do not produce a fluffy summary.
Do not leave milestone docs disconnected with overlapping contradictions.

This final pack must be exact enough for future developers to maintain the system without oral history.

[Task check list]

- [x] Create final overhaul spec
- [x] Create final overhaul test matrix
- [x] Create final observability contract doc
- [x] Create final rollout guide
- [x] Merge milestone semantics coherently
- [x] Remove contradictory duplicated wording
- [x] Keep the documentation maintenance-grade

[Task acceptance criteria]
The overhaul has one coherent final documentation pack that accurately reflects implementation and replaces fragmented tribal knowledge.

---

[x] (checkbox) - [Task 6] - Add observability, rollout, and documentation-integrity tests

[Task Description]
Lock the Milestone 7 contract with deterministic integrity tests so future changes cannot silently break surfaced truth, rollout safety, or documentation accuracy.

[Task technical implementation]
Add exact tests for the observability and documentation layer.

### Observability tests

Add test coverage for:

- deterministic explanation output for identical state,
- stable surfaced combat interaction fields,
- stable surfaced movement intention / blockage fields,
- stable surfaced persistent consequence summaries,
- and blocked/redirection reason semantics.

### Rollout-hardening tests

Add test coverage for:

- controlled feature-boundary behavior,
- safe fallback behavior,
- regression-link validation behavior,
- and deterministic configuration interactions.

### Documentation-integrity tests

Add test coverage for:

- documented surfaced fields exist in real serializers / presenters,
- documented explanation categories exist in real reason models,
- documented rollout controls exist in real config boundaries,
- and documented scenario / test references resolve to real implementation surfaces.

### Suggested test groups

- `tests/observability/test_combat_movement_observability_contract.py`
- `tests/rollout/test_combat_movement_rollout_boundaries.py`
- `tests/docs/test_combat_movement_documentation_integrity.py`

These tests should assert:

- surfaced truth stability,
- rollout safety semantics,
- and code-to-doc alignment,
  not gameplay balance outcomes.

[Task possible affected files]

- new observability contract test modules
- new rollout-boundary test modules
- new documentation-integrity test modules

[Task important notes]
Do not rely on manual doc review alone.
Do not treat exposed debug fields as “best effort.”

These are contract tests for surfaced truth and maintainability.

[Task check list]

- [x] Add deterministic explanation tests
- [x] Add surfaced-field stability tests
- [x] Add rollout-boundary tests
- [x] Add safe fallback tests
- [x] Add documentation-integrity tests
- [x] Add code-to-doc alignment checks
- [x] Keep the test surface deterministic and exact

[Task acceptance criteria]
The observability, rollout-hardening, and final documentation surfaces are pinned by deterministic integrity tests.

---

Priority Plan

What must change in mindset or assumptions
Stop treating observability and documentation as polish. In Milestone 7, surfaced truth and rollout safety are part of the implementation contract.

What actions must be taken immediately
Freeze the observability and rollout-hardening contracts, implement structured runtime inspection, add deterministic blocked-action explanations, add controlled rollout boundaries with safe degradation, finalize the unified documentation pack, and pin everything with integrity tests.

What must stop or be eliminated
Stop relying on logs, memory, and informal explanations. Stop allowing presenter layers to invent hidden truth. Stop leaving rollout behavior as undocumented toggle folklore.

The consequences and opportunity cost if this fails
The overhaul may technically work, but future debugging, tuning, and stabilization will degrade into superstition and trial-and-error, and the system will become expensive to maintain despite being “finished.”

---

### Implementation Comments (Audit 2026-04-17)

- **Observability Models**: Added `reason: str | dict` to `ActionProposal` and `IntentUpdate` in `src/actions/base.py`.
- **Rollout Hardening**: Added `overhaul_features` flag map to `SimulationConfig` in `src/config.py`.
- **System Integration**:
    - `ActionSystem`: Enforces `use_legality_v2` and `use_combat_interaction_v2` flags; populates `reason` for rejections and exhaustion.
    - `MovementModel`: Enforces `use_movement_model_v2`; populates `reason` in `NavigationUpdate` for planning and congestion results.
    - `TacticalEvaluator`: Enforces `use_tactical_evaluator_v2` with a safe legacy fallback.
- **API Visibility**: Updated `AIDecisionSchema` and `AIPresenter` to surface `last_reason` in the entity inspection response.
- **Documentation**: Consolidated all rules into `docs/combat/combat_movement_overhaul_spec.md`.
