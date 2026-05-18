import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, CombatComponent, IdentityComponent, BiologicalComponent
from src.core.updates import StateUpdate, EntityUpdate
from src.systems.strategic import StrategicIntelligenceSystem
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction

def test_concern_intake_salience_filtering():
    # Observer at (0, 0), Faction 1
    observer = (V2EntityBuilder(1)
                .kind("hero")
                .location(0.0, 0.0)
                .identity(faction=Faction.HERO_GUILD)
                .combat(hp=100)
                .build())
    
    # 1. Distant Hostile at (20, 0), Faction 2
    distant_hostile = (V2EntityBuilder(2)
                       .kind("monster")
                       .location(20.0, 0.0)
                       .identity(faction=Faction.MONSTER_HORDE)
                       .combat(hp=100)
                       .build())
    
    # 2. Nearby Hostile at (2, 0), Faction 2
    nearby_hostile = (V2EntityBuilder(3)
                      .kind("monster")
                      .location(2.0, 0.0)
                      .identity(faction=Faction.MONSTER_HORDE)
                      .combat(hp=100)
                      .build())
    
    # 3. Dead Ally at (1, 1), Faction 1
    dead_ally = (V2EntityBuilder(4)
                 .kind("hero")
                 .location(1.0, 1.0)
                 .identity(faction=Faction.HERO_GUILD)
                 .combat(hp=0, alive=False)
                 .build())
    
    state = AuthoritativeState(tick=99, seed=42, entities={1: observer, 2: distant_hostile, 3: nearby_hostile, 4: dead_ally})
    
    # Run concern evaluation
    update = StateUpdate()
    update = StrategicIntelligenceSystem.evaluate_all_concerns(state, update)
    
    # Check observer's updates
    obs_up = update.entity_updates.get(1)
    assert obs_up is not None
    assert obs_up.strategic is not None
    
    concerns = obs_up.strategic.concerns_add_or_update
    concern_ids = [c.id for c in concerns]
    
    print(f"\nGenerated Concerns: {concern_ids}")
    
    # Assertions
    # Should have danger_hostile_3 (nearby)
    assert "danger_hostile_3" in concern_ids
    # Should NOT have danger_hostile_2 (distant)
    assert "danger_hostile_2" not in concern_ids
    # Should have trauma_dead_ally_4
    assert "trauma_dead_ally_4" in concern_ids
    
    # Urgency check
    danger_3 = next(c for c in concerns if c.id == "danger_hostile_3")
    assert danger_3.urgency == 0.5 # dist is 2.0
