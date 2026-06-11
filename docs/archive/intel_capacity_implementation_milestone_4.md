---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

[Phase 4] - Apply Cognition Capacity to Social Reasoning and Cooperation

[Phase Description]
Phase 4 is the social-reasoning phase for the bounded-intelligence extension. Its purpose is to make entities differ in how well they recognize when a project is not solo-viable, how many ally candidates they can evaluate cleanly, how accurately they rank those candidates, and how stable a cooperation plan is likely to remain once a contract-backed effort starts. The strategy epic already established cooperation, obligations, and social contracts as structural parts of strategic life rather than cosmetic group behavior. This phase does not invent those systems. It applies the `CognitionCapacityProfile` from Phase 1 and the bounded-appraisal discipline from Phase 2 so that cooperation quality becomes entity-specific, deterministic, and bounded. The current architecture already has structured strategic presentation, contract-like social state, and bounded strategic reasoning, so this phase extends that same discipline rather than creating a separate social AI path.

This phase must not yet change event-interpretation quality. It must not yet change replay or API schema exposure for bounded cognition. Those belong to later phases. This phase is only about cooperation-need detection, bounded ally evaluation, deterministic ally ranking, and contract-stability forecasting.

[Phase technical implementation]
Create a new module, `src/ai/strategic_social_reasoning.py`, and define these exact derived working models:

- `CooperationNeedAssessment`
- `AllySuitabilityScore`
- `ContractStabilityForecast`

`CooperationNeedAssessment` must contain these exact fields:

- `project_id: str | None`
- `requires_cooperation: bool`
- `recognized_need: bool`
- `need_score: float`
- `recognition_score: float`
- `missing_role_tags: list[str]`
- `recommended_recruitment_objective_kind: str | None`
- `minimum_party_size: int`
- `current_party_size: int`

`AllySuitabilityScore` must contain these exact fields:

- `candidate_entity_id: int`
- `role_fit_score: float`
- `trust_score: float`
- `loyalty_score: float`
- `debt_score: float`
- `familiarity_score: float`
- `admiration_score: float`
- `resentment_penalty: float`
- `obligation_conflict_penalty: float`
- `project_conflict_penalty: float`
- `availability_score: float`
- `total_score: float`
- `accepted_by_filter: bool`

`ContractStabilityForecast` must contain these exact fields:

- `project_id: str | None`
- `candidate_ids: list[int]`
- `role_coverage_ratio: float`
- `average_trust: float`
- `average_loyalty: float`
- `average_familiarity: float`
- `average_resentment: float`
- `stability_score: float`
- `stability_label: str`

Add one exact service class:

- `StrategicSocialReasoningService`

This class must expose these exact static methods:

- `assess_cooperation_need(entity, strategic_state, current_project, tick) -> CooperationNeedAssessment | None`
- `score_allies(entity, candidate_entities, social_registry, assessment, tick) -> list[AllySuitabilityScore]`
- `forecast_contract_stability(entity, selected_scores, assessment, tick) -> ContractStabilityForecast`

The service must consume `CognitionCapacityProfile` from Phase 1. It must not mutate authoritative state directly. It must return derived outcomes that later strategic-update emission can convert into project updates, recruitment objectives, or contract proposals.

The current project model must expose these exact fields for this phase. If any are missing, add them explicitly rather than inferring them silently:

- `risk_score`
- `minimum_party_size`
- `required_role_tags`
- `solo_viable`
- `social_complexity`
- `active_member_ids`

The allowed `required_role_tags` in this phase are exactly:

- `frontliner`
- `scout`
- `caster`
- `generalist`

No other role tag is allowed in this phase.

The role-tag mapping for a candidate entity must use these exact rules:

1. If candidate hero class is `WARRIOR` or `TANK`, candidate tags are:
   - `frontliner`
   - `generalist`

2. If candidate hero class is `RANGER` or `ROGUE`, candidate tags are:
   - `scout`
   - `generalist`

3. If candidate hero class is `MAGE`, candidate tags are:
   - `caster`
   - `generalist`

4. Otherwise, candidate tags are:
   - `generalist`

No other role-tag mapping is allowed in this phase.

Add these exact helper functions:

```python id="cgqyvl"
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

def _safe_ratio(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return _clamp(value / max_value, 0.0, 1.0)

def _norm_relation(value: float | None) -> float:
    if value is None:
        return 0.0
    return _clamp(value, 0.0, 1.0)
```

Let:

- `social = profile.social_bandwidth / 7.0`
- `judgment = profile.judgment_stability`
- `resume = profile.resume_reliability`
- `interrupt = profile.interruption_resistance`
- `planning = profile.planning_budget / 9.0`

