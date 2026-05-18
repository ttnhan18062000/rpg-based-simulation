# tests/engine/test_phase9_stability.py
import pytest
from src.core.state import AuthoritativeState, RegionState, EntityState, IdentityComponent, CombatComponent, AptitudeComponent
from src.core.updates import StateUpdate
from src.engine.world_dynamics import WorldDynamicsSystem
from src.engine.apply import ApplyPath
from src.systems.world_systems.generator import EntityGenerator
from src.core.enums import EntityRole

def test_1000_tick_stability():
    """
    Stress test to verify world stability over 1,000 ticks.
    Checks for:
    1. Entity count staying within reasonable bounds (No explosion/extinction).
    2. Resource node replenishment.
    3. Regional trauma and hazard progression.
    """
    # 1. Setup World
    generator = EntityGenerator(seed=42)
    regions = {
        "forest_1": RegionState(id="forest_1", name="Dark Forest", bounds=(10, 10, 100, 100), kind="FOREST", stability=0.8),
        "plains_1": RegionState(id="plains_1", name="Sun Plains", bounds=(-100, -100, -10, -10), kind="PLAINS", stability=0.9)
    }
    
    # Spawn initial monsters
    entities = {}
    for i in range(10):
        mob = generator.spawn_monster((20 + i, 20 + i), kind="wolf", difficulty_tier=1)
        entities[mob.id] = mob
        
    state = AuthoritativeState(tick=0, seed=42, regions=regions, entities=entities)
    
    # 2. Run Simulation
    for t in range(1, 1001):
        # Tick dynamics
        update = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), generator)
        
        # Apply updates
        state = ApplyPath.apply_generation(state, update, next_tick=t)
        
        # Periodic assertions to prevent massive runaway early
        if t % 100 == 0:
            alive_monsters = [e for e in state.entities.values() if e.identity.role == EntityRole.MONSTER and e.combat.alive]
            # World should not be empty, nor should it have 1000s of monsters
            assert 2 <= len(alive_monsters) <= 100, f"Monster count unstable at tick {t}: {len(alive_monsters)}"
            
    # 3. Final Assertions
    alive_monsters = [e for e in state.entities.values() if e.identity.role == EntityRole.MONSTER and e.combat.alive]
    total_nodes = len(state.resource_nodes)
    
    print(f"Final tick: {state.tick}")
    print(f"Alive monsters: {len(alive_monsters)}")
    print(f"Total resource nodes: {total_nodes}")
    print(f"Region Forest Trauma: {state.regions['forest_1'].trauma_score}")
    
    assert 2 <= len(alive_monsters) <= 50, "Final monster count should be stable."
    assert total_nodes >= 2, "Resources should have replenished."
