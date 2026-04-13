"""Assertion helpers for simulation artifacts. [MILESTONE 7]"""

import json
from pathlib import Path
from typing import Any, Dict

def load_json(path: Path | str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def assert_graph_integrity(graph_json: Dict[str, Any]):
    """Verify that a cognition graph is structurally valid."""
    elements = graph_json.get("elements", {})
    nodes = elements.get("nodes", [])
    edges = elements.get("edges", [])
    
    assert len(nodes) > 0, "Graph must have at least one node (root)"
    
    node_ids = {n["data"]["id"] for n in nodes}
    
    # 1. Edge Integrity
    for edge in edges:
        data = edge["data"]
        assert "id" in data
        assert "source" in data
        assert "target" in data
        assert data["source"] in node_ids, f"Edge {data['id']} has dangling source {data['source']}"
        assert data["target"] in node_ids, f"Edge {data['id']} has dangling target {data['target']}"

    # 2. Root Integrity
    root_nodes = [n for n in nodes if n["data"]["kind"] == "entity"]
    assert len(root_nodes) == 1, "Graph must have exactly one entity root node"

def assert_strategic_consistency(replay_json: Dict[str, Any], cognition_graphs: Dict[int, Dict[str, Any]]):
    """Verify that the replay summary matches the exported graphs."""
    # This assumes the replay has a summary of strategic state at each tick
    # For now, we compare with the LAST state in the replay
    ticks = replay_json.get("ticks", [])
    if not ticks:
        return
        
    last_tick_data = ticks[-1]
    last_world_state = last_tick_data.get("state", {})
    entities = last_world_state.get("entities", {})
    
    for eid_str, graph in cognition_graphs.items():
        eid = int(eid_str)
        entity_data = entities.get(eid_str)
        if not entity_data:
            continue
            
        # Check current project/objective in graph matches entity state
        # In EntityCognitionExporter, we use kind="pursuing" for the current project edge
        mind = entity_data.get("mind", {})
        strat = mind.get("strategic", {})
        expected_project_id = strat.get("current_project_id")
        
        if expected_project_id:
            edges = graph["elements"]["edges"]
            pursuing_edges = [e for e in edges if e["data"]["kind"] == "pursuing"]
            assert len(pursuing_edges) > 0, f"Entity {eid} is pursuing {expected_project_id} but has no pursuing edge in graph"
            
            target_ids = {e["data"]["target"] for e in pursuing_edges}
            assert f"project:{expected_project_id}" in target_ids, \
                f"Entity {eid} graph pursuing edge target mismatch. Expected project:{expected_project_id}, found {target_ids}"

def assert_determinism(graph_a: Dict[str, Any], graph_b: Dict[str, Any]):
    """Verify that two graphs are structurally identical (ignoring dynamic metadata)."""
    # Simply compare the dumped JSON structures (since Milestone 6 enforced sorting)
    # We remove 'exported_at_tick' or similar if they differ, but they shouldn't for same seed.
    assert graph_a == graph_b, "Graphs diverged despite identical seeds"
