from __future__ import annotations
from typing import Dict, List
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, RegionState, BuildingState
from src.perf.scenarios import build_idle_state

def build_governance_state(
    *,
    region_count: int,
    buildings_per_region: int,
    entity_count: int,
    seed: int = 42
) -> AuthoritativeState:
    """
    Build a governance-heavy state for performance testing.
    """
    # 1. Build Base Entities
    # We use build_idle_state but then distribute them.
    state = build_idle_state(entity_count=entity_count, seed=seed)
    entities = state.entities
    
    # 2. Build Regions
    regions = {}
    for i in range(region_count):
        r_id = f"region_{i}"
        # Spiral or grid layout for regions
        x = (i % 10) * 100
        y = (i // 10) * 100
        regions[r_id] = RegionState(
            id=r_id,
            name=f"Territory {i}",
            bounds=(float(x), float(y), float(x + 100), float(y + 100)),
            owner_faction_id=Faction.HERO_GUILD if i % 2 == 0 else Faction.MONSTER_HORDE
        )
        
    # 3. Build Buildings
    buildings = {}
    b_id_counter = 1
    for r_id, region in regions.items():
        for b in range(buildings_per_region):
            bx = region.bounds[0] + (b % 10) * 5
            by = region.bounds[1] + (b // 10) * 5
            buildings[b_id_counter] = BuildingState(
                id=b_id_counter,
                kind="inn",
                position=(bx, by),
                functional=True
            )
            b_id_counter += 1
            
    # 4. Prepare Global Resources (Vaults)
    global_resources = {
        "faction_hero_guild_gold": 1000000.0,
        "faction_monster_horde_gold": 1000000.0
    }
    
    return AuthoritativeState(
        tick=0,
        seed=seed,
        entities=entities,
        regions=regions,
        buildings=buildings,
        global_resources=global_resources
    )
