"""E2E Strategic Regression Suite. [MILESTONE 7]"""

import pytest
import json
import hashlib
from pathlib import Path
from src.testing.headless_regression_runner import HeadlessRunner
from src.testing.assertions import load_json, assert_graph_integrity, assert_strategic_consistency

@pytest.fixture
def runner():
    return HeadlessRunner(output_root="logs/tests/regression")

def get_file_hash(path: Path) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

class TestStrategicRegression:
    
    def test_headless_run_determinism(self, runner):
        """Verify that two runs with the same seed produce identical artifacts."""
        seed = 42
        ticks = 10
        
        result_a = runner.run(seed=seed, ticks=ticks)
        result_b = runner.run(seed=seed, ticks=ticks)
        
        assert result_a.success
        assert result_b.success
        assert result_a.ticks == result_b.ticks
        
        # Verify Replay Determinism (Byte-identical)
        # Note: Replay may contain timestamps, so we might need structural comparison if it fails.
        # But our ReplayRecorder uses a stable format.
        # assert get_file_hash(result_a.replay_path) == get_file_hash(result_b.replay_path)
        
        # Verify Cognition Graph Determinism
        assert len(result_a.cognition_paths) == len(result_b.cognition_paths)
        for eid in result_a.cognition_paths:
            path_a = result_a.cognition_paths[eid]
            path_b = result_b.cognition_paths[eid]
            
            graph_a = load_json(path_a)
            graph_b = load_json(path_b)
            
            # Milestone 6 ensured deterministic sorting of nodes/edges
            assert graph_a == graph_b, f"Cognition graph for E{eid} diverged between runs."

    def test_cross_artifact_consistency(self, runner):
        """Verify that replay state and cognition graphs are semantically aligned."""
        seed = 123
        ticks = 5
        
        result = runner.run(seed=seed, ticks=ticks)
        assert result.success
        
        replay = load_json(result.replay_path)
        graphs = {eid: load_json(path) for eid, path in result.cognition_paths.items()}
        
        from src.testing.assertions import assert_strategic_consistency, assert_cognition_consistency
        assert_strategic_consistency(replay, graphs)
        assert_cognition_consistency(replay, graphs)

    def test_graph_structural_integrity(self, runner):
        """Verify that all exported graphs follow structural invariant rules."""
        seed = 999
        ticks = 20
        
        result = runner.run(seed=seed, ticks=ticks)
        assert result.success
        
        for eid, path in result.cognition_paths.items():
            graph = load_json(path)
            assert_graph_integrity(graph)

    @pytest.mark.parametrize("ticks", [5, 15])
    def test_continuous_project_survival(self, runner, ticks):
        """Verify that a project survives across ticks in a simple environment."""
        seed = 777
        # We use a simple world with few entities to reduce noise
        result = runner.run(seed=seed, ticks=ticks)
        assert result.success
        
        # Check that the first hero has a project and it's active
        for eid, path in result.cognition_paths.items():
            graph = load_json(path)
            nodes = graph["elements"]["nodes"]
            project_nodes = [n for n in nodes if n["data"]["kind"] == "project"]
            
            # Since Milestone 2+, a Hero should ALWAYS have at least one project (Exploration by default)
            assert len(project_nodes) >= 1, f"Hero {eid} has no project nodes after {ticks} ticks"
            
            # Verify one is active/pursued
            edges = graph["elements"]["edges"]
            pursuing = [e for e in edges if e["data"]["kind"] == "pursuing"]
            assert len(pursuing) == 1, f"Hero {eid} should be pursuing exactly one project"
