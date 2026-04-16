# Walkthrough: Hardening Strategic Cognition Explainability

We have completed the hardening of the Strategic Cognition pipeline, focusing on enforcing strict cognitive bounds on candidate zones and social ally evaluations, and enhancing the observability of cognitive overload.

## Key Accomplishments

### 1. Cognitive Bounding & Enforcements
- **BoundedStrategicAppraisalService**: Expanded to include `candidate_zones` and `recruitment_offers` in the pre-bound phase.
- **Strict Caps**: These candidates are now strictly capped based on the `CognitionCapacityProfile` (derived from PER, INT, and personality traits) *before* final sorting.
- **Metric Population**: `candidate_zones_used` and `ally_evaluations_used` are now correctly populated in the `StrategicUpdate`, reflecting the actual bounded slice.

### 2. Enhanced Observability
- **Overload Sources**: The system now explicitly identifies the `primary_overload_source` (e.g., `complexity`, `trauma`, `panic`, `hunger`).
- **Explainable Switches**: Every strategic project switch now includes a `switch_reason` providing a transparent comparison of rival vs. current project scores and the margin used.
- **Entity Inspector**: Updated the CLI inspector to visualize these new metrics with color-coded alerts and detailed overload status.

### 3. Verification
- **Integration Tests**: Implemented `tests/integration/strategy/test_strategic_explainability.py`.
- **Verified Scenarios**:
    - [x] **Zone Limits**: Excess zones are dropped when cognitive capacity is low.
    - [x] **Ally bandwidth**: Social contracts and recruitment offers are correctly capped.
    - [x] **Trauma Overload**: verifies that low HP correctly triggers the "trauma" source.
    - [x] **Switch Transparency**: verifies that project switch justifications include normalized score margins.

## Code Changes

### Core Logic
- [strategic_bounded_appraisal.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/strategic_bounded_appraisal.py): Implemented gathering, bounding, and scoring for zones/offers.
- [brain.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/brain.py): Finalized metric mapping and stressor-aware overload detections.

### UI & Testing
- [inspector.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ui/cli/inspector.py): Added rich overload visualization.
- [test_strategic_explainability.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/strategy/test_strategic_explainability.py): New integration test suite.

## Validation Results

All tests passed successfully:
```bash
tests/integration/strategy/test_strategic_explainability.py ....         [100%]
============================== 4 passed in 0.16s ===============================
```
