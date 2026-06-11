---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

## High-level implementation plan — cognition-capacity and bounded-intelligence extension

This plan assumes the existing strategic epic foundation is already in place: `StrategicState`, `StrategicUpdate`, strategic appraisal before tactics, uncertainty structures, social contract machinery, event-driven strategic consequences, API presenter serialization of strategy, cognition graph export, and the headless regression runner. The current implementation already exposes strategy through `AIPresenter._serialize_strategy` and `StrategicStateSchema`, so this feature must extend those same presenter/schema/API paths instead of inventing a second debug-only channel.

This plan is exact for the feature scope you asked for:

- entity-specific cognition quality,
- bounded overload control,
- deterministic proof,
- documentation as implementation work,
- and UI/API visibility beyond graph export.

It does **not** add unrelated world-systems or new story objects.

---

# Milestone 1 — Define the cognition-capacity contract

### Description

Create the exact data contract for bounded metacognition so the feature has a stable implementation target. This milestone exists to prevent hand-wavy “smartness” logic from leaking into the codebase.

### Technical implementation

Add one new derived model family dedicated to cognition capacity. The minimum required model set is:

- `CognitionCapacityProfile`
- `CognitionCapacityTier` enum if you want human-readable UI labels
- `CognitionDriverRecord` only if you want structured explainability for why a profile was derived the way it was

`CognitionCapacityProfile` must contain these exact fields:

- `planning_budget`
- `judgment_stability`
- `evidence_quality`
- `social_bandwidth`
- `detour_depth_limit`
- `active_slice_limit`
- `concern_intake_limit`
- `lead_retention_limit`
- `candidate_zone_limit`
- `ally_evaluation_limit`
- `blocker_resolution_patience`
- `resume_reliability`
- `interruption_resistance`
- `abandonment_threshold_mod`
- `contradiction_sensitivity`
- `source_trust_learning_rate`

Add one deterministic builder service:

- `CognitionCapacityBuilder.build(entity, world_tick) -> CognitionCapacityProfile`

This builder must derive the profile from exactly these entity inputs:

- `progression.attributes.int_`
- `progression.attributes.wis`
- `progression.attributes.per`
- `progression.attributes.cha`
- personality profile
- seeded motives
- traits
- archetype
- temporary emotional overload if present
- temporary trauma if present
- temporary exhaustion or low-stamina state if present

Do not persist the full profile in entity state in this milestone. It must be derived from authoritative entity state each appraisal cycle or cached per tick outside persistent domain truth. The existing strategic architecture already relies on authoritative state plus derived reasoning phases; follow that pattern.

### Important notes

Do not create a single `intelligence` scalar and route everything through it. The design explicitly rejects that model. Intelligence-related differentiation must be decomposed into planning quality, judgment quality, evidence handling, and social reasoning.

Do not hardcode race as cognition destiny. Race or entity kind can bias underlying attributes or trait pools through existing generation patterns, but cognition quality must remain primarily per-entity. The current architecture already supports trait/archetype differentiation and structured presentation; use that instead of species-wide smart/dumb classes.

### Testing requirements

Add these exact tests:

- profile derivation from baseline attributes
- profile derivation with high `int_`
- profile derivation with high `wis`
- profile derivation with high `per`
- profile derivation with high `cha`
- profile derivation with personality modifier
- profile derivation with trait modifier
- profile derivation with temporary overload penalty
- deterministic profile derivation from identical entity state
- non-mutation guarantee for profile derivation

### Documentation requirements

Create one implementation reference document section that defines:

- every profile field,
- its source inputs,
- its numeric range,
- and what system behavior it is allowed to influence.

### Acceptance criteria

The codebase has one exact, typed, deterministic cognition-capacity contract and one deterministic builder for it. Tests prove profile derivation is stable, bounded, and non-mutating.

### Checklist

