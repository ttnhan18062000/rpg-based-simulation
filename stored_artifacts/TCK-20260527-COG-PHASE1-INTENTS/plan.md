# Implementation Plan - Phase 1 ActionIntent Adapter

## Proposed Changes

### Component: Action Intents
#### [NEW] [action_intent.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/intent/action_intent.py)
- Implement `ActionIntent` schema and `ActionIntentAdapter`.

#### [NEW] [test_intents.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/strategic/test_intents.py)
- Write unit tests verifying that all 11 required Phase 1 intents can be adapted to existing execution loops.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/strategic/test_intents.py`
