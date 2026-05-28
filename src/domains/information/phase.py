"""
src/domains/information/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 5 — InformationBeliefPhase

Unified integration phase coordinating observation processing, pending query
routing, response normalizations, and belief assimilations.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any

from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate
from src.domains.information.schema import InformationQuery, InformationSourceProfile
from src.domains.information.router import InformationQueryRouter
from src.domains.information.normalizer import InformationResponseNormalizer
from src.domains.information.assimilation import InformationAssimilationService
from src.domains.information.resolver import InformationIntentResolver


class InformationBeliefPhase:
    """
    Coordinates subjective information routing and belief assimilation.
    """

    @staticmethod
    def apply(
        state: AuthoritativeState,
        profiles: List[InformationSourceProfile],
        pending_responses: Optional[List[Dict[str, Any]]] = None,
        context: Optional[dict] = None,
    ) -> StateUpdate:
        """
        Evaluate eligible actors on pending responses or active unknowns.
        """
        update = StateUpdate()
        entity_updates: Dict[int, EntityUpdate] = {}

        # 1. Filter active heroes
        actors = [e for e in state.entities.values() if e.combat.alive and e.lifecycle.active]
        if not actors:
            return update

        # Process pending responses
        resp_by_actor: Dict[int, List[Dict[str, Any]]] = {}
        if pending_responses:
            for r in pending_responses:
                actor_id = r.get("actor_id")
                if actor_id:
                    resp_by_actor.setdefault(actor_id, []).append(r)

        for actor in actors:
            # 2. Check if actor has active responses to assimilate
            actor_resps = resp_by_actor.get(actor.id, [])
            for r in actor_resps:
                q = InformationQuery(subject=r["subject"], kind=r["query_kind"])
                norm = InformationResponseNormalizer.normalize(
                    query=q,
                    source_id=r["source_id"],
                    raw_response=r["raw_response"],
                    cost_paid=r.get("cost_paid", 0),
                    current_tick=state.tick,
                )
                
                assim = InformationAssimilationService.assimilate(actor, norm, state.tick)
                
                # Setup updates
                entity_updates[actor.id] = EntityUpdate(
                    entity_id=actor.id,
                    intent_results=[],
                    property_updates={
                        "last_assimilated_subject": r["subject"],
                        "last_assimilated_tick": state.tick,
                    },
                    strategic=assim.strategic_update,
                    self_model_bundle_set=actor.self_model, # Re-attach updated self-model components later in engine loop
                )

            # 3. Else, if actor has unresolved unknowns, route new query
            if actor.id not in entity_updates:
                self_model = actor.self_model
                km = self_model.knowledge if self_model else None
                if km and km.unknowns:
                    # Select first unknown
                    first_unk = list(km.unknowns.values())[0]
                    q = InformationQuery(subject=first_unk.subject, kind="material_source")
                    
                    candidates = InformationQueryRouter.route(actor, q, state, profiles)
                    if candidates:
                        best_cand = candidates[0]
                        intent = InformationIntentResolver.resolve(actor, best_cand, q, state)
                        
                        if intent:
                            entity_updates[actor.id] = EntityUpdate(
                                entity_id=actor.id,
                                intent_results=[intent],
                                property_updates={
                                    "last_routed_query_subject": first_unk.subject,
                                    "last_routed_query_tick": state.tick,
                                },
                            )

        if entity_updates:
            update = StateUpdate(entity_updates=entity_updates)

        return update
