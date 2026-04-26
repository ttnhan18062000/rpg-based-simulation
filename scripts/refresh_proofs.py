import os
import sys
import json
import logging
from pathlib import Path

# Ensure PYTHONPATH is set
sys.path.insert(0, os.getcwd())

from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState, EntityState
from src.certification.harness import CertificationHarness
from src.certification.scenarios import get_scenario_expectations, PressureInjector, build_scenario_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("refresh_proofs")

MANIFEST_PATH = "docs/engine/manifest.json"
OUTPUT_DIR = "reports/release_proof"

def refresh_all():
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    
    targets = manifest["declared_release_targets"]
    profiles = targets["required_profiles"]
    scenarios = targets["required_scenarios"]
    
    # Base state
    base_state = AuthoritativeState(tick=0, seed=42, entities={
        1: EntityState(id=1, kind="ROOT", position=(0,0), readiness=100.0)
    })
    
    def get_profile(name):
        return RuntimeProfile(
            name=name,
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=1024,
            max_cpu_percent=80.0,
            max_worker_count=4,
            max_queue_depth=500,
            max_work_debt=1000, # 500 = DEGRADED, 1000 = SURVIVAL
            max_tick_budget_ms=16.6,
            sampling_interval_ticks=1,
            max_replay_buffer_kb=1024,
            max_observability_budget_percent=5.0,
            dwell_time_ticks=5,
            confidence_window_ticks=2
        )

    for p_name in profiles:
        profile = get_profile(p_name)
        harness = CertificationHarness(profile, output_dir=OUTPUT_DIR)
        
        for s_id in scenarios:
            logger.info(f"--- REFRESHING: {p_name} x {s_id} ---")
            expectations = get_scenario_expectations(s_id)
            
            # 1. Use scenario-specific base state if available (Milestone 5)
            state = build_scenario_state(s_id)
            
            # 2. BOLUS PRESSURE (Distributed across 4 subsystems to hit 16 drain/tick)
            if "SURVIVAL" in expectations.required_governor_modes:
                # 1200 total debt. 1200 / 16 = 75 ticks to recovery. (Passes 100 limit)
                for sys_id in ["KERNEL", "REPLAY", "PHYSICS", "AI"]:
                    state = PressureInjector.inject_work_debt(state, sys_id, 300)
                state = PressureInjector.inject_entities(state, 100)
            elif "DEGRADED" in expectations.required_governor_modes:
                # 700 total debt. 700 / 16 = 43 ticks to recovery.
                for sys_id in ["KERNEL", "REPLAY", "PHYSICS", "AI"]:
                    state = PressureInjector.inject_work_debt(state, sys_id, 175)
            
            if s_id == "RAM_PRESSURE":
                state = PressureInjector.inject_entities(state, 1000)
                
            try:
                harness.run_scenario(s_id, state, expectations, ticks=200)
            except Exception as e:
                logger.error(f"Failed to refresh {s_id}: {e}")

if __name__ == "__main__":
    refresh_all()
