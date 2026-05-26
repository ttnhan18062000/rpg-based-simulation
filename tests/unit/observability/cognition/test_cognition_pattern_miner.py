"""
Unit tests for the CognitionPatternMiner.
"""
import os
import json
import pytest
from pathlib import Path

from src.observability.cognition.pattern_miner import CognitionPatternMiner


class TestCognitionPatternMiner:
    """Milestone 63: Verify strategic behavioral pattern miner rules."""

    def test_project_churn_detected(self, tmp_path: Path):
        """Assert ProjectChurn is matching when project shifts are high without resolution."""
        snapshots_file = tmp_path / "cognition_graph_snapshots.jsonl"
        diffs_file = tmp_path / "cognition_graph_diffs.jsonl"

        # Mock snapshots: 4 snaps switching back and forth
        snaps = [
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 100, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_a"},
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 110, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_b"},
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 120, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_c"},
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 130, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_a"},
        ]
        with open(snapshots_file, "w") as f:
            for s in snaps:
                f.write(json.dumps(s) + "\n")

        # Mock diffs: 3 project changes
        diffs = [
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 110, "entity_id": 42, "current_project_changed": True, "added_nodes": ["proj_b"], "removed_nodes": []},
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 120, "entity_id": 42, "current_project_changed": True, "added_nodes": ["proj_c"], "removed_nodes": []},
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 130, "entity_id": 42, "current_project_changed": True, "added_nodes": ["proj_a"], "removed_nodes": []},
        ]
        with open(diffs_file, "w") as f:
            for d in diffs:
                f.write(json.dumps(d) + "\n")

        # Mine patterns
        patterns = CognitionPatternMiner.mine_patterns(
            str(tmp_path),
            spec_data={"run_id": "r1", "seed": 1},
            thresholds={"project_churn": 3}
        )

        churn_patterns = [p for p in patterns if p["pattern_type"] == "ProjectChurn"]
        assert len(churn_patterns) == 1
        assert churn_patterns[0]["severity"] in ("WARNING", "CRITICAL")
        assert churn_patterns[0]["affected_runs"] == ["r1"]
        assert churn_patterns[0]["affected_entities"] == [42]

    def test_detour_loop_detected(self, tmp_path: Path):
        """Assert DetourLoop is matching when multiple detour projects are spawned on a active blocker."""
        snapshots_file = tmp_path / "cognition_graph_snapshots.jsonl"
        diffs_file = tmp_path / "cognition_graph_diffs.jsonl"

        snaps = [
            # Tick 100: starts with blocker
            {
                "schema_version": "1.0.0", "run_id": "r1", "tick": 100, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_a",
                "graph": {"nodes": [{"node_id": "blocker_1", "kind": "blocker", "label": "Locked door"}]}
            },
            # Tick 120: detour_1 created
            {
                "schema_version": "1.0.0", "run_id": "r1", "tick": 120, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_detour_1",
                "graph": {"nodes": [{"node_id": "blocker_1", "kind": "blocker", "label": "Locked door"}, {"node_id": "proj_detour_1", "kind": "project", "label": "Detour 1"}]}
            },
            # Tick 140: detour_2 created
            {
                "schema_version": "1.0.0", "run_id": "r1", "tick": 140, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_detour_2",
                "graph": {"nodes": [{"node_id": "blocker_1", "kind": "blocker", "label": "Locked door"}, {"node_id": "proj_detour_2", "kind": "project", "label": "Detour 2"}]}
            },
        ]
        with open(snapshots_file, "w") as f:
            for s in snaps:
                f.write(json.dumps(s) + "\n")

        diffs = [
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 120, "entity_id": 42, "current_project_changed": True, "added_nodes": ["proj_detour_1"], "removed_nodes": []},
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 140, "entity_id": 42, "current_project_changed": True, "added_nodes": ["proj_detour_2"], "removed_nodes": []},
        ]
        with open(diffs_file, "w") as f:
            for d in diffs:
                f.write(json.dumps(d) + "\n")

        patterns = CognitionPatternMiner.mine_patterns(
            str(tmp_path),
            spec_data={"run_id": "r1", "seed": 1},
            thresholds={"detour_loop": 2}
        )

        loop_patterns = [p for p in patterns if p["pattern_type"] == "DetourLoop"]
        assert len(loop_patterns) == 1
        assert loop_patterns[0]["severity"] == "CRITICAL"
        assert loop_patterns[0]["evidence"]["detour_created_count"] == 2
        assert "strategy_detour_planner" in loop_patterns[0]["suspected_subsystems"]

    def test_negative_guards_normal_progression(self, tmp_path: Path):
        """Verify normal project shifts and blockers resolved do not trigger failure patterns."""
        snapshots_file = tmp_path / "cognition_graph_snapshots.jsonl"
        diffs_file = tmp_path / "cognition_graph_diffs.jsonl"

        snaps = [
            # Starts with proj_a and blocker_1
            {
                "schema_version": "1.0.0", "run_id": "r1", "tick": 100, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_a",
                "graph": {"nodes": [{"node_id": "blocker_1", "kind": "blocker", "label": "Blocker"}]}
            },
            # Shifts to detour project
            {
                "schema_version": "1.0.0", "run_id": "r1", "tick": 150, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_detour_1",
                "graph": {"nodes": [{"node_id": "blocker_1", "kind": "blocker", "label": "Blocker"}, {"node_id": "proj_detour_1", "kind": "project", "label": "Detour"}]}
            },
            # Blocker resolved, return to main proj_a
            {
                "schema_version": "1.0.0", "run_id": "r1", "tick": 200, "entity_id": 42, "reason": "PROJECT_CHANGED", "current_project_id": "proj_a",
                "graph": {"nodes": [{"node_id": "proj_a", "kind": "project", "label": "Project A"}]}
            },
        ]
        with open(snapshots_file, "w") as f:
            for s in snaps:
                f.write(json.dumps(s) + "\n")

        diffs = [
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 150, "entity_id": 42, "current_project_changed": True, "added_nodes": ["proj_detour_1"], "removed_nodes": []},
            {"schema_version": "1.0.0", "run_id": "r1", "tick": 200, "entity_id": 42, "current_project_changed": True, "added_nodes": ["proj_a"], "removed_nodes": ["blocker_1", "proj_detour_1"]},
        ]
        with open(diffs_file, "w") as f:
            for d in diffs:
                f.write(json.dumps(d) + "\n")

        patterns = CognitionPatternMiner.mine_patterns(
            str(tmp_path),
            spec_data={"run_id": "r1", "seed": 1},
            thresholds={"project_churn": 3, "detour_loop": 2}
        )

        # No patterns should match because thresholds are not met and blocker was resolved
        assert len(patterns) == 0
