[Phase 2] - Integrate Cognition Capacity into Strategic Appraisal

[Phase Description]
Phase 2 is the behavioral integration phase for the bounded-intelligence extension. Its purpose is to make strategic appraisal entity-specific and bounded without changing the authoritative storage model introduced by the strategy epic. In Phase 1, the system gained an exact `CognitionCapacityProfile` contract. In Phase 2, the brain must start using that profile to decide how many strategic candidates an entity can actively evaluate, how strongly it resists interruption, how reliably it maintains project continuity, and how aggressively it truncates noisy alternatives. The current codebase already has the right insertion point for this work because strategic appraisal exists before tactical deliberation, and strategy is already exposed through the structured presenter path rather than through ad hoc metadata.

This phase must not yet modify blocker learning depth, detour recursion behavior, social contract reasoning quality, or event-interpretation quality. Those belong to later phases. This phase is only about using cognition capacity to bound and stabilize the strategic candidate set, project continuity, and objective continuity.

[Phase technical implementation]
Create a bounded strategic appraisal layer that consumes the `CognitionCapacityProfile` produced in Phase 1 and applies it to the existing strategic selection pipeline.

Add a new appraisal-side working module, likely `src/ai/strategic_bounded_appraisal.py`, containing these exact derived working models:

- `StrategicCandidate`
- `BoundedStrategicSlice`
- `StrategicDecisionOutcome`

`StrategicCandidate` must contain these exact fields:

- `candidate_id: str`
- `kind: str`
- `source_id: str`
- `score: float`
- `continuity_score: float`
- `urgency_score: float`
- `salience_score: float`
- `capacity_fit_score: float`
- `source_kind: str`
- `is_current_project: bool`
- `is_current_objective: bool`
- `is_interrupting: bool`

`BoundedStrategicSlice` must contain these exact fields:

- `profile: CognitionCapacityProfile`
- `candidates: list[StrategicCandidate]`
- `dropped_candidates_count: int`
- `dropped_concerns_count: int`
- `dropped_leads_count: int`
- `dropped_suspended_projects_count: int`
- `reserved_current_project_slot_used: bool`

`StrategicDecisionOutcome` must contain these exact fields:

- `selected_project_id: str | None`
- `selected_objective_id: str | None`
- `kept_current_project: bool`
- `switched_project: bool`
- `switch_margin_used: float`
- `interrupting_candidate_id: str | None`
- `bounded_slice: BoundedStrategicSlice`

Add one exact orchestrator:

- `BoundedStrategicAppraisalService.evaluate(entity, snapshot, tick) -> StrategicDecisionOutcome`

This service must be called inside the existing strategic appraisal phase before tactical deliberation. It must not mutate authoritative state directly. Any selected continuity changes must still be emitted through typed strategic updates later, consistent with the strategy epic’s authoritative-update discipline.

The service must gather raw candidates from exactly these sources in this phase:

1. current project
2. current objective
3. unresolved concerns
4. unresolved obligations
5. suspended projects
6. active blockers tied to the current project
7. fresh unresolved leads
8. active contracts that bind current work

No other candidate source is allowed in this phase.

Implement these exact normalization helpers inside the appraisal module:

```python
def _clamp(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value

def _norm_weight(value: float | None, default: float = 1.0, max_value: float = 2.0) -> float:
    if value is None:
        value = default
    return _clamp(value / max_value, 0.0, 1.0)

def _bool_score(flag: bool) -> float:
    return 1.0 if flag else 0.0
```

For record models that do not already expose the following exact appraisal fields, add them in this phase:

- for projects:
  - `priority`
  - `urgency`
  - `salience`
  - `abandonment_cost`
  - `active_objective_id`
  - `status`
  - `last_selected_tick`

- for concerns:
  - `priority`
  - `urgency`
  - `salience`
  - `source_project_id`

- for obligations:
  - `priority`
  - `urgency`
  - `deadline_pressure`

