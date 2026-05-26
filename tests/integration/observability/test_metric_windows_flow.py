from __future__ import annotations
import os
import shutil
import json
import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.reporting.artifact_repository import RunArtifactRepository

@pytest.fixture
def clean_runs():
    base_dir = "data/runs"
    yield
    test_run_path = os.path.join(base_dir, "test_run_metrics_integration_123")
    if os.path.exists(test_run_path):
        shutil.rmtree(test_run_path)
    test_run_path_off = os.path.join(base_dir, "test_run_metrics_integration_off")
    if os.path.exists(test_run_path_off):
        shutil.rmtree(test_run_path_off)

def test_kernel_run_produces_metric_windows(clean_runs):
    """Verify that a standard simulation run produces metric_windows.jsonl."""
    # Set override mode to LIGHT
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    
    profile = RuntimeProfile(
        name="test-metrics-integration",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6
    )

    # Simple combat entity
    e1 = V2EntityBuilder(1).combat(hp=100, alive=True).location(10.0, 10.0).build()
    state = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: e1})
    rng = DeterministicRNG(42)
    
    run_id = "test_run_metrics_integration_123"
    kernel = Kernel(profile, state, rng, run_id=run_id)
    
    # Override window size on recorder to test flushes inside loop
    if kernel._metric_recorder:
        kernel._metric_recorder.window_size = 2
        
    # Tick 1
    kernel.tick_once()
    
    # Tick 2 - Should trigger window flush of 1-2
    kernel.tick_once()
    
    # Tick 3 - Tick is recorded, but window 3-4 is not yet complete
    kernel.tick_once()
    
    # Shutdown kernel - Should trigger final partial window flush (tick 3)
    shutdown_result = kernel.shutdown()
    
    repo = RunArtifactRepository()
    metrics_path = os.path.join(repo.base_dir, run_id, "metric_windows.jsonl")
    assert os.path.exists(metrics_path)
    
    with open(metrics_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    assert len(lines) == 2
    
    # Check first window
    w1 = json.loads(lines[0])
    assert w1["run_id"] == run_id
    assert w1["window_start_tick"] == 2
    assert w1["window_end_tick"] == 3
    assert w1["ticks_observed"] == 2
    assert w1["alive_entities_avg"] == 1.0
    assert w1["active_entities_avg"] == 1.0
    
    # Check second window (partial final)
    w2 = json.loads(lines[1])
    assert w2["run_id"] == run_id
    assert w2["window_start_tick"] == 4
    assert w2["window_end_tick"] == 4
    assert w2["ticks_observed"] == 1
    assert w2["alive_entities_avg"] == 1.0
    
    # Reset override mode
    ObservabilityConfig.set_override_mode(None)

def test_kernel_metrics_disabled_when_off(clean_runs):
    """Verify that when ObservabilityMode is OFF, no metrics or directories are emitted."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    
    profile = RuntimeProfile(
        name="test-metrics-off",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6
    )

    e1 = V2EntityBuilder(1).combat(hp=100, alive=True).location(10.0, 10.0).build()
    state = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: e1})
    rng = DeterministicRNG(42)
    
    run_id = "test_run_metrics_integration_off"
    kernel = Kernel(profile, state, rng, run_id=run_id)
    
    assert kernel._metric_recorder is None
    
    kernel.tick_once()
    kernel.shutdown()
    
    repo = RunArtifactRepository()
    metrics_path = os.path.join(repo.base_dir, run_id, "metric_windows.jsonl")
    assert not os.path.exists(metrics_path)
    
    # Reset override mode
    ObservabilityConfig.set_override_mode(None)

def test_kernel_state_parity_with_metrics():
    """Verify that enabling/disabling metrics does not mutate RNG or cause state hash drift."""
    profile = RuntimeProfile(
        name="test-metrics-parity",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6
    )
    e1 = V2EntityBuilder(1).combat(hp=100, alive=True).location(10.0, 10.0).build()
    
    # Run 1: Observability Mode = OFF
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    state1 = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: e1})
    rng1 = DeterministicRNG(42)
    kernel1 = Kernel(profile, state1, rng1, run_id="test_run_parity_metrics_off")
    kernel1.tick_once()
    res1 = kernel1.shutdown()
    hash_off = res1.final_hash
    
    # Run 2: Observability Mode = LIGHT
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    state2 = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: e1})
    rng2 = DeterministicRNG(42)
    kernel2 = Kernel(profile, state2, rng2, run_id="test_run_parity_metrics_light")
    kernel2.tick_once()
    res2 = kernel2.shutdown()
    hash_light = res2.final_hash
    
    # Assert bit-identical parity of authoritative states
    assert hash_off == hash_light
    
    # Cleanup parity runs
    repo = RunArtifactRepository()
    for rid in ["test_run_parity_metrics_off", "test_run_parity_metrics_light"]:
        p = os.path.join(repo.base_dir, rid)
        if os.path.exists(p):
            shutil.rmtree(p)

    # Reset override mode
    ObservabilityConfig.set_override_mode(None)
