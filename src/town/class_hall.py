from __future__ import annotations
from typing import Optional, List
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate, IdentityUpdate, StrategicUpdate, InventoryUpdate

class ClassHallAction:
    """Action for skill training and capability progression."""

    @staticmethod
    def train(entity: EntityState, skill_id: str, state: AuthoritativeState) -> Optional[StateUpdate]:
        """
        Train a specific skill/recipe.
        Cost: 50 gold.
        Resolves 'capability' blockers for the trained skill.
        """
        # 1. Validation: Has enough gold and doesn't know it yet
        if entity.inventory.gold < 50 or skill_id in entity.identity.known_recipes:
            return None
            
        # 2. Find matching capability blockers
        resolved_blockers = []
        for b_id, b in entity.strategic.blockers.items():
            if b.kind == "capability" and b.subject == skill_id:
                resolved_blockers.append(b_id)
                
        # 3. Transaction
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    inventory=InventoryUpdate(gold_delta=-50),
                    identity=IdentityUpdate(recipes_learned={skill_id}),
                    strategic=StrategicUpdate(blockers_remove=resolved_blockers)
                )
            }
        )
