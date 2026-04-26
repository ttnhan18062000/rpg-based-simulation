import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, RegionState, EntityState, IdentityComponent
from src.core.updates import StateUpdate
from src.core.enums import Faction
from src.world.influence import FactionInfluenceService

def test_influence_shift_on_death():
    # Initial state with a region
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=0.0)
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region}
    )
    
    # 1. Hero death -> -5.0 influence
    hero = EntityState(
        id=1, position=(5, 5), kind="hero", 
        identity=IdentityComponent(faction=Faction.HERO_GUILD)
    )
    update = FactionInfluenceService.process_influence_shift(state, [hero])
    
    assert "forest" in update.world_updates
    assert update.world_updates["forest"].influence_delta == -5.0
    
    # 2. Monster death -> +5.0 influence
    monster = EntityState(
        id=2, position=(6, 6), kind="goblin", 
        identity=IdentityComponent(faction=Faction.MONSTER_HORDE)
    )
    update = FactionInfluenceService.process_influence_shift(state, [monster])
    assert update.world_updates["forest"].influence_delta == 5.0

def test_conquest_and_liberation_thresholds():
    # Region near conquest threshold
    region = RegionState(id="forest", name="Forest", bounds=(0, 0, 10, 10), influence=-46.0)
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": region}
    )
    
    # Hero death -> influence becomes -51.0 (<= -50.0) -> Conquered
    hero = EntityState(id=1, position=(5, 5), kind="hero", identity=IdentityComponent(faction=Faction.HERO_GUILD))
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
    monster = EntityState(id=2, position=(6, 6), kind="goblin", identity=IdentityComponent(faction=Faction.MONSTER_HORDE))
    update_lib = FactionInfluenceService.process_influence_shift(state_conquered, [monster])
    
    assert update_lib.world_updates["forest"].owner_faction_id_set == -1 # Sentinel for None
