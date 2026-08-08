from __future__ import annotations
import os
import time
import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig
from src.observability.stream.factory import get_event_stream_adapter, reset_event_stream_adapter
from src.observability.stream.adapters import NullEventStreamAdapter


def test_scale_profile_resolution(monkeypatch):
    """Verifies that scale-test deployment profile resolves to NullEventStreamAdapter."""
    monkeypatch.setenv("SIM_DEPLOYMENT_PROFILE", "scale-test")
    reset_event_stream_adapter()
    
    try:
        adapter = get_event_stream_adapter()
        assert isinstance(adapter, NullEventStreamAdapter), "Scale test profile must resolve to NullEventStreamAdapter"
        
        # Sizing defaults check
        assert ObservabilityConfig.get_stream_backend() == "null"
        assert ObservabilityConfig.get_max_queue_size() == 0
    finally:
        reset_event_stream_adapter()


def test_scale_performance_and_footprint(monkeypatch):
    """Runs a simulated scale validation benchmark ensuring zero event collection overhead."""
    monkeypatch.setenv("SIM_DEPLOYMENT_PROFILE", "scale-test")
    reset_event_stream_adapter()
    
    try:
        profile = RuntimeProfile(
            name="scale-perf-profile",
            hardware_class=HardwareClass.CLASS_A,
            max_ram_mb=4096,
            max_cpu_percent=100.0,
            max_worker_count=2,
            max_queue_depth=1000,
            max_replay_buffer_kb=0,
            max_observability_budget_percent=0.0,
            max_tick_budget_ms=16.6
        )

        # Generate 100 entities to simulate high-intensity workload. Spread across a 10x10 grid,
        # one integer tile apart (LAW-SPAWN-OCCUPANCY collides on int(x), int(y) — see
        # HardLawMonitor._check_spawn_occupancy) — TCK-20260807-SCALE-VALIDATION-ENTITY-COLLISION-
        # BUG: all 100 previously shared literal (10.0, 10.0), tripping a real hard-law violation
        # that this test's own zero-telemetry-accumulation assertion then (correctly) caught.
        entities = {}
        for idx in range(1, 101):
            grid_x = 10.0 + ((idx - 1) % 10)
            grid_y = 10.0 + ((idx - 1) // 10)
            entities[idx] = V2EntityBuilder(idx).combat(hp=100, alive=True).location(grid_x, grid_y).build()

        state = AuthoritativeState(tick=1, seed=42, world_time=100, entities=entities)
        rng = DeterministicRNG(42)
        
        # Initialize kernel
        kernel = Kernel(profile, state, rng)
        
        # Measure start time and memory
        start_time = time.perf_counter()
        
        # Simulate 10 high-density ticks
        prior_state = state
        for tick in range(2, 12):
            next_state = AuthoritativeState(tick=tick, seed=42, world_time=100 + tick, entities=entities)
            kernel._phase_observability(prior_state, None)
            prior_state = next_state
            
        duration = time.perf_counter() - start_time
        
        # Assertions
        assert duration < 1.0, f"Performance bottleneck detected: 10 ticks took {duration:.4f}s"
        
        # Verify EventRecorder and NullEventStreamAdapter buffers are completely empty
        # (Null adapter drops everything instantly, preserving memory)
        assert len(kernel._event_recorder.events) == 0, "Telemetry events must not accumulate under scale profile"
        
        kernel.shutdown()
        
    finally:
        reset_event_stream_adapter()
