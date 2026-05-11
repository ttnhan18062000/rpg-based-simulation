# tests/world/test_camp_lifecycle.py
import pytest
from src.core.state import AuthoritativeState, RegionState, CampState
from src.systems.world_systems.generator import EntityGenerator
from src.engine.world_dynamics import WorldDynamicsSystem
from src.core.updates import StateUpdate

def test_camp_maturity_and_spawn():
    # Setup state with a goblin camp
    state = AuthoritativeState(
        tick=30, # Match spawn interval
        seed=42,
        regions={"forest": RegionState(id="forest", name="The Deep Woods", kind="forest", bounds=(0, 0, 100, 100), trauma_score=60.0)},
        camps={"camp_1": CampState(id="camp_1", kind="goblin", position=(50, 50), maturity=10.0)}
    )
    generator = EntityGenerator(seed=42)
    
    from src.engine.cadence import SystemCadence
    # 1. Process dynamics (Force world_dynamics to run at tick 30)
    update = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), generator, cadence=SystemCadence(world_dynamics=30))
    
    # 2. Verify maturity increase (boosted by trauma)
    # Base 0.05 * 1.5 = 0.075
    assert update.camp_updates["camp_1"].maturity_delta == pytest.approx(0.075)
    
    # 3. Verify monster spawn (since tick 30 % 30 == 0)
    assert len(update.entities_add) > 0
    goblin = next(e for e in update.entities_add if e.kind == "goblin_warrior")
    assert goblin.position == (50, 50)

def test_camp_clearing_reward():
    from src.world.camp import CampService
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": RegionState(id="forest", name="The Deep Woods", kind="forest", bounds=(0, 0, 100, 100), trauma_score=60.0)},
        camps={"camp_1": CampState(id="camp_1", kind="goblin", position=(50, 50), maturity=10.0)}
    )
    
    # Resolve clearing
    update = CampService.resolve_camp_clearing(state, "camp_1")
    
    # Verify camp deactivated
    assert update.camp_updates["camp_1"].active_set is False
    
    # Verify regional trauma reduction
    assert update.world_updates["forest"].trauma_delta == -10.0

def test_camp_raid_trigger():
    # Setup state with high maturity camp
    from src.world.camp import CampService
    state = AuthoritativeState(
        tick=500,
        seed=42,
        regions={"forest": RegionState(id="forest", name="The Deep Woods", kind="forest", bounds=(0, 0, 100, 100), trauma_score=10.0)},
        camps={"camp_1": CampState(id="camp_1", kind="goblin", position=(50, 50), maturity=90.0, last_raid_tick=0)}
    )
    generator = EntityGenerator(seed=42)
    
    update = CampService.process_camps(state, generator)
    
    # Verify maturity reduction (raid cost)
    assert update.camp_updates["camp_1"].maturity_delta == -20.0
    # Verify last_raid_tick updated
    assert update.camp_updates["camp_1"].last_raid_tick_set == 500
