---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

[Phase 5] - Apply Cognition Capacity to Event Interpretation and Identity Drift

[Phase Description]
Phase 5 is the event-interpretation phase for the bounded-intelligence extension. Its purpose is to make entities differ in how strongly they interpret major events, how likely those events are to generate strategic concerns, how those events reshape directives, and how current projects are kept, suspended, replaced, or transformed under pressure. The strategy epic already established that event interpretation is the heart of the life-direction system and must not collapse into flat score nudges. This phase does not invent event consequence. It applies the `CognitionCapacityProfile` from Phase 1 and the bounded strategic discipline from Phase 2 so that the same event can produce different but deterministic outcomes across entities with different judgment quality, interruption resistance, and resume reliability. The current architecture already supports strategic continuity, concern generation, directives, and structured explainability, so this phase extends that same discipline rather than creating a second event-AI subsystem.

This phase must not yet add replay or UI schema exposure for bounded cognition. Those belong to later phases. This phase is only about deterministic event interpretation, concern generation, directive mutation, identity-drift pressure, and project reprioritization.

[Phase technical implementation]
Create a new module, `src/ai/strategic_event_interpretation.py`, and define these exact derived working models:

- `EventInterpretationAssessment`
- `DirectiveMutationProposal`
- `ProjectReprioritizationOutcome`

`EventInterpretationAssessment` must contain these exact fields:

- `event_kind: str`
- `interpretation_score: float`
- `concern_kind: str | None`
- `concern_score: float`
- `creates_concern: bool`
- `identity_drift_pressure: float`
- `event_severity: float`
- `attachment_score: float`
- `bond_score: float`
- `obligation_score: float`
- `history_score: float`
- `public_visibility_score: float`

`DirectiveMutationProposal` must contain these exact fields:

- `target_directive_kind: str`
- `mutation_kind: str`
- `delta: float`
- `threshold_passed: bool`
- `identity_drift_pressure: float`

`ProjectReprioritizationOutcome` must contain these exact fields:

- `current_project_id: str | None`
- `action: str`
- `pressure_score: float`
- `continuity_resistance: float`
- `replacement_project_kind: str | None`
- `transformed_project_kind: str | None`
- `interrupting_concern_kind: str | None`
- `preserve_for_resume: bool`

Add one exact service class:

- `StrategicEventInterpretationService`

This class must expose these exact static methods:

- `interpret_event(entity, strategic_state, event_payload, social_registry, tick) -> EventInterpretationAssessment | None`
- `propose_directive_mutations(entity, strategic_state, interpretation, tick) -> list[DirectiveMutationProposal]`
- `reprioritize_project(entity, strategic_state, current_project, interpretation, tick) -> ProjectReprioritizationOutcome`

The service must consume `CognitionCapacityProfile` from Phase 1. It must not mutate authoritative state directly. It must return derived outcomes that later strategic-update emission can convert into concern creation, directive changes, and project continuity changes.

The event payload accepted in this phase must expose these exact fields:

- `event_kind`
- `severity`
- `related_entity_id`
- `related_location_kind`
- `public_visibility`
- `repeated_count`
- `related_obligation_pressure`

If any of these fields are absent in the current interpreted-event model, add a normalization adapter in this phase rather than reading ad hoc event dicts directly.

The allowed `event_kind` values in this phase are exactly:

- `home_threat`
- `ally_death`
- `betrayal`
- `near_death`
- `public_success`
- `repeated_failure`

No other event kind is allowed in this phase.

Add these exact helper functions:

```python id="lcb4w0"
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

def _norm_attachment(value: float | None) -> float:
    if value is None:
        return 0.0
    return _clamp(value, 0.0, 1.0)
```

Let:

- `sev = _clamp(event_payload.severity, 0.0, 1.0)`
- `j = profile.judgment_stability`
- `interrupt = profile.interruption_resistance`
- `resume = profile.resume_reliability`
- `abandon_norm = _clamp((profile.abandonment_threshold_mod - 0.60) / 0.60, 0.0, 1.0)`
- `hist = _safe_ratio(event_payload.repeated_count if event_payload.repeated_count is not None else 0, 3.0)`
- `oblig = _clamp(event_payload.related_obligation_pressure if event_payload.related_obligation_pressure is not None else 0.0, 0.0, 1.0)`
- `pub = _clamp(event_payload.public_visibility if event_payload.public_visibility is not None else 0.0, 0.0, 1.0)`

For `home_threat`, compute `attachment_score` as the maximum normalized place-attachment importance among attachments of kind `HOME`. If none exist, use `0.0`.

For `ally_death` and `betrayal`, compute `bond_score` as the arithmetic mean of:

- trust toward `related_entity_id`
- loyalty toward `related_entity_id`
- familiarity toward `related_entity_id`

using `_norm_relation` for each. If the entity is unknown in the social registry, use `0.0` for all three.

For all other event kinds:

- `attachment_score = 0.0`
- `bond_score = 0.0`

Then compute `interpretation_score` using these exact formulas.

For `home_threat`:

```python id="td7j2k"
interpretation_score = round(
    _clamp(
        0.30 * sev +
        0.30 * attachment_score +
        0.20 * oblig +
        0.10 * hist +
        0.10 * j,
        0.0,
        1.0,
    ),
    3,
)
```

For `ally_death`:

```python id="8p0oh3"
interpretation_score = round(
    _clamp(
        0.35 * sev +
        0.30 * bond_score +
        0.15 * oblig +
        0.10 * hist +
        0.10 * j,
        0.0,
        1.0,
    ),
    3,
)
```

For `betrayal`:

```python id="iaqmng"
interpretation_score = round(
    _clamp(
        0.35 * sev +
        0.30 * bond_score +
        0.15 * hist +
        0.10 * (1.0 - j) +
        0.10 * oblig,
        0.0,
        1.0,
    ),
    3,
)
```

For `near_death`:

```python id="jidmq7"
interpretation_score = round(
    _clamp(
        0.40 * sev +
        0.20 * hist +
        0.20 * j +
        0.20 * (1.0 - interrupt),
        0.0,
        1.0,
    ),
    3,
)
```

For `public_success`:

```python id="gh6v6p"
interpretation_score = round(
    _clamp(
        0.30 * sev +
        0.25 * pub +
        0.20 * oblig +
        0.15 * hist +
        0.10 * j,
        0.0,
        1.0,
    ),
    3,
)
```

For `repeated_failure`:

```python id="65rv2g"
interpretation_score = round(
    _clamp(
        0.30 * sev +
        0.25 * hist +
        0.20 * oblig +
        0.15 * j +
        0.10 * (1.0 - interrupt),
        0.0,
        1.0,
    ),
    3,
)
```

Then compute `identity_drift_pressure` using this exact formula for all allowed event kinds:

```python id="xkn9s0"
identity_drift_pressure = round(
    _clamp(
        0.40 * interpretation_score +
        0.30 * hist +
        0.20 * (1.0 - j) +
        0.10 * sev,
        0.0,
        1.0,
    ),
    3,
)
```

Then compute `concern_score` using this exact common formula:

```python id="i0rn78"
concern_score = round(
    _clamp(
        interpretation_score *
        (0.60 + 0.20 * sev + 0.10 * hist + 0.10 * oblig),
        0.0,
        1.0,
    ),
    3,
)
```

Map event kinds to concern generation using these exact rules:

- `home_threat`
  - `creates_concern = True` if `interpretation_score >= 0.45`
  - `concern_kind = "defend_home"` if true, else `None`

- `ally_death`
  - `creates_concern = True` if `interpretation_score >= 0.55`
  - if true and `bond_score >= 0.60` -> `concern_kind = "avenge_loss"`
  - if true and `bond_score < 0.60` -> `concern_kind = "protect_group"`
  - else `None`

