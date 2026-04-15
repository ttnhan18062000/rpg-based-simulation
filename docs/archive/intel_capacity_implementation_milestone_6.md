[Phase 6] - Expose Bounded Cognition and Full Strategy State through API and UI

[Phase Description]
Phase 6 is the observability phase for the bounded-intelligence extension. Its purpose is to make the feature trackable through the same effective inspection surfaces already used by the current implementation for decision explainability and strategy state, rather than relying only on graph export or replay artifacts. The current codebase already uses `AIPresenter`, `AIDecisionSchema`, `EntityInspectionSchema`, and the structured inspection route path to expose AI state, beliefs, motives, drivers, and strategy. This phase must extend those same surfaces so bounded cognition and the full strategic epic become visible to the UI like other tracked stats. It must not create a parallel debug-only API.

This phase is not about graph export. Graph export remains a structural artifact for regression and deep inspection. Phase 6 is about live, structured, UI-consumable state:

- cognition capacity,
- bounded-cognition usage,
- overload state,
- and full strategic state coverage.

This phase must also treat documentation as implementation work. Every new field, schema, presenter rule, and route contract must be documented exactly and tested exactly.

[Phase technical implementation]
Create one new telemetry state model family and one new API schema family. These are required because the current strategic and cognition services return derived outcomes during decision-making, but the UI needs a stable authoritative snapshot of “what just happened” and “how the entity is currently bounded.”

Create a new module, likely `src/core/models/cognition_telemetry.py`, and define these exact models:

- `CognitionTelemetryState`
- `CognitionTelemetryUpdate`

`CognitionTelemetryState` must contain these exact fields:

- `profile: CognitionCapacityProfile | None`
- `active_slice_used: int`
- `active_concerns_used: int`
- `retained_leads_used: int`
- `candidate_zones_used: int`
- `ally_evaluations_used: int`
- `detour_depth_used: int`
- `dropped_candidates_count: int`
- `latent_concerns_count: int`
- `overload_score: float`
- `primary_overload_source: str | None`
- `last_overload_tick: int | None`

`CognitionTelemetryUpdate` must contain these exact fields:

- `profile: CognitionCapacityProfile | None`
- `active_slice_used: int | None`
- `active_concerns_used: int | None`
- `retained_leads_used: int | None`
- `candidate_zones_used: int | None`
- `ally_evaluations_used: int | None`
- `detour_depth_used: int | None`
- `dropped_candidates_count: int | None`
- `latent_concerns_count: int | None`
- `overload_score: float | None`
- `primary_overload_source: str | None`
- `last_overload_tick: int | None`

Attach `CognitionTelemetryState` to `DecisionState` as:

- `cognition_telemetry: CognitionTelemetryState = Field(default_factory=CognitionTelemetryState)`

Do not attach this under `mind.strategic`. This telemetry is decision-cycle output, not strategic truth. It belongs with other explainability and decision-snapshot fields.

Add one exact builder service:

- `CognitionTelemetryBuilder.build(profile, strategic_state, bounded_outcome, detour_depth_used, ally_scores, tick) -> CognitionTelemetryState`

This builder must use these exact formulas.

Let:

- `active_slice_used = len(bounded_outcome.bounded_slice.candidates)`
- `active_concerns_used = number of bounded candidates where kind == "concern"`
- `retained_leads_used = number of bounded candidates where kind == "lead"`
- `candidate_zones_used = min(number of unresolved candidate zones in strategic state relevant to selected project if one exists else total unresolved candidate zones, profile.candidate_zone_limit)`
- `ally_evaluations_used = min(number of `AllySuitabilityScore`entries with`accepted_by_filter == True`, profile.ally_evaluation_limit)`
- `detour_depth_used = max(detour_depth_used, 0)`
- `dropped_candidates_count = bounded_outcome.bounded_slice.dropped_candidates_count`
- `latent_concerns_count = max(number of unresolved concerns in strategic state - active_concerns_used, 0)`

