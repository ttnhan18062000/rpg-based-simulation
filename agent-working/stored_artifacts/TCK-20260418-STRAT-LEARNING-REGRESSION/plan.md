---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260418-STRAT-LEARNING-REGRESSION
artifact_type: plan
tags: [strat, learning, regression]
---

# Resolve Strategic Learning Persistence Regression

Fixes a persistence regression where `LeadRecord` flags (`tested`, `is_exhausted`) are incorrectly reverted during simulation ticks.

## User Review Required

> [!IMPORTANT]
> The fix involves hardening the `StrategicState.apply_update` method to prevent "reverting" critical boolean flags. While this increases robustness, it assumes that once a lead is marked as tested or exhausted, it should stay that way for the duration of its lifecycle unless explicitly reset by a dedicated service (which currently doesn't exist).

## Proposed Changes

### AI Strategy & Navigation

#### [MODIFY] [navigation.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/states/navigation.py)
- Consolidate multiple `StrategicUpdate` objects into a single update object within the `INVESTIGATING` state handler. This prevents redundant application of updates and potential merging conflicts in the action proposal.

#### [MODIFY] [strategy.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/strategy.py)
- Update `StrategicState.apply_update` to include a protective check: if a `LeadRecord` in the update has `tested=False` but the existing record has `tested=True`, the `True` value is preserved. Same for `is_exhausted`.

#### [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/states/base.py)
- Enhance `_merge_intent_updates` to actually merge collection fields (like `leads_add_or_update`, `tested_lead_ids`) instead of overwriting the entire list. This ensures that sequential updates correctly accumulate state changes.

## Verification Plan

### Automated Tests
- `pytest tests/ai/test_learning_social.py -k test_intel_refutation_by_exhaustion`
- Ensure full regression suite passes to confirm no side effects on other strategic flows.

### Manual Verification
- None required.
