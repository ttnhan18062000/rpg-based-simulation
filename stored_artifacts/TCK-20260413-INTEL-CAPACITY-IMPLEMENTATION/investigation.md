# Investigation: Intel Capacity Foundation

## Current State Analysis

### Entity Attributes
- `entity.progression.attributes.int_`
- `entity.progression.attributes.wis`
- `entity.progression.attributes.per`
- `entity.progression.attributes.cha`

### Strategic Systems
- `AIBrain`: Main entry point for AI logic.
- `src/ai/strategy/`: Contains specialized strategic services.
- `StrategicState`: Persisted entity strategic state.
- `AIPresenter`: Serializes strategy for API/UI.

## Potential Conflicts / Redundancies
- The existing `strategic_evaluator.py` or `candidate_builder.py` might already have some "hardcoded" limits that need to be replaced by the new `CognitionCapacityProfile`.
- Check if `progression` model has the required attribute caps and stamina fields as assumed in Milestone 1.

## Proposed Module Location
- Milestone 1 suggests `src/ai/cognition_capacity.py`.
- Alternative: `src/ai/strategy/cognition.py` or similar if it's purely strategic.
- Decision: Stick to `src/ai/cognition_capacity.py` as it's the specific instruction in the milestone doc, unless a strong reason to change is found.

## Dependencies
- `SimulationModel` for the profile class.
- `Entity` (or equivalent) for the builder input.
