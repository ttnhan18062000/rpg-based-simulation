from __future__ import annotations

from typing import Optional
from src.core.state import AuthoritativeState, EntityState
from src.quests.generator import QuestGenerator, QuestPressureProfile
from src.core.registries import ResourceRegistry
from src.core.strategic import LeadState, LeadCertainty
from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.core.enums import Domain
from src.platform.rng import DeterministicRNG

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
        rng = DeterministicRNG(state.seed)
        selected_leads = rng.sample(Domain.SOCIAL, state.tick, entity.id, potential_leads, min(2, len(potential_leads)))
        
        # 3. Create a quest if the entity has space
        new_projects = []
        if len(entity.strategic.projects) < entity.strategic.profile.max_active_projects:
            # Resolve region for pressure-driven quest selection.
            # Mirrors ResourceOpportunityProvider.get_opportunities() exactly:
            # src/world/providers/resources.py:40 (region fallback) and :60-66 (node->region match).
            region_id = getattr(entity.navigation, "region_id", None) or "hometown"
            region = state.regions.get(region_id) if getattr(state, "regions", None) else None

            trauma = min(1.0, region.trauma_score / 50.0) if region else 0.0
            hazard = region.hazard_level if region else 0.0

            # Scarcity ratio: average (1 - remaining_charges/max_charges) across resource nodes
            # whose ResourceRegistry definition tags them into this region -- same node/region
            # match as src/world/providers/resources.py:60-66, but aggregated into one scalar
            # instead of per-node Opportunity objects.
            # ResourceRegistry.get() raises KeyError on an unregistered kind (unlike a dict
            # .get()), so contains() is checked first -- nodes with an ad hoc/unregistered
            # `kind` (e.g. test fixtures) are skipped rather than crashing the visit.
            ratios = []
            for node in getattr(state, "resource_nodes", {}).values():
                if not ResourceRegistry.contains(node.kind):
                    continue
                res_def = ResourceRegistry.get(node.kind)
                if region_id in res_def.source_region_tags and node.max_charges > 0:
                    ratios.append(node.remaining_charges / node.max_charges)
            scarcity = (1.0 - (sum(ratios) / len(ratios))) if ratios else 0.0

            pressure_profile = QuestPressureProfile(trauma=trauma, hazard=hazard, scarcity=scarcity)

            # Generate 1 quest scaled to entity level
            building_id = 1000 # Dummy guild ID for now
            quests = QuestGenerator.generate_quests(
                seed=state.tick + entity.id,
                level=entity.identity.evolution_level,
                tick=state.tick,
                building_id=building_id,
                count=1,
                pressure_profile=pressure_profile,
                origin_pos=entity.navigation.position,
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
