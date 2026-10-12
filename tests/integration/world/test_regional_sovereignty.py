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
        functional=True,
        maintenance_shifts_needed=1,  # one shift a period: upkeep is 1 x WAGE_GOLD (6), EXCH-02 ruling 66
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
    
    # EXCH-02, decisions 51 and 58: no per-head levy (the other-faction peasant pays nothing), no +10 mint for a functional building. The vault pays
    # the building's 6 upkeep (one shift's wage) INTO THE BUILDING'S OWN PURSE: 500 - 6 = 494, and the building holds the 6.
    assert next_state.entities[2].inventory.gold == 100
    assert next_state.global_resources["faction_hero_guild_gold"] == 494.0
    assert next_state.buildings[1].inventory.gold == 6

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
        functional=True,
        maintenance_shifts_needed=1,  # one shift a period: upkeep is 1 x WAGE_GOLD (6), EXCH-02 ruling 66
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
    # Upkeep is 6.0 (one shift's wage), paid from the vault into the building's own purse (no +10 mint any more)
    assert next_state_ok.global_resources["faction_hero_guild_gold"] == 100.0 - 6.0
    assert next_state_ok.buildings[1].inventory.gold == 6
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
        global_resources={"faction_hero_guild_gold": -100.0} # -100 < 5: the treasury cannot pay upkeep
    )
    
    refined_broke = AuthoritativeApplyPipeline.refine(state_broke, StateUpdate(), cadence=cadence)
    next_state_broke = ApplyPath.apply_generation(state_broke, refined_broke, next_tick=101, cadence=cadence)
    
    # Nothing is paid and nothing is minted: the vault stays -100 and the unpaid building holds nothing
    assert next_state_broke.global_resources["faction_hero_guild_gold"] == -100.0
    assert next_state_broke.buildings[1].inventory.gold == 0
    # An unpaid building is disabled
    assert next_state_broke.buildings[1].functional is False


def test_ownership_reevaluated_for_region_with_no_death_that_tick():
    """Ownership must be re-checked for a region with no death that tick.

    Guards AC-4 of TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION: the
    unconditional world_dynamics sweep, not the death-gated influence path, is what
    re-evaluates ownership. A consolidation that only evaluated ownership inside
    FactionInfluenceService.process_influence_shift (which is gated on `recent_deaths`)
    would silently narrow when ownership is checked and break non-death conquest.
    Logic ID: WORLD-024 (Regional Sovereignty)
    """
    from src.engine.pipeline import AuthoritativeApplyPipeline

    region = RegionState(
        id="forest", name="Grim Forest", bounds=(0, 0, 100, 100),
        influence=99.5, owner_faction_id=None,
    )
    bystander = (
        V2EntityBuilder(1).kind("hero").location(50, 50)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=10, alive=True).build()
    )
    state = AuthoritativeState(tick=7, seed=42, entities={1: bystander},
                               regions={"forest": region})

    # No death anywhere this tick -- asserted so the fixture cannot silently acquire one
    # and turn this into a death-driven flip without anyone noticing.
    assert all(e.combat.alive for e in state.entities.values())

    update = StateUpdate(world_updates={
        "forest": WorldUpdate(region_id="forest", influence_delta=10.0)
    })
    refined = AuthoritativeApplyPipeline.refine(state, update)
    final = ApplyPath.apply_generation(state, refined, next_tick=8)

    assert final.regions["forest"].owner_faction_id == Faction.HERO_GUILD, (
        "ownership was not re-evaluated for a region with no death that tick"
    )
