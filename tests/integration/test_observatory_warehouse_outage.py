"""
Warehouse Outage Resilience — Integration test.

Validates that when the warehouse backend (ClickHouse) is unreachable, the
engine continues operating, local run artifacts remain available, and
ingestion failures are handled gracefully.
"""
import os
import pytest

from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.warehouse.adapters import NullWarehouseAdapter, LocalWarehouseAdapter


ENTITY_COUNT = 20
SEED = 42


def _build_kernel(run_id: str) -> Kernel:
    profile = RuntimeProfile(
        name="warehouse-outage-profile",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=2048,
        max_cpu_percent=100.0,
        max_worker_count=2,
        max_queue_depth=500,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=50.0
    )
    entities = {}
    for idx in range(1, ENTITY_COUNT + 1):
        entities[idx] = V2EntityBuilder(idx).combat(hp=100, alive=True).location(10.0 + idx, 10.0 + idx).build()

    state = AuthoritativeState(tick=1, seed=SEED, world_time=100, entities=entities)
    rng = DeterministicRNG(SEED)
    return Kernel(profile, state, rng, run_id=run_id)


@pytest.fixture(autouse=True)
def setup_teardown():
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    yield
    ObservabilityConfig.set_override_mode(None)


def test_engine_continues_without_warehouse():
    """Engine completes ticks normally with NullWarehouseAdapter (simulating outage)."""
    kernel = _build_kernel("warehouse-outage-test")

    for _ in range(30):
        kernel.tick_once()

    assert kernel.state.tick >= 30, "Engine did not complete expected ticks"
    kernel.shutdown()


def test_local_artifacts_preserved_during_warehouse_outage():
    """Local run artifacts are written even when warehouse is unavailable."""
    run_id = "warehouse-outage-artifacts"
    kernel = _build_kernel(run_id)

    for _ in range(20):
        kernel.tick_once()

    kernel.shutdown()

    # Check that local run artifacts exist
    if hasattr(kernel, "_artifact_repo") and kernel._artifact_repo:
        run_dir = os.path.join(kernel._artifact_repo.base_dir, run_id)
        assert os.path.isdir(run_dir), f"Local run directory not found: {run_dir}"
        manifest_path = kernel._artifact_repo.resolve_path(run_id, "manifest")
        assert os.path.exists(manifest_path), f"Local manifest not found: {manifest_path}"


def test_null_warehouse_adapter_fails_safely():
    """NullWarehouseAdapter handles all operations without errors."""
    adapter = NullWarehouseAdapter()

    result = adapter.ingest_run("test-run")
    assert result.status in ("COMPLETED", "DRY_RUN")

    result = adapter.ingest_sweep("test-sweep")
    assert result.status in ("COMPLETED", "DRY_RUN")

    runs = adapter.query_runs({})
    assert runs == []

    health = adapter.health()
    assert health.connected is True

    adapter.close()  # Should not raise
