---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260412-STRAT-GRAPH-EXPORT
artifact_type: plan
tags: [strat, graph, export]
---

# Plan: Milestone 6 — Entity Cognition Graph Exporter

## Goal
Implement a structural graph schema and a read-only exporter service to capture entity strategic state in a deterministic, observable format compatible with Cytoscape.js.

## Proposed Changes
1. **Schema**: Create `src/core/models/cognition_graph.py` with Pydantic models.
2. **Exporter**: Create `src/core/logic/cognition_graph_exporter.py` for derivation logic.
3. **Adapter**: Create `src/api/adapters/cytoscape_adapter.py` for format conversion.
4. **Integration**: Update `scripts/test_harness.py` for regression observability.

## Verification
- Unit tests for schema validation and deterministic sorting.
- Integration tests in regression suite to verify "thinking" artifacts over time.