- `betrayal`
  - `creates_concern = True` if `interpretation_score >= 0.50`
  - if true and `bond_score >= 0.50` -> `concern_kind = "punish_betrayal"`
  - if true and `bond_score < 0.50` -> `concern_kind = "avoid_dependency"`
  - else `None`

- `near_death`
  - `creates_concern = True` if `interpretation_score >= 0.50`
  - if true -> `concern_kind = "recover_and_reassess"`
  - else `None`

- `public_success`
  - `creates_concern = True` if `interpretation_score >= 0.55`
  - if true and `pub >= 0.50` -> `concern_kind = "capitalize_reputation"`
  - if true and `pub < 0.50` -> `concern_kind = "reinforce_role"`
  - else `None`

- `repeated_failure`
  - `creates_concern = True` if `interpretation_score >= 0.50`
  - if true -> `concern_kind = "regroup_and_reassess"`
  - else `None`

No other concern kind is allowed in this phase.

For directive mutation, the only allowed `target_directive_kind` values in this phase are exactly:

- `protect_home`
- `protect_group`
- `trust_allies`
- `self_reliance`
- `seek_safety`
- `seek_prestige`
- `uphold_role`

The only allowed `mutation_kind` values are exactly:

- `strengthen_existing`
- `weaken_existing`
- `acquire_new`

No other directive target or mutation kind is allowed in this phase.

Set:

```python id="r90lm1"
threshold_passed = identity_drift_pressure >= 0.60
```

For positive mutation deltas, use this exact formula:

```python id="2an1v0"
positive_delta = round(
    _clamp(
        0.10 + 0.25 * interpretation_score + 0.10 * hist + 0.05 * oblig,
        0.05,
        0.50,
    ),
    3,
)
```

For negative mutation deltas, use this exact formula:

```python id="nmqpbp"
negative_delta = round(
    -_clamp(
        0.10 + 0.25 * interpretation_score + 0.10 * hist + 0.05 * (1.0 - j),
        0.05,
        0.50,
    ),
    3,
)
```

Then generate directive mutation proposals with this exact mapping:

- `home_threat`
  - if `threshold_passed` -> one proposal
    - `target_directive_kind = "protect_home"`
    - `mutation_kind = "strengthen_existing"` if directive already exists else `"acquire_new"`
    - `delta = positive_delta`

- `ally_death`
  - if `threshold_passed` -> one proposal
    - `target_directive_kind = "protect_group"`
    - `mutation_kind = "strengthen_existing"` if directive already exists else `"acquire_new"`
    - `delta = positive_delta`

- `betrayal`
  - if `threshold_passed` -> always one proposal
    - `target_directive_kind = "trust_allies"`
    - `mutation_kind = "weaken_existing"`
    - `delta = negative_delta`

  - if `identity_drift_pressure >= 0.75` -> add second proposal
    - `target_directive_kind = "self_reliance"`
    - `mutation_kind = "strengthen_existing"` if directive already exists else `"acquire_new"`
    - `delta = positive_delta`

- `near_death`
  - if `threshold_passed` -> one proposal
    - `target_directive_kind = "seek_safety"`
    - `mutation_kind = "strengthen_existing"` if directive already exists else `"acquire_new"`
    - `delta = positive_delta`

- `public_success`
  - if `threshold_passed` and `pub >= 0.50` -> one proposal
    - `target_directive_kind = "seek_prestige"`
    - `mutation_kind = "strengthen_existing"` if directive already exists else `"acquire_new"`
    - `delta = positive_delta`

  - if `threshold_passed` and `pub < 0.50` -> one proposal
    - `target_directive_kind = "uphold_role"`
    - `mutation_kind = "strengthen_existing"` if directive already exists else `"acquire_new"`
    - `delta = positive_delta`

- `repeated_failure`
  - if `threshold_passed` -> one proposal
    - `target_directive_kind = "seek_safety"`
    - `mutation_kind = "strengthen_existing"` if directive already exists else `"acquire_new"`
    - `delta = positive_delta`

No other mutation mapping is allowed in this phase.

For project reprioritization, let:

- `current_commit = _norm_weight(current_project.abandonment_cost, 1.0, 2.0)` if current project exists else `0.0`
- `current_urg = _norm_weight(current_project.urgency, 1.0, 2.0)` if current project exists else `0.0`

Compute `pressure_score` using this exact formula:

```python id="i2q1x4"
pressure_score = round(
    _clamp(
        0.40 * interpretation_score +
        0.20 * sev +
        0.15 * oblig +
        0.15 * hist +
        0.10 * (1.0 - interrupt),
        0.0,
        1.0,
    ),
    3,
)
```

Compute `continuity_resistance` using this exact formula:

```python id="otyk0u"
continuity_resistance = round(
    _clamp(
        0.30 * current_commit +
        0.20 * current_urg +
        0.20 * interrupt +
        0.15 * j +
        0.15 * abandon_norm,
        0.0,
        1.0,
    ),
    3,
)
```

Then apply this exact reprioritization rule:

1. If `current_project is None`:
   - if `interpretation_score >= 0.50` -> `action = "replace"`
   - else -> `action = "keep"`

2. If `current_project is not None` and `pressure_score <= continuity_resistance`:
   - `action = "keep"`

3. Else if `event_kind == "public_success"` and `interpretation_score >= 0.55`:
   - `action = "transform"`
   - `transformed_project_kind = "capitalize_success"`
   - `preserve_for_resume = False`

4. Else if `event_kind == "repeated_failure"` and `interpretation_score >= 0.50`:
   - `action = "transform"`
   - `transformed_project_kind = "regroup_and_reassess"`
   - `preserve_for_resume = False`

5. Else if `event_kind == "near_death"`:
   - `action = "suspend"`
   - `replacement_project_kind = "recover_and_reassess"`
   - `preserve_for_resume = True`

6. Else if `event_kind == "home_threat"`:
   - `action = "replace"`
   - `replacement_project_kind = "defend_home"`
   - `preserve_for_resume = True`

7. Else if `event_kind == "ally_death"`:
   - `action = "replace"`
   - if `bond_score >= 0.60` -> `replacement_project_kind = "avenge_loss"`
   - else -> `replacement_project_kind = "protect_group"`
   - `preserve_for_resume = True`

8. Else if `event_kind == "betrayal"`:
   - `action = "replace"`
   - if `bond_score >= 0.50` -> `replacement_project_kind = "punish_betrayal"`
   - else -> `replacement_project_kind = "avoid_dependency"`
   - `preserve_for_resume = False`

9. Else:
   - `action = "suspend"`
   - `replacement_project_kind = None`
   - `preserve_for_resume = True`

Set `interrupting_concern_kind` equal to `interpretation.concern_kind` if a concern was generated, else `None`.

No other reprioritization action, project kind, or continuity rule is allowed in this phase.

This phase must not directly create concerns, mutate directives, or update current project pointers. It must return deterministic derived outcomes that later strategic updates can apply authoritatively.

[Phase important notes]
The main trap in this phase is collapsing event consequence back into simple urgency nudges. This phase must treat interpretation, concern generation, directive mutation, and project reprioritization as explicit derived mechanics with exact formulas and thresholds. That is the whole point of this work.

The second trap is making low-judgment entities random. They must remain deterministic. Lower `judgment_stability` should make them more brittle, more overreactive in specific ways, and more likely to drift under repeated aligned pressure, not chaotic.

The third trap is letting event consequence bypass continuity logic. This phase must always compare event pressure to continuity resistance when a current project exists. Otherwise every major event becomes an unconditional branch and continuity becomes fake.

The fourth trap is conflating identity drift with arbitrary personality rewrite. This phase only affects directives through exact mutation rules. It does not rewrite the whole personality profile.

[Phase acceptance criteria]
At the end of Phase 5, major events produce deterministic interpretation scores, exact concern-generation decisions, exact directive-mutation proposals, and exact project reprioritization outcomes that differ by cognition profile and history pressure. Current projects are kept, suspended, replaced, or transformed through explicit formulas rather than ad hoc score nudges.