- for leads:
  - `priority`
  - `confidence`
  - `freshness`
  - `source_quality`

- for blockers:
  - `severity`
  - `source_project_id`

- for contracts:
  - `priority`
  - `status`

If those fields already exist, do not duplicate them. If any are missing, add them explicitly in this phase rather than improvising hidden defaults inside appraisers.

The raw candidate scoring must use these exact formulas.

For a **current project** candidate:

Let:

- `p = _norm_weight(project.priority, 1.0, 2.0)`
- `u = _norm_weight(project.urgency, 1.0, 2.0)`
- `s = _norm_weight(project.salience, 1.0, 2.0)`
- `a = _norm_weight(project.abandonment_cost, 1.0, 2.0)`

Compute:

```python
score = round(
    _clamp(
        0.30 * p +
        0.20 * u +
        0.15 * s +
        0.25 * a +
        0.10 * profile.resume_reliability,
        0.0,
        1.0,
    ),
    3,
)
```

For a **concern** candidate:

Let:

- `p = _norm_weight(concern.priority, 1.0, 2.0)`
- `u = _norm_weight(concern.urgency, 1.0, 2.0)`
- `s = _norm_weight(concern.salience, 1.0, 2.0)`

Compute:

```python
score = round(
    _clamp(
        0.25 * p +
        0.40 * u +
        0.25 * s +
        0.10 * (1.0 - profile.interruption_resistance),
        0.0,
        1.0,
    ),
    3,
)
```

For an **obligation** candidate:

Let:

- `p = _norm_weight(obligation.priority, 1.0, 2.0)`
- `u = _norm_weight(obligation.urgency, 1.0, 2.0)`
- `d = _norm_weight(obligation.deadline_pressure, 1.0, 2.0)`

Compute:

```python
score = round(
    _clamp(
        0.30 * p +
        0.35 * u +
        0.25 * d +
        0.10 * profile.judgment_stability,
        0.0,
        1.0,
    ),
    3,
)
```

For a **suspended project** candidate:

Let:

- `p = _norm_weight(project.priority, 1.0, 2.0)`
- `u = _norm_weight(project.urgency, 1.0, 2.0)`
- `a = _norm_weight(project.abandonment_cost, 1.0, 2.0)`

Compute:

```python
score = round(
    _clamp(
        0.25 * p +
        0.20 * u +
        0.25 * a +
        0.30 * profile.resume_reliability,
        0.0,
        1.0,
    ),
    3,
)
```

For a **lead follow-up** candidate:

Let:

- `p = _norm_weight(lead.priority, 1.0, 2.0)`
- `c = _clamp(lead.confidence if lead.confidence is not None else 0.5, 0.0, 1.0)`
- `f = _clamp(lead.freshness if lead.freshness is not None else 0.5, 0.0, 1.0)`
- `q = _clamp(lead.source_quality if lead.source_quality is not None else 0.5, 0.0, 1.0)`

Compute:

```python
score = round(
    _clamp(
        0.20 * p +
        0.25 * c +
        0.20 * f +
        0.20 * q +
        0.15 * profile.evidence_quality,
        0.0,
        1.0,
    ),
    3,
)
```

For a **blocker-resolution** candidate:

Let:

- `sev = _norm_weight(blocker.severity, 1.0, 2.0)`
- `proj = current_project_score if current project exists else 0.0`

Compute:

```python
score = round(
    _clamp(
        0.40 * sev +
        0.30 * proj +
        0.15 * profile.planning_budget / 9.0 +
        0.15 * profile.blocker_resolution_patience,
        0.0,
        1.0,
    ),
    3,
)
```

For an **active contract** candidate:

Let:

- `p = _norm_weight(contract.priority, 1.0, 2.0)`
- `active = 1.0 if contract.status == "active" else 0.5`

Compute:

