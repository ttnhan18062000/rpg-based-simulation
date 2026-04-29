# src/world/boss.py
from __future__ import annotations
import math
from typing import TYPE_CHECKING, List, Optional
from src.core.enums import Domain, EntityRole
from src.core.updates import StateUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, RegionState
    from src.systems.generator import EntityGenerator

class BossService:
    """
    Manages world boss spawning and resolution.
    """
    
    BOSS_SPAWN_THRESHOLD = 50.0 # Maturity or Threat threshold
    
    @staticmethod
    def check_for_boss_spawn(state: AuthoritativeState, generator: EntityGenerator) -> StateUpdate:
        """
        Deterministic, idempotent boss spawning.
        """
        # Rule: Max 1 active boss per region
        active_bosses = [e for e in state.entities.values() 
                         if e.kind == "world_boss" and e.active and e.combat.alive]
        
        # Mapping regions to their bosses
        # For simplicity, we check if ANY boss is active if we only want 1 world boss total,
        # but rule says "per region".
        region_boss_map = {}
        from src.engine.legality import LegalityServiceV2
        for b in active_bosses:
            r = LegalityServiceV2.get_region_for_position(b.position, state)
            if r: region_boss_map[r.id] = b
            
        entities_add = []
        
        for r_id, region in state.regions.items():
            # print(f"DEBUG: Tick {state.tick} Region {r_id} Maturity {state.maturity} Trauma {region.trauma_score}")
            if r_id in region_boss_map:
                continue
                
            # Deterministic Spawn Check
            # Rule: maturity > 50 and regional threat is elevated
            if state.maturity >= BossService.BOSS_SPAWN_THRESHOLD and region.trauma_score >= 20.0:
                # Deterministic Location: near regional danger anchor (center for now)
                xmin, ymin, xmax, ymax = region.bounds
                cx, cy = (xmin + xmax) / 2.0, (ymin + ymax) / 2.0
                
                # Rule: never inside town/sanctuary (Town is at 0,0)
                if abs(cx) < 20 and abs(cy) < 20:
                    # Shift to edge if too close to town
                    cx = math.copysign(25, cx)
                    cy = math.copysign(25, cy)
                
                # Ensure deterministic valid tile (simple grid snap for now)
                spawn_pos = (int(cx), int(cy))
                
                # Boss Metadata & Loot
                from src.core.state import ItemStack
                boss = generator.spawn_monster(
                    spawn_pos,
                    state=state,
                    kind="ancient_sentinel",
                    difficulty_tier=5 # Boss tier
                )
                # Mark as world_boss and add boss loot
                from dataclasses import replace
                boss = replace(boss, 
                    kind="world_boss",
                    inventory=replace(boss.inventory, items=[ItemStack(item_id="ancient_core", quantity=1)])
                )
                
                entities_add.append(boss)
                
        return StateUpdate(entities_add=entities_add)

    @staticmethod
    def resolve_boss_death(state: AuthoritativeState, boss_id: int) -> StateUpdate:
        """
        Rule: Boss death provides high-tier loot via transaction law.
        """
        # This is handled by LootSystem/QuestResolution if tied to a quest,
        # but here we ensure regional threat reduction.
        boss = state.entities.get(boss_id)
        if not boss: return StateUpdate()
        
        from src.engine.legality import LegalityServiceV2
        region = LegalityServiceV2.get_region_for_position(boss.position, state)
        if not region: return StateUpdate()
        
        from src.core.updates import WorldUpdate
        w_upd = WorldUpdate(
            region_id=region.id,
            trauma_score_delta=-20.0 # Significant reduction
        )
        
        return StateUpdate(world_updates={region.id: w_upd})
