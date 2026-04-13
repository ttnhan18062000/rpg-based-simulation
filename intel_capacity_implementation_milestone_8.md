[Phase 8] - Complete Documentation, Verification Pack, and Closure Audit

[Phase Description]
Phase 8 is the closure phase for the bounded-intelligence extension. Its purpose is to make the feature auditable, maintainable, and shippable as a complete subsystem rather than a pile of code plus informal knowledge. The earlier phases define the cognition-capacity contract, integrate it into strategic appraisal, uncertainty resolution, social reasoning, event interpretation, API/UI observability, and replay/graph regression. This phase does not add new mechanics. It turns the implementation into an exact reference set: a feature specification, a test matrix, a UI contract, a tuning guide, and a documentation-integrity audit that proves the documents, schemas, replay artifacts, graph export, and tests all still match the code. The current strategy epic already showed that the system becomes untrustworthy when observability and proof lag behind implementation; this phase closes that gap explicitly.

This phase is required work, not optional cleanup. The review already established that the ontology is stronger than the execution contract unless the operating rules are written down exactly. This phase is where the final execution contract is frozen, cross-checked, and made safe for future maintenance.

[Phase technical implementation]
Create four exact documents and one exact documentation-integrity test pack.

Create these exact documents:

1. `docs/strategy/bounded_cognition_feature_spec.md`
2. `docs/strategy/bounded_cognition_test_matrix.md`
3. `docs/strategy/bounded_cognition_ui_contract.md`
4. `docs/strategy/bounded_cognition_tuning_guide.md`

These files are mandatory and must be treated as implementation artifacts.

`bounded_cognition_feature_spec.md` must contain these exact sections:

1. Purpose
2. Scope
3. Non-goals
4. Core model contracts
5. `CognitionCapacityProfile` field definitions
6. Phase 1 derivation formulas
7. Strategic appraisal bounded-slice rules
8. Blocker diagnosis rules
9. Detour generation rules
10. Lead-learning rules
11. Cooperation-need rules
12. Ally-scoring rules
13. Contract-stability rules
14. Event-interpretation rules
15. Directive-mutation rules
16. Project-reprioritization rules
17. Telemetry state rules
18. Replay artifact rules
19. Graph export rules
20. Determinism rules
21. Authoritative-application rules
22. Known invariants
23. Known failure modes

`bounded_cognition_test_matrix.md` must contain these exact sections:

1. Phase 1 tests
2. Phase 2 tests
3. Phase 3 tests
4. Phase 4 tests
5. Phase 5 tests
6. Phase 6 tests
7. Phase 7 tests
8. Shared fixture rules
9. Determinism requirements
10. Non-mutation requirements
11. Artifact-consistency requirements
12. Documentation-integrity requirements

For every required test function introduced across Phases 1 through 7, this document must include exactly:

- test module path
- test function name
- phase
- fixture shape
- exact expected behavior
- exact regression caught

`bounded_cognition_ui_contract.md` must contain these exact sections:

1. UI observability goals
2. `CognitionCapacitySchema`
3. `CognitionBudgetUsageSchema`
4. `CognitionOverloadSchema`
5. `AIDecisionSchema` additions
6. `EntityInspectionSchema` additions
7. Full `StrategicStateSchema` field coverage
8. Presenter serialization rules
9. Inspection route contract
10. CLI inspector contract
11. Replay cognition summary contract
12. Graph bounded-cognition node contract
13. Shared field naming rules
14. Nullability rules
15. Non-goals for UI exposure

For every field in every schema or artifact section, this document must include exactly:

- field name
- type
- nullable or non-nullable status
- source of truth
- serialization surface
- intended UI interpretation

`bounded_cognition_tuning_guide.md` must contain these exact sections:

1. Tuning goals
2. Attribute normalization assumptions
3. Capacity-field value ranges
4. Recommended default interpretation of low, medium, and high values
5. Strategic appraisal tuning rules
6. Uncertainty-resolution tuning rules
7. Social-reasoning tuning rules
8. Event-interpretation tuning rules
9. Overload-score tuning rules
10. Safe change policy
11. Unsafe change examples
12. Regression watchlist
13. Scenario-based tuning checklist

This guide must not contain vague advice. Every tuning section must name the exact formulas or thresholds that can be tuned and the exact classes of regression that each change can trigger.

Add one new documentation-integrity test module family:

- `tests/docs/test_bounded_cognition_docs_integrity.py`

This file must verify all four document contracts against the implementation.

It must include these exact test functions:

- `test_feature_spec_references_all_required_cognition_profile_fields`
- `test_feature_spec_references_all_required_phase_formulas`
- `test_test_matrix_references_all_required_bounded_cognition_test_functions`
- `test_ui_contract_references_all_required_schema_fields`
- `test_ui_contract_references_all_required_replay_cognition_fields`
- `test_ui_contract_references_all_required_graph_cognition_fields`
- `test_tuning_guide_references_all_required_tunable_formula_groups`
- `test_documented_api_fields_exist_in_schema_models`
- `test_documented_replay_fields_exist_in_replay_summary_model`
- `test_documented_graph_fields_exist_in_graph_export_contract`
- `test_documented_test_functions_exist_in_test_modules`

To support these tests, add one exact document-audit helper module:

- `src/testing/doc_contract_audit.py`

This helper module must expose these exact functions:

- `load_markdown_sections(path: str) -> dict[str, str]`
- `extract_bullet_values(section_text: str) -> list[str]`
- `assert_required_strings_present(section_text: str, required: list[str]) -> None`
- `assert_test_functions_exist(module_paths: list[str], function_names: list[str]) -> None`
- `assert_schema_fields_exist(model_cls, field_names: list[str]) -> None`

The documentation-integrity tests must use these exact comparison sets.

For `CognitionCapacityProfile`, the required field set is exactly:

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

For `CognitionBudgetUsageSchema`, the required field set is exactly:

- `active_slice_used`
- `active_concerns_used`
- `retained_leads_used`
- `candidate_zones_used`
- `ally_evaluations_used`
- `detour_depth_used`
- `dropped_candidates_count`
- `latent_concerns_count`

For `CognitionOverloadSchema`, the required field set is exactly:

- `is_overloaded`
- `overload_score`
- `primary_overload_source`
- `last_overload_tick`

For replay cognition summary, the required field set is exactly:

- `planning_budget`
- `judgment_stability`
- `evidence_quality`
- `social_bandwidth`
- `detour_depth_limit`
- `active_slice_limit`
- `ally_evaluation_limit`
- `active_slice_used`
- `active_concerns_used`
- `retained_leads_used`
- `candidate_zones_used`
- `ally_evaluations_used`
- `detour_depth_used`
- `dropped_candidates_count`
- `latent_concerns_count`
- `overload_score`
- `primary_overload_source`
- `is_overloaded`
- `current_project_id`
- `current_objective_id`

For graph bounded-cognition node attributes, the required field set is exactly:

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
- `active_slice_used`
- `active_concerns_used`
- `retained_leads_used`
- `candidate_zones_used`
- `ally_evaluations_used`
- `detour_depth_used`
- `dropped_candidates_count`
- `latent_concerns_count`
- `overload_score`
- `primary_overload_source`
- `is_overloaded`
- `last_overload_tick`

Add one exact closure-review helper document:

- `docs/strategy/bounded_cognition_release_checklist.md`

It must contain these exact sections:

1. Contract completion checks
2. Behavior integration checks
3. API and UI checks
4. Replay and graph artifact checks
5. Regression suite checks
6. Documentation checks
7. Tuning sign-off checks
8. Release blockers

Each section must contain only checkboxes, and each checkbox must correspond to one implemented requirement from Phases 1 through 7.

Add one final closure audit test module:

- `tests/docs/test_bounded_cognition_release_checklist.py`

It must include these exact test functions:

- `test_release_checklist_contains_all_phase_headers`
- `test_release_checklist_references_all_required_artifact_classes`
- `test_release_checklist_references_all_required_schema_classes`
- `test_release_checklist_references_all_required_regression_scenarios`

This phase must also add one final audit path into the headless regression runner:

- after all bounded-cognition scenarios pass, set `cognition_consistency_checked = True` in the runner manifest
- only if:
  - replay cognition consistency checks passed,
  - graph cognition consistency checks passed,
  - and documentation-integrity tests are green in the same CI job or test invocation

If those conditions are not met, the manifest must leave:

- `cognition_consistency_checked = False`

No other completion rule is allowed in this phase.

[Phase important notes]
The main trap in this phase is writing nice-looking documents that are not executable against the code. This phase must make documentation testable, not merely readable.

The second trap is drifting field names between docs, schemas, replay, graph export, and tests. This phase exists specifically to stop that.

The third trap is treating documentation as a separate concern from delivery. In this phase, documentation is part of the release contract and must be gated by tests.

The fourth trap is allowing the release checklist to become vague. Every checklist item must map to an implemented requirement from an earlier phase. No generic “looks good” items are allowed.

The fifth trap is declaring the feature complete without documentation-integrity proof. This phase must make the system self-auditing.