```python
score = round(
    _clamp(
        0.35 * p +
        0.35 * active +
        0.30 * (profile.social_bandwidth / 7.0),
        0.0,
        1.0,
    ),
    3,
)
```

After scoring, apply these exact pre-bounds:

1. unresolved concerns -> keep top `profile.concern_intake_limit` by score
2. fresh unresolved leads -> keep top `profile.lead_retention_limit` by score
3. suspended projects -> keep top `profile.planning_budget` by score
4. active contracts -> keep top `profile.social_bandwidth` by score
5. blocker-resolution candidates -> keep top `profile.detour_depth_limit + 1` by score

Always include the current project candidate if it exists and is unresolved. This reserved slot is mandatory in Phase 2 and must set `reserved_current_project_slot_used = True`.

Merge the bounded partitions, remove exact duplicates by `(kind, source_id)` keeping the highest-scoring candidate, and then sort all remaining candidates by this exact deterministic key:

1. `score` descending
2. `is_current_project` descending
3. `urgency_score` descending
4. `candidate_id` ascending

After sorting, apply the final slice cap:

- if a reserved current-project slot exists, keep it plus the top `profile.active_slice_limit - 1` remaining candidates
- otherwise keep the top `profile.active_slice_limit` candidates

Set:

- `dropped_candidates_count`
- `dropped_concerns_count`
- `dropped_leads_count`
- `dropped_suspended_projects_count`

exactly from the number of items removed during pre-bounds and final slicing.

Project continuity must then be resolved with this exact switch rule.

Let:

- `current_score = score of current project candidate` if it exists, else `0.0`
- `best_rival_score = highest score among non-current-project candidates`, else `0.0`

Define:

```python
switch_margin = round(
    _clamp(
        0.10 +
        0.25 * profile.interruption_resistance +
        0.15 * profile.judgment_stability,
        0.10,
        0.45,
    ),
    3,
)
```

If `current project` exists, keep it unless:

```python
best_rival_score > current_score + switch_margin
```

If that inequality is true, switch to the rival candidate’s project source or create a project-selection outcome tied to that rival’s source type. Set:

- `kept_current_project = False`
- `switched_project = True`
- `interrupting_candidate_id = rival.candidate_id`

If the inequality is false, keep current project and set:

- `kept_current_project = True`
- `switched_project = False`

If there is no current project, select the highest-scoring candidate that can map to a project. That mapping must use these exact rules in this phase:

- project candidate -> selected project is that project
- suspended project candidate -> selected project is that suspended project
- concern candidate -> create or reuse concern-driven project shell in later project-selection service, but for this phase outcome set `selected_project_id = None` and carry the candidate as interrupting source
- obligation candidate -> same as concern mapping rule
- lead candidate -> no project change in this phase, only objective pressure
- blocker candidate -> no project change in this phase, only objective pressure
- contract candidate -> retain current project unless it is the only available candidate

Objective continuity must use this exact rule:

If the selected project is the current project and `current_objective_id` still belongs to that project and no blocker candidate scored above `0.70`, keep current objective.

Otherwise derive a new objective with this exact source precedence:

1. blocker candidate tied to selected project
2. lead candidate tied to selected project
3. obligation candidate tied to selected project
4. concern candidate tied to selected project
5. project’s `active_objective_id`
6. first unresolved objective in project order

No other precedence order is allowed in this phase.

The `StrategicDecisionOutcome` must be converted later into typed strategic updates and structured decision drivers. This phase must not directly mutate `entity.mind.strategic`.

[Phase important notes]
The main trap in this phase is candidate explosion. The phase must not gather a rich set of strategic possibilities and then casually pass them all downstream. Every strategic source listed above must be bounded exactly by the profile. If you skip hard caps, the feature becomes expressive in code and noisy in behavior.

The second trap is fake continuity. Always reserving a current-project slot does not mean always keeping the current project. Continuity is preserved by keeping the project in the decision slice, then using the exact switch rule to decide whether it survives. If you skip the reserved slot, low-budget entities will churn too aggressively. If you skip the switch rule, they will cling to stale work forever.

