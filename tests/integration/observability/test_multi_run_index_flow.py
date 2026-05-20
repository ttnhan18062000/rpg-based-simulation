import os
import sys
import shutil
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.config import ObservabilityMode
from src.observability.reporting.run_set_repository import RunSetArtifactRepository
from src.cli.entry import _run_list_sweeps, _run_inspect_sweep


def test_multi_run_index_and_cli_flow(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    sweep_id = "test_multi_run_index_sweep"

    config = ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[10, 20],
        ticks=2,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    # 1. Run Sweep Execution
    manifest = ScenarioSweeper.run_sweep(config)

    assert manifest.status == "COMPLETED"
    assert manifest.completed_count == 2

    # Assert repo outputs
    repo = RunSetArtifactRepository(base_dir=output_dir)
    records = repo.read_run_index(sweep_id)
    assert len(records) == 2
    assert records[0].run_id == "run_test_multi_run_index_sweep_seed_10"
    assert records[0].health_score == 100.0
    assert records[1].run_id == "run_test_multi_run_index_sweep_seed_20"
    assert records[1].health_score == 100.0

    summary = repo.read_sweep_summary(sweep_id)
    assert summary.sweep_id == sweep_id
    assert summary.total_runs == 2
    assert summary.completed_runs == 2
    assert summary.failed_runs == 0
    assert summary.average_health_score == 100.0
    assert summary.best_run_id is not None
    assert summary.worst_run_id is not None

    # 2. Test CLI commands outputs
    # Patch RunSetArtifactRepository to use our custom base_dir in list-sweeps & inspect-sweep
    original_init = RunSetArtifactRepository.__init__
    def mock_init(self, base_dir="data/run_sets"):
        original_init(self, base_dir=output_dir)

    with patch.object(RunSetArtifactRepository, "__init__", mock_init):
        # Test List Sweeps CLI function
        list_args = MagicMock()
        list_args.json_logs = False
        
        captured_out = StringIO()
        sys.stdout = captured_out
        try:
            _run_list_sweeps(list_args)
        finally:
            sys.stdout = sys.__stdout__

        list_output = captured_out.getvalue()
        assert sweep_id in list_output
        assert "idle" in list_output
        assert "COMPLETED" in list_output

        # Test Inspect Sweep CLI function
        inspect_args = MagicMock()
        inspect_args.sweep_id = sweep_id
        inspect_args.json_logs = False
        
        captured_out_ins = StringIO()
        sys.stdout = captured_out_ins
        try:
            _run_inspect_sweep(inspect_args)
        finally:
            sys.stdout = sys.__stdout__

        inspect_output = captured_out_ins.getvalue()
        assert f"Sweep Observatory: {sweep_id}" in inspect_output
        assert "Avg Health Score:  100.0%" in inspect_output
        assert "run_test_multi_run_index_sweep_seed_10" in inspect_output
        assert "run_test_multi_run_index_sweep_seed_20" in inspect_output
