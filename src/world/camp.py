# src/world/camp.py
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List
from src.core.updates import StateUpdate, CampUpdate
from src.core.enums import Domain, EntityRole

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, CampState
    from src.systems.generator import EntityGenerator

class CampService:
    """
    Manages persistent world encampments, their maturity, and associated spawns.
    """
    
    MATURITY_PER_TICK = 0.05
    RAID_MATURITY_THRESHOLD = 80.0
    CAMP_SPAWN_INTERVAL = 30
    
    @staticmethod
    def process_camps(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Evolve camps and spawn monsters or raids.
        """
        camp_updates: Dict[str, CampUpdate] = {}
        entities_add = []
        
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
            
            # 2. Camp-based Spawning
            if state.tick % CampService.CAMP_SPAWN_INTERVAL == 0:
                # Count monsters near camp
                mobs_near = [e for e in state.entities.values() 
                             if e.identity.role == EntityRole.MONSTER and e.combat.alive
                             and abs(e.position[0] - camp.position[0]) < 10
                             and abs(e.position[1] - camp.position[1]) < 10]
                
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
            
            # 3. Raid Trigger
            if camp.maturity >= CampService.RAID_MATURITY_THRESHOLD:
                # Check if enough time has passed since last raid
                if state.tick - camp.last_raid_tick >= 500: # 5 days
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
                    
        return StateUpdate(camp_updates=camp_updates, entities_add=entities_add)

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
