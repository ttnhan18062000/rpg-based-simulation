---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-COGNITION-FEATURE-MINING
artifact_type: plan
tags: [cognition, feature, mining]
---

# plan.md - Feature & Pattern Mining

Extract strategic features and run behavior pattern mining rules across simulation ticks/runs.

## Key Actions
1. Implement `CognitionFeatureExtractor` in `src/observability/cognition/feature_extractor.py`.
2. Extract metrics per run/entity, writing to `cognition_features.jsonl`.
3. Implement `CognitionPatternMiner` in `src/observability/cognition/pattern_miner.py`.
4. Define the rules for the 5 target failure patterns: `ProjectChurn`, `DetourLoop`, `StaleBlocker`, `LeadExhaustionStorm`, and `StrategicOverload`.
5. Output matched patterns to `cognition_patterns.json` under standard structure.
