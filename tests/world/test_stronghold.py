import pytest
from src.core.state import AuthoritativeState, RegionState, EntityState, IdentityComponent, CombatComponent
from src.core.enums import Faction
from src.systems.generator import EntityGenerator
from src.world.influence import FactionInfluenceService

def test_stronghold_lifecycle():
    generator = EntityGenerator(seed=42)
    region = RegionState(id="wild", name="Wild", bounds=(0, 0, 10, 10), influence=0.0)
    state = AuthoritativeState(tick=100, seed=42, regions={"wild": region})
    
    # 1. Conquest: Drop influence to -50
    # Create 10 hero deaths
    deaths = []
    for i in range(10):
        deaths.append(EntityState(
            id=i+1, position=(5, 5), kind="hero",
            identity=IdentityComponent(faction=Faction.HERO_GUILD),
            combat=CombatComponent(hp=0, alive=False)
        ))
        
    update = FactionInfluenceService.process_influence_shift(state, deaths)
    assert update.world_updates["wild"].owner_faction_id_set == Faction.MONSTER_HORDE
    
    # Process lifecycle
    lifecycle_update = FactionInfluenceService.process_conquest_lifecycle(state, update, generator)
    
    # Should have a stronghold in entities_add
    assert len(lifecycle_update.entities_add) == 1
    stronghold = lifecycle_update.entities_add[0]
    assert stronghold.kind == "stronghold"
    assert stronghold.position == (5.0, 5.0) # Center of (0,0,10,10)

def test_stronghold_removal():
    generator = EntityGenerator(seed=42)
    region = RegionState(id="wild", name="Wild", bounds=(0, 0, 10, 10), influence=-50.0, owner_faction_id=Faction.MONSTER_HORDE)
    
    # Existing stronghold
    stronghold = EntityState(
        id=100, kind="stronghold", position=(5, 5),
        identity=IdentityComponent(faction=Faction.MONSTER_HORDE),
        combat=CombatComponent(hp=1000, alive=True)
    )
    
    state = AuthoritativeState(tick=100, seed=42, regions={"wild": region}, entities={100: stronghold})
    
    # 1. Liberation: Increase influence to 50
    # Create 20 monster deaths (5 * 20 = 100, -50 + 100 = 50)
    deaths = []
    for i in range(20):
        deaths.append(EntityState(
            id=i+1, position=(5, 5), kind="monster",
            identity=IdentityComponent(faction=Faction.MONSTER_HORDE),
            combat=CombatComponent(hp=0, alive=False)
        ))
        
    update = FactionInfluenceService.process_influence_shift(state, deaths)
    assert update.world_updates["wild"].owner_faction_id_set == -1 # Liberation
    
    # Process lifecycle
    lifecycle_update = FactionInfluenceService.process_conquest_lifecycle(state, update, generator)
    
    # Should have stronghold ID in entities_remove
    assert 100 in lifecycle_update.entities_remove
