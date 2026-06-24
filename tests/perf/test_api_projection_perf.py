import time
import pytest
from src.config.profiles import PROD_DEFAULT
from src.api.engine_manager import V2EngineManager
from src.api.presenters.state_presenter import StatePresenter

@pytest.mark.slow
def test_api_projection_performance_benchmark():
    # Instantiate engine with 200 entities
    manager = V2EngineManager(profile=PROD_DEFAULT, entities_count=200)

    try:
        # Let manager build initial state and cache
        state = manager._latest_state
        assert state is not None

        # 1. Measure uncached raw StatePresenter performance across 20 iterations
        start_raw = time.perf_counter()
        for _ in range(20):
            entities_raw = [
                StatePresenter.present_entity(state.entities[eid])
                for eid in sorted(state.entities.keys())[:100]
            ]
        duration_raw = time.perf_counter() - start_raw

        # 2. Measure cached ReadModelCache performance across 20 iterations
        start_cached = time.perf_counter()
        for _ in range(20):
            res_cached = manager.get_entities_paged(offset=0, limit=100)
        duration_cached = time.perf_counter() - start_cached

        metrics = manager.read_cache.get_metrics()
        print(f"\n[API Projection Benchmark (200 entities)]")
        print(f"Uncached 20x 100-entity DTOs: {duration_raw:.5f}s")
        print(f"Cached   20x 100-entity DTOs: {duration_cached:.5f}s")
        print(f"Metrics: {metrics}")

        # Assert significant speedup (at least 3x faster)
        speedup = duration_raw / max(duration_cached, 1e-6)
        print(f"Speedup factor: {speedup:.2f}x")

        assert speedup >= 3.0, f"Expected at least 3x speedup, got {speedup:.2f}x"
        assert metrics["hits"] > 0
    finally:
        manager.shutdown()
