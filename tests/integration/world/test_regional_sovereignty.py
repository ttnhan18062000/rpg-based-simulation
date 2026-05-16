import pytest
from src.core.state import AuthoritativeState, RegionState, EntityState, BuildingState
from src.core.updates import StateUpdate, EntityUpdate, WorldUpdate, BuildingUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, EntityRole
from dataclasses import replace

def test_regional_ownership_flip():
    """
    Verify that regions flip ownership when influence thresholds are crossed.
    Logic ID: WORLD-024 (Regional Sovereignty)
    """
    region = RegionState(
        id="forest",
        name="Grim Forest",
        bounds=(0, 0, 100, 100),
        influence=90.0,
        owner_faction_id=None
    )
    
    # 1. Kill a monster in the region to push influence over 100
    monster = (
        V2EntityBuilder(1)
        .kind("monster")
        .location(50, 50)
        .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
        .combat(hp=10, alive=True)
        .build()
    )
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: monster},
        regions={"forest": region}
    )
    
    # 1. Monster death -> Influence increase
    # We bypass the full pipeline refine() here because Phase 1 (Trust) 
    # strips raw CombatUpdate. In a real game, this update would come 
    # from a previous system in the pipeline.
    from src.systems.lifecycle_systems.lifecycle import LifecycleSystem
    from src.systems.world_systems.generator import EntityGenerator
    generator = EntityGenerator(seed=42)
    
    from src.core.updates import CombatUpdate, EntityUpdate
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, combat=CombatUpdate(outcome_kind="KILL", hp_delta=-20, alive_set=False))
    })
    
    # Manually run the lifecycle system to see influence increase (+5.0 for monster death)
    refined_update_1 = LifecycleSystem.resolve_lifecycle(state, update)
    next_state = ApplyPath.apply_generation(state, refined_update_1, next_tick=2)
    
    # Influence should be 90 + 5 = 95 (not flipped yet)
    assert next_state.regions["forest"].influence == 95.0
    assert next_state.regions["forest"].owner_faction_id is None
    
    # 2. Add more influence to trigger flip
    # This time we use the pipeline to ensure the flip logic in resolve_dynamics triggers
    state_2 = replace(next_state, regions={"forest": replace(next_state.regions["forest"], influence=99.5)})
    large_inf_update = StateUpdate(world_updates={"forest": WorldUpdate(region_id="forest", influence_delta=10.0)})
    
    # Authoritative pass (WorldUpdate is NOT stripped by TrustBoundaryPhase)
    from src.engine.pipeline import AuthoritativeApplyPipeline
    refined_update_2 = AuthoritativeApplyPipeline.refine(state_2, large_inf_update)
    final_state = ApplyPath.apply_generation(state_2, refined_update_2, next_tick=3)
    
    assert final_state.regions["forest"].influence >= 100.0
    assert final_state.regions["forest"].owner_faction_id == Faction.HERO_GUILD

def test_governance_taxation_and_vaults():
    """
    Verify that regional owners collect taxes and store them in faction vaults.
    Logic ID: TOWN-138 (Regional Taxation)
    """
    from src.engine.pipeline import AuthoritativeApplyPipeline
    
    region = RegionState(
        id="town_region",
        name="Hero Town",
        bounds=(0, 0, 20, 20),
        owner_faction_id=Faction.HERO_GUILD
    )
    
    hero = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(10, 10)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD) # Self-faction (no tax)
        .inventory(gold=100)
        .build()
    )
    
    peasant = (
        V2EntityBuilder(2)
        .kind("peasant")
        .location(11, 11)
        .identity(role=EntityRole.HERO, faction=Faction.NEUTRAL) # Other faction (taxable)
        .inventory(gold=100)
        .build()
    )
    
    building = BuildingState(
        id=1,
        kind="inn",
        position=(5, 5),
        functional=True
    )
    
    state = AuthoritativeState(
        tick=100, # Tax tick (multiple of 100)
        seed=42,
        entities={1: hero, 2: peasant},
        regions={"town_region": region},
        buildings={1: building},
        global_resources={"faction_hero_guild_gold": 500.0}
    )
    
    # Cadence needs to align
    from src.engine.cadence import SystemCadence
    cadence = SystemCadence(town_resolution=50) # 50 * 2 = 100 tax interval
    
    # Authoritative pass
    refined_update = AuthoritativeApplyPipeline.refine(state, StateUpdate(), cadence=cadence)
    next_state = ApplyPath.apply_generation(state, refined_update, next_tick=101, cadence=cadence)
    
    # Peasant should have paid 2.0 gold
    assert next_state.entities[2].inventory.gold == 98.0
    # Building should have produced 10.0 gold
    # Vault should have 500 + 2 (peasant) + 10 (building) = 512
    # PLUS maintenance deduction? 512 - 5 = 507.
    assert next_state.global_resources["faction_hero_guild_gold"] == 507.0

def test_governance_maintenance_and_degradation():
    """
    Verify that buildings degrade if faction vaults cannot pay maintenance.
    Logic ID: TOWN-139 (Service Maintenance)
    """
    from src.engine.pipeline import AuthoritativeApplyPipeline
    
    region = RegionState(
        id="town_region",
        name="Hero Town",
        bounds=(0, 0, 20, 20),
        owner_faction_id=Faction.HERO_GUILD
    )
    
    building = BuildingState(
        id=1,
        kind="inn",
        position=(5, 5),
        functional=True
    )
    
    # Case 1: Sufficient funds
    state_ok = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"town_region": region},
        buildings={1: building},
        global_resources={"faction_hero_guild_gold": 100.0}
    )
    
    from src.engine.cadence import SystemCadence
    cadence = SystemCadence(town_resolution=50)
    
    refined_ok = AuthoritativeApplyPipeline.refine(state_ok, StateUpdate(), cadence=cadence)
    next_state_ok = ApplyPath.apply_generation(state_ok, refined_ok, next_tick=101, cadence=cadence)
    # Maintenance cost is 5.0
    assert next_state_ok.global_resources["faction_hero_guild_gold"] == 100.0 + 10.0 - 5.0 # Tax +10, Maint -5
    assert next_state_ok.buildings[1].functional is True
    
    from src.core.updates import BuildingUpdate
    
    # Let's adjust the system logic to use a larger maintenance cost for the test
    # Or just make the vault empty enough.
    # Case 2: Insolvent
    state_broke = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"town_region": region},
        buildings={1: building},
        global_resources={"faction_hero_guild_gold": -100.0} # -100 + 10 (tax) = -90. Maintenance is 5. -90 < 5.
    )
    
    refined_broke = AuthoritativeApplyPipeline.refine(state_broke, StateUpdate(), cadence=cadence)
    next_state_broke = ApplyPath.apply_generation(state_broke, refined_broke, next_tick=101, cadence=cadence)
    
    # Vault should remain -90 (deduction skipped)
    assert next_state_broke.global_resources["faction_hero_guild_gold"] == -90.0
    # Building should be disabled
    assert next_state_broke.buildings[1].functional is False
