import os
import sys
import json
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock

from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.config import ObservabilityMode
from src.observability.reporting.run_set_repository import RunSetArtifactRepository
from src.observability.reporting.baseline_generator import BaselineGenerator
from src.cli.entry import _run_gate


def test_cli_gate_scenario_level_flow(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    sweep_id = "test_gate_sweep"

    config = ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[1, 2],
        ticks=5,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    # 1. Execute sequential sweep
    ScenarioSweeper.run_sweep(config)

    # 2. Write deterministic metric fixtures BEFORE baseline generation so that
    #    the baseline thresholds are derived from the same values the comparison
    #    will see — avoids WARNING when actual tick-compute varies with system load.
    records = RunSetArtifactRepository(base_dir=output_dir).read_run_index(sweep_id)
    for r in records:
        run_dir = os.path.join(output_dir, sweep_id, "runs", r.run_id)
        with open(os.path.join(run_dir, "anomalies.json"), "w") as f:
            json.dump([], f)
        mw_path = os.path.join(run_dir, "metric_windows.jsonl")
        with open(mw_path, "w") as f:
            f.write(json.dumps({
                "tick_compute_ms_p95": 10.0,
                "memory_rss_bytes_max": 500.0,
                "event_count": 2
            }) + "\n")

    # 3. Generate baseline from the fixture data written above
    BaselineGenerator.generate_baseline(sweep_id, base_dir=output_dir)
    baseline_path = os.path.join(output_dir, sweep_id, "baseline.json")

    # Mock repository base directory during CLI subcommand execution
    original_init = RunSetArtifactRepository.__init__
    def mock_init(self, base_dir="data/run_sets"):
        original_init(self, base_dir=output_dir)

    # Test CLI execution passing successfully
    with patch.object(RunSetArtifactRepository, "__init__", mock_init), \
         patch("sys.exit") as mock_exit:
         
        cli_args = MagicMock()
        cli_args.sweep_id = sweep_id
        cli_args.baseline = baseline_path
        cli_args.envelope = None
        cli_args.warn_as_fail = False
        cli_args.insufficient_as_fail = False
        
        captured_out = StringIO()
        sys.stdout = captured_out
        try:
            _run_gate(cli_args)
        finally:
            sys.stdout = sys.__stdout__

        assert mock_exit.called
        assert mock_exit.call_args[0][0] == 0  # Expected pass code 0
        cli_output = captured_out.getvalue()
        assert "CI Gate Evaluation Result: PASS" in cli_output
        assert "Markdown Report Generated:" in cli_output
        assert "JSON Report Generated:" in cli_output

        # Verify artifacts exist
        sweep_dir = os.path.join(output_dir, sweep_id)
        assert os.path.exists(os.path.join(sweep_dir, "sweep_report.md"))
        assert os.path.exists(os.path.join(sweep_dir, "sweep_report.json"))
        assert os.path.exists(os.path.join(sweep_dir, "ci_gate_result.json"))


def test_cli_gate_warn_as_fail(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    sweep_id = "test_gate_sweep_warn"

    config = ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[1, 2],
        ticks=5,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    ScenarioSweeper.run_sweep(config)
    BaselineGenerator.generate_baseline(sweep_id, base_dir=output_dir)
    baseline_path = os.path.join(output_dir, sweep_id, "baseline.json")

    # Injecting warnings to the run results to trigger a WARNING state
    records = RunSetArtifactRepository(base_dir=output_dir).read_run_index(sweep_id)
    for idx, r in enumerate(records):
        run_dir = os.path.join(output_dir, sweep_id, "runs", r.run_id)
        
        # Overwrite run_report.json with warnings_count: 1
        report_data = {
            "metadata": {
                "health_score": 100.0,
                "errors_count": 0,
                "warnings_count": 1,
                "hard_law_violations_count": 0
            }
        }
        with open(os.path.join(run_dir, "run_report.json"), "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
            
        r.warning_count = 1
        with open(os.path.join(run_dir, "anomalies.json"), "w") as f:
            # Adding an anomaly triggers warning
            json.dump([{
                "rule_name": "NavigationStuckBasic",
                "severity": "WARNING",
                "tick_detected": 1,
                "message": "Warning trigger",
                "entity_id": "hero",
                "context": {}
            }], f)
        
        mw_path = os.path.join(run_dir, "metric_windows.jsonl")
        with open(mw_path, "w") as f:
            f.write(json.dumps({
                "tick_compute_ms_p95": 10.0,
                "memory_rss_bytes_max": 500.0,
                "event_count": 2
            }) + "\n")

    # Rewrite the run_index with updated records
    with open(os.path.join(output_dir, sweep_id, "run_index.jsonl"), "w") as f:
        for r in records:
            f.write(r.model_dump_json() + "\n")

    original_init = RunSetArtifactRepository.__init__
    def mock_init(self, base_dir="data/run_sets"):
        original_init(self, base_dir=output_dir)

    # Test warn_as_fail = True (should exit with 1)
    with patch.object(RunSetArtifactRepository, "__init__", mock_init), \
         patch("sys.exit") as mock_exit:
         
        cli_args = MagicMock()
        cli_args.sweep_id = sweep_id
        cli_args.baseline = baseline_path
        cli_args.envelope = None
        cli_args.warn_as_fail = True
        cli_args.insufficient_as_fail = False
        
        captured_out = StringIO()
        sys.stdout = captured_out
        try:
            _run_gate(cli_args)
        finally:
            sys.stdout = sys.__stdout__

        assert mock_exit.called
        assert mock_exit.call_args_list[0][0][0] == 1  # Should exit with code 1
        cli_output = captured_out.getvalue()
        assert "CI Gate Evaluation Result: FAIL" in cli_output
        assert "Warnings detected and --warn-as-fail is enabled." in cli_output
