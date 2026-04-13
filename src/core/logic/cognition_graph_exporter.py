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
                
                # Link objective to its supporting leads [phase_3_task_5]
                for lead_ref in o.leads:
                    l_ref_id = f"lead:{lead_ref.lead_id}"
                    add_edge(l_ref_id, o_id, "supports_objective")
                
                # Link objective to its blockers [phase_3_task_5]
                for b_id_ref in o.blocker_ids:
                    b_ref_id = f"blocker:{b_id_ref}"
                    add_edge(b_ref_id, o_id, "blocks_objective")

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
            
            # Map structural links for concerns if applicable [phase_3_task_5]
            if hasattr(c, "source_event_id") and c.source_event_id:
                ev_id = f"event:{c.source_event_id}"
                # (Events aren't fully in graph yet, but we could add stub nodes)
                # add_node(ev_id, "event", f"Event {c.source_event_id}")
                # add_edge(ev_id, c_id, "caused_concern")
                pass

        # 9. Map Blockers
        for b in sorted(strat.blockers, key=lambda x: x.blocker_id):
            b_id = f"blocker:{b.blocker_id}"
            add_node(b_id, "blocker", b.label, {"severity": b.severity})
            # Edges for blockers depend on what they block, often linked via objectives
            # For now, link to entity root if general
            add_edge(root_id, b_id, "has_blocker")

        # 10. Map Leads
            add_node(l_id, "lead", l.label, {
                "certainty": l.certainty,
                "kind": str(l.kind),
                "target_pos": str(l.target_coords) if l.target_coords else None
            })
            add_edge(root_id, l_id, "has_lead")
            
        # 11. Map Decision Drivers [phase_3_task_5]
        for driver in getattr(strat, "recent_drivers", []):
            dr_id = f"driver:{driver.label}:{tick}"
            add_node(dr_id, "decision_driver", driver.label, {
                "kind": driver.kind,
                "weight": driver.weight,
                "description": driver.description
            })
            add_edge(root_id, dr_id, "driven_by")

        # 12. Map Turning Points [MILESTONE 6 Expansion]
        narrative = getattr(entity.mind, "narrative", None)
        if narrative:
            for tp in sorted(narrative.turning_points, key=lambda x: x.event_id):
                tp_id = f"turning_point:{tp.event_id}"
                add_node(tp_id, "turning_point", tp.summary_tag or tp.kind.name, {
                    "kind": tp.kind.name,
                    "tick": tp.tick,
                    "impact": tp.emotional_impact,
                    "salience": tp.salience_score
                })
                add_edge(root_id, tp_id, "experienced")

        # 13. Map Place Attachments [MILESTONE 6 Expansion]
        attachments = getattr(entity.mind, "place_attachments", [])
        for pa in sorted(attachments, key=lambda x: str(x.location_pos)):
            pa_id = f"place_attachment:{pa.location_pos}"
            add_node(pa_id, "place_attachment", pa.kind.name, {
                "kind": pa.kind.name,
                "importance": pa.importance,
                "pos": str(pa.location_pos)
            })
            add_edge(root_id, pa_id, "attached_to")

        # Final Determinism: Sort nodes and edges
        graph.nodes.sort(key=lambda x: x.node_id)
        graph.edges.sort(key=lambda x: x.edge_id)

        return graph
