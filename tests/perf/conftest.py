import pytest
import json
import logging
from pathlib import Path
from typing import Dict, Any

from src.perf.bench_harness import BenchHarness
from src.perf.profiles import PERF_PROFILES

logger = logging.getLogger(__name__)


@pytest.fixture
def perf_harness():
    """Returns a factory for BenchHarness with a specific profile."""
    def _make_harness(profile_name: str = "PERF_512MB_LOCAL"):
        profile = PERF_PROFILES[profile_name]
        return BenchHarness(profile)
    return _make_harness


@pytest.fixture(autouse=True)
def perf_reporter(request):
    """Automatically logs performance results to a JSON file if the test is marked 'perf'."""
    yield
    
    # After test execution
    if "perf" in request.keywords:
        results = getattr(request.node, "perf_results", None)
        if results:
            report_dir = Path("reports/perf")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_path = report_dir / f"{request.node.name}.json"
            with open(report_path, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Performance report saved to {report_path}")

@pytest.fixture
def perf_report_dir():
    """Directory for performance reports."""
    path = Path("reports/perf")
    path.mkdir(parents=True, exist_ok=True)
    return path
