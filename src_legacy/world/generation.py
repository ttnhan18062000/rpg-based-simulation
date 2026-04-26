from __future__ import annotations
import random
from typing import Dict, List, TYPE_CHECKING
from src_legacy.core.state import (
    AuthoritativeState, RegionState, BuildingState, ResourceNodeState, EntityState
)
from src_legacy.systems.generator import EntityGenerator

class WorldGenerator:
    """
    Authoritative world generation.
    Law: World generation is 100% deterministic given a single seed.
    """
    WORLD_SIZE = 128
    
    @staticmethod
    def generate_world(seed: int, num_entities: int = 10) -> AuthoritativeState:
        rng = random.Random(seed)
        gen = EntityGenerator(seed)
        
        # 1. Regions
        regions = {
            "TOWN": RegionState(
                id="TOWN", name="Town Center", 
                bounds=(48, 48, 80, 80), kind="TOWN", 
                hazard_level=0.0
            ),
            "WILDERNESS": RegionState(
                id="WILDERNESS", name="Wilderness", 
                bounds=(0, 0, 128, 128), kind="FOREST", 
                hazard_level=0.1
            )
        }
        
        # 2. Buildings (Town Center & Camps)
        buildings = {
            1: BuildingState(id=1, kind="SHOP", position=(64.0, 60.0)),
            2: BuildingState(id=2, kind="BLACKSMITH", position=(60.0, 64.0)),
            3: BuildingState(id=3, kind="GOBLIN_CAMP", position=(20.0, 20.0)),
            4: BuildingState(id=4, kind="GOBLIN_CAMP", position=(100.0, 100.0))
        }
        
        # 3. Resource Nodes
        resource_nodes = {}
        node_id = 1
        for _ in range(20):
            # Spawn wood nodes
            pos = (rng.uniform(10, 118), rng.uniform(10, 118))
            resource_nodes[node_id] = ResourceNodeState(
                id=node_id, kind="TREE", position=pos, 
                yields_item="wood", remaining_charges=5, max_charges=5, required_ticks=10
            )
            node_id += 1
            
        for _ in range(10):
            # Spawn ore nodes
            pos = (rng.uniform(10, 118), rng.uniform(10, 118))
            resource_nodes[node_id] = ResourceNodeState(
                id=node_id, kind="ROCK", position=pos, 
                yields_item="iron_ore", remaining_charges=3, max_charges=3, required_ticks=20
            )
            node_id += 1

        # 4. Entities
        entities = {}
        hero = gen.spawn_hero((64.0, 64.0))
        entities[hero.id] = hero
        
        # Spawn monsters near camps instead of randomly
        camp_positions = [b.position for b in buildings.values() if b.kind == "GOBLIN_CAMP"]
        
        for _ in range(num_entities - 1):
            camp_pos = rng.choice(camp_positions)
            monster = gen.spawn_goblin((
                camp_pos[0] + rng.uniform(-10, 10), 
                camp_pos[1] + rng.uniform(-10, 10)
            ))
            entities[monster.id] = monster
            
        return AuthoritativeState(
            tick=0,
            seed=seed,
            entities=entities,
            regions=regions,
            buildings=buildings,
            resource_nodes=resource_nodes
        )
