from __future__ import annotations
import random
from typing import Dict, List, Set, Tuple
from src_v2.core.state import (
    EntityState, IdentityComponent, InventoryComponent, 
    NavigationComponent, CombatComponent, LifecycleComponent,
    AuthoritativeState, ResourceNodeState, BuildingState
)

class EntityGenerator:
    """Minimal V2 entity generator for CLI parity."""
    
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.next_id = 1

    def spawn_hero(self, pos: Tuple[float, float]) -> EntityState:
        eid = self.next_id
        self.next_id += 1
        return EntityState(
            id=eid,
            kind="hero",
            position=pos,
            identity=IdentityComponent(role=0, faction=0), # HERO_GUILD
            combat=CombatComponent(hp=100, max_hp=100, atk=15, def_stat=5),
            inventory=InventoryComponent(max_slots=16, gold=50),
            lifecycle=LifecycleComponent(max_age_ticks=5000),
            navigation=NavigationComponent(target=pos)
        )

    def spawn_goblin(self, pos: Tuple[float, float]) -> EntityState:
        eid = self.next_id
        self.next_id += 1
        return EntityState(
            id=eid,
            kind="goblin",
            position=pos,
            identity=IdentityComponent(role=1, faction=1), # MONSTER
            combat=CombatComponent(hp=30, max_hp=30, atk=8, def_stat=2),
            inventory=InventoryComponent(max_slots=4, gold=5),
            lifecycle=LifecycleComponent(max_age_ticks=2000),
            navigation=NavigationComponent(target=pos)
        )

    def spawn_resource(self, kind: str, pos: Tuple[float, float]) -> ResourceNodeState:
        rid = self.next_id
        self.next_id += 1
        yields = "wood" if kind == "tree" else "iron_ore"
        return ResourceNodeState(
            id=rid,
            kind=kind,
            position=pos,
            yields_item=yields,
            remaining_charges=5,
            max_charges=5,
            required_ticks=3
        )
