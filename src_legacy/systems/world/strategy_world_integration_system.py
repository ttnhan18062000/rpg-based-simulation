"""World-tier strategic integration system. [PHASE 6]

This system manages shared strategic opportunities and broadcasts world-level 
pressures into the simulation.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src_legacy.systems.infrastructure.base import System
from src_legacy.core.models.enums import Faction, Material, StrategicStatus
from src_legacy.core.models.world_strategy import StrategicOpportunity, WorldObligation
from src_legacy.core.models.strategy import LeadRecord, LeadKind

if TYPE_CHECKING:
    from src_legacy.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)

class StrategicWorldIntegrationSystem(System):
    """Coordinates shared strategic pressures and broadcasted opportunities."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Process world-tier strategic shifts every 20 ticks."""
        if tick % 20 != 0:
            return

        self._update_territorial_opportunities(context)
        self._update_war_obligations(context)
        self._prune_expired_records(context)

    def _update_territorial_opportunities(self, context: SystemContext) -> None:
        """Create shared opportunities based on region control shifts."""
        world = context.world
        for region in world.regions:
            if region.terrain == Material.TOWN:
                continue

            control = world.region_control.get(region.region_id, 0.0)
            opp_id = f"opp_liberate_{region.region_id}"

            # If a region is conquered, create a 'Liberation' opportunity
            if control < -50.0 and region.owner_faction is not None:
                if opp_id not in world.strategic_registry.opportunities:
                    lead = LeadRecord(
                        lead_id=f"lead_opp_{opp_id}",
                        kind=LeadKind.LOCATION,
                        label=f"Liberate {region.name}",
                        subject=region.region_id,
                        target_coords=region.center,
                        source_type="world_system",
                        discovered_tick=world.tick
                    )
                    world.strategic_registry.opportunities[opp_id] = StrategicOpportunity(
                        opportunity_id=opp_id,
                        label=f"Liberation: {region.name}",
                        description=f"The region {region.name} has fallen to {region.owner_faction.name}. The Guild seeks liberators.",
                        lead=lead,
                        difficulty_rating=region.difficulty / 5.0,
                        created_tick=world.tick
                    )
                    logger.info("Created World Opportunity: %s", opp_id)
            
            # If a region is liberated, resolve the opportunity
            elif control > 50.0 and opp_id in world.strategic_registry.opportunities:
                opp = world.strategic_registry.opportunities[opp_id]
                if opp.status == StrategicStatus.ACTIVE:
                    opp.status = StrategicStatus.RESOLVED
                    logger.info("Resolved World Opportunity: %s", opp_id)

    def _update_war_obligations(self, context: SystemContext) -> None:
        """Create world-level obligations during wartime."""
        world = context.world
        for f_id, at_war in world.war_status.items():
            obl_id = f"obl_war_{f_id}"
            if at_war:
                if obl_id not in world.strategic_registry.obligations:
                    faction_name = Faction(f_id).name
                    world.strategic_registry.obligations[obl_id] = WorldObligation(
                        obligation_id=obl_id,
                        label=f"War Duty: {faction_name}",
                        description=f"The town is at war with {faction_name}! All heroes are called to defend.",
                        faction_restriction=int(Faction.HERO_GUILD),
                        priority_mult=2.0,
                        created_tick=world.tick
                    )
                    logger.info("Broadcasted World Obligation: %s", obl_id)
            else:
                if obl_id in world.strategic_registry.obligations:
                    # Obligations simply expire or are removed when peace is signed
                    del world.strategic_registry.obligations[obl_id]
                    logger.info("Withdrew World Obligation: %s", obl_id)

    def _prune_expired_records(self, context: SystemContext) -> None:
        """Remove old or non-active shared strategic data."""
        registry = context.world.strategic_registry
        tick = context.world.tick
        
        # Prune opportunities
        to_remove = []
        for opp_id, opp in registry.opportunities.items():
            if opp.status in (StrategicStatus.RESOLVED, StrategicStatus.ABANDONED):
                # Keep resolved for a few ticks?
                if tick - (opp.created_tick) > 200: 
                    to_remove.append(opp_id)
            elif opp.expires_tick and tick >= opp.expires_tick:
                to_remove.append(opp_id)
        
        for oid in to_remove:
            del registry.opportunities[oid]
