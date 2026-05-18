import pytest
import time
import copy
import json
from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES
from src.perf.scenarios import build_idle_state
from src.api.presenters.state_presenter import StatePresenter

def _run_snapshot_benchmark(entity_count, samples, perf_report_dir):
    state = build_idle_state(entity_count=entity_count)
    
    results = {}
    
    # 1. Deepcopy
    latencies = []
    for _ in range(samples):
        start = time.perf_counter()
        _ = copy.deepcopy(state)
        latencies.append((time.perf_counter() - start) * 1000.0)
    results["deepcopy"] = {
        "avg": sum(latencies) / samples,
        "p95": sorted(latencies)[int(samples * 0.95)] if samples > 1 else latencies[0]
    }
    
    # 2. to_readonly
    latencies = []
    for _ in range(samples):
        start = time.perf_counter()
        _ = state.to_readonly()
        latencies.append((time.perf_counter() - start) * 1000.0)
    results["to_readonly"] = {
        "avg": sum(latencies) / samples,
        "p95": sorted(latencies)[int(samples * 0.95)] if samples > 1 else latencies[0]
    }
    
    # 3. Present Minimal
    latencies = []
    for _ in range(samples):
        start = time.perf_counter()
        _ = StatePresenter.present_minimal(state)
        latencies.append((time.perf_counter() - start) * 1000.0)
    results["present_minimal"] = {
        "avg": sum(latencies) / samples,
        "p95": sorted(latencies)[int(samples * 0.95)] if samples > 1 else latencies[0]
    }
    
    # 4. Present Full
    latencies = []
    for _ in range(samples):
        start = time.perf_counter()
        _ = StatePresenter.present_full(state)
        latencies.append((time.perf_counter() - start) * 1000.0)
    results["present_full"] = {
        "avg": sum(latencies) / samples,
        "p95": sorted(latencies)[int(samples * 0.95)] if samples > 1 else latencies[0]
    }
    
    final_result = {
        "scenario_id": f"API_SNAPSHOT_COMPARE_{entity_count}",
        "entity_count": entity_count,
        "metrics": results,
        "samples": samples
    }
    
    report_path = perf_report_dir / f"API_SNAPSHOT_COMPARE_{entity_count}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(final_result, f, indent=2)
        
    print(f"\nAPI Comparison ({entity_count} entities):")
    print(f"  Deepcopy:        {results['deepcopy']['p95']:.4f}ms")
    print(f"  to_readonly:     {results['to_readonly']['p95']:.4f}ms")
    print(f"  Present Minimal: {results['present_minimal']['p95']:.4f}ms")
    print(f"  Present Full:    {results['present_full']['p95']:.4f}ms")
    
    return results

@pytest.mark.perf
@pytest.mark.parametrize("entity_count", [100, 1000])
def test_api_snapshot_performance_comparison(entity_count, perf_report_dir):
    """
    CI-safe comparison of state snapshot mechanisms for small to medium entity counts.
    """
    samples = 50 if entity_count <= 100 else 30
    results = _run_snapshot_benchmark(entity_count, samples, perf_report_dir)
    
    assert results["present_minimal"]["p95"] < 1.5
    assert results["to_readonly"]["p95"] < 1.5

@pytest.mark.slow
@pytest.mark.perf
@pytest.mark.parametrize("entity_count", [5000])
def test_api_snapshot_performance_stress(entity_count, perf_report_dir):
    """
    Stress comparison of state snapshot mechanisms for massive entity counts (5,000+).
    Marked slow to prevent CI timeouts during routine test runs.
    """
    samples = 15
    results = _run_snapshot_benchmark(entity_count, samples, perf_report_dir)
    assert results["present_minimal"]["p95"] < 2.5
    assert results["to_readonly"]["p95"] < 2.5
