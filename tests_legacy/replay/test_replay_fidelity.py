import pytest
import time
import shutil
from pathlib import Path
from src_legacy.config.profiles import RuntimeProfile
from src_legacy.core.state import AuthoritativeState, EntityState
from src_legacy.platform.rng import DeterministicRNG
from src_legacy.engine.kernel import Kernel
from src_legacy.engine.checkpoint import CanonicalStateHasher
from src_legacy.engine.replay_manager import ReplayManager
from src_legacy.replay.replay_player import ReplayPlayer

def get_test_profile(name="fidelity_test"):
    from src_legacy.config.profiles import HardwareClass
    return RuntimeProfile(
        name=name,
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=0, # Synchronous
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=100.0
    )

def test_replay_fidelity_end_to_end(tmp_path):
    """
    Phase 10 Law: Replaying a simulation run must result in bit-identical state.
    """
    # 1. Setup original simulation
    run_dir = tmp_path / "original_run"
    profile = get_test_profile("fidelity_test")
    
    # Create initial state with a few entities to generate activity
    initial_state = AuthoritativeState(
        tick=0, seed=12345,
        entities={
            1: EntityState(id=1, kind="HERO", position=(0.0, 0.0)),
            2: EntityState(id=2, kind="MONSTER", position=(5.0, 5.0))
        }
    )
    rng = DeterministicRNG(seed=12345)
    
    replay_mgr = ReplayManager(run_dir=run_dir, profile_name="fidelity_test")
    
    kernel = Kernel(profile, initial_state, rng, replay=replay_mgr)
    
    # 2. Run for X ticks
    num_ticks = 20
    original_states = {}
    for i in range(num_ticks):
        kernel.tick_once()
        if kernel.state.tick == 9:
            original_states[9] = CanonicalStateHasher.to_canonical_json(kernel.state, pretty=True)
        
    shutdown_result = kernel.shutdown()
    original_final_hash = shutdown_result.final_hash
    
    # Ensure chunks are written
    assert (run_dir / "manifest.json").exists()
    assert len(list(run_dir.glob("chunk_*.json"))) > 0
    
    # 3. Setup ReplayPlayer
    player = ReplayPlayer(run_dir)
    
    # Reconstruct initial state (must be identical to starting state)
    player.load_initial_state({
        "tick": 0, "seed": 12345, "world_time": 0,
        "entities": {
            "1": {"id": 1, "kind": "HERO", "position": [0.0, 0.0]},
            "2": {"id": 2, "kind": "MONSTER", "position": [5.0, 5.0]}
        }
    })
    
    # 4. Replay and Verify
    replay_results = player.replay_all()
    
    # 5. Assertions
    if len(replay_results["verification_failures"]) > 0:
        with open("original_9.json", "w") as f:
            f.write(original_states.get(9, ""))
        with open("replayed_9.json", "w") as f:
            f.write(replay_results.get("replayed_state_9", ""))
            
    assert replay_results["ticks_replayed"] == num_ticks
    assert len(replay_results["verification_failures"]) == 0
    assert replay_results["final_hash"] == original_final_hash
    print(f"Original Hash: {original_final_hash}")
    print(f"Replayed Hash: {replay_results['final_hash']}")

def test_replay_with_complex_activity(tmp_path):
    """Verify fidelity with more complex state changes (combat/leveling)."""
    run_dir = tmp_path / "complex_run"
    profile = get_test_profile("complex_fidelity")
    
    # Setup state where entities are close and will interact (if logic allows)
    initial_state = AuthoritativeState(
        tick=0, seed=999,
        entities={
            1: EntityState(id=1, kind="HERO", position=(1.0, 1.0)),
            2: EntityState(id=2, kind="MONSTER", position=(1.5, 1.5))
        }
    )
    rng = DeterministicRNG(seed=999)
    replay_mgr = ReplayManager(run_dir=run_dir, profile_name="complex_fidelity")
    kernel = Kernel(profile, initial_state, rng, replay=replay_mgr)
    
    for _ in range(10):
        kernel.tick_once()
        
    original_hash = kernel.shutdown().final_hash
    
    player = ReplayPlayer(run_dir)
    player.load_initial_state({
        "tick": 0, "seed": 999, "world_time": 0,
        "entities": {
            "1": {"id": 1, "kind": "HERO", "position": [1.0, 1.0]},
            "2": {"id": 2, "kind": "MONSTER", "position": [1.5, 1.5]}
        }
    })
    
    replay_results = player.replay_all()
    assert len(replay_results["verification_failures"]) == 0
    assert replay_results["final_hash"] == original_hash
