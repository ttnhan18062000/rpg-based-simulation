# Walkthrough - Strategic Cognition Repair Finalization

The strategic cognition hardening has been finalized by replacing simulated proofs with authoritative end-to-end integration tests. This ensures that the simulation engine's claims are backed by real runtime behavior, not test-local manual patching.

## 1. Accomplishments

### Authoritative Source-Trust Loop (Milestone 3)
- **Problem**: Trust updates were previously verified by manually patching the entity state in tests.
- **Solution**: Refactored `tests/ai/test_source_trust_learning_loop.py` to use `ActionSystem.apply_strategic_update`.
- **Proof**: Demonstrated a full behavioral loop where a lead outcome updates trust, which then authoritatively affects the source weighting of subsequent intel ingestion.

### Structured Explainability Surfacing (Milestone 4)
- **Problem**: Strategic decisions (labels and reasons) were stored internally but not fully surfaced in the API schemas.
- **Solution**: 
    - Updated `src/api/schemas.py` to include structured `recent_drivers` (kind, label, weight, description).
    - Updated `AIPresenter.serialize_strategy` to populate these drivers for the Inspector.
- **Proof**: Verified in `test_strategic_explainability.py` that `STRATEGIC_SWITCH` and other labels are correctly committed to state and visible in the presenter output.

### Personality Contract Honesty (Milestone 1)
- **Problem**: Previous claims implied all personality traits affected cognition, which risked "omni-influence" determinism issues.
- **Solution**: 
    - Standardized `CognitionCapacityBuilder` on sparse mappings: `curiosity` -> `lead_retention_limit`, `caution` -> `resume_reliability`, `neuroticism` -> `judgment_stability`.
    - Updated `test_cognition_capacity_builder.py` with deterministic delta assertions.
- **Proof**: Explicitly verified that unmapped traits (e.g., `aggression`, `greed`) have NO effect on cognitive capacity, fulfilling the strategic determinism constraint.

## 2. Verification Results

### Strategic Integrity Suite
All 22 targeted hardening tests passed:
```bash
tests/ai/test_cognition_capacity_builder.py ...............              [ 68%]
tests/ai/test_source_trust_learning_loop.py .                            [ 72%]
tests/integration/strategy/test_strategic_explainability.py ....         [ 90%]
tests/unit/ai/strategy/test_strategic_uncertainty.py ..                  [100%]
============================== 22 passed in 0.66s ==============================
```

## 3. Instructions for User
> [!IMPORTANT]
> **Schema Stability**: `StrategicStateSchema` now includes `recent_drivers`. If you use custom UI components for the Inspector, ensure they can handle the new structured list instead of just string labels.

> [!TIP]
> **Debugging Personality**: You can now verify sparse mapping behavior in the `test_cognition_capacity_builder.py`. Any new personality-to-capacity mappings should be added to `cognition_capacity.py` and reflected in this test suite first.