- [x] Create `CognitionCapacityProfile`
- [x] Create optional `CognitionCapacityTier` enum
- [x] Create `CognitionCapacityBuilder`
- [x] Map `int_` into planning-related fields
- [x] Map `wis` into judgment-related fields
- [x] Map `per` into evidence-related fields
- [x] Map `cha` into social-related fields
- [x] Map personality modifiers
- [x] Map trait modifiers
- [x] Map archetype modifiers
- [x] Map temporary overload modifiers
- [x] Add profile derivation tests
- [x] Add derivation documentation section

**Implementation Note (M1):** Established `CognitionCapacityProfile` as a derived model, ensuring it remains a strategic-layer construct decoupled from raw attribute storage. Builder uses a weighted attribution model for deterministic derivation.

---

# Milestone 2 — Integrate cognition capacity into strategic appraisal

### Description

Apply the profile to the existing strategic appraisal pass so entities no longer use identical strategic bandwidth.

### Technical implementation

Extend the current strategic appraisal flow in `AIBrain` and its helper services so every appraisal cycle performs these exact steps:

1. Build `CognitionCapacityProfile`
2. Gather raw strategic candidates from:
   - current project
   - current objective
   - active concerns
   - urgent obligations
   - suspended projects
   - fresh leads
   - active blockers
   - active contracts

3. Score and rank candidates by existing strategic salience logic
4. Apply `active_slice_limit`
5. Apply `concern_intake_limit`
6. Apply `lead_retention_limit` to the decision-relevant subset
7. Apply `candidate_zone_limit`
8. Apply `ally_evaluation_limit` when social evaluation is triggered
9. Pass bounded results to project selection and objective derivation

Use the profile to influence these exact strategic behaviors:

- project switching resistance
- objective persistence
- interruption resistance
- resumption reliability
- abandonment threshold
- blocker diagnosis confidence
- candidate pruning count
- number of concerns that become active instead of latent

This must be implemented in the current strategic appraisal path, not in tactical goal scoring. The earlier strategic implementation plan already established that project selection belongs above tactics, and the current codebase already serializes structured strategy through the presenter path. Keep that architecture intact.

### Important notes

Do not let the tactical layer impersonate cognition capacity. The tactical layer should consume a narrowed strategic context, not decide how many projects, leads, or obligations the entity can mentally juggle.

Do not silently drop strategic candidates without traceability. Every bounded-pruning rule must be observable through structured strategic drivers or bounded-cognition debug fields.

### Testing requirements

Add these exact tests:

- low-profile entity active slice is smaller than high-profile entity active slice
- low-profile entity activates fewer simultaneous concerns
- high `wis` entity resists noisy interruption better than low `wis` entity
- high `int_` entity preserves objective continuity better than low `int_` entity
- bounded candidate pruning is deterministic
- bounded pruning does not mutate stored `StrategicState`
- strategic explainability includes pruning or overload reasons when pruning happens

### Documentation requirements

Add one exact decision-flow section documenting:

- where profile derivation occurs,
- where candidate truncation occurs,
- and how bounded cognition interacts with current project continuity.

### Acceptance criteria

Strategic appraisal uses per-entity cognition capacity deterministically, and tests prove that active-slice width and continuity behavior differ across entities in controlled ways.

### Checklist

- [x] Build profile at strategic appraisal entry
- [x] Bound current strategic candidate set
- [x] Bound active concerns
- [x] Bound retained leads in current slice
- [x] Bound candidate zones in current slice
- [x] Bound ally evaluation width
- [x] Modulate interruption resistance
- [x] Modulate abandonment threshold
- [x] Modulate resumption reliability
- [x] Add bounded-appraisal tests
- [x] Add appraisal-flow documentation section

**Implementation Note (M2):** Injected bounded slice logic into `AIBrain.py` and `ObjectiveDerivationService`. Pruning is performed using a priority-sorted slice mechanism, ensuring the highest salience items are preserved while respecting cognitive limits.

---

# Milestone 3 — Apply cognition capacity to blocker diagnosis, detours, and lead learning

### Description

Use cognition capacity to make entities differ in how well they interpret failure, choose detours, and learn from uncertainty.

### Technical implementation

Integrate the profile into the existing blocker and detour services. Apply it to these exact behaviors:

- blocker diagnosis precision
- blocker misclassification probability if your implementation uses explicit probabilistic error
- detour depth limit
- number of simultaneous detour candidates considered
- tested-lead retry suppression
- contradiction response strength
- source-trust adjustment speed
- candidate-zone narrowing quality

You must implement these exact rules:

1. `detour_depth_limit` hard-caps recursive detour propagation
2. when detour depth is exhausted, the entity must choose exactly one of:
   - suspend root project
   - delay root project
   - abandon root project

3. `contradiction_sensitivity` governs how strongly contradictory evidence degrades lead confidence
4. `source_trust_learning_rate` governs how quickly sources gain or lose trust after confirmed or failed leads
5. `blocker_resolution_patience` governs how long the entity tolerates a blocker before suspension or abandonment pressure rises

Do not add infinite planning recursion. The original design and your review both identified recursive preparation loops as a major failure mode. This milestone is where that gets shut down explicitly.

### Important notes

Do not let vague leads collapse into exact coordinates because a high-capacity entity exists. Higher capacity should sharpen uncertainty faster, not erase it prematurely. The uncertainty design already treats candidate zones and hypotheses as first-class strategic objects, and this extension must preserve that.

### Testing requirements

Add these exact tests:

- high `per` entity narrows candidate zones faster than low `per` entity
- low `per` entity retains noisier candidate-zone spread under same clue input
- high `int_` entity diagnoses blocker type more accurately than low `int_` entity under controlled fixtures
- detour depth limit stops recursive blocker chains
- exhausted detour depth forces suspend, delay, or abandon outcome
- high `wis` entity stops retrying failed leads sooner than low `wis` entity
- contradictory evidence updates source trust deterministically
- tested-lead suppression prevents immediate blind retry

### Documentation requirements

Add one exact failure-handling section documenting:

- blocker diagnosis rules,
- detour depth rules,
- tested-lead learning rules,
- and the forced fallback outcome when detour depth is exhausted.

### Acceptance criteria

Entities differ in blocker diagnosis, detour discipline, and uncertainty learning, and no recursive detour chain can continue unbounded.

### Checklist

- [x] Apply profile to blocker diagnosis
- [x] Apply profile to detour selection breadth
- [x] Enforce detour depth limit
- [x] Enforce suspend, delay, or abandon fallback
- [x] Apply profile to tested-lead retry suppression
- [x] Apply profile to contradiction handling
- [x] Apply profile to source-trust learning
- [x] Add blocker and detour tests
- [x] Add uncertainty-learning documentation section

**Implementation Note (M3):** Unified `StrategicLearningService` provides a central path for lead trust/certainty recalibration. Detour recursion is strictly bounded by `detour_depth_limit` with forced suspension fallback in `ObjectiveDerivationService` to prevent planning cycles.

---

# Milestone 4 — Apply cognition capacity to social reasoning and cooperation

### Description

Make cooperation quality differ by entity instead of only by need, trust, and role fit.

### Technical implementation

Integrate the profile into social cooperation services and contract logic. Apply it to these exact behaviors:

- detection of non-solo viability
- recruitment objective generation confidence
- ally-evaluation breadth
- ally-ranking quality
- contract stabilization after activation
- contract recovery after interruption
- future willingness to re-engage after breach or success

Map profile fields into social logic as follows:

- `social_bandwidth` caps how many allies can be actively evaluated
- `judgment_stability` influences whether risky solo attempts are incorrectly preferred
- `resume_reliability` influences whether interrupted party-backed projects recover properly
- `source_trust_learning_rate` can also modulate trust recalibration after contract outcomes
- `interruption_resistance` influences whether temporary disruption dissolves cooperation too easily

Use the current social and strategy presentation path for visibility. Strategy already appears inside the AI presenter via `AIPresenter._serialize_strategy`; extend that same schema flow with bounded-social-cognition fields rather than inventing a second API object that the UI has to stitch together manually.

### Important notes

Do not confuse “asks fewer people” with “is less social.” The feature is about strategic reasoning quality, not personality inversion. A low-`cha` entity can still want help; it should just be worse at selecting, persuading, and stabilizing the right help.

### Testing requirements

