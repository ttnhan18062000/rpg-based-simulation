import pytest
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.generator import EntityGenerator

def test_maturity_advancement():
    # Setup state at tick 1000 (MATURITY_INTERVAL)
    region = RegionState(id="forest", name="Forest", bounds=(0,0,10,10))
    state = AuthoritativeState(tick=1000, seed=42, regions={"forest": region})
    generator = EntityGenerator(42)
    update = StateUpdate()
    
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    
    assert refined.maturity_set == 1

def test_calamity_boss_spawn():
    # Setup state with high intensity region and force interval tick
    region = RegionState(
        id="badlands", 
        name="Badlands", 
        bounds=(50,50,60,60), 
        calamity_intensity=0.8
    )
    # FORCE_INTERVAL is 5000
    state = AuthoritativeState(
        tick=5000, 
        seed=42, 
        regions={"badlands": region},
        last_calamity_tick=0
    )
    generator = EntityGenerator(42)
    update = StateUpdate()
    
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    
    assert len(refined.entities_add) > 0
    boss = next(e for e in refined.entities_add if e.kind == "world_boss")
    assert boss.kind == "world_boss"
    assert boss.position == region.center
    assert refined.last_calamity_tick_set == 5000

def test_regional_transformation():
    # Setup Forest with high trauma
    region = RegionState(
        id="f1", 
        name="Ancient Forest", 
        bounds=(0,0,20,20), 
        kind="FOREST",
        trauma_score=60.0 # Threshold for BURNT_FOREST is 50.0
    )
    state = AuthoritativeState(tick=10, seed=42, regions={"f1": region})
    generator = EntityGenerator(42)
    update = StateUpdate()
    
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    
    assert refined.world_updates["f1"].kind_set == "BURNT_FOREST"

def test_raid_spawning():
    # RAID_INTERVAL_DAYS=5, TICKS_PER_DAY=100 -> 500 ticks
    state = AuthoritativeState(tick=500, seed=42)
    generator = EntityGenerator(42)
    update = StateUpdate()
    
    refined = WorldDynamicsSystem.resolve_dynamics(state, update, generator)
    
    # Raiders should be added (default 3 + maturity 0 = 3)
    raiders = [e for e in refined.entities_add if e.kind == "goblin_raider"]
    assert len(raiders) == 3


def test_boss_spawn_is_idempotent_even_if_existing_boss_left_region():
    """
    LAW:
        A region must not spawn a second boss while its original boss is still
        active/alive, even if that boss has moved outside the region bounds.

    Fraud this catches:
        - boss idempotency depends on current position
        - original boss wanders out of region and region spawns duplicate boss
    """
    from dataclasses import replace

    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState, RegionState
    from src.systems.generator import EntityGenerator
    from src.world.boss import BossService

    region = RegionState(
        id="region_1",
        name="Dark Forest",
        bounds=(0, 0, 100, 100),
        kind="FOREST",
        trauma_score=30.0,
    )

    existing_boss = (
        V2EntityBuilder(100)
        .kind("world_boss")
        .location(150.0, 150.0)  # Outside original region.
        .combat(
            hp=500,
            max_hp=500,
            alive=True,
        )
        .lifecycle(active=True)
        .build()
    )

    existing_boss = replace(
        existing_boss,
        identity=replace(
            existing_boss.identity,
            properties={
                **existing_boss.identity.properties,
                "boss_region_id": "region_1",
            },
        ),
        strategic=replace(
            existing_boss.strategic,
            home_region_id="region_1",
        ),
    )

    state = AuthoritativeState(
        tick=853,
        seed=42,
        maturity=90,
        regions={
            "region_1": region,
        },
        entities={
            100: existing_boss,
        },
    )

    update = BossService.check_for_boss_spawn(
        state,
        EntityGenerator(42),
    )

    assert update.entities_add == []