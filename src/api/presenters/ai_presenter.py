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
            for oid, pos in perception.entity_memory.items():
                d = entity.spatial.pos.manhattan(pos)
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
        social_bonds = [
            SocialBondSchema(
                target_id=bond.target_id,
                trust=round(bond.trust, 2),
                fear=round(bond.fear, 2),
                rivalry=round(bond.rivalry, 2),
                familiarity=round(bond.familiarity, 2)
            )
            for bond in mind.social.known_bonds.values()
        ]
        
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
            nearest_target_id=nearest_id
        )