Add these exact tests:

- high `cha` entity evaluates more valid allies than low `cha` entity under same scenario
- low `cha` entity produces worse ally ranking under controlled candidate set
- low `wis` entity incorrectly attempts solo execution more often in non-solo-viable scenario
- high-capacity entity stabilizes contract continuation better after temporary disruption
- post-breach trust and future recruitment behavior diverge by cognition profile

### Documentation requirements

Add one exact social-cognition section documenting:

- which profile fields affect recruitment,
- which affect contract durability,
- and which affect solo-viability judgment.

### Acceptance criteria

Entities differ in cooperation quality and social strategic judgment in deterministic, explainable ways.

### Checklist

- [x] Apply profile to non-solo viability judgment
- [x] Apply profile to recruitment objective confidence
- [x] Apply profile to ally search width
- [x] Apply profile to ally ranking quality
- [x] Apply profile to contract stabilization
- [x] Apply profile to contract recovery after interruption
- [x] Add social-cognition tests
- [x] Add social-cognition documentation section

**Implementation Note (M4):** Integrated `SOCIAL` blocker detection with probabilistic misjudgment based on `judgment_stability`. Ally search and evaluation are now bounded by `social_bandwidth`, with ranking perturbed by `judgment_stability` to simulate varied cooperation quality.

---

# Milestone 5 — Apply cognition capacity to event interpretation and identity drift

### Description

Make entities differ in how they interpret major events and how strongly those events reshape future strategy.

### Technical implementation

Integrate the profile into the existing event-to-strategy interpreter and strategic reprioritization services. Apply it to these exact behaviors:

- concern generation threshold
- concern urgency amplification or damping
- project suspension versus replacement versus transformation
- directive strengthening threshold
- directive weakening threshold
- repeated-event accumulation threshold
- revenge or protection escalation quality
- failure-to-reattempt discipline
- drift resistance of identity-linked directives

Use these mappings:

- `judgment_stability` influences overreaction versus appropriate reprioritization
- `interruption_resistance` influences whether current project is dropped too eagerly
- `abandonment_threshold_mod` influences when the entity fully lets go
- `resume_reliability` influences whether interrupted work is returned to after crisis
- `contradiction_sensitivity` can influence how repeated false leads reshape future source weighting after event-like evidence outcomes

The original design explicitly says event consequence must not collapse into score nudges. This milestone is where that becomes mechanically differentiated by cognition quality.

### Important notes

Do not make low-capacity entities purely irrational. They must still be coherent, just less skillful at reprioritization and learning. The goal is divergence in judgment quality, not random chaos.

### Testing requirements

Add these exact tests:

- high `wis` entity reprioritizes home threat more appropriately than low `wis` entity under same attachment profile
- high `wis` entity is less likely to panic-switch on weak event pressure
- low `wis` entity escalates betrayal consequences more aggressively under same history
- identity drift after repeated events is thresholded and profile-sensitive
- interrupted project resumption after crisis differs by `resume_reliability`

### Documentation requirements

Add one exact interpretation section documenting:

- how cognition capacity affects concern generation,
- how it affects directive mutation,
- and how it affects project suspension, replacement, and transformation.

### Acceptance criteria

Event consequence handling becomes profile-sensitive, deterministic, and explainable without becoming random or purely utility-based.

### Checklist

- [x] Apply profile to concern generation threshold
- [x] Apply profile to concern urgency handling
- [x] Apply profile to suspension, replacement, and transformation logic
- [x] Apply profile to directive mutation thresholds
- [x] Apply profile to identity drift resistance
- [x] Add event-interpretation tests
- [x] Add interpretation documentation section

### Implementation Notes (Milestone 5)

Milestone 5 successfully integrated `CognitionCapacityProfile` into the event interpretation pipeline. Key changes included:
- **StrategicConsequenceService**: Now orchestrates the passing of the cognitive profile to all downstream interpretation logic.
- **ConcernGenerationService**: Implemented deterministic priority/urgency perturbation based on `judgment_stability`. Added "Panic" noise logic for unstable entities.
- **ProjectMutationService**: Modulates project suspension and abandonment thresholds based on `interruption_resistance`.
- **DirectiveMutationService**: High `judgment_stability` now increases the salience threshold required for identity-linked directive shifts (Identity Drift).
- **StrategicKnowledgeIngestion**: Added cognitive-sensitive danger thresholds for rumors.
- **Verification**: New tests in `tests/ai/test_event_interpretation.py` confirm these behaviors.