The third trap is hidden decision-making. Every dropped count, reserved-slot usage, and switch margin must be available for later structured explainability. Phase 2 must not silently prune cognition.

The fourth trap is scope drift. This phase must not yet add profile-sensitive blocker learning, detour recursion quality, contract stabilization quality, or event-interpretation quality. Those belong later. This phase only integrates capacity into candidate gathering, bounded slicing, continuity, and objective retention.

[Phase acceptance criteria]
At the end of Phase 2, strategic appraisal builds a deterministic bounded candidate set, keeps the current project in consideration through a reserved-slot rule, uses the exact switch-margin formula to decide project continuity, and derives objective continuity through the exact precedence chain. The result is exposed as a structured `StrategicDecisionOutcome` and remains non-mutating until later authoritative updates are emitted.

## Task

[ ] (checkbox) - [Task 1] - Add bounded strategic appraisal working models

[Task Description]
Create the exact derived working models that represent bounded candidate evaluation and the continuity decision outcome.

[Task technical implementation]
Add `src/ai/strategic_bounded_appraisal.py` and define exactly:

- `StrategicCandidate`
- `BoundedStrategicSlice`
- `StrategicDecisionOutcome`

with the exact field lists defined in the phase description.

[Task possible affected files]

- `src/ai/strategic_bounded_appraisal.py`

[Task important notes]
These are appraisal-side derived models only. They are not authoritative persistent entity state and they must not be stored inside `MindAspect` in this phase.

[Task check list]

- [ ] Add `StrategicCandidate`
- [ ] Add `BoundedStrategicSlice`
- [ ] Add `StrategicDecisionOutcome`
- [ ] Keep all field names exact
- [ ] Keep models typed and deterministic
- [ ] Avoid hidden mutable dict payloads

[Task acceptance criteria]
The codebase compiles with exact bounded-appraisal working models that match the required field contract.

---

[ ] (checkbox) - [Task 2] - Implement candidate gathering, scoring, and pre-bounds

[Task Description]
Build the exact bounded candidate-set construction pipeline from existing strategic state.

[Task technical implementation]
Implement `BoundedStrategicAppraisalService.evaluate(entity, snapshot, tick)` to gather candidates from exactly:

- current project
- current objective
- unresolved concerns
- unresolved obligations
- suspended projects
- active blockers tied to current project
- fresh unresolved leads
- active contracts that bind current work

Add the exact normalization helpers and the exact per-candidate scoring formulas defined above.

Then apply these exact pre-bounds:

- concerns -> top `profile.concern_intake_limit`
- leads -> top `profile.lead_retention_limit`
- suspended projects -> top `profile.planning_budget`
- active contracts -> top `profile.social_bandwidth`
- blocker-resolution candidates -> top `profile.detour_depth_limit + 1`

Always reserve one slot for the current project if it exists and is unresolved.

[Task possible affected files]

- `src/ai/strategic_bounded_appraisal.py`
- `src/core/models/strategy.py` if required appraisal fields are missing on records

[Task important notes]
If appraisal-required fields are missing on any strategic record, add them explicitly. Do not hide implicit defaults in ad hoc appraiser code without making the model requirements explicit.

[Task check list]

- [ ] Gather raw candidates from the exact allowed sources
- [ ] Add normalization helpers
- [ ] Implement current-project score formula
- [ ] Implement concern score formula
- [ ] Implement obligation score formula
- [ ] Implement suspended-project score formula
- [ ] Implement lead score formula
- [ ] Implement blocker score formula
- [ ] Implement contract score formula
- [ ] Apply exact pre-bounds
- [ ] Reserve current-project slot when applicable
- [ ] Track dropped counts exactly

[Task acceptance criteria]
The service produces a bounded candidate pool using the exact source list, formulas, and pre-bound rules.