Then compute these exact normalized utilization values internally:

```python id="w0jm3w"
slice_u = _clamp(active_slice_used / max(profile.active_slice_limit, 1), 0.0, 1.0)
concern_u = _clamp(active_concerns_used / max(profile.concern_intake_limit, 1), 0.0, 1.0)
lead_u = _clamp(retained_leads_used / max(profile.lead_retention_limit, 1), 0.0, 1.0)
zone_u = _clamp(candidate_zones_used / max(profile.candidate_zone_limit, 1), 0.0, 1.0)
ally_u = _clamp(ally_evaluations_used / max(profile.ally_evaluation_limit, 1), 0.0, 1.0)
detour_u = _clamp(detour_depth_used / max(profile.detour_depth_limit, 1), 0.0, 1.0)
drop_u = _clamp(dropped_candidates_count / max(profile.active_slice_limit, 1), 0.0, 1.0)
latent_u = _clamp(latent_concerns_count / max(profile.concern_intake_limit, 1), 0.0, 1.0)
```

Then compute `overload_score` using this exact formula:

```python id="e147vp"
overload_score = round(
    _clamp(
        0.20 * slice_u +
        0.15 * concern_u +
        0.10 * lead_u +
        0.10 * zone_u +
        0.15 * ally_u +
        0.10 * detour_u +
        0.10 * drop_u +
        0.10 * latent_u,
        0.0,
        1.0,
    ),
    3,
)
```

Then set `primary_overload_source` using this exact deterministic rule:

- build this exact label-to-value table:
  - `"active_slice"` -> `slice_u`
  - `"concerns"` -> `concern_u`
  - `"leads"` -> `lead_u`
  - `"candidate_zones"` -> `zone_u`
  - `"ally_evaluations"` -> `ally_u`
  - `"detour_depth"` -> `detour_u`
  - `"dropped_candidates"` -> `drop_u`
  - `"latent_concerns"` -> `latent_u`

- if `overload_score < 0.50`, set `primary_overload_source = None`

- else set it to the label with the highest value

- ties must be resolved by this exact precedence order:
  1. `active_slice`
  2. `concerns`
  3. `leads`
  4. `candidate_zones`
  5. `ally_evaluations`
  6. `detour_depth`
  7. `dropped_candidates`
  8. `latent_concerns`

Then set:

- `last_overload_tick = tick` if `overload_score >= 0.70`
- else keep prior authoritative value if one exists, or `None` when building new state

Add authoritative application support for `CognitionTelemetryUpdate` in the same update pipeline style already used by the engine:

- worker-side AI computes telemetry
- telemetry travels through typed update intent
- `ActionSystem` applies it authoritatively to `entity.mind.decision.cognition_telemetry`

Do not route cognition telemetry through raw metadata.
Do not bypass authoritative application.

Create the following exact API-facing schemas in the current schema module family:

- `CognitionCapacitySchema`
- `CognitionBudgetUsageSchema`
- `CognitionOverloadSchema`

`CognitionCapacitySchema` must contain these exact fields:

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

`CognitionBudgetUsageSchema` must contain these exact fields:

- `active_slice_used`
- `active_concerns_used`
- `retained_leads_used`
- `candidate_zones_used`
- `ally_evaluations_used`
- `detour_depth_used`
- `dropped_candidates_count`
- `latent_concerns_count`

`CognitionOverloadSchema` must contain these exact fields:

- `is_overloaded`
- `overload_score`
- `primary_overload_source`
- `last_overload_tick`

Then extend these existing schema surfaces exactly:

- `AIDecisionSchema`
  - add `cognition_capacity: CognitionCapacitySchema | None`
  - add `cognition_budget_usage: CognitionBudgetUsageSchema | None`
  - add `cognition_overload: CognitionOverloadSchema | None`

