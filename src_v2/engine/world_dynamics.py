# src_v2/engine/world_dynamics.py
# Phase 7 Implementation: Handles Regional Hazards, Calamities, and World Consequences (LEG-RPG-071/139).
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING
from src_v2.core.updates import WorldUpdate, EntityUpdate, CombatUpdate

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, RegionState, EntityState
    from src_v2.core.updates import StateUpdate

class WorldDynamicsSystem:
    """
    Law: World-level consequences apply to all entities.
    Handles Regional Hazards and Calamity Scaling (LEG-RPG-071/139).
    """

    @staticmethod
    def resolve_dynamics(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Apply regional effects to entities and update world markers.
        """
        # 1. Resolve Hazards (Entity-level impact)
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            
            region = WorldDynamicsSystem._get_region_for_pos(state, entity.position)
            if not region:
                continue
            
            # HP Drain from Hazard
            if region.hazard_level > 0:
                # Formula: hazard_level * 10 * (1.0 + calamity_intensity)
                # Calamity intensity acts as a multiplier for regional danger
                base_drain = region.hazard_level * 10.0
                calamity_bonus = base_drain * region.calamity_intensity
                total_drain = int(base_drain + calamity_bonus)
                
                if total_drain > 0:
                    ent_upd = update.entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                    combat_upd = ent_upd.combat or CombatUpdate()
                    update.entity_updates[e_id] = replace(
                        ent_upd,
                        combat=replace(combat_upd, hp_delta=combat_upd.hp_delta - total_drain)
                    )

            # Readiness Drain from Suppression
            if region.suppression_active:
                ent_upd = update.entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                update.entity_updates[e_id] = replace(
                    ent_upd,
                    readiness_delta=ent_upd.readiness_delta - 5.0
                )

        # 2. Resolve Calamity Progression (World-level impact)
        # Intense trauma scores (LEG-RPG-139) gradually increase hazard levels
        for r_id, region in state.regions.items():
            if region.trauma_score > 50.0:
                new_hazard = min(1.0, region.hazard_level + 0.01)
                if new_hazard > region.hazard_level:
                    world_upd = update.world_updates.get(r_id, WorldUpdate(region_id=r_id))
                    update.world_updates[r_id] = replace(world_upd, hazard_level_set=new_hazard)

        return update

    @staticmethod
    def _get_region_for_pos(state: AuthoritativeState, pos: tuple[float, float]) -> RegionState | None:
        px, py = pos
        for region in state.regions.values():
            xmin, ymin, xmax, ymax = region.bounds
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return region
        return None