---

[ ] (checkbox) - [Task 3] - Implement deterministic final slice construction and continuity decision

[Task Description]
Convert the bounded candidate pool into a final strategic slice and continuity outcome without mutating authoritative state.

[Task technical implementation]
Implement these exact steps:

1. merge pre-bounded candidates
2. deduplicate by `(kind, source_id)` keeping highest score
3. sort using the exact deterministic key
4. apply final `active_slice_limit`
5. compute `switch_margin`
6. keep or switch current project using the exact inequality rule
7. derive objective continuity using the exact precedence order
8. return `StrategicDecisionOutcome`

[Task possible affected files]

- `src/ai/strategic_bounded_appraisal.py`
- `src/ai/brain.py`

[Task important notes]
Do not directly mutate `entity.mind.strategic`. The result must remain a derived outcome that later strategic-update emission can consume.

[Task check list]

- [ ] Deduplicate candidates deterministically
- [ ] Sort candidates with exact tie rules
- [ ] Apply final slice cap
- [ ] Compute `switch_margin`
- [ ] Apply exact keep/switch rule
- [ ] Apply exact objective-retention rule
- [ ] Apply exact objective-derivation precedence
- [ ] Return structured non-mutating outcome

[Task acceptance criteria]
The service returns a deterministic `StrategicDecisionOutcome` that captures bounded slicing and project/objective continuity without mutating stored strategy.

---

[ ] (checkbox) - [Task 4] - Integrate bounded appraisal into the brain pipeline

[Task Description]
Route the new bounded-appraisal layer into the existing strategic appraisal flow so entities start using cognition capacity during thinking.

[Task technical implementation]
Update the strategic phase in `AIBrain` so it:

1. builds `CognitionCapacityProfile`
2. calls `BoundedStrategicAppraisalService.evaluate`
3. converts the returned outcome into later strategic-update emission and structured decision drivers
4. keeps the tactical layer downstream of the selected bounded result

Do not bypass the existing structured strategy presentation path. The later UI/API work depends on this remaining coherent with current strategy explainability surfaces.

[Task possible affected files]

- `src/ai/brain.py`
- `src/ai/strategic_bounded_appraisal.py`
- presenter/debug driver code if structured driver surfaces are extended internally

[Task important notes]
Do not let tactical goal scoring re-expand the candidate space. Tactical logic must consume the bounded strategic result, not rebuild a larger life-direction search.

[Task check list]

- [ ] Build profile at strategic phase entry
- [ ] Call bounded appraisal service
- [ ] Route outcome into continuity handling
- [ ] Keep tactical layer downstream only
- [ ] Preserve structured explainability discipline

[Task acceptance criteria]
The brain uses bounded strategic appraisal before tactics, and tactical choice no longer sees an unbounded strategic frontier.

---

[ ] (checkbox) - [Task 5] - Add deterministic tests for bounded slicing and continuity

[Task Description]
Lock the behavioral contract so Phase 2 cannot silently degrade into either project churn or unbounded candidate noise.

[Task technical implementation]
Add these exact test files:

- `tests/ai/test_bounded_strategic_slice.py`
- `tests/ai/test_bounded_project_continuity.py`
- `tests/ai/test_bounded_objective_continuity.py`

Required exact test functions:

In `test_bounded_strategic_slice.py`

- `test_low_profile_entity_has_smaller_active_slice_than_high_profile_entity`
- `test_concern_intake_is_capped_by_profile`
- `test_lead_retention_is_capped_by_profile`
- `test_reserved_current_project_slot_is_used_when_current_project_exists`
- `test_dropped_candidate_counts_are_deterministic`

In `test_bounded_project_continuity.py`

- `test_current_project_is_kept_when_rival_does_not_exceed_switch_margin`
- `test_current_project_switches_when_rival_exceeds_switch_margin`
- `test_switch_margin_depends_on_interruption_resistance_and_judgment_stability`
- `test_no_current_project_selects_highest_valid_project_source`

