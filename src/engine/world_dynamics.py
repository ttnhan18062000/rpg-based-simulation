# Compliance IDs: AUTH-001, AUTH-004, AUTH-020, COMBAT-012, COMBAT-026, DATA-003, DATA-015, DATA-016, DATA-026, DATA-037, DATA-038, DATA-048, DATA-095, DATA-105, DATA-116, DATA-125, DATA-126, DATA-127, DATA-128, INFRA-016, INFRA-045, INFRA-048, INFRA-078, INFRA-118, INFRA-119, INFRA-127, INFRA-153, INFRA-154, STRAT-032, STRAT-048, STRAT-053, STRAT-074, STRAT-136, WORLD-001, WORLD-002, WORLD-006, WORLD-011, WORLD-014, WORLD-016, WORLD-019, WORLD-020, WORLD-021, WORLD-029, WORLD-032, WORLD-041, WORLD-044, WORLD-046, WORLD-049, WORLD-050, WORLD-051, WORLD-053, WORLD-054, WORLD-055, WORLD-056, WORLD-057, WORLD-058, WORLD-060, WORLD-072, WORLD-074, WORLD-104, WORLD-105, WORLD-106, WORLD-107, WORLD-108, WORLD-109, WORLD-110, WORLD-111, WORLD-113, WORLD-114, WORLD-115, WORLD-116, WORLD-117, WORLD-120, WORLD-123, WORLD-125, WORLD-126, WORLD-130, WORLD-131, WORLD-132, WORLD-134, WORLD-135, WORLD-136, WORLD-137, WORLD-138, WORLD-202, WORLD-203, WORLD-207, WORLD-208, WORLD-209, WORLD-210, WORLD-215, WORLD-216, WORLD-217, WORLD-218, WORLD-219, WORLD-222, WORLD-223, WORLD-224, WORLD-225, WORLD-226, WORLD-227, WORLD-228, WORLD-229, WORLD-247, WORLD-248
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
        # Regional hazards and environment impact evaluation
        from src.world.environment import EnvironmentService
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            if entity.combat and entity.combat.alive and entity.lifecycle and entity.lifecycle.active:
                region = WorldDynamicsSystem._get_region_for_pos(state, entity.navigation.position)
                if region:
                    hazard_dmg = EnvironmentService.calculate_hazard_drain(region, entity)
                    if hazard_dmg > 0:
                        e_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                        c_upd = e_upd.combat or CombatUpdate()
                        new_hp = max(0, entity.combat.hp + c_upd.hp_delta - hazard_dmg)
                        c_upd = replace(c_upd, hp_delta=c_upd.hp_delta - hazard_dmg, outcome_kind="HAZARD", alive_set=(new_hp > 0))
                        refined_entity_updates[e_id] = replace(e_upd, combat=c_upd)
        update = update.replace(entity_updates=refined_entity_updates)


        # 2.1 Death-triggered Trauma & Sovereignty (LEG-RPG-071/139)
        from src.core.enums import Faction
        for e_id, ent_upd in update.entity_updates.items():
            if ent_upd.combat and ent_upd.combat.alive_set is False:
                entity = state.entities.get(e_id)
                if entity:
                    region = WorldDynamicsSystem._get_region_for_pos(state, entity.navigation.position)
                    if region:
                        world_upd = update.world_updates.get(region.id, WorldUpdate(region_id=region.id))
                        
                        # Each death adds 1.0 trauma
                        new_trauma_delta = world_upd.trauma_delta + 1.0
                            
                        update.world_updates[region.id] = replace(
                            world_upd, 
                            trauma_delta=new_trauma_delta
                        )

        # 2.2 Ownership & Calamity Progression
        from src.world.influence import _region_owner_faction_id_str
        from src.content_semantics.faction import get_faction_semantics_service as _get_sem
        _sem = _get_sem()
        for r_id, region in state.regions.items():
            w_upd = update.world_updates.get(r_id)

            # Apply proposed trauma/influence if any
            current_trauma = region.trauma_score + (w_upd.trauma_delta if w_upd else 0.0)
            current_influence = region.influence + (w_upd.influence_delta if w_upd else 0.0)

            world_upd = w_upd or WorldUpdate(region_id=r_id)
            changed = False

            owner_fid = _region_owner_faction_id_str(region.owner_faction_id)

            # Ownership Law: Threshold of 100/-100 for control
            if current_influence >= 100.0 and (owner_fid is None or not _sem.is_protector(owner_fid)):
                world_upd = replace(world_upd, owner_faction_id_set=Faction.HERO_GUILD)
                changed = True
            elif current_influence <= -100.0 and (owner_fid is None or not _sem.is_invader(owner_fid)):
                world_upd = replace(world_upd, owner_faction_id_set=Faction.MONSTER_HORDE)
                changed = True
            
            # Hazard scaling (LEG-RPG-139)
            if current_trauma > 50.0:
                new_hazard = min(1.0, region.hazard_level + 0.01)
                if new_hazard > region.hazard_level:
                    world_upd = replace(world_upd, hazard_level_set=new_hazard)
                    changed = True
            
            if changed or w_upd:
                update.world_updates[r_id] = world_upd

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

            # 3.7 Demographic Birth/Death Cycle (E52A)
            from src.domains.demographics.cohort import DemographicCycleService
            demo_update = DemographicCycleService.process_demographics(state, state.tick)

            update = update.replace(
                maturity_set=calamity_update.maturity_set if calamity_update.maturity_set is not None else update.maturity_set,
                last_calamity_tick_set=calamity_update.last_calamity_tick_set if calamity_update.last_calamity_tick_set is not None else update.last_calamity_tick_set,
                entities_add=update.entities_add + calamity_update.entities_add + raid_update.entities_add + spawn_update.entities_add + boss_spawn_update.entities_add + camp_state_update.entities_add,
                nodes_add=update.nodes_add + ecology_update.nodes_add,
                camp_updates=camp_state_update.camp_updates,
                next_node_id_set=ecology_update.next_node_id_set or update.next_node_id_set,
                next_entity_id_set=generator._last_id + 1 if (generator._last_id + 1) > state.next_entity_id else None
            )
            # Merge demographic world_updates into the main update
            if not demo_update.is_noop():
                update = update.merge(demo_update)


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
        from src.engine.spatial_query import SpatialQueryService
        return SpatialQueryService.get_region_at(state, pos)