---

# Milestone 6 — Expose cognition-capacity and bounded-thinking state through API and UI-facing schemas

### Description

Make the feature visible through the same API and presenter patterns used for other stats and for current strategy state. This is required for tracking, debugging, and user trust.

### Technical implementation

Add one exact API-facing schema family for cognition capacity and bounded-thinking status. Minimum required schema set:

- `CognitionCapacitySchema`
- `CognitionBudgetUsageSchema`
- `CognitionOverloadSchema`

`CognitionCapacitySchema` must expose these exact fields:

- `planning_budget`
- `judgment_stability`
- `evidence_quality`
- `social_bandwidth`
- `detour_depth_limit`
- `active_slice_limit`
- `concern_intake_limit`
- `lead_retention_limit`
- `candidate_zone_limit`
- `ally_evaluation_limit`
- `blocker_resolution_patience`
- `resume_reliability`
- `interruption_resistance`
- `abandonment_threshold_mod`
- `contradiction_sensitivity`
- `source_trust_learning_rate`

`CognitionBudgetUsageSchema` must expose these exact live-state fields:

- `active_slice_used`
- `active_concerns_used`
- `retained_leads_used`
- `candidate_zones_used`
- `ally_evaluations_used`
- `detour_depth_used`
- `dropped_candidates_count`
- `latent_concerns_count`

`CognitionOverloadSchema` must expose these exact status fields:

- `is_overloaded`
- `overload_score`
- `primary_overload_source`
- `last_overload_tick`

Integrate these schemas into the existing entity decision and inspection presenter path:

- extend `AIDecisionSchema`
- extend `EntityInspectionSchema`
- extend `AIPresenter.get_explanation`
- extend any current inspect route that already returns strategic state
- extend CLI inspector rendering

The current implementation already serializes structured strategy through `AIPresenter._serialize_strategy`. Use the same presenter-to-schema path for cognition capacity and budget usage. Do not route this only through graph export.

### Important notes

Do not expose only raw budgets. Expose both:

- what the entity is capable of,
- and what it is currently using or dropping.

That is the only way a user can actually track how the system behaves.

Do not create a UI surface that depends on replay parsing for live inspection. The API presenter path is already the effective pattern; reuse it.

### Testing requirements

Add these exact tests:

- `AIPresenter` includes cognition capacity schema when strategy is present
- `AIPresenter` includes cognition budget usage fields
- entity inspection schema serializes cognition capacity without crash
- empty strategy still returns stable cognition-capacity surface if entity attributes exist
- UI-facing serialization is deterministic for identical entity state
- CLI inspector shows cognition capacity summary and current budget usage

### Documentation requirements

Add one exact observability section documenting:

- every new schema,
- every new field,
- which route or presenter exposes it,
- and how UI should interpret it.

### Acceptance criteria

Users can inspect this feature through the API and inspector using the same effective structured surfaces as other stats and strategy state, without relying on graph export alone.

### Checklist

- [x] Add `CognitionCapacitySchema`
- [x] Add `CognitionBudgetUsageSchema`
- [x] Add `CognitionOverloadSchema`
- [x] Integrate capacity visibility into `AIPresenter`
- [x] Implement CLI budget bars in `EntityInspector`
- [x] Add API sterilization and inspector verification tests

### Implementation Notes (Milestone 6)

