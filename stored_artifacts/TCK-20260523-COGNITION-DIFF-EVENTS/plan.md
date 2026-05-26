# plan.md - Graph Diffing & Event Mapping

Compute deterministic differences between cognition graph snapshots and translate them to high-severity SimulationEvents.

## Key Actions
1. Implement `CognitionGraphDiffBuilder` in `src/observability/cognition/diff_builder.py`.
2. Ensure deterministic ordering of diff outputs (sort nodes/edges by ID and type) to guarantee reproducible test signatures.
3. Map diff deltas to simulation event definitions (`StrategicProjectChanged`, `StrategicBlockerAdded`, etc.).
4. Register the event mapper into the post-commit observability cycle so that it appends cleanly to `simulation_events.jsonl`.
