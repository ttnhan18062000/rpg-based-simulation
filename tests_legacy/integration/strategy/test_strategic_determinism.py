import os
import json
import pytest
from src_legacy.testing.headless_regression_runner import HeadlessRunner

@pytest.fixture
def runner(tmp_path):
    """HeadlessRunner instance for testing."""
    outdir = tmp_path / "regression_tests"
    return HeadlessRunner(output_root=str(outdir), max_runs=5)

def test_harness_determinism(runner):
    """Verify that two runs with the same seed produce byte-identical results."""
    seed = 123
    ticks = 5 # Reduced for speed, still proves determinism
    
    # Run 1
    res1 = runner.run(seed, ticks)
    assert res1.success, f"Run 1 failed: {res1.error}"
    
    # Run 2
    res2 = runner.run(seed, ticks)
    assert res2.success, f"Run 2 failed: {res2.error}"
    
    # Verify replay files match
    with open(res1.replay_path, 'r') as f:
        replay1 = json.load(f)
    with open(res2.replay_path, 'r') as f:
        replay2 = json.load(f)
        
    assert replay1 == replay2, "Replay logs differ between deterministic runs!"
    print("✓ Replay logs are identical.")

    # Verify cognition exports match for tracked entities
    for eid in res1.cognition_paths:
        with open(res1.cognition_paths[eid], 'r') as f:
            cognition1 = json.load(f)
        with open(res2.cognition_paths[eid], 'r') as f:
            cognition2 = json.load(f)
            
        assert cognition1 == cognition2, f"Cognition exports for E{eid} differ between deterministic runs!"
    print("✓ Cognition exports are identical.")

def test_harness_non_determinism_different_seed(runner):
    """Verify that different seeds produce different outcomes (basic sanity check)."""
    ticks = 5
    
    # Run with Seed A
    res_a = runner.run(111, ticks)
    assert res_a.success
    
    # Run with Seed B
    res_b = runner.run(222, ticks)
    assert res_b.success
    
    with open(res_a.replay_path, 'r') as f:
        replay_a = json.load(f)
    with open(res_b.replay_path, 'r') as f:
        replay_b = json.load(f)
        
    # Verify that the runs are actually different at an action level
    diverged = False
    for t_a, t_b in zip(replay_a["ticks"], replay_b["ticks"]):
        actions_a = t_a["actions"]
        actions_b = t_b["actions"]
        if actions_a != actions_b:
            diverged = True
            break
    
    assert diverged, "Runs with different seeds produced identical action logs!"
    print("✓ Different seeds correctly produced different outcomes.")
