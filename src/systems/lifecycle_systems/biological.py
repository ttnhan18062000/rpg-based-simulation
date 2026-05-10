from __future__ import annotations
from typing import Dict
from src.core.state import AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate, BiologicalUpdate, CombatUpdate

class BiologicalSystem:
    """Simulates biological decay (hunger, sleep) over time."""

    @staticmethod
    def update(state: AuthoritativeState) -> StateUpdate:
        entity_updates = {}
        
        for entity in state.entities.values():
            if not entity.lifecycle.active:
                continue
                
            # Only certain entities have biological needs (Heroes, maybe certain Monsters)
            if entity.kind not in ["HERO", "VILLAGER"]:
                continue
                
            # 1. Hunger Decay (0.5% per tick)
            hunger_delta = 0.5
            
            # 2. Sleep Debt Decay (0.3% per tick)
            sleep_delta = 0.3
            
            # 3. Penalties at high values
            hp_delta = 0
            if entity.biological.hunger > 90:
                hp_delta -= 1 # Starvation damage
            if entity.biological.sleep_debt > 95:
                hp_delta -= 1 # Exhaustion damage
                
            entity_updates[entity.id] = EntityUpdate(
                entity_id=entity.id,
                biological=BiologicalUpdate(
                    hunger_delta=hunger_delta,
                    sleep_debt_delta=sleep_delta
                ),
                combat=CombatUpdate(hp_delta=hp_delta) if hp_delta < 0 else None
            )
            
        return StateUpdate(entity_updates=entity_updates)
