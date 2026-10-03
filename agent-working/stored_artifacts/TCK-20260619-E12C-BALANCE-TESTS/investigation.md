---
ticket_id: TCK-20260619-E12C-BALANCE-TESTS
phase: investigation
date: 2026-06-20
---

# Investigation: Balance Regression Tests

## Key Findings

- tests/integration/scenarios/ exists; has __init__.py
- Other integration tests call kernel.shutdown() after ticks — required to avoid QueueDrainWorker thread leak
- FeatureFlagManager has no module-level FEATURE_FLAGS dict; must instantiate FeatureFlagManager() to read defaults
- AdventureRouteOption does NOT have an urgency field — urgency comes from entity.self_model.needs.active_needs

## E12A Baselines Used

- ATTRITION_CAP = 0.60 (E12A measured 46.7%)
- CONFIDENCE_BONUS_WEIGHT = 0.15 (from scoring.py)
- PERSONALITY_BIAS_WEIGHT = 0.25 (from scoring.py)
- BLOCKER_PENALTY = 2.0 (from scoring.py, E12B decision: keep)
