import json
import logging
from src_v2.certification.harness import CertificationHarness
from src_v2.certification.scenarios import get_scenario_expectations, PressureInjector
from src_v2.config.profiles import RuntimeProfile
from src_v2.core.state import AuthoritativeState

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    import sys
    with open("docs/engine/manifest.json", "r") as f:
        manifest = json.load(f)
    
    targets = manifest["declared_release_targets"]
    required_profiles = targets["required_profiles"]
    required_scenarios = targets["required_scenarios"]
    
    if len(sys.argv) > 1:
        required_scenarios = [sys.argv[1]]
        print(f"Running targeted scenario: {required_scenarios}")
        
    for profile_name in required_profiles:
        profile = RuntimeProfile(
            name=profile_name,
            hardware_class="class_b",
            max_cpu_percent=80.0,
            max_tick_budget_ms=10.0, 
            max_ram_mb=500.0,
            max_worker_count=4,
            max_queue_depth=1000,
            max_work_debt=40,
            max_replay_buffer_kb=5000,
            max_observability_budget_percent=10.0
        )
        harness = CertificationHarness(profile, override_class=None)
        
        for scenario_id in required_scenarios:
            expectations = get_scenario_expectations(scenario_id)
            initial_state = AuthoritativeState(tick=0, seed=42)
            
            # Apply specific injections based on scenarios
            if scenario_id in ["RAM_PRESSURE", "TICK_BUDGET_PRESSURE"]:
                initial_state = PressureInjector.inject_entities(initial_state, 1000)
            elif scenario_id == "QUEUE_INFLIGHT_PRESSURE":
                # Just scale entities
                initial_state = PressureInjector.inject_entities(initial_state, 500)
            elif scenario_id == "WORK_DEBT_BUILDUP":
                initial_state = PressureInjector.inject_work_debt(initial_state, "simulation", 30)
            elif scenario_id == "DEGRADED_NORMAL_RECOVERY":
                initial_state = PressureInjector.inject_work_debt(initial_state, "simulation", 30)
            elif scenario_id == "SURVIVAL_NORMAL_RECOVERY":
                initial_state = PressureInjector.inject_work_debt(initial_state, "simulation", 50)
            elif scenario_id == "REPLAY_OVERFLOW_SURVIVAL":
                initial_state = PressureInjector.inject_work_debt(initial_state, "simulation", 50)
            elif scenario_id == "REPLAY_PRESSURE":
                # We can simulate replay pressure by injecting many entities which writes many replay chunks
                initial_state = PressureInjector.inject_entities(initial_state, 1000)
                # To ensure it gets to SURVIVAL, inject enough debt
                initial_state = PressureInjector.inject_work_debt(initial_state, "simulation", 50)
            elif scenario_id == "SHUTDOWN_TIMEOUT_SURVIVAL":
                # Ensure it's in survival to test gated shutdown
                initial_state = PressureInjector.inject_work_debt(initial_state, "simulation", 50)
            
            # Run the scenario
            try:
                # 60 ticks is enough to see failures / recovery
                result = harness.run_scenario(
                    scenario_id, 
                    initial_state, 
                    expectations, 
                    ticks=60
                )
                print(f"[{profile_name}] {scenario_id} - PASS: {result.conformance_passed}")
            except Exception as e:
                print(f"Error running {scenario_id} for {profile_name}: {e}")
