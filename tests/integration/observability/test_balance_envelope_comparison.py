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
from src.observability.reporting.baseline_comparator import BaselineComparator
from src.cli.entry import _run_compare_run, _run_compare_sweep


def test_balance_envelope_integration_and_cli_flow(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    sweep_id = "test_env_compare_sweep"

    config = ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[1, 2],
        ticks=2,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    # 1. Execute sequential sweep
    ScenarioSweeper.run_sweep(config)

    # 2. Generate baseline
    baseline = BaselineGenerator.generate_baseline(sweep_id, base_dir=output_dir)
    baseline_path = os.path.join(output_dir, sweep_id, "baseline.json")

    # 3. Inject mock run details to simulate a run that degraded slightly but within envelope
    records = RunSetArtifactRepository(base_dir=output_dir).read_run_index(sweep_id)
    for r in records:
        run_dir = os.path.join(output_dir, sweep_id, "runs", r.run_id)
        # Ensure anomalies.json exists
        with open(os.path.join(run_dir, "anomalies.json"), "w") as f:
            json.dump([], f)
        # Ensure metric_windows.jsonl exists with tick_compute_ms_p95=95.0
        mw_path = os.path.join(run_dir, "metric_windows.jsonl")
        with open(mw_path, "w") as f:
            f.write(json.dumps({"tick_compute_ms_p95": 95.0, "memory_rss_bytes_max": 1000.0, "event_count": 5}) + "\n")

    run_id = records[0].run_id

    # Create custom balance envelope file
    envelope_data = {
        "scenario_name": "SANDBOX_E2E_ENVELOPE",
        "scenario_type": "sandbox",
        "expectations": {
            "tick_compute_ms_p95": {
                "max": 100.0,
                "severity": "FAIL"
            },
            "health_score": {
                "min": 80.0,
                "severity": "FAIL"
            }
        },
        "schema_version": "1.0"
    }
    envelope_path = os.path.join(output_dir, "sandbox_balance_envelope.json")
    with open(envelope_path, "w", encoding="utf-8") as f:
        json.dump(envelope_data, f)

    # Test programmatic run compare with envelope
    res_run = BaselineComparator.compare_run(
        run_id, 
        baseline_path, 
        run_dir=os.path.join(output_dir, sweep_id, "runs"),
        envelope_path=envelope_path
    )
    assert res_run.status == "PASS"
    assert res_run.envelope_name == "SANDBOX_E2E_ENVELOPE"
    assert res_run.metric_comparisons["tick_compute_ms_p95"].status == "PASS"

    # Test compare-run CLI command launcher with --envelope
    original_init = RunSetArtifactRepository.__init__
    def mock_init(self, base_dir="data/run_sets"):
        original_init(self, base_dir=output_dir)

    with patch.object(RunSetArtifactRepository, "__init__", mock_init), \
         patch("sys.exit") as mock_exit:
         
        cli_args = MagicMock()
        cli_args.run_id = run_id
        cli_args.baseline = baseline_path
        cli_args.envelope = envelope_path
        
        captured_out = StringIO()
        sys.stdout = captured_out
        try:
            _run_compare_run(cli_args)
        finally:
            sys.stdout = sys.__stdout__

        assert mock_exit.called
        assert mock_exit.call_args[0][0] == 0  # Passed run exit code 0
        cli_output = captured_out.getvalue()
        assert "Comparison Result: PASS" in cli_output
        assert "Envelope Name:     SANDBOX_E2E_ENVELOPE" in cli_output

    # Test compare-sweep CLI command launcher with --envelope
    with patch.object(RunSetArtifactRepository, "__init__", mock_init), \
         patch("sys.exit") as mock_exit:
         
        cli_args = MagicMock()
        cli_args.sweep_id = sweep_id
        cli_args.baseline = baseline_path
        cli_args.envelope = envelope_path
        
        captured_out = StringIO()
        sys.stdout = captured_out
        try:
            _run_compare_sweep(cli_args)
        finally:
            sys.stdout = sys.__stdout__

        assert mock_exit.called
        assert mock_exit.call_args[0][0] == 0  # Passed sweep exit code 0
        cli_output = captured_out.getvalue()
        assert "Comparison Result: PASS" in cli_output
        assert "Envelope Name:     SANDBOX_E2E_ENVELOPE" in cli_output
