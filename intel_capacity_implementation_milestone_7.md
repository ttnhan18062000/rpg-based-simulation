[Phase 7] - Extend Replay, Graph Export, and Headless Regression for Bounded Cognition

[Phase Description]
Phase 7 is the final-proof phase for the bounded-intelligence extension. Its purpose is to make bounded cognition part of the production-like regression path, not just part of live inspection. The current strategy epic already has a headless regression runner, replay artifacts, cognition graph export, and artifact-level assertions. This phase extends those exact surfaces so bounded cognition is visible in replay, visible in graph export, and verified through deterministic end-to-end scenarios. This phase is not about adding new behavior. It is about proving that the behavior added in Phases 1 through 6 survives a real engine run and remains consistent across artifacts. The current implementation already treats replay and graph export as the durable proof surfaces for strategic continuity, so bounded cognition must be integrated into those same artifacts rather than creating a separate test-only output path.

This phase must not add new strategic mechanics. It must not change the live API inspection contract from Phase 6. It must only extend replay, graph export, regression assertions, and deterministic end-to-end scenarios.

[Phase technical implementation]
Extend replay, graph export, and headless regression in one exact, aligned way.

First, define one exact replay-side cognition summary model. Add a new module, likely `src/testing/cognition_artifacts.py` if the codebase keeps artifact models together, or extend the existing replay artifact model family directly if replay summaries are already represented by typed models.

Define this exact typed model:

- `ReplayCognitionSummary`

`ReplayCognitionSummary` must contain these exact fields:

- `planning_budget: int`
- `judgment_stability: float`
- `evidence_quality: float`
- `social_bandwidth: int`
- `detour_depth_limit: int`
- `active_slice_limit: int`
- `ally_evaluation_limit: int`
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
- `is_overloaded: bool`
- `current_project_id: str | None`
- `current_objective_id: str | None`

Do not omit any of the above. Do not add extra replay cognition fields in this phase.

Then extend the replay entity snapshot or replay entity summary so each tracked entity contains:

- `cognition: ReplayCognitionSummary | None`

Use these exact rules when building replay cognition data:

1. If `entity.mind.decision.cognition_telemetry.profile is None`, set `cognition = None`
2. Otherwise serialize the fields listed above directly from:
   - `entity.mind.decision.cognition_telemetry`
   - `entity.mind.decision.cognition_telemetry.profile`
   - `entity.mind.strategic.current_project_id`
   - `entity.mind.strategic.current_objective_id`

3. Set:
   - `is_overloaded = True` if and only if `overload_score >= 0.70`
   - otherwise `False`

No other overload threshold is allowed in this phase.

Second, extend cognition graph export in one exact way. This phase must choose one representation and use it consistently. Use a dedicated bounded-cognition annotation node, not root-node-only attributes.

Add this exact graph node kind:

- `bounded_cognition`

Add this exact graph edge kind:

- `has_cognition_state`

For every exported entity graph, if `entity.mind.decision.cognition_telemetry.profile is not None`, add exactly one `bounded_cognition` node with:

- `node_id = f"cognition:{entity.id}"`
- `kind = "bounded_cognition"`
- `label = "Bounded Cognition"`
- `ref_id = f"cognition:{entity.id}"`

The `attributes` of that node must contain these exact keys:

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

No additional bounded-cognition graph attribute is allowed in this phase.

Add exactly one edge from the root entity node to this node:

- `edge_id = f"edge:entity:{entity.id}:has_cognition_state:cognition:{entity.id}"`
- `kind = "has_cognition_state"`
- `source_id = f"entity:{entity.id}"`
- `target_id = f"cognition:{entity.id}"`

If `profile is None`, do not add the node and do not add the edge.

Do not represent bounded cognition as multiple graph nodes in this phase.
Do not store it only as root attributes in this phase.
Do not serialize a partial subset of cognition telemetry into the graph in this phase.

Third, extend the headless regression runner artifact manifest. The runner manifest must now contain these exact fields:

- `seed`
- `ticks`
- `tracked_entity_ids`
- `replay_path`
- `graph_export_paths`
- `tracked_entities_with_cognition`
- `cognition_consistency_checked`

If a tracked entity exported a graph and also had replay cognition, its ID must be included in `tracked_entities_with_cognition`.

Fourth, extend the regression assertion helpers with exact bounded-cognition consistency checks.

Create or extend assertion helpers to expose these exact checks:

