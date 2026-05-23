"""
Unit tests for the CognitionFeatureExtractor.
"""
import os
import json
import pytest
from pathlib import Path

from src.observability.cognition.feature_extractor import CognitionFeatureExtractor


class TestCognitionFeatureExtractor:
    """Milestone 62: Assert accurate feature aggregation from snapshots and diffs."""

    def test_empty_logs_handled_safely(self, tmp_path: Path):
        """Verify that a run with missing/empty cognition files returns an empty dict and doesn't crash."""
        # 1. Non-existent path
        features = CognitionFeatureExtractor.extract_features(str(tmp_path / "non_existent"))
        assert features == {}

        # 2. Empty directory
        features = CognitionFeatureExtractor.extract_features(str(tmp_path))
        assert features == {}

        # 3. Empty files
        (tmp_path / "cognition_graph_snapshots.jsonl").write_text("")
        (tmp_path / "cognition_graph_diffs.jsonl").write_text("")
        features = CognitionFeatureExtractor.extract_features(str(tmp_path))
        assert features == {}

    def test_feature_aggregation(self, tmp_path: Path):
        """Verify features are aggregated correctly from actual snapshot and diff logs."""
        snapshots_file = tmp_path / "cognition_graph_snapshots.jsonl"
        diffs_file = tmp_path / "cognition_graph_diffs.jsonl"

        # Write mock snapshots
        snaps = [
            # Tick 100: Project proj_a starts, blocker blocker_1 added
            {
                "schema_version": "1.0.0",
                "run_id": "run_test_01",
                "tick": 100,
                "entity_id": 42,
                "reason": "PROJECT_CHANGED",
                "current_project_id": "proj_a",
                "current_objective_id": "obj_a",
                "overload_source": None,
                "node_count": 2,
                "edge_count": 0,
                "graph_hash": "hash_100",
                "graph": {
                    "nodes": [
                        {"node_id": "proj_a", "kind": "project", "label": "Project A", "metadata": {}},
                        {"node_id": "blocker_1", "kind": "blocker", "label": "Locked Door", "metadata": {}},
                    ],
                    "edges": []
                }
            },
            # Tick 150: Blocker resolved, project shifts to detour proj_detour_1, overload triggered
            {
                "schema_version": "1.0.0",
                "run_id": "run_test_01",
                "tick": 150,
                "entity_id": 42,
                "reason": "OVERLOAD_CHANGED",
                "current_project_id": "proj_detour_1",
                "current_objective_id": "obj_a",
                "overload_source": "Too many leads",
                "node_count": 3,
                "edge_count": 0,
                "graph_hash": "hash_150",
                "graph": {
                    "nodes": [
                        {"node_id": "proj_detour_1", "kind": "project", "label": "Detour 1", "metadata": {}},
                        {"node_id": "lead_1", "kind": "lead", "label": "Find key", "metadata": {}},
                        {"node_id": "concern_1", "kind": "concern", "label": "Concern", "metadata": {}},
                    ],
                    "edges": []
                }
            },
            # Tick 300: Detour project completed, shift back to proj_a, lead_1 removed (exhausted)
            {
                "schema_version": "1.0.0",
                "run_id": "run_test_01",
                "tick": 300,
                "entity_id": 42,
                "reason": "PROJECT_CHANGED",
                "current_project_id": "proj_a",
                "current_objective_id": "obj_a",
                "overload_source": None,
                "node_count": 1,
                "edge_count": 0,
                "graph_hash": "hash_300",
                "graph": {
                    "nodes": [
                        {"node_id": "proj_a", "kind": "project", "label": "Project A", "metadata": {}},
                    ],
                    "edges": []
                }
            }
        ]

        with open(snapshots_file, "w") as f:
            for s in snaps:
                f.write(json.dumps(s) + "\n")

        # Write mock diffs
        diffs = [
            # Tick 150: blocker_1 removed, proj_detour_1, lead_1, concern_1 added
            {
                "schema_version": "1.0.0",
                "run_id": "run_test_01",
                "tick": 150,
                "entity_id": 42,
                "previous_graph_hash": "hash_100",
                "new_graph_hash": "hash_150",
                "reason": "OVERLOAD_CHANGED",
                "added_nodes": ["proj_detour_1", "lead_1", "concern_1"],
                "removed_nodes": ["blocker_1"],
                "changed_nodes": [],
                "added_edges": [],
                "removed_edges": [],
                "current_project_changed": True,
                "current_objective_changed": False,
                "blocker_delta_count": 1,
                "lead_delta_count": 1,
                "concern_delta_count": 1,
                "hypothesis_delta_count": 0,
                "project_delta_count": 1,
                "overload_changed": True
            },
            # Tick 300: lead_1 removed, proj_detour_1 removed
            {
                "schema_version": "1.0.0",
                "run_id": "run_test_01",
                "tick": 300,
                "entity_id": 42,
                "previous_graph_hash": "hash_150",
                "new_graph_hash": "hash_300",
                "reason": "PROJECT_CHANGED",
                "added_nodes": ["proj_a"],
                "removed_nodes": ["lead_1", "proj_detour_1", "concern_1"],
                "changed_nodes": [],
                "added_edges": [],
                "removed_edges": [],
                "current_project_changed": True,
                "current_objective_changed": False,
                "blocker_delta_count": 0,
                "lead_delta_count": 1,
                "concern_delta_count": 1,
                "hypothesis_delta_count": 0,
                "project_delta_count": 2,
                "overload_changed": True
            }
        ]

        with open(diffs_file, "w") as f:
            for d in diffs:
                f.write(json.dumps(d) + "\n")

        # Run extraction
        features_map = CognitionFeatureExtractor.extract_features(
            str(tmp_path),
            spec_data={
                "run_id": "run_test_01",
                "seed": 999,
                "scenario": "test_scenario",
                "scenario_type": "sandbox",
            }
        )

        assert 42 in features_map
        f = features_map[42]

        assert f["run_id"] == "run_test_01"
        assert f["seed"] == 999
        assert f["scenario_name"] == "test_scenario"
        assert f["scenario_type"] == "sandbox"
        assert f["snapshot_count"] == 3
        assert f["diff_count"] == 2
        assert f["project_switch_count"] == 2
        assert f["objective_switch_count"] == 0
        assert f["blocker_add_count"] == 0  # blocker_1 was present at tick 100 baseline, not added in diffs
        assert f["blocker_resolve_count"] == 1  # blocker_1 removed in diff at tick 150
        assert f["unresolved_blocker_count"] == 0
        assert f["lead_exhaustion_count"] == 1  # lead_1 removed at tick 300
        assert f["concern_raise_count"] == 1  # concern_1 added at tick 150
        assert f["detour_created_count"] == 1  # proj_detour_1 added at tick 150
        assert f["overload_count"] == 1  # tick 150 snapshot has overload_source
        assert f["latest_current_project"] == "proj_a"
        assert f["latest_current_objective"] == "obj_a"

        # Verify max project age: proj_a was active from 100-150 (50 ticks) and 300-300 (0 ticks), proj_detour_1 active 150-300 (150 ticks)
        # So max project age should be 150
        assert f["max_project_age"] == 150

        # Verify blocker_1 was present at tick 100, removed in diff tick 150.
        # Its age is 150 - 100 = 50 ticks
        assert f["max_blocker_age"] == 50

        # Verify graph churn rate: 2 switches / (300 - 100) = 0.01
        assert f["graph_churn_rate"] == 0.01
