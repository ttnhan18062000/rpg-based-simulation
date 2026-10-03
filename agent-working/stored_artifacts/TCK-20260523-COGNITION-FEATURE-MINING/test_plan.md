---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-COGNITION-FEATURE-MINING
artifact_type: test_plan
tags: [cognition, feature, mining]
---

# test_plan.md - Mining Tests

## Unit Tests
- `tests/unit/observability/cognition/test_cognition_feature_extractor.py`:
  - Verify project switches and blocker ages are calculated correctly.
  - Verify empty logs produce empty datasets safely.
- `tests/unit/observability/cognition/test_cognition_pattern_miner.py`:
  - Assert ProjectChurn is detected when projects change rapidly.
  - Assert DetourLoop is detected on repeated detours with same blocker.
  - Assert negative guards: normal progress should never match churn patterns.

## Integration Tests
- `tests/integration/observability/test_cognition_pattern_mining_flow.py`:
  - Run full mining logic over raw mock outputs and assert accurate matches in `cognition_patterns.json`.
