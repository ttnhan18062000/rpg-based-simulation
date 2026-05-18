# Compliance IDs: PERF-001, PERF-004, PERF-011
from __future__ import annotations

import os
from pathlib import Path
import pytest

from scripts.generate_optimization_proof import run_proof


@pytest.mark.slow
def test_generate_optimization_proof_report() -> None:
    """
    Verify that the optimization proof report generator successfully runs,
    calculates empirical speedups, and produces valid JSON/MD artifacts.
    """
    results = run_proof(quick_test=True)
    
    assert "metadata" in results
    assert "comparisons" in results
    
    # Assert all 5 benchmark scenarios are present
    expected_scenarios = {
        "MOVEMENT_1000", "RESOURCE_1000", "COMBAT_100", 
        "STRATEGIC_500", "MIXED_1000"
    }
    assert set(results["comparisons"].keys()) == expected_scenarios
    
    for name, comp in results["comparisons"].items():
        assert comp["scenario"] == name
        assert comp["speedup_x"] > 0
        assert comp["latency_reduction_x"] > 0
        assert "metrics" in comp["optimized"]
        
    # Check that output files were successfully created
    reports_dir = Path("reports/perf")
    assert (reports_dir / "optimization_proof.json").exists()
    assert (reports_dir / "optimization_proof.md").exists()