For cooperation-need detection, define:

- `risk = _norm_weight(project.risk_score, 1.0, 2.0)`
- `party_pressure = _safe_ratio(max(project.minimum_party_size - 1, 0), 3.0)`
- `role_gap_ratio = _safe_ratio(len(missing_role_tags), max(len(project.required_role_tags), 1))`
- `solo_pressure = 0.0 if project.solo_viable else 1.0`
- `social_complexity = _norm_weight(project.social_complexity, 1.0, 2.0)`

Then compute `need_score` using this exact formula:

```python id="15s7zm"
need_score = round(
    _clamp(
        0.30 * risk +
        0.20 * party_pressure +
        0.20 * role_gap_ratio +
        0.20 * solo_pressure +
        0.10 * social_complexity,
        0.0,
        1.0,
    ),
    3,
)
```

Then compute `recognition_score` using this exact formula:

```python id="m2wdft"
recognition_score = round(
    _clamp(
        need_score *
        (0.40 + 0.30 * judgment + 0.30 * planning),
        0.0,
        1.0,
    ),
    3,
)
```

Then set:

- `requires_cooperation = True` if and only if `need_score >= 0.55`
- `recognized_need = True` if and only if `recognition_score >= 0.50`

The `recommended_recruitment_objective_kind` must be chosen by this exact precedence rule applied to `missing_role_tags`:

1. if `"frontliner"` is missing -> `recruit_frontliner`
2. else if `"scout"` is missing -> `recruit_scout`
3. else if `"caster"` is missing -> `recruit_caster`
4. else if `requires_cooperation` is true -> `recruit_generalist`
5. else -> `None`

No other recruitment objective kind is allowed in this phase.

For ally scoring, every candidate entity must first pass these exact filters:

1. candidate ID is not equal to initiator ID
2. candidate is alive
3. candidate is not already in `current_project.active_member_ids`
4. `obligation_conflict_penalty < 0.75`
5. `project_conflict_penalty < 0.75`
6. at least one of the following is true:
   - `trust_score >= 0.20`
   - `loyalty_score >= 0.30`
   - `debt_score >= 0.30`

If any filter fails, set:

- `accepted_by_filter = False`
- `total_score = 0.0`

No candidate failing the filter may be considered further.

For relation extraction, use these exact normalized relation values from the social registry or fallback `0.0` if missing:

- `trust_score`
- `loyalty_score`
- `debt_score`
- `familiarity_score`
- `admiration_score`
- `resentment_penalty`

Use `_norm_relation` for all six.

For conflict extraction, use these exact values:

- `obligation_conflict_penalty = _clamp(candidate_active_obligation_pressure, 0.0, 1.0)`
- `project_conflict_penalty = _clamp(candidate_current_project_conflict, 0.0, 1.0)`

If these fields are unavailable in the current implementation, add deterministic accessors that return `0.0` by default.

For availability, use:

```python id="tb34sv"
availability_score = round(
    _clamp(
        1.0 - max(obligation_conflict_penalty, project_conflict_penalty),
        0.0,
        1.0,
    ),
    3,
)
```

Role-fit must use this exact rule:

- `role_fit_score = 1.0` if candidate role tags intersect `missing_role_tags`
- else `role_fit_score = 0.40` if candidate has `generalist`
- else `role_fit_score = 0.0`

If `missing_role_tags` is empty and `requires_cooperation = True`, then:

- `role_fit_score = 0.75` if candidate has `generalist`
- else `role_fit_score = 0.0`

Then compute `total_score` using this exact formula:

```python id="p27z8y"
total_score = round(
    _clamp(
        0.20 * role_fit_score +
        0.20 * trust_score +
        0.15 * loyalty_score +
        0.10 * debt_score +
        0.10 * familiarity_score +
        0.10 * admiration_score +
        0.10 * availability_score +
        0.05 * social +
        0.05 * judgment -
        0.10 * resentment_penalty -
        0.10 * obligation_conflict_penalty -
        0.10 * project_conflict_penalty,
        0.0,
        1.0,
    ),
    3,
)
```

After scoring all candidates, sort them with this exact deterministic key:

1. `accepted_by_filter` descending
2. `total_score` descending
3. `role_fit_score` descending
4. `trust_score` descending
5. `candidate_entity_id` ascending

Then keep only the top `profile.ally_evaluation_limit` candidates.

No more than `profile.ally_evaluation_limit` candidate scores may survive in this phase.