[Phase acceptance criteria]
At the end of Phase 8, the bounded-intelligence extension has:

- a complete feature specification,
- a complete test matrix,
- a complete UI contract,
- a complete tuning guide,
- a complete release checklist,
- documentation-integrity tests that verify docs against implementation,
- and a final manifest-level completion flag that is only true when artifact consistency and documentation integrity are both verified.

The feature is only considered closed when those conditions are met.

## Task

[ ] (checkbox) - [Task 1] - Create the complete feature specification document

[Task Description]
Write the exact implementation specification for the bounded-intelligence extension so the entire subsystem has one authoritative reference.

[Task technical implementation]
Create `docs/strategy/bounded_cognition_feature_spec.md` with the exact section list defined in the phase description. Every section must reflect the implemented contracts and formulas from Phases 1 through 7.

[Task possible affected files]

- `docs/strategy/bounded_cognition_feature_spec.md`

[Task important notes]
Do not summarize loosely. Include exact formulas, exact field names, exact thresholds, and exact allowed value sets.

[Task check list]

- [ ] Add Purpose
- [ ] Add Scope
- [ ] Add Non-goals
- [ ] Add Core model contracts
- [ ] Add profile field definitions
- [ ] Add Phase 1 formulas
- [ ] Add appraisal rules
- [ ] Add uncertainty rules
- [ ] Add social rules
- [ ] Add event rules
- [ ] Add telemetry rules
- [ ] Add replay and graph rules
- [ ] Add determinism rules
- [ ] Add authoritative-application rules
- [ ] Add invariants and failure modes

[Task acceptance criteria]
The feature spec exists and fully describes the implemented bounded-cognition system with exact contracts and formulas.

---

[ ] (checkbox) - [Task 2] - Create the complete test matrix document

[Task Description]
Document every required bounded-cognition test so the proof surface is explicit and auditable.

[Task technical implementation]
Create `docs/strategy/bounded_cognition_test_matrix.md` with the exact sections defined in the phase description. Include every required test function from Phases 1 through 7.

[Task possible affected files]

- `docs/strategy/bounded_cognition_test_matrix.md`

[Task important notes]
Do not group tests vaguely. Every test function must be listed by exact module path and exact function name.

[Task check list]

- [ ] Add Phase 1 tests
- [ ] Add Phase 2 tests
- [ ] Add Phase 3 tests
- [ ] Add Phase 4 tests
- [ ] Add Phase 5 tests
- [ ] Add Phase 6 tests
- [ ] Add Phase 7 tests
- [ ] Add shared fixture rules
- [ ] Add determinism requirements
- [ ] Add non-mutation requirements
- [ ] Add artifact-consistency requirements
- [ ] Add documentation-integrity requirements

[Task acceptance criteria]
The test matrix exists and enumerates the complete bounded-cognition proof surface exactly.

---

[ ] (checkbox) - [Task 3] - Create the exact UI contract document

[Task Description]
Document every UI-facing bounded-cognition and strategy field so frontend and inspection consumers can rely on a stable contract.

[Task technical implementation]
Create `docs/strategy/bounded_cognition_ui_contract.md` with the exact sections defined in the phase description. Document all schema fields, replay fields, graph fields, and their intended interpretation.

[Task possible affected files]

- `docs/strategy/bounded_cognition_ui_contract.md`

[Task important notes]
Do not describe fields informally. Include exact type, nullability, source, surface, and intended meaning for every field.

[Task check list]

- [ ] Add UI observability goals
- [ ] Add capacity schema contract
- [ ] Add budget-usage schema contract
- [ ] Add overload schema contract
- [ ] Add decision schema additions
- [ ] Add inspection schema additions
- [ ] Add full strategy coverage
- [ ] Add presenter serialization rules
- [ ] Add route contract
- [ ] Add CLI contract
- [ ] Add replay cognition contract
- [ ] Add graph cognition contract
- [ ] Add naming and nullability rules

[Task acceptance criteria]
The UI contract exists and covers every required field and surface exactly.

---

[ ] (checkbox) - [Task 4] - Create the exact tuning guide

[Task Description]
Document how bounded-cognition formulas and thresholds may be tuned safely without breaking determinism or feature semantics.

[Task technical implementation]
Create `docs/strategy/bounded_cognition_tuning_guide.md` with the exact section list defined in the phase description.

[Task possible affected files]

- `docs/strategy/bounded_cognition_tuning_guide.md`

[Task important notes]
Do not write generic balancing advice. Every tuning note must name exact formula groups or thresholds and exact regression classes to watch.

