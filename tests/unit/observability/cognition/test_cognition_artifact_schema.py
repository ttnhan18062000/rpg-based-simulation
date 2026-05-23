"""
Unit contract tests for Cognition Graph Artifact Schemas.

Covers:
- Milestone 58: Stable artifact schema contract for snapshots and diffs.
- Anti-misdirection: Independent of active engine simulation tick logic.
"""
import pytest
import json
from typing import Dict, Any

# Define the set of valid snapshot reasons
VALID_REASONS = {
    "ANOMALY_TRIGGERED",
    "PROJECT_CHANGED",
    "OBJECTIVE_CHANGED",
    "BLOCKER_CHANGED",
    "LEAD_CHANGED",
    "CONCERN_CHANGED",
    "OVERLOAD_CHANGED",
    "DEBUG_SELECTED_ENTITY",
    "CERTIFICATION_BOUNDARY",
    "EVIDENCE_PACK_REQUEST",
}

# The latest stable schema version
SCHEMA_VERSION = "1.0.0"


def validate_snapshot_record(record: Dict[str, Any]) -> None:
    """Validates snapshot record invariants without external database schemas."""
    required = {
        "schema_version",
        "run_id",
        "tick",
        "entity_id",
        "reason",
        "node_count",
        "edge_count",
        "graph_hash",
        "graph",
    }
    # Check required fields
    for field in required:
        if field not in record:
            raise ValueError(f"Missing required field: '{field}'")

    # Invariant: schema version must be current stable
    if record["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema version: {record['schema_version']}")

    # Invariant: reason must be in valid enum set
    if record["reason"] not in VALID_REASONS:
        raise ValueError(f"Unknown trigger reason: {record['reason']}")

    # Invariant: graph hash must be a non-empty string
    if not isinstance(record["graph_hash"], str) or not record["graph_hash"]:
        raise ValueError("Invalid graph_hash field")

    # Check compact graph format
    graph = record["graph"]
    if not isinstance(graph, dict) or "nodes" not in graph or "edges" not in graph:
        raise ValueError("Graph must contain 'nodes' and 'edges' lists")

    nodes = graph["nodes"]
    edges = graph["edges"]
    if len(nodes) != record["node_count"]:
        raise ValueError(f"Node count mismatch: expected {record['node_count']}, got {len(nodes)}")
    if len(edges) != record["edge_count"]:
        raise ValueError(f"Edge count mismatch: expected {record['edge_count']}, got {len(edges)}")

    # Nodes must be compact
    for node in nodes:
        node_req = {"node_id", "kind", "label", "metadata"}
        for f in node_req:
            if f not in node:
                raise ValueError(f"Node missing required field: {f}")
        # Validate metadata size to prevent bloat
        metadata_str = json.dumps(node["metadata"])
        if len(metadata_str) > 1000:
            raise ValueError("Node metadata is too large (exceeds 1000 chars limit)")

    # Edges must be compact
    for edge in edges:
        edge_req = {"source_id", "target_id", "kind"}
        for f in edge_req:
            if f not in edge:
                raise ValueError(f"Edge missing required field: {f}")


