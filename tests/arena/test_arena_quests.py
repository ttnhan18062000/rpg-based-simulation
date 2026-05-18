import pytest
from src.certification.harness import CertificationHarness
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.quests import QuestStatus

def test_arena_quest_progression():
    """Verify that a hero in the arena can progress and complete quests."""
    profile = RuntimeProfile(
        name="QUEST_ARENA_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=100.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_QUESTS"
    state = build_scenario_state(scenario_id)
    expectations = get_scenario_expectations(scenario_id)
    
    harness = CertificationHarness(profile, output_dir="reports/arena_quests")
    # Run for 5 ticks to allow the hero to kill the goblin and collect reward
    result = harness.run_scenario(scenario_id, state, expectations, ticks=5)
    
    assert result.conformance_passed
    
    final_state = result.final_state
    hero = final_state.entities[11]

    # Verify quest completion
    quest = hero.strategic.projects["test_hunt"]
    assert quest.current_value == 1.0
    # Quest should be REWARDED (as ApplyPath automates Active -> Completed -> Rewarded)
    assert quest.quest_status == QuestStatus.REWARDED
    
    # Verify rewards
    assert hero.inventory.gold >= 50
    # Hero should have leveled up, meaning they spent their XP
    assert hero.identity.evolution_level == 2
    # Current points are what's left after leveling up (110 - 100 = 10)
    assert hero.identity.evolution_points == 10
