import pytest
from src.certification.harness import CertificationHarness
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import RuntimeProfile, HardwareClass

@pytest.mark.slow
def test_arena_group_coordination():
    """Verify that entities form groups and propagate targets during a battle."""
    profile = RuntimeProfile(
        name="TACTICS_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=250.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_5V5"
    state = build_scenario_state(scenario_id)
    expectations = get_scenario_expectations(scenario_id)
    
    harness = CertificationHarness(profile, output_dir="reports/arena_tactics")
    # Run for 20 ticks to allow group formation and engagement
    result = harness.run_scenario(scenario_id, state, expectations, ticks=20)
    
    if not result.conformance_passed:
        print(f"FAILURE KIND: {result.failure_kind}")
        print(f"FAILURE REASON: {result.failure_reason}")
        
        # Baseline run is hidden inside run_scenario, so we have to re-run it here to diff
        # Or we can just check what we have in result
        from tests.arena.state_diff import diff_states
        # We don't have the baseline state easily, but we can reconstruct it
        profile_dict = profile.model_dump()
        profile_dict["max_worker_count"] = 0
        from src.engine.kernel import Kernel
        from src.platform.rng import DeterministicRNG
        baseline_kernel = Kernel(RuntimeProfile(**profile_dict), state, DeterministicRNG(state.seed), flags={"no_replay": True, "audit_mode": True})
        try:
            for _ in range(20):
                baseline_kernel.tick_once()

            diffs = diff_states(baseline_kernel.state, result.final_state)
            print(f"ALL DIFFS: {diffs}")
        finally:
            baseline_kernel.shutdown()

    assert result.conformance_passed
    
    # Verify group formation (should have at least 2 groups: one per team)
    final_state = result.final_state
    assert len(final_state.groups) >= 2
    
    # Check shared targets
    for group in final_state.groups.values():
        if group.shared_target_id:
            pass
            # Ensure the target is actually an entity
            assert group.shared_target_id in final_state.entities
