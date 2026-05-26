from __future__ import annotations
import os
import json
import pytest
from src.observability.mining.evidence import EvidencePackBuilder
from src.observability.mining.orchestrator import AIAgentInvestigationRunner

@pytest.fixture
def mock_experiment_dir(tmp_path):
    exp_id = "test_experiment"
    exp_dir = tmp_path / exp_id
    exp_dir.mkdir()
    
    # Write engineering backlog
    backlog = {
        "backlog_items": [
            {
                "candidate_id": "anomaly_pattern_Rule123",
                "title": "Navigation Stalls",
                "priority": "P1",
                "category": "navigation",
                "scenario_name": "RESOURCE_ECONOMY_10"
            }
        ]
    }
    with open(exp_dir / "engineering_backlog.json", "w", encoding="utf-8") as f:
        json.dump(backlog, f)
        
    # Write dataset anomalies
    dataset_dir = exp_dir / "dataset"
    dataset_dir.mkdir()
    anomalies = [
        {
            "run_id": "run_a",
            "seed": 42,
            "rule_id": "Rule123",
            "entity_id": 1,
            "tick": 10
        }
    ]
    with open(dataset_dir / "anomalies.json", "w", encoding="utf-8") as f:
        json.dump(anomalies, f)
        
    # Create representative runs folder
    runs_dir = exp_dir / "runs"
    runs_dir.mkdir()
    
    run_folder = runs_dir / "run_a"
    run_folder.mkdir()
    
    # Write dummy snapshots
    snapshots = [
        {
            "tick": 5,
            "entity_id": 1,
            "current_project_id": "project_1",
            "current_objective_id": "obj_1",
            "overload_source": None,
            "nodes": [
                {"id": "node1", "kind": "blocker"},
                {"id": "node2", "kind": "lead"}
            ]
        },
        {
            "tick": 12,
            "entity_id": 1,
            "current_project_id": "project_2",
            "current_objective_id": "obj_2",
            "overload_source": "congestion",
            "nodes": [
                {"id": "node3", "kind": "blocker"},
                {"id": "node4", "kind": "blocker"}
            ]
        }
    ]
    with open(run_folder / "cognition_graph_snapshots.jsonl", "w", encoding="utf-8") as f:
        for s in snapshots:
            f.write(json.dumps(s) + "\n")
            
    # Write dummy diffs
    diffs = [
        {
            "tick": 12,
            "entity_id": 1,
            "current_project_changed": True,
            "detour_delta_count": 1,
            "added_nodes": [{"id": "node3"}],
            "removed_nodes": []
        }
    ]
    with open(run_folder / "cognition_graph_diffs.jsonl", "w", encoding="utf-8") as f:
        for d in diffs:
            f.write(json.dumps(d) + "\n")
            
    # Write dummy features
    features = [
        {"tick": 5, "entity_id": 1, "detour_delta_count": 0},
        {"tick": 12, "entity_id": 1, "detour_delta_count": 1}
    ]
    with open(run_folder / "cognition_features.jsonl", "w", encoding="utf-8") as f:
        for feat in features:
            f.write(json.dumps(feat) + "\n")
            
    # Write dummy patterns
    patterns = [
        {"pattern_id": "P01", "entity_id": 1, "severity": "WARNING"}
    ]
    with open(run_folder / "cognition_patterns.json", "w", encoding="utf-8") as f:
        json.dump(patterns, f)
        
    yield str(tmp_path), exp_id, "anomaly_pattern_Rule123"


def test_build_evidence_pack_with_cognition(mock_experiment_dir):
    base_dir, exp_id, candidate_id = mock_experiment_dir
    
    pack = EvidencePackBuilder.build_evidence_pack(
        experiment_id=exp_id,
        candidate_id=candidate_id,
        base_dir=base_dir
    )
    
    # Assert manifest was enriched
    assert "cognition_summary" in pack
    cog = pack["cognition_summary"]
    
    assert 1 in cog["top_affected_entities"]
    assert cog["unresolved_blockers_count"] == 2  # tick 12 is latest for entity 1, which has 2 blockers
    assert cog["known_leads_count"] == 0         # tick 12 has 0 leads
    assert cog["project_switch_count"] == 1
    assert cog["detour_count"] == 1
    assert cog["overload_count"] == 1
    assert cog["graph_diff_summary"] == {
        "added_nodes_count": 1,
        "removed_nodes_count": 0
    }
    
    # Verify exact files are outputted to the evidence directory
    evidence_dir = pack["evidence_directory"]
    assert os.path.exists(os.path.join(evidence_dir, "cognition_snapshot_before.json"))
    assert os.path.exists(os.path.join(evidence_dir, "cognition_snapshot_after.json"))
    assert os.path.exists(os.path.join(evidence_dir, "cognition_diff.json"))
    assert os.path.exists(os.path.join(evidence_dir, "cognition_feature_summary.json"))
    assert os.path.exists(os.path.join(evidence_dir, "cognition_pattern_summary.json"))
    assert os.path.exists(os.path.join(evidence_dir, "affected_entities_cognition_summary.json"))
    
    # Verify the contents of before snapshot (tick 5 <= trigger 10)
    with open(os.path.join(evidence_dir, "cognition_snapshot_before.json"), "r") as f:
        before = json.load(f)
        assert before["tick"] == 5
        
    # Verify the contents of after snapshot (tick 12 > trigger 10)
    with open(os.path.join(evidence_dir, "cognition_snapshot_after.json"), "r") as f:
        after = json.load(f)
        assert after["tick"] == 12

    # Now verify AIAgentInvestigationRunner uses the anti-misdirection phrasing if cognition_summary is present
    finding = AIAgentInvestigationRunner.run_investigation(
        experiment_id=exp_id,
        candidate_id=candidate_id,
        base_dir=base_dir
    )
    
    assert "Cognition analysis shows strategic state is likely related to unresolved blocker" in finding["agent_notes"]
    assert " definitive root cause" in finding["agent_notes"]
