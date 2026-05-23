"""
Unit tests for the CognitionGraphDiffBuilder.
"""
import pytest
import json
from src.observability.cognition.diff_builder import CognitionGraphDiffBuilder
from src.observability.cognition.schema import SCHEMA_VERSION, build_snapshot_record


class TestCognitionGraphDiffBuilder:
    """Milestone 60: deterministic diff builder checks."""

    @pytest.fixture
    def empty_snapshot(self):
        return build_snapshot_record(
            run_id="run_1",
            tick=1,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[],
            edges=[],
        )

    def test_same_graph_produces_empty_diff(self, empty_snapshot):
        """Verify comparing identical snapshots yields empty diff fields."""
        diff = CognitionGraphDiffBuilder.compute_diff(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            prev_snapshot=empty_snapshot,
            curr_snapshot=empty_snapshot,
        )

        assert diff["schema_version"] == SCHEMA_VERSION
        assert diff["previous_graph_hash"] == empty_snapshot["graph_hash"]
        assert diff["new_graph_hash"] == empty_snapshot["graph_hash"]
        assert not diff["added_nodes"]
        assert not diff["removed_nodes"]
        assert not diff["changed_nodes"]
        assert not diff["added_edges"]
        assert not diff["removed_edges"]
        assert not diff["current_project_changed"]
        assert not diff["current_objective_changed"]
        assert diff["blocker_delta_count"] == 0

    def test_added_blocker_detected(self):
        """Verify added blocker node is captured in added_nodes and deltas."""
        snap_a = build_snapshot_record(
            run_id="run_1",
            tick=1,
            entity_id=42,
            reason="PROJECT_CHANGED",
            nodes=[],
            edges=[],
            current_project_id="p1",
        )

        blocker_node = {
            "node_id": "blocker_01",
            "kind": "blocker",
            "label": "Stuck in Mud",
            "metadata": {"severity": "high"},
        }
        snap_b = build_snapshot_record(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="BLOCKER_CHANGED",
            nodes=[blocker_node],
            edges=[],
            current_project_id="p1",
        )

        diff = CognitionGraphDiffBuilder.compute_diff(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="BLOCKER_CHANGED",
            prev_snapshot=snap_a,
            curr_snapshot=snap_b,
        )

        assert diff["added_nodes"] == ["blocker_01"]
        assert not diff["removed_nodes"]
        assert diff["blocker_delta_count"] == 1
        assert diff["project_delta_count"] == 0

    def test_removed_lead_detected(self):
        """Verify removed lead node is captured in removed_nodes."""
        lead_node = {
            "node_id": "lead_01",
            "kind": "lead",
            "label": "Investigate Iron Mine",
            "metadata": {},
        }
        snap_a = build_snapshot_record(
            run_id="run_1",
            tick=1,
            entity_id=42,
            reason="LEAD_CHANGED",
            nodes=[lead_node],
            edges=[],
        )
        snap_b = build_snapshot_record(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="LEAD_CHANGED",
            nodes=[],
            edges=[],
        )

        diff = CognitionGraphDiffBuilder.compute_diff(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="LEAD_CHANGED",
            prev_snapshot=snap_a,
            curr_snapshot=snap_b,
        )

        assert not diff["added_nodes"]
        assert diff["removed_nodes"] == ["lead_01"]
        assert diff["lead_delta_count"] == 1

    def test_changed_project_status_detected(self):
        """Verify node attribute changes trigger changed_nodes entry."""
        node_a = {
            "node_id": "proj_1",
            "kind": "project",
            "label": "Clear Forest",
            "metadata": {"status": "ACTIVE"},
        }
        snap_a = build_snapshot_record(
            run_id="run_1",
            tick=1,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[node_a],
            edges=[],
        )

        node_b = {
            "node_id": "proj_1",
            "kind": "project",
            "label": "Clear Forest",
            "metadata": {"status": "COMPLETED"},
        }
        snap_b = build_snapshot_record(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[node_b],
            edges=[],
        )

        diff = CognitionGraphDiffBuilder.compute_diff(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            prev_snapshot=snap_a,
            curr_snapshot=snap_b,
        )

        assert diff["changed_nodes"] == ["proj_1"]
        assert diff["project_delta_count"] == 1

    def test_changed_metadata_switches_detected(self):
        """Verify current_project_changed and overload_changed are computed correctly."""
        snap_a = build_snapshot_record(
            run_id="run_1",
            tick=1,
            entity_id=42,
            reason="PROJECT_CHANGED",
            nodes=[],
            edges=[],
            current_project_id="p1",
            overload_source=None,
        )
        snap_b = build_snapshot_record(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="PROJECT_CHANGED",
            nodes=[],
            edges=[],
            current_project_id="p2",
            overload_source="cognitive_load",
        )

        diff = CognitionGraphDiffBuilder.compute_diff(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="PROJECT_CHANGED",
            prev_snapshot=snap_a,
            curr_snapshot=snap_b,
        )

        assert diff["current_project_changed"] is True
        assert diff["current_objective_changed"] is False
        assert diff["overload_changed"] is True

    def test_edge_addition_removal_detected(self):
        """Verify added and removed edges are detected."""
        snap_a = build_snapshot_record(
            run_id="run_1",
            tick=1,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[{"node_id": "a", "kind": "project", "label": "A", "metadata": {}},
                   {"node_id": "b", "kind": "blocker", "label": "B", "metadata": {}}],
            edges=[{"source_id": "b", "target_id": "a", "kind": "blocks"}],
        )

        snap_b = build_snapshot_record(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[{"node_id": "a", "kind": "project", "label": "A", "metadata": {}},
                   {"node_id": "b", "kind": "blocker", "label": "B", "metadata": {}}],
            edges=[{"source_id": "a", "target_id": "b", "kind": "resolves"}],
        )

        diff = CognitionGraphDiffBuilder.compute_diff(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            prev_snapshot=snap_a,
            curr_snapshot=snap_b,
        )

        assert diff["added_edges"] == [{"source_id": "a", "target_id": "b", "kind": "resolves"}]
        assert diff["removed_edges"] == [{"source_id": "b", "target_id": "a", "kind": "blocks"}]

    def test_deterministic_key_ordering(self):
        """Verify that diff list elements are sorted alphabetically by ID/keys."""
        snap_a = build_snapshot_record(
            run_id="run_1",
            tick=1,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[],
            edges=[],
        )
        # Added nodes in out-of-order sequence
        snap_b = build_snapshot_record(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[
                {"node_id": "z", "kind": "lead", "label": "Z", "metadata": {}},
                {"node_id": "a", "kind": "blocker", "label": "A", "metadata": {}},
                {"node_id": "m", "kind": "project", "label": "M", "metadata": {}},
            ],
            edges=[
                {"source_id": "z", "target_id": "m", "kind": "points"},
                {"source_id": "a", "target_id": "m", "kind": "blocks"},
            ],
        )

        diff = CognitionGraphDiffBuilder.compute_diff(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            prev_snapshot=snap_a,
            curr_snapshot=snap_b,
        )

        # Nodes should be sorted alphabetically: ["a", "m", "z"]
        assert diff["added_nodes"] == ["a", "m", "z"]
        # Edges should be sorted by source_id, target_id, kind
        assert diff["added_edges"] == [
            {"source_id": "a", "target_id": "m", "kind": "blocks"},
            {"source_id": "z", "target_id": "m", "kind": "points"},
        ]

    def test_diff_does_not_mutate_input_graphs(self):
        """Verify computing diff doesn't touch the original snapshots."""
        snap_a = build_snapshot_record(
            run_id="run_1",
            tick=1,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[{"node_id": "n1", "kind": "project", "label": "P", "metadata": {}}],
            edges=[],
        )
        snap_b = build_snapshot_record(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            nodes=[{"node_id": "n1", "kind": "project", "label": "P", "metadata": {"status": "ACTIVE"}}],
            edges=[],
        )

        snap_a_str = json.dumps(snap_a)
        snap_b_str = json.dumps(snap_b)

        _ = CognitionGraphDiffBuilder.compute_diff(
            run_id="run_1",
            tick=2,
            entity_id=42,
            reason="ANOMALY_TRIGGERED",
            prev_snapshot=snap_a,
            curr_snapshot=snap_b,
        )

        assert json.dumps(snap_a) == snap_a_str
        assert json.dumps(snap_b) == snap_b_str

    def test_golden_file_diff_output(self, tmp_path):
        """Golden test verifying rich transitions generate exact expected schema output."""
        snap_a = build_snapshot_record(
            run_id="golden_run",
            tick=10,
            entity_id=1,
            reason="PROJECT_CHANGED",
            nodes=[
                {"node_id": "proj_1", "kind": "project", "label": "Mine Iron", "metadata": {"status": "ACTIVE"}},
                {"node_id": "block_1", "kind": "blocker", "label": "No pickaxe", "metadata": {}},
            ],
            edges=[
                {"source_id": "block_1", "target_id": "proj_1", "kind": "blocks"}
            ],
            current_project_id="proj_1",
        )

        snap_b = build_snapshot_record(
            run_id="golden_run",
            tick=11,
            entity_id=1,
            reason="BLOCKER_CHANGED",
            nodes=[
                {"node_id": "proj_1", "kind": "project", "label": "Mine Iron", "metadata": {"status": "ACTIVE"}},
                {"node_id": "lead_1", "kind": "lead", "label": "Forge Pickaxe", "metadata": {}},
            ],
            edges=[
                {"source_id": "lead_1", "target_id": "proj_1", "kind": "resolves"}
            ],
            current_project_id="proj_1",
        )

        diff = CognitionGraphDiffBuilder.compute_diff(
            run_id="golden_run",
            tick=11,
            entity_id=1,
            reason="BLOCKER_CHANGED",
            prev_snapshot=snap_a,
            curr_snapshot=snap_b,
        )

        # Save to temporary path as if writing to file
        out_file = tmp_path / "diff_golden.json"
        with open(out_file, "w") as f:
            json.dump(diff, f, sort_keys=True, indent=2)

        # Load and verify exact golden structure
        with open(out_file, "r") as f:
            loaded_diff = json.load(f)

        assert loaded_diff["schema_version"] == SCHEMA_VERSION
        assert loaded_diff["previous_graph_hash"] == snap_a["graph_hash"]
        assert loaded_diff["new_graph_hash"] == snap_b["graph_hash"]
        assert loaded_diff["added_nodes"] == ["lead_1"]
        assert loaded_diff["removed_nodes"] == ["block_1"]
        assert loaded_diff["changed_nodes"] == []
        assert loaded_diff["added_edges"] == [{"source_id": "lead_1", "target_id": "proj_1", "kind": "resolves"}]
        assert loaded_diff["removed_edges"] == [{"source_id": "block_1", "target_id": "proj_1", "kind": "blocks"}]
        assert loaded_diff["blocker_delta_count"] == 1
        assert loaded_diff["lead_delta_count"] == 1
        assert loaded_diff["current_project_changed"] is False
