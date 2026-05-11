# src/engine/world_dynamics.py
# Phase 7 Implementation: Handles Regional Hazards, Calamities, and World Consequences (LEG-RPG-071/139).
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING
from src.core.updates import WorldUpdate, EntityUpdate, CombatUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, RegionState, EntityState
    from src.core.updates import StateUpdate
    from src.systems.world_systems.generator import EntityGenerator
    from src.engine.cadence import SystemCadence

class WorldDynamicsSystem:
    """
    Law: World-level consequences apply to all entities.
    Handles Regional Hazards and Calamity Scaling (LEG-RPG-071/139).
    VERIFIED v2: passive_world_progression
    """

    @staticmethod
    def resolve_dynamics(state: AuthoritativeState, update: StateUpdate, generator: EntityGenerator, cadence: SystemCadence | None = None) -> StateUpdate:
        """
        Apply regional effects to entities and update world markers.
        """
        # 1. Resolve Hazards & Environment (Entity-level impact)
        from src.world.environment import EnvironmentService
        from src.core.updates import BiologicalUpdate
        
        for e_id, entity in state.entities.items():
            if not entity.lifecycle.active: continue
            
            region = WorldDynamicsSystem._get_region_for_pos(state, entity.navigation.position)
            if not region:
                continue
            
            ent_upd = update.entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            # 1.1 HP Drain from Hazards (Authoritative calculation)
            # VERIFIED v2: regional_hazard_impact
            damage = EnvironmentService.calculate_hazard_drain(region, entity)
            if damage > 0:
                comb_upd = ent_upd.combat or CombatUpdate()
                ent_upd = replace(ent_upd,
                    combat=replace(comb_upd, 
                        hp_delta=comb_upd.hp_delta - damage,
                        outcome_kind="HAZARD"
                    )
                )

            # 1.2 Readiness Drain from Suppression
            if region.suppression_active:
                ent_upd = replace(ent_upd,
                    readiness_delta=ent_upd.readiness_delta - 5.0
                )
                
            # 1.3 Environmental Exposure (Biological Pressure)
            # Extreme weather adds to sleep debt (fatigue)
            exposure_mults = EnvironmentService.get_weather_multipliers(region)
            if exposure_mults.get("stamina_drain", 1.0) > 1.0:
                bio_upd = ent_upd.biological or BiologicalUpdate()
                ent_upd = replace(ent_upd,
                    biological=replace(bio_upd,
                        sleep_debt_delta=bio_upd.sleep_debt_delta + 1.0 # Extra fatigue
                    )
                )
            
            update.entity_updates[e_id] = ent_upd


        # 2. Resolve Trauma and Calamity Progression
        # 2.1 Death-triggered Trauma (LEG-RPG-139)
        for e_id, ent_upd in update.entity_updates.items():
            if ent_upd.combat and ent_upd.combat.alive_set is False:
                entity = state.entities.get(e_id)
                if entity:
                    region = WorldDynamicsSystem._get_region_for_pos(state, entity.navigation.position)
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
        from src.engine.cadence import SystemCadence as DefaultCadence, should_run
        cadence = cadence or DefaultCadence()
        
        if should_run(state.tick, None, cadence.world_dynamics):
            from src.world.calamity import CalamityService
            calamity_update = CalamityService.process_world_dynamics(state, generator)
            
            # 3.1 Standard Monster Replenishment
            from src.world.spawn import SpawnService
            spawn_update = SpawnService.process_spawns(state, generator)
            
            # 3.2 Resource Ecology (Replenishment)
            from src.world.ecology import ResourceEcologyService
            ecology_update = ResourceEcologyService.process_ecology(state, generator)

            # 3.3 Threat Evolution (LEG-RPG-071 Hardening)
            from src.world.threat import ThreatService
            for r_id, region in state.regions.items():
                t_upd = ThreatService.process_threat_evolution(state, region)
                if t_upd:
                    # Merge if existing
                    if r_id in update.world_updates:
                        update.world_updates[r_id] = update.world_updates[r_id].merge(t_upd)
                    else:
                        update.world_updates[r_id] = t_upd

            # 3.4 Boss Spawning (Deterministic & Idempotent)
            if should_run(state.tick, None, cadence.boss_spawn):
                from src.world.boss import BossService
                boss_spawn_update = BossService.check_for_boss_spawn(state, generator)
            else:
                from src.core.updates import StateUpdate as NewStateUpdate
                boss_spawn_update = NewStateUpdate()

            # 3.5 Process Raids
            from src.world.raid import RaidService
            raid_update = RaidService.check_for_raid(state, generator)

            # 3.6 Process Camps (Persistent Encampments)
            from src.world.camp import CampService
            camp_state_update = CampService.process_camps(state, generator)
            
            update = update.replace(
                maturity_set=calamity_update.maturity_set if calamity_update.maturity_set is not None else update.maturity_set,
                last_calamity_tick_set=calamity_update.last_calamity_tick_set if calamity_update.last_calamity_tick_set is not None else update.last_calamity_tick_set,
                entities_add=update.entities_add + calamity_update.entities_add + raid_update.entities_add + spawn_update.entities_add + boss_spawn_update.entities_add + camp_state_update.entities_add,
                nodes_add=update.nodes_add + ecology_update.nodes_add,
                camp_updates=camp_state_update.camp_updates,
                next_node_id_set=ecology_update.next_node_id_set or update.next_node_id_set,
                next_entity_id_set=generator._last_id + 1 if (generator._last_id + 1) > state.next_entity_id else None
            )


        # 4. Regional Transformations (Type Shifting)
        from src.world.transformation import TransformationService
        refined_world_updates = dict(update.world_updates)
        for r_id, region in state.regions.items():
            new_kind = TransformationService.get_potential_transformation(region)
            if new_kind and new_kind != region.kind:
                world_upd = refined_world_updates.get(r_id, WorldUpdate(region_id=r_id))
                refined_world_updates[r_id] = replace(world_upd, kind_set=new_kind)
        
        # 5. Global Object Lifecycle (LEG-RPG-002/005)
        from src.core.updates import ResourceNodeUpdate, ChestUpdate
        
        # 5.1 Nodes
        refined_node_updates = dict(update.node_updates)
        for n_id, node in state.resource_nodes.items():
            if node.cooldown_remaining > 0:
                n_upd = refined_node_updates.get(n_id, ResourceNodeUpdate(node_id=n_id))
                # If finished cooldown, recharge
                if node.cooldown_remaining == 1:
                     refined_node_updates[n_id] = replace(n_upd, 
                        cooldown_set=0,
                        charges_delta=node.max_charges
                    )
                else:
                     refined_node_updates[n_id] = replace(n_upd, cooldown_set=node.cooldown_remaining - 1)

        # 5.2 Chests
        refined_chest_updates = dict(update.chest_updates)
        for c_id, chest in state.chests.items():
            if chest.cooldown_remaining > 0:
                c_upd = refined_chest_updates.get(c_id, ChestUpdate(chest_id=c_id))
                refined_chest_updates[c_id] = replace(c_upd, cooldown_set=chest.cooldown_remaining - 1)
        
        # 5.3 Corpses & Ground Items (Decay)
        corpses_remove = list(update.corpses_remove)
        for cp_id, corpse in state.corpses.items():
            if state.tick >= corpse.decay_tick:
                corpses_remove.append(cp_id)

        return update.replace(
            world_updates=refined_world_updates,
            node_updates=refined_node_updates,
            chest_updates=refined_chest_updates,
            corpses_remove=corpses_remove
        )

    @staticmethod
    def _get_region_for_pos(state: AuthoritativeState, pos: tuple[float, float]) -> RegionState | None:
        px, py = pos
        for region in state.regions.values():
            xmin, ymin, xmax, ymax = region.bounds
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return region
        return None
