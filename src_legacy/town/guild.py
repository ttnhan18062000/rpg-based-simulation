from __future__ import annotations
import random
from typing import Optional
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.quests.generator import QuestGenerator
from src_legacy.core.strategic import LeadState, LeadCertainty
from src_legacy.core.updates import StateUpdate, EntityUpdate, StrategicUpdate

class GuildAction:
    """Action to visit the Guild for quests and world intelligence."""

    @staticmethod
    def visit(entity: EntityState, state: AuthoritativeState) -> Optional[StateUpdate]:
        """
        Scan world state and provide 1-2 new strategic leads.
        Deterministic: Uses world state and entity identity.
        """
        # 1. Gather potential intelligence
        # Find some resource nodes the entity doesn't have leads for
        potential_leads = []
        
        # Example: Find Iron Nodes
        for node in state.resource_nodes.values():
            if node.kind == "iron":
                lead_id = f"iron_lead_{node.id}"
                if lead_id not in entity.strategic.leads:
                    potential_leads.append(
                        LeadState(
                            id=lead_id,
                            kind="location",
                            subject="iron_ore",
                            detail=f"Rumors of iron near {node.position}",
                            discovered_tick=state.tick,
                            certainty=LeadCertainty.VAGUE,
                            source_entity_id=None # GUILD
                        )
                    )
                    
        # 2. Select 1-2 leads (Deterministic choice based on seed + entity ID)
        rng = random.Random(state.seed + entity.id + state.tick)
        selected_leads = rng.sample(potential_leads, min(2, len(potential_leads)))
        
        # 3. Create a quest if the entity has space
        new_projects = []
        if len(entity.strategic.projects) < entity.strategic.profile.max_active_projects:
            # Generate 1 quest scaled to entity level
            building_id = 1000 # Dummy guild ID for now
            quests = QuestGenerator.generate_quests(
                seed=state.tick + entity.id,
                level=entity.identity.evolution_level,
                tick=state.tick,
                building_id=building_id,
                count=1
            )
            new_projects.extend(quests)
            
        if not selected_leads and not new_projects:
            return None
            
        # 4. Emit StrategicUpdate
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    strategic=StrategicUpdate(
                        leads_add_or_update=selected_leads,
                        projects_add_or_update=new_projects
                    )
                )
            }
        )
