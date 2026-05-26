import os
import sys
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.config import ObservabilityMode
from src.observability.reporting.run_set_repository import RunSetArtifactRepository
from src.observability.reporting.baseline_generator import BaselineGenerator
from src.cli.entry import _run_generate_baseline


def test_baseline_generation_and_cli_flow(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    sweep_id = "test_baseline_sweep"

    config = ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        # 5 seeds to get accepted_run_count = 5 and avoid the weak baseline warning flag if needed
        seeds=[1, 2, 3, 4, 5],
        ticks=2,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    # 1. Execute sequential sweep
    ScenarioSweeper.run_sweep(config)

    # Verify run set repository listings
    repo = RunSetArtifactRepository(base_dir=output_dir)
    assert sweep_id in repo.list_sweeps()

    # 2. Invoke Baseline Generation
    baseline = BaselineGenerator.generate_baseline(sweep_id, base_dir=output_dir)

    assert baseline.baseline_id == f"baseline_{sweep_id}"
    assert baseline.run_count == 5
    assert baseline.accepted_run_count == 5
    assert baseline.is_weak_baseline is False  # Exactly 5 completed runs

    # Assert metric statistics are complete and correct
    health_score_dist = baseline.metrics["health_score"]
    assert health_score_dist.count == 5
    assert health_score_dist.mean == 100.0
    assert health_score_dist.median == 100.0

    # 3. Test CLI Subcommand Execution
    # Patch RunSetArtifactRepository default instantiation path
    original_init = RunSetArtifactRepository.__init__
    def mock_init(self, base_dir="data/run_sets"):
        original_init(self, base_dir=output_dir)

    with patch.object(RunSetArtifactRepository, "__init__", mock_init):
        cli_args = MagicMock()
        cli_args.sweep_id = sweep_id
        cli_args.json_logs = False

        captured_out = StringIO()
        sys.stdout = captured_out
        try:
            _run_generate_baseline(cli_args)
        finally:
            sys.stdout = sys.__stdout__

        cli_output = captured_out.getvalue()
        assert f"Baseline successfully generated: baseline_{sweep_id}" in cli_output
        assert "idle (sandbox)" in cli_output
        assert "health_score" in cli_output
        assert "critical_count" in cli_output
        assert "memory_rss_bytes_max" in cli_output
