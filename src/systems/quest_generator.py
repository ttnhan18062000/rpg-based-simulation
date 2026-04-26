from __future__ import annotations
import random
from typing import List, Optional
from src.core.state import AuthoritativeState, EntityState, Faction
from src.core.quests import QuestState, QuestKind, QuestStatus

class QuestGenerator:
    """Generates dynamic quests based on the current world state."""

    @staticmethod
    def generate_for_entity(entity: EntityState, state: AuthoritativeState) -> List[QuestState]:
        """Generate a pool of potential quests for an entity."""
        rng = random.Random(state.seed + state.tick + entity.id)
        quests = []
        
        # 1. Explore Quest
        # Find a region far from the entity or with low stability
        unstable_regions = [r for r in state.regions.values() if r.stability < 0.8]
        if unstable_regions:
            target_region = rng.choice(unstable_regions)
            quests.append(QuestState(
                id=f"explore_{target_region.id}_{state.tick}",
                kind=QuestKind.EXPLORE,
                title=f"Scout {target_region.name}",
                target_position=(
                    (target_region.bounds[0] + target_region.bounds[2]) / 2,
                    (target_region.bounds[1] + target_region.bounds[3]) / 2
                ),
                reward_gold=50,
                reward_xp=100
            ))
            
        # 2. Bounty Quest
        # Find a monster camp or stronghold
        for region in state.regions.values():
            if region.owner_faction_id == Faction.MONSTER:
                quests.append(QuestState(
                    id=f"bounty_{region.id}_{state.tick}",
                    kind=QuestKind.BOUNTY,
                    title=f"Liberate {region.name}",
                    target_id=region.id,
                    reward_gold=200,
                    reward_xp=500
                ))
                break # Only one bounty for now
                
        # 3. Harvest Quest
        # If world has low global resources
        if state.global_resources.get("iron_ore", 0) < 100:
            quests.append(QuestState(
                id=f"harvest_iron_{state.tick}",
                kind=QuestKind.HARVEST,
                title="Secure Iron Supply",
                target_item_id="iron_ore",
                target_quantity=10,
                reward_gold=100,
                reward_xp=150
            ))
            
        return quests
