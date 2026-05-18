import pytest
from src_legacy.certification.harness import CertificationHarness
from src_legacy.certification.scenarios import build_scenario_state, get_scenario_expectations
from src_legacy.config.profiles import RuntimeProfile, HardwareClass
from src_legacy.core.enums import Faction

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
    """Verify that conquest triggers debuffs for heroes."""
    profile = RuntimeProfile(
        name="CONQUEST_ARENA_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=100.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_REGIONAL"
    state = build_scenario_state(scenario_id)
    
    # Force conquest state
    from dataclasses import replace
    region = state.regions["test_wilderness"]
    # Conquest threshold is -50.0
    conquered_region = replace(region, influence=-60.0, owner_faction_id=Faction.MONSTER_HORDE)
    # Set tick=100 to trigger taxation in the first run
    state = replace(state, regions={"test_wilderness": conquered_region}, tick=100)
    
    harness = CertificationHarness(profile, output_dir="reports/arena_conquest")
    expectations = get_scenario_expectations(scenario_id)
    result = harness.run_scenario(scenario_id, state, expectations, ticks=1)
    
    final_state = result.final_state
    hero = final_state.entities[13]
    
    # Verify DEBUFF (0.8x Atk/Def, 0.9x Spd)
    # Base: Atk=100, Def=20, Spd=10
    # Expected: Atk=80, Def=16, Spd=9
    assert hero.combat.atk == 80
    assert hero.combat.def_stat == 16
    assert hero.combat.speed == 9
    
    # Verify Taxation for owner
    # Hero had 100 gold. Tax is 2.0. Kill gives 5.0.
    # Total: 100 - 2 + 5 = 103
    assert hero.inventory.gold == 103
    faction_key = f"faction_{Faction.MONSTER_HORDE}_gold"
    assert final_state.global_resources.get(faction_key, 0.0) == 2.0
