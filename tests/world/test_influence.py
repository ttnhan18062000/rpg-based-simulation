import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, RegionState, EntityState, IdentityComponent
from src.core.updates import StateUpdate
from src.core.enums import Faction
from src.world.influence import FactionInfluenceService

def test_influence_shift_on_death():
    from src.core.builder import V2EntityBuilder
    # Initial state with a region
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=0.0)
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region}
    )
    
    # 1. Hero death -> -5.0 influence
    hero = (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .identity(faction=Faction.HERO_GUILD)
        .build())
    update = FactionInfluenceService.process_influence_shift(state, [hero])
    
    assert "forest" in update.world_updates
    assert update.world_updates["forest"].influence_delta == -5.0
    
    # 2. Monster death -> +5.0 influence
    monster = (V2EntityBuilder(2)
        .kind("goblin")
        .location(6.0, 6.0)
        .identity(faction=Faction.MONSTER_HORDE)
        .build())
    update = FactionInfluenceService.process_influence_shift(state, [monster])
    assert update.world_updates["forest"].influence_delta == 5.0

def test_conquest_and_liberation_thresholds():
    from src.core.builder import V2EntityBuilder
    # Region near conquest threshold
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=-46.0)
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region}
    )
    
    # Hero death -> influence becomes -51.0 (<= -50.0) -> Conquered
    hero = (V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .identity(faction=Faction.HERO_GUILD)
        .build())
    update = FactionInfluenceService.process_influence_shift(state, [hero])
    
    assert update.world_updates["forest"].owner_faction_id_set == Faction.MONSTER_HORDE.value
    
    # Region near liberation threshold
    region_conquered = replace(region, influence=46.0, owner_faction_id=Faction.MONSTER_HORDE.value)
    state_conquered = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region_conquered}
    )
    
    # Monster death -> influence becomes 51.0 (>= 50.0) -> Liberated
    monster = (V2EntityBuilder(2)
        .kind("goblin")
        .location(6.0, 6.0)
        .identity(faction=Faction.MONSTER_HORDE)
        .build())
    update_lib = FactionInfluenceService.process_influence_shift(state_conquered, [monster])
    
    assert update_lib.world_updates["forest"].owner_faction_id_set == -1 # Sentinel for None
