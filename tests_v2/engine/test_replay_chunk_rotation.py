from src_v2.core.diagnostic import TraceEvent
from src_v2.engine.replay_manager import ReplayManager
from src_v2.engine.policy import GovernorPolicy
from src_v2.config.profiles import RuntimeProfile, HardwareClass
import json


def test_replay_chunk_rotation_logic(tmp_path):
    """
    M6 Law: Chunks are rotated deterministically based on ticks/size.
    """
    run_dir = tmp_path / "rotation_run"
    # Rotate every 2 ticks
    profile = RuntimeProfile(
        name="TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_work_debt=100,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=10.0
    )
    replay = ReplayManager(run_dir=run_dir, profile_name=profile.name, chunk_tick_limit=2)
    policy = GovernorPolicy()
    
    # Tick 0
    replay.emit(TraceEvent(tick=0, system="K", event_type="E0"), policy)
    replay.on_tick_end(0)
    assert not (run_dir / "chunk_0000.json").exists()
    
    # Tick 1 -> Boundary (Ticks in chunk: 1-0 = 1. Limit is 2.)
    replay.emit(TraceEvent(tick=1, system="K", event_type="E1"), policy)
    replay.on_tick_end(1)
    assert not (run_dir / "chunk_0000.json").exists()

    # 2 - 0 = 2. Trigered!
    replay.emit(TraceEvent(tick=2, system="K", event_type="E2"), policy)
    replay.on_tick_end(2)
    
    # Wait for async rotation
    import time
    for _ in range(50):
        if (run_dir / "chunk_0000.json").exists():
            break
        time.sleep(0.01)
        
    assert (run_dir / "chunk_0000.json").exists()
    
    # Emit E3 so finalize has something to flush into chunk_0001
    replay.emit(TraceEvent(tick=3, system="K", event_type="E3"), policy)
    replay.finalize()
    assert (run_dir / "chunk_0001.json").exists()


def test_manifest_integrity(tmp_path):
    """
    M6 Law: Each run contains a valid manifest tracking chunks and metadata.
    """
    run_dir = tmp_path / "manifest_run"
    replay = ReplayManager(run_dir=run_dir, profile_name="TEST_PROFILE", chunk_tick_limit=1)
    policy = GovernorPolicy()
    
    replay.emit(TraceEvent(tick=0, system="K", event_type="E0"), policy)
    replay.on_tick_end(0) # Rotates chunk 0
    
    # Wait for manifest update (M6 Law)
    import time
    for _ in range(50):
        with replay._manifest_lock:
            if len(replay._manifest["chunks"]) == 1:
                break
        time.sleep(0.01)
        
    replay.finalize()
    
    manifest_path = run_dir / "manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        assert manifest["profile"] == "TEST_PROFILE"
        assert manifest["status"] == "COMPLETED"
        assert len(manifest["chunks"]) == 1
        assert manifest["chunks"][0]["id"] == 0
        assert manifest["chunks"][0]["event_count"] == 1
        assert "metrics" in manifest
