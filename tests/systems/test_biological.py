import pytest
from src.core.state import AuthoritativeState, EntityState, BiologicalComponent
from src.systems.biological_system import BiologicalSystem

def test_biological_decay():
    entity = EntityState(
        id=1, kind="HERO", position=(0, 0),
        biological=BiologicalComponent(hunger=10.0, sleep_debt=10.0)
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    update = BiologicalSystem.update(state)
    
    ent_upd = update.entity_updates[1]
    assert ent_upd.biological.hunger_delta == 0.5
    assert ent_upd.biological.sleep_debt_delta == 0.3

def test_biological_penalties():
    entity = EntityState(
        id=1, kind="HERO", position=(0, 0),
        biological=BiologicalComponent(hunger=95.0, sleep_debt=98.0)
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    update = BiologicalSystem.update(state)
    
    ent_upd = update.entity_updates[1]
    # Both hunger (>90) and sleep (>95) should contribute to HP loss
    assert ent_upd.combat.hp_delta == -2
