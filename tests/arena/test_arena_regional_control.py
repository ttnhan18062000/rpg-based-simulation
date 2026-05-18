import pytest
from src.certification.harness import CertificationHarness
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.enums import Faction

def test_arena_regional_control():
    """Verify regional influence, conquest, and taxation."""
    profile = RuntimeProfile(
        name="REGIONAL_ARENA_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=100.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_REGIONAL"
    state = build_scenario_state(scenario_id)
    expectations = get_scenario_expectations(scenario_id)
    
    harness = CertificationHarness(profile, output_dir="reports/arena_regional")
    
    # Tick 99 -> Tick 100
    # Hero (ID 13) kills Monster (ID 14)
    # Monster death -> +5.0 influence
    # -45.0 + 5.0 = -40.0
    
    result = harness.run_scenario(scenario_id, state, expectations, ticks=1)
    
    assert result.conformance_passed
    final_state = result.final_state
    region = final_state.regions["test_wilderness"]
    
    # 1. Verify Influence Shift
    assert region.influence == -40.0
    
    # 2. Verify Gold (No Taxation yet because prior_tick was 99)
    # Hero had 100 gold. Kill gives 5.0 gold.
    hero = final_state.entities[13]
    assert hero.inventory.gold == 105 # 100 + 5
    
    # 3. Now run one more tick (prior_tick will be 100)
    result2 = harness.run_scenario(scenario_id, final_state, expectations, ticks=1)
    hero2 = result2.final_state.entities[13]
    # No taxation because region is still unowned (Influence -40.0)
    assert hero2.inventory.gold == 105 

def test_arena_conquest_and_debuff():
    """
    Verify that monster-owned conquered regions apply hero combat debuffs
    and taxation.

    Logic under test:
        When a region is conquered by MONSTER_HORDE and suppression is active,
        heroes inside that region receive the regional conquest debuff:

            atk      = int(base_atk * 0.8)
            def_stat = int(base_def * 0.8)
            speed    = int(base_speed * 0.9)

    Important:
        This test must use the scenario's actual combat values, not
        LevelingService-derived attribute bonuses.

        The COMBAT_ARENA_REGIONAL hero starts with:
            atk=100
            def_stat=20
            speed=10

        Therefore expected debuffed values are:
            atk=int(100 * 0.8) = 80
            def=int(20 * 0.8)  = 16
            speed=int(10 * 0.9) = 9

    Fraud this catches:
        - conquered-region debuff is not applied
        - debuff uses wrong multiplier
        - test falsely adds attribute-derived bonuses that are not part of
          arena scenario combat initialization
        - taxation is skipped when region ownership is forced before the tick
    """
    profile = RuntimeProfile(
        name="CONQUEST_ARENA_TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=1,
        max_tick_budget_ms=100.0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
    )

    scenario_id = "COMBAT_ARENA_REGIONAL"
    state = build_scenario_state(scenario_id)

    from dataclasses import replace

    region = state.regions["test_wilderness"]

    conquered_region = replace(
        region,
        influence=-60.0,
        owner_faction_id=Faction.MONSTER_HORDE,
        suppression_active=True,
    )

    # Set tick=100 so taxation is evaluated during this run.
    state = replace(
        state,
        regions={"test_wilderness": conquered_region},
        tick=100,
    )

    harness = CertificationHarness(
        profile,
        output_dir="reports/arena_conquest",
    )
    expectations = get_scenario_expectations(scenario_id)

    result = harness.run_scenario(
        scenario_id,
        state,
        expectations,
        ticks=1,
    )

    final_state = result.final_state
    hero = final_state.entities[13]

    assert hero.combat.atk == 80
    assert hero.combat.def_stat == 16
    assert hero.combat.speed == 9

    # Hero had 100 gold.
    # Tax is 2.0.
    # Kill reward gives 5.0.
    # Final: 100 - 2 + 5 = 103.
    assert hero.inventory.gold == 103

    faction_key = f"faction_{Faction.MONSTER_HORDE.name.lower()}_gold"
    assert final_state.global_resources.get(faction_key, 0.0) == 2.0