Milestone 6 exposed the cognitive bounded-thinking state through the rest API and CLI.
- **StrategicState Expansion**: Added `last_capacity_profile` and live budget usage tracking (e.g., `active_slice_used`, `dropped_candidates_count`).
- **API Schemas**: Defined `CognitionCapacitySchema`, `CognitionBudgetUsageSchema`, and `CognitionOverloadSchema`.
- **AIPresenter**: Now serializes the current cognitive profile and budget usage for entity inspection.
- **CLI Inspector**: Added a dedicated `COGNITION & CAPACITY` section with color-coded status bars for active budgets (Candidates, Concerns, Leads, Zones, Allies) and proactive overload alerts.
- **Verification**: `tests/ai/test_intel_capacity_visibility.py` ensures perfect match between derivation and reporting.

---

# Milestone 7 — Extend replay, graph export, and headless regression to cover bounded cognition

### Description

Make bounded cognition part of the final proof path so the feature is regression-testable end to end.

### Technical implementation

Extend replay summary generation to include these exact compact fields per tracked entity:

- `planning_budget`
- `judgment_stability`
- `evidence_quality`
- `social_bandwidth`
- `active_slice_used`
- `dropped_candidates_count`
- `detour_depth_used`
- `is_overloaded`
- `current_project_id`
- `current_objective_id`

Extend cognition graph export to include bounded-thinking data in one of these exact ways:

- root entity node attributes, or
- dedicated bounded-cognition annotation node linked from entity root

Choose one and document it. Do not leave export shape ambiguous.

Extend headless regression assertions to verify:

- profile values are deterministic for identical seed and entity state
- low- and high-capacity entities produce different bounded-thinking artifacts under controlled scenario
- overload flags appear when active-candidate pressure exceeds profile budget
- detour depth limit is reflected in artifact state
- replay and graph agree on current bounded-cognition summary where semantics overlap

The current implementation already has headless runner and assertion helpers; this milestone extends them rather than inventing new regression surfaces.

### Important notes

Do not compare replay and graph on semantics that one side does not intentionally expose. Either enrich both or narrow the assertion rule precisely.

### Testing requirements

Add these exact tests:

- deterministic replay fields for cognition capacity
- deterministic graph export fields for cognition capacity
- replay-versus-graph consistency for bounded-thinking summary
- overload scenario produces overload flag
- recursive blocker scenario respects detour depth limit in artifacts
- low-versus-high capacity scenario diverges deterministically in dropped candidate counts and active-slice usage

### Documentation requirements

Add one exact regression section documenting:

- which bounded-cognition fields are written to replay,
- which are written to graph export,
- and which consistency checks are enforced.

### Acceptance criteria

The bounded-intelligence feature is fully visible in replay, graph export, and headless regression outputs, with deterministic artifact-level proof.

### Checklist

- [x] Extend replay summaries with cognitive fields
- [x] Implement `cognition_profile` node in graph export
- [x] Add cognitive assertions in `assertions.py`
- [x] Add e2e regression test `tests/ai/test_intel_capacity_regression.py`
- [x] Verify determinism and overload behavior

### Implementation Notes (Milestone 7)

Milestone 7 established the regression proof for bounded cognition.
- **Replay Hardening**: Extended `src/utils/replay.py` to capture cognitive metrics in tick-by-tick shots.
- **Graph Observability**: Added a dedicated `cognition_profile` node to the graph export, allowing for structural verification of cognitive state.
- **Regression Suite**: Added `tests/ai/test_intel_capacity_regression.py` which uses the `HeadlessRunner` to verify:
  - **Determinism**: Identical seeds produce bit-identical cognitive artifacts.
  - **Consistency**: Replay summaries and graph exports agree on cognitive metrics.
  - **Overload**: Injected cognitive pressure correctly triggers the `is_overloaded` flag.
- **AOA Integrity**: Fixed several incorrect `from_entity` calls in logic services to use the deterministic `CognitionCapacityBuilder.build` method.
- [x] Add detour-depth scenario
- [x] Add low-versus-high capacity divergence scenario
- [x] Add regression documentation section

**Implementation Note (M7):** Established the regression proof for bounded cognition using `ReplayRecorder` and `CognitionGraphExporter`. Extended the suite with diversity and detour scenarios in `tests/ai/test_intel_capacity_regression.py`, proving deterministic divergence and hard-bound behavior.

---

# Milestone 8 — Complete feature documentation and verification pack

### Description

