from __future__ import annotations
from typing import Dict, List
from src.core.state import AuthoritativeState, EntityState, BuildingState
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, BiologicalUpdate, InventoryUpdate, CombatUpdate

class TownServiceSystem:
    """Processes multi-tick interactions with town buildings."""

    @staticmethod
    def update(state: AuthoritativeState) -> StateUpdate:
        entity_updates = {}
        
        for entity in state.entities.values():
            if not entity.interaction or entity.interaction.target_node_id is None:
                continue
                
            kind = entity.properties.get("interaction_kind")
            if kind not in ["inn", "tavern", "guild"]:
                continue
                
            building_id = entity.interaction.target_node_id
            building = state.buildings.get(building_id)
            
            if not building or not building.functional:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            # Proximity
            dist = abs(entity.position[0] - building.position[0]) + abs(entity.position[1] - building.position[1])
            if dist > 1.5:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            # Progress
            new_progress = entity.interaction.progress + 1.0
            required = 10.0 # Standard interaction time
            
            if new_progress >= required:
                # SUCCESS
                if kind == "inn":
                    # Full rest and HP recovery
                    entity_updates[entity.id] = EntityUpdate(
                        entity_id=entity.id,
                        biological=BiologicalUpdate(sleep_debt_set=0.0, last_sleep_tick_set=state.tick),
                        combat=CombatUpdate(hp_delta=entity.combat.max_hp), # Fully heal
                        inventory=InventoryUpdate(gold_delta=-10), # Pay for inn
                        interaction=InteractionUpdate(reset=True)
                    )
                elif kind == "tavern":
                    # Hunger recovery
                    entity_updates[entity.id] = EntityUpdate(
                        entity_id=entity.id,
                        biological=BiologicalUpdate(hunger_set=0.0, last_meal_tick_set=state.tick),
                        inventory=InventoryUpdate(gold_delta=-5), # Pay for meal
                        interaction=InteractionUpdate(reset=True)
                    )
                elif kind == "guild":
                    # Intel and quest generation (Placeholder for now)
                    entity_updates[entity.id] = EntityUpdate(
                        entity_id=entity.id,
                        interaction=InteractionUpdate(reset=True),
                        property_updates={"visited_guild_tick": state.tick}
                    )
            else:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(progress_delta=1.0)
                )
                
        return StateUpdate(entity_updates=entity_updates)