## Task

[x] (checkbox) - [Task 1] - Add event-interpretation working models and service surface

[Task Description]
Create the exact derived working models and service interface for deterministic event interpretation, directive mutation, and project reprioritization.

[Task technical implementation]
Add `src/ai/strategic_event_interpretation.py` and define exactly:

- `EventInterpretationAssessment`
- `DirectiveMutationProposal`
- `ProjectReprioritizationOutcome`
- `StrategicEventInterpretationService`

with the exact field lists and static methods defined in the phase description.

[Task possible affected files]

- `src/ai/strategic_event_interpretation.py`

[Task important notes]
These are derived interpretation outputs only. They are not authoritative state and must not be stored directly in `StrategicState`.

[Task check list]

- [x] Add `EventInterpretationAssessment`
- [x] Add `DirectiveMutationProposal`
- [x] Add `ProjectReprioritizationOutcome`
- [x] Add `StrategicEventInterpretationService`
- [x] Keep field names exact
- [x] Keep outputs typed and deterministic
- [x] Avoid loose metadata dicts

[Implementation Note]: Established `StrategicEventInterpretationService` and working models for assessment, mutation, and reprioritization in `src/ai/strategic_event_interpretation.py`.

[Task acceptance criteria]
The codebase compiles with exact event-interpretation models and service entrypoints matching the required contract.

---

[x] (checkbox) - [Task 2] - Implement deterministic interpretation scoring and concern generation

[Task Description]
Make major-event interpretation exact and profile-sensitive so concern generation becomes deterministic and history-aware.

[Task technical implementation]
Implement `interpret_event(...)` using:

- the exact allowed event kinds
- the exact input payload fields
- the exact attachment and bond extraction rules
- the exact interpretation formulas by event kind
- the exact identity-drift-pressure formula
- the exact concern-score formula
- the exact concern-threshold and concern-kind mapping table

[Task possible affected files]

- `src/ai/strategic_event_interpretation.py`
- event payload normalization adapter modules if required
- social registry access helpers if bond extraction helpers are missing

[Task important notes]
Do not add extra event kinds. Do not use random interpretation variance. Do not let high evidence or high judgment create omniscient event meaning.

[Task check list]

- [x] Add exact event-kind set
- [x] Add exact event-payload normalization
- [x] Add exact home-attachment extraction
- [x] Add exact social-bond extraction
- [x] Add exact formulas for all six event kinds
- [x] Add exact identity-drift-pressure formula
- [x] Add exact concern-score formula
- [x] Add exact concern-threshold mapping
- [x] Keep interpretation deterministic

[Implementation Note]: Event interpretation scoring for all 6 core events (threat, death, betrayal, etc.) implemented with deterministic, attribute-weighted formulas. Concern generation mappings verified.

[Task acceptance criteria]
The service returns deterministic interpretation assessments and exact concern-generation decisions for all allowed event kinds.

---

[x] (checkbox) - [Task 3] - Implement exact directive mutation rules

[Task Description]
Make directive mutation explicit, thresholded, and profile-sensitive so identity drift is bounded and testable rather than vague.

[Task technical implementation]
Implement `propose_directive_mutations(...)` using:

- the exact allowed directive target kinds
- the exact allowed mutation kinds
- the exact threshold rule:
  - `identity_drift_pressure >= 0.60`

- the exact positive and negative delta formulas
- the exact event-kind to mutation mapping table
- the exact second betrayal mutation rule for `self_reliance`

[Task possible affected files]

- `src/ai/strategic_event_interpretation.py`
- `src/core/models/strategy.py` if directive records need explicit lookup helpers by kind

[Task important notes]
Do not mutate directives directly in this phase. Do not create broad identity rewrites. Do not add extra mutation kinds.

[Task check list]

- [x] Add exact directive target set
- [x] Add exact mutation-kind set
- [x] Add exact threshold rule
- [x] Add exact positive delta formula
- [x] Add exact negative delta formula
- [x] Add exact event-to-directive mapping
- [x] Add exact betrayal second-mutation rule
- [x] Keep mutation proposals deterministic