Treat documentation as implementation work and close the feature with one exact, maintainable reference set.

### Technical implementation

Produce these exact documents:

1. `bounded_cognition_feature_spec.md`
   - purpose
   - data contract
   - profile derivation rules
   - integration points
   - bounded-cognition rules
   - API exposure
   - replay/export exposure

2. `bounded_cognition_test_matrix.md`
   - every unit test class
   - every integration test class
   - every end-to-end scenario
   - what each test proves
   - what each test intentionally does not prove

3. `bounded_cognition_ui_contract.md`
   - every UI-facing schema
   - every field
   - which API response contains it
   - how to display budget versus usage versus overload

4. `bounded_cognition_tuning_guide.md`
   - numeric ranges
   - recommended defaults
   - what high and low values should feel like
   - known failure patterns
   - safe ways to rebalance without breaking determinism

This milestone also includes one exact review pass:

- verify every presenter field has a schema field
- verify every replay field is documented
- verify every graph-export bounded-cognition field is documented
- verify every test mentioned in the matrix exists

### Important notes

Do not leave this feature as code plus tribal knowledge. The review already called out that the design is stronger as ontology than as execution contract. This milestone closes that gap by making the operational semantics explicit.

### Testing requirements

Add one documentation-integrity test group that checks:

- all documented API schema fields exist in schema models
- all documented replay fields exist in replay output
- all documented graph fields exist in exporter output
- all documented tests resolve to real test modules

### Acceptance criteria

The feature is fully documented, verifiable, and maintainable without relying on memory or informal explanation.

### Checklist

- [x] Create `bounded_cognition_feature_spec.md`
- [x] Create `bounded_cognition_test_matrix.md`
- [x] Create `bounded_cognition_ui_contract.md`
- [x] Create `bounded_cognition_tuning_guide.md`
- [x] Add documentation-integrity tests
- [x] Verify schema-to-doc alignment
- [x] Verify replay-to-doc alignment
- [x] Verify graph-to-doc alignment
- [x] Verify test-matrix alignment

**Implementation Note (M8):** Finalized the Bounded Cognition Documentation Pack and Verification Suite. Documentation integrity tests ensure that schemas, artifacts, and test modules remain in sync with the codebase's operational semantics.

---

## Recommended implementation order

1. Milestone 1 — Define the contract
2. Milestone 2 — Apply it to strategic appraisal
3. Milestone 3 — Apply it to blockers, detours, and leads
4. Milestone 4 — Apply it to social reasoning
5. Milestone 5 — Apply it to event interpretation
6. Milestone 6 — Expose it through API and inspector
7. Milestone 7 — Add replay, graph, and regression proof
8. Milestone 8 — Finalize documentation and verification pack

This order is the correct one because it follows the current architecture:

- authoritative strategic domain first,
- strategic reasoning integration second,
- observability through existing presenter/schema paths after behavior exists,
- and full regression proof after the API and artifact surfaces are stable.

## Final delivery condition

This feature is complete only when all of the following are true:

- entities derive deterministic cognition-capacity profiles
- strategic appraisal is bounded by per-entity capacity
- blocker, detour, and lead learning are capacity-sensitive
- recruitment and cooperation quality are capacity-sensitive
- event interpretation and identity drift are capacity-sensitive
- API and inspector expose both cognition capacity and live budget usage
- replay and graph export include bounded-cognition state
- headless regression proves deterministic divergence and overload control
- documentation exactly matches implementation

If any one of those is missing, the feature is not finished.

## Priority plan

What must change in mindset or assumptions
Stop treating this as a tuning tweak. This is a core extension of the strategic system’s execution contract.

What actions must be taken immediately
Start with the exact data contract, then integrate bounded cognition into strategic appraisal before touching social or event interpretation.

What must stop or be eliminated
Stop using one implicit shared metacognitive budget for all entities. Stop relying on graph export alone for visibility. Stop postponing documentation until after implementation.

The consequences and opportunity cost if this fails
You will keep a rich strategic system with too-uniform thinkers, weak overload control, and poor observability. That means more code, less believable variation, and harder-to-debug regressions.
