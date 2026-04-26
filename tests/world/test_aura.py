import pytest
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent
from src.core.enums import Faction
from src.world.environment import EnvironmentService

def test_aura_of_despair():
    # 1. Setup stronghold
    stronghold = EntityState(
        id=1, kind="stronghold", position=(10, 10),
        identity=IdentityComponent(faction=Faction.MONSTER_HORDE),
        combat=CombatComponent(hp=1000, alive=True)
    )
    
    # 2. Setup hero near stronghold (dist = 5)
    hero_near = EntityState(
        id=2, kind="hero", position=(15, 10),
        identity=IdentityComponent(faction=Faction.HERO_GUILD),
        combat=CombatComponent(hp=100, alive=True)
    )
    
    # 3. Setup hero far from stronghold (dist = 20)
    hero_far = EntityState(
        id=3, kind="hero", position=(30, 10),
        identity=IdentityComponent(faction=Faction.HERO_GUILD),
        combat=CombatComponent(hp=100, alive=True)
    )
    
    state = AuthoritativeState(tick=100, seed=42, entities={1: stronghold, 2: hero_near, 3: hero_far})
    
    # Test near hero
    mods_near = EnvironmentService.get_aura_effects(state, hero_near)
    assert mods_near["move_speed"] == 0.7
    
    # Test far hero
    mods_far = EnvironmentService.get_aura_effects(state, hero_far)
    assert mods_far["move_speed"] == 1.0
