from typing import TYPE_CHECKING, Any, Optional
from src.api.schemas import AIDecisionSchema, GoalScoreSchema, SocialBondSchema, DecisionDriverSchema

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

class AIPresenter:
    """Translates raw AI decision data into explainable schemas.
    
    [TRUTH OWNERSHIP]
    - Owner of Structured Human-Facing Inspection.
    - Responsible for translating raw MindAspect state into a shape matching AIDecisionSchema.
    - Must NOT mutate entity state or invent missing history.
    - Used by the REST API and entity inspection endpoints.
    """

    @staticmethod
    def get_explanation(entity: "Entity") -> AIDecisionSchema:
        mind = entity.mind
        decision = mind.decision
        perception = mind.perception
        
        goal_scores = []
        for gname, score in decision.goal_scores.items():
            status = "considering"
            if gname == decision.last_goal:
                status = "executing"
            
            goal_scores.append(GoalScoreSchema(
                goal_name=gname,
                score=round(score, 3),
                status=status
            ))
            
        # Sort by score for readability
        goal_scores.sort(key=lambda x: x.score, reverse=True)

        # Tactical context from memory
        nearest_dist = None
        nearest_id = None
        if perception.entity_memory:
            # Find nearest recorded entity
            min_d = 999
            for oid, belief in perception.entity_memory.items():
                d = entity.spatial.pos.manhattan(belief.pos)
                if d < min_d:
                    min_d = d
                    nearest_id = oid
            nearest_dist = float(min_d) if nearest_id is not None else None

        # Stage 1: Personality, Motives, and Beliefs
        personality_dict = {
            "aggression": round(decision.personality.aggression, 2),
            "greed": round(decision.personality.greed, 2),
            "caution": round(decision.personality.caution, 2),
            "ambition": round(decision.personality.ambition, 2),
            "curiosity": round(decision.personality.curiosity, 2)
        }
        
        motives_list = [
            {"kind": m.kind, "priority": round(m.priority, 2), "progress": round(m.progress, 2)}
            for m in decision.motives if m.active
        ]
        
        beliefs_list = []
        for eid, belief in perception.entity_memory.items():
            beliefs_list.append({
                "entity_id": eid,
                "threat": {"overall": round(belief.threat.overall, 2)},
                "confidence": round(belief.confidence, 2),
                "apparent_faction": belief.apparent_faction,
                "apparent_role": belief.apparent_role,
                "apparent_class": belief.apparent_class,
                "visible_weapon": belief.visible_weapon,
                "visible_injury": round(belief.visible_injury, 2) if belief.confidence > 0.5 else -1.0
            })

        # [PHASE 2] Social Stance
        name_map = {}
        # Simple name resolution for explanations
        if hasattr(entity, 'world') and entity.world:
             name_map = {e.id: e.identity.display_name for e in entity.world.entities.values()}
        
        social_bonds = []
        for bond in mind.social.known_bonds.values():
            # Find relevant turning points for this specific bond
            relevant_tps = [
                tp for tp in mind.narrative.turning_points 
                if bond.target_id in tp.involved_entity_ids
            ]
            relevant_tps.sort(key=lambda x: x.tick, reverse=True)
            
            impacts = []
            if relevant_tps:
                top_tp = relevant_tps[0]
                impacts.append(f"{top_tp.kind.name.title()} event on tick {top_tp.tick}")
                if top_tp.emotional_impact > 5:
                    impacts.append("Extreme emotional impact")
                elif top_tp.emotional_impact < -5:
                    impacts.append("Severe negative trauma")
                    
            social_bonds.append(SocialBondSchema(
                target_id=bond.target_id,
                target_name=name_map.get(bond.target_id, f"Entity {bond.target_id}"),
                trust=round(bond.trust, 2),
                fear=round(bond.fear, 2),
                rivalry=round(bond.rivalry, 2),
                familiarity=round(bond.familiarity, 2),
                social_impacts=impacts
            ))
            
        # Top-level dramatic turning points
        dramatic_tps = sorted(
            [tp for tp in mind.narrative.turning_points if tp.emotional_impact > 7 or tp.still_salient],
            key=lambda x: x.salience_score,
            reverse=True
        )[:3]
        
        narrative_impacts = []
        for tp in dramatic_tps:
             involves = [name_map.get(eid, f"entity {eid}") for eid in tp.involved_entity_ids]
             msg = f"{tp.kind.name.replace('_', ' ').title()}"
             if involves:
                 msg += f" involving {', '.join(involves)}"
             narrative_impacts.append(f"{msg} (Tick {tp.tick})")
        
        return AIDecisionSchema(
            entity_id=entity.id,
            current_state=decision.ai_state.name.lower() if hasattr(decision.ai_state, 'name') else str(decision.ai_state),
            winning_goal=str(decision.last_goal) if decision.last_goal else "none",
            goal_scores=goal_scores,
            personality=personality_dict,
            motives=motives_list,
            beliefs=beliefs_list,
            social_bonds=social_bonds,
            faction_standing=dict(mind.social.faction_standing),
            decision_drivers=list(decision.decision_drivers) if decision.decision_drivers else [],
            driver_details=[
                DecisionDriverSchema(kind=d.kind, label=d.label, weight=round(d.weight, 2))
                for d in decision.driver_details
            ],
            nearest_enemy_dist=nearest_dist,
            nearest_target_id=nearest_id,
            group_id=entity.identity.group_id,
            active_routine_id=mind.routine.active_routine_id,
            strategy=AIPresenter.serialize_strategy(entity), # [PHASE 4]
            narrative_impacts=narrative_impacts
        )

    @staticmethod
    def serialize_strategy(entity: "Entity") -> Any:
        """Shim for strategic serialization to avoid circular dependencies with EntityPresenter."""
        from src.api.schemas import (
            StrategicStateSchema, ProjectSchema, ObjectiveSchema, 
            BlockerSchema, LeadSchema, DirectiveSchema, ConcernSchema,
            CandidateZoneSchema, HypothesisSchema, ObligationSchema,
            SocialContractSchema, RecruitmentOfferSchema,
            CognitionCapacitySchema, CognitionBudgetUsageSchema, CognitionOverloadSchema
        )
        s = entity.mind.strategic
        if not s:
            return None
            
        return StrategicStateSchema(
            directives=[
                DirectiveSchema(
                    directive_id=d.directive_id,
                    kind=d.kind.name.lower() if hasattr(d.kind, "name") else str(d.kind).lower(),
                    label=d.label,
                    priority=d.priority
                ) for d in s.directives
            ],
            projects=[
                ProjectSchema(
                    project_id=p.project_id,
                    kind=p.kind.name.lower() if hasattr(p.kind, "name") else str(p.kind).lower(),
                    label=p.label,
                    status=p.status.name.lower() if hasattr(p.status, "name") else str(p.status).lower(),
                    priority=round(p.priority, 2),
                    urgency=round(p.urgency, 2),
                    active_objective_id=p.active_objective_id,
                    suspension_reason=p.suspension_reason,
                    committed_at=p.committed_at,
                    abandonment_cost=round(p.abandonment_cost, 2),
                    interruption_threshold=round(p.interruption_threshold, 2),
                    emotional_weight=round(p.emotional_weight, 2),
                    objectives=[
                        ObjectiveSchema(
                            objective_id=o.objective_id,
                            kind=o.kind.name.lower() if hasattr(o.kind, "name") else str(o.kind).lower(),
                            label=o.label,
                            status=o.status.name.lower() if hasattr(o.status, "name") else str(o.status).lower(),
                            priority=round(o.priority, 2),
                            progress=round(o.progress, 2),
                            blocker_ids=o.blocker_ids,
                            leads=[
                                LeadSchema(
                                    lead_id=l.lead_id,
                                    kind=l.kind.name.lower() if hasattr(l.kind, "name") else str(l.kind).lower(),
                                    label=l.label,
                                    subject=l.subject,
                                    certainty=round(l.certainty, 2),
                                    source_type=l.source_type,
                                    discovered_tick=l.discovered_tick,
                                    directness=round(l.directness, 2),
                                    is_exhausted=l.is_exhausted
                                ) for l in o.leads
                            ]
                        ) for o in p.objectives
                    ]
                ) for p in s.projects
            ],
            blockers=[
                BlockerSchema(
                    blocker_id=b.blocker_id,
                    kind=b.kind.name.lower() if hasattr(b.kind, "name") else str(b.kind).lower(),
                    label=b.label,
                    severity=round(b.severity, 2),
                    resolved=b.resolved
                ) for b in s.blockers
            ],
            leads=[
                LeadSchema(
                    lead_id=l.lead_id,
                    kind=l.kind.name.lower() if hasattr(l.kind, "name") else str(l.kind).lower(),
                    label=l.label,
                    subject=l.subject,
                    certainty=round(l.certainty, 2),
                    source_type=l.source_type,
                    discovered_tick=l.discovered_tick,
                    directness=round(l.directness, 2),
                    is_exhausted=l.is_exhausted
                ) for l in s.leads
            ],
            zones=[
                CandidateZoneSchema(
                    zone_id=z.zone_id,
                    region_id=z.region_id,
                    confidence=round(z.confidence, 2),
                    search_outcome=z.search_outcome,
                    last_search_tick=z.last_search_tick
                ) for z in s.candidate_zones
            ],
            hypotheses=[
                HypothesisSchema(
                    hypothesis_id=h.hypothesis_id,
                    label=h.label,
                    confidence=round(h.confidence, 2),
                    is_active=h.is_active
                ) for h in s.hypotheses
            ],
            concerns=[
                ConcernSchema(
                    concern_id=c.concern_id,
                    kind=c.kind.name.lower() if hasattr(c.kind, "name") else str(c.kind).lower(),
                    label=c.label,
                    priority=round(c.priority, 2),
                    urgency=round(c.urgency, 2),
                    visibility=c.visibility
                ) for c in s.concerns
            ],
            obligations=[
                ObligationSchema(
                    obligation_id=o.obligation_id,
                    target_id=o.target_id,
                    label=o.label,
                    priority=round(o.priority, 2),
                    deadline_tick=o.deadline_tick
                ) for o in s.obligations
            ],
            contracts=[
                SocialContractSchema(
                    contract_id=c.contract_id,
                    kind=c.kind.name.lower() if hasattr(c.kind, "name") else str(c.kind).lower(),
                    purpose=c.purpose,
                    founder_id=c.founder_id,
                    member_ids=c.member_ids,
                    member_roles=c.member_roles,
                    status=c.status.name.lower() if hasattr(c.status, "name") else str(c.status).lower(),
                    created_tick=c.created_tick,
                    expires_tick=c.expires_tick,
                    breach_count=len(c.breach_history)
                ) for c in s.contracts
            ],
            offers=[
                RecruitmentOfferSchema(
                    offer_id=o.offer_id,
                    recruiter_id=o.recruiter_id,
                    candidate_id=o.candidate_id,
                    contract_kind=o.contract_kind.name.lower() if hasattr(o.contract_kind, "name") else str(o.contract_kind).lower(),
                    status=o.status.name.lower() if hasattr(o.status, "name") else str(o.status).lower(),
                    negotiation_count=o.negotiation_count,
                    expires_tick=o.expires_tick
                ) for o in s.offers
            ],
            current_project_id=s.current_project_id,
            current_objective_id=s.current_objective_id,
            interrupted_project_id=s.interrupted_project_id,
            project_lock_until=s.project_lock_until,
            recent_driver_labels=[d.label for d in s.recent_drivers],
            recent_drivers=[
                DecisionDriverSchema(kind=d.kind, label=d.label, weight=round(d.weight, 2))
                for d in s.recent_drivers
            ],
            
            # [phase_2_intel_capacity]
            capacity=CognitionCapacitySchema(**s.last_capacity_profile.model_dump()) if s.last_capacity_profile else None,
            usage=CognitionBudgetUsageSchema(
                active_slice_used=s.active_slice_used,
                active_concerns_used=s.active_concerns_used,
                retained_leads_used=s.retained_leads_used,
                candidate_zones_used=s.candidate_zones_used,
                ally_evaluations_used=s.ally_evaluations_used,
                detour_depth_used=s.detour_depth_used,
                dropped_candidates_count=s.dropped_candidates_count,
                latent_concerns_count=s.latent_concerns_count
            ) if s.last_capacity_profile else None,
            overload=CognitionOverloadSchema(
                is_overloaded=s.is_overloaded,
                overload_score=round(s.overload_score, 2),
                primary_overload_source=s.primary_overload_source,
                last_overload_tick=s.last_overload_tick
            ) if s.last_capacity_profile else None
        )