def validate_diff_record(record: Dict[str, Any]) -> None:
    """Validates diff record invariants."""
    required = {
        "schema_version",
        "run_id",
        "tick",
        "entity_id",
        "previous_graph_hash",
        "new_graph_hash",
        "reason",
        "added_nodes",
        "removed_nodes",
        "changed_nodes",
        "added_edges",
        "removed_edges",
    }
    for field in required:
        if field not in record:
            raise ValueError(f"Missing required field: '{field}'")

    if record["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"Unsupported schema version: {record['schema_version']}")

    if record["reason"] not in VALID_REASONS:
        raise ValueError(f"Unknown trigger reason: {record['reason']}")


class TestCognitionArtifactSchema:
    """Milestone 58: Cognition schema validation checks."""

    def test_valid_snapshot_serialization(self):
        """Verify standard rich snapshot serializes and passes validation rules."""
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "run_id": "test_run_123",
            "tick": 42,
            "entity_id": 99,
            "reason": "ANOMALY_TRIGGERED",
            "trigger_event_id": "evt_001",
            "trigger_anomaly_id": "anom_002",
            "current_project_id": "p1",
            "current_objective_id": "o1",
            "overload_source": None,
            "node_count": 2,
            "edge_count": 1,
            "graph_hash": "a1b2c3d4",
            "graph": {
                "nodes": [
                    {
                        "node_id": "n1",
                        "kind": "project",
                        "label": "Crafting",
                        "status": "ACTIVE",
                        "metadata": {"custom_key": "val"},
                    },
                    {
                        "node_id": "n2",
                        "kind": "blocker",
                        "label": "No Iron",
                        "metadata": {},
                    },
                ],
                "edges": [
                    {
                        "source_id": "n2",
                        "target_id": "n1",
                        "kind": "blocks",
                        "metadata": {},
                    }
                ],
            },
        }
        # Assert no validation error
        validate_snapshot_record(snapshot)
        serialized = json.dumps(snapshot)
        assert json.loads(serialized) == snapshot

    def test_missing_required_fields(self):
        """Verify validation fails when a required field is missing."""
        invalid_snapshot = {
            "schema_version": SCHEMA_VERSION,
            "run_id": "test_run_123",
            # "tick": 42,  # Missing required field
            "entity_id": 99,
            "reason": "ANOMALY_TRIGGERED",
            "node_count": 0,
            "edge_count": 0,
            "graph_hash": "hash_val",
            "graph": {"nodes": [], "edges": []},
        }
        with pytest.raises(ValueError, match="Missing required field: 'tick'"):
            validate_snapshot_record(invalid_snapshot)

    def test_unknown_reason_rejected(self):
        """Verify validation rejects unknown reasons."""
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "run_id": "test_run_123",
            "tick": 42,
            "entity_id": 99,
            "reason": "TOTALLY_UNKNOWN_REASON",
            "node_count": 0,
            "edge_count": 0,
            "graph_hash": "hash_val",
            "graph": {"nodes": [], "edges": []},
        }
        with pytest.raises(ValueError, match="Unknown trigger reason: TOTALLY_UNKNOWN_REASON"):
            validate_snapshot_record(snapshot)

    def test_graph_hash_required(self):
        """Verify validation rejects invalid or empty graph hash."""
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "run_id": "test_run_123",
            "tick": 42,
            "entity_id": 99,
            "reason": "ANOMALY_TRIGGERED",
            "node_count": 0,
            "edge_count": 0,
            "graph_hash": "",
            "graph": {"nodes": [], "edges": []},
        }
        with pytest.raises(ValueError, match="Invalid graph_hash field"):
            validate_snapshot_record(snapshot)

    def test_empty_graph_snapshot_valid(self):
        """Verify an empty graph is syntactically valid."""
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "run_id": "test_run_123",
            "tick": 42,
            "entity_id": 99,
            "reason": "ANOMALY_TRIGGERED",
            "node_count": 0,
            "edge_count": 0,
            "graph_hash": "empty_hash",
            "graph": {"nodes": [], "edges": []},
        }
        validate_snapshot_record(snapshot)

    def test_large_metadata_rejected(self):
        """Verify huge metadata block causes a validation failure."""
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "run_id": "test_run_123",
            "tick": 42,
            "entity_id": 99,
            "reason": "ANOMALY_TRIGGERED",
            "node_count": 1,
            "edge_count": 0,
            "graph_hash": "hash_val",
            "graph": {
                "nodes": [
                    {
                        "node_id": "n1",
                        "kind": "project",
                        "label": "Crafting",
                        "metadata": {"bloat": "x" * 2000},
                    }
                ],
                "edges": [],
            },
        }
        with pytest.raises(ValueError, match="Node metadata is too large"):
            validate_snapshot_record(snapshot)

    def test_valid_diff_serialization(self):
        """Verify standard diff record serializes and validates successfully."""
        diff = {
            "schema_version": SCHEMA_VERSION,
            "run_id": "test_run_123",
            "tick": 43,
            "entity_id": 99,
            "previous_graph_hash": "a1b2c3d4",
            "new_graph_hash": "e5f6g7h8",
            "reason": "PROJECT_CHANGED",
            "added_nodes": ["n3"],
            "removed_nodes": [],
            "changed_nodes": ["n1"],
            "added_edges": [{"source_id": "n3", "target_id": "n1", "kind": "drives"}],
            "removed_edges": [],
            "current_project_changed": True,
            "current_objective_changed": False,
            "blocker_delta_count": 0,
            "lead_delta_count": 0,
            "concern_delta_count": 0,
            "hypothesis_delta_count": 0,
            "project_delta_count": 1,
            "overload_changed": False,
        }
        validate_diff_record(diff)
        serialized = json.dumps(diff)
        assert json.loads(serialized) == diff
