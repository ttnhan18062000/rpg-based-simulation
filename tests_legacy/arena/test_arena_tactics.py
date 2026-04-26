import pytest
from src_legacy.certification.harness import CertificationHarness
from src_legacy.certification.scenarios import build_scenario_state, get_scenario_expectations
from src_legacy.config.profiles import RuntimeProfile, HardwareClass

def test_arena_group_coordination():
    """Verify that entities form groups and propagate targets during a battle."""
    profile = RuntimeProfile(
        name="TACTICS_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=100.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_5V5"
    state = build_scenario_state(scenario_id)
    expectations = get_scenario_expectations(scenario_id)
    
    harness = CertificationHarness(profile, output_dir="reports/arena_tactics")
    # Run for 20 ticks to allow group formation and engagement
    result = harness.run_scenario(scenario_id, state, expectations, ticks=20)
    
    assert result.conformance_passed
    
    # Verify group formation (should have at least 2 groups: one per team)
    final_state = result.final_state
    assert len(final_state.groups) >= 2
    
    # Check shared targets
    for group in final_state.groups.values():
        if group.shared_target_id:
            print(f"Group {group.id} (Faction {group.member_ids}) focus firing on {group.shared_target_id}")
            # Ensure the target is actually an entity
            assert group.shared_target_id in final_state.entities
