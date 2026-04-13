# TCK-20260412-STRAT-GRAPH-EXPORT

## Title
Implement Exportable Entity Cognition Graph (Milestone 6)

## Status
DONE

## Request Summary
Create a canonical, deterministic, and observable representation of entity strategic state as a graph for regression testing and visualization.

## Scope
- Define typed graph schema (`GraphNode`, `GraphEdge`, `CognitionGraph`).
- Implement `EntityCognitionExporter` service to derive graph from entity state.
- Implement `CytoscapeAdapter` for visualization frontend compatibility.
- Integrate export into `scripts/test_harness.py`.
- Add unit and integration tests for determinism and structural integrity.

## Out of Scope
- Interactive graph visualization UI (handled by external tool/dashboard).
- Real-time streaming of graph updates (batch export only).

## Acceptance Criteria
- [x] Canonical schema exists in `src/core/models/cognition_graph.py`.
- [x] Exporter is strictly read-only and deterministic.
- [x] Exporter handles Directives, Projects, Objectives, and Continuity edges.
- [x] Cytoscape.js JSON format is supported via adapter.
- [x] Integration tests pass in the regression suite.

## Related Tickets
- TCK-20260412-STRAT-EVENT-REP (Previous Milestone)

## Related Docs
- docs/specs/2026-04-12-entity-cognition-graph-design.md

## Related Code Areas
- src/core/models/cognition_graph.py
- src/core/logic/cognition_graph_exporter.py
- src/api/adapters/cytoscape_adapter.py
- scripts/test_harness.py

## Implementation Notes
- Used HSL tailored colors for visual metadata (in future UI).
- Enforced strict sorting by ID in exporter for byte-identical determinism.
- Handled `entity.id` attribute correction during TDD loop.

## Test Summary
- Unit tests: `tests/core/test_cognition_graph_exporter.py` (4 passed)
- Integration tests: `tests/integration/strategy/test_cognition_graph_regression.py` (2 passed)

## Files Changed
- [NEW] [cognition_graph.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/cognition_graph.py)
- [NEW] [cognition_graph_exporter.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/logic/cognition_graph_exporter.py)
- [NEW] [cytoscape_adapter.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/adapters/cytoscape_adapter.py)
- [MODIFY] [test_harness.py](file:///home/vboxuser/Work/rpg-based-simulation/scripts/test_harness.py)
- [NEW] [test_cognition_graph_exporter.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/core/test_cognition_graph_exporter.py)
- [NEW] [test_cognition_graph_regression.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/integration/strategy/test_cognition_graph_regression.py)

## Completion Summary
Successfully implemented the strategic cognition graph exporter. The system now provides an authoritative "thinking" artifact that can be used to verify strategic continuity in regression tests.
