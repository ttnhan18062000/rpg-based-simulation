---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: 2026-04-12
---

# Design Spec: Entity Cognition Graph Exporter (Milestone 6)

## Title
Exportable Entity Cognition Graph for Observability and Verification

## Status
DRAFT

## Context
As the RPG simulation grows in strategic complexity, understanding "why" an entity makes a decision becomes challenging. While existing presenters provide text-based views, they are optimized for display rather than canonical structural verification. 

Milestone 6 introduces a deterministic, graph-based representation of an entity's internal "thinking" state. This graph allows for:
1. **Visual Debugging**: Using tools like Cytoscape.js to see relationships between goals, blockers, and history.
2. **Regression Testing**: Capturing "golden" graph snapshots to verify that strategic reasoning hasn't drifted.
3. **Observability**: Providing a unified view of disparate cognitive domains (Directives, Projects, Social, etc.).

## Requirements

### Functional
- Derive a canonical graph from any `Entity` with a `MindAspect`.
- Support core strategic nodes: Directives, Projects, Objectives, Concerns, Leads, Blockers, Obligations, and Contracts.
- Support explicit continuity edges: `current_project`, `current_objective`.
- Support interruption edges: `interrupted_by` (suspended project -> cause).
- Export to **Cytoscape.js JSON** format (elements/nodes/edges).
- Ensure 100% determinism (byte-identical output for identical input).

### Non-Functional
- **Read-Only**: No mutation of entity state during export.
- **Stable IDs**: Node IDs must be stable across ticks (e.g., based on record IDs).
- **Performance**: Graph construction should be efficient (linear with respect to cognition state size).

## Architecture

### Components
1. **`src/core/models/cognition_graph.py`**: Pydantic models for the canonical graph (nodes, edges, metadata).
2. **`src/core/logic/cognition_graph_exporter.py`**: Service responsible for traversing the `StrategicState` and generating the `CognitionGraph`.
3. **`src/api/adapters/cytoscape_adapter.py`**: (Optional) Utility to transform the canonical graph into the Cytoscape structure.
4. **`src/ui/cli/cognition_export_command.py`**: CLI command to dump the graph to a file.

### Data Flow
1. **Trigger**: Test harness, CLI, or API request.
2. **Derivation**: `EntityCognitionExporter` takes `Entity` + `worldinfo`.
3. **Traversal**:
    - Creates `Root` node for Entity.
    - Adds `Directive` nodes; links from Root.
    - Adds `Project` nodes; links from parent Directive or Root.
    - Adds `Objective` nodes; links from parent Project.
    - Adds `Blocker` nodes; links from target Objective.
    - Adds special edges for `current` status and `interruption` causes.
4. **Serialization**: The resulting `CognitionGraph` is returned/serialized to JSON.

## Determinism Rules
- **Node Ordering**: Sorted by `node_id`.
- **Edge Ordering**: Sorted by `edge_id` (derived from `source:target:kind`).
- **Stable IDs**: 
    - Records with IDs (e.g., `project_id`) use those as stable IDs.
    - Derived edges use lexicographical sources/targets.

## Verification Plan
- **Unit Tests**:
    - `tests/core/test_cognition_graph_schema.py`: Validate schema and serialization.
    - `tests/core/test_cognition_graph_exporter.py`: Verify node/edge generation for specific scenarios (e.g., project with blocker).
- **Integration Tests**:
    - Verify that a multi-tick simulation produces stable, predictable graph sequences.
    - Verify non-mutation of the entity.

## Open Questions
- None (Cytoscape JSON confirmed as the visual format).
