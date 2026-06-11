---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260523-COGNITION-FEATURE-MINING
phase: done
date: 2026-05-23
tags: [cognition, feature, mining]
---

# TCK-20260523-COGNITION-FEATURE-MINING

## Title

Cognition Feature Extractor and Strategic Pattern Miner

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the logic to extract structured strategic features from raw cognition artifacts and analyze these features across ticks/runs to mine complex behavioral patterns (e.g. stalled progress, looping detours, or strategic overloading).

## Scope

- Implement `CognitionFeatureExtractor` aggregating metrics (snapshot counts, project switches, blocker additions/resolutions, graph churn rate) into `cognition_features.jsonl` / parquet.
- Implement `CognitionPatternMiner` detecting 5 specific strategic behavior patterns:
  1. `ProjectChurn`: Rapid switching between projects without completion.
  2. `DetourLoop`: Repeated detours created while the original blocker remains unresolved.
  3. `StaleBlocker`: Active blocker lingering past age thresholds while leads are available.
  4. `LeadExhaustionStorm`: High rate of lead exhaustion causing strategic stalls.
  5. `StrategicOverload`: Repeated bandwidth enforcement throwing away concerns/leads.
- Ensure pattern mining outputs are structured into `cognition_patterns.json`.
- Add unit/integration tests confirming correct feature aggregation, and positive/negative test patterns to protect against false positives.

## Out of Scope

- Exposing mined patterns via API/CLI (handled in TCK-20260523-COGNITION-REPORTS-API).
- Snapshotting and diffing logic.

## Acceptance Criteria

- [x] Feature extraction cleanly supports runs with zero cognition logs without crashes (returns empty features safely).
- [x] Pattern miner distinguishes normal progression (e.g., normal project shifts) from actual behavioral anomalies.
- [x] Mined patterns save to JSON containing severity, affected runs/entities, and suspected subsystems.
- [x] Multi-run dataset joining on `run_id` and `entity_id` works correctly.

## Related Tickets

- TCK-20260523-COGNITION-DIFF-EVENTS
- TCK-20260523-COGNITION-REPORTS-API

## Related Docs

- `obs_sim_phase10.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/cognition/`
- `src/observability/mining/`

## Assumptions / Open Questions

- Assumes access to run databases or local file records for multiple simulation runs.

## Implementation Notes

- Designed extremely robust and sparse-snapshot-proof age calculation.
- Separated thresholds out for flexibility.

## Test Summary

- `tests/unit/observability/cognition/test_cognition_feature_extractor.py` (2 tests, all passing)
- `tests/unit/observability/cognition/test_cognition_pattern_miner.py` (3 tests, all passing)
- `tests/integration/observability/test_cognition_pattern_mining_flow.py` (1 test, all passing)

## Files Changed

- `src/observability/cognition/feature_extractor.py`
- `src/observability/cognition/pattern_miner.py`
- `src/observability/cognition/__init__.py`
- `tests/unit/observability/cognition/test_cognition_feature_extractor.py`
- `tests/unit/observability/cognition/test_cognition_pattern_miner.py`
- `tests/integration/observability/test_cognition_pattern_mining_flow.py`

## Completion Summary

- Implemented the full feature extraction and pattern miner layers. Validated against comprehensive unit and integration mock runs covering positive triggers for all 5 Failure patterns and negative guards. All tests passed.