In `test_bounded_objective_continuity.py`

- `test_current_objective_is_retained_when_valid_and_no_high_blocker_exists`
- `test_blocker_above_threshold_forces_objective_rederivation`
- `test_objective_derivation_uses_exact_precedence_order`
- `test_bounded_appraisal_does_not_mutate_strategic_state`

[Task possible affected files]

- `tests/ai/test_bounded_strategic_slice.py`
- `tests/ai/test_bounded_project_continuity.py`
- `tests/ai/test_bounded_objective_continuity.py`

[Task important notes]
Use controlled fixtures with identical strategic state and different cognition profiles to prove bounded-cognition divergence. Do not use vague scenario tests here.

[Task check list]

- [ ] Add bounded slice width tests
- [ ] Add concern cap tests
- [ ] Add lead cap tests
- [ ] Add reserved-slot test
- [ ] Add deterministic dropped-count test
- [ ] Add keep-project switch-margin test
- [ ] Add switch-project switch-margin test
- [ ] Add current-objective retention test
- [ ] Add blocker-triggered objective replacement test
- [ ] Add non-mutation test

[Task acceptance criteria]
Phase 2 ships with deterministic tests proving bounded candidate slicing, continuity stability, switch behavior, and objective retention rules.

---

[ ] (checkbox) - [Task 6] - Add exact decision-flow documentation

[Task Description]
Document the operational semantics of bounded strategic appraisal so the phase is auditable and later phases can build on it without reinterpreting the rules.

[Task technical implementation]
Create:

- `docs/strategy/bounded_cognition_m2_decision_flow.md`
- `docs/strategy/bounded_cognition_m2_test_matrix.md`

`bounded_cognition_m2_decision_flow.md` must contain these exact sections:

1. Candidate sources
2. Candidate working models
3. Normalization helpers
4. Scoring formulas by candidate kind
5. Pre-bound rules
6. Final slice construction rules
7. Project keep/switch rule
8. Objective retention and derivation rule
9. Non-mutation rule
10. Non-goals for this phase

`bounded_cognition_m2_test_matrix.md` must contain these exact sections:

1. Slice-width tests
2. Concern and lead cap tests
3. Project continuity tests
4. Objective continuity tests
5. Non-mutation tests

For every test function, document:

- test name
- fixture shape
- exact expected behavior
- regression caught

[Task possible affected files]

- `docs/strategy/bounded_cognition_m2_decision_flow.md`
- `docs/strategy/bounded_cognition_m2_test_matrix.md`

[Task important notes]
Do not describe this phase in prose only. The formulas, bounds, tie-break rules, and switch rules must be written exactly.

[Task check list]

- [ ] Document exact candidate sources
- [ ] Document exact candidate fields
- [ ] Document exact scoring formulas
- [ ] Document exact bound rules
- [ ] Document exact switch-margin rule
- [ ] Document exact objective precedence
- [ ] Document all required tests
- [ ] Document exact regression purpose of each test

[Task acceptance criteria]
Phase 2 has an exact operational decision-flow document and exact test-matrix document that match implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop treating cognition capacity as a passive stat sheet. In this phase it becomes a hard bound on what strategic reasoning is allowed to consider.

What actions must be taken immediately
Implement the bounded candidate models, exact scoring formulas, exact bound rules, exact keep/switch rule, exact objective-precedence rule, and deterministic tests before touching blocker recursion, social cognition quality, or event-interpretation quality.

What must stop or be eliminated
Stop allowing strategic appraisal to consider an unbounded frontier. Stop letting current-project continuity be implicit. Stop hiding candidate pruning from explainability.

The consequences and opportunity cost if this fails
You will have a clean cognition-capacity profile from Phase 1 but no real bounded-reasoning behavior, which means all entities will still think over roughly the same noisy frontier and the overload problem will remain structurally unsolved.