- `assert_replay_cognition_present_for_entity(replay_data, entity_id)`
- `assert_graph_cognition_node_present(graph_data, entity_id)`
- `assert_replay_graph_cognition_capacity_consistency(replay_data, graph_data, entity_id)`
- `assert_replay_graph_cognition_usage_consistency(replay_data, graph_data, entity_id)`
- `assert_replay_graph_overload_consistency(replay_data, graph_data, entity_id)`
- `assert_bounded_cognition_project_consistency(replay_data, graph_data, entity_id)`

These helpers must compare exactly the following overlapping semantics.

For capacity consistency, compare exact equality for:

- `planning_budget`
- `judgment_stability`
- `evidence_quality`
- `social_bandwidth`
- `detour_depth_limit`
- `active_slice_limit`
- `ally_evaluation_limit`

For usage consistency, compare exact equality for:

- `active_slice_used`
- `active_concerns_used`
- `retained_leads_used`
- `candidate_zones_used`
- `ally_evaluations_used`
- `detour_depth_used`
- `dropped_candidates_count`
- `latent_concerns_count`

For overload consistency, compare exact equality for:

- `overload_score`
- `primary_overload_source`
- `is_overloaded`

For project consistency, compare exact equality for:

- `current_project_id`
- `current_objective_id`

No other field comparison is allowed in this phase.

Fifth, add deterministic end-to-end scenario coverage for bounded cognition. Add these exact scenarios to the headless regression suite:

1. `bounded_slice_pressure_scenario`
2. `detour_depth_exhaustion_scenario`
3. `social_bandwidth_divergence_scenario`
4. `overload_flag_scenario`

These scenarios must be deterministic by seed and small enough to be run in CI.

The scenarios must prove these exact outcomes:

`bounded_slice_pressure_scenario`

- two tracked entities with different cognition-capacity profiles receive the same strategic pressure
- the higher-capacity entity has greater `active_slice_used` or lower `dropped_candidates_count`
- replay and graph agree on those fields

`detour_depth_exhaustion_scenario`

- at least one tracked entity reaches `detour_depth_used == detour_depth_limit`
- replay and graph agree on detour usage
- overload fields remain present and deterministic

`social_bandwidth_divergence_scenario`

- two tracked entities receive the same cooperation-demand scenario
- the higher-social-bandwidth entity has greater `ally_evaluations_used`
- replay and graph agree on this field

`overload_flag_scenario`

- at least one tracked entity reaches `overload_score >= 0.70`
- `is_overloaded == True` in replay
- graph cognition node carries `is_overloaded == True`
- `primary_overload_source` is non-null and consistent across artifacts

No other end-to-end scenario is required in this phase.

Sixth, add exact failure diagnostics. When a replay-vs-graph bounded-cognition assertion fails, the assertion helper must emit a concise structured diff with these exact keys:

- `entity_id`
- `field_name`
- `replay_value`
- `graph_value`
- `replay_path`
- `graph_path`

Do not emit vague “mismatch” errors in this phase.

[Phase important notes]
The main trap in this phase is creating a second cognition artifact contract unrelated to the existing replay and graph infrastructure. This phase must reuse those exact artifact paths because the point is final-system proof, not more bespoke telemetry.

The second trap is inconsistency between replay and graph representation. This phase chooses one exact graph representation — a single `bounded_cognition` node — and one exact replay representation — a single nested cognition summary. Do not let different callers serialize different subsets.

The third trap is comparing semantics that are not intentionally shared. This phase only compares the exact overlapping fields listed above. Do not invent extra consistency checks that rely on graph-only or replay-only details.

The fourth trap is using end-to-end scenarios that are too broad. These scenarios must be deterministic and minimal, otherwise they will become flaky and will not actually prove bounded cognition behavior.

The fifth trap is treating graph export as enough. This phase must prove consistency across both replay and graph, because that is the trustworthy final-system path.

[Phase acceptance criteria]
At the end of Phase 7, replay contains a bounded-cognition summary for tracked entities, cognition graph export contains exactly one bounded-cognition annotation node per tracked entity when telemetry exists, the headless runner records cognition-aware artifact metadata, regression helpers compare exact shared bounded-cognition semantics across replay and graph, and deterministic end-to-end scenarios prove bounded-slice pressure, detour-depth exhaustion, social-bandwidth divergence, and overload-flag behavior.

## Task

[ ] (checkbox) - [Task 1] - Add replay cognition summary contract

