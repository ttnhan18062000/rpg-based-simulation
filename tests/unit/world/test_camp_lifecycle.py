# tests/world/test_camp_lifecycle.py
import inspect

import pytest
from src.core.state import AuthoritativeState, RegionState, CampState
from src.systems.world_systems.generator import EntityGenerator
from src.engine.world_dynamics import WorldDynamicsSystem
from src.core.updates import StateUpdate, CampUpdate
from src.world.camp import CampService
from src.domains.optimization.feature_flags import FeatureFlagManager, FeatureMode

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


# TCK-20260904-CAMP-NEST-CLASSIFICATION


def test_nest_race_kinds_classification_matches_documented_table():
    """Parity guard: CampService.NEST_RACE_KINDS must match the investigation/plan's
    documented Nest classification exactly -- no more, no fewer."""
    assert CampService.NEST_RACE_KINDS == frozenset({"wolf", "spider", "troll", "slime"})


def test_nest_flag_registered_in_feature_flag_manager_default_off():
    manager = FeatureFlagManager()
    assert "ENABLE_CAMP_NEST_SPREAD" in manager.get_all_flags()
    assert manager.get_flag_mode("ENABLE_CAMP_NEST_SPREAD") == FeatureMode.OFF


def test_camp_flag_off_nest_kind_camp_still_raids():
    """Regression / flag-off no-op: a Nest-eligible kind ('wolf') at raid maturity with the
    flag left at its default OFF still produces the existing raid outcome."""
    state = AuthoritativeState(
        tick=500,
        seed=42,
        regions={"forest": RegionState(id="forest", name="The Deep Woods", kind="forest", bounds=(0, 0, 100, 100), trauma_score=10.0)},
        camps={"camp_1": CampState(id="camp_1", kind="wolf", position=(50, 50), maturity=90.0, last_raid_tick=0)},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    assert update.camp_updates["camp_1"].maturity_delta == -20.0
    assert update.camp_updates["camp_1"].last_raid_tick_set == 500
    assert all(e.kind != "wolf" for e in update.entities_add)


def test_camp_flag_on_camp_kind_still_raids():
    """A Camp-classified kind ('goblin') at raid maturity, with the new flag ON, still takes
    the raid outcome -- proves the fork keys off classification, not just the flag."""
    state = AuthoritativeState(
        tick=500,
        seed=42,
        regions={"forest": RegionState(id="forest", name="The Deep Woods", kind="forest", bounds=(0, 0, 100, 100), trauma_score=10.0)},
        camps={"camp_1": CampState(id="camp_1", kind="goblin", position=(50, 50), maturity=90.0, last_raid_tick=0)},
        feature_flags={"ENABLE_CAMP_NEST_SPREAD": "ON"},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    assert update.camp_updates["camp_1"].maturity_delta == -20.0
    assert update.camp_updates["camp_1"].last_raid_tick_set == 500


def test_camp_flag_on_nest_kind_spreads_instead_of_raiding():
    """Core new-behavior AC: flag ON + Nest-kind camp at raid maturity, past the cooldown,
    produces a spread outcome (parentless same-kind offspring) instead of a raid, applying the
    same cost/cooldown-reset fields the raid path uses."""
    state = AuthoritativeState(
        tick=500,
        seed=42,
        regions={"forest": RegionState(id="forest", name="The Deep Woods", kind="forest", bounds=(0, 0, 100, 100), trauma_score=10.0)},
        camps={"camp_1": CampState(id="camp_1", kind="wolf", position=(50, 50), maturity=90.0, last_raid_tick=0)},
        feature_flags={"ENABLE_CAMP_NEST_SPREAD": "ON"},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    offspring = [e for e in update.entities_add if e.kind == "wolf"]
    assert len(offspring) == 1
    assert offspring[0].lifecycle.parent_a_entity_id is None
    assert offspring[0].lifecycle.parent_b_entity_id is None
    assert offspring[0].lifecycle.genetic_profile is None
    assert update.camp_updates["camp_1"].maturity_delta == -20.0
    assert update.camp_updates["camp_1"].last_raid_tick_set == 500


def test_nest_spread_reuses_same_500_tick_cooldown_as_raid():
    """Anti-drift guard: a Nest-kind camp still inside the 500-tick cooldown, even with
    maturity above threshold and the flag ON, does not trigger a spread outcome."""
    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"forest": RegionState(id="forest", name="The Deep Woods", kind="forest", bounds=(0, 0, 100, 100), trauma_score=10.0)},
        camps={"camp_1": CampState(id="camp_1", kind="wolf", position=(50, 50), maturity=90.0, last_raid_tick=0)},
        feature_flags={"ENABLE_CAMP_NEST_SPREAD": "ON"},
    )
    generator = EntityGenerator(seed=42)

    update = CampService.process_camps(state, generator)

    assert all(e.kind != "wolf" for e in update.entities_add)
    # No raid/spread outcome fired -- camp_updates["camp_1"] only carries the normal
    # maturity-evolution delta from block 1, not the -20.0 raid/spread cost.
    assert update.camp_updates["camp_1"].maturity_delta != -20.0
    assert update.camp_updates["camp_1"].last_raid_tick_set is None


def test_nest_branch_does_not_construct_new_campstate():
    """Architecture guard: the Nest branch must never construct a new CampState -- camps are
    pre-placed at world generation only (WORLD-109)."""
    assert "CampState(" not in inspect.getsource(CampService.process_camps)


def test_campstate_totem_stockpile_palisade_round_trip_canonical_dict():
    camp = CampState(
        id="camp_1", kind="wolf", position=(10.0, 20.0),
        totem_tier=2, stockpile=15.5, palisade_integrity=40.0,
    )
    canonical = camp.to_canonical_dict()
    assert canonical["totem_tier"] == 2
    assert canonical["stockpile"] == 15.5
    assert canonical["palisade_integrity"] == 40.0


def test_campupdate_totem_stockpile_palisade_merge_semantics():
    first = CampUpdate(id="camp_1", stockpile_delta=5.0, totem_tier_set=1)
    second = CampUpdate(id="camp_1", stockpile_delta=3.0, totem_tier_set=2, palisade_integrity_set=25.0)

    merged = first.merge(second)

    assert merged.stockpile_delta == 8.0
    assert merged.totem_tier_set == 2
    assert merged.palisade_integrity_set == 25.0


def test_campupdate_totem_stockpile_palisade_apply_via_apply_plan():
    from src.engine.apply import ApplyPath

    state = AuthoritativeState(
        tick=0, seed=42,
        camps={"camp_1": CampState(id="camp_1", kind="wolf", position=(50, 50))},
    )
    update = StateUpdate(camp_updates={
        "camp_1": CampUpdate(
            id="camp_1", totem_tier_set=3, stockpile_delta=12.0, palisade_integrity_set=60.0,
        )
    })

    next_state = ApplyPath.apply_partial(state, update)

    camp = next_state.camps["camp_1"]
    assert camp.totem_tier == 3
    assert camp.stockpile == 12.0
    assert camp.palisade_integrity == 60.0