[Task check list]

- [ ] Add tuning goals
- [ ] Add normalization assumptions
- [ ] Add value-range guidance
- [ ] Add low-medium-high interpretation guidance
- [ ] Add appraisal tuning rules
- [ ] Add uncertainty tuning rules
- [ ] Add social tuning rules
- [ ] Add event tuning rules
- [ ] Add overload tuning rules
- [ ] Add safe change policy
- [ ] Add unsafe change examples
- [ ] Add regression watchlist
- [ ] Add scenario-based tuning checklist

[Task acceptance criteria]
The tuning guide exists and provides exact safe-tuning guidance for all bounded-cognition formula groups.

---

[ ] (checkbox) - [Task 5] - Add documentation-integrity audit helpers and tests

[Task Description]
Make the documentation executable against the code so drift is detected automatically.

[Task technical implementation]
Add `src/testing/doc_contract_audit.py` with the exact helper functions:

- `load_markdown_sections`
- `extract_bullet_values`
- `assert_required_strings_present`
- `assert_test_functions_exist`
- `assert_schema_fields_exist`

Add `tests/docs/test_bounded_cognition_docs_integrity.py` with the exact test functions listed in the phase description.

[Task possible affected files]

- `src/testing/doc_contract_audit.py`
- `tests/docs/test_bounded_cognition_docs_integrity.py`

[Task important notes]
Do not write brittle free-text snapshot tests. Use exact section extraction and exact required-field checks.

[Task check list]

- [ ] Add markdown section loader
- [ ] Add bullet extraction helper
- [ ] Add required-string assertion helper
- [ ] Add test-function existence helper
- [ ] Add schema-field existence helper
- [ ] Add feature-spec field coverage tests
- [ ] Add test-matrix completeness tests
- [ ] Add UI-contract field coverage tests
- [ ] Add replay field coverage tests
- [ ] Add graph field coverage tests
- [ ] Add test-function existence tests

[Task acceptance criteria]
Documentation-integrity tests prove that docs, schemas, replay artifacts, graph export, and test modules all align exactly.

---

[ ] (checkbox) - [Task 6] - Create the exact release checklist and closure audit tests

[Task Description]
Turn the completed bounded-cognition implementation into a release-auditable subsystem with one exact closure checklist.

[Task technical implementation]
Create `docs/strategy/bounded_cognition_release_checklist.md` with the exact sections defined in the phase description, using only checkbox items that map to implemented requirements from Phases 1 through 7.

Add `tests/docs/test_bounded_cognition_release_checklist.py` with the exact test functions:

- `test_release_checklist_contains_all_phase_headers`
- `test_release_checklist_references_all_required_artifact_classes`
- `test_release_checklist_references_all_required_schema_classes`
- `test_release_checklist_references_all_required_regression_scenarios`

Extend the headless regression runner so it sets:

- `cognition_consistency_checked = True`

only when:

- replay cognition assertions passed,
- graph cognition assertions passed,
- and documentation-integrity tests are green in the same validation run.

[Task possible affected files]

- `docs/strategy/bounded_cognition_release_checklist.md`
- `tests/docs/test_bounded_cognition_release_checklist.py`
- `src/testing/headless_regression_runner.py`

[Task important notes]
Do not let the release checklist become descriptive prose. It must be machine-auditable by the closure tests.

[Task check list]

- [ ] Add release checklist document
- [ ] Add all required phase headers
- [ ] Add artifact-class references
- [ ] Add schema-class references
- [ ] Add regression-scenario references
- [ ] Add checklist audit tests
- [ ] Gate manifest completion flag on consistency and docs integrity

[Task acceptance criteria]
The bounded-cognition feature has a machine-auditable release checklist and a final completion flag that only turns true when both artifact proof and documentation proof are satisfied.

---

Priority Plan

What must change in mindset or assumptions
Stop thinking of documentation as explanation after the fact. In this phase, documentation is part of the executable release contract.

What actions must be taken immediately
Write the feature spec, test matrix, UI contract, tuning guide, doc-audit helpers, documentation-integrity tests, release checklist, and closure-audit tests before calling the feature done.

What must stop or be eliminated
Stop relying on tribal knowledge. Stop allowing docs to drift from schemas and artifacts. Stop treating the feature as closed because the code works in isolation.

The consequences and opportunity cost if this fails
You will end up with a technically powerful bounded-cognition system that future engineers and UI consumers cannot trust, audit, or evolve safely. That means slower maintenance, more regressions, and eventual divergence between what the system does and what everyone thinks it does.