[Task Description]
Create the exact replay-side bounded-cognition summary model and integrate it into tracked entity replay output.

[Task technical implementation]
Add or extend replay artifact models to include `ReplayCognitionSummary` with the exact field list defined in the phase description, then attach:

- `cognition: ReplayCognitionSummary | None`

to each tracked replay entity summary.

Serialize cognition only when `entity.mind.decision.cognition_telemetry.profile` exists.

[Task possible affected files]

- `src/utils/replay.py`
- typed replay artifact modules if present

[Task important notes]
Do not flatten cognition fields into the top-level replay entity summary in this phase. Keep them nested under `cognition`.

[Task check list]

- [ ] Create `ReplayCognitionSummary`
- [ ] Add all required capacity fields
- [ ] Add all required usage fields
- [ ] Add overload fields
- [ ] Add current project and objective fields
- [ ] Attach `cognition` to replay tracked entity summary
- [ ] Apply exact `is_overloaded` threshold
- [ ] Keep replay serialization deterministic

[Task acceptance criteria]
Tracked replay entities serialize bounded cognition through one exact nested replay summary object.

---

[ ] (checkbox) - [Task 2] - Add exact bounded-cognition graph node export

[Task Description]
Extend graph export so bounded cognition becomes part of the structural artifact, not just live inspection.

[Task technical implementation]
Update the cognition graph exporter so that if cognition telemetry exists, it adds exactly:

- one `bounded_cognition` node
- one `has_cognition_state` edge from the entity root

using the exact node IDs, edge IDs, labels, and attribute keys defined in the phase description.

[Task possible affected files]

- `src/core/logic/cognition_graph_exporter.py`
- `src/core/models/cognition_graph.py`
- graph exporter tests

[Task important notes]
Do not represent bounded cognition as multiple nodes.
Do not skip usage fields and export only capacity.
Do not place bounded cognition only in root-node attributes.

[Task check list]

- [ ] Add `bounded_cognition` node kind handling
- [ ] Add `has_cognition_state` edge kind handling
- [ ] Add exact node ID rule
- [ ] Add exact edge ID rule
- [ ] Add exact label
- [ ] Add all required attribute keys
- [ ] Skip node creation when no profile exists
- [ ] Keep export deterministic

[Task acceptance criteria]
Graph export includes exactly one bounded-cognition node and one edge per entity when telemetry exists.

---

[ ] (checkbox) - [Task 3] - Extend headless runner manifest and artifact plumbing

[Task Description]
Make the headless regression runner explicitly aware of bounded-cognition artifacts.

[Task technical implementation]
Extend the runner manifest with these exact fields:

- `seed`
- `ticks`
- `tracked_entity_ids`
- `replay_path`
- `graph_export_paths`
- `tracked_entities_with_cognition`
- `cognition_consistency_checked`

Populate them deterministically during artifact writing.

[Task possible affected files]

- `src/testing/headless_regression_runner.py`
- artifact manifest module if present

[Task important notes]
Do not infer cognition presence after the fact by reading freeform logs. The manifest must record it directly.

[Task check list]

- [ ] Add `tracked_entities_with_cognition`
- [ ] Add `cognition_consistency_checked`
- [ ] Populate cognition-aware manifest fields deterministically
- [ ] Keep runner output stable by seed

[Task acceptance criteria]
The headless runner writes a manifest that explicitly records bounded-cognition artifact participation.

---

[ ] (checkbox) - [Task 4] - Add exact replay-vs-graph cognition assertion helpers

[Task Description]
Create deterministic consistency checks so bounded cognition is verified across final artifacts.

[Task technical implementation]
Add or extend assertion helpers to expose exactly:

- `assert_replay_cognition_present_for_entity`
- `assert_graph_cognition_node_present`
- `assert_replay_graph_cognition_capacity_consistency`
- `assert_replay_graph_cognition_usage_consistency`
- `assert_replay_graph_overload_consistency`
- `assert_bounded_cognition_project_consistency`

The helpers must compare only the exact overlapping fields listed in the phase description.

On mismatch, emit a structured diff with these exact keys:

- `entity_id`
- `field_name`
- `replay_value`
- `graph_value`
- `replay_path`
- `graph_path`

[Task possible affected files]

- `src/testing/assertions.py`
- helper utility modules used by end-to-end tests

[Task important notes]
Do not compare extra fields that are not intentionally shared between replay and graph. Keep the shared contract exact.

[Task check list]

