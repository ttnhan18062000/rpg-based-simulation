"""
Integration test for strategic cognition pattern mining flow.
"""
import os
import json
import pytest
from pathlib import Path

from src.observability.cognition.feature_extractor import CognitionFeatureExtractor
from src.observability.cognition.pattern_miner import CognitionPatternMiner


class TestCognitionPatternMiningFlow:
    """Milestone 63: Integration tests for the full strategic behavior mining pipeline."""

    def test_full_mining_flow(self, tmp_path: Path):
        """Verifies end-to-end extraction and matching of all 5 strategic cognition failure patterns."""
        run_dir = tmp_path / "run_integration_01"
        os.makedirs(run_dir, exist_ok=True)

        snapshots_file = run_dir / "cognition_graph_snapshots.jsonl"
        diffs_file = run_dir / "cognition_graph_diffs.jsonl"

        # Construct comprehensive snapshots to trigger ALL 5 patterns
        # Entity 1: triggers ProjectChurn, DetourLoop, LeadExhaustionStorm, StrategicOverload
        # Entity 2: triggers StaleBlocker (no project switches, blocker remains active, leads exist)
        snaps = [
            # Entity 1 snaps
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 100, "entity_id": 1, "reason": "PROJECT_CHANGED",
                "current_project_id": "proj_a", "current_objective_id": "obj_a", "overload_source": "Overload 1",
                "graph": {
                    "nodes": [
                        {"node_id": "proj_a", "kind": "project", "label": "Project A"},
                        {"node_id": "blocker_1", "kind": "blocker", "label": "Blocker"},
                        {"node_id": "lead_active", "kind": "lead", "label": "Active Lead"}
                    ],
                    "edges": []
                }
            },
            # Tick 150: lead_active removed, lead_2 added
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 150, "entity_id": 1, "reason": "OVERLOAD_CHANGED",
                "current_project_id": "proj_b", "current_objective_id": "obj_a", "overload_source": "Overload 2",
                "graph": {
                    "nodes": [
                        {"node_id": "proj_b", "kind": "project", "label": "Project B"},
                        {"node_id": "blocker_1", "kind": "blocker", "label": "Blocker"},
                        {"node_id": "proj_detour_1", "kind": "project", "label": "Detour 1"},
                        {"node_id": "lead_2", "kind": "lead", "label": "Lead 2"}
                    ],
                    "edges": []
                }
            },
            # Tick 250: lead_2 removed, lead_3 added
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 250, "entity_id": 1, "reason": "OVERLOAD_CHANGED",
                "current_project_id": "proj_c", "current_objective_id": "obj_a", "overload_source": "Overload 3",
                "graph": {
                    "nodes": [
                        {"node_id": "proj_c", "kind": "project", "label": "Project C"},
                        {"node_id": "blocker_1", "kind": "blocker", "label": "Blocker"},
                        {"node_id": "proj_detour_2", "kind": "project", "label": "Detour 2"},
                        {"node_id": "lead_3", "kind": "lead", "label": "Lead 3"}
                    ],
                    "edges": []
                }
            },
            # Tick 350: lead_3 removed
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 350, "entity_id": 1, "reason": "PROJECT_CHANGED",
                "current_project_id": "proj_a", "current_objective_id": "obj_a", "overload_source": None,
                "graph": {
                    "nodes": [
                        {"node_id": "proj_a", "kind": "project", "label": "Project A"},
                        {"node_id": "blocker_1", "kind": "blocker", "label": "Blocker"},
                    ],
                    "edges": []
                }
            },

            # Entity 2 snaps (StaleBlocker: active blocker unresolved for 250 ticks, project unchanged, lead exists)
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 100, "entity_id": 2, "reason": "PROJECT_CHANGED",
                "current_project_id": "proj_x", "current_objective_id": "obj_x", "overload_source": None,
                "graph": {
                    "nodes": [
                        {"node_id": "proj_x", "kind": "project", "label": "Project X"},
                        {"node_id": "blocker_stale", "kind": "blocker", "label": "Stale Blocker"},
                        {"node_id": "lead_active_2", "kind": "lead", "label": "Active Lead"}
                    ],
                    "edges": []
                }
            },
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 350, "entity_id": 2, "reason": "DEBUG_SELECTED_ENTITY",
                "current_project_id": "proj_x", "current_objective_id": "obj_x", "overload_source": None,
                "graph": {
                    "nodes": [
                        {"node_id": "proj_x", "kind": "project", "label": "Project X"},
                        {"node_id": "blocker_stale", "kind": "blocker", "label": "Stale Blocker"},
                        {"node_id": "lead_active_2", "kind": "lead", "label": "Active Lead"}
                    ],
                    "edges": []
                }
            },
        ]
        with open(snapshots_file, "w") as f:
            for s in snaps:
                f.write(json.dumps(s) + "\n")

        diffs = [
            # Entity 1 diffs
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 150, "entity_id": 1, "previous_graph_hash": "hash_100", "new_graph_hash": "hash_150",
                "reason": "OVERLOAD_CHANGED", "added_nodes": ["proj_b", "proj_detour_1", "lead_2"], "removed_nodes": ["lead_active"], "changed_nodes": [],
                "added_edges": [], "removed_edges": [], "current_project_changed": True, "current_objective_changed": False, "overload_changed": True
            },
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 250, "entity_id": 1, "previous_graph_hash": "hash_150", "new_graph_hash": "hash_250",
                "reason": "OVERLOAD_CHANGED", "added_nodes": ["proj_c", "proj_detour_2", "lead_3"], "removed_nodes": ["lead_2"], "changed_nodes": [],
                "added_edges": [], "removed_edges": [], "current_project_changed": True, "current_objective_changed": False, "overload_changed": True
            },
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 350, "entity_id": 1, "previous_graph_hash": "hash_250", "new_graph_hash": "hash_350",
                "reason": "PROJECT_CHANGED", "added_nodes": ["proj_a"], "removed_nodes": ["lead_3"], "changed_nodes": [],
                "added_edges": [], "removed_edges": [], "current_project_changed": True, "current_objective_changed": False, "overload_changed": True
            },

            # Entity 2 diffs (no switches)
            {
                "schema_version": "1.0.0", "run_id": "i1", "tick": 350, "entity_id": 2, "previous_graph_hash": "hash_x100", "new_graph_hash": "hash_x350",
                "reason": "DEBUG_SELECTED_ENTITY", "added_nodes": [], "removed_nodes": [], "changed_nodes": [],
                "added_edges": [], "removed_edges": [], "current_project_changed": False, "current_objective_changed": False, "overload_changed": False
            },
        ]
        with open(diffs_file, "w") as f:
            for d in diffs:
                f.write(json.dumps(d) + "\n")

        # Run complete mining logic
        patterns = CognitionPatternMiner.mine_patterns(
            str(run_dir),
            spec_data={
                "run_id": "i1",
                "seed": 7,
                "scenario": "mining_integration_test",
                "scenario_type": "sandbox"
            },
            thresholds={
                "project_churn": 3,
                "detour_loop": 2,
                "stale_blocker_age": 200,
                "lead_exhaustion_storm": 3,
                "strategic_overload": 3,
            }
        )

        # We assert that the mined patterns were correctly saved to cognition_patterns.json
        saved_patterns_file = run_dir / "cognition_patterns.json"
        assert os.path.exists(saved_patterns_file)
        with open(saved_patterns_file, "r") as f:
            saved_patterns = json.load(f)

        assert len(saved_patterns) == len(patterns)

        # Assert all 5 failure patterns were triggered!
        pattern_types = [p["pattern_type"] for p in patterns]
        assert "ProjectChurn" in pattern_types
        assert "DetourLoop" in pattern_types
        assert "StaleBlocker" in pattern_types
        assert "LeadExhaustionStorm" in pattern_types
        assert "StrategicOverload" in pattern_types

        # Verify pattern details
        for p in patterns:
            assert p["affected_runs"] == ["i1"]
            assert 1 in p["affected_entities"] or 2 in p["affected_entities"]
            assert p["affected_seeds"] == [7]
            assert p["tick_ranges"] == [[100, 350]]
            assert "confidence" in p
            assert "suspected_subsystems" in p
            assert "recommended_investigation" in p
