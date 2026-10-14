import pytest
from src.core.state import AuthoritativeState, RegionState, EntityState
from src.core.updates import StateUpdate, EntityUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole

def test_biological_decay():
    """
    Verify that hunger and sleep debt increase every tick.
    Logic ID: WORLD-001 (Quiet tick hunger/sleep decay)
    """
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .biological(hunger=10.0, sleep_debt=10.0)
        .build()
    )
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: hero}
    )
    
    next_state = ApplyPath.apply_generation(state, StateUpdate(), next_tick=2)
    
    # ApplyPath.py: hunger += 0.05 for a person (humanoid_survival hunger is low, owner decision 33), sleep_debt += 0.05
    assert next_state.entities[1].biological.hunger == pytest.approx(10.05)
    assert next_state.entities[1].biological.sleep_debt == pytest.approx(10.05)

def test_corpse_spawning_on_death():
    """
    Verify that a corpse is spawned when an entity dies.
    Logic ID: WORLD-002 (Corpse spawning on death)
    """
    # Create a hero that is alive
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .combat(hp=10, max_hp=10, alive=True)
        .build()
    )
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: hero}
    )
    
    # Apply an update that kills the hero
    from src.core.updates import CombatUpdate
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-20, alive_set=False))
    })
    
    next_state = ApplyPath.apply_generation(state, update, next_tick=2)
    
    assert next_state.entities[1].combat.alive is False
    # Corpse ID mapping: 1000000 + entity_id
    assert 1000001 in next_state.corpses
    corpse = next_state.corpses[1000001]
    assert corpse.original_entity_id == 1
    assert corpse.position == (5.0, 5.0)
    assert corpse.decay_tick == 2 + 100 # Tick 2 + 100

def test_regional_hazard_and_starvation():
    """
    Verify that regional hazards and starvation cause HP loss.
    Logic ID: WORLD-004 (Regional hazard and starvation effects)
    """
    # 1. Starvation: hunger >= 100
    starving_hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(hp=6000, max_hp=6000, alive=True)  # owner decision 36: 1 HP every round(6000 / max_hp) ticks, so this body loses 1 HP each tick
        .biological(hunger=100.0)
        .build()
    )
    
    # 2. Regional Hazard: hazard_level > 0
    hazard_region = RegionState(
        id="hazard",
        name="Death Valley",
        bounds=(-10, -10, 10, 10),
        hazard_level=1.0 # 1.0 * 10 = 10 damage per tick
    )
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: starving_hero},
        regions={"hazard": hazard_region}
    )
    
    from src.engine.pipeline import AuthoritativeApplyPipeline
    update = AuthoritativeApplyPipeline.refine(state, StateUpdate())
    next_state = ApplyPath.apply_generation(state, update, next_tick=2)
    
    # The hazard drain is pinned exactly and separately from the starvation loss. Starvation is staged (owner decision 36, divergence 2.94): at
    # hunger >= 95 a body of max_hp 6000 loses 1 HP each tick (the period is round(6000 / max_hp) = 1); the old flat 2 HP per tick is gone.
    from src.engine.starvation import hp_loss
    from src.world.environment import EnvironmentService
    hazard = EnvironmentService.calculate_hazard_drain(hazard_region, starving_hero)
    starvation = hp_loss(100.0, 6000, 1, 1)
    assert hazard == 10
    assert starvation == 1
    assert next_state.entities[1].combat.hp == 6000 - hazard - starvation

def test_regional_recovery():
    """
    Verify that regional trauma score decays over time.
    Logic ID: WORLD-006 (Regional trauma and stability recovery over time)
    """
    region = RegionState(
        id="f1",
        name="Ancient Forest",
        bounds=(0,0,20,20),
        trauma_score=10.0,
        stability=0.5
    )
    state = AuthoritativeState(tick=1, seed=42, regions={"f1": region})
    
    next_state = ApplyPath.apply_generation(state, StateUpdate(), next_tick=2)
    
    # RegionalConsequenceService.py: trauma_score -= 0.0005, stability += 0.0001
    assert next_state.regions["f1"].trauma_score == pytest.approx(9.9995)
    assert next_state.regions["f1"].stability == pytest.approx(0.5001)

def test_deterministic_spawning():
    """
    Verify that same seed produces same entity stats.
    Logic ID: WORLD-005 (Spawn rules are deterministic / seeded generator)
    """
    from src.systems.world_systems.generator import EntityGenerator
    
    g1 = EntityGenerator(42)
    h1 = g1.spawn_hero((0,0))
    
    g2 = EntityGenerator(42)
    h2 = g2.spawn_hero((0,0))
    
    assert h1.identity.evolution_level == h2.identity.evolution_level
    assert h1.combat.hp == h2.combat.hp
    assert h1.combat.atk == h2.combat.atk
