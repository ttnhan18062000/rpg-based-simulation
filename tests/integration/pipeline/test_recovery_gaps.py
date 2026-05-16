# tests/verify/test_recovery_gaps.py
import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, RegionState, BuildingState, TaskComponent
from src.core.updates import StateUpdate, EntityUpdate, IdentityUpdate, TaskUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.evolution import EvolutionSystem

def test_regional_hazard_impact():
    """
    Verify that regional hazard damage is applied through the authoritative
    EnvironmentService calculation.

    Fraud this catches:
    - pipeline skips regional hazard logic
    - pipeline uses a stale hardcoded formula
    - pipeline applies hazard to the wrong entity/location
    """
    from src.world.environment import EnvironmentService

    region = RegionState(
        id="r1",
        name="Toxic Swamp",
        bounds=(0, 0, 10, 10),
        hazard_level=10.0,
    )

    entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .combat(hp=100, max_hp=100)
        .build()
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        regions={"r1": region},
    )

    expected_damage = EnvironmentService.calculate_hazard_drain(region, entity)

    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate())

    ent_upd = refined.entity_updates[1]
    assert ent_upd.combat is not None
    assert ent_upd.combat.outcome_kind == "HAZARD"
    assert ent_upd.combat.hp_delta == -expected_damage

def test_building_sabotage():
    """
    Verify that a nearby SABOTAGE task damages the target building.

    Fraud this catches:
    - sabotage task is accepted but no BuildingUpdate is emitted
    - sabotage mutates entity/task only and skips building state
    - BuildingUpdate incorrectly uses entity CombatUpdate fields
    - functionality is computed from the wrong HP delta
    """
    building = BuildingState(
        id=1,
        kind="shop",
        position=(10, 10),
        hp=100,
    )

    entity = (
        V2EntityBuilder(2)
        .kind("hero")
        .location(9.0, 10.0)
        .task(work_kind="SABOTAGE", payload={"target_pos": (10, 10)})
        .build()
    )

    state = AuthoritativeState(
        tick=0,
        seed=42,
        entities={2: entity},
        buildings={1: building},
        building_tiles={(10, 10): "shop"},
    )

    raw_update = StateUpdate(
        entity_updates={
            2: EntityUpdate(
                entity_id=2,
                task=TaskUpdate(
                    work_kind_set="SABOTAGE",
                    payload_set={"target_pos": (10, 10)},
                ),
            )
        }
    )

    refined = AuthoritativeApplyPipeline.refine(state, raw_update)

    b_upd = refined.building_updates[1]
    assert b_upd.hp_delta == -50
    assert b_upd.functional_set is True


def test_hero_evolution_trigger():
    """
    Verify that a hero reaching the evolution threshold becomes LEGEND_HERO.

    Fraud this catches:
    - XP threshold is ignored
    - evolution level is not advanced
    - hero kind mapping is accidentally changed to monster evolution
    """
    entity = (
        V2EntityBuilder(3)
        .kind("hero")
        .location(0.0, 0.0)
        .identity(evolution_level=9, evolution_points=90)
        .build()
    )

    state = AuthoritativeState(tick=1, seed=42, entities={3: entity})

    from src.progression.leveling import LevelingService

    req = LevelingService.get_xp_required(9)

    raw_update = StateUpdate(
        entity_updates={
            3: EntityUpdate(
                entity_id=3,
                identity=IdentityUpdate(evolution_points_delta=req - 80),
            )
        }
    )

    refined = EvolutionSystem.evaluate(state, raw_update)

    ent_upd = refined.entity_updates[3]
    assert ent_upd.kind_set == "LEGEND_HERO"
    assert ent_upd.identity.evolution_level_set == 10

def test_goblin_evolution_trigger():
    """
    Verify that a goblin reaching the evolution threshold becomes GOBLIN_WARRIOR.

    Fraud this catches:
    - monster evolution mapping is broken
    - evolution test accidentally uses hero setup while asserting goblin behavior
    """
    entity = (
        V2EntityBuilder(3)
        .kind("GOBLIN")
        .location(0.0, 0.0)
        .identity(evolution_level=9, evolution_points=90)
        .build()
    )

    state = AuthoritativeState(tick=1, seed=42, entities={3: entity})

    from src.progression.leveling import LevelingService

    req = LevelingService.get_xp_required(9)

    raw_update = StateUpdate(
        entity_updates={
            3: EntityUpdate(
                entity_id=3,
                identity=IdentityUpdate(evolution_points_delta=req - 80),
            )
        }
    )

    refined = EvolutionSystem.evaluate(state, raw_update)

    ent_upd = refined.entity_updates[3]
    assert ent_upd.kind_set == "GOBLIN_WARRIOR"
    assert ent_upd.identity.evolution_level_set == 10