- [ ] Add presence assertions
- [ ] Add capacity consistency assertion
- [ ] Add usage consistency assertion
- [ ] Add overload consistency assertion
- [ ] Add project consistency assertion
- [ ] Add structured mismatch diff output
- [ ] Keep assertion behavior deterministic

[Task acceptance criteria]
The regression suite can verify bounded-cognition consistency across replay and graph using exact field comparisons and structured diagnostics.

---

[ ] (checkbox) - [Task 5] - Add deterministic end-to-end bounded-cognition scenarios

[Task Description]
Prove that bounded cognition survives a real headless engine run and produces stable artifact-level divergence.

[Task technical implementation]
Add or extend end-to-end regression tests for these exact scenarios:

- `bounded_slice_pressure_scenario`
- `detour_depth_exhaustion_scenario`
- `social_bandwidth_divergence_scenario`
- `overload_flag_scenario`

Each scenario must:

- use a deterministic seed,
- export replay and graph artifacts,
- run the exact cognition assertion helpers,
- and prove the exact scenario-specific conditions listed in the phase description.

[Task possible affected files]

- `tests/e2e/test_bounded_slice_pressure_scenario.py`
- `tests/e2e/test_detour_depth_exhaustion_scenario.py`
- `tests/e2e/test_social_bandwidth_divergence_scenario.py`
- `tests/e2e/test_overload_flag_scenario.py`
- `src/testing/headless_regression_runner.py`

[Task important notes]
Keep scenarios small and explicit. These are proof scenarios, not sandbox demos.

[Task check list]

- [ ] Add bounded-slice pressure scenario
- [ ] Add detour-depth exhaustion scenario
- [ ] Add social-bandwidth divergence scenario
- [ ] Add overload-flag scenario
- [ ] Assert replay artifact values
- [ ] Assert graph artifact values
- [ ] Assert replay-vs-graph consistency
- [ ] Keep all scenarios deterministic

[Task acceptance criteria]
The regression suite proves bounded cognition end to end through deterministic artifact-level scenarios.

---

[ ] (checkbox) - [Task 6] - Add exact replay/export/regression documentation

[Task Description]
Document the final artifact contract for bounded cognition so the regression path remains auditable and maintainable.

[Task technical implementation]
Create:

- `docs/strategy/bounded_cognition_m7_artifact_contract.md`
- `docs/strategy/bounded_cognition_m7_test_matrix.md`

`bounded_cognition_m7_artifact_contract.md` must contain these exact sections:

1. Replay cognition summary contract
2. Graph bounded-cognition node contract
3. Headless runner manifest additions
4. Shared replay-vs-graph field set
5. Consistency assertion rules
6. Structured mismatch diff format
7. Deterministic scenario set
8. Non-goals for this phase

`bounded_cognition_m7_test_matrix.md` must contain these exact sections:

1. Replay serialization tests
2. Graph export tests
3. Manifest tests
4. Consistency assertion tests
5. End-to-end scenario tests

For every test function, document:

- test name
- fixture or scenario shape
- exact expected behavior
- regression caught

[Task possible affected files]

- `docs/strategy/bounded_cognition_m7_artifact_contract.md`
- `docs/strategy/bounded_cognition_m7_test_matrix.md`

[Task important notes]
Do not describe this phase vaguely. The exact replay fields, exact graph attributes, exact shared field set, and exact scenario expectations must all be written down.

[Task check list]

- [ ] Document replay cognition contract
- [ ] Document graph node contract
- [ ] Document manifest fields
- [ ] Document shared consistency field set
- [ ] Document mismatch diff format
- [ ] Document exact scenarios
- [ ] Document all required tests
- [ ] Document exact regression purpose for each test

[Task acceptance criteria]
Phase 7 has an exact artifact-contract document and exact test-matrix document that match implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop treating bounded cognition as “visible enough” because it appears in live inspection. In this phase it must become part of the final-system artifact proof path.

What actions must be taken immediately
Implement the exact replay summary, exact bounded-cognition graph node, exact manifest additions, exact replay-vs-graph assertions, and deterministic end-to-end scenarios before calling the feature fully verified.

What must stop or be eliminated
Stop relying on graph export alone. Stop relying on replay alone. Stop allowing replay and graph to tell slightly different stories about bounded cognition.

The consequences and opportunity cost if this fails
You will have a feature that looks good in live inspection but is weakly verified in the only place that really matters: the full engine run. That means regressions in bounded cognition will survive until they become expensive and confusing to diagnose.