For contract-stability forecasting, use the top selected ally scores that would be chosen for recruitment. Compute:

- `role_coverage_ratio = matched_required_roles / max(len(required_role_tags), 1)`
- `average_trust = arithmetic mean of trust_score`
- `average_loyalty = arithmetic mean of loyalty_score`
- `average_familiarity = arithmetic mean of familiarity_score`
- `average_resentment = arithmetic mean of resentment_penalty`

If there are no selected scores, all averages are `0.0` and `role_coverage_ratio = 0.0`.

Then compute `stability_score` using this exact formula:

```python id="nz00w4"
stability_score = round(
    _clamp(
        0.20 * role_coverage_ratio +
        0.20 * average_trust +
        0.15 * average_loyalty +
        0.10 * average_familiarity +
        0.10 * social +
        0.10 * resume +
        0.10 * interrupt +
        0.05 * judgment -
        0.10 * average_resentment,
        0.0,
        1.0,
    ),
    3,
)
```

Then assign `stability_label` using this exact threshold table:

- `stable` if `stability_score >= 0.75`
- `fragile` if `0.50 <= stability_score < 0.75`
- `unstable` if `stability_score < 0.50`

No other label is allowed in this phase.

This phase must not create or mutate contracts directly. It must only return a deterministic forecast that later contract-creation and contract-update logic can consume.

[Phase important notes]
The main trap in this phase is confusing social desire with cooperation quality. A low-`cha` entity may still want help. This phase must make it worse at recognizing the right time to recruit, selecting the right candidates, and sustaining a stable plan, not less social in personality.

The second trap is unbounded ally search. The current design already warns that cognition must stay bounded. In this phase, ally ranking must be hard-capped by `profile.ally_evaluation_limit`. Do not let entities evaluate every possible ally in range or in faction.

The third trap is fuzzy role matching. This phase uses an exact role-tag vocabulary and exact class-to-role mapping to stay deterministic and testable. Do not add extra tags in this phase.

The fourth trap is premature contract mutation. This phase only assesses need, ranks candidates, and forecasts stability. It does not yet authoritatively create, modify, or dissolve contracts itself.

[Phase acceptance criteria]
At the end of Phase 4, cooperation need is profile-sensitive and deterministic, ally evaluation is bounded by `social_bandwidth` and `ally_evaluation_limit`, candidate ranking follows the exact formula and filter rules, and contract stability is forecast with an exact deterministic score and label. No unbounded ally search remains in strategic cooperation reasoning.

## Task

[x] (checkbox) - [Task 1] - Add social-reasoning working models and service surface

[Task Description]
Create the exact derived working models and service interface for cooperation-need detection, bounded ally scoring, and contract-stability forecasting.

[Task technical implementation]
Add `src/ai/strategic_social_reasoning.py` and define exactly:

- `CooperationNeedAssessment`
- `AllySuitabilityScore`
- `ContractStabilityForecast`
- `StrategicSocialReasoningService`

with the exact field lists and static methods defined in the phase description.

[Task possible affected files]

- `src/ai/strategic_social_reasoning.py`

[Task important notes]
These are derived reasoning outputs only. They are not authoritative social or strategic state and must not be stored directly in `StrategicState`.

[Task check list]

- [x] Add `CooperationNeedAssessment`
- [x] Add `AllySuitabilityScore`
- [x] Add `ContractStabilityForecast`
- [x] Add `StrategicSocialReasoningService`
- [x] Keep field names exact
- [x] Keep outputs typed and deterministic
- [x] Avoid loose metadata dicts

[Implementation Note]: Established social reasoning models and `StrategicSocialReasoningService` in `src/ai/strategic_social_reasoning.py`. All interfaces are non-mutating and deterministic.

[Task acceptance criteria]
The codebase compiles with exact social-reasoning models and service entrypoints matching the required contract.

---

[x] (checkbox) - [Task 2] - Implement deterministic cooperation-need detection

[Task Description]
Make recognition of non-solo-viable work profile-sensitive and exact so low-judgment entities can miss cooperation need while high-judgment entities detect it reliably.

[Task technical implementation]
Implement `assess_cooperation_need(...)` using:

- the exact project input fields
- the exact allowed role tags
- the exact role-gap calculation
- the exact `need_score` formula
- the exact `recognition_score` formula
- the exact `requires_cooperation` threshold
- the exact `recognized_need` threshold
- the exact recruitment-objective precedence table

[Task possible affected files]

- `src/ai/strategic_social_reasoning.py`
- `src/core/models/strategy.py` if required project fields are missing

