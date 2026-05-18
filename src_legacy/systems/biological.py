from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING

from src_legacy.core.updates import BiologicalUpdate, EntityUpdate, CombatUpdate

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState
    from src_legacy.core.updates import StateUpdate

class BiologicalSystem:
    """
    Authoritative handler for biological pressures (Hunger, Sleep).
    Pillar 1.3: Routine & Biological Cycle.
    """

    @staticmethod
    def resolve_pressures(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Passive progression of hunger and sleep debt for all active entities.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        # Scaling factors (Parity with V1 logic)
        HUNGER_RATE = 0.01 # 1.0 per 100 ticks
        SLEEP_RATE = 0.005 # 1.0 per 200 ticks
        
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            
            # Entities with no biological component (e.g. ghosts, static items) are skipped
            # (Assuming HERO and CITIZEN always have it)
            if not hasattr(entity, "biological"): continue
            
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            bio_upd = ent_upd.biological or BiologicalUpdate()

            # 1. Passive Increase
            new_hunger = bio_upd.hunger_delta + HUNGER_RATE
            new_sleep = bio_upd.sleep_debt_delta + SLEEP_RATE
            
            # 2. Consequences: Starvation (Phase 2)
            comb_upd = ent_upd.combat or CombatUpdate()
            if entity.biological.hunger > 90.0:
                # Gradual drain
                comb_upd = replace(comb_upd, hp_delta=comb_upd.hp_delta - 1)
            if entity.biological.hunger >= 100.0:
                # Lethal drain
                comb_upd = replace(comb_upd, hp_delta=comb_upd.hp_delta - 10, outcome_kind="STARVATION")
            
            refined_entity_updates[e_id] = replace(
                ent_upd,
                combat=comb_upd if comb_upd != (ent_upd.combat or CombatUpdate()) else ent_upd.combat,
                biological=replace(
                    bio_upd,
                    hunger_delta=new_hunger,
                    sleep_debt_delta=new_sleep
                )
            )
            
        return replace(update, entity_updates=refined_entity_updates)
