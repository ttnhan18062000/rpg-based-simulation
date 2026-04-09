from typing import TYPE_CHECKING
from src.api.schemas import AIDecisionSchema, GoalScoreSchema, SocialBondSchema, DecisionDriverSchema

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

class AIPresenter:
    """Translates raw AI decision data into explainable schemas."""

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
            narrative_impacts=narrative_impacts
        )
