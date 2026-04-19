import json
import logging
import os
from pathlib import Path
from src_v2.certification.harness import CertificationHarness
from src_v2.core.state import AuthoritativeState
from src_v2.config.profiles import HardwareClass, RuntimeProfile
from src_v2.certification.scenarios import get_scenario_expectations

logging.basicConfig(level=logging.INFO)

def run_matrix():
    manifest_path = "docs/engine/manifest.json"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    targets = manifest["declared_release_targets"]
    profiles = targets["required_profiles"]
    scenarios = targets.get("required_scenarios", [])
    
    profile_defs = {
        "authoritative_equivalence_test": RuntimeProfile(
            name="authoritative_equivalence_test",
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=8192,
            max_tick_budget_ms=16.6,
            max_cpu_percent=80.0,
            max_worker_count=8,
            max_queue_depth=1000,
            max_replay_buffer_kb=32768,
            max_observability_budget_percent=10.0
        ),
        "standard_gaming_profile": RuntimeProfile(
            name="standard_gaming_profile",
            hardware_class=HardwareClass.CLASS_C,
            max_ram_mb=4096,
            max_tick_budget_ms=33.3,
            max_cpu_percent=70.0,
            max_worker_count=4,
            max_queue_depth=500,
            max_replay_buffer_kb=16384,
            max_observability_budget_percent=5.0
        )
    }

    for p_name in profiles:
        profile = profile_defs.get(p_name)
        if not profile:
            continue
            
        harness = CertificationHarness(profile)
        
        for s_id in scenarios:
            print(f"Running Final Certification: {p_name} x {s_id}")
            initial_state = AuthoritativeState(tick=0, seed=12345)
            expectations = get_scenario_expectations(s_id)
            
            harness.run_scenario(s_id, initial_state, expectations, ticks=20)

if __name__ == "__main__":
    run_matrix()
