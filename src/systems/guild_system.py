from __future__ import annotations
from typing import Dict, List
import random
from src.core.state import AuthoritativeState, EntityState, BuildingState
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, StrategicUpdate
from src.core.strategic import LeadState, ConcernState

class GuildIntelSystem:
    """Emits strategic intel when heroes visit the guild."""

    @staticmethod
    def update(state: AuthoritativeState) -> StateUpdate:
        entity_updates = {}
        
        for entity in state.entities.values():
            if not entity.interaction or entity.interaction.target_node_id is None:
                continue
                
            if entity.properties.get("interaction_kind") != "guild":
                continue
                
            building_id = entity.interaction.target_node_id
            building = state.buildings.get(building_id)
            
            if not building or not building.functional:
                continue
                
            # Progress Check
            new_progress = entity.interaction.progress + 1.0
            if new_progress >= 10.0:
                # HERO GETS INTEL
                rng = random.Random(state.seed + state.tick + entity.id)
                
                # 1. Find the region with highest trauma or lowest stability
                high_risk_regions = sorted(
                    state.regions.values(), 
                    key=lambda r: r.trauma_score, 
                    reverse=True
                )
                
                leads_add = []
                concerns_add = []
                
                if high_risk_regions:
                    target = high_risk_regions[0]
                    # Create a Lead
                    from src.core.strategic import LeadCertainty
                    leads_add.append(LeadState(
                        id=f"guild_lead_{target.id}_{state.tick}",
                        kind="location",
                        subject=target.id,
                        detail=f"Danger reported in {target.name}",
                        discovered_tick=state.tick,
                        certainty=LeadCertainty.APPROXIMATE,
                        source_entity_id=building_id
                    ))
                    
                    # Create a Concern if trauma is very high
                    if target.trauma_score > 5.0:
                        concerns_add.append(ConcernState(
                            id=f"guild_concern_{target.id}",
                            kind="danger",
                            urgency=target.trauma_score / 10.0,
                            source=target.id,
                            created_tick=state.tick
                        ))
                
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True),
                    strategic=StrategicUpdate(
                        leads_add_or_update=leads_add,
                        concerns_add_or_update=concerns_add
                    )
                )
            else:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(progress_delta=1.0)
                )
                
        return StateUpdate(entity_updates=entity_updates)
