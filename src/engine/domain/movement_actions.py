from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Dict, Tuple

from src.core.updates import EntityUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


class MovementActions:
    """
    Domain action handlers for authoritative movement.
    """

    @staticmethod
    def execute_move(
        state: AuthoritativeState,
        entity: EntityState, 
        target_pos: Tuple[float, float]
    ) -> Dict[int, EntityUpdate]:
        """GRID-BASED AUTHORITATIVE MOVEMENT."""
        from src.engine.movement import MovementSystem
        from src.engine.quests import QuestResolutionSystem
        
        res = MovementSystem.resolve_move(state, entity, target_pos)
        updates_dict = res if isinstance(res, dict) else {entity.id: res}
        
        # Check EXPLORE quests
        entity_up = updates_dict.get(entity.id)
        if entity_up and entity_up.new_position:
            # Create a temporary entity with the new position for evaluation
            temp_entity = replace(entity, navigation=replace(entity.navigation, position=entity_up.new_position))
            q_updates = QuestResolutionSystem.evaluate_explore(state, temp_entity)
            if q_updates:
                # Merge the first quest update
                updates_dict[entity.id] = replace(entity_up, quest=q_updates[0])
                
        return updates_dict