[Task important notes]
Do not use hidden heuristics for missing roles or party size. If required project fields are missing, add them explicitly to the model rather than improvising defaults in reasoning code.

[Task check list]

- [x] Add exact required project fields if missing
- [x] Add exact role-gap calculation
- [x] Add exact `need_score` formula
- [x] Add exact `recognition_score` formula
- [x] Add exact `requires_cooperation` threshold
- [x] Add exact `recognized_need` threshold
- [x] Add exact recruitment objective precedence rule
- [x] Keep assessment deterministic

[Implementation Note]: Cooperation need detection implemented with specific thresholds for requirement (0.55) and recognition (0.50). Precise role-gap calculation and objective precedence verified.

[Task acceptance criteria]
The service returns deterministic, profile-sensitive cooperation-need assessments using the exact formulas and thresholds.

---

[x] (checkbox) - [Task 3] - Implement bounded ally filtering and ranking

[Task Description]
Make ally evaluation profile-sensitive, deterministic, and bounded so cooperation quality differs by entity without exploding candidate search.

[Task technical implementation]
Implement `score_allies(...)` using:

- the exact alive/self/existing-member filters
- the exact minimum relation/admissibility gate
- the exact normalized relation extraction
- the exact conflict penalties
- the exact availability calculation
- the exact role-fit rules
- the exact `total_score` formula
- the exact deterministic sort key
- the exact `profile.ally_evaluation_limit` cap

[Task possible affected files]

- `src/ai/strategic_social_reasoning.py`
- social registry access helpers if normalized relation access is missing

[Task important notes]
Do not evaluate more than `profile.ally_evaluation_limit` final ranked candidates. Do not use fuzzy tie breaking. Do not treat generalists as equal to exact role matches.

[Task check list]

- [x] Add exact candidate filters
- [x] Add exact relation normalization
- [x] Add exact conflict-penalty extraction
- [x] Add exact availability formula
- [x] Add exact role-fit rules
- [x] Add exact `total_score` formula
- [x] Add exact deterministic sorting
- [x] Apply exact evaluation cap

[Implementation Note]: Ally evaluation applies the `ally_evaluation_limit` cap and deterministic sorting. Relationship scores (trust, loyalty, etc.) and role-fit are correctly weighted.

[Task acceptance criteria]
The service returns a deterministic bounded ally ranking using the exact formula, filter rules, and evaluation cap.

---

[x] (checkbox) - [Task 4] - Implement exact contract-stability forecasting

[Task Description]
Forecast whether a proposed recruited group is likely to remain stable enough for contract-backed cooperation before any authoritative contract mutation occurs.

[Task technical implementation]
Implement `forecast_contract_stability(...)` using:

- exact `role_coverage_ratio`
- exact averages for trust, loyalty, familiarity, and resentment
- exact `stability_score` formula
- exact threshold-to-label mapping:
  - `stable`
  - `fragile`
  - `unstable`

[Task possible affected files]

- `src/ai/strategic_social_reasoning.py`

[Task important notes]
This is only a forecast in this phase. It must not directly create, modify, or dissolve contracts.

[Task check list]

- [x] Compute exact role coverage
- [x] Compute exact averages
- [x] Compute exact `stability_score`
- [x] Apply exact label thresholds
- [x] Keep forecast deterministic and non-mutating

[Implementation Note]: Stability forecasting derives deterministic scores and labels (stable/fragile/unstable) based on trust, coverage, and resourcing.

[Task acceptance criteria]
The service returns a deterministic contract-stability forecast using the exact formula and labels.

---

[x] (checkbox) - [Task 5] - Add deterministic tests for cooperation need, ally ranking, and stability forecasting

[Task Description]
Lock the social-reasoning contract so the phase cannot silently regress into unbounded ally search, vague cooperation heuristics, or unstable social selection.

[Task technical implementation]
Add these exact test files:

- `tests/ai/test_cooperation_need_assessment.py`
- `tests/ai/test_bounded_ally_scoring.py`
- `tests/ai/test_contract_stability_forecast.py`

Required exact test functions:

In `test_cooperation_need_assessment.py`

- `test_high_need_project_crosses_requires_cooperation_threshold`
- `test_low_judgment_profile_can_fail_to_recognize_cooperation_need`
- `test_missing_role_tags_use_exact_recruitment_objective_precedence`
- `test_solo_viable_project_can_stay_below_need_threshold`

In `test_bounded_ally_scoring.py`

