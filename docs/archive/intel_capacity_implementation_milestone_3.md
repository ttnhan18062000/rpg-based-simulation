---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

[Phase 3] - Apply Cognition Capacity to Blockers, Detours, and Lead Learning

[Phase Description]
Phase 3 is the uncertainty-discipline phase for the bounded-intelligence extension. Its purpose is to make entities differ in how well they diagnose blocked progress, how far they are allowed to recurse into preparation work, how strongly they learn from contradictory evidence, and how quickly they stop retrying exhausted leads. The strategic epic already established blockers, leads, candidate zones, tested leads, and detours as first-class parts of the thinking system. This phase does not invent those structures. It applies the `CognitionCapacityProfile` from Phase 1 and the bounded strategic-appraisal discipline from Phase 2 to make uncertainty handling realistic, bounded, and deterministic. The design documents already identify recursive detour loops and silent knowledge collapse as major failure modes, so this phase is where those risks are explicitly shut down.

This phase must not yet change social recruitment quality or event-interpretation quality. Those belong to later phases. This phase is only about cognition-sensitive blocker diagnosis, detour propagation control, candidate-zone narrowing, contradiction handling, and tested-lead learning.

[Phase technical implementation]
Create a new module, `src/ai/strategic_uncertainty_resolution.py`, and define these exact derived working models:

- `BlockerDiagnosisResult`
- `DetourPlanCandidate`
- `LeadLearningOutcome`

`BlockerDiagnosisResult` must contain these exact fields:

- `project_id: str | None`
- `objective_id: str | None`
- `diagnosed_blocker_type: str`
- `diagnosis_confidence: float`
- `misdiagnosed: bool`
- `true_blocker_type: str | None`
- `severity_score: float`
- `recommended_detour_kinds: list[str]`
- `forced_terminal_outcome: str | None`

`DetourPlanCandidate` must contain these exact fields:

- `detour_kind: str`
- `source_project_id: str | None`
- `source_blocker_id: str | None`
- `depth: int`
- `score: float`
- `terminal: bool`

`LeadLearningOutcome` must contain these exact fields:

- `lead_id: str`
- `tested: bool`
- `confirmed: bool`
- `contradicted: bool`
- `new_confidence: float`
- `new_source_trust_delta: float`
- `retry_suppressed: bool`

Add one exact service class:

- `StrategicUncertaintyResolutionService`

This class must expose these exact static methods:

- `diagnose_blocker(entity, strategic_state, current_project, current_objective, tick) -> BlockerDiagnosisResult | None`
- `generate_detour_candidates(entity, diagnosis, current_depth, tick) -> list[DetourPlanCandidate]`
- `apply_lead_learning(entity, lead, outcome_kind, source_trust, tick) -> LeadLearningOutcome`

The service must consume `CognitionCapacityProfile` from Phase 1. It must not mutate authoritative state directly. It must return derived outcomes that later strategic-update emission can convert into `StrategicUpdate` records.

The blocker-diagnosis phase must only classify blockers into these exact types in this phase:

- `knowledge_unknown`
- `location_unknown`
- `capability_insufficient`
- `resource_insufficient`
- `social_access_insufficient`
- `route_unsafe`
- `time_window_blocked`

No other blocker type is allowed in this phase.

For diagnosis scoring, use these exact normalized helpers:

```python id="zc5hvg"
def _clamp(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value

def _bool_score(flag: bool) -> float:
    return 1.0 if flag else 0.0

def _safe_ratio(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return _clamp(value / max_value, 0.0, 1.0)
```

Let:

- `p = profile.planning_budget / 9.0`
- `j = profile.judgment_stability`
- `e = profile.evidence_quality`
- `d = profile.detour_depth_limit / 4.0`
- `c = profile.contradiction_sensitivity`
- `t = profile.source_trust_learning_rate`

Define these exact base diagnosis confidences by blocker type:

- `knowledge_unknown = 0.40`
- `location_unknown = 0.45`
- `capability_insufficient = 0.50`
- `resource_insufficient = 0.45`
- `social_access_insufficient = 0.40`
- `route_unsafe = 0.45`
- `time_window_blocked = 0.35`

Then compute `diagnosis_confidence` with these exact formulas.

For `knowledge_unknown`:

```python id="ep3hbg"
diagnosis_confidence = round(
    _clamp(0.40 + 0.30 * e + 0.20 * j + 0.10 * p, 0.10, 0.95),
    3,
)
```

For `location_unknown`:

```python id="xqp3xa"
diagnosis_confidence = round(
    _clamp(0.45 + 0.35 * e + 0.10 * p + 0.10 * j, 0.10, 0.95),
    3,
)
```

For `capability_insufficient`:

```python id="zxsvm9"
diagnosis_confidence = round(
    _clamp(0.50 + 0.25 * p + 0.15 * j + 0.10 * e, 0.10, 0.95),
    3,
)
```

For `resource_insufficient`:

```python id="cgmxoi"
diagnosis_confidence = round(
    _clamp(0.45 + 0.20 * p + 0.20 * j + 0.15 * e, 0.10, 0.95),
    3,
)
```

For `social_access_insufficient`:

```python id="4lfr71"
diagnosis_confidence = round(
    _clamp(0.40 + 0.15 * p + 0.25 * j + 0.20 * (profile.social_bandwidth / 7.0), 0.10, 0.95),
    3,
)
```

For `route_unsafe`:

```python id="c6cfri"
diagnosis_confidence = round(
    _clamp(0.45 + 0.25 * e + 0.20 * j + 0.10 * p, 0.10, 0.95),
    3,
)
```

For `time_window_blocked`:

```python id="rrv7ha"
diagnosis_confidence = round(
    _clamp(0.35 + 0.20 * j + 0.20 * p + 0.10 * e, 0.10, 0.95),
    3,
)
```

Set `misdiagnosed = True` if and only if:

```python id="90vu8q"
diagnosis_confidence < 0.55
```

If `misdiagnosed = True`, map the misdiagnosed blocker type using this exact deterministic fallback table:

- true `knowledge_unknown` -> diagnosed `resource_insufficient`
- true `location_unknown` -> diagnosed `knowledge_unknown`
- true `capability_insufficient` -> diagnosed `resource_insufficient`
- true `resource_insufficient` -> diagnosed `capability_insufficient`
- true `social_access_insufficient` -> diagnosed `knowledge_unknown`
- true `route_unsafe` -> diagnosed `location_unknown`
- true `time_window_blocked` -> diagnosed `resource_insufficient`

This phase must not use randomness in misdiagnosis. It must use deterministic confidence thresholding and the exact fallback table above.

For each diagnosed blocker type, generate detour candidates using this exact mapping:

- `knowledge_unknown` -> `gather_rumor`, `ask_expert`
- `location_unknown` -> `scout_region`, `gather_rumor`
- `capability_insufficient` -> `train`, `upgrade_gear`
- `resource_insufficient` -> `gather_materials`, `earn_gold`
- `social_access_insufficient` -> `recruit_support`, `gain_trust`
- `route_unsafe` -> `scout_route`, `delay_departure`
- `time_window_blocked` -> `delay_departure`, `prepare_locally`

No additional detour kind is allowed in this phase.

Score each detour candidate using this exact formula.

Let:

- `depth_ratio = _clamp(current_depth / max(profile.detour_depth_limit, 1), 0.0, 1.0)`
- `patience = profile.blocker_resolution_patience`
- `planning = profile.planning_budget / 9.0`
- `evidence = profile.evidence_quality`
- `social = profile.social_bandwidth / 7.0`

Then use these exact detour scores:

For `gather_rumor`:

