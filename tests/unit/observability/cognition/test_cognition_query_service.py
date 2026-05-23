from __future__ import annotations
import os
import json
import pytest
import shutil
from src.observability.reporting.history_query import HistoricalRunQueryService
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunManifest

@pytest.fixture
def temp_run_dir(tmp_path):
    run_id = "test_run_service"
    base_dir = tmp_path / "runs"
    base_dir.mkdir()
    
    # Create the run folder
    run_folder = base_dir / run_id
    run_folder.mkdir()
    
    # Write dummy manifest
    manifest_data = {
        "run_id": run_id,
        "scenario_name": "test_scenario",
        "scenario_type": "combat",
        "seed": 42,
        "engine_version": "2.0.0",
        "observability_version": "1.0.0",
        "observability_mode": "full",
        "started_at": "2026-05-23T12:00:00Z",
        "ticks_requested": 100,
        "ticks_completed": 10,
        "status": "COMPLETED",
        "artifact_schema_version": "observability_artifact_v1"
    }
    with open(run_folder / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f)
        
    # Write dummy snapshots jsonl
    snapshots = [
        {"tick": 1, "entity_id": 1, "objective": "survive", "nodes": [{"id": "node1"}], "edges": []},
        {"tick": 2, "entity_id": 1, "objective": "explore", "nodes": [{"id": "node2"}], "edges": []},
        {"tick": 3, "entity_id": 2, "objective": "gather", "nodes": [{"id": "node3"}], "edges": []}
    ]
    with open(run_folder / "cognition_graph_snapshots.jsonl", "w", encoding="utf-8") as f:
        for s in snapshots:
            f.write(json.dumps(s) + "\n")
            
    # Write dummy diffs jsonl
    diffs = [
        {"tick": 2, "entity_id": 1, "added_edges": ["edge1"]},
        {"tick": 3, "entity_id": 2, "added_edges": []}
    ]
    with open(run_folder / "cognition_graph_diffs.jsonl", "w", encoding="utf-8") as f:
        for d in diffs:
            f.write(json.dumps(d) + "\n")

    # Write dummy features jsonl
    features = [
        {"tick": 1, "entity_id": 1, "detour_delta_count": 0},
        {"tick": 2, "entity_id": 1, "detour_delta_count": 1}
    ]
    with open(run_folder / "cognition_features.jsonl", "w", encoding="utf-8") as f:
        for feat in features:
            f.write(json.dumps(feat) + "\n")
            
    # Write dummy patterns json
    patterns = [
        {"pattern_id": "P01", "entity_id": 1, "severity": "WARNING"}
    ]
    with open(run_folder / "cognition_patterns.json", "w", encoding="utf-8") as f:
        json.dump(patterns, f)
        
    repo = RunArtifactRepository(base_dir=str(base_dir))
    yield HistoricalRunQueryService(repo=repo), run_id


def test_service_get_snapshots(temp_run_dir):
    service, run_id = temp_run_dir
    
    # Test with full_graph = False (default)
    res = service.get_entity_snapshots(run_id=run_id, entity_id="1", page=1, page_size=2)
    assert res["total"] == 2
    assert len(res["snapshots"]) == 2
    # Verify raw nodes/edges stripped
    assert "nodes" not in res["snapshots"][0]
    assert "edges" not in res["snapshots"][0]
    assert res["snapshots"][0]["nodes_count"] == 1
    assert res["snapshots"][0]["edges_count"] == 0
    assert res["snapshots"][0]["objective"] == "survive"

    # Test with full_graph = True
    res_full = service.get_entity_snapshots(run_id=run_id, entity_id="1", page=1, page_size=2, full_graph=True)
    assert "nodes" in res_full["snapshots"][0]
    assert res_full["snapshots"][0]["nodes"] == [{"id": "node1"}]

    # Test pagination
    res_pag = service.get_entity_snapshots(run_id=run_id, entity_id="1", page=2, page_size=1)
    assert len(res_pag["snapshots"]) == 1
    assert res_pag["snapshots"][0]["tick"] == 2


def test_service_get_diffs(temp_run_dir):
    service, run_id = temp_run_dir
    res = service.get_entity_diffs(run_id=run_id, entity_id="1")
    assert len(res) == 1
    assert res[0]["tick"] == 2
    assert res[0]["added_edges"] == ["edge1"]


def test_service_get_features(temp_run_dir):
    service, run_id = temp_run_dir
    res = service.get_entity_features(run_id=run_id, entity_id="1")
    assert len(res) == 2
    assert res[0]["tick"] == 1
    assert res[1]["detour_delta_count"] == 1


def test_service_get_patterns(temp_run_dir):
    service, run_id = temp_run_dir
    res = service.get_run_patterns(run_id=run_id)
    assert len(res) == 1
    assert res[0]["pattern_id"] == "P01"


def test_service_security_check(temp_run_dir):
    service, run_id = temp_run_dir
    with pytest.raises(ValueError, match="Invalid identifier"):
        service.get_entity_snapshots(run_id="../../passwd", entity_id="1")
