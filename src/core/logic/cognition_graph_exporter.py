"""Service for exporting an entity's cognition as a deterministic graph. [MILESTONE 6]

This service derives a canonical CognitionGraph structure from the persisted 
state of an entity mind.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from src.core.models.cognition_graph import CognitionGraph, GraphNode, GraphEdge
from src.core.models.enums import StrategicStatus

if TYPE_CHECKING:
    from src.core.aspects.mind import Entity # type: ignore

class EntityCognitionExporter:
    """Read-only derivation of a cognition graph from entity state."""

    @staticmethod
    def export(entity: Any, tick: int) -> CognitionGraph:
        """Derive a canonical cognition graph for the given entity and tick."""
        
        # 1. Initialize graph
        graph = CognitionGraph(
            entity_id=entity.id,
            tick=tick,
            exported_at_tick=tick
        )
        
        # Helper for node creation to ensure stability
        def add_node(node_id: str, kind: str, label: str, attributes: dict | None = None):
            graph.nodes.append(GraphNode(
                node_id=node_id,
                kind=kind,
                label=label,
                attributes=attributes or {}
            ))
            
        def add_edge(source_id: str, target_id: str, kind: str, label: str | None = None):
            # Deterministic edge ID
            edge_id = f"{source_id}:{target_id}:{kind}"
            graph.edges.append(GraphEdge(
                edge_id=edge_id,
                source_id=source_id,
                target_id=target_id,
                kind=kind,
                label=label
            ))

        # 2. Map Entity Root
        root_id = f"entity:{entity.id}"
        add_node(root_id, "entity", f"Entity {entity.id}")
        
        # 3. Access Strategic State
        # Note: We assume MindAspect has a 'strategic' attribute of type StrategicState
        strat = getattr(entity.mind, "strategic", None)
        if not strat:
            return graph

        # 4. Map Directives
        for d in sorted(strat.directives, key=lambda x: x.directive_id):
            d_id = f"directive:{d.directive_id}"
            add_node(d_id, "directive", d.label, {"priority": d.priority, "kind": str(d.kind)})
            add_edge(root_id, d_id, "has_directive")

        # 5. Map Projects
        for p in sorted(strat.projects, key=lambda x: x.project_id):
            p_id = f"project:{p.project_id}"
            add_node(p_id, "project", p.label, {
                "project_kind": str(p.kind.name if hasattr(p.kind, "name") else p.kind),
                "status": str(p.status.name if hasattr(p.status, "name") else p.status),
                "priority": p.priority,
                "urgency": p.urgency
            })
            add_edge(root_id, p_id, "owns_project")
            
            # Map Objectives under Project
            for o in sorted(p.objectives, key=lambda x: x.objective_id):
                o_id = f"objective:{o.objective_id}"
                add_node(o_id, "objective", o.label, {
                    "status": str(o.status),
                    "progress": o.progress
                })
                add_edge(p_id, o_id, "has_objective")
                
                # Link objective to its active status
                if p.active_objective_id == o.objective_id:
                    add_edge(p_id, o_id, "active_objective")

        # 6. Map Continuity Edges
        if strat.current_project_id:
            curr_p_id = f"project:{strat.current_project_id}"
            add_edge(root_id, curr_p_id, "pursuing")
            
        if strat.current_objective_id:
            curr_o_id = f"objective:{strat.current_objective_id}"
            add_edge(root_id, curr_o_id, "active_objective")

        # 7. Map Interruptions & Suspensions
        if strat.interrupted_project_id and strat.current_project_id:
            old_p_id = f"project:{strat.interrupted_project_id}"
            new_p_id = f"project:{strat.current_project_id}"
            add_edge(old_p_id, new_p_id, "interrupted_by")

        # 8. Map Concerns
        for c in sorted(strat.concerns, key=lambda x: x.concern_id):
            c_id = f"concern:{c.concern_id}"
            add_node(c_id, "concern", c.label, {
                "concern_kind": str(c.kind.name if hasattr(c.kind, "name") else c.kind),
                "priority": c.priority
            })
            add_edge(root_id, c_id, "has_concern")

        # 9. Map Blockers
        for b in sorted(strat.blockers, key=lambda x: x.blocker_id):
            b_id = f"blocker:{b.blocker_id}"
            add_node(b_id, "blocker", b.label, {"severity": b.severity})
            # Edges for blockers depend on what they block, often linked via objectives
            # For now, link to entity root if general
            add_edge(root_id, b_id, "has_blocker")

        # 10. Map Leads
        for l in sorted(strat.leads, key=lambda x: x.lead_id):
            l_id = f"lead:{l.lead_id}"
            add_node(l_id, "lead", l.label, {"certainty": l.certainty})
            add_edge(root_id, l_id, "has_lead")

        # Final Determinism: Sort nodes and edges
        graph.nodes.sort(key=lambda x: x.node_id)
        graph.edges.sort(key=lambda x: x.edge_id)

        return graph