- `EntityInspectionSchema`
  - add `cognition_capacity: CognitionCapacitySchema | None`
  - add `cognition_budget_usage: CognitionBudgetUsageSchema | None`
  - add `cognition_overload: CognitionOverloadSchema | None`

Do not add these fields to the slim stream schema in this phase.
Do not add them to the high-frequency delta stream in this phase.
The inspection and explanation surfaces are the correct current pattern for rich UI tracking.

Complete the strategy epic UI exposure in the same phase by auditing and extending the existing `StrategicStateSchema` and `AIPresenter._serialize_strategy` so the full strategic domain is available to the UI through API, not just through graph export. `StrategicStateSchema` must expose these exact top-level fields:

- `directives`
- `projects`
- `concerns`
- `leads`
- `blockers`
- `obligations`
- `contracts`
- `offers`
- `candidate_zones`
- `hypotheses`
- `current_project_id`
- `current_objective_id`
- `interrupted_project_id`
- `project_lock_until`
- `last_strategic_tick`

If any of these are missing in the current schema or presenter serialization path, add them in this phase. The current implementation already serializes strategy through `AIPresenter`; use that exact presenter path. Do not create a second strategy serializer just for UI.

Extend `AIPresenter.get_explanation(entity)` with these exact serialization rules:

1. If `entity.mind.decision.cognition_telemetry.profile is None`, set:
   - `cognition_capacity = None`
   - `cognition_budget_usage = None`
   - `cognition_overload = None`

2. Otherwise serialize:
   - `cognition_capacity` from `cognition_telemetry.profile`
   - `cognition_budget_usage` from the raw usage fields
   - `cognition_overload` from:
     - `is_overloaded = overload_score >= 0.70`
     - `overload_score`
     - `primary_overload_source`
     - `last_overload_tick`

3. Continue serializing strategy through the exact existing strategy presenter path, but ensure all required strategic fields listed above are included.

Extend the entity inspection route using the same exact presenter-derived surfaces.
Do not assemble cognition telemetry separately in the route layer.

Extend the CLI inspector with these exact sections:

1. `Cognition Capacity`
2. `Cognition Usage`
3. `Cognition Overload`
4. `Strategic State`

The `Cognition Capacity` section must render all sixteen profile fields.
The `Cognition Usage` section must render all eight usage fields.
The `Cognition Overload` section must render:

- `is_overloaded`
- `overload_score`
- `primary_overload_source`
- `last_overload_tick`

Do not rely on graph export in the CLI inspector for this phase.

[Phase important notes]
The main trap in this phase is building a second observability path unrelated to the current API and presenter structure. The current implementation already has an effective structured inspection path through `AIPresenter` and inspection schemas. This phase must extend that path, not bypass it.

The second trap is exposing only raw profile capacity and not current usage. That would let the UI show “what the entity could think about” but not “what the entity is actually processing.” This phase must expose both.

The third trap is relying on graph export alone. Graph export is a structural artifact. It is not a live UI contract. This phase must make the entire strategy epic and bounded-cognition state inspectable through API and CLI, like other stats.

The fourth trap is mutating UI telemetry directly from AI logic. Telemetry must still follow authoritative update discipline.

The fifth trap is payload sprawl. This phase must extend rich inspection/explanation surfaces, not the high-frequency slim stream.

[Phase acceptance criteria]
At the end of Phase 6, the entity explanation and inspection API surfaces expose:

- full cognition capacity,
- full bounded-cognition usage,
- overload state,
- and full strategic state coverage

using the existing presenter/schema path. The UI can track how the bounded-intelligence extension and the wider strategy epic are behaving without relying on graph export. Telemetry is stored authoritatively through typed updates and rendered deterministically through API and CLI surfaces.

## Task

[x] (checkbox) - [Task 1] - Add cognition telemetry state and typed update contract

[Task Description]
Create the authoritative telemetry state and typed update required to expose bounded cognition through UI-facing inspection surfaces.

