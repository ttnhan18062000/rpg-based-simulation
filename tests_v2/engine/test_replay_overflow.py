import pytest
from pathlib import Path
from src_v2.core.diagnostic import TraceEvent
from src_v2.engine.replay_manager import ReplayManager
from src_v2.engine.policy import GovernorPolicy


def test_replay_staging_overflow_oldest_evicted(tmp_path):
    """
    M6 Law: Replay staging must stay within declared memory bounds.
    Verifies that ReplayBuffer uses OverflowPolicy.EVICT_OLDEST.
    """
    # Small capacity for testing: 1 KB (~4 items @ 250b each)
    run_dir = tmp_path / "overflow_run"
    replay = ReplayManager(run_dir=run_dir, profile_name="TEST", buffer_capacity_kb=1)
    policy = GovernorPolicy()
    
    # 1. Fill buffer exactly (4 items)
    for i in range(4):
        replay.emit(TraceEvent(tick=0, system="K", event_type=f"E{i}"), policy)
        
    assert replay._buffer.item_count == 4
    
    # 2. Add 5th item -> E0 should be evicted
    replay.emit(TraceEvent(tick=0, system="K", event_type="E4"), policy)
    assert replay._buffer.item_count == 4
    
    events = replay._buffer.extract_chunk()
    assert events[0].event_type == "E1" # E0 is gone
    assert events[-1].event_type == "E4"


def test_replay_waterfall_degradation(tmp_path):
    """
    M6 Law: Replay richness follows GovernorPolicy de-escalation.
    """
    run_dir = tmp_path / "degradation_run"
    replay = ReplayManager(run_dir=run_dir, profile_name="TEST")
    
    # 1. NORMAL policy (FULL richness)
    policy_normal = GovernorPolicy(replay_allowed=True, replay_richness="FULL", allow_subsystem_traces=True)
    replay.emit(TraceEvent(tick=1, system="SUBSYSTEM", event_type="INTERNAL"), policy_normal)
    assert replay._buffer.item_count == 1
    replay._buffer.extract_chunk() # Clear
    
    # 2. CONSTRAINED policy (No subsystem traces)
    policy_constrained = GovernorPolicy(replay_allowed=True, replay_richness="FULL", allow_subsystem_traces=False)
    replay.emit(TraceEvent(tick=2, system="SUBSYSTEM", event_type="INTERNAL"), policy_constrained)
    assert replay._buffer.item_count == 0 # DROPPED
    
    # 3. DEGRADED policy (MINIMAL richness - Actions only)
    policy_degraded = GovernorPolicy(replay_allowed=True, replay_richness="MINIMAL", allow_subsystem_traces=False)
    replay.emit(TraceEvent(tick=3, system="ENTITY", event_type="ACTION"), policy_degraded)
    assert replay._buffer.item_count == 1 # KEPT
    
    replay.emit(TraceEvent(tick=3, system="KERNEL", event_type="TICK_END"), policy_degraded)
    assert replay._buffer.item_count == 2 # KEPT
    
    # 4. SURVIVAL policy (OFF)
    policy_survival = GovernorPolicy(replay_allowed=False, replay_richness="OFF")
    replay.emit(TraceEvent(tick=4, system="ENTITY", event_type="ACTION"), policy_survival)
    assert replay._buffer.item_count == 2 # NO NEW EVENTS
