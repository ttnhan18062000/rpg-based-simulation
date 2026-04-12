import os
import json
import shutil
import pytest
from scripts.test_harness import run_harness

@pytest.fixture
def harness_outdir(tmp_path):
    """Temporary directory for harness outputs."""
    outdir = tmp_path / "harness_test"
    outdir.mkdir()
    return str(outdir)

def test_harness_determinism(harness_outdir):
    """Verify that two runs with the same seed produce byte-identical results."""
    seed = 123
    ticks = 10
    
    run1_dir = os.path.join(harness_outdir, "run1")
    run2_dir = os.path.join(harness_outdir, "run2")
    
    # Run 1
    res1 = run_harness(seed, ticks, run1_dir, verify=True)
    
    # Run 2
    res2 = run_harness(seed, ticks, run2_dir, verify=True)
    
    # Verify replay files match
    with open(res1.replay_path, 'r') as f:
        replay1 = json.load(f)
    with open(res2.replay_path, 'r') as f:
        replay2 = json.load(f)
        
    assert replay1 == replay2, "Replay logs differ between deterministic runs!"
    print("✓ Replay logs are identical.")

    # Verify cognition exports match for one tracked entity
    eid = list(res1.cognition_paths.keys())[0]
    with open(res1.cognition_paths[eid], 'r') as f:
        cognition1 = json.load(f)
    with open(res2.cognition_paths[eid], 'r') as f:
        cognition2 = json.load(f)
        
    assert cognition1 == cognition2, "Cognition exports differ between deterministic runs!"
    print("✓ Cognition exports are identical.")

def test_harness_non_determinism_different_seed(harness_outdir):
    """Verify that different seeds produce different outcomes (basic sanity check)."""
    ticks = 10
    
    # Run with Seed A
    run_a_dir = os.path.join(harness_outdir, "run_a")
    res_a = run_harness(111, ticks, run_a_dir)
    
    # Run with Seed B
    run_b_dir = os.path.join(harness_outdir, "run_b")
    res_b = run_harness(222, ticks, run_b_dir)
    
    with open(res_a.replay_path, 'r') as f:
        replay_a = json.load(f)
    with open(res_b.replay_path, 'r') as f:
        replay_b = json.load(f)
        
    # Verify that the runs are actually different at an action level
    # Different seeds should lead to at least one divergent AI decision
    diverged = False
    for t_a, t_b in zip(replay_a["ticks"], replay_b["ticks"]):
        actions_a = t_a["actions"]
        actions_b = t_b["actions"]
        if actions_a != actions_b:
            diverged = True
            break
    
    assert diverged, "Runs with different seeds produced identical action logs!"
    print("✓ Different seeds correctly produced different outcomes.")
