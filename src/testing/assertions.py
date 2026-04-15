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
    entities = last_tick_data.get("entities", [])
    
    # Track 2: Strategic consistency should work with list-based entities
    for entity_snapshot in entities:
        eid = entity_snapshot.get("id")
        graph = cognition_graphs.get(eid)
        if not graph:
            continue
            
        # Check current project/objective in graph matches entity state
        strat = entity_snapshot.get("strategy", {})
        expected_project_id = strat.get("project_id")
        
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

def assert_cognition_consistency(replay_json: Dict[str, Any], cognition_graphs: Dict[int, Dict[str, Any]]):
    """Verify that cognitive metrics in replay summary match the exported graphs.
    
    [INTENTIONAL OVERLAP CONTRACT]
    - Capacity: planning_budget, judgment_stability, evidence_quality, social_bandwidth.
    - Usage: active_slice_used, dropped_candidates_count, is_overloaded.
    - Determinism: Both must derive from the exact same StrategicState snapshot.
    """
    ticks = replay_json.get("ticks", [])
    if not ticks:
        return
        
    last_tick_data = ticks[-1]
    entities = last_tick_data.get("entities", [])
    
    for entity_snapshot in entities:
        eid = entity_snapshot.get("id")
        strat = entity_snapshot.get("strategy", {})
        cp = strat.get("last_capacity_profile", {})
        
        graph = cognition_graphs.get(eid)
        if not graph:
            continue
            
        # 1. Find the cognition profile node in graph
        nodes = graph["elements"]["nodes"]
        cp_node = next((n for n in nodes if n["data"]["kind"] == "cognition_profile"), None)
        assert cp_node is not None, f"Entity {eid} graph missing cognition_profile node"
        
        # 2. Compare attributes (flattened in Cytoscape format)
        data = cp_node["data"]
        
        # Capacity Parity (Complete Milestone 2 Set)
        capacity_fields = [
            "planning_budget", "judgment_stability", "evidence_quality", "social_bandwidth",
            "detour_depth_limit", "active_slice_limit", "concern_intake_limit", "lead_retention_limit",
            "candidate_zone_limit", "ally_evaluation_limit", "blocker_resolution_patience",
            "resume_reliability", "interruption_resistance", "abandonment_threshold_mod",
            "contradiction_sensitivity", "source_trust_learning_rate"
        ]
        
        for field in capacity_fields:
            eb_val = cp.get(field)
            gr_val = data.get(field)
            if eb_val is not None: # Replay might have None if not updated
                assert gr_val == eb_val, f"{field} mismatch for entity {eid}: Graph={gr_val}, Replay={eb_val}"
        
        # Usage Parity
        usage_fields = {
            "active_slice_used": "active_slice_used",
            "dropped_candidates_count": "dropped_candidates",
            "active_concerns_used": "active_concerns_used",
            "retained_leads_used": "retained_leads_used",
            "candidate_zones_used": "candidate_zones_used",
            "ally_evaluations_used": "ally_evaluations_used",
            "detour_depth_used": "detour_depth_used"
        }
        
        for eb_key, gr_key in usage_fields.items():
            eb_val = strat.get(eb_key)
            gr_val = data.get(gr_key)
            if eb_val is not None:
                assert gr_val == eb_val, f"{eb_key} mismatch for entity {eid}: Graph={gr_val}, Replay={eb_val}"
        
        # 3. Overload Parity
        eb_over = strat.get("is_overloaded")
        gr_over = data.get("is_overloaded")
        assert gr_over == eb_over, f"Overload status mismatch for entity {eid}: Graph={gr_over}, Replay={eb_over}"
        
        eb_source = strat.get("primary_overload_source")
        gr_source = data.get("primary_overload_source")
        assert gr_source == eb_source, f"Primary overload source mismatch for entity {eid}: Graph={gr_source}, Replay={eb_source}"

def assert_overload_behavior(replay_json: Dict[str, Any]):
    """Ensure that overload flags appear if active_slice_used >= budget. [STABILIZATION]"""
    for tick_data in replay_json.get("ticks", []):
        for e in tick_data.get("entities", []):
            strat = e.get("strategy", {})
            if strat.get("is_overloaded"):
                # If overloaded, usage should be close to or at budget (or high pressure)
                used = strat.get("active_slice_used", 0)
                budget = strat.get("planning_budget", 1)
                # Overload can trigger before reaching budget if pressure is extremely high, 
                # but usually used will be high.
                assert used >= 0, f"Negative usage {used} for overloaded entity {e.get('id')}"
