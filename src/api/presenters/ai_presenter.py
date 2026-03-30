from typing import TYPE_CHECKING
from src.api.schemas import AIDecisionSchema, GoalScoreSchema

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

        return AIDecisionSchema(
            entity_id=entity.id,
            current_state=decision.ai_state.name.lower(),
            winning_goal=decision.last_goal or "none",
            goal_scores=goal_scores,
            nearest_enemy_dist=nearest_dist,
            nearest_target_id=nearest_id
        )