[Implementation Note]: Directive mutation logic correctly applies the drift pressure threshold (0.60) and computes exact delta proposals for strategic identity shift.

[Task acceptance criteria]
The service returns deterministic directive-mutation proposals using the exact formulas, thresholds, and mapping rules.

---

[x] (checkbox) - [Task 4] - Implement exact project reprioritization rules

[Task Description]
Make event-driven project continuity explicit so current work is kept, suspended, replaced, or transformed through exact deterministic rules.

[Task technical implementation]
Implement `reprioritize_project(...)` using:

- the exact `pressure_score` formula
- the exact `continuity_resistance` formula
- the exact action-order rule:
  - keep
  - transform on public success
  - transform on repeated failure
  - suspend on near death
  - replace on home threat
  - replace on ally death
  - replace on betrayal
  - fallback suspend

and the exact replacement/transformation project kind mapping.

[Task possible affected files]

- `src/ai/strategic_event_interpretation.py`
- `src/core/models/strategy.py` if project records need explicit urgency or abandonment-cost accessors

[Task important notes]
Do not skip the continuity comparison when a current project exists. Do not treat all events as replacement events. Do not mutate project state directly in this phase.

[Task check list]

- [x] Add exact `pressure_score` formula
- [x] Add exact `continuity_resistance` formula
- [x] Add exact keep rule
- [x] Add exact transform rules
- [x] Add exact suspend rule for near death
- [x] Add exact replace rules for home threat, ally death, and betrayal
- [x] Add exact preserve-for-resume flags
- [x] Keep reprioritization deterministic and non-mutating

[Implementation Note]: Reprioritization logic balances `pressure_score` against `continuity_resistance` to decide project outcomes (keep/suspend/replace/transform) deterministically.

[Task acceptance criteria]
The service returns deterministic reprioritization outcomes using the exact formulas and action mapping rules.

---

[x] (checkbox) - [Task 5] - Add deterministic tests for interpretation, directive mutation, and reprioritization

[Task Description]
Lock the event-consequence contract so the phase cannot silently regress into urgency nudges, unconditional branching, or fuzzy identity drift.

[Task technical implementation]
Add these exact test files:

- `tests/ai/test_event_interpretation_assessment.py`
- `tests/ai/test_directive_mutation_proposals.py`
- `tests/ai/test_project_reprioritization_outcomes.py`

Required exact test functions:

In `test_event_interpretation_assessment.py`

- `test_home_threat_with_high_home_attachment_generates_higher_interpretation_score_than_unattached_entity`
- `test_ally_death_uses_social_bond_in_interpretation_score`
- `test_betrayal_with_low_judgment_has_higher_identity_drift_pressure_than_same_event_with_high_judgment`
- `test_public_success_uses_public_visibility_in_concern_mapping`
- `test_repeated_failure_uses_exact_threshold_for_regroup_concern`

In `test_directive_mutation_proposals.py`

- `test_home_threat_strengthens_or_acquires_protect_home_when_threshold_passes`
- `test_betrayal_weakens_trust_allies_with_exact_negative_delta`
- `test_betrayal_can_add_second_self_reliance_mutation_when_high_drift_pressure`
- `test_public_success_maps_to_seek_prestige_when_public_visibility_is_high`
- `test_no_mutation_generated_when_threshold_not_passed`

In `test_project_reprioritization_outcomes.py`

- `test_current_project_is_kept_when_pressure_does_not_exceed_continuity_resistance`
- `test_near_death_suspends_current_project_and_replaces_with_recovery_kind`
- `test_home_threat_replaces_with_defend_home_and_preserves_resume`
- `test_repeated_failure_transforms_project_to_regroup_and_reassess`
- `test_event_interpretation_does_not_mutate_authoritative_state`

[Task possible affected files]

- `tests/ai/test_event_interpretation_assessment.py`
- `tests/ai/test_directive_mutation_proposals.py`
- `tests/ai/test_project_reprioritization_outcomes.py`

