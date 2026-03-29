from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.systems.infrastructure.base import System
from src.core.models.enums import Faction, AIState, Material
from src.core.entities.entity import Entity, Stats, Vector2

if TYPE_CHECKING:
    from src.systems.infrastructure.base import SystemContext

logger = logging.getLogger(__name__)

class StrategySystem(System):
    """Milestone 7: Strategic layer for Faction Wars and Territory Conquest."""

    def on_tick(self, context: SystemContext, tick: int) -> None:
        """Process strategic shifts every 10 ticks (faster feedback than 100)."""
        if tick % 10 != 0:
            return

        self._process_deaths(context)
        self._update_war_status(context)
        self._update_region_control(context)
        self._apply_regional_effects(context)

    def _process_deaths(self, context: SystemContext) -> None:
        """Shift region control based on recent deaths."""
        to_clear = []
        for (fac_id, reg_id), count in context.world.faction_deaths_per_region.items():
            # Shift influence: Hero death = -5.0, Monster death = +5.0
            shift = 5.0 * count
            if fac_id == int(Faction.HERO_GUILD):
                context.world.region_control[reg_id] = context.world.region_control.get(reg_id, 0.0) - shift
            else:
                context.world.region_control[reg_id] = context.world.region_control.get(reg_id, 0.0) + shift
            
            # Clamp Influence
            context.world.region_control[reg_id] = max(-100.0, min(100.0, context.world.region_control[reg_id]))
            to_clear.append((fac_id, reg_id))

        # We clear deaths in WorldLoop currently, but let's shift it here soon.
        # Actually, let's just clear what we processed.
        for key in to_clear:
            context.world.faction_deaths_per_region[key] = 0

    def _apply_regional_effects(self, context: SystemContext) -> None:
        """Apply Stronghold Auras and Regional Influence to entities."""
        from src.core.world.regions import find_region_at
        from src.core.gameplay.effects import EffectType, conquered_debuff

        # Pillar 5: Static Influence (Stronghold Auras)
        # We optimize by finding all active strongholds first
        strongholds = [e for e in context.world.entities.values() if e.kind == "stronghold" and e.combat.alive]
        
        for ent in context.world.entities.values():
            if not ent.combat.alive or ent.kind in ("generator", "stronghold"):
                continue
                
            region = find_region_at(ent.spatial.pos, context.world.regions)
            if not region:
                continue
            
            # 1. Stronghold Aura: Proximity based (Dist < 10) or Region-wide if conquered
            local_stronghold = next((s for s in strongholds if ent.spatial.pos.manhattan(s.spatial.pos) < 12), None)
            
            if ent.identity.faction == Faction.HERO_GUILD and local_stronghold:
                # Hero is under the shadow of a stronghold
                if not any(e.effect_type == EffectType.CONQUERED_DEBUFF for e in ent.combat.effects):
                    # Rename conceptually to 'Aura of Despair' or keep debuff class
                    ent.combat.effects.append(conquered_debuff(duration=5))
                    logger.debug(f"Tick {context.world.tick}: Hero {ent.id} affected by Stronghold Aura at {local_stronghold.spatial.pos}")
            else:
                # Remove if out of range
                ent.combat.effects = [e for e in ent.combat.effects if e.effect_type != EffectType.CONQUERED_DEBUFF]
            
            # 2. Regional Fatigue (Pillar 6 integration for Goal scoring)
            # This is handled in AIBrain/GoalEvaluator, but we can update world-state influence here

    def _update_war_status(self, context: SystemContext) -> None:
        """Handle transition to WAR state based on aggression."""
        for f_id, agg in context.world.faction_aggression.items():
            was_at_war = context.world.war_status.get(f_id, False)
            is_at_war = agg >= 80.0
            
            if is_at_war and not was_at_war:
                context.world.war_status[f_id] = True
                from src.core.data.events import WarEvent
                if hasattr(context.world, "event_bus") and context.world.event_bus:
                    context.world.event_bus.publish(WarEvent(faction_id=f_id, is_declared=True, aggression=agg))
                if context.emit:
                    context.emit("war", f"FACTION {Faction(f_id).name} HAS DECLARED WAR ON THE TOWN!",
                                metadata={"faction_id": f_id, "aggression": agg})
            elif not is_at_war and was_at_war:
                # Optional: Peace transition if aggression drops below 50
                if agg < 50.0:
                    context.world.war_status[f_id] = False
                    from src.core.data.events import WarEvent
                    if hasattr(context.world, "event_bus") and context.world.event_bus:
                        context.world.event_bus.publish(WarEvent(faction_id=f_id, is_declared=False, aggression=agg))
                    if context.emit:
                        context.emit("peace", f"FACTION {Faction(f_id).name} has signed a temporary truce.",
                                    metadata={"faction_id": f_id, "aggression": agg})

    def _update_region_control(self, context: SystemContext) -> None:
        """Evaluate territory ownership based on control index."""
        for region in context.world.regions:
            # Town region is always neutral/sanctuary
            if region.terrain == Material.TOWN:
                continue

            control = context.world.region_control.get(region.region_id, 0.0)
            
            # Conquest by Monsters: Influence < -50
            if control < -50.0 and region.owner_faction is None:
                # Find the most likely owner (simplification for now: matching terrain)
                from src.core.gameplay.faction import FactionRegistry
                owner = context.identity.tile_owner(region.terrain)
                if owner:
                    region.owner_faction = owner
                    self._spawn_stronghold(context, region)
                    from src.core.data.events import ConquestEvent
                    if hasattr(context.world, "event_bus") and context.world.event_bus:
                        context.world.event_bus.publish(ConquestEvent(
                            region_id=region.region_id, region_name=region.name, 
                            old_owner=None, new_owner=owner.name, is_liberation=False
                        ))
                    if context.emit:
                        context.emit("conquest", f"REGION {region.name} HAS FALLEN TO {owner.name}!",
                                    metadata={"region_id": region.region_id, "owner": owner.name})

            # Liberation by Heroes: Influence > 50
            elif control > 50.0 and region.owner_faction is not None:
                old_owner = region.owner_faction
                region.owner_faction = None
                self._remove_stronghold(context, region)
                from src.core.data.events import ConquestEvent
                if hasattr(context.world, "event_bus") and context.world.event_bus:
                    context.world.event_bus.publish(ConquestEvent(
                        region_id=region.region_id, region_name=region.name, 
                        old_owner=old_owner.name, new_owner=None, is_liberation=True
                    ))
                if context.emit:
                    context.emit("liberation", f"REGION {region.name} HAS BEEN LIBERATED FROM {old_owner.name}!",
                                metadata={"region_id": region.region_id, "liberator": "HERO_GUILD"})

    def _spawn_stronghold(self, context: SystemContext, region: any) -> None:
        """Spawn a defensive fortification that heroes must destroy to retake the region."""
        from src.core.entities.entity_builder import EntityBuilder
        builder = EntityBuilder(context.rng, context.world.allocate_entity_id(), context.world.tick)
        stronghold = (
            builder
            .kind("stronghold")
            .at(region.center)
            .faction(region.owner_faction)
            .ai_state(AIState.IDLE)
            .with_base_stats(
                hp=2000,
                atk=0, def_=50, spd=0,
                level=region.difficulty * 5
            )
            .build()
        )
        context.world.add_entity(stronghold)
        logger.info("Spawned Stronghold at %s for faction %s", region.name, region.owner_faction)

    def _remove_stronghold(self, context: SystemContext, region: any) -> None:
        """Find and remove the stronghold in this region."""
        to_remove = []
        for ent in context.world.entities.values():
            if ent.kind == "stronghold" and ent.spatial.pos == region.center:
                to_remove.append(ent.id)
        
        for eid in to_remove:
            context.world.remove_entity(eid)

    def is_conquered(self, context: SystemContext, region_id: str) -> bool:
        """Helper to check if a region is currently conquered."""
        return context.world.region_control.get(region_id, 0.0) <= -80.0