- `test_exact_role_match_scores_higher_than_generalist_fallback`
- `test_candidate_filter_rejects_low_relation_and_high_conflict_candidate`
- `test_high_social_bandwidth_profile_keeps_more_ranked_candidates_than_low_social_bandwidth_profile`
- `test_ally_sorting_is_deterministic`
- `test_ally_scoring_does_not_mutate_social_or_strategic_state`

In `test_contract_stability_forecast.py`

- `test_high_trust_high_coverage_group_forecasts_stable`
- `test_low_trust_high_resentment_group_forecasts_unstable`
- `test_middle_range_group_forecasts_fragile`
- `test_empty_selected_scores_returns_zeroed_forecast_deterministically`

[Task possible affected files]

- `tests/ai/test_cooperation_need_assessment.py`
- `tests/ai/test_bounded_ally_scoring.py`
- `tests/ai/test_contract_stability_forecast.py`

[Task important notes]
Use controlled fixtures with fixed project fields, fixed role requirements, fixed social relations, and fixed cognition profiles. Do not use freeform scenario tests here.

[Task check list]

- [x] Add cooperation-need threshold tests
- [x] Add recognition-failure test for low judgment
- [x] Add exact recruitment-objective precedence test
- [x] Add exact role-fit ranking test
- [x] Add filter rejection test
- [x] Add bounded ally count test
- [x] Add deterministic sorting test
- [x] Add stability forecast label tests
- [x] Add non-mutation test

[Implementation Note]: Robust test suite implemented for M4 in `tests/ai/`. Verified that low-judgment entities can fail to recognize cooperation need.

[Task acceptance criteria]
Phase 4 ships with deterministic tests proving exact cooperation-need detection, exact ally ranking, bounded candidate evaluation, exact stability forecasting, and non-mutation behavior.

---

[x] (checkbox) - [Task 6] - Add exact social-reasoning documentation

[Task Description]
Document the full operational semantics of cooperation-need detection, bounded ally ranking, and contract-stability forecasting so later phases cannot reinterpret them informally.

[Task technical implementation]
Create:

- `docs/strategy/bounded_cognition_m4_social_reasoning.md`
- `docs/strategy/bounded_cognition_m4_test_matrix.md`

`bounded_cognition_m4_social_reasoning.md` must contain these exact sections:

1. Allowed role tags
2. Role-tag mapping by class
3. Cooperation-need working model
4. `need_score` formula
5. `recognition_score` formula
6. Recruitment-objective precedence rule
7. Ally filter rules
8. Ally-scoring formula
9. Evaluation cap rule
10. Contract-stability formula
11. Stability-label thresholds
12. Non-goals for this phase

`bounded_cognition_m4_test_matrix.md` must contain these exact sections:

1. Cooperation-need tests
2. Role-fit and ranking tests
3. Filter and cap tests
4. Stability-forecast tests
5. Non-mutation tests

For every test function, document:

- test name
- fixture shape
- exact expected behavior
- regression caught

[Task possible affected files]

- `docs/strategy/bounded_cognition_m4_social_reasoning.md`
- `docs/strategy/bounded_cognition_m4_test_matrix.md`

[Task important notes]
Do not describe this phase in broad prose only. The role-tag vocabulary, formulas, filters, thresholds, caps, and labels must all be exact.

[Task check list]

- [x] Document exact role tags
- [x] Document exact class-to-role mapping
- [x] Document exact `need_score` formula
- [x] Document exact `recognition_score` formula
- [x] Document exact recruitment-objective precedence
- [x] Document exact ally filter rules
- [x] Document exact ally-scoring formula
- [x] Document exact evaluation cap
- [x] Document exact stability formula and thresholds
- [x] Document all required tests
- [x] Document exact regression purpose for each test

[Implementation Note]: Social reasoning operational semantics and matrices documented in `docs/strategy/`. Alignment with implementation verified.

[Task acceptance criteria]
Phase 4 has an exact social-reasoning document and exact test-matrix document that match implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop treating cooperation as a binary yes-or-no outcome. In this phase it becomes a bounded, profile-sensitive strategic judgment with exact scoring and exact caps.

What actions must be taken immediately
Implement the exact cooperation-need formulas, exact ally filters, exact ally-scoring formula, exact evaluation cap, exact stability forecast, and deterministic tests before touching event interpretation or UI exposure.

What must stop or be eliminated
Stop allowing unbounded ally search. Stop using fuzzy role matching. Stop treating low-capacity entities as randomly antisocial instead of strategically weaker at recognizing, selecting, and stabilizing cooperation.

The consequences and opportunity cost if this fails
You will keep a strategic system where cooperation exists in theory but still feels generic in practice, with too many candidates, weak differentiation in ally choice, and poor determinism in social planning.
