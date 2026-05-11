# Compliance IDs: STRAT-013
"""
Cognition Graph Export (Read-Only Presenter).

Exposes persisted strategic state for debugging and visualization
without becoming the source of truth.

Covers:
- Part 1 §Strategic: Cognition graph export exposes persisted strategic state
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any

from src.core.state import EntityState
from src.core.strategic import StrategicComponent


@dataclass(frozen=True, slots=True)
class CognitionGraphNode:
    """A single node in the cognition graph."""
    id: str
    kind: str  # 'directive', 'project', 'objective', 'blocker', 'lead', 'concern', 'hypothesis'
    label: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CognitionGraphEdge:
    """A relationship between cognition nodes."""
    source: str
    target: str
    kind: str  # 'blocks', 'drives', 'suggests', 'supports'


@dataclass(frozen=True, slots=True)
class CognitionGraph:
    """Complete cognition graph snapshot."""
    entity_id: int
    nodes: List[CognitionGraphNode] = field(default_factory=list)
    edges: List[CognitionGraphEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CognitionGraphExporter:
    """
    Read-only presenter for strategic cognition state.
    Does NOT mutate any state. Does NOT serve as source of truth.
    """

    @staticmethod
    def export(entity: EntityState) -> CognitionGraph:
        """
        Export the entity's strategic state as a typed graph.
        """
        nodes: List[CognitionGraphNode] = []
        edges: List[CognitionGraphEdge] = []
        strat = entity.strategic

        # Directives
        for d in strat.directives.values():
            nodes.append(CognitionGraphNode(
                id=d.id, kind="directive",
                label=f"{d.kind}: {d.target or 'general'}",
                attributes={"priority": d.priority.value, "salience": d.salience}
            ))

        # Projects
        for p in strat.projects.values():
            nodes.append(CognitionGraphNode(
                id=p.id, kind="project",
                label=f"{p.kind} ({p.status.value})",
                attributes={"score": p.score, "status": p.status.value}
            ))
            # Link objectives
            for obj in p.objectives:
                nodes.append(CognitionGraphNode(
                    id=obj.id, kind="objective",
                    label=f"{obj.kind}: {obj.target or '?'}",
                    attributes={"status": obj.status.value}
                ))
                edges.append(CognitionGraphEdge(
                    source=p.id, target=obj.id, kind="drives"
                ))
                # Link blockers to objectives
                for b_id in obj.blocker_ids:
                    if b_id in strat.blockers:
                        edges.append(CognitionGraphEdge(
                            source=b_id, target=obj.id, kind="blocks"
                        ))

        # Blockers
        for b in strat.blockers.values():
            nodes.append(CognitionGraphNode(
                id=b.id, kind="blocker",
                label=f"{b.kind}: {b.subject}",
                attributes={"severity": b.severity, "resolved": b.resolved}
            ))

        # Leads
        for l in strat.leads.values():
            nodes.append(CognitionGraphNode(
                id=l.id, kind="lead",
                label=f"{l.kind}: {l.subject}",
                attributes={"certainty": l.certainty.value, "tested": l.tested}
            ))

        # Concerns
        for c in strat.concerns.values():
            nodes.append(CognitionGraphNode(
                id=c.id, kind="concern",
                label=f"{c.kind}: {c.source}",
                attributes={"urgency": c.urgency}
            ))

        # Hypotheses
        for h in strat.hypotheses.values():
            nodes.append(CognitionGraphNode(
                id=h.id, kind="hypothesis",
                label=f"{h.claim}",
                attributes={"confidence": h.confidence}
            ))
            for lead_id in h.supporting_lead_ids:
                edges.append(CognitionGraphEdge(
                    source=lead_id, target=h.id, kind="supports"
                ))

        # Metadata
        metadata = {
            "current_project": strat.current_project_id,
            "current_objective": strat.current_objective_id,
            "overload_source": strat.primary_overload_source,
            "profile": {
                "max_leads": strat.profile.max_leads,
                "max_concerns": strat.profile.max_concerns,
                "interruption_resistance": strat.profile.interruption_resistance
            }
        }

        return CognitionGraph(
            entity_id=entity.id,
            nodes=nodes,
            edges=edges,
            metadata=metadata
        )

    @staticmethod
    def is_deterministic(entity: EntityState) -> bool:
        """Verify that multiple exports from the same state are identical."""
        g1 = CognitionGraphExporter.export(entity)
        g2 = CognitionGraphExporter.export(entity)
        return g1 == g2
