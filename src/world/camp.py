# Compliance IDs: WORLD-030, WORLD-031
# src/world/camp.py
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Dict, List
from src.core.updates import StateUpdate, CampUpdate, WorldUpdate
from src.core.enums import Domain, EntityRole

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, CampState
    from src.systems.world_systems.generator import EntityGenerator

class CampService:
    """
    Manages persistent world encampments, their maturity, and associated spawns.
    """

    MATURITY_PER_TICK = 0.05
    RAID_MATURITY_THRESHOLD = 80.0
    CAMP_SPAWN_INTERVAL = 30
    NEST_RACE_KINDS = frozenset({"wolf", "spider", "troll", "slime"})
    EXPAND_TERRITORY_MATURITY_BOOST = 1.0

    @staticmethod
    def process_camps(state: AuthoritativeState, generator: EntityGenerator, faction_directives: list | None = None) -> StateUpdate:
        """
        Evolve camps and spawn monsters or raids.
        """
        camp_updates: Dict[str, CampUpdate] = {}
        entities_add = []
        world_updates: Dict[str, WorldUpdate] = {}
        flags = getattr(state, "feature_flags", None) or {}

        # 1. Maturity Evolution
        for c_id, camp in state.camps.items():
            if not camp.active:
                continue
                
            m_delta = CampService.MATURITY_PER_TICK
            
            # Rule: High regional trauma increases maturity faster
            from src.engine.legality import LegalityServiceV2
            region = LegalityServiceV2.get_region_for_position(camp.position, state)
            if region and region.trauma_score > 50.0:
                m_delta *= 1.5
                
            camp_updates[c_id] = CampUpdate(id=c_id, maturity_delta=m_delta)

            # 1b. Faction EXPAND_TERRITORY consumption: a matching directive boosts maturity growth.
            if faction_directives and region is not None:
                from src.engine.faction_constants import EXPAND_TERRITORY
                for directive in faction_directives:
                    if getattr(directive, "directive_kind", None) == EXPAND_TERRITORY and directive.target_region == region.id:
                        existing = camp_updates[c_id]
                        camp_updates[c_id] = replace(
                            existing,
                            maturity_delta=existing.maturity_delta + CampService.EXPAND_TERRITORY_MATURITY_BOOST,
                        )
                        break

            # 2. Camp-based Spawning
            if state.tick % CampService.CAMP_SPAWN_INTERVAL == 0:
                # Count monsters near camp
                mobs_near = [e for e in state.entities.values() 
                             if e.identity.role == EntityRole.MONSTER and e.combat.alive
                             and abs(e.navigation.position[0] - camp.position[0]) < 10
                             and abs(e.navigation.position[1] - camp.position[1]) < 10]
                
                # Rule: Camp spawns monsters up to maturity/10 (min 2)
                cap = max(2, int(camp.maturity / 10.0))
                if len(mobs_near) < cap:
                    mob = generator.spawn_monster(
                        camp.position,
                        state=state,
                        kind="goblin_warrior" if camp.kind == "goblin" else "orc_warrior",
                        difficulty_tier=int(camp.maturity / 20.0) + 1
                    )
                    entities_add.append(mob)
            
            # 3. Raid Trigger (or Nest Spread, for Nest-classified camps with the flag ON)
            if camp.maturity >= CampService.RAID_MATURITY_THRESHOLD:
                # Check if enough time has passed since last raid
                if state.tick - camp.last_raid_tick >= 500: # 5 days
                    is_nest_spread = (
                        flags.get("ENABLE_CAMP_NEST_SPREAD", "OFF") == "ON"
                        and camp.kind in CampService.NEST_RACE_KINDS
                    )
                    if is_nest_spread:
                        offspring = generator.spawn_natural_creature_offspring(
                            camp.position,
                            state=state,
                            kind=camp.kind,
                            difficulty_tier=int(camp.maturity / 20.0) + 1,
                            birth_tick=state.tick,
                        )
                        entities_add.append(offspring)
                        camp_updates[c_id] = CampUpdate(
                            id=c_id,
                            maturity_delta=-20.0,  # same cost as raiding, per ticket's "reuses timing" requirement
                            last_raid_tick_set=state.tick
                        )
                    else:
                        # Trigger a raid from this camp!
                        from src.world.raid import RaidService
                        # For now, we reuse RaidService logic but anchored here
                        raid_update = RaidService.check_for_raid(state, generator)
                        # Adjust positions to camp
                        for mob in raid_update.entities_add:
                            # We can't easily mutate the update list, so we just add them
                            # but in a real system we'd pass the origin.
                            # For now, let's just mark the last_raid_tick.
                            pass

                        camp_updates[c_id] = CampUpdate(
                            id=c_id,
                            maturity_delta=-20.0, # Cost of raiding
                            last_raid_tick_set=state.tick
                        )

            # 4. Natural-Creature Reproduction
            if flags.get("ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH", "OFF") == "ON":
                if (camp.maturity >= CampService.RAID_MATURITY_THRESHOLD
                        and state.tick % CampService.CAMP_SPAWN_INTERVAL == 0):
                    eligible = True
                    if region is not None and region.population_cohorts:
                        young = region.population_cohorts.get("young")
                        threshold = young.migration_threshold if young is not None else 0.7
                        from src.domains.demographics.cohort import compute_regional_scarcity
                        scarcity = compute_regional_scarcity(region.id, state)
                        eligible = scarcity <= threshold
                    if eligible:
                        offspring = generator.spawn_natural_creature_offspring(
                            camp.position,
                            state=state,
                            kind="goblin_warrior" if camp.kind == "goblin" else "orc_warrior",
                            difficulty_tier=int(camp.maturity / 20.0) + 1,
                            birth_tick=state.tick,
                        )
                        entities_add.append(offspring)
                        if region is not None:
                            # TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE: coarse +1
                            # nudge, additive across camps in this call — must merge, not
                            # overwrite, or a second eligible camp in the same region on the
                            # same tick would silently drop the first camp's nudge.
                            nudge = WorldUpdate(region_id=region.id, population_young_births_delta=1)
                            if region.id in world_updates:
                                world_updates[region.id] = world_updates[region.id].merge(nudge)
                            else:
                                world_updates[region.id] = nudge

        return StateUpdate(camp_updates=camp_updates, entities_add=entities_add, world_updates=world_updates)

    @staticmethod
    def resolve_camp_clearing(state: AuthoritativeState, camp_id: str) -> StateUpdate:
        """
        Rule: Clearing a camp provides rewards and reduces threat.
        """
        camp = state.camps.get(camp_id)
        if not camp or not camp.active:
            return StateUpdate()
            
        camp_updates = {camp_id: CampUpdate(id=camp_id, active_set=False)}
        
        from src.engine.legality import LegalityServiceV2
        region = LegalityServiceV2.get_region_for_position(camp.position, state)
        if not region:
            return StateUpdate(camp_updates=camp_updates)
            
        from src.core.updates import WorldUpdate
        w_upd = WorldUpdate(
            region_id=region.id,
            trauma_delta=-10.0 # Reward for clearing
        )
        
        return StateUpdate(camp_updates=camp_updates, world_updates={region.id: w_upd})
