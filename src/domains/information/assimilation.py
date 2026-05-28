"""
src/domains/information/assimilation.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — InformationAssimilationService

Assimilates normalized responses into the entity's KnowledgeModelComponent
and strategic state under strict capacity restrictions.
"""

from __future__ import annotations
from typing import Dict, Any

from src.core.state import EntityState
from src.core.updates import StrategicUpdate
from src.core.self_model import KnowledgeModelComponent
from src.domains.information.schema import (
    NormalizedInformationResponse,
    InformationAssimilationResult,
)


class InformationAssimilationService:
    """
    Handles personal knowledge integration within capacity limits.
    """

    @staticmethod
    def assimilate(
        entity: EntityState,
        response: NormalizedInformationResponse,
        current_tick: int,
    ) -> InformationAssimilationResult:
        """
        Merge new facts, leads, and unknowns, maintaining strict memory capacities.
        """
        # Load existing knowledge model
        self_model = entity.self_model
        km = self_model.knowledge if self_model else None
        
        if not km:
            km = KnowledgeModelComponent()

        # Deduplicate facts & unknowns
        new_facts = dict(km.facts)
        new_unknowns = dict(km.unknowns)

        # 1. Capacity bounds check (max = 10 facts to avoid memory inflation)
        max_facts = 10
        max_unknowns = 5

        for fact in response.facts:
            # If already full, pop oldest or skip
            if len(new_facts) >= max_facts and fact.subject not in new_facts:
                oldest_key = min(new_facts.keys(), key=lambda k: new_facts[k].recorded_tick)
                new_facts.pop(oldest_key)
            
            new_facts[fact.subject] = fact
            
            # Resolve corresponding unknown if any
            if fact.subject in new_unknowns:
                new_unknowns.pop(fact.subject)

        for unk in response.unknowns:
            if len(new_unknowns) >= max_unknowns and unk.subject not in new_unknowns:
                oldest_key = min(new_unknowns.keys(), key=lambda k: new_unknowns[k].recorded_tick)
                new_unknowns.pop(oldest_key)
            
            new_unknowns[unk.subject] = unk

        from src.engine.apply import replace
        updated_km = replace(km, facts=new_facts, unknowns=new_unknowns, last_updated_tick=current_tick)

        # 2. Add lead state to strategic updates
        leads_to_add = list(response.leads)
        
        # Prune older strategic leads if exceeding strategic limits (max = 8)
        strat = getattr(entity, "strategic", None)
        existing_leads = dict(strat.leads) if strat else {}
        for lead in leads_to_add:
            if len(existing_leads) >= 8 and lead.id not in existing_leads:
                oldest_lead_id = min(existing_leads.keys(), key=lambda lid: existing_leads[lid].discovered_tick)
                existing_leads.pop(oldest_lead_id)
            existing_leads[lead.id] = lead

        # Prepare StrategicUpdate
        strat_upd = StrategicUpdate(
            leads_add_or_update=list(existing_leads.values()),
        )

        trace = {
            "source_id": response.source_id,
            "answer_kind": response.answer_kind,
            "facts_added": len(response.facts),
            "leads_added": len(response.leads),
        }

        return InformationAssimilationResult(
            knowledge_update=updated_km,
            strategic_update=strat_upd,
            source_trust_update=None, # Will be resolved by trust service
            trace=trace,
        )
