# src/engine/world_dynamics.py
# Phase 7 Implementation: Handles Regional Hazards, Calamities, and World Consequences (LEG-RPG-071/139).
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING
from src.core.updates import WorldUpdate, EntityUpdate, CombatUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, RegionState, EntityState
    from src.core.updates import StateUpdate
    from src.systems.generator import EntityGenerator

class WorldDynamicsSystem:
    """
    Law: World-level consequences apply to all entities.
    Handles Regional Hazards and Calamity Scaling (LEG-RPG-071/139).
    """

    @staticmethod
    def resolve_dynamics(state: AuthoritativeState, update: StateUpdate, generator: EntityGenerator) -> StateUpdate:
        """
        Apply regional effects to entities and update world markers.
        """
        # 1. Resolve Hazards (Entity-level impact)
        for e_id, entity in state.entities.items():
            if not entity.active: continue
            
            region = WorldDynamicsSystem._get_region_for_pos(state, entity.position)
            if not region:
                continue
            
            # 1.1 Readiness Drain from Suppression
            if region.suppression_active:
                ent_upd = update.entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                update.entity_updates[e_id] = replace(
                    ent_upd,
                    readiness_delta=ent_upd.readiness_delta - 5.0
                )
                
            # 1.2 HP Drain from Hazards (LEG-RPG-071)
            if region.hazard_level > 0:
                # Formula: 0.5 * hazard * (1 + intensity)
                damage = int(0.5 * region.hazard_level * (1.0 + region.calamity_intensity))
                if damage > 0:
                    ent_upd = update.entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                    comb_upd = ent_upd.combat or CombatUpdate()
                    update.entity_updates[e_id] = replace(
                        ent_upd,
                        combat=replace(comb_upd, 
                            hp_delta=comb_upd.hp_delta - damage,
                            outcome_kind="HAZARD"
                        )
                    )

        # 2. Resolve Trauma and Calamity Progression
        # 2.1 Death-triggered Trauma (LEG-RPG-139)
        for e_id, ent_upd in update.entity_updates.items():
            if ent_upd.combat and ent_upd.combat.alive_set is False:
                entity = state.entities.get(e_id)
                if entity:
                    region = WorldDynamicsSystem._get_region_for_pos(state, entity.position)
                    if region:
                        world_upd = update.world_updates.get(region.id, WorldUpdate(region_id=region.id))
                        # Each death adds 1.0 trauma
                        update.world_updates[region.id] = replace(
                            world_upd, 
                            trauma_delta=world_upd.trauma_delta + 1.0
                        )

        # 2.2 Calamity Progression (Hazard scaling)
        # Intense trauma scores (LEG-RPG-139) gradually increase hazard levels
        for r_id, region in state.regions.items():
            # Apply proposed trauma if any
            w_upd = update.world_updates.get(r_id)
            current_trauma = region.trauma_score + (w_upd.trauma_delta if w_upd else 0.0)
            
            if current_trauma > 50.0:
                new_hazard = min(1.0, region.hazard_level + 0.01)
                if new_hazard > region.hazard_level:
                    world_upd = update.world_updates.get(r_id, WorldUpdate(region_id=r_id))
                    update.world_updates[r_id] = replace(world_upd, hazard_level_set=new_hazard)

        # 3. Process Macro World Dynamics (Calamity Spawns, Maturity)
        from src.world.calamity import CalamityService
        calamity_update = CalamityService.process_world_dynamics(state, generator)
        
        # 3.5 Process Raids
        from src.world.raid import RaidService
        raid_update = RaidService.check_for_raid(state, generator)
        
        update = update.replace(
            maturity_set=calamity_update.maturity_set if calamity_update.maturity_set is not None else update.maturity_set,
            last_calamity_tick_set=calamity_update.last_calamity_tick_set if calamity_update.last_calamity_tick_set is not None else update.last_calamity_tick_set,
            entities_add=update.entities_add + calamity_update.entities_add + raid_update.entities_add
        )

        # 4. Regional Transformations (Type Shifting)
        from src.world.transformation import TransformationService
        refined_world_updates = dict(update.world_updates)
        for r_id, region in state.regions.items():
            new_kind = TransformationService.get_potential_transformation(region)
            if new_kind and new_kind != region.kind:
                world_upd = refined_world_updates.get(r_id, WorldUpdate(region_id=r_id))
                refined_world_updates[r_id] = replace(world_upd, kind_set=new_kind)
        
        update = update.replace(world_updates=refined_world_updates)

        return update

    @staticmethod
    def _get_region_for_pos(state: AuthoritativeState, pos: tuple[float, float]) -> RegionState | None:
        px, py = pos
        for region in state.regions.values():
            xmin, ymin, xmax, ymax = region.bounds
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return region
        return None
