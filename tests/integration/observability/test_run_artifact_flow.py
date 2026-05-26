from __future__ import annotations
import os
import shutil
import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.engine.checkpoint import CanonicalStateHasher

@pytest.fixture
def clean_runs():
    base_dir = "data/runs"
    # Clean up test directories after run
    yield
    test_run_path = os.path.join(base_dir, "test_run_integration_123")
    if os.path.exists(test_run_path):
        shutil.rmtree(test_run_path)

def test_kernel_run_produces_manifest_and_events(clean_runs):
    # Set override mode to LIGHT
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    
    profile = RuntimeProfile(
        name="test-obs-integration",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6
    )

    # Active entity
    e1 = V2EntityBuilder(1).combat(hp=100, alive=True).location(10.0, 10.0).build()
    state = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: e1})
    rng = DeterministicRNG(42)
    
    # Initialize kernel with custom run_id
    run_id = "test_run_integration_123"
    kernel = Kernel(profile, state, rng, run_id=run_id)
    
    # Verify CREATED/RUNNING manifest is already written
    repo = RunArtifactRepository()
    manifest_before = repo.read_manifest(run_id)
    assert manifest_before.status == "RUNNING"
    assert manifest_before.run_id == run_id
    assert manifest_before.scenario_name == "test-obs-integration"
    
    # Simulate single tick advancement
    prior_state = AuthoritativeState(tick=0, seed=42, world_time=100, entities={})
    kernel._phase_observability(prior_state, None)
    
    # Shutdown kernel
    shutdown_result = kernel.shutdown()
    
    # Verify manifest completion updates
    manifest_after = repo.read_manifest(run_id)
    assert manifest_after.status == "COMPLETED"
    assert manifest_after.ticks_completed == 1
    assert manifest_after.ended_at is not None
    
    # Verify simulation_events.jsonl is successfully written
    events_path = repo.resolve_path(run_id, "events")
    assert os.path.exists(events_path)
    with open(events_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) >= 1

    # Reset override mode
    ObservabilityConfig.set_override_mode(None)

def test_kernel_state_parity_invariants():
    # Setup standard simulation inputs
    profile = RuntimeProfile(
        name="test-obs-parity",
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
    kernel1 = Kernel(profile, state1, rng1)
    prior_state1 = AuthoritativeState(tick=0, seed=42, world_time=100, entities={})
    kernel1._phase_observability(prior_state1, None)
    res1 = kernel1.shutdown()
    hash_off = res1.final_hash
    
    # Run 2: Observability Mode = LIGHT
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    state2 = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: e1})
    rng2 = DeterministicRNG(42)
    kernel2 = Kernel(profile, state2, rng2, run_id="test_run_parity_check")
    prior_state2 = AuthoritativeState(tick=0, seed=42, world_time=100, entities={})
    kernel2._phase_observability(prior_state2, None)
    res2 = kernel2.shutdown()
    hash_light = res2.final_hash
    
    # Assert bit-identical parity of authoritative states
    assert hash_off == hash_light
    
    # Cleanup parity run
    repo = RunArtifactRepository()
    test_run_path = os.path.join(repo.base_dir, "test_run_parity_check")
    if os.path.exists(test_run_path):
        shutil.rmtree(test_run_path)

    # Reset override mode
    ObservabilityConfig.set_override_mode(None)
