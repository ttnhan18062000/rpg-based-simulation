# Cognition Explainability Hardening Plan

This plan addresses the remaining gaps in strategic cognition derivation and explainability listed in `TCK-20260414-COGNITION-EXPLAINABILITY-HARDENING`.

## Proposed Changes

### Strategic Cognition Layer

#### [MODIFY] [strategic_bounded_appraisal.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/strategic_bounded_appraisal.py)
- **Gather `candidate_zones`**: In `evaluate`, gather all `candidate_zones` as `StrategicCandidate` objects (kind='zone').
- **Gather `offers`**: Gather `RecruitmentOfferRecord`s as `StrategicCandidate` objects (kind='offer').
- **Apply Pre-bounds**:
    - Cap `zone` candidates using `profile.candidate_zone_limit`.
    - Cap `contract` and `offer` candidates using `profile.ally_evaluation_limit`.
- **Update Usage Metrics**: Update `dropped_candidates_count` to include these new caps.

#### [MODIFY] [brain.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/brain.py)
- Update `candidate_zones_used` and `ally_evaluations_used` population to use the `bounded_slice` results instead of raw state length.

### UI & Observability

#### [MODIFY] [inspector.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ui/cli/inspector.py)
- Update `render_cognition_capacity` to display `primary_overload_source` and `last_overload_tick` when overloaded.
- Colorize the overload alert based on the primary source (e.g., Red for trauma, Yellow for complexity).

### Verification & Testing

#### [NEW] [test_strategic_explainability.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/strategy/test_strategic_explainability.py)
- **Proof of Enforcement**: Assert that an entity with a small `candidate_zone_limit` correctly drops excess zones.
- **Explainability Check**: Assert that `switch_reason` contains the expected rival-comparison or no-project-found strings.
- **Overload Audit**: Assert that internal stressors (HP/Hunger) correctly trigger the specific overload sources.

## Verification Plan

### Automated Tests
- `PYTHONPATH=. pytest tests/ai/test_cognition_capacity_builder.py` (Verify personality effects)
- `PYTHONPATH=. pytest tests/integration/strategy/test_strategic_explainability.py` (Verify enforcement and reasoning)

### Manual Verification
- Run `EntityInspector.inspect_full` during a high-stress simulation scenario to verify CLI output.
