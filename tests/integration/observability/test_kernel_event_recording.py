from __future__ import annotations
import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.events import LifecycleEvent

def test_kernel_observability_event_recording(tmp_path):
    # Enable CERTIFICATION mode
    ObservabilityConfig.set_override_mode(ObservabilityMode.CERTIFICATION)
    
    profile = RuntimeProfile(
        name="test-obs-recording",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6
    )

    # Setup one active entity in current state
    e1 = V2EntityBuilder(1).combat(hp=100, alive=True).location(10.0, 10.0).build()
    state = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: e1})
    rng = DeterministicRNG(42)
    
    # Initialize kernel with current state
    kernel = Kernel(profile, state, rng)
    
    # Prior state has empty entities list (representing spawn of entity 1)
    prior_state = AuthoritativeState(tick=0, seed=42, world_time=100, entities={})
    
    # Invoke post-tick observability phase manually to verify seamless event flow
    kernel._phase_observability(prior_state, None)
    
    # The spawn event should be recorded in kernel._entity_timeline_store
    timeline = kernel._entity_timeline_store.get_entity_timeline(1)
    assert len(timeline) >= 1
    
    # The event should be a spawn LifecycleEvent
    spawn_evs = [ev for ev in timeline if isinstance(ev, LifecycleEvent) and ev.action == "spawn"]
    assert len(spawn_evs) == 1
    assert spawn_evs[0].entity_id == 1
    assert spawn_evs[0].tick == 1
    
    # Assert events exist in recorder
    assert len(kernel._event_recorder.events) >= 1
    assert any(isinstance(ev, LifecycleEvent) and ev.action == "spawn" for ev in kernel._event_recorder.events)
    
    # Shutdown kernel
    kernel.shutdown()

    # Reset override mode
    ObservabilityConfig.set_override_mode(None)
