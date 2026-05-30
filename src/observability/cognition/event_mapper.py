"""
Translates strategic cognition graph diffs into concrete SimulationEvents.
"""
from typing import Dict, Any, List, Optional
from src.observability.events import SimulationEvent
from src.observability.cognition.events import (
    StrategicProjectChanged,
    StrategicObjectiveChanged,
    StrategicBlockerAdded,
    StrategicBlockerResolved,
    StrategicLeadExhausted,
    StrategicConcernRaised,
    StrategicOverloadDetected,
    StrategicDetourCreated,
    StrategicDetourLoopSuspected,
)


class CognitionEventMapper:
    """
    Translates cognition graph diffs and snapshot state into high-salience SimulationEvents.
    Maintains a deterministic history of detour counts to identify potential infinite loop anomalies.
    """

    def __init__(self, detour_loop_threshold: int = 2) -> None:
        self.detour_loop_threshold = detour_loop_threshold
        # Tracks blocker_id -> count of detour projects created for it
        self.blocker_detour_counts: Dict[str, int] = {}

    def map_diff_to_events(
        self,
        diff: Dict[str, Any],
        prev_snapshot: Dict[str, Any] | None,
        curr_snapshot: Dict[str, Any]
    ) -> List[SimulationEvent]:
        """
        Processes a diff and the active snapshots to produce an ordered list of SimulationEvents.
        """
        events: List[SimulationEvent] = []

        run_id = curr_snapshot.get("run_id")
        tick = curr_snapshot.get("tick", 0)
        entity_id = curr_snapshot.get("entity_id")

        # Prep dictionaries for fast node lookups
        curr_nodes = {
            node["node_id"]: node
            for node in curr_snapshot.get("graph", {}).get("nodes", [])
        }
        prev_nodes = {}
        if prev_snapshot:
            prev_nodes = {
                node["node_id"]: node
                for node in prev_snapshot.get("graph", {}).get("nodes", [])
            }

        # 1. Project changed
        if diff.get("current_project_changed"):
            prev_proj = prev_snapshot.get("current_project_id") if prev_snapshot else None
            curr_proj = curr_snapshot.get("current_project_id")
            events.append(
                StrategicProjectChanged(
                    run_id=run_id,
                    tick=tick,
                    entity_id=entity_id,
                    previous_project_id=prev_proj,
                    new_project_id=curr_proj,
                    reason=curr_snapshot.get("reason", ""),
                    source_goal_score=curr_snapshot.get("source_goal_score"),
                    resulting_action=curr_snapshot.get("resulting_action"),
                    target_pos=curr_snapshot.get("target_pos"),
                )
            )

        # 2. Objective changed
        if diff.get("current_objective_changed"):
            prev_obj = prev_snapshot.get("current_objective_id") if prev_snapshot else None
            curr_obj = curr_snapshot.get("current_objective_id")
            events.append(
                StrategicObjectiveChanged(
                    run_id=run_id,
                    tick=tick,
                    entity_id=entity_id,
                    previous_objective_id=prev_obj,
                    new_objective_id=curr_obj,
                )
            )

        # 3. Blocker added
        for node_id in diff.get("added_nodes", []):
            node = curr_nodes.get(node_id)
            if node and node.get("kind") == "blocker":
                events.append(
                    StrategicBlockerAdded(
                        run_id=run_id,
                        tick=tick,
                        entity_id=entity_id,
                        blocker_id=node_id,
                        blocker_kind=node.get("metadata", {}).get("kind", "unknown"),
                        blocker_label=node.get("label", ""),
                    )
                )

        # 4. Blocker resolved
        for node_id in diff.get("removed_nodes", []):
            node = prev_nodes.get(node_id)
            if node and node.get("kind") == "blocker":
                events.append(
                    StrategicBlockerResolved(
                        run_id=run_id,
                        tick=tick,
                        entity_id=entity_id,
                        blocker_id=node_id,
                        blocker_label=node.get("label", ""),
                    )
                )

        # 5. Lead exhausted
        for node_id in diff.get("removed_nodes", []):
            node = prev_nodes.get(node_id)
            if node and node.get("kind") == "lead":
                events.append(
                    StrategicLeadExhausted(
                        run_id=run_id,
                        tick=tick,
                        entity_id=entity_id,
                        lead_id=node_id,
                        lead_label=node.get("label", ""),
                    )
                )

        # 6. Concern raised
        for node_id in diff.get("added_nodes", []):
            node = curr_nodes.get(node_id)
            if node and node.get("kind") == "concern":
                events.append(
                    StrategicConcernRaised(
                        run_id=run_id,
                        tick=tick,
                        entity_id=entity_id,
                        concern_id=node_id,
                        concern_label=node.get("label", ""),
                    )
                )

        # 7. Overload detected
        if diff.get("overload_changed") and curr_snapshot.get("overload_source"):
            events.append(
                StrategicOverloadDetected(
                    run_id=run_id,
                    tick=tick,
                    entity_id=entity_id,
                    overload_source=curr_snapshot["overload_source"],
                )
            )

        # 8. Detour Created & Loop Suspected
        for node_id in diff.get("added_nodes", []):
            node = curr_nodes.get(node_id)
            if node and node.get("kind") == "project" and ("detour" in node.get("label", "").lower() or "detour" in node_id.lower()):
                # Attempt to find the blocker this detour project is trying to resolve
                blocker_id = self._find_associated_blocker(node_id, curr_snapshot)
                if blocker_id:
                    events.append(
                        StrategicDetourCreated(
                            run_id=run_id,
                            tick=tick,
                            entity_id=entity_id,
                            blocker_id=blocker_id,
                            detour_project_id=node_id,
                        )
                    )

                    # Increment detour count for this blocker
                    self.blocker_detour_counts[blocker_id] = (
                        self.blocker_detour_counts.get(blocker_id, 0) + 1
                    )
                    count = self.blocker_detour_counts[blocker_id]

                    if count >= self.detour_loop_threshold:
                        events.append(
                            StrategicDetourLoopSuspected(
                                run_id=run_id,
                                tick=tick,
                                entity_id=entity_id,
                                blocker_id=blocker_id,
                                detour_count=count,
                            )
                        )

        return events

    def _find_associated_blocker(self, detour_project_id: str, snapshot: Dict[str, Any]) -> Optional[str]:
        """
        Searches snapshot edges to identify the blocker linked to this detour project.
        Typically, blocker -> drives/blocks -> objective <- drives <- project.
        """
        graph = snapshot.get("graph", {})
        edges = graph.get("edges", [])
        nodes = {n["node_id"]: n for n in graph.get("nodes", [])}

        # Step 1: Find objectives driven by this detour project
        driven_objectives = set()
        for edge in edges:
            if edge.get("source_id") == detour_project_id and edge.get("kind") == "drives":
                driven_objectives.add(edge.get("target_id"))

        # Step 2: Find blockers that block those objectives
        for edge in edges:
            target = edge.get("target_id")
            source = edge.get("source_id")
            if target in driven_objectives and edge.get("kind") == "blocks":
                blocker_node = nodes.get(source)
                if blocker_node and blocker_node.get("kind") == "blocker":
                    return source

        # Fallback: Parse from ID structure if named detour_blockerId_tick or similar
        # e.g. proj_detour_blocker_01_100 -> blocker_01
        if "detour_" in detour_project_id:
            parts = detour_project_id.split("_")
            # If parts contain a blocker id sub-segment
            for part in parts:
                if part.startswith("blocker") or "block" in part:
                    return part

        return None
