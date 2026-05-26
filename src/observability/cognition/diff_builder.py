"""
Cognition Graph Diff Builder for computing differences between cognition snapshots.
"""
from typing import Dict, Any, List, Set, Tuple
from src.observability.cognition.schema import build_diff_record


class CognitionGraphDiffBuilder:
    """
    Computes deterministic deltas between subsequent strategic cognition snapshots
    for behavior mining and diagnostic tracking.
    """

    @staticmethod
    def compute_diff(
        run_id: str,
        tick: int,
        entity_id: int,
        reason: str,
        prev_snapshot: Dict[str, Any] | None,
        curr_snapshot: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares prev_snapshot and curr_snapshot deterministically.
        Returns a validated diff record.
        """
        # If prev_snapshot is None, set up empty baseline values
        if prev_snapshot is None:
            prev_nodes_dict: Dict[str, Dict[str, Any]] = {}
            prev_edges_set: Set[Tuple[str, str, str]] = set()
            prev_project = None
            prev_objective = None
            prev_overload = None
            prev_hash = ""
        else:
            prev_hash = prev_snapshot.get("graph_hash", "")
            prev_project = prev_snapshot.get("current_project_id")
            prev_objective = prev_snapshot.get("current_objective_id")
            prev_overload = prev_snapshot.get("overload_source")

            prev_graph = prev_snapshot.get("graph", {})
            prev_nodes_list = prev_graph.get("nodes", [])
            prev_edges_list = prev_graph.get("edges", [])

            prev_nodes_dict = {node.get("node_id", ""): node for node in prev_nodes_list if node.get("node_id")}
            prev_edges_set = {
                (edge.get("source_id", ""), edge.get("target_id", ""), edge.get("kind", ""))
                for edge in prev_edges_list
                if edge.get("source_id") and edge.get("target_id")
            }

        new_hash = curr_snapshot.get("graph_hash", "")
        new_project = curr_snapshot.get("current_project_id")
        new_objective = curr_snapshot.get("current_objective_id")
        new_overload = curr_snapshot.get("overload_source")

        curr_graph = curr_snapshot.get("graph", {})
        curr_nodes_list = curr_graph.get("nodes", [])
        curr_edges_list = curr_graph.get("edges", [])

        curr_nodes_dict = {node.get("node_id", ""): node for node in curr_nodes_list if node.get("node_id")}
        curr_edges_set = {
            (edge.get("source_id", ""), edge.get("target_id", ""), edge.get("kind", ""))
            for edge in curr_edges_list
            if edge.get("source_id") and edge.get("target_id")
        }

        # Calculate added, removed, changed nodes
        added_nodes: List[str] = []
        removed_nodes: List[str] = []
        changed_nodes: List[str] = []

        # Track kind deltas for blockers, leads, concerns, hypotheses, projects
        blocker_delta = 0
        lead_delta = 0
        concern_delta = 0
        hypothesis_delta = 0
        project_delta = 0

        # Added nodes
        for node_id, node in curr_nodes_dict.items():
            if node_id not in prev_nodes_dict:
                added_nodes.append(node_id)
                kind = node.get("kind", "")
                if kind == "blocker":
                    blocker_delta += 1
                elif kind == "lead":
                    lead_delta += 1
                elif kind == "concern":
                    concern_delta += 1
                elif kind == "hypothesis":
                    hypothesis_delta += 1
                elif kind == "project":
                    project_delta += 1

        # Removed nodes
        for node_id, node in prev_nodes_dict.items():
            if node_id not in curr_nodes_dict:
                removed_nodes.append(node_id)
                kind = node.get("kind", "")
                if kind == "blocker":
                    blocker_delta += 1
                elif kind == "lead":
                    lead_delta += 1
                elif kind == "concern":
                    concern_delta += 1
                elif kind == "hypothesis":
                    hypothesis_delta += 1
                elif kind == "project":
                    project_delta += 1

        # Changed nodes (present in both but content differs)
        for node_id, curr_node in curr_nodes_dict.items():
            if node_id in prev_nodes_dict:
                prev_node = prev_nodes_dict[node_id]
                # Compare critical attributes
                if (
                    curr_node.get("kind") != prev_node.get("kind") or
                    curr_node.get("label") != prev_node.get("label") or
                    curr_node.get("metadata") != prev_node.get("metadata")
                ):
                    changed_nodes.append(node_id)
                    kind = curr_node.get("kind", "")
                    # Changed blocker / lead / concern etc counts as dynamic shift
                    if kind == "blocker":
                        blocker_delta += 1
                    elif kind == "lead":
                        lead_delta += 1
                    elif kind == "concern":
                        concern_delta += 1
                    elif kind == "hypothesis":
                        hypothesis_delta += 1
                    elif kind == "project":
                        project_delta += 1

        # Calculate added and removed edges
        added_edges_tuples = curr_edges_set - prev_edges_set
        removed_edges_tuples = prev_edges_set - curr_edges_set

        added_edges = [
            {"source_id": s, "target_id": t, "kind": k}
            for s, t, k in added_edges_tuples
        ]
        removed_edges = [
            {"source_id": s, "target_id": t, "kind": k}
            for s, t, k in removed_edges_tuples
        ]

        # Metadata changes
        current_project_changed = (prev_project != new_project)
        current_objective_changed = (prev_objective != new_objective)
        overload_changed = (prev_overload != new_overload)

        # Build stable sorted diff record
        return build_diff_record(
            run_id=run_id,
            tick=tick,
            entity_id=entity_id,
            previous_graph_hash=prev_hash,
            new_graph_hash=new_hash,
            reason=reason,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            changed_nodes=changed_nodes,
            added_edges=added_edges,
            removed_edges=removed_edges,
            current_project_changed=current_project_changed,
            current_objective_changed=current_objective_changed,
            blocker_delta_count=blocker_delta,
            lead_delta_count=lead_delta,
            concern_delta_count=concern_delta,
            hypothesis_delta_count=hypothesis_delta,
            project_delta_count=project_delta,
            overload_changed=overload_changed,
        )
