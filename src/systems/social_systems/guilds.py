from __future__ import annotations
from typing import Dict, List

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
                
            if entity.interaction.kind != "guild":
                continue
                
            building_id = entity.interaction.target_node_id
            building = state.buildings.get(building_id)
            
            if not building or not building.functional:
                continue
                
            # Progress Check
            new_progress = entity.interaction.progress + 1.0
            if new_progress >= 10.0:
                # 1. Find the region with highest trauma or lowest stability
                high_risk_regions = sorted(
                    state.regions.values(), 
                    key=lambda r: r.trauma_score, 
                    reverse=True
                )
                
                leads_add = []
                beliefs_add = []
                concerns_add = []
                
                if high_risk_regions:
                    target = high_risk_regions[0]
                    # Create rumor belief and lead
                    from src.systems.strategic_systems.belief import BeliefCycleSystem
                    rumor_up = BeliefCycleSystem.process_rumor(
                        entity,
                        target.id,
                        f"Danger reported in {target.name}",
                        building_id,
                        state.tick
                    )
                    leads_add.extend(rumor_up.leads_add_or_update)
                    beliefs_add.extend(rumor_up.beliefs_add_or_update)
                    
                    # Log belief creation event
                    import logging
                    logger = logging.getLogger(__name__)
                    for b in rumor_up.beliefs_add_or_update:
                        logger.debug(
                            f"[Tick {state.tick}] BeliefCreated: Entity {entity.id} acquired rumor "
                            f"belief '{b.id}' about {b.subject} with certainty {b.certainty:.2f} from source {building_id}"
                        )
                    
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
                        beliefs_add_or_update=beliefs_add,
                        concerns_add_or_update=concerns_add
                    )
                )
            else:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(progress_delta=1.0)
                )
                
        return StateUpdate(entity_updates=entity_updates)
