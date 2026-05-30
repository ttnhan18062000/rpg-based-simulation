"""
Cognition Graph Artifact Schema contracts and serialization.
"""
from __future__ import annotations
import json
import hashlib
from typing import Dict, Any, List

# Stable schema version constant
SCHEMA_VERSION = "1.0.0"

# Set of valid snapshot/diff trigger reasons
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


def compute_stable_graph_hash(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
    """
    Computes a stable, deterministic SHA-256 hash for nodes and edges.
    Nodes and edges are sorted by stable keys to guarantee consistent signatures.
    """
    # Deterministically sort and shape nodes
    sorted_nodes = []
    for node in sorted(nodes, key=lambda x: x.get("node_id", "")):
        sorted_nodes.append({
            "node_id": node.get("node_id", ""),
            "kind": node.get("kind", ""),
            "label": node.get("label", ""),
            "metadata": dict(sorted(node.get("metadata", {}).items()))
        })

    # Deterministically sort and shape edges
    sorted_edges = []
    for edge in sorted(edges, key=lambda x: (x.get("source_id", ""), x.get("target_id", ""), x.get("kind", ""))):
        sorted_edges.append({
            "source_id": edge.get("source_id", ""),
            "target_id": edge.get("target_id", ""),
            "kind": edge.get("kind", "")
        })

    graph_dict = {
        "nodes": sorted_nodes,
        "edges": sorted_edges
    }
    serialized = json.dumps(graph_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def build_snapshot_record(
    run_id: str,
    tick: int,
    entity_id: int,
    reason: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    trigger_event_id: str | None = None,
    trigger_anomaly_id: str | None = None,
    current_project_id: str | None = None,
    current_objective_id: str | None = None,
    overload_source: str | None = None,
    source_goal_score: float | None = None,
    resulting_action: str | None = None,
    target_pos: list[float] | None = None,
) -> Dict[str, Any]:
    """
    Constructs a compliant compact cognition snapshot record.
    Ensures metadata limits are enforced to prevent massive bloated artifacts.
    """
    if reason not in VALID_REASONS:
        raise ValueError(f"Unknown trigger reason: {reason}")

    # Build and truncate node metadata if necessary to protect against bloat
    clean_nodes = []
    for node in nodes:
        raw_meta = node.get("metadata", {})
        # Remove any huge keys or truncate to keep it compact
        truncated_meta = {}
        for k, v in raw_meta.items():
            str_v = str(v)
            if len(str_v) > 200:
                truncated_meta[k] = str_v[:197] + "..."
            else:
                truncated_meta[k] = v

        clean_node = {
            "node_id": node.get("node_id", ""),
            "kind": node.get("kind", ""),
            "label": node.get("label", ""),
            "metadata": truncated_meta
        }
        # Invariant check: metadata size limit
        if len(json.dumps(truncated_meta)) > 1000:
            clean_node["metadata"] = {"error": "metadata size exceeded"}
        clean_nodes.append(clean_node)

    clean_edges = []
    for edge in edges:
        clean_edges.append({
            "source_id": edge.get("source_id", ""),
            "target_id": edge.get("target_id", ""),
            "kind": edge.get("kind", "")
        })

    graph_hash = compute_stable_graph_hash(clean_nodes, clean_edges)

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "tick": tick,
        "entity_id": entity_id,
        "reason": reason,
        "trigger_event_id": trigger_event_id,
        "trigger_anomaly_id": trigger_anomaly_id,
        "current_project_id": current_project_id,
        "current_objective_id": current_objective_id,
        "overload_source": overload_source,
        "source_goal_score": source_goal_score,
        "resulting_action": resulting_action,
        "target_pos": target_pos,
        "node_count": len(clean_nodes),
        "edge_count": len(clean_edges),
        "graph_hash": graph_hash,
        "graph": {
            "nodes": clean_nodes,
            "edges": clean_edges
        }
    }


def build_diff_record(
    run_id: str,
    tick: int,
    entity_id: int,
    previous_graph_hash: str,
    new_graph_hash: str,
    reason: str,
    added_nodes: List[str],
    removed_nodes: List[str],
    changed_nodes: List[str],
    added_edges: List[Dict[str, Any]],
    removed_edges: List[Dict[str, Any]],
    current_project_changed: bool = False,
    current_objective_changed: bool = False,
    blocker_delta_count: int = 0,
    lead_delta_count: int = 0,
    concern_delta_count: int = 0,
    hypothesis_delta_count: int = 0,
    project_delta_count: int = 0,
    overload_changed: bool = False,
) -> Dict[str, Any]:
    """
    Constructs a compliant compact cognition graph diff record.
    """
    if reason not in VALID_REASONS:
        raise ValueError(f"Unknown trigger reason: {reason}")

    # Deterministically sort added/removed/changed nodes
    sorted_added_nodes = sorted(added_nodes)
    sorted_removed_nodes = sorted(removed_nodes)
    sorted_changed_nodes = sorted(changed_nodes)

    # Deterministically sort added/removed edges
    sorted_added_edges = []
    for edge in sorted(added_edges, key=lambda x: (x.get("source_id", ""), x.get("target_id", ""), x.get("kind", ""))):
        sorted_added_edges.append({
            "source_id": edge.get("source_id", ""),
            "target_id": edge.get("target_id", ""),
            "kind": edge.get("kind", "")
        })

    sorted_removed_edges = []
    for edge in sorted(removed_edges, key=lambda x: (x.get("source_id", ""), x.get("target_id", ""), x.get("kind", ""))):
        sorted_removed_edges.append({
            "source_id": edge.get("source_id", ""),
            "target_id": edge.get("target_id", ""),
            "kind": edge.get("kind", "")
        })

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "tick": tick,
        "entity_id": entity_id,
        "previous_graph_hash": previous_graph_hash,
        "new_graph_hash": new_graph_hash,
        "reason": reason,
        "added_nodes": sorted_added_nodes,
        "removed_nodes": sorted_removed_nodes,
        "changed_nodes": sorted_changed_nodes,
        "added_edges": sorted_added_edges,
        "removed_edges": sorted_removed_edges,
        "current_project_changed": current_project_changed,
        "current_objective_changed": current_objective_changed,
        "blocker_delta_count": blocker_delta_count,
        "lead_delta_count": lead_delta_count,
        "concern_delta_count": concern_delta_count,
        "hypothesis_delta_count": hypothesis_delta_count,
        "project_delta_count": project_delta_count,
        "overload_changed": overload_changed,
    }

