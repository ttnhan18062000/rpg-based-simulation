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
from src.core.strategic import LeadCertainty
from src.core.updates import StateUpdate, EntityUpdate
from src.domains.information.bridge import ObservationBeliefBridge
from src.domains.information.schema import InformationQuery, InformationSourceProfile
from src.domains.information.router import InformationQueryRouter
from src.domains.information.normalizer import InformationResponseNormalizer
from src.domains.information.assimilation import InformationAssimilationService
from src.domains.information.resolver import InformationIntentResolver
from src.engine.intent.action_intent import ActionIntent


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
                
                from dataclasses import replace as dataclass_replace
                new_self_model = dataclass_replace(actor.self_model, knowledge=assim.knowledge_update)
                
                # Setup updates
                entity_updates[actor.id] = EntityUpdate(
                    entity_id=actor.id,
                    intent_results=[],
                    property_updates={
                        "last_assimilated_subject": r["subject"],
                        "last_assimilated_tick": state.tick,
                    },
                    strategic=assim.strategic_update,
                    self_model_bundle_set=new_self_model,
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
                    for cand in candidates:
                        result = InformationIntentResolver.resolve(actor, cand, q, state)
                        if isinstance(result, ActionIntent):
                            entity_updates[actor.id] = EntityUpdate(
                                entity_id=actor.id,
                                intent_results=[result],
                                property_updates={
                                    "last_routed_query_subject": first_unk.subject,
                                    "last_routed_query_tick": state.tick,
                                },
                            )
                            break
                        # else: InformationResponse(answer_kind="insufficient_gold", ...) — try next candidate

            # 4. Synthesize claim_failed_search / region_danger_seen observations for
            # untested leads and route them through BeliefContradictionService via the
            # bridge. Not gated on branches (2)/(3) already having written this actor --
            # merge into whatever EntityUpdate they may have produced instead of a bare
            # assignment (see EntityUpdate.merge()'s self_model_bundle_set hazard note below).
            for lead in actor.strategic.leads.values():
                if lead.tested or lead.certainty == LeadCertainty.EXHAUSTED:
                    continue

                obs_event: Optional[Dict[str, Any]] = None

                if actor.navigation.last_failure_reason is not None:
                    project = actor.strategic.projects.get(actor.strategic.current_project_id)
                    objective = None
                    if project is not None:
                        objective = next(
                            (o for o in project.objectives if o.id == actor.strategic.current_objective_id),
                            None,
                        )
                    if objective is not None and objective.target == lead.subject:
                        obs_event = {
                            "kind": "claim_failed_search",
                            "subject": lead.subject,
                            "lead_id": lead.id,
                            "location_searched": lead.detail,
                            "details": {},
                        }

                if obs_event is None and lead.kind == "location" and lead.certainty in (
                    LeadCertainty.VAGUE, LeadCertainty.APPROXIMATE
                ) and lead.detail == actor.navigation.region_id:
                    region_id = actor.navigation.region_id
                    region = state.regions.get(region_id) if region_id else None
                    has_active_scar = False
                    if region is not None:
                        x_min, y_min, x_max, y_max = region.bounds
                        for scar in state.local_scars.values():
                            sx, sy = scar.position
                            if x_min <= sx <= x_max and y_min <= sy <= y_max:
                                has_active_scar = True
                                break
                    if has_active_scar:
                        obs_event = {
                            "kind": "region_danger_seen",
                            "subject": lead.subject,
                            "region_id": region_id,
                            "details": {},
                        }

                if obs_event is None:
                    continue

                assim = ObservationBeliefBridge.process_observation(actor, obs_event, state)
                if assim.strategic_update is not None:
                    new_ent_upd = EntityUpdate(entity_id=actor.id, strategic=assim.strategic_update)
                    existing = entity_updates.get(actor.id)
                    entity_updates[actor.id] = existing.merge(new_ent_upd) if existing is not None else new_ent_upd

        if entity_updates:
            update = StateUpdate(entity_updates=entity_updates)

        return update
