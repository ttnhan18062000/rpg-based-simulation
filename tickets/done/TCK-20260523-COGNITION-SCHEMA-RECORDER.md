---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260523-COGNITION-SCHEMA-RECORDER
phase: done
date: 2026-05-23
tags: [cognition, schema, recorder]
---

# TCK-20260523-COGNITION-SCHEMA-RECORDER

## Title

Cognition Graph Artifact Schema and Triggered Snapshot Recorder

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Establish the initial structural foundation for Phase 10: define stable artifact schemas for strategic cognition snapshots, build a read-only post-commit snapshot recorder that leverages the existing `CognitionGraphExporter`, and implement capture policies restricting snapshots to controlled, low-overhead moments.

## Scope

- Define stable JSON schema contract for entity strategic cognition snapshots (`cognition_graph_snapshots.jsonl`).
- Implement `CognitionCapturePolicy` managing capture triggers (anomaly-based like stuck actors, or strategy-based like project/objective shifts).
- Implement `ObservabilityCognitionRecorder` executing post-commit snapshot exports to run directory.
- Support mode-based behavior (`OFF`, `LIGHT`, `DEBUG`, `LONG_RUN`, `CERTIFICATION`).
- Create unit tests for artifact schema validation without simulation dependencies.
- Create unit/integration tests for the trigger policy and post-commit recording.

## Out of Scope

- Building graph diff computation logic (handled in TCK-20260523-COGNITION-DIFF-EVENTS).
- Synthesizing patterns or mining features (handled in TCK-20260523-COGNITION-FEATURE-MINING).

## Acceptance Criteria

- [x] Schema contract serializes to standard JSON format including `schema_version`, `run_id`, `tick`, `entity_id`, `reason`, `graph_hash`, and node/edge collections.
- [x] Snapshot capture respects trigger rules (does not log every entity on every tick).
- [x] Recording occurs strictly post-commit during simulation ticks, guaranteeing no state mutations or state hash drifts.
- [x] All unit and integration tests for recorder policy pass successfully.

## Related Tickets

- TCK-20260523-COGNITION-DIFF-EVENTS
- TCK-20260523-COGNITION-FEATURE-MINING

## Related Docs

- `obs_sim_phase10.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/systems/strategic_systems/cognition_export.py`
- `src/observability/` (new module `src/observability/cognition/`)

## Assumptions / Open Questions

- Assumes existing strategic components are fully initialized on HERO entities.

## Implementation Notes

- Fully implemented post-commit execution pattern in Kernel post-tick phase observability hooks.
- Used dataclasses.replace to handle immutable state updates cleanly in unit tests.

## Test Summary

- `tests/unit/observability/cognition/test_cognition_artifact_schema.py` (7 tests passed)
- `tests/unit/observability/cognition/test_cognition_capture_policy.py` (4 tests passed)
- `tests/integration/observability/test_cognition_snapshot_artifact.py` (4 tests passed)

## Files Changed

- [NEW] `src/observability/cognition/schema.py`
- [NEW] `src/observability/cognition/recorder.py`
- [MODIFY] `src/engine/kernel.py`
- [NEW] `tests/unit/observability/cognition/test_cognition_artifact_schema.py`
- [NEW] `tests/unit/observability/cognition/test_cognition_capture_policy.py`
- [NEW] `tests/integration/observability/test_cognition_snapshot_artifact.py`

## Completion Summary

- Architected stable snapshot metadata schema ensuring sorting determinism and collision-resistant `graph_hash` logic.
- Implemented `CognitionCapturePolicy` restricting state snapshot recording frequency to prevent memory or file bloat under LIGHT and LONG_RUN modes.
- Wired `ObservabilityCognitionRecorder` to `Kernel` post-commit pipeline hooks ensuring zero state hash drift and full read-only safety.