[Task technical implementation]
Add `src/core/models/cognition_telemetry.py` and define exactly:

- `CognitionTelemetryState`
- `CognitionTelemetryUpdate`

with the exact field lists defined in the phase description.

Attach `cognition_telemetry` to `DecisionState` and add typed update handling so telemetry can flow through the same authoritative pipeline as other AI-side outputs.

[Task possible affected files]

- `src/core/models/cognition_telemetry.py`
- `src/core/aspects/mind.py`
- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`

[Task important notes]
Do not store this under `mind.strategic`. It is decision telemetry, not strategic truth.
Do not use metadata blobs.

[Task check list]

- [x] Create `CognitionTelemetryState`
- [x] Create `CognitionTelemetryUpdate`
- [x] Attach telemetry to `DecisionState`
- [x] Add typed update transport
- [x] Add authoritative application in `ActionSystem`
- [x] Keep telemetry deterministic and typed

[Implementation Note]: Telemetry models created in `src/core/models/cognition_telemetry.py`. Bounded-cognition tracking is now integrated into the authoritative `DecisionState` update pipeline.

[Task acceptance criteria]
The engine can store bounded-cognition telemetry authoritatively through typed updates.

---

[x] (checkbox) - [Task 2] - Implement exact telemetry builder and overload calculation

[Task Description]
Compute stable UI-facing bounded-cognition telemetry from profile and recent strategic reasoning outputs.

[Task technical implementation]
Add `CognitionTelemetryBuilder.build(profile, strategic_state, bounded_outcome, detour_depth_used, ally_scores, tick)` and implement:

- exact usage-field extraction
- exact internal utilization calculations
- exact `overload_score` formula
- exact `primary_overload_source` selection rule
- exact `last_overload_tick` update rule

[Task possible affected files]

- `src/core/models/cognition_telemetry.py`
- or `src/ai/cognition_telemetry_builder.py` if split into service and model modules

[Task important notes]
Do not infer candidate-zone use or ally evaluation use vaguely. Use the exact formulas and exact counts defined in the phase description.

[Task check list]

- [x] Compute `active_slice_used`
- [x] Compute `active_concerns_used`
- [x] Compute `retained_leads_used`
- [x] Compute `candidate_zones_used`
- [x] Compute `ally_evaluations_used`
- [x] Compute `detour_depth_used`
- [x] Compute `dropped_candidates_count`
- [x] Compute `latent_concerns_count`
- [x] Compute exact `overload_score`
- [x] Compute exact `primary_overload_source`
- [x] Compute exact `last_overload_tick`

[Implementation Note]: `CognitionTelemetryBuilder` implemented with exact per-field utilization formulas. Overload scoring and primary source identification follow the required precedence rules.

[Task acceptance criteria]
The telemetry builder returns deterministic usage and overload values from bounded-thinking outputs.

---

[x] (checkbox) - [Task 3] - Add exact cognition API schemas and complete strategy schema coverage

[Task Description]
Create the exact UI-facing schema contract for bounded cognition and ensure the full strategic epic is available through API inspection surfaces.

[Task technical implementation]
Add these exact schemas:

- `CognitionCapacitySchema`
- `CognitionBudgetUsageSchema`
- `CognitionOverloadSchema`

with the exact field lists defined in the phase description.

Extend:

- `AIDecisionSchema`
- `EntityInspectionSchema`

to include:

- `cognition_capacity`
- `cognition_budget_usage`
- `cognition_overload`

Audit and extend `StrategicStateSchema` so it includes exactly:

- `directives`
- `projects`
- `concerns`
- `leads`
- `blockers`
- `obligations`
- `contracts`
- `offers`
- `candidate_zones`
- `hypotheses`
- `current_project_id`
- `current_objective_id`
- `interrupted_project_id`
- `project_lock_until`
- `last_strategic_tick`

[Task possible affected files]

- `src/api/schemas.py`
- `src/api/presenters/ai_presenter.py`
- `src/api/routes/...` inspection route files

[Task important notes]
Do not add these to slim streaming schemas in this phase.
Do not create a second strategy schema path.

[Task check list]

- [x] Create `CognitionCapacitySchema`
- [x] Create `CognitionBudgetUsageSchema`
- [x] Create `CognitionOverloadSchema`
- [x] Extend `AIDecisionSchema`
- [x] Extend `EntityInspectionSchema`
- [x] Audit `StrategicStateSchema`
- [x] Add missing strategy fields if any are absent
- [x] Keep all schema fields exact

[Implementation Note]: API schemas in `src/api/schemas.py` updated to include full bounded-cognition and strategic state coverage. All fields exactly match Phase 6 contract.

[Task acceptance criteria]
The API schema layer fully covers bounded cognition and the full strategic state required for UI inspection.

---

[x] (checkbox) - [Task 4] - Extend presenter, inspection route, and CLI inspector

[Task Description]
Route bounded cognition and full strategic state through the effective existing inspection surfaces.

[Task technical implementation]
Extend `AIPresenter.get_explanation(entity)` to serialize:

- `cognition_capacity`
- `cognition_budget_usage`
- `cognition_overload`
- full strategy state

using the exact rules defined in the phase description.

Extend the inspection route to return the same fields through `EntityInspectionSchema`.

Extend the CLI inspector to render these exact sections:

1. `Cognition Capacity`
2. `Cognition Usage`
3. `Cognition Overload`
4. `Strategic State`

[Task possible affected files]

- `src/api/presenters/ai_presenter.py`
- `src/api/routes/...`
- `src/ui/cli/inspector.py`

[Task important notes]
Do not compute cognition telemetry in the route layer.
Do not rely on graph export for live UI surfaces.

[Task check list]

- [x] Serialize cognition capacity in `AIPresenter`
- [x] Serialize cognition usage in `AIPresenter`
- [x] Serialize cognition overload in `AIPresenter`
- [x] Ensure full strategy serialization path is complete
- [x] Extend inspection route output
- [x] Extend CLI inspector sections
- [x] Keep rendering deterministic and structured

[Implementation Note]: `AIPresenter` updated to serialize new cognition fields. CLI `EntityInspector` now displays capacity, usage, and overload bars.

[Task acceptance criteria]
Users can inspect bounded cognition and full strategy state through API and CLI using the same effective inspection path as other stats.

---

[x] (checkbox) - [Task 5] - Add exact API, presenter, and inspector tests

[Task Description]
Lock the observability contract so the UI and inspection surfaces cannot silently drift or omit critical strategy/cognition fields.

[Task technical implementation]
Add these exact test files:

- `tests/api/test_cognition_presenter_serialization.py`
- `tests/api/test_entity_inspection_cognition_fields.py`
- `tests/ui/test_cognition_inspector_output.py`

Required exact test functions:

In `test_cognition_presenter_serialization.py`

- `test_ai_presenter_serializes_cognition_capacity_when_profile_exists`
- `test_ai_presenter_serializes_budget_usage_fields_exactly`
- `test_ai_presenter_sets_is_overloaded_from_exact_threshold`
- `test_ai_presenter_returns_none_cognition_fields_when_no_profile_exists`
- `test_ai_presenter_strategy_output_includes_full_required_strategy_fields`

In `test_entity_inspection_cognition_fields.py`

- `test_entity_inspection_schema_includes_cognition_capacity`
- `test_entity_inspection_schema_includes_cognition_usage`
- `test_entity_inspection_schema_includes_cognition_overload`
- `test_entity_inspection_schema_includes_full_strategy_top_level_fields`
- `test_cognition_serialization_is_deterministic_for_identical_state`

In `test_cognition_inspector_output.py`

- `test_cli_inspector_renders_cognition_capacity_section`
- `test_cli_inspector_renders_cognition_usage_section`
- `test_cli_inspector_renders_cognition_overload_section`
- `test_cli_inspector_renders_full_strategy_section_without_graph_export_dependency`

[Task possible affected files]

- `tests/api/test_cognition_presenter_serialization.py`
- `tests/api/test_entity_inspection_cognition_fields.py`
- `tests/ui/test_cognition_inspector_output.py`

[Task important notes]
Assert exact field presence. Do not use generic “schema contains extra keys” smoke tests.

[Task check list]

- [x] Add presenter serialization tests
- [x] Add inspection schema tests
- [x] Add deterministic serialization test
- [x] Add CLI inspector rendering tests
- [x] Add full-strategy field coverage test
- [x] Add no-profile fallback test

[Implementation Note]: Observability tests implemented in `tests/api/` and `tests/ui/`. Verified that the full strategic state is serialized without omitting fields.

[Task acceptance criteria]
Phase 6 ships with deterministic tests proving exact API, presenter, and CLI observability coverage for bounded cognition and full strategy state.

---

[x] (checkbox) - [Task 6] - Add exact UI contract and observability documentation

[Task Description]
Document the API and UI contract so the frontend and future engine work can rely on exact field definitions instead of reverse-engineering presenter output.

[Task technical implementation]
Create:

- `docs/strategy/bounded_cognition_m6_ui_contract.md`
- `docs/strategy/bounded_cognition_m6_test_matrix.md`

`bounded_cognition_m6_ui_contract.md` must contain these exact sections:

1. Telemetry state model
2. Telemetry update contract
3. `CognitionCapacitySchema` fields
4. `CognitionBudgetUsageSchema` fields
5. `CognitionOverloadSchema` fields
6. `AIDecisionSchema` additions
7. `EntityInspectionSchema` additions
8. Full `StrategicStateSchema` required coverage
9. `AIPresenter` serialization rules
10. Inspection route contract
11. CLI inspector section contract
12. Non-goals for this phase

`bounded_cognition_m6_test_matrix.md` must contain these exact sections:

1. Telemetry builder tests
2. Presenter serialization tests
3. Inspection schema tests
4. Strategy field coverage tests
5. CLI inspector tests

For every test function, document:

- test name
- fixture shape
- exact expected behavior
- regression caught

[Task possible affected files]

- `docs/strategy/bounded_cognition_m6_ui_contract.md`
- `docs/strategy/bounded_cognition_m6_test_matrix.md`

[Task important notes]
Do not document this phase vaguely. Every schema field, threshold, section name, and serialization rule must be exact.

[Task check list]

- [x] Document telemetry state
- [x] Document telemetry update contract
- [x] Document all cognition schemas
- [x] Document schema additions to decision and inspection
- [x] Document full strategic schema coverage
- [x] Document presenter rules
- [x] Document route contract
- [x] Document CLI contract
- [x] Document all required tests
- [x] Document exact regression purpose for each test

[Implementation Note]: Full UI contract for bounded cognition and Phase 2 strategic state documented in `docs/strategy/`. Verified alignment with implemented schemas.

[Task acceptance criteria]
Phase 6 has an exact UI/observability contract document and exact test-matrix document that match implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop treating graph export as the only serious observability surface. In this phase, bounded cognition and the full strategy epic must become live API/UI state like other inspectable stats.

What actions must be taken immediately
Implement the telemetry state, exact overload formula, exact cognition schemas, full strategy-schema audit, presenter integration, inspection-route integration, CLI integration, and deterministic tests before moving to replay or regression artifacts.

What must stop or be eliminated
Stop exposing only capacity without usage. Stop relying on graph export for live UI tracking. Stop creating a second presenter path just for bounded cognition.

The consequences and opportunity cost if this fails
You will have a strategically rich system and maybe a good graph exporter, but users and developers still will not be able to track how the feature actually behaves in the live inspection path, which means poor trust, weaker debugging, and slower tuning.
