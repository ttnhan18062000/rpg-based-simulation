---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260523-COGNITION-DIFF-EVENTS
phase: done
date: 2026-05-23
tags: [cognition, diff, events]
---

# TCK-20260523-COGNITION-DIFF-EVENTS

## Title

Cognition Graph Diff Builder and Event Integration

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement deterministic Strategic Cognition Graph diffing to compare subsequent entity snapshots and translate significant structural changes into high-salience SimulationEvents captured by the `EventRecorder` pipeline.

## Scope

- [x] Implement a stable, deterministic `CognitionGraphDiffBuilder` comparing graph nodes, edges, and strategic metadata (e.g. current project/objective switches).
- [x] Generate sorted, consistent JSON serialization format for diff outputs (`cognition_graph_diffs.jsonl`) avoiding unordered dictionary keys.
- [x] Map significant cognition changes to specialized SimulationEvents (e.g., `StrategicProjectChanged`, `StrategicBlockerAdded`, `StrategicLeadExhausted`).
- [x] Integrate event mapping into the post-commit observability cycle so events are saved directly into `simulation_events.jsonl`.
- [x] Write unit tests for diff builders (verifying empty diffs on identical graphs, exact blocker/lead changes) and golden tests.

## Out of Scope

- Snapshot recording logic (handled in TCK-20260523-COGNITION-SCHEMA-RECORDER).
- Multi-run pattern mining (handled in TCK-20260523-COGNITION-FEATURE-MINING).

## Acceptance Criteria

- [x] Node, edge, and metadata deltas are calculated correctly based on stable identifiers.
- [x] Diff computation is purely read-only and does not mutate strategic component records.
- [x] Diff JSON fields are deterministically ordered.
- [x] Events are correctly formatted and registered in the `EventRecorder` pipeline post-commit.
- [x] Enabling cognition event integration has zero effect on the simulation's state hash.

## Related Tickets

- TCK-20260523-COGNITION-SCHEMA-RECORDER
- TCK-20260523-COGNITION-FEATURE-MINING

## Related Docs

- `obs_sim_phase10.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/observability/cognition/`
- `src/observability/events/`

## Assumptions / Open Questions

- Assumes snapshot JSONL records are available and correctly formatted in the run directory.

## Implementation Notes

- Designed stateful detour counter tracking per blocker to identify infinite looping anomalies and emit `StrategicDetourLoopSuspected` events.
- Created `StrategicCognitionEvent` as a baseline Pydantic class that dynamically serializes strategic attributes both as class attributes and within a nested `payload` dict, providing flawless integration with both `EventRecorder` JSONL writing and downstream Warehouse / ClickHouse / Anomaly rule parsing.

## Test Summary

- Added extensive suite of unit checks in `tests/unit/observability/cognition/test_cognition_event_mapper.py` covering all event types and detour loop triggers.
- Implemented full end-to-end integration check in `tests/integration/observability/test_cognition_diff_events.py` ensuring snapshots, diff files, and JSONL events are saved perfectly with correct payload values.
- All tests passed 100% successfully.

## Files Changed

- `src/observability/cognition/event_mapper.py` (New)
- `src/observability/cognition/events.py` (Modified)
- `src/observability/cognition/recorder.py` (Modified)
- `src/engine/kernel.py` (Modified)
- `tests/unit/observability/cognition/test_cognition_event_mapper.py` (New)
- `tests/integration/observability/test_cognition_diff_events.py` (New)

## Completion Summary

- Successfully completed the entire implementation of Ticket 2 (Cognition Graph Diff Builder and Event Integration). Diffs and high-salience strategic events now flow deterministically during the post-commit observability cycle, with full clickhouse and warehouse compatibility.