```python id="ipaz99"
score = round(_clamp(0.35 + 0.30 * evidence + 0.20 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `ask_expert`:

```python id="qivyxr"
score = round(_clamp(0.30 + 0.20 * evidence + 0.20 * social + 0.20 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `scout_region`:

```python id="n1pov3"
score = round(_clamp(0.35 + 0.25 * evidence + 0.15 * planning + 0.15 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `train`:

```python id="gx0b1h"
score = round(_clamp(0.40 + 0.25 * planning + 0.20 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `upgrade_gear`:

```python id="pnm1wm"
score = round(_clamp(0.35 + 0.20 * planning + 0.20 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `gather_materials`:

```python id="w27mg5"
score = round(_clamp(0.35 + 0.20 * planning + 0.15 * evidence + 0.20 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `earn_gold`:

```python id="p3qdct"
score = round(_clamp(0.30 + 0.20 * planning + 0.20 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `recruit_support`:

```python id="tbjlwm"
score = round(_clamp(0.35 + 0.30 * social + 0.15 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `gain_trust`:

```python id="pakg4w"
score = round(_clamp(0.30 + 0.25 * social + 0.20 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `scout_route`:

```python id="udb4wg"
score = round(_clamp(0.35 + 0.25 * evidence + 0.15 * planning + 0.15 * patience - 0.20 * depth_ratio, 0.0, 1.0), 3)
```

For `delay_departure`:

```python id="r5z8ws"
score = round(_clamp(0.25 + 0.20 * judgment_stability + 0.20 * patience - 0.10 * depth_ratio, 0.0, 1.0), 3)
```

For `prepare_locally`:

```python id="ynvqyq"
score = round(_clamp(0.30 + 0.20 * planning + 0.20 * patience - 0.15 * depth_ratio, 0.0, 1.0), 3)
```

In the `delay_departure` formula above, `judgment_stability` refers exactly to `profile.judgment_stability`.

Then enforce the exact detour depth rule:

If:

```python id="6bdm51"
current_depth >= profile.detour_depth_limit
```

then no detour candidate may be returned as non-terminal. Instead, return exactly one terminal `DetourPlanCandidate` with:

- `detour_kind = "forced_terminal"`
- `terminal = True`

and set `forced_terminal_outcome` in the diagnosis result using this exact decision rule:

1. if `current_project.abandonment_cost >= 1.5` -> `forced_terminal_outcome = "suspend"`
2. else if `profile.abandonment_threshold_mod >= 0.95` -> `forced_terminal_outcome = "delay"`
3. else -> `forced_terminal_outcome = "abandon"`

No other terminal resolution is allowed in this phase.

For lead learning, `apply_lead_learning` must accept `outcome_kind` with only these exact values:

- `"confirmed"`
- `"contradicted"`
- `"no_result"`

Use these exact formulas.

Let:

- `old_conf = _clamp(lead.confidence if lead.confidence is not None else 0.5, 0.0, 1.0)`
- `old_trust = _clamp(source_trust, 0.0, 1.0)`
- `e = profile.evidence_quality`
- `c = profile.contradiction_sensitivity`
- `t = profile.source_trust_learning_rate`
- `j = profile.judgment_stability`

If `outcome_kind == "confirmed"`:

```python id="3aqgo4"
new_confidence = round(_clamp(old_conf + 0.20 * e + 0.10 * t, 0.0, 1.0), 3)
new_source_trust_delta = round(_clamp(0.10 * t, -1.0, 1.0), 3)
confirmed = True
contradicted = False
retry_suppressed = False
```

If `outcome_kind == "contradicted"`:

```python id="al2c6g"
new_confidence = round(_clamp(old_conf - (0.20 * c + 0.10 * e), 0.0, 1.0), 3)
new_source_trust_delta = round(_clamp(-(0.15 * t + 0.05 * c), -1.0, 1.0), 3)
confirmed = False
contradicted = True
retry_suppressed = True if new_confidence <= 0.35 else False
```

If `outcome_kind == "no_result"`:

```python id="y0z3sm"
new_confidence = round(_clamp(old_conf - (0.05 * j), 0.0, 1.0), 3)
new_source_trust_delta = 0.0
confirmed = False
contradicted = False
retry_suppressed = True if new_confidence <= 0.25 else False
```

Every `LeadLearningOutcome` in this phase must set:

- `tested = True`

No other learning rule is allowed in this phase.

The service must not directly mutate the lead record, source-trust table, or strategic state. It must return learning outcomes that later update application can convert into authoritative changes.

[Phase important notes]
The main trap in this phase is recursive preparation drift. If detour depth is not hard-capped, the system will generate elegant-looking but useless preparation chains. That is one of the exact failure modes the design warned about. This phase must implement the hard terminal rule exactly, not approximately.

The second trap is silent knowledge collapse. High evidence quality must sharpen uncertainty faster, but it must not convert vague leads directly into exact coordinates or certainty in this phase. This phase only controls confidence change, contradiction handling, and source trust learning.

The third trap is randomness in cognition failure. Misdiagnosis in this phase must be deterministic from confidence thresholds and the exact fallback table. Random misdiagnosis would make the feature harder to test and would weaken the headless regression path established by the strategy epic.

The fourth trap is mutating strategy directly inside uncertainty services. Diagnosis results, detour plans, and lead-learning outcomes must remain derived outputs until later authoritative updates are emitted.

[Phase acceptance criteria]
At the end of Phase 3, blocker diagnosis is profile-sensitive and deterministic, detour generation is bounded by an exact depth limit and forced terminal rule, lead learning uses exact confidence and source-trust formulas, and tested-lead retry suppression is deterministic. No recursive preparation chain can exceed the configured depth semantics of the cognition profile.

## Task

[x] (checkbox) - [Task 1] - Add uncertainty-resolution working models and service surface

[Task Description]
Create the exact derived working models and service interface for cognition-sensitive blocker diagnosis, detour planning, and lead learning.

[Task technical implementation]
Add `src/ai/strategic_uncertainty_resolution.py` and define exactly:

- `BlockerDiagnosisResult`
- `DetourPlanCandidate`
- `LeadLearningOutcome`
- `StrategicUncertaintyResolutionService`

with the exact field lists and static methods defined in the phase description.

[Task possible affected files]

- `src/ai/strategic_uncertainty_resolution.py`

[Task important notes]
These are appraisal-side and learning-side derived models only. They are not authoritative state and they must not be stored directly in `MindAspect` or `StrategicState`.

[Task check list]

- [x] Add `BlockerDiagnosisResult`
- [x] Add `DetourPlanCandidate`
- [x] Add `LeadLearningOutcome`
- [x] Add `StrategicUncertaintyResolutionService`
- [x] Keep field names exact
- [x] Keep outputs typed and deterministic
- [x] Avoid loose metadata dicts

[Implementation Note]: Established `StrategicUncertaintyResolutionService` and associated working models in `src/ai/strategic_uncertainty_resolution.py`. The interface is pure and deterministic.

[Task acceptance criteria]
The codebase compiles with exact uncertainty-resolution models and service entrypoints matching the required contract.

---

[x] (checkbox) - [Task 2] - Implement deterministic blocker diagnosis

[Task Description]
Make blocker diagnosis profile-sensitive and exact so entities differ in diagnosis quality without introducing randomness.

[Task technical implementation]
Implement `diagnose_blocker(...)` using:

- the exact blocker type set
- the exact base diagnosis confidence mapping
- the exact formulas by blocker type
- the exact `misdiagnosed` threshold
- the exact deterministic fallback table

Set:

- `diagnosed_blocker_type`
- `diagnosis_confidence`
- `misdiagnosed`
- `true_blocker_type`
- `severity_score`
- `recommended_detour_kinds`
- `forced_terminal_outcome`

exactly as defined in the phase description.

[Task possible affected files]

- `src/ai/strategic_uncertainty_resolution.py`
- `src/core/models/strategy.py` if required blocker fields are missing

[Task important notes]
Do not use random misdiagnosis. Do not add extra blocker types. Do not hide missing model fields with undocumented defaults.

[Task check list]

- [x] Add exact blocker type enumeration for this phase
- [x] Add exact confidence formulas for all seven blocker types
- [x] Add exact `misdiagnosed` threshold
- [x] Add exact fallback misdiagnosis table
- [x] Add exact recommended detour mapping
- [x] Keep diagnosis deterministic

[Implementation Note]: Blocker diagnosis implemented with exact per-type confidence formulas. Deterministic misdiagnosis threshold (0.55) and fallback mapping table verified.

[Task acceptance criteria]
The service returns deterministic blocker diagnoses and can produce profile-sensitive misdiagnosis through the exact confidence threshold and fallback table.

---

[x] (checkbox) - [Task 3] - Implement bounded detour candidate generation and forced terminal resolution

[Task Description]
Bound recursive preparation work so blocked projects cannot spawn infinite detour chains.

[Task technical implementation]
Implement `generate_detour_candidates(...)` using:

- the exact detour mapping by diagnosed blocker type
- the exact detour scoring formulas
- the exact depth ratio
- the exact depth-limit comparison
- the exact forced terminal outcome rule:
  - `suspend`
  - `delay`
  - `abandon`

If `current_depth >= profile.detour_depth_limit`, return exactly one terminal `DetourPlanCandidate` with `detour_kind = "forced_terminal"` and set the diagnosis result’s `forced_terminal_outcome` using the exact abandonment-cost and `abandonment_threshold_mod` rule.

[Task possible affected files]

- `src/ai/strategic_uncertainty_resolution.py`

[Task important notes]
Do not allow partial overflow of detour depth. There is no “soft” recursion in this phase. Once depth is exhausted, only the forced terminal path is allowed.

[Task check list]

- [x] Add exact detour mapping table
- [x] Add exact detour scoring formulas
- [x] Add exact depth ratio computation
- [x] Add exact depth-limit comparison
- [x] Add exact forced terminal candidate
- [x] Add exact suspend/delay/abandon rule
- [x] Prevent any further recursive detour candidate generation after depth exhaustion

[Implementation Note]: Detour generation is strictly bounded by `detour_depth_limit`. Forced terminal outcomes (suspend/delay/abandon) are derived deterministically when depth is exhausted.

[Task acceptance criteria]
Detour generation is profile-sensitive, deterministic, and cannot recurse past the exact depth limit.

---

[x] (checkbox) - [Task 4] - Implement exact lead-learning outcomes

[Task Description]
Make lead confidence and source trust evolve deterministically based on confirmation, contradiction, and no-result outcomes.

[Task technical implementation]
Implement `apply_lead_learning(...)` using only these exact `outcome_kind` values:

- `confirmed`
- `contradicted`
- `no_result`

Use the exact formulas for:

- `new_confidence`
- `new_source_trust_delta`
- `retry_suppressed`

Always set:

- `tested = True`

Use the exact suppression thresholds:

- `<= 0.35` after contradiction
- `<= 0.25` after no result

[Task possible affected files]

- `src/ai/strategic_uncertainty_resolution.py`

[Task important notes]
This phase must not directly update source-trust state or lead state. It only returns the exact derived learning outcome.

[Task check list]

- [x] Add exact confirmed formula
- [x] Add exact contradicted formula
- [x] Add exact no-result formula
- [x] Add exact retry-suppression thresholds
- [x] Always mark leads as tested
- [x] Keep learning outcome deterministic and non-mutating

[Implementation Note]: Lead learning applies exact confidence and source-trust deltas. Verified retry suppression thresholds for contradiction (0.35) and no-result (0.25).

[Task acceptance criteria]
Lead learning outcomes are exact, deterministic, and ready for later authoritative update application.

---

[x] (checkbox) - [Task 5] - Add deterministic tests for diagnosis, detour bounding, and lead learning

[Task Description]
Lock the uncertainty-handling contract so the phase cannot silently regress into fake omniscience, unbounded preparation loops, or noisy lead handling.

[Task technical implementation]
Add these exact test files:

- `tests/ai/test_blocker_diagnosis_profile_sensitivity.py`
- `tests/ai/test_bounded_detour_generation.py`
- `tests/ai/test_lead_learning_outcomes.py`

Required exact test functions:

In `test_blocker_diagnosis_profile_sensitivity.py`

- `test_high_evidence_profile_produces_higher_location_diagnosis_confidence_than_low_evidence_profile`
- `test_low_confidence_diagnosis_triggers_exact_deterministic_misdiagnosis_mapping`
- `test_capability_blocker_uses_exact_confidence_formula`
- `test_social_access_blocker_uses_social_bandwidth_in_diagnosis`

In `test_bounded_detour_generation.py`

- `test_location_unknown_maps_to_exact_detour_kinds`
- `test_capability_insufficient_maps_to_exact_detour_kinds`
- `test_detour_scores_follow_exact_formulas`
- `test_detour_depth_limit_returns_exact_forced_terminal_candidate`
- `test_forced_terminal_outcome_prefers_suspend_delay_abandon_in_exact_order`

In `test_lead_learning_outcomes.py`

- `test_confirmed_lead_raises_confidence_and_source_trust_exactly`
- `test_contradicted_lead_reduces_confidence_and_sets_retry_suppression_when_threshold_crossed`
- `test_no_result_lead_reduces_confidence_without_source_trust_change`
- `test_lead_learning_always_marks_tested_true`
- `test_uncertainty_resolution_does_not_mutate_authoritative_state`

[Task possible affected files]

- `tests/ai/test_blocker_diagnosis_profile_sensitivity.py`
- `tests/ai/test_bounded_detour_generation.py`
- `tests/ai/test_lead_learning_outcomes.py`

[Task important notes]
Use controlled fixtures with fixed cognition profiles and fixed blocker/lead inputs. Do not use freeform scenario tests here.

[Task check list]

- [x] Add diagnosis confidence tests
- [x] Add deterministic misdiagnosis-table tests
- [x] Add exact detour-mapping tests
- [x] Add exact detour-score tests
- [x] Add exact depth-limit tests
- [x] Add exact forced terminal outcome tests
- [x] Add exact lead-confirmation tests
- [x] Add exact contradiction tests
- [x] Add exact no-result tests
- [x] Add non-mutation test

[Implementation Note]: Complete test coverage in `tests/ai/` for diagnosis sensitivity, detour depth bounding, and lead learning formulas. Purity and non-mutation verified.

[Task acceptance criteria]
Phase 3 ships with deterministic tests proving exact blocker diagnosis, exact detour bounding, exact lead learning, and non-mutation behavior.

---

[x] (checkbox) - [Task 6] - Add exact uncertainty-resolution documentation

[Task Description]
Document the full operational semantics of diagnosis, detour bounding, and lead learning so later phases cannot reinterpret the rules informally.

[Task technical implementation]
Create:

- `docs/strategy/bounded_cognition_m3_uncertainty_resolution.md`
- `docs/strategy/bounded_cognition_m3_test_matrix.md`

`bounded_cognition_m3_uncertainty_resolution.md` must contain these exact sections:

1. Allowed blocker types
2. Diagnosis working model
3. Diagnosis confidence formulas
4. Deterministic misdiagnosis rule
5. Detour-kind mapping by blocker type
6. Detour scoring formulas
7. Detour depth limit rule
8. Forced terminal outcome rule
9. Lead-learning formulas
10. Non-goals for this phase

`bounded_cognition_m3_test_matrix.md` must contain these exact sections:

1. Diagnosis sensitivity tests
2. Misdiagnosis tests
3. Detour-mapping tests
4. Detour-depth-limit tests
5. Lead-learning tests
6. Non-mutation tests

For every test function, document:

- test name
- fixture shape
- exact expected behavior
- regression caught

[Task possible affected files]

- `docs/strategy/bounded_cognition_m3_uncertainty_resolution.md`
- `docs/strategy/bounded_cognition_m3_test_matrix.md`

[Task important notes]
Do not describe this phase in broad prose only. The blocker-type set, formulas, thresholds, mapping tables, and terminal rules must all be exact.

[Task check list]

- [x] Document exact blocker types
- [x] Document exact diagnosis formulas
- [x] Document exact misdiagnosis threshold and fallback table
- [x] Document exact detour mappings
- [x] Document exact detour formulas
- [x] Document exact depth-limit rule
- [x] Document exact forced terminal outcome rule
- [x] Document exact lead-learning formulas
- [x] Document all required tests
- [x] Document exact regression purpose for each test

[Implementation Note]: Operational semantics for M3 documented in `docs/strategy/`. Verified alignment with implemented formulas and mapping rules.

[Task acceptance criteria]
Phase 3 has an exact uncertainty-resolution document and exact test-matrix document that match implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop treating uncertainty handling as a soft emergent side effect. In this phase it becomes a hard, bounded, deterministic part of strategic reasoning.

What actions must be taken immediately
Implement the exact blocker type set, exact diagnosis formulas, exact misdiagnosis rule, exact detour scoring and depth-limit rule, exact lead-learning formulas, and deterministic tests before touching social reasoning or event interpretation.

What must stop or be eliminated
Stop allowing recursive preparation chains without a hard stop. Stop using random cognition failure. Stop letting leads drift without exact tested, contradicted, or confirmed learning semantics.

The consequences and opportunity cost if this fails
You will keep a rich strategic system that appears thoughtful but either cheats through uncertainty or stalls in preparation loops, which is exactly the kind of fake depth the design was trying to avoid.
