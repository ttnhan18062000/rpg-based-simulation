import pytest
from src.certification.harness import CertificationHarness
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import RuntimeProfile, HardwareClass

@pytest.mark.slow
@pytest.mark.extra_slow
def test_arena_stress_50v50():
    """Verify that a 50v50 battle stays within resource limits."""
    profile = RuntimeProfile(
        name="STRESS_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=400.0, max_queue_depth=500,
        max_replay_buffer_kb=4096, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_STRESS_50V50"
    state = build_scenario_state(scenario_id)
    expectations = get_scenario_expectations(scenario_id)
    
    harness = CertificationHarness(profile, output_dir="reports/arena_stress")
    # Run for 50 ticks to measure scaling
    result = harness.run_scenario(scenario_id, state, expectations, ticks=50)
    
    assert result.conformance_passed
    print(f"Stress Arena 50v50 completed.")
    print(f"Peak RSS: {result.peak_rss_mb:.1f} MB")
    print(f"Total CPU: {result.total_cpu_sec:.3f} sec")
    
    # TCK-20260818-STANDARD-PERF-SLOW-CI-FIRST-RUN-CALIBRATION: this test only ever ran to
    # completion under the real "Slow regression" CI job's own `--resource-budget large`
    # invocation for the first time on 2026-08-17/18 (TCK-20260817-CI-FAST-LANE-EXTRA-SLOW-FILTER
    # -INCONSISTENCY removed it from the `perf-cert-arena` fast lane, where it had never actually
    # exercised its own real 3-kernel-run resource cost before). The original `200.0` bound
    # (TCK-20260623-FIX-ARENA) was never a real measurement — its own comment said "starting from
    # ~48MB, should stay well below 200MB", an eyeballed guess. Real CI: peak_rss_mb=247.07MB.
    # Local reproduction (.venv, this session): peak_rss_mb=92.2MB — same order of magnitude, no
    # regression signal, just CI's shared-runner process baseline running higher. Raised with
    # ~50% headroom above the highest real observed value (CI's own 247.07MB), matching the
    # precedent methodology in TCK-20260817-STANDARD-PERF-COMBAT-MISSING-SLOW-MARKER.
    assert result.peak_rss_mb < 375.0
