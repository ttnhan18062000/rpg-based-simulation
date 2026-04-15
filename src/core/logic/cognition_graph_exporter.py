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
    """Read-only derivation of a cognition graph from entity state.
    
    [TRUTH OWNERSHIP]
    - Owner of Relational Reasoning Topology.
    - Responsible for mapping internal state (projects, links, biases) into nodes and edges.
    - Must stay structurally consistent with AIPresenter claims.
    - Used for advanced graph-based verification and visual reasoning inspection.
    """

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
        for l in sorted(strat.leads, key=lambda x: x.lead_id):
            l_id = f"lead:{l.lead_id}"
            add_node(l_id, "lead", l.label, {
                "certainty": l.certainty,
                "kind": str(l.kind),
                "target_pos": str(l.target_coords) if l.target_coords else None
            })
            add_edge(root_id, l_id, "has_lead")

        # 11. Map Candidate Zones [MILESTONE 6 Expansion]
        for z in sorted(strat.candidate_zones, key=lambda x: x.zone_id):
            z_id = f"candidate_zone:{z.zone_id}"
            add_node(z_id, "candidate_zone", f"Zone {z.zone_id}", {
                "confidence": z.confidence,
                "approx_coords": str(z.approx_coords) if z.approx_coords else None
            })
            add_edge(root_id, z_id, "monitoring_zone")
            
            # Link supporting leads back to zone
            for lead_id in z.supporting_lead_ids:
                add_edge(f"lead:{lead_id}", z_id, "supports_zone")

        # 12. Map Hypotheses [MILESTONE 6 Expansion]
        for h in sorted(strat.hypotheses, key=lambda x: x.hypothesis_id):
            h_id = f"hypothesis:{h.hypothesis_id}"
            add_node(h_id, "hypothesis", h.label, {"confidence": h.confidence})
            add_edge(root_id, h_id, "formulated_hypothesis")
            
            for lead_id in h.supporting_lead_ids:
                add_edge(f"lead:{lead_id}", h_id, "supports_hypothesis")
            for lead_id in h.contradicted_by_lead_ids:
                add_edge(f"lead:{lead_id}", h_id, "contradicts_hypothesis")
            
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
                
                # Link involved entities to turning point
                for inv_id in tp.involved_entity_ids:
                    add_edge(tp_id, f"entity:{inv_id}", "involved")

        # 14. Map Social Bonds (Relational Edges) [MILESTONE 6 Expansion]
        social = getattr(entity.mind, "social", None)
        if social:
            for bond in sorted(social.known_bonds.values(), key=lambda x: x.target_id):
                target_node_id = f"entity:{bond.target_id}"
                # Add stub node for target if it doesn't exist ( exporter is local to one entity usually)
                # But we want to see the edge.
                edge_kind = "social_bond"
                add_edge(root_id, target_node_id, edge_kind, f"Trust: {bond.trust:.2f}")
                # We could add more specific edges or attributes to the edge here
                # [PHASE 5] Add detailed attributes to social edges
        
        # 15. Map Active Recruitment Offers [MILESTONE 6 Expansion]
        for offer in sorted(strat.offers, key=lambda x: x.offer_id):
            off_id = f"offer:{offer.offer_id}"
            target_id = f"entity:{offer.candidate_id}"
            add_node(off_id, "offer", f"Offer {offer.offer_id}", {
                "status": str(offer.status),
                "kind": str(offer.contract_kind)
            })
            add_edge(root_id, off_id, "sent_offer")
            add_edge(off_id, target_id, "proposed_to")

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

        # 14. Map Cognition Profile & Usage [MILESTONE 7 Expansion]
        if strat.last_capacity_profile:
            cp_id = f"cognition:{entity.id}:{tick}"
            cp = strat.last_capacity_profile
            add_node(cp_id, "cognition_profile", "Cognitive Profile", {
                "planning_budget": cp.planning_budget,
                "judgment_stability": cp.judgment_stability,
                "evidence_quality": cp.evidence_quality,
                "social_bandwidth": cp.social_bandwidth,
                "detour_depth_limit": cp.detour_depth_limit,
                "active_slice_limit": cp.active_slice_limit,
                "concern_intake_limit": cp.concern_intake_limit,
                "lead_retention_limit": cp.lead_retention_limit,
                "candidate_zone_limit": cp.candidate_zone_limit,
                "ally_evaluation_limit": cp.ally_evaluation_limit,
                "blocker_resolution_patience": cp.blocker_resolution_patience,
                "resume_reliability": cp.resume_reliability,
                "interruption_resistance": cp.interruption_resistance,
                "abandonment_threshold_mod": cp.abandonment_threshold_mod,
                "contradiction_sensitivity": cp.contradiction_sensitivity,
                "source_trust_learning_rate": cp.source_trust_learning_rate,
                # Usage stats
                "active_slice_used": strat.active_slice_used,
                "active_concerns_used": strat.active_concerns_used,
                "retained_leads_used": strat.retained_leads_used,
                "candidate_zones_used": strat.candidate_zones_used,
                "ally_evaluations_used": strat.ally_evaluations_used,
                "detour_depth_used": strat.detour_depth_used,
                "dropped_candidates": strat.dropped_candidates_count,
                "is_overloaded": strat.is_overloaded,
                "overload_score": strat.overload_score,
                "primary_overload_source": strat.primary_overload_source,
                "last_overload_tick": strat.last_overload_tick
            })
            add_edge(root_id, cp_id, "has_cognition_profile")

        # Final Determinism: Sort nodes and edges
        graph.nodes.sort(key=lambda x: x.node_id)
        graph.edges.sort(key=lambda x: x.edge_id)

        return graph