[Task important notes]
Use controlled fixtures with fixed event payloads, fixed profile values, fixed attachment data, fixed bond data, and fixed current project data. Do not use broad simulation scenarios here.

[Task check list]

- [x] Add interpretation-score tests
- [x] Add concern-threshold tests
- [x] Add directive-mutation threshold tests
- [x] Add exact positive and negative delta tests
- [x] Add second-betrayal-mutation test
- [x] Add project keep-versus-replace test
- [x] Add transform tests
- [x] Add suspend-and-resume-preservation test
- [x] Add non-mutation test

[Implementation Note]: Regression suite in `tests/ai/` covers all M5 scenarios, including high-attachment home threat and low-judgment identity drift. Verified non-mutating purity.

[Task acceptance criteria]
Phase 5 ships with deterministic tests proving exact event interpretation, exact directive mutation, exact reprioritization logic, and non-mutation behavior.

---

[x] (checkbox) - [Task 6] - Add exact event-interpretation documentation

[Task Description]
Document the full operational semantics of event interpretation, directive mutation, and project reprioritization so later phases cannot reinterpret them informally.

[Task technical implementation]
Create:

- `docs/strategy/bounded_cognition_m5_event_interpretation.md`
- `docs/strategy/bounded_cognition_m5_test_matrix.md`

`bounded_cognition_m5_event_interpretation.md` must contain these exact sections:

1. Allowed event kinds
2. Event payload contract
3. Attachment and bond extraction rules
4. Interpretation formulas by event kind
5. Identity-drift-pressure formula
6. Concern-score formula
7. Concern-threshold and concern-kind mapping
8. Allowed directive targets and mutation kinds
9. Mutation formulas and thresholds
10. Event-to-directive mapping
11. `pressure_score` formula
12. `continuity_resistance` formula
13. Reprioritization action order
14. Replacement and transformation project kind mapping
15. Non-goals for this phase

`bounded_cognition_m5_test_matrix.md` must contain these exact sections:

1. Interpretation-score tests
2. Concern-generation tests
3. Directive-mutation tests
4. Project-reprioritization tests
5. Non-mutation tests

For every test function, document:

- test name
- fixture shape
- exact expected behavior
- regression caught

[Task possible affected files]

- `docs/strategy/bounded_cognition_m5_event_interpretation.md`
- `docs/strategy/bounded_cognition_m5_test_matrix.md`

[Task important notes]
Do not describe this phase in broad prose only. The event-kind set, formulas, thresholds, mapping rules, and action order must all be exact.

[Task check list]

- [x] Document exact event kinds
- [x] Document exact payload fields
- [x] Document exact attachment and bond extraction
- [x] Document exact formulas for all six event kinds
- [x] Document exact drift and concern formulas
- [x] Document exact directive mutation rules
- [x] Document exact reprioritization formulas
- [x] Document exact action-order rule
- [x] Document all required tests
- [x] Document exact regression purpose for each test

[Implementation Note]: All operational semantics for event-consequence and identity-drift documented in `docs/strategy/`. Verified alignment with implementation.

[Task acceptance criteria]
Phase 5 has an exact event-interpretation document and exact test-matrix document that match implementation.

---

Priority Plan

What must change in mindset or assumptions
Stop treating event consequence as a mood bump. In this phase it becomes an exact interpretation and continuity-transform layer with deterministic formulas and thresholds.

What actions must be taken immediately
Implement the exact event-kind set, exact interpretation formulas, exact concern-generation rules, exact directive-mutation rules, exact project-reprioritization rules, and deterministic tests before touching replay or UI exposure.

What must stop or be eliminated
Stop allowing major events to bypass continuity comparison. Stop using vague identity drift. Stop letting event handling mutate strategy directly inside the interpreter.

The consequences and opportunity cost if this fails
You will keep a strategic system that can hold projects and concerns but still reacts to major life events like a dressed-up priority queue, which destroys the exact “lived rather than scripted” quality the epic is trying to achieve.
